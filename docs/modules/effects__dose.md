# `effects/dose`

Python: `ccps_consequence.effects.dose`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Piecewise-constant normalized exposure; coefficients must use the same concentration/flux and time reference.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `values` | array[number] | required | dimensionless / metadata / nested; see contract |  |
| `durations_s` | array[number] | required | s |  |
| `exponent` | number | required | 1 | exclusiveMinimum=0 |
| `reference_value` | number | required | dimensionless / metadata / nested; see contract | exclusiveMinimum=0 |
| `reference_unit` | enum kg/m3, W/m2, Pa | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `normalized_dose_s` | number | required | s | minimum=0 |

## Evidence and traceability

CCPS topic section identifiers: 4.1,4.2,4.3. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_dose_and_probit`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
