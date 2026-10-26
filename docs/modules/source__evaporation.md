# `source/evaporation`

Python: `ccps_consequence.source.evaporation`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

User-supplied constant mass flux; no pool energy balance or spreading correlation.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `area_m2` | number | required | m2 | exclusiveMinimum=0 |
| `mass_flux_kg_m2_s` | number | required | kg/m2/s | minimum=0 |
| `duration_s` | number | required | s | minimum=0 |
| `inventory_kg` | number | required | kg | minimum=0 |
| `flux_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1 |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `released_mass_kg` | number | required | kg | minimum=0 |
| `remaining_mass_kg` | number | required | kg | minimum=0 |
| `effective_duration_s` | number | required | s | minimum=0 |

## Evidence and traceability

CCPS topic section identifiers: 2.2. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_flash_and_evaporation_mass_balance`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
