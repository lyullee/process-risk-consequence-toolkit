# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Research 1D isothermal variable-density shallow-layer conservation model.

One Eulerian field, no independent-cloud superposition. This is an authored
restricted model, not TWODEE, SLAB or the published two-layer formulation.
"""
from __future__ import annotations
import math
from typing import Annotated, Literal
from pydantic import Field, model_validator
from .contracts import Model, Name, Nonnegative, Positive
from .release_history import ReleaseHistory
from .dense import DenseReceptor, DenseHistory


class CoupledInput(Model):
    source: ReleaseHistory
    temperature_k: Positive
    air_density_kg_m3: Positive
    pure_vapour_density_kg_m3: Positive
    density_basis: Name
    x_min_m: float
    x_max_m: float
    cells: Annotated[int,Field(ge=20,le=2000)]
    width_m: Positive
    source_start_m: float
    wind_speed_m_s: float
    injection_velocity_m_s: float
    wind_relaxation_time_s: Positive | None
    entrainment_coefficient: Annotated[float,Field(ge=0,le=.5)]
    closure_basis: Name
    gravity_m_s2: Positive
    maximum_step_s: Positive
    cfl: Annotated[float,Field(gt=0,le=.45)]
    maximum_steps: Annotated[int,Field(ge=10,le=200000)] = 40000
    sample_times_s: Annotated[tuple[Nonnegative,...],Field(min_length=2,max_length=2001)]
    receptors: Annotated[tuple[DenseReceptor,...],Field(min_length=1,max_length=32)]
    tail_threshold_kg_m3: Positive
    boundary: Literal["open_vacuum", "reflecting"]
    applicability: Literal["research_1d_isothermal_fixed_width_flat_ground_layer"]

    @model_validator(mode="after")
    def domain(self):
        if self.x_max_m<=self.x_min_m:
            raise ValueError("coupled domain must have positive length")
        if self.pure_vapour_density_kg_m3<=self.air_density_kg_m3:
            raise ValueError("coupled model requires a denser-than-air constituent")
        if self.source.temperature_k!=self.temperature_k:
            raise ValueError("isothermal coupled boundary requires equal source/ambient temperature")
        if self.sample_times_s[0]!=0. or any(b<=a for a,b in zip(self.sample_times_s,self.sample_times_s[1:])) or self.sample_times_s[-1]>3600:
            raise ValueError("sample clock must start at zero, increase and end <=3600s")
        end=self.sample_times_s[-1]
        source_end=self.source.intervals[-1].end_s
        if (self.source.mode=="finite" and source_end>end) or (self.source.mode=="continuous_through_window" and source_end!=end):
            raise ValueError("source/observation window mismatch")
        dx=(self.x_max_m-self.x_min_m)/self.cells
        start=(self.source_start_m-self.x_min_m)/dx
        count=self.source.area_m2/(self.width_m*dx)
        if not math.isclose(start,round(start),abs_tol=1e-9) or not math.isclose(count,round(count),abs_tol=1e-9) or count<1 or start<0 or start+count>self.cells:
            raise ValueError("source footprint must align with whole grid cells and stay inside domain")
        if len({r.id for r in self.receptors})!=len(self.receptors):
            raise ValueError("duplicate coupled receptor")
        for r in self.receptors:
            if not self.x_min_m<=r.downwind_distance_m<self.x_max_m or abs(r.crosswind_distance_m)>=self.width_m/2:
                raise ValueError("receptor outside fixed-width coupled domain")
        if len(self.sample_times_s)*len(self.receptors)>32000:
            raise ValueError("coupled receptor/time product exceeds limit")
        return self


class CoupledOutput(Model):
    solver: Literal["authored_1d_variable_density_rusanov_v1"] = "authored_1d_variable_density_rusanov_v1"
    model_status: Literal["research_numerically_verified_not_field_validated"] = "research_numerically_verified_not_field_validated"
    numpy_version: Name
    air_density_kg_m3: Positive
    pure_vapour_density_kg_m3: Positive
    cell_plan_area_m2: Positive
    sample_times_s: tuple[Nonnegative,...]
    histories: tuple[DenseHistory,...]
    cumulative_source_mass_kg: tuple[Nonnegative,...]
    domain_emission_mass_kg: tuple[Nonnegative,...]
    escaped_emission_mass_kg: tuple[Nonnegative,...]
    domain_mixture_mass_kg: tuple[Nonnegative,...]
    escaped_mixture_mass_kg: tuple[Nonnegative,...]
    entrained_air_mass_kg: tuple[Nonnegative,...]
    emission_roundoff_correction_kg: tuple[float,...]
    mixture_roundoff_correction_kg: tuple[float,...]
    maximum_emission_mass_relative_residual: Nonnegative
    maximum_mixture_mass_relative_residual: Nonnegative
    maximum_absolute_roundoff_correction_kg: Nonnegative
    maximum_observed_cfl: Nonnegative
    accepted_steps: Annotated[int,Field(ge=1)]
    final_cell_centers_m: tuple[float,...]
    final_layer_height_m: tuple[Nonnegative,...]
    final_mixture_density_kg_m3: tuple[Nonnegative,...]
    final_velocity_m_s: tuple[float,...]
    final_emission_column_kg_m2: tuple[Nonnegative,...]
    final_mixture_column_kg_m2: tuple[Nonnegative,...]
    source_active_at_window_end: bool
    numerical_diffusion_present: Literal[True] = True
    physical_validation_claim: Literal[False] = False

    @model_validator(mode="after")
    def ledger(self):
        n=len(self.sample_times_s)
        arrays=(self.cumulative_source_mass_kg,self.domain_emission_mass_kg,self.escaped_emission_mass_kg,
            self.domain_mixture_mass_kg,self.escaped_mixture_mass_kg,self.entrained_air_mass_kg,
            self.emission_roundoff_correction_kg,self.mixture_roundoff_correction_kg)
        if n<2 or any(len(v)!=n for v in arrays) or any(b<=a for a,b in zip(self.sample_times_s,self.sample_times_s[1:])):
            raise ValueError("coupled output ledger arrays/clock invalid")
        scale=max(self.cumulative_source_mass_kg[-1],1e-30)
        gas=max(abs(s+c-d-e) for s,c,d,e in zip(self.cumulative_source_mass_kg,self.emission_roundoff_correction_kg,self.domain_emission_mass_kg,self.escaped_emission_mass_kg))/scale
        mix=max(abs(s+a+c-d-e) for s,a,c,d,e in zip(self.cumulative_source_mass_kg,self.entrained_air_mass_kg,self.mixture_roundoff_correction_kg,self.domain_mixture_mass_kg,self.escaped_mixture_mass_kg))/max(scale,self.entrained_air_mass_kg[-1])
        if max(gas,mix)>1e-8 or not math.isclose(gas,self.maximum_emission_mass_relative_residual,abs_tol=1e-12) or not math.isclose(mix,self.maximum_mixture_mass_relative_residual,abs_tol=1e-12):
            raise ValueError("coupled conservation ledger failed")
        if self.maximum_observed_cfl>.450000001 or self.maximum_absolute_roundoff_correction_kg>1e-9*max(scale,1.):
            raise ValueError("coupled numerical tolerance exceeded")
        nc=len(self.final_cell_centers_m)
        if nc<20 or any(len(v)!=nc for v in (self.final_layer_height_m,self.final_mixture_density_kg_m3,self.final_velocity_m_s,self.final_emission_column_kg_m2,self.final_mixture_column_kg_m2)):
            raise ValueError("coupled final grid arrays unpaired")
        for m,s,h,rho in zip(self.final_mixture_column_kg_m2,self.final_emission_column_kg_m2,self.final_layer_height_m,self.final_mixture_density_kg_m3):
            expected_h=s/self.pure_vapour_density_kg_m3+(m-s)/self.air_density_kg_m3
            expected_rho=m/h if h>0 else 0.
            if s>m or not math.isclose(h,expected_h,rel_tol=1e-10,abs_tol=1e-14) or not math.isclose(rho,expected_rho,rel_tol=1e-10,abs_tol=1e-14):
                raise ValueError("coupled final composition/volume closure failed")
        if not math.isclose(math.fsum(self.final_emission_column_kg_m2)*self.cell_plan_area_m2,self.domain_emission_mass_kg[-1],rel_tol=1e-10,abs_tol=1e-12) or not math.isclose(math.fsum(self.final_mixture_column_kg_m2)*self.cell_plan_area_m2,self.domain_mixture_mass_kg[-1],rel_tol=1e-10,abs_tol=1e-12):
            raise ValueError("coupled final field/domain ledger mismatch")
        if not self.histories or len({h.receptor_id for h in self.histories})!=len(self.histories):
            raise ValueError("coupled histories invalid")
        for h in self.histories:
            if len(h.concentration_kg_m3)!=n or len(h.volume_fraction)!=n:
                raise ValueError("coupled receptor/clock mismatch")
            peak=max(range(n),key=lambda i:h.concentration_kg_m3[i])
            integral=math.fsum((b-a)*(c+d)/2 for a,b,c,d in zip(self.sample_times_s,self.sample_times_s[1:],h.concentration_kg_m3,h.concentration_kg_m3[1:]))
            if h.sampled_peak_kg_m3!=h.concentration_kg_m3[peak] or h.sampled_peak_time_s!=self.sample_times_s[peak] or not math.isclose(integral,h.sampled_integral_kg_s_m3,rel_tol=1e-10,abs_tol=1e-12):
                raise ValueError("coupled receptor summary mismatch")
        return self


def state_fields(state,air_density,pure_density,gravity):
    """M,S,P per plan area -> h,rho,u,pressure,maximum wave speed.

    Isothermal additive volumes: h=S/rho_s+(M-S)/rho_a.
    Hydrostatic pressure above ambient: g*(rho-rho_a)*h^2/2.
    At fixed mass fraction p is quadratic in M, so a^2=2p/M.
    """
    import numpy as np
    m,s,p=state
    h=s/pure_density+(m-s)/air_density
    rho=np.divide(m,h,out=np.zeros_like(m),where=h>0)
    u=np.divide(p,m,out=np.zeros_like(m),where=m>1e-14)
    pressure=.5*gravity*(1-air_density/pure_density)*s*h
    speed=np.abs(u)+np.sqrt(np.divide(2*pressure,m,out=np.zeros_like(m),where=m>0))
    return h,rho,u,pressure,speed


def face_flux(state,air_density,pure_density,gravity,boundary):
    import numpy as np
    left=state[:,0].copy() if boundary=="reflecting" else np.zeros(3)
    right=state[:,-1].copy() if boundary=="reflecting" else np.zeros(3)
    if boundary=="reflecting":
        left[2]*=-1
        right[2]*=-1
    padded=np.column_stack((left,state,right))
    _,_,u,p,speed=state_fields(padded,air_density,pure_density,gravity)
    flux=padded*u
    flux[2]+=p
    waves=np.maximum(speed[:-1],speed[1:])
    return .5*(flux[:,:-1]+flux[:,1:])-.5*waves*(padded[:,1:]-padded[:,:-1]),float(np.max(waves))


def solve_coupled(inputs: CoupledInput) -> CoupledOutput:
    try:
        import numpy as np
    except ImportError as exc:
        raise ValueError("coupled solver requires optional numpy; no fallback") from exc
    x=CoupledInput.model_validate_json(inputs.model_dump_json())
    dx=(x.x_max_m-x.x_min_m)/x.cells
    cell_area=dx*x.width_m
    start=round((x.source_start_m-x.x_min_m)/dx)
    count=round(x.source.area_m2/cell_area)
    state=np.zeros((3,x.cells))
    rows=x.source.canonical_intervals()
    events=sorted({r.end_s for r in rows}|set(x.sample_times_s))
    clock=0.
    steps=0
    maxcfl=0.
    escaped_s=escaped_m=air_added=correction_s=correction_m=0.
    total_correction=0.
    ledger=[[] for _ in range(8)]
    concentrations=[[] for _ in x.receptors]
    fractions=[[] for _ in x.receptors]

    def record():
        h,rho,u,_,_=state_fields(state,x.air_density_kg_m3,x.pure_vapour_density_kg_m3,x.gravity_m_s2)
        vals=(x.source.cumulative_mass(clock),float(np.sum(state[1])*cell_area),escaped_s,
            float(np.sum(state[0])*cell_area),escaped_m,air_added,correction_s,correction_m)
        for v,series in zip(vals,ledger):
            series.append(v)
        for k,r in enumerate(x.receptors):
            i=min(x.cells-1,int((r.downwind_distance_m-x.x_min_m)/dx))
            active=h[i]>r.height_m and h[i]>1e-14
            concentrations[k].append(float(state[1,i]/h[i]) if active else 0.)
            fractions[k].append(float((state[1,i]/x.pure_vapour_density_kg_m3)/h[i]) if active else 0.)
    record()
    for target in x.sample_times_s[1:]:
        while clock<target:
            if steps>=x.maximum_steps:
                raise ValueError("coupled solver step budget exceeded; no result promoted")
            next_event=min(t for t in events if t>clock)
            dt=min(x.maximum_step_s,target-clock,next_event-clock)
            q=next((r.mass_rate_kg_s for r in rows if r.start_s<=clock<r.end_s),0.)
            for attempt in range(60):
                trial=state.copy()
                added=q*dt/(count*cell_area)
                trial[0,start:start+count]+=added
                trial[1,start:start+count]+=added
                trial[2,start:start+count]+=added*x.injection_velocity_m_s
                height,_,u,_,_=state_fields(trial,x.air_density_kg_m3,x.pure_vapour_density_kg_m3,x.gravity_m_s2)
                entrained=x.air_density_kg_m3*x.entrainment_coefficient*np.abs(x.wind_speed_m_s-u)*dt*(height>1e-12)
                trial[0]+=entrained
                trial[2]+=entrained*x.wind_speed_m_s
                if x.wind_relaxation_time_s is not None:
                    trial[2]=trial[0]*x.wind_speed_m_s+(trial[2]-trial[0]*x.wind_speed_m_s)*math.exp(-dt/x.wind_relaxation_time_s)
                flux,speed=face_flux(trial,x.air_density_kg_m3,x.pure_vapour_density_kg_m3,x.gravity_m_s2,x.boundary)
                observed=dt*speed/dx
                if observed>x.cfl*(1+1e-12):
                    dt*=min(.5,.9*x.cfl/observed)
                    continue
                updated=trial-dt/dx*(flux[:,1:]-flux[:,:-1])
                if not np.all(np.isfinite(updated)):
                    raise ValueError("coupled nonfinite numerical state")
                tolerance=1e-13*max(1.,float(np.max(trial[0])))
                if np.min(updated[1])< -tolerance or np.min(updated[0]-updated[1])< -tolerance:
                    dt*=.5
                    continue
                break
            else:
                raise ValueError("coupled positivity/CFL retry limit exceeded")
            old_m,old_s=updated[0].copy(),updated[1].copy()
            updated[0]=np.maximum(updated[0],0.)
            updated[1]=np.minimum(np.maximum(updated[1],0.),updated[0])
            delta_m=float(np.sum(updated[0]-old_m)*cell_area)
            delta_s=float(np.sum(updated[1]-old_s)*cell_area)
            total_correction+=float(np.sum(np.abs(updated[0]-old_m)+np.abs(updated[1]-old_s))*cell_area)
            correction_m+=delta_m
            correction_s+=delta_s
            escaped_m+=float(dt*x.width_m*(flux[0,-1]-flux[0,0]))
            escaped_s+=float(dt*x.width_m*(flux[1,-1]-flux[1,0]))
            air_added+=float(np.sum(entrained)*cell_area)
            state=updated
            clock+=dt
            # Exact event alignment is essential to PRISM left-held source mass.
            if math.isclose(clock,next_event,rel_tol=0.,abs_tol=1e-12):
                clock=next_event
            steps+=1
            maxcfl=max(maxcfl,observed)
        record()
    histories=[]
    for r,values,volume in zip(x.receptors,concentrations,fractions):
        peak=max(range(len(values)),key=values.__getitem__)
        tail="end_above_threshold" if values[-1]>=x.tail_threshold_kg_m3 else "end_below_threshold_peak_at_end" if peak==len(values)-1 else "end_below_threshold"
        histories.append(DenseHistory(receptor_id=r.id,concentration_kg_m3=tuple(values),volume_fraction=tuple(volume),sampled_peak_kg_m3=values[peak],
            sampled_peak_time_s=x.sample_times_s[peak],sampled_integral_kg_s_m3=math.fsum((b-a)*(c+d)/2 for a,b,c,d in zip(x.sample_times_s,x.sample_times_s[1:],values,values[1:])),tail_status=tail))
    emitted,domain_s,out_s,domain_m,out_m,air,corr_s,corr_m=ledger
    scale=max(emitted[-1],1e-30)
    gaserr=max(abs(s+c-d-e) for s,c,d,e in zip(emitted,corr_s,domain_s,out_s))/scale
    mixerr=max(abs(s+a+c-d-e) for s,a,c,d,e in zip(emitted,air,corr_m,domain_m,out_m))/max(scale,air[-1])
    h,rho,u,_,_=state_fields(state,x.air_density_kg_m3,x.pure_vapour_density_kg_m3,x.gravity_m_s2)
    return CoupledOutput(numpy_version=np.__version__,air_density_kg_m3=x.air_density_kg_m3,pure_vapour_density_kg_m3=x.pure_vapour_density_kg_m3,
        cell_plan_area_m2=cell_area,sample_times_s=x.sample_times_s,histories=tuple(histories),
        cumulative_source_mass_kg=tuple(emitted),domain_emission_mass_kg=tuple(domain_s),escaped_emission_mass_kg=tuple(out_s),
        domain_mixture_mass_kg=tuple(domain_m),escaped_mixture_mass_kg=tuple(out_m),entrained_air_mass_kg=tuple(air),
        emission_roundoff_correction_kg=tuple(corr_s),mixture_roundoff_correction_kg=tuple(corr_m),
        maximum_emission_mass_relative_residual=gaserr,maximum_mixture_mass_relative_residual=mixerr,
        maximum_absolute_roundoff_correction_kg=total_correction,maximum_observed_cfl=maxcfl,accepted_steps=steps,
        final_cell_centers_m=tuple(float(x.x_min_m+(i+.5)*dx) for i in range(x.cells)),final_layer_height_m=tuple(map(float,h)),
        final_mixture_density_kg_m3=tuple(map(float,rho)),final_velocity_m_s=tuple(map(float,u)),
        final_emission_column_kg_m2=tuple(map(float,state[1])),final_mixture_column_kg_m2=tuple(map(float,state[0])),
        source_active_at_window_end=x.source.mode=="continuous_through_window")
