# `source/gas`

Python: `ccps_consequence.source.gas`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Ideal gas, fixed stagnation state, short orifice; no real gas, two-phase or pipe model.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `area_m2` | number | required | m2 | exclusiveMinimum=0 |
| `upstream_pressure_pa_abs` | number | required | Pa_abs | exclusiveMinimum=0 |
| `downstream_pressure_pa_abs` | number | required | Pa_abs | exclusiveMinimum=0 |
| `temperature_k` | number | required | K | exclusiveMinimum=0 |
| `specific_gas_constant_j_kg_k` | number | required | J/kg/K | exclusiveMinimum=0 |
| `heat_capacity_ratio` | number | required | 1 | exclusiveMinimum=1; maximum=2 |
| `discharge_coefficient` | number | required | 1 | exclusiveMinimum=0; maximum=1 |
| `phase` | literal ideal_gas | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `mass_rate_kg_s` | number | required | kg/s | minimum=0 |
| `regime` | string | required | dimensionless / metadata / nested; see contract |  |

## Evidence and traceability

CCPS topic section identifiers: 2.1. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_gas_regimes_and_continuity`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
