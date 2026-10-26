# `dispersion/slabx-release-history`

Python: `ccps_consequence.release_history.run_release_history`.

Execution: `optional_slabx_worker`. Coverage: `public_primitive_partial`.

## Purpose and limitations

Pinned SLABx constant ground-vapour segments; finite plume-to-puff and continuous-through-window modes. Pretransition growing-cloud reconstruction and independent segment superposition are explicit approximations, not a coupled arbitrary-rate solver. No jet momentum, droplets, LH2 corrections or cloud interaction.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `engine` | literal slabx | default `"slabx"` | dimensionless / metadata / nested; see contract |  |
| `required_version` | literal 1.0.8 | default `"1.0.8"` | dimensionless / metadata / nested; see contract |  |
| `expected_engine_code_digest` | string | required | dimensionless / metadata / nested; see contract | pattern=^[a-f0-9]{64}$ |
| `source` | ReleaseHistory | required | dimensionless / metadata / nested; see contract |  |
| `substance` | DenseSubstance | required | dimensionless / metadata / nested; see contract |  |
| `atmosphere` | DenseAtmosphere | required | dimensionless / metadata / nested; see contract |  |
| `receptors` | array[DenseReceptor] | required | dimensionless / metadata / nested; see contract | minItems=1; maxItems=32 |
| `sample_times_s` | array[number] | required | s | minItems=2; maxItems=2001 |
| `simulation_end_s` | number | required | s | exclusiveMinimum=0; maximum=86400 |
| `native_puff_steps` | integer | default `240` | dimensionless / metadata / nested; see contract | minimum=80; maximum=2000 |
| `timeout_s` | number | default `60.0` | s | exclusiveMinimum=0; maximum=300 |
| `tail_threshold_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `applicability` | literal left_held_ground_vapour_release_history | required | dimensionless / metadata / nested; see contract |  |
| `plume_distance_limit_m` | number | required | m | exclusiveMinimum=0; maximum=100000 |
| `coupling` | literal independent_constant_segments_no_cloud_interaction | required | dimensionless / metadata / nested; see contract |  |
| `pretransition_reconstruction` | literal mass_normalized_quasi_steady_growing_cloud | required | dimensionless / metadata / nested; see contract |  |

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
| `cumulative_emitted_mass_kg` | array[number] | required | kg |  |
| `reconstructed_cloud_mass_kg` | array[number] | required | kg |  |
| `source_mass_within_window_kg` | number | required | kg | exclusiveMinimum=0 |
| `maximum_reconstruction_mass_relative_residual` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `segments` | array[SegmentLedger] | required | dimensionless / metadata / nested; see contract |  |
| `source_active_at_window_end` | boolean | required | dimensionless / metadata / nested; see contract |  |
| `coupling` | literal independent_constant_segments_no_cloud_interaction | default `"independent_constant_segments_no_cloud_interaction"` | dimensionless / metadata / nested; see contract |  |
| `reconstruction` | literal finite_growing_cloud_native_puff_or_continuous_conservative_filling_plume | default `"finite_growing_cloud_native_puff_or_continuous_conservative_filling_plume"` | dimensionless / metadata / nested; see contract |  |
| `physical_validation_claim` | literal False | default `false` | dimensionless / metadata / nested; see contract |  |

## Evidence and traceability

CCPS topic section identifiers: 2.3.2,4.2. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_release_history.py::test_real_finite_plume_to_puff`.

Direct references:

- https://www.epa.gov/scram/air-quality-dispersion-modeling-alternative-models#slab
- https://github.com/lyullee/slabx
- Ermak 1990 equations 29-30; own mass-normalized quasi-steady pretransition closure

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
