# `fire/solid-flame`

Python: `ccps_consequence.fire.solid_flame`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Supplied emissive power, view factor and transmissivity only; no pool/jet flame geometry or fuel database.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `surface_emissive_power_w_m2` | number | required | W/m2 | minimum=0 |
| `view_factor` | number | required | 1 | minimum=0; maximum=1 |
| `transmissivity` | number | required | 1 | minimum=0; maximum=1 |
| `emissive_power_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `view_factor_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `applicability` | literal supplied_solid_flame_geometry | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `heat_flux_w_m2` | number | required | W/m2 | minimum=0 |

## Evidence and traceability

CCPS topic section identifiers: 3.4,3.6,3.7,4.3. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_solid_flame_bounds`.

Direct references:

- https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf#page=73

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
