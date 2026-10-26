# `dispersion/richardson-screen`

Python: `ccps_consequence.dispersion.richardson`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Friction Richardson diagnostic only; supplied characteristic dimension and friction velocity; no concentration solver or automatic Gaussian routing.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `cloud_density_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `air_density_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `characteristic_dimension_m` | number | required | m | exclusiveMinimum=0 |
| `friction_velocity_m_s` | number | required | m/s | exclusiveMinimum=0 |
| `gravity_m_s2` | number | required | m/s2 | exclusiveMinimum=0 |
| `characteristic_dimension_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `applicability` | literal noaa_2013_friction_richardson_screen | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `reduced_gravity_m_s2` | number | required | m/s2 |  |
| `friction_richardson_number` | number | required | 1 |  |
| `screening` | enum passive_candidate, dense_model_required, buoyant_review_required | required | dimensionless / metadata / nested; see contract |  |
| `concentration_prediction_available` | literal False | default `false` | dimensionless / metadata / nested; see contract |  |

## Evidence and traceability

CCPS topic section identifiers: 2.3.2. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_richardson_screen`.

Direct references:

- https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf#page=54
- https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf#page=55

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
