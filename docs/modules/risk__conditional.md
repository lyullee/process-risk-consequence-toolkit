# `risk/conditional`

Python: `ccps_consequence.risk.risk`.

Execution: `native_primitive`. Coverage: `public_primitive_partial`.

## Purpose and limitations

One LOC scenario, one receptor and explicit branch partition; no facility total or dependence inference.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `frequency` | Frequency | required | dimensionless / metadata / nested; see contract |  |
| `receptor_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `branches` | array[Branch] | required | dimensionless / metadata / nested; see contract |  |
| `partition_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `mutually_exclusive_exhaustive` | literal True | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `receptor_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `annual_harm_frequency_per_year` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `branches` | array[BranchRisk] | required | dimensionless / metadata / nested; see contract |  |
| `complete_facility_qra_claim` | literal False | default `false` | dimensionless / metadata / nested; see contract |  |

## Evidence and traceability

CCPS topic section identifiers: 1.2. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_physics.py::test_risk_ownership_and_partition`.

Direct references:

- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
