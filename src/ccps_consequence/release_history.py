# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Left-held source histories and explicit independent-segment SLAB boundary."""
from __future__ import annotations
import json
import math
from typing import Annotated, Literal
from pydantic import Field, model_validator
from .contracts import Model, Name, SHA256, Positive, Nonnegative, digest
from .dense import DenseInput, DenseHistory, DenseEngineError, _call


class ReleaseInterval(Model):
    start_s: Nonnegative
    end_s: Positive
    mass_rate_kg_s: Nonnegative

    @model_validator(mode="after")
    def ordered(self):
        if self.end_s <= self.start_s:
            raise ValueError("release interval end must exceed start")
        return self


class ReleaseHistory(Model):
    schema_version: Literal["ccps.release-history.v1"] = "ccps.release-history.v1"
    asset_id: Name
    scenario_id: Name
    operating_case_id: Name
    origin: Literal["prism", "user_supplied"]
    source_digest: SHA256
    source_code_digest: SHA256
    evidence_ids: tuple[Name, ...]
    mode: Literal["finite", "continuous_through_window"]
    intervals: Annotated[tuple[ReleaseInterval, ...], Field(min_length=1, max_length=128)]
    declared_mass_within_history_kg: Positive
    area_m2: Positive
    temperature_k: Positive
    qualification_basis: Name
    boundary: Literal["qualified_ground_level_thermalized_pure_vapour"]

    @model_validator(mode="after")
    def ledger(self):
        if self.intervals[0].start_s != 0. or any(a.end_s != b.start_s for a,b in zip(self.intervals,self.intervals[1:])):
            raise ValueError("release history must start at zero and have contiguous intervals; gaps require explicit zero rate")
        if not self.evidence_ids or len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("release history requires unique evidence ids")
        total = math.fsum((r.end_s-r.start_s)*r.mass_rate_kg_s for r in self.intervals)
        if not math.isclose(total,self.declared_mass_within_history_kg,rel_tol=1e-10,abs_tol=1e-12):
            raise ValueError("release history integrated mass differs from declared mass")
        if self.mode == "continuous_through_window" and self.intervals[-1].mass_rate_kg_s <= 0:
            raise ValueError("continuous history requires positive final rate")
        return self

    def cumulative_mass(self, at_s):
        return math.fsum(max(0.,min(at_s,r.end_s)-r.start_s)*r.mass_rate_kg_s for r in self.intervals)

    def canonical_intervals(self):
        """Merge adjacent identical rates: arbitrary source sampling cannot create clouds."""
        rows = []
        for row in self.intervals:
            if rows and rows[-1].mass_rate_kg_s == row.mass_rate_kg_s:
                rows[-1] = ReleaseInterval(start_s=rows[-1].start_s,end_s=row.end_s,mass_rate_kg_s=row.mass_rate_kg_s)
            else:
                rows.append(row)
        return tuple(rows)


class ReleaseHistoryInput(DenseInput):
    source: ReleaseHistory
    applicability: Literal["left_held_ground_vapour_release_history"]
    plume_distance_limit_m: Annotated[float, Field(gt=0,le=100000)]
    coupling: Literal["independent_constant_segments_no_cloud_interaction"]
    pretransition_reconstruction: Literal["mass_normalized_quasi_steady_growing_cloud"]

    @model_validator(mode="after")
    def source_boundary(self):
        if self.source.temperature_k != self.substance.normal_boiling_temperature_k:
            raise ValueError("native ground source requires supplied boundary at normal boiling temperature")
        end = self.source.intervals[-1].end_s
        if self.source.mode == "finite" and end >= self.simulation_end_s:
            raise ValueError("finite history must stop before simulation end to resolve post-release puff")
        if self.source.mode == "continuous_through_window" and end != self.simulation_end_s:
            raise ValueError("continuous history must cover the whole observation window")
        if len([r for r in self.source.canonical_intervals() if r.mass_rate_kg_s>0])>8:
            raise ValueError("at most eight positive canonical source segments supported")
        return self


class SegmentLedger(Model):
    start_s: Nonnegative
    stop_s: Positive
    rate_kg_s: Positive
    mode: Literal["finite", "continuous_through_window"]
    source_mass_within_window_kg: Positive
    transition_time_s: Nonnegative | None
    transition_x_m: float | None
    native_final_time_s: Nonnegative
    used_source_area_m2: Positive
    maximum_puff_mass_relative_residual: Nonnegative
    maximum_plume_flux_relative_residual: Nonnegative
    transition_mass_relative_residual: Nonnegative
    native_transition_flux_relative_residual: Nonnegative
    native_duplicate_clock_rows_removed: Annotated[int,Field(ge=0)] = 0
    native_times_s: tuple[Nonnegative,...]
    native_clock_kind: Literal["plume_twice_integrated_mass_over_rate", "plume_release_clock_then_puff"]
    native_modes: tuple[Literal["plume","puff"],...]
    native_center_x_m: tuple[float,...]
    accounted_emission_mass_kg: tuple[Nonnegative,...]


