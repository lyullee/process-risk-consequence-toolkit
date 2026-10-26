# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Regenerate only authored schemas/metadata and synthetic workflow fixtures."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ccps_consequence import contract_schemas, calculation_catalog
from ccps_consequence.catalog import DEFERRED
from ccps_consequence.workflow import Workflow


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    schemas = contract_schemas()
    write(ROOT / "contracts/ccps.contracts.v1.schema.json", schemas)
    # Each schema below is independently consumable; the bundle above is an index.
    for key in ("receipt", "workflow", "workflow_result", "frequency", "external_source", "provider_request", "provider_result", "instantaneous_source", "dense_request", "dense_result", "release_history_source", "release_history_request", "release_history_result", "coupled_request", "coupled_result"):
        write(ROOT / f"contracts/ccps.{key}.v1.schema.json", {"$schema": "https://json-schema.org/draft/2020-12/schema", **schemas[key]})
    write(ROOT / "contracts/ccps.catalog.v1.json", {"calculations": calculation_catalog(), "deferred_sections": DEFERRED})
    workflow = dict(context=dict(asset_id="synthetic-tank", scenario_id="gas-leak", operating_case_id="normal",
        evidence=[dict(id="synthetic-input", kind="synthetic", citation="New analytic fixture", locator="examples/ccps_screening.workflow.json")]), steps=[
        dict(id="gas", calculation_id="source/gas", inputs=dict(area_m2=.0001, upstream_pressure_pa_abs=600000.,
            downstream_pressure_pa_abs=100000., temperature_k=300., specific_gas_constant_j_kg_k=300., heat_capacity_ratio=1.3,
            discharge_coefficient=.6, phase="ideal_gas")),
        dict(id="inventory", calculation_id="source/inventory", inputs=dict(mass_rate_kg_s={"$ref": "gas.mass_rate_kg_s"}, duration_s=60., inventory_kg=100.)),
        dict(id="plume", calculation_id="dispersion/plume", inputs=dict(mass_rate_kg_s={"$ref": "gas.mass_rate_kg_s"}, wind_speed_m_s=3.,
            downwind_distance_m=60., crosswind_distance_m=0., receptor_height_m=0., release_height_m=0., sigma_y_m=10., sigma_z_m=5.,
            sigma_basis="Synthetic passive sigmas at 60m; no stability correlation", applicability="passive_steady_open_terrain")),
        dict(id="dose", calculation_id="effects/dose", inputs=dict(values=[{"$ref": "plume.concentration_kg_m3"}], durations_s=[10.],
            exponent=1., reference_value=.001, reference_unit="kg/m3")),
        dict(id="probit", calculation_id="effects/probit", inputs=dict(normalized_dose_s={"$ref": "dose.normalized_dose_s"},
            reference_time_s=1., intercept=0., slope=1., normal_offset=5., coefficient_basis="Synthetic coefficients; no real chemical endpoint"))])
    typed = Workflow.model_validate_json(json.dumps(workflow))
    write(ROOT / "examples/ccps_screening.workflow.json", typed.model_dump(mode="json"))
    fire_workflow = dict(context=workflow["context"], steps=[
        dict(id="fireball", calculation_id="fire/fireball", inputs=dict(participating_mass_kg=8., mass_basis="Synthetic participating fuel",
            correlation="noaa_2013_roberts_diameter_dutch_duration")),
        dict(id="sphere", calculation_id="fire/sphere-radiation", inputs=dict(diameter_m={"$ref": "fireball.diameter_m"},
            horizontal_distance_m=20., surface_emissive_power_w_m2=120000., transmissivity=.8, emissive_power_basis="Synthetic supplied power",
            geometry="ground_tangent_sphere_ground_level_vertical_receptor")),
        dict(id="solid", calculation_id="fire/solid-flame", inputs=dict(surface_emissive_power_w_m2=120000.,
            view_factor={"$ref": "sphere.view_factor"}, transmissivity=.8,
            emissive_power_basis="Synthetic supplied power", view_factor_basis="Explicit sphere geometry",
            applicability="supplied_solid_flame_geometry")),
        dict(id="thermal_dose", calculation_id="effects/dose", inputs=dict(values=[{"$ref": "sphere.heat_flux_w_m2"}],
            durations_s=[{"$ref": "fireball.duration_s"}], exponent=1., reference_value=1000., reference_unit="W/m2")),
        dict(id="pool", calculation_id="fire/pool-energy", inputs=dict(area_m2=10., burning_flux_kg_m2_s=.05, inventory_kg=100.,
            duration_s=100., heat_of_combustion_j_kg=30e6, combustion_efficiency=.9, burning_flux_basis="Synthetic supplied burning flux",
            applicability="constant_area_constant_burning_flux_no_replenishment")),
        dict(id="pool_flux", calculation_id="effects/radiation", inputs=dict(heat_release_rate_w={"$ref": "pool.heat_release_rate_w"},
            radiative_fraction=.2, transmissivity=.8, distance_m=20., applicability="far_field_isotropic_point_source")),
        dict(id="blast_endpoint", calculation_id="explosion/epa-1psi", inputs=dict(flammable_mass_kg=10., heat_of_combustion_j_kg=4_680_000.,
            mass_basis="Synthetic vapour cloud", applicability="epa_1999_worst_case_vapour_cloud_1psi")),
        dict(id="dense_screen", calculation_id="dispersion/richardson-screen", inputs=dict(cloud_density_kg_m3=3., air_density_kg_m3=1.2,
            characteristic_dimension_m=.2, friction_velocity_m_s=.3, gravity_m_s2=9.80665, characteristic_dimension_basis="Synthetic supplied height",
            applicability="noaa_2013_friction_richardson_screen"))])
    typed_fire = Workflow.model_validate_json(json.dumps(fire_workflow))
    fixture = typed_fire.model_dump(mode="json")
    fixture["context"]["evidence"][0]["locator"] = "examples/ccps_fire_explosion.workflow.json"
    write(ROOT / "examples/ccps_fire_explosion.workflow.json", fixture)
    lines = ["# CCPS calculation traceability", "", "Generated by `python scripts/build_ccps_contracts.py`.", "",
        "Section identifiers locate topics only. All routes are partial public primitives, not complete book implementations.", "",
        "| Calculation | CCPS topic section | Function | Direct analytic test |", "|---|---|---|---|"]
    for item in calculation_catalog():
        lines.append(f"| {item['calculation_id']} | {', '.join(item['sections'])} | `{item['python_path']}` | `{item['test']}` |")
    lines += ["", "## Public equation references", ""]
    for item in calculation_catalog():
        for ref in item["method_references"]:
            lines.append(f"- `{item['calculation_id']}`: {ref}")
    lines += ["", "Deferred external model boundaries:", ""]
    lines += [f"- Section {section}: `{reason}`" for section, reason in DEFERRED.items()]
    lines += ["", "Sections 2.1/2.2 also require external models for two-phase/transient discharge and full pool thermodynamics.",
              "Sections 3.1/3.6/3.7 and 4 are only partially covered; no proprietary curves or chemical coefficients are supplied.",
              "See CCPS_API.md for equations, scope, evidence and integration semantics.", ""]
    (ROOT / "docs/CCPS_TRACEABILITY.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
