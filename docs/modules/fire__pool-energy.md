# `fire/pool-energy`

Python: `ccps_consequence.fire.pool`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Conservation wrapper with supplied burning flux, constant area and no replenishment; active HRR not an interval average; no burning-flux or flame-height correlation.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `area_m2` | number | required | m2 | exclusiveMinimum=0 |
| `burning_flux_kg_m2_s` | number | required | kg/m2/s | minimum=0 |
| `inventory_kg` | number | required | kg | minimum=0 |
| `duration_s` | number | required | s | minimum=0 |
| `heat_of_combustion_j_kg` | number | required | J/kg | exclusiveMinimum=0 |
| `combustion_efficiency` | number | required | 1 | minimum=0; maximum=1 |
| `burning_flux_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `applicability` | literal constant_area_constant_burning_flux_no_replenishment | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `mass_rate_kg_s` | number | required | kg/s | minimum=0 |
| `burned_mass_kg` | number | required | kg | minimum=0 |
| `remaining_mass_kg` | number | required | kg | minimum=0 |
| `effective_duration_s` | number | required | s | minimum=0 |
| `heat_release_rate_w` | number | required | W | minimum=0 |
| `released_energy_j` | number | required | J | minimum=0 |

## Evidence and traceability

CCPS topic section identifiers: 3.6. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_pool_energy_balance`.

Direct references:

- https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf#page=73
- Conservation of mass and energy; independently authored finite-inventory wrapper

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
