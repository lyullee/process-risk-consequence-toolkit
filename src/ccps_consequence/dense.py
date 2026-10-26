# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Typed SLABx instantaneous-vapour boundary; engine imports stay in a worker."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
from typing import Annotated, Literal
from pydantic import Field, model_validator
from .contracts import Model, Name, SHA256, Positive, Nonnegative, Probability


class DenseInventory(Model):
    schema_version: Literal["ccps.instantaneous-source.v1"] = "ccps.instantaneous-source.v1"
    asset_id: Name
    scenario_id: Name
    operating_case_id: Name
    origin: Literal["prism", "api581", "user_supplied"]
    source_digest: SHA256
    source_code_digest: SHA256
    evidence_ids: tuple[Name, ...]
    release_kind: Literal["instantaneous_pure_vapour"]
    mass_kg: Positive
    area_m2: Positive
    temperature_k: Positive
    qualification_basis: Name

    @model_validator(mode="after")
    def evidence(self):
        if not self.evidence_ids or len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("instantaneous inventory requires nonempty unique evidence")
        return self


class DenseSubstance(Model):
    name: Name
    molecular_weight_kg_mol: Positive
    vapor_heat_capacity_j_kg_k: Positive
    liquid_heat_capacity_j_kg_k: Positive
    latent_heat_j_kg: Positive
    normal_boiling_temperature_k: Positive
    liquid_density_kg_m3: Positive
    property_basis: Name


class DenseAtmosphere(Model):
    wind_speed_m_s: Positive
    wind_reference_height_m: Positive
    temperature_k: Positive
    relative_humidity_fraction: Probability
    roughness_length_m: Positive
    stability: Literal["A", "B", "C", "D", "E", "F"]
    pressure_pa_abs: Literal[101325.0] = 101325.

    @model_validator(mode="after")
    def reference(self):
        if self.wind_reference_height_m <= self.roughness_length_m:
            raise ValueError("wind reference height must exceed roughness length")
        return self


class DenseReceptor(Model):
    id: Name
    downwind_distance_m: Nonnegative
    crosswind_distance_m: float
    height_m: Nonnegative


class DenseInput(Model):
    engine: Literal["slabx"] = "slabx"
    required_version: Literal["1.0.8"] = "1.0.8"
    expected_engine_code_digest: SHA256
    source: DenseInventory
    substance: DenseSubstance
    atmosphere: DenseAtmosphere
    receptors: Annotated[tuple[DenseReceptor, ...], Field(min_length=1, max_length=32)]
    sample_times_s: Annotated[tuple[Nonnegative, ...], Field(min_length=2, max_length=2001)]
    simulation_end_s: Annotated[float, Field(gt=0, le=86400)]
    native_puff_steps: Annotated[int, Field(ge=80, le=2000)] = 240
    timeout_s: Annotated[float, Field(gt=0, le=300)] = 60.
    tail_threshold_kg_m3: Positive
    applicability: Literal["instantaneous_ground_vapour_flat_terrain_no_meander"]

    @model_validator(mode="after")
    def limits(self):
        if len({r.id for r in self.receptors}) != len(self.receptors):
            raise ValueError("duplicate dense receptor id")
        if self.sample_times_s[0] != 0. or any(b <= a for a, b in zip(self.sample_times_s, self.sample_times_s[1:])):
            raise ValueError("sample times must start at zero and strictly increase")
        if self.sample_times_s[-1] != self.simulation_end_s:
            raise ValueError("sample history must end at simulation_end_s")
        if len(self.sample_times_s) * len(self.receptors) > 32000:
            raise ValueError("dense receptor/time product exceeds 32000")
        if self.source.temperature_k < self.substance.normal_boiling_temperature_k:
            raise ValueError("source temperature below normal boiling point; pure-vapour boundary unsupported")
        return self


class DenseHistory(Model):
    receptor_id: Name
    concentration_kg_m3: tuple[Nonnegative, ...]
    volume_fraction: tuple[Probability, ...]
    sampled_peak_kg_m3: Nonnegative
    sampled_peak_time_s: Nonnegative
    sampled_integral_kg_s_m3: Nonnegative
    tail_status: Literal["end_above_threshold", "end_below_threshold_peak_at_end", "end_below_threshold"]


