# `effects/probit`

Python: `ccps_consequence.effects.probit`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

User-supplied dimensionless-log convention and coefficients; no toxicity database or endpoint certification.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `normalized_dose_s` | number | required | s | minimum=0 |
| `reference_time_s` | number | required | s | exclusiveMinimum=0 |
| `intercept` | number | required | 1 |  |
| `slope` | number | required | 1 | exclusiveMinimum=0 |
| `normal_offset` | number | required | 1 |  |
| `coefficient_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `probability` | number | required | 1 | minimum=0; maximum=1 |

## Evidence and traceability

CCPS topic section identifiers: 4.1. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_dose_and_probit`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
