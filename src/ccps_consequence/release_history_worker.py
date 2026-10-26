# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""SLABx finite/continuous runs with an explicitly approximate growing-cloud bridge."""
import json
import math
from .dense_worker import engine_info
from .dense_profile import normalized_profile,horizontal_shape


def execute_release_history(payload):
    import numpy as np
    from slabx.core.source import EvaporatingPool
    from slabx.core.plume import run_dispersion
    from slabx.submodels.atmosphere import Atmosphere
    from slabx.thermo.base import Substance,LegacyThermo,water_backend
    from .dense import DenseHistory
    from .release_history import ReleaseHistoryInput,ReleaseHistoryOutput,SegmentLedger
    x=ReleaseHistoryInput.model_validate_json(json.dumps(payload))
    info=engine_info()
    if info["status"]!="available" or info["engine_code_digest"]!=x.expected_engine_code_digest:
        raise ValueError("SLABx missing, version or source fingerprint mismatch; no fallback")
    s,a=x.substance,x.atmosphere
    substance=Substance(name=s.name,mw=s.molecular_weight_kg_mol,cp_vapour=s.vapor_heat_capacity_j_kg_k,
        cp_liquid=s.liquid_heat_capacity_j_kg_k,dh_vap=s.latent_heat_j_kg,T_boil=s.normal_boiling_temperature_k,rho_liquid=s.liquid_density_kg_m3)
    atm=Atmosphere(u_ref=a.wind_speed_m_s,z_ref=a.wind_reference_height_m,T=a.temperature_k,
        rh=100*a.relative_humidity_fraction,z0=a.roughness_length_m,stability=a.stability,p=a.pressure_pa_abs)
    samples=np.asarray(x.sample_times_s)
    total_values=np.zeros((len(x.receptors),len(samples)))
    total_fractions=np.zeros_like(total_values)
    cloud_mass=np.zeros(len(samples))
    ledgers=[]
    canonical=x.source.canonical_intervals()
    for segment in canonical:
        if segment.mass_rate_kg_s==0:
            continue
        is_continuous=x.source.mode=="continuous_through_window" and segment is canonical[-1]
        duration=math.inf if is_continuous else segment.end_s-segment.start_s
        local_end=x.simulation_end_s-segment.start_s
        src=EvaporatingPool(substance,rate=segment.mass_rate_kg_s,area=x.source.area_m2,duration=duration,T_source=x.source.temperature_k)
        if src.T!=x.source.temperature_k or src.rho_source<=atm.rho:
            raise ValueError("qualified source is not a native dense ground vapour boundary")
        traj,used=run_dispersion(src,atm,LegacyThermo(substance),water_backend(),x_max=x.plume_distance_limit_m,
            t_max=local_end,n_puff_steps=x.native_puff_steps)
        if np.any(np.diff(traj.t)<0):
            raise ValueError("native clock runs backwards")
        # Very fine log-puff output steps may round to the same float at t_sd.
        # Keep the first state (including the exact plume cut), never interpolate
        # a zero-width interval. Record removal rather than altering the clock.
        keep=np.r_[True,np.diff(traj.t)>0]
        duplicate_count=int(np.count_nonzero(~keep))
        if duplicate_count:
            from dataclasses import fields,replace
            traj=replace(traj,**{f.name:getattr(traj,f.name)[keep] for f in fields(traj)
                if isinstance(getattr(traj,f.name),np.ndarray) and len(getattr(traj,f.name))==len(keep)})
        needed=(traj.t,traj.x,traj.rho,traj.mass_frac,traj.vol_frac,traj.u,traj.h,traj.b_half,
            traj.b_shape,traj.beta,traj.b_half_x,traj.b_shape_x,traj.beta_x,traj.sigma_z,traj.z_c,traj.mass_frac_emission_liquid)
        if any(not np.all(np.isfinite(v)) for v in needed) or np.any(np.diff(traj.t)<=0) or traj.t[0]!=0.:
            raise ValueError("native release trajectory invalid")
        needed_clock=2*local_end if is_continuous else local_end
        if traj.t[-1]<needed_clock and not math.isclose(float(traj.t[-1]),needed_clock,rel_tol=1e-12,abs_tol=1e-12):
            raise ValueError("native plume distance limit does not cover requested clock; increase plume_distance_limit_m")
        if np.max(traj.mass_frac_emission_liquid)>1e-8:
            raise ValueError("native emitted-liquid condensation outside pure vapour boundary")
        transition=traj.meta.get("transition_t")
        if not is_continuous and (transition is None or not np.any(traj.is_puff)):
            raise ValueError("native plume-to-puff transition not reached; increase plume_distance_limit_m")
        q=segment.mass_rate_kg_s
        native_mass=np.where(traj.is_puff,4*traj.rho*traj.b_half_x*traj.b_half*traj.h*traj.mass_frac,q*np.minimum(traj.t,duration))
        puff_error=float(np.max(np.abs(native_mass[traj.is_puff]/(q*duration)-1))) if np.any(traj.is_puff) else 0.
        flux=2*traj.rho*traj.u*traj.b_half*traj.h*traj.mass_frac
        downstream=traj.is_plume & (traj.x>used.half_width)
        transition_flux_error=0.
        if transition is not None:
            cut=int(np.flatnonzero(traj.is_plume)[-1])
            transition_flux_error=float(abs(flux[cut]/q-1))
            downstream[cut]=False  # native cut interpolates states; its flux residual is separately reported
        flux_error=float(np.max(np.abs(flux[downstream]/q-1))) if np.any(downstream) else 0.
        if max(puff_error,flux_error)>1e-5:
            raise ValueError("native puff mass or post-source plume flux conservation failed")
        # During filling, reconstruct a quasi-steady whole cloud of mass q*t.
        # Eq.30 extends its half-length to the native transition; this is an
        # explicit closure, not a native transient plume solution.
        reconstructed_bx=np.asarray(traj.b_half_x).copy()
        reconstructed_shape_x=np.asarray(traj.b_shape_x).copy()
        reconstructed_beta_x=np.asarray(traj.beta_x).copy()
        for j in np.flatnonzero(traj.is_plume):
            if native_mass[j]<=0:
                continue
            denominator=4*traj.rho[j]*traj.b_half[j]*traj.h[j]*traj.mass_frac[j]
            if denominator<=0:
                raise ValueError("nonpositive mean state in growing cloud")
            reconstructed_bx[j]=native_mass[j]/denominator
            reconstructed_shape_x[j]=.9999*reconstructed_bx[j]
            reconstructed_beta_x[j]=math.sqrt(reconstructed_bx[j]**2-reconstructed_shape_x[j]**2)/math.sqrt(3)
        native_volume=4*reconstructed_bx*traj.b_half*traj.h
        native_vapour_volume=native_volume*traj.vol_frac
        valid=np.flatnonzero(samples>=segment.start_s)
        clock=samples[valid]-segment.start_s
        if is_continuous:
            # Native plume t=2*Q_integral/q, not travel time. Fill a steady,
            # spatially varying plume to Q_integral=q*elapsed: front at native
            # clock 2*elapsed. Its integrated emission mass is exactly q*t.
            cloud_mass[valid]+=q*clock
            for k,r in enumerate(x.receptors):
                rx=r.downwind_distance_m
                if not traj.x[0]<=rx<=traj.x[-1]:
                    raise ValueError("continuous receptor outside native plume grid")
                get=lambda v:float(np.interp(rx,traj.x,v))
                by,beta,sigma,zc=get(traj.b_shape),get(traj.beta),get(traj.sigma_z),get(traj.z_c)
                shape=horizontal_shape(r.crosswind_distance_m,by,beta)*(math.exp(-.5*((r.height_m-zc)/sigma)**2)+math.exp(-.5*((r.height_m+zc)/sigma)**2))/(4*by*math.sqrt(2*math.pi)*sigma)
                line_mass=get(2*traj.rho*traj.b_half*traj.h*traj.mass_frac)
                line_volume=get(2*traj.b_half*traj.h*traj.vol_frac)
                arrival=get(traj.t)/2
                active=clock>=arrival
                total_values[k,valid]+=line_mass*shape*active
                total_fractions[k,valid]+=line_volume*shape*active
            ledgers.append(SegmentLedger(start_s=segment.start_s,stop_s=segment.end_s,rate_kg_s=q,mode="continuous_through_window",
                source_mass_within_window_kg=q*(segment.end_s-segment.start_s),transition_time_s=None,transition_x_m=None,
                native_final_time_s=float(traj.t[-1]),used_source_area_m2=float(used.area),
                maximum_puff_mass_relative_residual=0.,maximum_plume_flux_relative_residual=flux_error,
                transition_mass_relative_residual=0.,native_transition_flux_relative_residual=0.,
                native_duplicate_clock_rows_removed=duplicate_count,
                native_times_s=tuple(map(float,traj.t)),native_clock_kind="plume_twice_integrated_mass_over_rate",native_modes=tuple("plume" for _ in traj.t),
                native_center_x_m=tuple(map(float,traj.x)),accounted_emission_mass_kg=tuple(map(float,q*traj.t/2))))
            continue
        def interp(v):
            return np.interp(clock,traj.t,v)
        masses=interp(native_mass)
        # The t=0 native row has no released mass even if native placeholder widths are nonzero.
        native_vapour_volume[0]=0.
        vapour_volumes=interp(native_vapour_volume)
        cx,cz,bx,by,bex,bey,sz=map(interp,(traj.x,traj.z_c,reconstructed_shape_x,traj.b_shape,reconstructed_beta_x,traj.beta,traj.sigma_z))
        cloud_mass[valid]+=masses
        for k,r in enumerate(x.receptors):
            for i,global_index in enumerate(valid):
                if masses[i]<=0:
                    continue
                kernel=normalized_profile(dx=r.downwind_distance_m-cx[i],y=r.crosswind_distance_m,z=r.height_m,
                    center_z=cz[i],bx=bx[i],by=by[i],beta_x=bex[i],beta_y=bey[i],sigma_z=sz[i])
                total_values[k,global_index]+=masses[i]*kernel
                total_fractions[k,global_index]+=vapour_volumes[i]*kernel
        transition_mass_error=0.
        if transition is not None:
            cut=int(np.flatnonzero(traj.is_plume)[-1])
            cut_mass=4*traj.rho[cut]*reconstructed_bx[cut]*traj.b_half[cut]*traj.h[cut]*traj.mass_frac[cut]
            transition_mass_error=float(abs(cut_mass/(q*duration)-1))
        ledgers.append(SegmentLedger(start_s=segment.start_s,stop_s=segment.end_s,rate_kg_s=q,
            mode="continuous_through_window" if is_continuous else "finite",source_mass_within_window_kg=q*(segment.end_s-segment.start_s),
            transition_time_s=float(transition+segment.start_s) if transition is not None else None,
            transition_x_m=float(traj.meta["transition_x"]) if transition is not None else None,
            native_final_time_s=float(traj.t[-1]),used_source_area_m2=float(used.area),
            maximum_puff_mass_relative_residual=puff_error,maximum_plume_flux_relative_residual=flux_error,
            transition_mass_relative_residual=transition_mass_error,native_transition_flux_relative_residual=transition_flux_error,
            native_duplicate_clock_rows_removed=duplicate_count,
            native_times_s=tuple(map(float,traj.t)),native_clock_kind="plume_release_clock_then_puff",native_modes=tuple("puff" if p else "plume" for p in traj.is_puff),
            native_center_x_m=tuple(map(float,traj.x)),accounted_emission_mass_kg=tuple(map(float,native_mass))))
    if np.any(~np.isfinite(total_values)) or np.any(~np.isfinite(total_fractions)) or np.any(total_fractions<0) or np.any(total_fractions>1):
        raise ValueError("independent-cloud superposition exceeds physical bounds; no clipping or fallback")
    histories=[]
    for k,r in enumerate(x.receptors):
        values=total_values[k].tolist()
        peak=max(range(len(values)),key=values.__getitem__)
        tail="end_above_threshold" if values[-1]>=x.tail_threshold_kg_m3 else "end_below_threshold_peak_at_end" if peak==len(values)-1 else "end_below_threshold"
        histories.append(DenseHistory(receptor_id=r.id,concentration_kg_m3=tuple(values),volume_fraction=tuple(map(float,total_fractions[k])),
            sampled_peak_kg_m3=values[peak],sampled_peak_time_s=x.sample_times_s[peak],
            sampled_integral_kg_s_m3=math.fsum((b-a)*(c+d)/2 for a,b,c,d in zip(samples,samples[1:],values,values[1:])),tail_status=tail))
    emitted=tuple(x.source.cumulative_mass(t) for t in x.sample_times_s)
    residual=float(np.max(np.abs(cloud_mass-np.asarray(emitted)))/x.source.declared_mass_within_history_kg)
    if engine_info()["engine_code_digest"]!=info["engine_code_digest"]:
        raise ValueError("SLABx source changed during release history run")
    return ReleaseHistoryOutput(engine_code_digest=info["engine_code_digest"],dependency_versions=info["dependencies"],request_digest=x.digest(),
        sample_times_s=x.sample_times_s,histories=tuple(histories),cumulative_emitted_mass_kg=emitted,reconstructed_cloud_mass_kg=tuple(map(float,cloud_mass)),
        source_mass_within_window_kg=x.source.declared_mass_within_history_kg,maximum_reconstruction_mass_relative_residual=residual,
        segments=tuple(ledgers),source_active_at_window_end=x.source.mode=="continuous_through_window").model_dump(mode="json")
