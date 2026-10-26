# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Discoverable pure Python API; HTTP is an optional PHA Core host."""
from .catalog import CALCULATIONS
from .contracts import Context, Model, Receipt, code_digest, digest


class UnsupportedCalculation(ValueError):
    pass


def calculate(calculation_id: str, inputs: Model | dict, *, context: Context) -> Receipt:
    if calculation_id not in CALCULATIONS:
        raise UnsupportedCalculation(f"unsupported calculation: {calculation_id}; no fallback model")
    calc = CALCULATIONS[calculation_id]
    # Revalidate model instances as well: model_copy(update=...) bypasses Pydantic validation.
    if isinstance(inputs, Model):
        if type(inputs) is not calc.input_type:
            raise TypeError(f"{calculation_id} requires {calc.input_type.__name__}")
        inputs = inputs.model_dump(mode="json")
    import json
    x = calc.input_type.model_validate_json(json.dumps(inputs, allow_nan=False))
    context = Context.model_validate_json(context.model_dump_json())
    if calculation_id == "risk/conditional":
        f = x.frequency
        if (f.asset_id, f.scenario_id, f.operating_case_id) != (context.asset_id, context.scenario_id, context.operating_case_id):
            raise ValueError("risk frequency/context identity mismatch")
        if not set(f.evidence_ids) <= {e.id for e in context.evidence}:
            raise ValueError("risk frequency evidence not resolved in context")
    if calculation_id in {"dispersion/slabx-instantaneous","dispersion/slabx-release-history","dispersion/coupled-layer-1d"}:
        s = x.source
        if (s.asset_id, s.scenario_id, s.operating_case_id) != (context.asset_id, context.scenario_id, context.operating_case_id):
            raise ValueError("dense source/context identity mismatch")
        if not set(s.evidence_ids) <= {e.id for e in context.evidence}:
            raise ValueError("dense source evidence not resolved in context")
    normalized = x.model_dump(mode="json")
    try:
        output = calc.output_type.model_validate_json(calc.function(x).model_dump_json()).model_dump(mode="json")
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError("input exceeds numerical range; no result promoted") from exc
    return Receipt(calculation_id=calculation_id, context=context, code_digest=code_digest(),
                   input_digest=digest(normalized), normalized_inputs=normalized, outputs=output,
                   output_digest=digest(output), sections=tuple(calc.section.split(",")),
                   evidence_ids=tuple(e.id for e in context.evidence), limitations=(calc.limitation,),
                   method_references=calc.method_references,
                   validation_level="research_numerical_tests" if calc.execution_kind=="coupled_research" else "native_engine_executed" if calc.execution_kind == "optional_slabx_worker" else "synthetic_analytic_tests")


def verify_receipt(receipt: Receipt) -> Receipt:
    """Recompute current native calculation; hashes alone are not authentication."""
    receipt = Receipt.model_validate_json(receipt.model_dump_json())
    if receipt.code_digest != code_digest():
        raise ValueError("stale CCPS code digest")
    expected = calculate(receipt.calculation_id, receipt.normalized_inputs, context=receipt.context)
    if receipt != expected:
        raise ValueError("receipt differs from reproducible calculation")
    return receipt
