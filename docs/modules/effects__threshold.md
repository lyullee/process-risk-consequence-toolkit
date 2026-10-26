# `effects/threshold`

Python: `ccps_consequence.effects.threshold`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Single receptor threshold comparison; not a contour, fatality probability or exposure-duration criterion.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `value` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `threshold` | number | required | dimensionless / metadata / nested; see contract | exclusiveMinimum=0 |
| `unit` | enum kg/m3, W/m2, Pa | required | dimensionless / metadata / nested; see contract |  |
| `criterion_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `exceeded` | boolean | required | dimensionless / metadata / nested; see contract |  |
| `ratio` | number | required | 1 | minimum=0 |

## Evidence and traceability

CCPS topic section identifiers: 4.2,4.3,4.4. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_tnt_and_threshold`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
