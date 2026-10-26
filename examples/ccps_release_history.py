# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Authored synthetic PRISM-shaped rows, actual SLABx finite/continuous execution."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from ccps_consequence import Context, Evidence, calculate
from ccps_consequence.contracts import digest
from ccps_consequence.dense import capabilities
from ccps_consequence.release_history import history_from_prism_rows
from ccps_dense_history import example_inputs as instantaneous_inputs


def example_rows(mode="finite"):
    pairs=[(0.,.5),(20.,0.)] if mode=="finite" else [(0.,.5),(120.,.5)] if mode=="continuous_through_window" else [(0.,.5),(10.,.2),(25.,0.)]
    return [dict(time_s=t,total_mass_flow_kg_s=q,gas_mass_flow_kg_s=q,airborne_liquid_mass_flow_kg_s=0.,ground_liquid_mass_flow_kg_s=0.,mass_residual_kg_s=0.) for t,q in pairs]


def example_context():
    return Context(asset_id="synthetic-vessel",scenario_id="finite-release",operating_case_id="normal",
        evidence=(Evidence(id="synthetic-release",kind="synthetic",citation="Synthetic PRISM-shaped gas rows",locator="examples/ccps_release_history.py"),))


def example_inputs(engine_digest,mode="finite"):
    payload=instantaneous_inputs(engine_digest)
    rows=example_rows(mode)
    source=history_from_prism_rows(rows,duration_s=rows[-1]["time_s"],mode="continuous_through_window" if mode=="continuous_through_window" else "finite",
        asset_id="synthetic-vessel",scenario_id="finite-release",operating_case_id="normal",source_code_digest="0"*64,
        expected_rows_digest=digest(rows),evidence_ids=("synthetic-release",),area_m2=25.,temperature_k=230.,
        qualification_basis="Synthetic qualified ground thermalized boundary; rows are not an actual PRISM source execution")
    payload.update(source=source.model_dump(mode="json"),plume_distance_limit_m=1000.,
        coupling="independent_constant_segments_no_cloud_interaction",pretransition_reconstruction="mass_normalized_quasi_steady_growing_cloud",
        applicability="left_held_ground_vapour_release_history")
    return payload


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=["finite","continuous_through_window","variable"],default="finite")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    info=capabilities()
    if info["status"]!="available":
        raise SystemExit(info)
    receipt=calculate("dispersion/slabx-release-history",example_inputs(info["engine_code_digest"],args.mode),context=example_context())
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(receipt.model_dump_json(indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"mode":args.mode,"mass_kg":receipt.outputs["source_mass_within_window_kg"],
        "mass_relative_residual":receipt.outputs["maximum_reconstruction_mass_relative_residual"],
        "transitions":[s["transition_time_s"] for s in receipt.outputs["segments"]],
        "sampled_peaks_kg_m3":[h["sampled_peak_kg_m3"] for h in receipt.outputs["histories"]]},indent=2))


if __name__=="__main__":
    main()
