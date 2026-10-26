# `dispersion/puff`

Python: `ccps_consequence.dispersion.puff`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Passive instantaneous puff with ground reflection; supplied sigmas; no dense gas or deposition.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `mass_kg` | number | required | kg | minimum=0 |
| `downwind_distance_m` | number | required | m |  |
| `crosswind_distance_m` | number | required | m |  |
| `receptor_height_m` | number | required | m | minimum=0 |
| `release_height_m` | number | required | m | minimum=0 |
| `wind_speed_m_s` | number | required | m/s | exclusiveMinimum=0 |
| `elapsed_s` | number | required | s | exclusiveMinimum=0 |
| `sigma_x_m` | number | required | m | exclusiveMinimum=0 |
| `sigma_y_m` | number | required | m | exclusiveMinimum=0 |
| `sigma_z_m` | number | required | m | exclusiveMinimum=0 |
| `sigma_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `applicability` | literal passive_instantaneous_open_terrain | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `concentration_kg_m3` | number | required | kg/m3 | minimum=0 |

## Evidence and traceability

CCPS topic section identifiers: 2.3.1. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_gaussian_identities`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
