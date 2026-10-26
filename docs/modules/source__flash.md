# `source/flash`

Python: `ccps_consequence.source.flash`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Constant-property sensible-heat approximation; no EOS, aerosol entrainment or two-phase flow.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `mass_kg` | number | required | kg | minimum=0 |
| `liquid_heat_capacity_j_kg_k` | number | required | J/kg/K | exclusiveMinimum=0 |
| `initial_temperature_k` | number | required | K | exclusiveMinimum=0 |
| `boiling_temperature_k` | number | required | K | exclusiveMinimum=0 |
| `latent_heat_j_kg` | number | required | J/kg | exclusiveMinimum=0 |
| `assumption` | literal constant_properties_sensible_heat_only | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `vapour_fraction` | number | required | 1 | minimum=0; maximum=1 |
| `vapour_mass_kg` | number | required | kg | minimum=0 |
| `liquid_mass_kg` | number | required | kg | minimum=0 |

## Evidence and traceability

CCPS topic section identifiers: 2.2. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_flash_and_evaporation_mass_balance`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
