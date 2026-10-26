# `dispersion/coupled-layer-1d`

Python: `ccps_consequence.coupled.solve_coupled`.

Execution: `coupled_research`. Coverage: `restricted_research_1d`.

## Purpose and limitations

Research 1D isothermal fixed-width vertically mixed layer: shared mixture/species/momentum finite-volume field with composition-dependent hydrostatic pressure. User-qualified densities, entrainment and wind relaxation; no energy equation, 2D spreading, obstacles, droplets or field validation. Not a SLAB/TWODEE implementation.

## Input

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `source` | ReleaseHistory | required | dimensionless / metadata / nested; see contract |  |
| `temperature_k` | number | required | K | exclusiveMinimum=0 |
| `air_density_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `pure_vapour_density_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `density_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `x_min_m` | number | required | m |  |
| `x_max_m` | number | required | m |  |
| `cells` | integer | required | dimensionless / metadata / nested; see contract | minimum=20; maximum=2000 |
| `width_m` | number | required | m | exclusiveMinimum=0 |
| `source_start_m` | number | required | m |  |
| `wind_speed_m_s` | number | required | m/s |  |
| `injection_velocity_m_s` | number | required | m/s |  |
| `wind_relaxation_time_s` | number or null | required | s |  |
| `entrainment_coefficient` | number | required | dimensionless / metadata / nested; see contract | minimum=0; maximum=0.5 |
| `closure_basis` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `gravity_m_s2` | number | required | m/s2 | exclusiveMinimum=0 |
| `maximum_step_s` | number | required | s | exclusiveMinimum=0 |
| `cfl` | number | required | dimensionless / metadata / nested; see contract | exclusiveMinimum=0; maximum=0.45 |
| `maximum_steps` | integer | default `40000` | dimensionless / metadata / nested; see contract | minimum=10; maximum=200000 |
| `sample_times_s` | array[number] | required | s | minItems=2; maxItems=2001 |
| `receptors` | array[DenseReceptor] | required | dimensionless / metadata / nested; see contract | minItems=1; maxItems=32 |
| `tail_threshold_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `boundary` | enum open_vacuum, reflecting | required | dimensionless / metadata / nested; see contract |  |
| `applicability` | literal research_1d_isothermal_fixed_width_flat_ground_layer | required | dimensionless / metadata / nested; see contract |  |

## Output

| Field | Type / allowed values | Required / default | Unit | Bounds |
|---|---|---|---|---|
| `solver` | literal authored_1d_variable_density_rusanov_v1 | default `"authored_1d_variable_density_rusanov_v1"` | dimensionless / metadata / nested; see contract |  |
| `model_status` | literal research_numerically_verified_not_field_validated | default `"research_numerically_verified_not_field_validated"` | dimensionless / metadata / nested; see contract |  |
| `numpy_version` | string | required | dimensionless / metadata / nested; see contract | minLength=1; maxLength=160 |
| `air_density_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `pure_vapour_density_kg_m3` | number | required | kg/m3 | exclusiveMinimum=0 |
| `cell_plan_area_m2` | number | required | m2 | exclusiveMinimum=0 |
| `sample_times_s` | array[number] | required | s |  |
| `histories` | array[DenseHistory] | required | dimensionless / metadata / nested; see contract |  |
| `cumulative_source_mass_kg` | array[number] | required | kg |  |
| `domain_emission_mass_kg` | array[number] | required | kg |  |
| `escaped_emission_mass_kg` | array[number] | required | kg |  |
| `domain_mixture_mass_kg` | array[number] | required | kg |  |
| `escaped_mixture_mass_kg` | array[number] | required | kg |  |
| `entrained_air_mass_kg` | array[number] | required | kg |  |
| `emission_roundoff_correction_kg` | array[number] | required | kg |  |
| `mixture_roundoff_correction_kg` | array[number] | required | kg |  |
| `maximum_emission_mass_relative_residual` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `maximum_mixture_mass_relative_residual` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `maximum_absolute_roundoff_correction_kg` | number | required | kg | minimum=0 |
| `maximum_observed_cfl` | number | required | dimensionless / metadata / nested; see contract | minimum=0 |
| `accepted_steps` | integer | required | dimensionless / metadata / nested; see contract | minimum=1 |
| `final_cell_centers_m` | array[number] | required | m |  |
| `final_layer_height_m` | array[number] | required | m |  |
| `final_mixture_density_kg_m3` | array[number] | required | kg/m3 |  |
| `final_velocity_m_s` | array[number] | required | m/s |  |
| `final_emission_column_kg_m2` | array[number] | required | kg/m2 |  |
| `final_mixture_column_kg_m2` | array[number] | required | kg/m2 |  |
| `source_active_at_window_end` | boolean | required | dimensionless / metadata / nested; see contract |  |
| `numerical_diffusion_present` | literal True | default `true` | dimensionless / metadata / nested; see contract |  |
| `physical_validation_claim` | literal False | default `false` | dimensionless / metadata / nested; see contract |  |

## Evidence and traceability

CCPS topic section identifiers: 2.3.2,4.2. These locate topics, not copied book equations.

Direct tests: `tests/test_ccps_coupled.py::test_coupled_mass_and_interaction`.

Direct references:

- https://doi.org/10.1029/2007GC001762
- https://arxiv.org/abs/2101.04384
- https://www.clawpack.org/v5.12.x/riemann/Shallow_water_Riemann_solvers.html
- Own isothermal additive-volume closure, reduced hydrostatic pressure and first-order Rusanov implementation

## Failure and integration behavior

Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.

Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.
