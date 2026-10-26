# `fire/sphere-radiation`

Python: `ccps_consequence.fire.sphere`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Ground-tangent sphere and ground-level facing vertical receptor, horizontal distance > radius only; no shielding, lift-off or automatic emissive power.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `diameter_m` | number | required | m | exclusiveMinimum=0 |
| `horizontal_distance_m` | number | required | m | exclusiveMinimum=0 |
| `surface_emissive_power_w_m2` | number | required | W/m2 | minimum=0 |
| `transmissivity` | number | required | 1 | minimum=0; maximum=1 |
| `emissive_power_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `geometry` | literal ground_tangent_sphere_ground_level_vertical_receptor | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `view_factor` | number | required | 1 | minimum=0; maximum=1 |
| `heat_flux_w_m2` | number | required | W/m2 | minimum=0 |

## Evidence and traceability

CCPS topic section identifiers: 3.4,4.3. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_sphere_radiation_geometry`.

Direct references:

- https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf#page=77

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
