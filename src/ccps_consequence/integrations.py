# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Explicit wire boundaries. External engines remain optional and separately owned.

These payloads attest identity and provenance, not authenticity or model validity.
No arbitrary Python path, subprocess command or silently selected engine is accepted.
"""
from typing import Literal, Protocol
from pydantic import model_validator
from .contracts import Model, Context, Name, SHA256, Nonnegative, Positive, Probability, digest


class ExternalSource(Model):
    schema_version: Literal["ccps.external-source.v1"] = "ccps.external-source.v1"
    asset_id: Name
    scenario_id: Name
    operating_case_id: Name
    origin: Literal["api581", "prism", "user_supplied"]
    source_digest: SHA256
    source_code_digest: SHA256
    evidence_ids: tuple[Name, ...]
    phase: Literal["vapour", "liquid", "two_phase"]
    mass_rate_kg_s: Nonnegative
    duration_s: Nonnegative
    released_mass_kg: Nonnegative
    history_basis: Literal["constant_rate"]

    @model_validator(mode="after")
    def mass(self):
        import math
        if not math.isclose(self.released_mass_kg, self.mass_rate_kg_s * self.duration_s, rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError("source mass/rate/duration mismatch")
        if not self.evidence_ids or len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("nonempty unique source evidence required")
        return self


class ProviderRequest(Model):
    schema_version: Literal["ccps.provider-request.v1"] = "ccps.provider-request.v1"
    context: Context
    source: ExternalSource
    engine: Literal["api581", "prism", "user_supplied"]
    model_id: Name
    expected_engine_code_digest: SHA256
    receptor_id: Name
    distance_m: Positive
    quantity: Literal["concentration_kg_m3", "heat_flux_w_m2", "overpressure_pa", "harm_probability"]
    settings: dict

    @model_validator(mode="after")
    def identity(self):
        if (self.context.asset_id, self.context.scenario_id, self.context.operating_case_id) != (
                self.source.asset_id, self.source.scenario_id, self.source.operating_case_id):
            raise ValueError("source/context identity mismatch")
        if not set(self.source.evidence_ids) <= {e.id for e in self.context.evidence}:
            raise ValueError("source evidence not resolved in context")
        return self


class ProviderResult(Model):
    schema_version: Literal["ccps.provider-result.v1"] = "ccps.provider-result.v1"
    request_digest: SHA256
    engine: Literal["api581", "prism", "user_supplied"]
    model_id: Name
    engine_version: Name
    engine_code_digest: SHA256
    receptor_id: Name
    quantity: Literal["concentration_kg_m3", "heat_flux_w_m2", "overpressure_pa", "harm_probability"]
    value: Nonnegative
    evidence_ids: tuple[Name, ...]
    limitations: tuple[Name, ...]
    validation_status: Literal["provider_reported_unverified"] = "provider_reported_unverified"

    @model_validator(mode="after")
    def probability(self):
        if self.quantity == "harm_probability" and self.value > 1:
            raise ValueError("harm probability must be in [0,1]")
        if not self.evidence_ids or not self.limitations:
            raise ValueError("provider evidence and limitations required")
        return self


class Provider(Protocol):
    def evaluate(self, request: ProviderRequest) -> ProviderResult: ...


def evaluate_provider(request: ProviderRequest, provider: Provider | None) -> ProviderResult:
    request = ProviderRequest.model_validate_json(request.model_dump_json())
    if provider is None:
        raise ValueError("external provider unavailable; no fallback model")
    result = ProviderResult.model_validate_json(provider.evaluate(request).model_dump_json())
    if (result.request_digest, result.engine, result.model_id, result.engine_code_digest, result.receptor_id, result.quantity) != (
            request.digest(), request.engine, request.model_id, request.expected_engine_code_digest, request.receptor_id, request.quantity):
        raise ValueError("provider response binding mismatch")
    if not set(result.evidence_ids) <= {e.id for e in request.context.evidence}:
        raise ValueError("provider evidence not resolved in context")
    return result


def api581_release_source(receipt: dict, *, context: Context, phase: Literal["vapour", "liquid"],
                          duration_s: float, expected_code_digest: str,
                          evidence_ids: tuple[str, ...]) -> ExternalSource:
    """Map an API-581 release/gas or release/liquid Python result, never COF area.

    Caller pins the trusted engine fingerprint. A wire receipt cannot establish
    authenticity; transport and licensed-engine execution remain caller-owned.
    Duration is explicit and assumes constant rate; no inventory inference.
    """
    calc = receipt.get("calculation_id")
    if calc not in {"release/gas", "release/liquid"}:
        raise ValueError("only API-581 gas/liquid release-rate receipts are supported")
    if (calc == "release/gas") != (phase == "vapour"):
        raise ValueError("API-581 calculation/phase mismatch")
    if receipt.get("code_fingerprint") != expected_code_digest:
        raise ValueError("API-581 engine fingerprint mismatch")
    if receipt.get("context", {}).get("asset_id") != context.asset_id:
        raise ValueError("API-581 asset mapping mismatch")
    if not receipt.get("engine_version") or not receipt.get("input_hash"):
        raise ValueError("API-581 receipt provenance missing")
    if not set(evidence_ids) <= {e.id for e in context.evidence}:
        raise ValueError("API-581 evidence not resolved in context")
    q = receipt.get("outputs", {}).get("mass_rate_kg_s")
    # Validate before multiplication, including negative/NaN/bool and duration.
    from .source import InventoryInput
    import json
    checked = InventoryInput.model_validate_json(json.dumps({"mass_rate_kg_s": q, "duration_s": duration_s, "inventory_kg": 0.}, allow_nan=False))
    return ExternalSource(asset_id=context.asset_id, scenario_id=context.scenario_id,
        operating_case_id=context.operating_case_id, origin="api581", source_digest=digest(receipt),
        source_code_digest=expected_code_digest, evidence_ids=evidence_ids, phase=phase,
        mass_rate_kg_s=checked.mass_rate_kg_s, duration_s=checked.duration_s,
        released_mass_kg=checked.mass_rate_kg_s * checked.duration_s, history_basis="constant_rate")
