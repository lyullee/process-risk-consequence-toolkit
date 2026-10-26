# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Synthetic PRISM-shaped variable source, one shared isothermal PDE field."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from ccps_consequence import Context,Evidence,calculate
from ccps_consequence.contracts import digest
from ccps_consequence.release_history import history_from_prism_rows


def example_context():
    return Context(asset_id="synthetic-vessel",scenario_id="coupled-pulses",operating_case_id="normal",
        evidence=(Evidence(id="synthetic-coupled",kind="synthetic",citation="New isothermal coupled test",locator="examples/ccps_coupled_layer.py"),))


def example_inputs():
    rows=[dict(time_s=t,total_mass_flow_kg_s=q,gas_mass_flow_kg_s=q,airborne_liquid_mass_flow_kg_s=0.,ground_liquid_mass_flow_kg_s=0.,mass_residual_kg_s=0.) for t,q in [(0.,1.),(5.,0.),(8.,1.),(13.,0.)]]
    source=history_from_prism_rows(rows,duration_s=13.,mode="finite",asset_id="synthetic-vessel",scenario_id="coupled-pulses",operating_case_id="normal",
        source_code_digest="0"*64,expected_rows_digest=digest(rows),evidence_ids=("synthetic-coupled",),area_m2=50.,temperature_k=300.,
        qualification_basis="Synthetic isothermal thermalized gas boundary; not an actual PRISM source run")
    return dict(source=source.model_dump(mode="json"),temperature_k=300.,air_density_kg_m3=1.2,pure_vapour_density_kg_m3=2.4,
        density_basis="Synthetic constituent densities at 300K and same ambient pressure",x_min_m=-20.,x_max_m=180.,cells=200,width_m=5.,source_start_m=0.,
        wind_speed_m_s=2.,injection_velocity_m_s=0.,wind_relaxation_time_s=5.,entrainment_coefficient=.01,
        closure_basis="Synthetic entrainment and wind-relaxation parameters; no fitted field coefficients",gravity_m_s2=9.80665,
        maximum_step_s=.25,cfl=.4,sample_times_s=[float(i) for i in range(61)],
        receptors=[dict(id="R20",downwind_distance_m=20.,crosswind_distance_m=0.,height_m=0.),dict(id="R50",downwind_distance_m=50.,crosswind_distance_m=0.,height_m=0.)],
        tail_threshold_kg_m3=1e-5,boundary="open_vacuum",applicability="research_1d_isothermal_fixed_width_flat_ground_layer")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path)
    p.add_argument("--compare-independent",action="store_true")
    args=p.parse_args()
    receipt=calculate("dispersion/coupled-layer-1d",example_inputs(),context=example_context())
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(receipt.model_dump_json(indent=2)+"\n",encoding="utf-8")
    r=receipt.outputs
    summary={"source_mass_kg":r["cumulative_source_mass_kg"][-1],"domain_mass_kg":r["domain_emission_mass_kg"][-1],
        "escaped_mass_kg":r["escaped_emission_mass_kg"][-1],"gas_mass_relative_residual":r["maximum_emission_mass_relative_residual"],
        "mixture_mass_relative_residual":r["maximum_mixture_mass_relative_residual"],"steps":r["accepted_steps"],"maximum_cfl":r["maximum_observed_cfl"]}
    if args.compare_independent:
        import numpy as np
        columns=[]
        for index in (0,2):
            payload=example_inputs()
            payload["source"]["intervals"][index]["mass_rate_kg_s"]=0.
            payload["source"].update(declared_mass_within_history_kg=5.,origin="user_supplied",
                source_digest=digest(payload["source"]["intervals"]),qualification_basis="Derived synthetic one-pulse comparison input")
            columns.append(np.array(calculate("dispersion/coupled-layer-1d",payload,context=example_context()).outputs["final_emission_column_kg_m2"]))
        actual=np.asarray(r["final_emission_column_kg_m2"])
        summary["coupled_vs_independent_final_species_relative_l1"]=float(np.sum(np.abs(actual-columns[0]-columns[1]))/np.sum(actual))
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
