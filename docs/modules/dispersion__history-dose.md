# `dispersion/history-dose`

Python: `ccps_consequence.dense.integrate_history`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Trapezoid quadrature of powered sampled concentrations over the supplied window only; no tail extrapolation, toxicity coefficients or exact unsampled peak/integral claim.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `sample_times_s` | array[number] | required | s |  |
| `histories` | array[DenseHistory] | required | dimensionless / metadata / nested; see contract |  |
| `receptor_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `exponent` | number | required | 1 | exclusiveMinimum=0 |
| `reference_value_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `integration` | literal sampled_trapezoid | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `normalized_dose_s` | number | required | s | minimum=0 |
| `observation_end_s` | number | required | s | minimum=0 |
| `tail_status` | enum end_above_threshold, end_below_threshold_peak_at_end, end_below_threshold | required | dimensionless / metadata / nested; see contract |  |

## Evidence and traceability

CCPS topic section identifiers: 4.1,4.2. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_dense.py::test_history_dose_trapezoid`.

Direct references:

- Independent trapezoid quadrature; normalized exposure integral

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