class DenseOutput(Model):
    engine: Literal["slabx"] = "slabx"
    engine_version: Literal["1.0.8"] = "1.0.8"
    engine_code_digest: SHA256
    dependency_versions: dict[str, Name]
    request_digest: SHA256
    sample_times_s: tuple[Nonnegative, ...]
    histories: tuple[DenseHistory, ...]
    native_times_s: tuple[Nonnegative, ...]
    native_center_x_m: tuple[float, ...]
    native_emission_mass_kg: tuple[Positive, ...]
    source_mass_kg: Positive
    maximum_mass_relative_residual: Nonnegative
    initial_source_density_kg_m3: Positive
    ambient_density_kg_m3: Positive
    source_initial_height_m: Positive
    reconstruction: Literal["slab_eq28_normalized_puff_similarity_linear_state_interpolation"] = "slab_eq28_normalized_puff_similarity_linear_state_interpolation"
    averaging: Literal["instantaneous_ensemble_mean_no_meander"] = "instantaneous_ensemble_mean_no_meander"
    physical_validation_claim: Literal[False] = False

    @model_validator(mode="after")
    def arrays(self):
        import math
        n = len(self.sample_times_s)
        if n < 2 or any(b <= a for a, b in zip(self.sample_times_s, self.sample_times_s[1:])):
            raise ValueError("invalid returned sample clock")
        if len(self.native_times_s) != len(self.native_center_x_m) or len(self.native_times_s) != len(self.native_emission_mass_kg):
            raise ValueError("native arrays are unpaired")
        if len(self.native_times_s) < 2 or any(b <= a for a, b in zip(self.native_times_s, self.native_times_s[1:])):
            raise ValueError("invalid native clock")
        if not self.histories or len({h.receptor_id for h in self.histories}) != len(self.histories):
            raise ValueError("missing or duplicate returned history")
        for h in self.histories:
            if len(h.concentration_kg_m3) != n or len(h.volume_fraction) != n:
                raise ValueError("history/clock shape mismatch")
            index = max(range(n), key=lambda i: h.concentration_kg_m3[i])
            integral = math.fsum((b-a) * (c+d) / 2 for a,b,c,d in zip(self.sample_times_s, self.sample_times_s[1:], h.concentration_kg_m3, h.concentration_kg_m3[1:]))
            if h.sampled_peak_kg_m3 != h.concentration_kg_m3[index] or h.sampled_peak_time_s != self.sample_times_s[index] or not math.isclose(h.sampled_integral_kg_s_m3, integral, rel_tol=1e-10, abs_tol=1e-14):
                raise ValueError("history summary mismatch")
        residual = max(abs(v / self.source_mass_kg - 1) for v in self.native_emission_mass_kg)
        if residual > 1e-5 or not math.isclose(residual, self.maximum_mass_relative_residual, abs_tol=1e-12):
            raise ValueError("native emitted-mass ledger failed")
        return self


class DenseEngineError(ValueError):
    pass


def _call(payload, timeout_s):
    own_src = str(Path(__file__).resolve().parents[1])
    bootstrap = "import sys; sys.path.insert(0,sys.argv[1]); from ccps_consequence.dense_worker import main; main()"
    try:
        process = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", bootstrap, own_src],
            input=json.dumps(payload, allow_nan=False), capture_output=True, encoding="utf-8", timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        raise DenseEngineError("SLABx worker timeout; no fallback") from exc
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise DenseEngineError("SLABx worker returned invalid JSON; no result promoted") from exc
    if process.returncode or not isinstance(result, dict) or "error" in result:
        raise DenseEngineError(str(result.get("error", "SLABx worker failed")) if isinstance(result, dict) else "invalid SLABx worker response")
    return result


def capabilities() -> dict:
    """Explicit process-isolated probe; no native imports in host."""
    return _call({"operation": "capabilities"}, 30.)


