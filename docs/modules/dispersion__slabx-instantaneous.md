# `dispersion/slabx-instantaneous`

Python: `ccps_consequence.dense.run_dense`.

Execution: `optional_slabx_worker`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Optional pinned SLABx 1.0.8, instantaneous dense pure vapour at ground level only; flat terrain, no meander. Reconstructed ensemble histories, sampled peaks/integrals and finite-window tail diagnostics; no continuous source, droplets, LH2 correction or field validation.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `engine` | literal slabx | default `"slabx"` | dimensionless / metadata / nested; see contract |  |
| `required_version` | literal 1.0.8 | default `"1.0.8"` | dimensionless / metadata / nested; see contract |  |
| `expected_engine_code_digest` | string | required | dimensionless / metadata / nested; see contract | pattern=^[a-f0-9]{64}$ |
| `source` | DenseInventory | required | dimensionless / metadata / nested; see contract |  |
| `substance` | DenseSubstance | required | dimensionless / metadata / nested; see contract |  |
| `atmosphere` | DenseAtmosphere | required | dimensionless / metadata / nested; see contract |  |
| `receptors` | array[DenseReceptor] | required | dimensionless / metadata / nested; see contract | minItems=1; maxItems=32 |
| `sample_times_s` | array[number] | required | s | minItems=2; maxItems=2001 |
| `simulation_end_s` | number | required | s | exclusiveMinimum=0; maximum=86400 |
| `native_puff_steps` | integer | default `240` | dimensionless / metadata / nested; see contract | minimum=80; maximum=2000 |
| `timeout_s` | number | default `60.0` | s | exclusiveMinimum=0; maximum=300 |
| `tail_threshold_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `applicability` | literal instantaneous_ground_vapour_flat_terrain_no_meander | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `engine` | literal slabx | default `"slabx"` | dimensionless / metadata / nested; see contract |  |
| `engine_version` | literal 1.0.8 | default `"1.0.8"` | dimensionless / metadata / nested; see contract |  |
| `engine_code_digest` | string | required | dimensionless / metadata / nested; see contract | pattern=^[a-f0-9]{64}$ |
| `dependency_versions` | object | required | dimensionless / metadata / nested; see contract |  |
| `request_digest` | string | required | dimensionless / metadata / nested; see contract | pattern=^[a-f0-9]{64}$ |
| `sample_times_s` | array[number] | required | s |  |
| `histories` | array[DenseHistory] | required | dimensionless / metadata / nested; see contract |  |
| `native_times_s` | array[number] | required | s |  |
| `native_center_x_m` | array[number] | required | m |  |
| `native_emission_mass_kg` | array[number] | required | kg |  |
| `source_mass_kg` | number | required | kg | exclusiveMinimum=0 |
| `maximum_mass_relative_residual` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `initial_source_density_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `ambient_density_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `source_initial_height_m` | number | required | m | exclusiveMinimum=0 |
| `reconstruction` | literal slab_eq28_normalized_puff_similarity_linear_state_interpolation | default `"slab_eq28_normalized_puff_similarity_linear_state_interpolation"` | dimensionless / metadata / nested; see contract |  |
| `averaging` | literal instantaneous_ensemble_mean_no_meander | default `"instantaneous_ensemble_mean_no_meander"` | dimensionless / metadata / nested; see contract |  |
| `physical_validation_claim` | literal False | default `false` | dimensionless / metadata / nested; see contract |  |

## Evidence and traceability

CCPS topic section identifiers: 2.3.2,4.2. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_dense.py::test_real_dense_history`.

Direct references:

- https://www.epa.gov/scram/air-quality-dispersion-modeling-alternative-models#slab
- https://github.com/lyullee/slabx
- Ermak 1990 UCRL-MA-105607 sections 2.3.2 and 2.4, equations 15-28; normalized similarity reconstruction

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