class ReleaseHistoryOutput(Model):
    engine: Literal["slabx"] = "slabx"
    engine_version: Literal["1.0.8"] = "1.0.8"
    engine_code_digest: SHA256
    dependency_versions: dict[str, Name]
    request_digest: SHA256
    sample_times_s: tuple[Nonnegative,...]
    histories: tuple[DenseHistory,...]
    cumulative_emitted_mass_kg: tuple[Nonnegative,...]
    reconstructed_cloud_mass_kg: tuple[Nonnegative,...]
    source_mass_within_window_kg: Positive
    maximum_reconstruction_mass_relative_residual: Nonnegative
    segments: tuple[SegmentLedger,...]
    source_active_at_window_end: bool
    coupling: Literal["independent_constant_segments_no_cloud_interaction"] = "independent_constant_segments_no_cloud_interaction"
    reconstruction: Literal["finite_growing_cloud_native_puff_or_continuous_conservative_filling_plume"] = "finite_growing_cloud_native_puff_or_continuous_conservative_filling_plume"
    physical_validation_claim: Literal[False] = False

    @model_validator(mode="after")
    def arrays_and_mass(self):
        n=len(self.sample_times_s)
        if n<2 or any(b<=a for a,b in zip(self.sample_times_s,self.sample_times_s[1:])):
            raise ValueError("history output clock invalid")
        if len(self.cumulative_emitted_mass_kg)!=n or len(self.reconstructed_cloud_mass_kg)!=n:
            raise ValueError("history mass ledger array mismatch")
        if any(b<a for a,b in zip(self.cumulative_emitted_mass_kg,self.cumulative_emitted_mass_kg[1:])):
            raise ValueError("cumulative source mass decreases")
        if not self.histories or len({h.receptor_id for h in self.histories})!=len(self.histories):
            raise ValueError("history receptors invalid")
        for h in self.histories:
            if len(h.concentration_kg_m3)!=n or len(h.volume_fraction)!=n:
                raise ValueError("history receptor array mismatch")
            index=max(range(n),key=lambda i:h.concentration_kg_m3[i])
            integral=math.fsum((b-a)*(c+d)/2 for a,b,c,d in zip(self.sample_times_s,self.sample_times_s[1:],h.concentration_kg_m3,h.concentration_kg_m3[1:]))
            if h.sampled_peak_kg_m3!=h.concentration_kg_m3[index] or h.sampled_peak_time_s!=self.sample_times_s[index] or not math.isclose(integral,h.sampled_integral_kg_s_m3,rel_tol=1e-10,abs_tol=1e-12):
                raise ValueError("history summary invalid")
        residual=max(abs(a-b) for a,b in zip(self.cumulative_emitted_mass_kg,self.reconstructed_cloud_mass_kg))/self.source_mass_within_window_kg
        if residual>1e-5 or not math.isclose(residual,self.maximum_reconstruction_mass_relative_residual,abs_tol=1e-12):
            raise ValueError("reconstructed source mass ledger failed")
        if not math.isclose(self.cumulative_emitted_mass_kg[-1],self.source_mass_within_window_kg,rel_tol=1e-10):
            raise ValueError("final cumulative source mass mismatch")
        if not self.segments or not math.isclose(math.fsum(s.source_mass_within_window_kg for s in self.segments),self.source_mass_within_window_kg,rel_tol=1e-10):
            raise ValueError("segment mass sum mismatch")
        for s in self.segments:
            if not (len(s.native_times_s)==len(s.native_modes)==len(s.native_center_x_m)==len(s.accounted_emission_mass_kg)) or len(s.native_times_s)<2 or any(b<=a for a,b in zip(s.native_times_s,s.native_times_s[1:])):
                raise ValueError("native segment arrays/clock invalid")
            if not math.isclose(s.source_mass_within_window_kg,(s.stop_s-s.start_s)*s.rate_kg_s,rel_tol=1e-10):
                raise ValueError("segment source mass/rate/duration mismatch")
            if s.mode=="finite" and (s.transition_time_s!=s.stop_s or "puff" not in s.native_modes):
                raise ValueError("finite segment transition missing or misaligned")
            if s.mode=="continuous_through_window" and (s.transition_time_s is not None or "puff" in s.native_modes):
                raise ValueError("continuous segment incorrectly stopped")
            if max(s.maximum_puff_mass_relative_residual,s.maximum_plume_flux_relative_residual,s.transition_mass_relative_residual)>1e-5:
                raise ValueError("native segment conservation gate failed")
        return self


