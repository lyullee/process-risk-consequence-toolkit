# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Optional separately installed PHA boundary; no PHA source is distributed."""
from __future__ import annotations
from ccps_consequence.contracts import Context
from ccps_consequence.risk import Frequency
from ccps_consequence.workflow import Workflow, run_workflow


def frequency_from_study(snapshot: StudySnapshot, scenario_id: str, *, context: Context,
                         analysis: dict | None = None) -> Frequency:
    from pha_core.application import analyze
    from pha_core.domain import StudySnapshot, digest
    from pha_core.storage import code_digest
    snapshot = StudySnapshot.model_validate_json(snapshot.model_dump_json())
    expected = analyze(snapshot)
    if analysis is not None:
        if analysis.get("input_digest") != snapshot.digest() or analysis.get("code_digest") != code_digest():
            raise ValueError("stale PHA baseline/code")
        for field in ("fta", "lopa_baseline", "sil", "lopa_proposed"):
            if analysis.get(field) != expected[field]:
                raise ValueError("PHA result differs from reproducible calculation")
    scenario = snapshot.index("scenarios")[scenario_id]
    if (context.asset_id, context.scenario_id, context.operating_case_id) != (
            scenario.asset_id, scenario.id, scenario.operating_case_id):
        raise ValueError("PHA/consequence context identity mismatch")
    if snapshot.mode == "synthetic" and context.mode != "synthetic":
        raise ValueError("synthetic PHA inputs cannot be promoted to engineering context")
    result = expected["lopa_proposed"][scenario_id]
    if result["endpoint"] != "loss_of_containment":
        raise ValueError("consequence analysis requires LOC frequency before ignition/occupancy")
    # Both the snapshot and calculation are identified, including upstream FTA/SIL credits.
    evidence_id = f"pha:{snapshot.digest()}"
    if not any(e.id == evidence_id and e.sha256 == snapshot.digest() and
               (snapshot.mode != "synthetic" or e.kind == "synthetic") for e in context.evidence):
        raise ValueError("context requires PHA snapshot evidence with matching digest and status")
    return Frequency(asset_id=scenario.asset_id, scenario_id=scenario.id,
        operating_case_id=scenario.operating_case_id,
        annual_frequency_per_year=result["residual_frequency_per_year"], origin="pha_core",
        source_digest=digest(expected), source_code_digest=expected["code_digest"],
        included_factor_ids=tuple(result["included_barrier_ids"] + result["included_transition_ids"]),
        evidence_ids=(evidence_id,))


def run_consequence_workflow(snapshot: StudySnapshot, scenario_id: str, workflow: Workflow) -> dict:
    """Bind a consequence DAG's risk steps to freshly recomputed PHA LOC frequency."""
    from pha_core.storage import code_digest
    workflow = Workflow.model_validate_json(workflow.model_dump_json())
    frequency = frequency_from_study(snapshot, scenario_id, context=workflow.context)
    risk_steps = [s for s in workflow.steps if s.calculation_id == "risk/conditional"]
    if not risk_steps:
        raise ValueError("PHA integrated workflow requires a risk/conditional step")
    for step in risk_steps:
        if step.inputs.get("frequency") != frequency.model_dump(mode="json"):
            raise ValueError("workflow must use exact recomputed PHA frequency contract")
    result = run_workflow(workflow)
    return {"schema_version": "pha.ccps-analysis.v1", "baseline_digest": snapshot.digest(),
            "pha_code_digest": code_digest(), "frequency": frequency.model_dump(mode="json"),
            "workflow": result.model_dump(mode="json"), "physical_validation_claim": False,
            "complete_facility_qra_claim": False}