def run_dense(inputs: DenseInput) -> DenseOutput:
    inputs = DenseInput.model_validate_json(inputs.model_dump_json())
    result = DenseOutput.model_validate_json(json.dumps(_call({"operation": "run", "inputs": inputs.model_dump(mode="json")}, inputs.timeout_s)))
    if result.request_digest != inputs.digest() or result.engine_code_digest != inputs.expected_engine_code_digest:
        raise DenseEngineError("dense result request/engine binding mismatch")
    if result.sample_times_s != inputs.sample_times_s or tuple(h.receptor_id for h in result.histories) != tuple(r.id for r in inputs.receptors):
        raise DenseEngineError("dense result receptor/clock binding mismatch")
    if result.source_mass_kg != inputs.source.mass_kg:
        raise DenseEngineError("dense source mass binding mismatch")
    for h in result.histories:
        expected = "end_above_threshold" if h.concentration_kg_m3[-1] >= inputs.tail_threshold_kg_m3 else "end_below_threshold_peak_at_end" if h.sampled_peak_time_s == inputs.sample_times_s[-1] else "end_below_threshold"
        if h.tail_status != expected:
            raise DenseEngineError("dense tail status mismatch")
    return result


def history_dose_input(result: DenseOutput, receptor_id: str, *, exponent: float, reference_value: float):
    """Trapezoid of powered sampled concentration, represented as paired half intervals.

    This is a quadrature of samples, not an exact integral of the continuous
    solver or an assertion that a nonlinear transform commutes with averaging.
    """
    from .effects import DoseInput
    result = DenseOutput.model_validate_json(result.model_dump_json())
    row = next((h for h in result.histories if h.receptor_id == receptor_id), None)
    if row is None:
        raise ValueError("unknown dense receptor")
    values, durations = [], []
    for a,b,c,d in zip(result.sample_times_s,result.sample_times_s[1:],row.concentration_kg_m3,row.concentration_kg_m3[1:]):
        values.extend((c,d))
        durations.extend(((b-a)/2,(b-a)/2))
    return DoseInput(values=tuple(values), durations_s=tuple(durations), exponent=exponent,
                     reference_value=reference_value, reference_unit="kg/m3")


class HistoryDoseInput(Model):
    sample_times_s: tuple[Nonnegative, ...]
    histories: tuple[DenseHistory, ...]
    receptor_id: Name
    exponent: Positive
    reference_value_kg_m3: Positive
    integration: Literal["sampled_trapezoid"]

    @model_validator(mode="after")
    def paired(self):
        if len(self.sample_times_s) < 2 or any(b <= a for a,b in zip(self.sample_times_s,self.sample_times_s[1:])):
            raise ValueError("history dose requires increasing paired sample times")
        if len({h.receptor_id for h in self.histories}) != len(self.histories) or not any(h.receptor_id == self.receptor_id for h in self.histories):
            raise ValueError("history dose receptor missing or duplicated")
        if any(len(h.concentration_kg_m3) != len(self.sample_times_s) or len(h.volume_fraction) != len(self.sample_times_s) for h in self.histories):
            raise ValueError("history dose arrays unpaired")
        return self


class HistoryDoseOutput(Model):
    normalized_dose_s: Nonnegative
    observation_end_s: Nonnegative
    tail_status: Literal["end_above_threshold", "end_below_threshold_peak_at_end", "end_below_threshold"]


def integrate_history(inputs: HistoryDoseInput) -> HistoryDoseOutput:
    import math
    row = next(h for h in inputs.histories if h.receptor_id == inputs.receptor_id)
    powered = [(v/inputs.reference_value_kg_m3)**inputs.exponent for v in row.concentration_kg_m3]
    total = math.fsum((b-a)*(c+d)/2 for a,b,c,d in zip(inputs.sample_times_s,inputs.sample_times_s[1:],powered,powered[1:]))
    return HistoryDoseOutput(normalized_dose_s=total, observation_end_s=inputs.sample_times_s[-1],tail_status=row.tail_status)