def run_release_history(inputs: ReleaseHistoryInput) -> ReleaseHistoryOutput:
    inputs=ReleaseHistoryInput.model_validate_json(inputs.model_dump_json())
    result=ReleaseHistoryOutput.model_validate_json(json.dumps(_call({"operation":"release_history","inputs":inputs.model_dump(mode="json")},inputs.timeout_s)))
    if result.request_digest!=inputs.digest() or result.engine_code_digest!=inputs.expected_engine_code_digest or result.sample_times_s!=inputs.sample_times_s:
        raise DenseEngineError("release history request/clock/engine binding mismatch")
    if tuple(h.receptor_id for h in result.histories)!=tuple(r.id for r in inputs.receptors):
        raise DenseEngineError("release history receptor binding mismatch")
    if result.source_active_at_window_end != (inputs.source.mode=="continuous_through_window"):
        raise DenseEngineError("release history final source state mismatch")
    expected=tuple(inputs.source.cumulative_mass(t) for t in inputs.sample_times_s)
    if any(not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12) for a,b in zip(expected,result.cumulative_emitted_mass_kg)):
        raise DenseEngineError("release history input/output mass mismatch")
    for h in result.histories:
        expected_tail="end_above_threshold" if h.concentration_kg_m3[-1]>=inputs.tail_threshold_kg_m3 else "end_below_threshold_peak_at_end" if h.sampled_peak_time_s==inputs.sample_times_s[-1] else "end_below_threshold"
        if h.tail_status!=expected_tail:
            raise DenseEngineError("release history tail binding mismatch")
    return result


def history_from_prism_rows(rows: list[dict], *, duration_s: float, mode: Literal["finite","continuous_through_window"],
    asset_id: str, scenario_id: str, operating_case_id: str, source_code_digest: str,
    expected_rows_digest: str, evidence_ids: tuple[str,...], area_m2: float, temperature_k: float,
    qualification_basis: str) -> ReleaseHistory:
    """Map PRISM chain-worker left-held rows, not raw external endpoint samples.

    Caller explicitly qualifies a thermalized ground boundary. Geometry and
    temperature are not inferred from nozzle areas or jet momentum. Only a
    gas-only partition is accepted; no liquid mass can silently disappear.
    """
    if digest(rows)!=expected_rows_digest:
        raise ValueError("PRISM rows digest mismatch")
    parsed=[PrismGasRow.model_validate_json(json.dumps({k:r[k] for k in PrismGasRow.model_fields})) for r in rows]
    if not parsed or parsed[0].time_s!=0. or any(b.time_s<=a.time_s for a,b in zip(parsed,parsed[1:])) or parsed[-1].time_s>duration_s:
        raise ValueError("PRISM rows must start at zero, increase and not exceed duration")
    intervals=[]
    for i,r in enumerate(parsed):
        if r.time_s==duration_s:
            continue  # endpoint is explicitly not a held interval
        stop=parsed[i+1].time_s if i+1<len(parsed) else duration_s
        intervals.append(ReleaseInterval(start_s=r.time_s,end_s=stop,mass_rate_kg_s=r.gas_mass_flow_kg_s))
    total=math.fsum((r.end_s-r.start_s)*r.mass_rate_kg_s for r in intervals)
    return ReleaseHistory(asset_id=asset_id,scenario_id=scenario_id,operating_case_id=operating_case_id,origin="prism",
        source_digest=expected_rows_digest,source_code_digest=source_code_digest,evidence_ids=evidence_ids,mode=mode,
        intervals=tuple(intervals),declared_mass_within_history_kg=total,area_m2=area_m2,temperature_k=temperature_k,
        qualification_basis=qualification_basis,boundary="qualified_ground_level_thermalized_pure_vapour")


class PrismGasRow(Model):
    time_s: Nonnegative
    total_mass_flow_kg_s: Nonnegative
    gas_mass_flow_kg_s: Nonnegative
    airborne_liquid_mass_flow_kg_s: Nonnegative
    ground_liquid_mass_flow_kg_s: Nonnegative
    mass_residual_kg_s: float

    @model_validator(mode="after")
    def partition(self):
        if self.airborne_liquid_mass_flow_kg_s!=0. or self.ground_liquid_mass_flow_kg_s!=0.:
            raise ValueError("PRISM pure-vapour mapping rejects airborne or ground liquid")
        if abs(self.mass_residual_kg_s)>1e-10 or not math.isclose(self.total_mass_flow_kg_s,self.gas_mass_flow_kg_s,rel_tol=1e-10,abs_tol=1e-12):
            raise ValueError("PRISM gas mass partition/residual failed")
        return self
