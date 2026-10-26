# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Deterministic DAG execution, explicit named output references and lineage."""
from typing import Annotated, Literal
from pydantic import Field, model_validator
from .contracts import Model, Context, Receipt, SHA256, Name, digest, code_digest
from .api import calculate
from .catalog import CALCULATIONS

StepId = Annotated[str, Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")]

# Explicit wire dimensions for referenceable outputs and common input targets.
# No unit conversions or unlabelled floating-point links are inferred.
UNITS = {
    "mass_rate_kg_s": "kg/s", "released_mass_kg": "kg", "remaining_mass_kg": "kg",
    "inventory_kg": "kg", "mass_kg": "kg", "vapour_mass_kg": "kg", "liquid_mass_kg": "kg",
    "flammable_mass_kg": "kg", "equivalent_tnt_mass_kg": "kg", "effective_duration_s": "s",
    "duration_s": "s", "durations_s": "s", "reference_time_s": "s", "elapsed_s": "s",
    "normalized_dose_s": "s", "concentration_kg_m3": "kg/m3", "heat_flux_w_m2": "W/m2",
    "probability": "1", "harm_probability": "1", "conditional_probability": "1",
    "vapour_fraction": "1", "radiative_fraction": "1", "transmissivity": "1", "ratio": "1",
    "area_m2": "m2", "density_kg_m3": "kg/m3", "wind_speed_m_s": "m/s",
    "upstream_pressure_pa_abs": "Pa_abs", "downstream_pressure_pa_abs": "Pa_abs",
    "distance_m": "m", "downwind_distance_m": "m", "crosswind_distance_m": "m",
    "receptor_height_m": "m", "release_height_m": "m", "sigma_x_m": "m", "sigma_y_m": "m", "sigma_z_m": "m",
    "heat_release_rate_w": "W", "mass_flux_kg_m2_s": "kg/m2/s", "temperature_k": "K",
    "initial_temperature_k": "K", "boiling_temperature_k": "K", "exponent": "1", "normal_offset": "1",
    "intercept": "1", "slope": "1", "explosion_efficiency": "1", "discharge_coefficient": "1",
    "heat_capacity_ratio": "1", "scaled_distance_m_kg_third": "m/kg^(1/3)",
    "latent_heat_j_kg": "J/kg", "heat_of_combustion_j_kg": "J/kg", "tnt_specific_energy_j_kg": "J/kg",
    "specific_gas_constant_j_kg_k": "J/kg/K", "liquid_heat_capacity_j_kg_k": "J/kg/K",
    "participating_mass_kg": "kg", "burned_mass_kg": "kg", "diameter_m": "m", "horizontal_distance_m": "m",
    "endpoint_distance_m": "m", "endpoint_pressure_pa": "Pa", "burning_flux_kg_m2_s": "kg/m2/s",
    "surface_emissive_power_w_m2": "W/m2", "view_factor": "1", "combustion_efficiency": "1",
    "released_energy_j": "J", "cloud_density_kg_m3": "kg/m3", "air_density_kg_m3": "kg/m3",
    "characteristic_dimension_m": "m", "friction_velocity_m_s": "m/s", "gravity_m_s2": "m/s2",
    "reduced_gravity_m_s2": "m/s2", "friction_richardson_number": "1",
    "sample_times_s": "s", "observation_end_s": "s", "reference_value_kg_m3": "kg/m3",
}


def reference_targets(value, target=None):
    if isinstance(value, dict):
        if "$ref" in value:
            yield target, value["$ref"].split(".")
        else:
            for field, child in value.items():
                yield from reference_targets(child, field)
    elif isinstance(value, (tuple, list)):
        for child in value:
            yield from reference_targets(child, target)


def references(value):
    if isinstance(value, dict):
        if "$ref" in value:
            if set(value) != {"$ref"} or not isinstance(value["$ref"], str):
                raise ValueError("reference must be exactly {'$ref': 'step.output_field'}")
            parts = value["$ref"].split(".")
            if len(parts) != 2 or not all(parts):
                raise ValueError("reference needs step.output_field")
            yield tuple(parts)
        else:
            for child in value.values():
                yield from references(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from references(child)


class Step(Model):
    id: StepId
    calculation_id: Name
    inputs: dict


class Workflow(Model):
    schema_version: Literal["ccps.workflow.v1"] = "ccps.workflow.v1"
    context: Context
    steps: tuple[Step, ...]

    @model_validator(mode="after")
    def graph(self):
        index = {s.id: s for s in self.steps}
        if not self.steps or len(index) != len(self.steps):
            raise ValueError("nonempty unique workflow steps required")
        deps = {}
        for step in self.steps:
            if step.calculation_id not in CALCULATIONS:
                raise ValueError(f"unsupported calculation: {step.calculation_id}")
            deps[step.id] = set()
            for parent, field in references(step.inputs):
                if parent not in index:
                    raise ValueError(f"missing referenced step: {parent}")
                output_type = CALCULATIONS[index[parent].calculation_id].output_type
                if field not in output_type.model_fields:
                    raise ValueError(f"unknown output field: {parent}.{field}")
                deps[step.id].add(parent)
            for target, (parent, field) in reference_targets(step.inputs):
                expected_unit = UNITS.get(target)
                if target in {"values", "reference_value"} and step.calculation_id == "effects/dose":
                    expected_unit = step.inputs.get("reference_unit")
                if target in {"value", "threshold"} and step.calculation_id == "effects/threshold":
                    expected_unit = step.inputs.get("unit")
                actual_unit = UNITS.get(field)
                if actual_unit and expected_unit and actual_unit != expected_unit:
                    raise ValueError(f"reference unit mismatch: {parent}.{field} ({actual_unit}) -> {target} ({expected_unit})")
        done = set()
        while len(done) < len(index):
            ready = {key for key in index if key not in done and deps[key] <= done}
            if not ready:
                raise ValueError("workflow dependency cycle")
            done.update(ready)
        return self


class StepResult(Model):
    id: StepId
    dependency_receipt_digests: dict[str, SHA256]
    receipt: Receipt
    receipt_digest: SHA256

    @model_validator(mode="after")
    def integrity(self):
        if self.receipt_digest != self.receipt.digest():
            raise ValueError("step receipt digest mismatch")
        return self


class WorkflowResult(Model):
    schema_version: Literal["ccps.workflow-result.v1"] = "ccps.workflow-result.v1"
    workflow_digest: SHA256
    code_digest: SHA256
    steps: tuple[StepResult, ...]


class WorkflowError(ValueError):
    def __init__(self, step_id, message):
        self.step_id = step_id
        super().__init__(f"workflow step {step_id}: {message}; no workflow result promoted")


def run_workflow(workflow: Workflow) -> WorkflowResult:
    workflow = Workflow.model_validate_json(workflow.model_dump_json())
    completed = {}
    rows = []

    def resolve(value):
        if isinstance(value, dict):
            if "$ref" in value:
                parent, field = value["$ref"].split(".")
                return completed[parent].outputs[field]
            return {k: resolve(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [resolve(v) for v in value]
        return value

    fingerprint = code_digest()
    while len(completed) < len(workflow.steps):
        for step in workflow.steps:
            if step.id in completed:
                continue
            parents = {p for p, _ in references(step.inputs)}
            if not parents <= completed.keys():
                continue
            try:
                receipt = calculate(step.calculation_id, resolve(step.inputs), context=workflow.context)
            except (ValueError, TypeError) as exc:
                raise WorkflowError(step.id, str(exc)) from exc
            completed[step.id] = receipt
            rows.append(StepResult(id=step.id, dependency_receipt_digests={
                p: completed[p].digest() for p in sorted(parents)}, receipt=receipt, receipt_digest=receipt.digest()))
    if fingerprint != code_digest():
        raise ValueError("code changed during workflow; no result promoted")
    return WorkflowResult(workflow_digest=workflow.digest(), code_digest=fingerprint, steps=tuple(rows))
