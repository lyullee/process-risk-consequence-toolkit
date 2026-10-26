# `source/inventory`

Python: `ccps_consequence.source.inventory`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Constant rate clipped to inventory; not a transient pressure or replenishment model.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `mass_rate_kg_s` | number | required | kg/s | minimum=0 |
| `duration_s` | number | required | s | minimum=0 |
| `inventory_kg` | number | required | kg | minimum=0 |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `released_mass_kg` | number | required | kg | minimum=0 |
| `remaining_mass_kg` | number | required | kg | minimum=0 |
| `effective_duration_s` | number | required | s | minimum=0 |

## Evidence and traceability

CCPS topic section identifiers: 2.1. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_liquid_and_inventory`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
