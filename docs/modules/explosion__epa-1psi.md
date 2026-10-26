# `explosion/epa-1psi`

Python: `ccps_consequence.explosion.epa_one_psi`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

EPA 1999 C-1 worst-case screening: fixed 10% yield, 4.68 MJ/kg TNT energy, 1 psi endpoint only; not an arbitrary-pressure curve, confinement model or regulatory compliance determination.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `flammable_mass_kg` | number | required | kg | minimum=0 |
| `heat_of_combustion_j_kg` | number | required | J/kg | exclusiveMinimum=0 |
| `mass_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `applicability` | literal epa_1999_worst_case_vapour_cloud_1psi | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `equivalent_tnt_mass_kg` | number | required | kg | minimum=0 |
| `endpoint_distance_m` | number | required | m | minimum=0 |
| `endpoint_pressure_pa` | literal 6894.757293168 | default `6894.757293168` | Pa |  |
| `explosion_efficiency` | literal 0.1 | default `0.1` | 1 |  |
| `tnt_specific_energy_j_kg` | literal 4680000.0 | default `4680000.0` | J/kg |  |

## Evidence and traceability

CCPS topic section identifiers: 3.1,4.4. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_epa_one_psi_endpoint`.

Direct references:

- https://www.epa.gov/sites/default/files/2017-05/documents/oca-apds.pdf#page=19

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
