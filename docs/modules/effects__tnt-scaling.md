# `effects/tnt-scaling`

Python: `ccps_consequence.effects.tnt`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Energy equivalence and scaled distance only; no blast pressure curve, congestion, confinement or impulse.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `flammable_mass_kg` | number | required | kg | minimum=0 |
| `heat_of_combustion_j_kg` | number | required | J/kg | exclusiveMinimum=0 |
| `explosion_efficiency` | number | required | 1 | minimum=0; maximum=1 |
| `tnt_specific_energy_j_kg` | number | required | J/kg | exclusiveMinimum=0 |
| `distance_m` | number | required | m | exclusiveMinimum=0 |
| `efficiency_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `equivalent_tnt_mass_kg` | number | required | kg | minimum=0 |
| `scaled_distance_m_kg_third` | number or null | required | m/kg^(1/3) |  |

## Evidence and traceability

CCPS topic section identifiers: 3.1. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_tnt_and_threshold`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
