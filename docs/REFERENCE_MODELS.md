# Nested input/output contracts

Generated definitions include every nested field used by registered calculations. JSON Schema relational limits also apply in Python.

## Branch

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `conditional_probability` | number | required | 1 | minimum=0; maximum=1 |
| `probability_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `probability_factor_ids` | array[string] | required | dimensionless / metadata / nested; see contract |  |
| `harm_probability` | number | required | 1 | minimum=0; maximum=1 |
| `harm_factor_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `harm_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `factors` | array[Factor] | default `[]` | dimensionless / metadata / nested; see contract |  |

## BranchRisk

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `branch_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `annual_frequency_per_year` | number | required | year^-1 | minimum=0 |
| `annual_harm_frequency_per_year` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `applied_factor_ids` | array[string] | required | dimensionless / metadata / nested; see contract |  |

## DenseAtmosphere

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `wind_speed_m_s` | number | required | m/s | exclusiveMinimum=0 |
| `wind_reference_height_m` | number | required | m | exclusiveMinimum=0 |
| `temperature_k` | number | required | K | exclusiveMinimum=0 |
| `relative_humidity_fraction` | number | required | dimensionless / metadata / nested; see contract | minimum=0; maximum=1 |
| `roughness_length_m` | number | required | m | exclusiveMinimum=0 |
| `stability` | enum A, B, C, D, E, F | required | dimensionless / metadata / nested; see contract |  |
| `pressure_pa_abs` | literal 101325.0 | default `101325.0` | Pa absolute |  |

## DenseHistory

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `receptor_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `concentration_kg_m3` | array[number] | required | kg/m3 |  |
| `volume_fraction` | array[number] | required | dimensionless / metadata / nested; see contract |  |
| `sampled_peak_kg_m3` | number | required | kg/m3 | minimum=0 |
| `sampled_peak_time_s` | number | required | s | minimum=0 |
| `sampled_integral_kg_s_m3` | number | required | kg*s/m3 | minimum=0 |
| `tail_status` | enum end_above_threshold, end_below_threshold_peak_at_end, end_below_threshold | required | dimensionless / metadata / nested; see contract |  |

## DenseInventory

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `schema_version` | literal ccps.instantaneous-source.v1 | default `"ccps.instantaneous-source.v1"` | dimensionless / metadata / nested; see contract |  |
| `asset_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `scenario_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `operating_case_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `origin` | enum prism, api581, user_supplied | required | dimensionless / metadata / nested; see contract |  |
| `source_digest` | string | required | dimensionless / metadata / nested; see contract | pattern=^[a-f0-9]{64}$ |
| `source_code_digest` | string | required | dimensionless / metadata / nested; see contract | pattern=^[a-f0-9]{64}$ |
| `evidence_ids` | array[string] | required | dimensionless / metadata / nested; see contract |  |
| `release_kind` | literal instantaneous_pure_vapour | required | dimensionless / metadata / nested; see contract |  |
| `mass_kg` | number | required | kg | exclusiveMinimum=0 |
| `area_m2` | number | required | m2 | exclusiveMinimum=0 |
| `temperature_k` | number | required | K | exclusiveMinimum=0 |
| `qualification_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |

## DenseReceptor

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `downwind_distance_m` | number | required | m | minimum=0 |
| `crosswind_distance_m` | number | required | m |  |
| `height_m` | number | required | m | minimum=0 |

## DenseSubstance

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `name` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `molecular_weight_kg_mol` | number | required | kg/mol | exclusiveMinimum=0 |
| `vapor_heat_capacity_j_kg_k` | number | required | J/kg/K | exclusiveMinimum=0 |
| `liquid_heat_capacity_j_kg_k` | number | required | J/kg/K | exclusiveMinimum=0 |
| `latent_heat_j_kg` | number | required | J/kg | exclusiveMinimum=0 |
| `normal_boiling_temperature_k` | number | required | K | exclusiveMinimum=0 |
| `liquid_density_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `property_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |

## Factor

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `probability` | number | required | 1 | minimum=0; maximum=1 |
| `kind` | enum weather, ignition, occupancy, conditional_harm, other | required | dimensionless / metadata / nested; see contract |  |
| `basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |

