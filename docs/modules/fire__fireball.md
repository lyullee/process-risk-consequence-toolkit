# `fire/fireball`

Python: `ccps_consequence.fire.fireball`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Public empirical size/duration only; caller supplies participating mass; 0 < mass <= 5e6 kg; no rupture, flash fraction, lift-off or pressurized-gas applicability claim.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `participating_mass_kg` | number | required | kg | exclusiveMinimum=0; maximum=5000000 |
| `mass_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `correlation` | literal noaa_2013_roberts_diameter_dutch_duration | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `diameter_m` | number | required | m | exclusiveMinimum=0 |
| `duration_s` | number | required | s | exclusiveMinimum=0 |

## Evidence and traceability

CCPS topic section identifiers: 3.4. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_fireball_public_correlations`.

Direct references:

- https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf#page=75
- https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf#page=76
- https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf#page=77

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
