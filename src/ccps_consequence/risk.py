# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""A single LOC scenario's explicit, mutually exclusive conditional branches."""
import math
from typing import Literal
from pydantic import model_validator
from .contracts import Model, Name, SHA256, Nonnegative, Probability


class Frequency(Model):
    schema_version: Literal["ccps.frequency.v1"] = "ccps.frequency.v1"
    asset_id: Name
    scenario_id: Name
    operating_case_id: Name
    annual_frequency_per_year: Nonnegative
    endpoint: Literal["loss_of_containment"] = "loss_of_containment"
    origin: Literal["pha_core", "api581", "prism", "user_supplied"]
    source_digest: SHA256
    source_code_digest: SHA256
    included_factor_ids: tuple[Name, ...] = ()
    evidence_ids: tuple[Name, ...]

    @model_validator(mode="after")
    def unique(self):
        if len(set(self.included_factor_ids)) != len(self.included_factor_ids):
            raise ValueError("duplicate upstream factor")
        if not self.evidence_ids or len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("nonempty unique frequency evidence required")
        return self


class Factor(Model):
    id: Name
    probability: Probability
    kind: Literal["weather", "ignition", "occupancy", "conditional_harm", "other"]
    basis: Name


class Branch(Model):
    id: Name
    conditional_probability: Probability
    probability_basis: Name
    probability_factor_ids: tuple[Name, ...]
    harm_probability: Probability
    harm_factor_id: Name
    harm_basis: Name
    factors: tuple[Factor, ...] = ()


class RiskInput(Model):
    frequency: Frequency
    receptor_id: Name
    branches: tuple[Branch, ...]
    partition_basis: Name
    mutually_exclusive_exhaustive: Literal[True]

    @model_validator(mode="after")
    def partition(self):
        if not self.branches or len({b.id for b in self.branches}) != len(self.branches):
            raise ValueError("branches must have unique ids")
        if not math.isclose(math.fsum(b.conditional_probability for b in self.branches), 1., abs_tol=1e-10, rel_tol=0):
            raise ValueError("branch conditional probabilities must sum to one")
        for branch in self.branches:
            ids = branch.probability_factor_ids + (branch.harm_factor_id,) + tuple(f.id for f in branch.factors)
            if not branch.probability_factor_ids:
                raise ValueError("branch probability ownership ids required")
            if len(ids) != len(set(ids)) or set(ids) & set(self.frequency.included_factor_ids):
                raise ValueError("duplicate probability credit within branch or upstream")
        return self


class BranchRisk(Model):
    branch_id: Name
    annual_frequency_per_year: Nonnegative
    annual_harm_frequency_per_year: Nonnegative
    applied_factor_ids: tuple[Name, ...]


class RiskOutput(Model):
    receptor_id: Name
    annual_harm_frequency_per_year: Nonnegative
    branches: tuple[BranchRisk, ...]
    complete_facility_qra_claim: Literal[False] = False


def risk(x: RiskInput) -> RiskOutput:
    rows = []
    for b in x.branches:
        frequency = x.frequency.annual_frequency_per_year * b.conditional_probability
        harm = frequency * b.harm_probability * math.prod(f.probability for f in b.factors)
        rows.append(BranchRisk(branch_id=b.id, annual_frequency_per_year=frequency,
                               annual_harm_frequency_per_year=harm,
                               applied_factor_ids=x.frequency.included_factor_ids + b.probability_factor_ids +
                               (b.harm_factor_id,) + tuple(f.id for f in b.factors)))
    return RiskOutput(receptor_id=x.receptor_id, annual_harm_frequency_per_year=math.fsum(
        b.annual_harm_frequency_per_year for b in rows), branches=tuple(rows))