## Frequency

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `schema_version` | literal ccps.frequency.v1 | default `"ccps.frequency.v1"` | dimensionless / metadata / nested; see contract |  |
| `asset_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `scenario_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `operating_case_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `annual_frequency_per_year` | number | required | year^-1 | minimum=0 |
| `endpoint` | literal loss_of_containment | default `"loss_of_containment"` | dimensionless / metadata / nested; see contract |  |
| `origin` | enum pha_core, api581, prism, user_supplied | required | dimensionless / metadata / nested; see contract |  |
| `source_digest` | string | required | dimensionless / metadata / nested; see contract | pattern=^[a-f0-9]{64}$ |
| `source_code_digest` | string | required | dimensionless / metadata / nested; see contract | pattern=^[a-f0-9]{64}$ |
| `included_factor_ids` | array[string] | default `[]` | dimensionless / metadata / nested; see contract |  |
| `evidence_ids` | array[string] | required | dimensionless / metadata / nested; see contract |  |

## ReleaseHistory

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `schema_version` | literal ccps.release-history.v1 | default `"ccps.release-history.v1"` | dimensionless / metadata / nested; see contract |  |
| `asset_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `scenario_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `operating_case_id` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `origin` | enum prism, user_supplied | required | dimensionless / metadata / nested; see contract |  |
| `source_digest` | string | required | dimensionless / metadata / nested; see contract | pattern=^[a-f0-9]{64}$ |
| `source_code_digest` | string | required | dimensionless / metadata / nested; see contract | pattern=^[a-f0-9]{64}$ |
| `evidence_ids` | array[string] | required | dimensionless / metadata / nested; see contract |  |
| `mode` | enum finite, continuous_through_window | required | dimensionless / metadata / nested; see contract |  |
| `intervals` | array[ReleaseInterval] | required | dimensionless / metadata / nested; see contract | minItems=1; maxItems=128 |
| `declared_mass_within_history_kg` | number | required | kg | exclusiveMinimum=0 |
| `area_m2` | number | required | m2 | exclusiveMinimum=0 |
| `temperature_k` | number | required | K | exclusiveMinimum=0 |
| `qualification_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `boundary` | literal qualified_ground_level_thermalized_pure_vapour | required | dimensionless / metadata / nested; see contract |  |

## ReleaseInterval

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `start_s` | number | required | s | minimum=0 |
| `end_s` | number | required | s | exclusiveMinimum=0 |
| `mass_rate_kg_s` | number | required | kg/s | minimum=0 |

## SegmentLedger

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `start_s` | number | required | s | minimum=0 |
| `stop_s` | number | required | s | exclusiveMinimum=0 |
| `rate_kg_s` | number | required | kg/s | exclusiveMinimum=0 |
| `mode` | enum finite, continuous_through_window | required | dimensionless / metadata / nested; see contract |  |
| `source_mass_within_window_kg` | number | required | kg | exclusiveMinimum=0 |
| `transition_time_s` | number or null | required | s |  |
| `transition_x_m` | number or null | required | m |  |
| `native_final_time_s` | number | required | s | minimum=0 |
| `used_source_area_m2` | number | required | m2 | exclusiveMinimum=0 |
| `maximum_puff_mass_relative_residual` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `maximum_plume_flux_relative_residual` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `transition_mass_relative_residual` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `native_transition_flux_relative_residual` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `native_duplicate_clock_rows_removed` | integer | default `0` | dimensionless / metadata / nested; see contract | minimum=0 |
| `native_times_s` | array[number] | required | s |  |
| `native_clock_kind` | enum plume_twice_integrated_mass_over_rate, plume_release_clock_then_puff | required | dimensionless / metadata / nested; see contract |  |
| `native_modes` | array[enum plume, puff] | required | dimensionless / metadata / nested; see contract |  |
| `native_center_x_m` | array[number] | required | m |  |
| `accounted_emission_mass_kg` | array[number] | required | kg |  |
