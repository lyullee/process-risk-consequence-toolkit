# `effects/radiation`

Python: `ccps_consequence.effects.radiation`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Far-field point-source screening only; no flame geometry, jet trajectory or near-field prediction.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `heat_release_rate_w` | number | required | W | minimum=0 |
| `radiative_fraction` | number | required | 1 | minimum=0; maximum=1 |
| `transmissivity` | number | required | 1 | minimum=0; maximum=1 |
| `distance_m` | number | required | m | exclusiveMinimum=0 |
| `applicability` | literal far_field_isotropic_point_source | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `heat_flux_w_m2` | number | required | W/m2 | minimum=0 |

## Evidence and traceability

CCPS topic section identifiers: 3.6,3.7,4.3. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_radiation_inverse_square`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
