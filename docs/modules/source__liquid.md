# `source/liquid`

Python: `ccps_consequence.source.liquid`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Nonflashing incompressible orifice only; no pipe friction, hydrostatic head or transient depletion.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `area_m2` | number | required | m2 | exclusiveMinimum=0 |
| `density_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `upstream_pressure_pa_abs` | number | required | Pa_abs | exclusiveMinimum=0 |
| `downstream_pressure_pa_abs` | number | required | Pa_abs | exclusiveMinimum=0 |
| `discharge_coefficient` | number | required | 1 | exclusiveMinimum=0; maximum=1 |
| `phase` | literal incompressible_nonflashing_liquid | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `mass_rate_kg_s` | number | required | kg/s | minimum=0 |
| `regime` | string | required | dimensionless / metadata / nested; see contract |  |

## Evidence and traceability

CCPS topic section identifiers: 2.1. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_liquid_and_inventory`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
