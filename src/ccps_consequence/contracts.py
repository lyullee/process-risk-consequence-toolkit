# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Independent SI contracts; no plant data or licensed coefficient database."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Positive = Annotated[float, Field(gt=0)]
Nonnegative = Annotated[float, Field(ge=0)]
Probability = Annotated[float, Field(ge=0, le=1)]
Name = Annotated[str, Field(min_length=1, max_length=160)]
SHA256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def source_code_digest() -> str:
    sha = hashlib.sha256()
    root = Path(__file__).parent
    for path in sorted(root.glob("*.py")):
        sha.update(path.name.encode())
        sha.update(path.read_bytes())
    return sha.hexdigest()


_LOADED_CODE_DIGEST = source_code_digest()


def code_digest() -> str:
    if source_code_digest() != _LOADED_CODE_DIGEST:
        raise ValueError("CCPS source changed after startup; restart before calculation")
    return _LOADED_CODE_DIGEST


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True,
                              allow_inf_nan=False, validate_default=True)

    def digest(self):
        return digest(self.model_dump(mode="json"))


class Evidence(Model):
    id: Name
    kind: Literal["public_reference", "synthetic", "user_supplied"]
    citation: Name
    locator: Name
    sha256: SHA256 | None = None
    url: str | None = None


class Context(Model):
    asset_id: Name
    scenario_id: Name
    operating_case_id: Name
    mode: Literal["synthetic", "engineering_review_required"] = "synthetic"
    evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def unique_evidence(self):
        if len({e.id for e in self.evidence}) != len(self.evidence):
            raise ValueError("duplicate evidence id")
        if self.mode != "synthetic" and not any(e.kind != "synthetic" for e in self.evidence):
            raise ValueError("engineering inputs require non-synthetic evidence")
        return self


class Receipt(Model):
    schema_version: Literal["ccps.receipt.v1"] = "ccps.receipt.v1"
    calculation_id: Name
    engine_version: Literal["0.1.0"] = "0.1.0"
    context: Context
    code_digest: SHA256
    input_digest: SHA256
    normalized_inputs: dict
    outputs: dict
    output_digest: SHA256
    sections: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    method_references: tuple[str, ...] = ()
    validation_level: Literal["synthetic_analytic_tests", "native_engine_executed", "research_numerical_tests"] = "synthetic_analytic_tests"
    standard_conformity_claim: Literal[False] = False
    physical_validation_claim: Literal[False] = False
    complete_facility_qra_claim: Literal[False] = False

    @model_validator(mode="after")
    def hashes(self):
        if self.input_digest != digest(self.normalized_inputs) or self.output_digest != digest(self.outputs):
            raise ValueError("receipt payload/hash mismatch")
        if self.evidence_ids != tuple(e.id for e in self.context.evidence):
            raise ValueError("receipt evidence mismatch")
        return self
