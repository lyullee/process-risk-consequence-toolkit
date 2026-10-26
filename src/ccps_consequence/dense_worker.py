# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Fresh-process optional SLABx engine. No engine source or observations bundled."""
import contextlib
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import sys


def engine_info():
    try:
        version = importlib.metadata.version("slabx")
    except importlib.metadata.PackageNotFoundError:
        return {"engine": "slabx", "status": "missing", "required_version": "1.0.8"}
    if version != "1.0.8":
        return {"engine": "slabx", "status": "version_mismatch", "version": version, "required_version": "1.0.8"}
    import slabx
    root = Path(slabx.__file__).parent
    sha = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        sha.update(path.relative_to(root).as_posix().encode())
        sha.update(path.read_bytes())
    dependencies = {name: importlib.metadata.version(name) for name in ("numpy", "scipy")}
    return {"engine": "slabx", "status": "available", "version": version,
            "engine_code_digest": sha.hexdigest(), "dependencies": dependencies,
            "operation": "instantaneous_pure_vapour_receptor_histories"}


def execute(payload):
    import math
    import numpy as np
    from slabx.core.source import InstantaneousRelease
    from slabx.core.plume import run_dispersion
    from slabx.submodels.atmosphere import Atmosphere
    from slabx.thermo.base import Substance, LegacyThermo, water_backend
    from .dense import DenseInput, DenseOutput, DenseHistory
    from .dense_profile import normalized_profile
    x = DenseInput.model_validate_json(json.dumps(payload))
    info = engine_info()
    if info["status"] != "available" or info["engine_code_digest"] != x.expected_engine_code_digest:
        raise ValueError("SLABx missing, unsupported version or pinned source fingerprint mismatch; no fallback")
    s, a = x.substance, x.atmosphere
    substance = Substance(name=s.name, mw=s.molecular_weight_kg_mol, cp_vapour=s.vapor_heat_capacity_j_kg_k,
        cp_liquid=s.liquid_heat_capacity_j_kg_k, dh_vap=s.latent_heat_j_kg,
        T_boil=s.normal_boiling_temperature_k, rho_liquid=s.liquid_density_kg_m3)
    atm = Atmosphere(u_ref=a.wind_speed_m_s, z_ref=a.wind_reference_height_m, T=a.temperature_k,
        rh=a.relative_humidity_fraction*100, z0=a.roughness_length_m, stability=a.stability, p=a.pressure_pa_abs)
    source = InstantaneousRelease(substance=substance, rate=0., duration=0., area=x.source.area_m2,
        mass=x.source.mass_kg, T_source=x.source.temperature_k, liquid_fraction=0., height=0.)
    density = source.rho_source(atm)
    if density <= atm.rho:
        raise ValueError("instantaneous dense mapping requires source density greater than ambient")
    if source.T != x.source.temperature_k:
        raise ValueError("native source temperature changed; no result promoted")
    initial_height = x.source.mass_kg / (density*x.source.area_m2)
    if initial_height >= atm.h_mix:
        raise ValueError("initial cloud exceeds native mixing height")
    # x_max is irrelevant to this all-puff path when t_max is explicit.
    traj, used = run_dispersion(source, atm, LegacyThermo(substance), water_backend(),
        x_max=1., t_max=x.simulation_end_s, n_puff_steps=x.native_puff_steps)
    arrays = [traj.t, traj.x, traj.rho, traj.mass_frac, traj.vol_frac, traj.b_half_x,
              traj.b_half, traj.h, traj.b_shape_x, traj.b_shape, traj.beta_x, traj.beta,
              traj.sigma_z, traj.z_c, traj.mass_frac_emission_liquid]
    if any(not np.all(np.isfinite(v)) for v in arrays) or not np.all(traj.is_puff):
        raise ValueError("native nonfinite trajectory or non-puff state")
    if np.any(np.diff(traj.t) <= 0) or traj.t[0] != 0. or not math.isclose(float(traj.t[-1]), x.simulation_end_s, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("native clock incomplete; no extrapolation")
    if np.max(traj.mass_frac_emission_liquid) > 1e-8:
        raise ValueError("native emission condensation outside pure-vapour mapping")
    cloud_volume = 4*traj.b_half_x*traj.b_half*traj.h
    masses = cloud_volume*traj.rho*traj.mass_frac
    residual = float(np.max(np.abs(masses/x.source.mass_kg-1)))
    if residual > 1e-5:
        raise ValueError("native emitted-mass ledger failed")
    for v in (traj.b_shape_x,traj.b_shape,traj.beta_x,traj.beta,traj.sigma_z):
        if np.any(v <= 0):
            raise ValueError("native nonpositive shape width")
    times = np.asarray(x.sample_times_s)
    def interp(v):
        return np.interp(times, traj.t, v)
    centers, heights = interp(traj.x), interp(traj.z_c)
    bx,by,bex,bey,sz = map(interp, (traj.b_shape_x,traj.b_shape,traj.beta_x,traj.beta,traj.sigma_z))
    mass_series, volume_series = interp(masses), interp(cloud_volume*traj.vol_frac)
    histories = []
    for receptor in x.receptors:
        values, fractions = [], []
        for i in range(len(times)):
            kernel = normalized_profile(dx=receptor.downwind_distance_m-centers[i], y=receptor.crosswind_distance_m,
                z=receptor.height_m, center_z=heights[i], bx=bx[i], by=by[i], beta_x=bex[i], beta_y=bey[i], sigma_z=sz[i])
            value, fraction = float(mass_series[i]*kernel), float(volume_series[i]*kernel)
            if not math.isfinite(value) or not math.isfinite(fraction) or not 0 <= fraction <= 1:
                raise ValueError("similarity profile outside physical volume-fraction bounds; receptor too near source or invalid state")
            values.append(value)
            fractions.append(fraction)
        peak_index = max(range(len(values)), key=values.__getitem__)
        tail = "end_above_threshold" if values[-1] >= x.tail_threshold_kg_m3 else "end_below_threshold_peak_at_end" if peak_index == len(values)-1 else "end_below_threshold"
        integral = math.fsum((b-a)*(c+d)/2 for a,b,c,d in zip(times,times[1:],values,values[1:]))
        histories.append(DenseHistory(receptor_id=receptor.id, concentration_kg_m3=tuple(values), volume_fraction=tuple(fractions),
            sampled_peak_kg_m3=values[peak_index], sampled_peak_time_s=float(times[peak_index]), sampled_integral_kg_s_m3=integral, tail_status=tail))
    if engine_info()["engine_code_digest"] != info["engine_code_digest"]:
        raise ValueError("SLABx source changed during run")
    return DenseOutput(engine_code_digest=info["engine_code_digest"], dependency_versions=info["dependencies"], request_digest=x.digest(), sample_times_s=x.sample_times_s,
        histories=tuple(histories), native_times_s=tuple(map(float,traj.t)), native_center_x_m=tuple(map(float,traj.x)),
        native_emission_mass_kg=tuple(map(float,masses)), source_mass_kg=x.source.mass_kg,
        maximum_mass_relative_residual=residual, initial_source_density_kg_m3=float(density),
        ambient_density_kg_m3=float(atm.rho), source_initial_height_m=float(initial_height)).model_dump(mode="json")


def main():
    try:
        payload = json.loads(sys.stdin.read())
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            if payload.get("operation") == "capabilities":
                result = engine_info()
            elif payload.get("operation") == "run":
                result = execute(payload["inputs"])
            elif payload.get("operation") == "release_history":
                from .release_history_worker import execute_release_history
                result = execute_release_history(payload["inputs"])
            else:
                raise ValueError("unknown dense worker operation")
        print(json.dumps(result, allow_nan=False))
    except Exception as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
