# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Synthetic dense gas, actual optional SLABx worker. No book example inputs.

python examples/ccps_dense_history.py --output artifacts/ccps-dense.json
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ccps_consequence import Context, Evidence, calculate
from ccps_consequence.dense import capabilities
from ccps_consequence.contracts import digest


def example_context():
    return Context(asset_id="synthetic-vessel", scenario_id="instantaneous-inventory", operating_case_id="normal",
        evidence=(Evidence(id="synthetic-dense", kind="synthetic", citation="New synthetic dense-vapour input", locator="examples/ccps_dense_history.py"),))


def example_inputs(engine_digest):
    source = dict(asset_id="synthetic-vessel", scenario_id="instantaneous-inventory", operating_case_id="normal",
        origin="user_supplied", source_digest=digest({"fixture": "new-synthetic-dense-inventory-v1"}), source_code_digest="0"*64,
        evidence_ids=["synthetic-dense"], release_kind="instantaneous_pure_vapour", mass_kg=20., area_m2=25., temperature_k=280.,
        qualification_basis="Synthetic instantaneous inventory, no upstream flow-history conversion")
    return dict(expected_engine_code_digest=engine_digest, source=source,
        substance=dict(name="synthetic-heavy-vapour", molecular_weight_kg_mol=.064, vapor_heat_capacity_j_kg_k=900.,
            liquid_heat_capacity_j_kg_k=1800., latent_heat_j_kg=300000., normal_boiling_temperature_k=230., liquid_density_kg_m3=1200.,
            property_basis="Synthetic constant properties; not a chemical database record"),
        atmosphere=dict(wind_speed_m_s=3., wind_reference_height_m=10., temperature_k=290., relative_humidity_fraction=.3,
            roughness_length_m=.03, stability="D"),
        receptors=[dict(id="R20", downwind_distance_m=20., crosswind_distance_m=0., height_m=0.),
                   dict(id="R60", downwind_distance_m=60., crosswind_distance_m=0., height_m=0.),
                   dict(id="R60-side", downwind_distance_m=60., crosswind_distance_m=10., height_m=0.)],
        sample_times_s=[float(i) for i in range(121)], simulation_end_s=120., native_puff_steps=240,
        tail_threshold_kg_m3=1e-6, applicability="instantaneous_ground_vapour_flat_terrain_no_meander")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    info = capabilities()
    if info["status"] != "available":
        raise SystemExit(f"SLABx unavailable: {info}")
    receipt = calculate("dispersion/slabx-instantaneous", example_inputs(info["engine_code_digest"]), context=example_context())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(receipt.model_dump_json(indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"calculation_id": receipt.calculation_id, "engine_code_digest": info["engine_code_digest"],
        "maximum_mass_relative_residual": receipt.outputs["maximum_mass_relative_residual"],
        "histories": [{k: v for k,v in h.items() if k not in {"concentration_kg_m3", "volume_fraction"}} for h in receipt.outputs["histories"]]}, indent=2))


if __name__ == "__main__":
    main()
