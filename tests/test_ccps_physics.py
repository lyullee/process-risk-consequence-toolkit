# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Synthetic analytic identities; no copyrighted example values or datasets."""
import math
import pytest
from pydantic import ValidationError
from ccps_consequence import Context, calculate, verify_receipt, UnsupportedCalculation
from ccps_consequence.catalog import CALCULATIONS
from ccps_consequence.contracts import Receipt, digest

@pytest.fixture
def context():
    return Context(asset_id='synthetic-vessel', scenario_id='leak', operating_case_id='normal')

def run(context, key, **inputs):
    return calculate(key, inputs, context=context).outputs

def test_liquid_and_inventory(context):
    q = run(context, 'source/liquid', area_m2=0.002, density_kg_m3=800.0, upstream_pressure_pa_abs=300000.0, downstream_pressure_pa_abs=100000.0, discharge_coefficient=0.5, phase='incompressible_nonflashing_liquid')
    assert q['mass_rate_kg_s'] == pytest.approx(0.001 * math.sqrt(2 * 800 * 200000))
    result = run(context, 'source/inventory', mass_rate_kg_s=2.0, duration_s=8.0, inventory_kg=10.0)
    assert result == {'released_mass_kg': 10.0, 'remaining_mass_kg': 0.0, 'effective_duration_s': 5.0}
    assert run(context, 'source/inventory', mass_rate_kg_s=0.0, duration_s=8.0, inventory_kg=10.0)['released_mass_kg'] == 0

def test_gas_regimes_and_continuity(context):
    args = dict(area_m2=0.0002, upstream_pressure_pa_abs=800000.0, temperature_k=310.0, specific_gas_constant_j_kg_k=290.0, heat_capacity_ratio=1.4, discharge_coefficient=0.7, phase='ideal_gas')
    critical = (2 / 2.4) ** (1.4 / 0.4)
    sonic = run(context, 'source/gas', **args, downstream_pressure_pa_abs=800000.0 * critical)
    near = run(context, 'source/gas', **args, downstream_pressure_pa_abs=800000.0 * (critical + 1e-08))
    expected = 0.7 * 0.0002 * 800000 * math.sqrt(1.4 / (290 * 310) * (2 / 2.4) ** 6)
    assert sonic['mass_rate_kg_s'] == pytest.approx(expected)
    assert near['mass_rate_kg_s'] == pytest.approx(sonic['mass_rate_kg_s'])
    assert near['regime'] == 'subsonic'
    zero = run(context, 'source/gas', **args, downstream_pressure_pa_abs=800000.0)
    assert zero['mass_rate_kg_s'] == 0
    with pytest.raises(ValueError, match='reverse'):
        run(context, 'source/gas', **args, downstream_pressure_pa_abs=900000.0)

def test_flash_and_evaporation_mass_balance(context):
    result = run(context, 'source/flash', mass_kg=20.0, liquid_heat_capacity_j_kg_k=2000.0, initial_temperature_k=350.0, boiling_temperature_k=300.0, latent_heat_j_kg=400000.0, assumption='constant_properties_sensible_heat_only')
    assert result == {'vapour_fraction': 0.25, 'vapour_mass_kg': 5.0, 'liquid_mass_kg': 15.0}
    result = run(context, 'source/evaporation', area_m2=3.0, mass_flux_kg_m2_s=0.1, duration_s=100.0, inventory_kg=9.0, flux_basis='synthetic fixed flux')
    assert result['released_mass_kg'] == 9.0
    assert result['effective_duration_s'] == pytest.approx(30.0)

def test_gaussian_identities(context):
    args = dict(mass_rate_kg_s=2.0, wind_speed_m_s=4.0, downwind_distance_m=100.0, crosswind_distance_m=0.0, receptor_height_m=0.0, release_height_m=0.0, sigma_y_m=8.0, sigma_z_m=5.0, sigma_basis='synthetic supplied sigmas', applicability='passive_steady_open_terrain')
    center = run(context, 'dispersion/plume', **args)['concentration_kg_m3']
    assert center == pytest.approx(2 / (math.pi * 4 * 8 * 5))
    args['crosswind_distance_m'] = 8.0
    assert run(context, 'dispersion/plume', **args)['concentration_kg_m3'] == pytest.approx(center * math.exp(-0.5))
    args['applicability'] = 'dense_gas'
    with pytest.raises(ValueError):
        run(context, 'dispersion/plume', **args)
    puff = run(context, 'dispersion/puff', mass_kg=4.0, downwind_distance_m=20.0, crosswind_distance_m=0.0, receptor_height_m=0.0, release_height_m=0.0, wind_speed_m_s=2.0, elapsed_s=10.0, sigma_x_m=3.0, sigma_y_m=4.0, sigma_z_m=5.0, sigma_basis='synthetic supplied sigmas', applicability='passive_instantaneous_open_terrain')
    assert puff['concentration_kg_m3'] == pytest.approx(8 / ((2 * math.pi) ** 1.5 * 3 * 4 * 5))

def test_radiation_inverse_square(context):
    args = dict(heat_release_rate_w=2000000.0, radiative_fraction=0.2, transmissivity=0.8, distance_m=10.0, applicability='far_field_isotropic_point_source')
    first = run(context, 'effects/radiation', **args)['heat_flux_w_m2']
    args['distance_m'] = 20.0
    assert run(context, 'effects/radiation', **args)['heat_flux_w_m2'] == pytest.approx(first / 4)

def test_dose_and_probit(context):
    d = run(context, 'effects/dose', values=[2.0, 4.0], durations_s=[3.0, 2.0], exponent=2.0, reference_value=2.0, reference_unit='kg/m3')
    assert d['normalized_dose_s'] == 11.0
    args = dict(normalized_dose_s=1.0, reference_time_s=1.0, intercept=5.0, slope=1.0, normal_offset=5.0, coefficient_basis='synthetic convention')
    assert run(context, 'effects/probit', **args)['probability'] == 0.5
    args['normalized_dose_s'] = 0.0
    assert run(context, 'effects/probit', **args)['probability'] == 0.0
    with pytest.raises(ValueError, match='paired'):
        run(context, 'effects/dose', values=[2.0], durations_s=[], exponent=1.0, reference_value=1.0, reference_unit='Pa')

def test_tnt_and_threshold(context):
    args = dict(flammable_mass_kg=10.0, heat_of_combustion_j_kg=40000000.0, explosion_efficiency=0.1, tnt_specific_energy_j_kg=4000000.0, distance_m=20.0, efficiency_basis='synthetic energy conversion')
    value = run(context, 'effects/tnt-scaling', **args)
    assert value['equivalent_tnt_mass_kg'] == 10.0
    assert value['scaled_distance_m_kg_third'] == pytest.approx(20 / 10 ** (1 / 3))
    args['explosion_efficiency'] = 0.0
    assert run(context, 'effects/tnt-scaling', **args)['scaled_distance_m_kg_third'] is None
    assert run(context, 'effects/threshold', value=2.0, threshold=2.0, unit='Pa', criterion_basis='synthetic equality')['exceeded']

def test_risk_ownership_and_partition(context):
    from ccps_consequence import Evidence
    context = context.model_copy(update={'evidence': (Evidence(id='freq', kind='synthetic', citation='Synthetic', locator='test'),)})
    frequency = dict(asset_id=context.asset_id, scenario_id=context.scenario_id, operating_case_id=context.operating_case_id, annual_frequency_per_year=0.01, origin='user_supplied', source_digest='0' * 64, source_code_digest='1' * 64, included_factor_ids=['IPL-1'], evidence_ids=['freq'])
    args = dict(frequency=frequency, receptor_id='R1', mutually_exclusive_exhaustive=True, partition_basis='synthetic split', branches=[dict(id='fire', conditional_probability=0.2, probability_basis='synthetic ignition', probability_factor_ids=['ignition'], harm_probability=0.5, harm_factor_id='harm', harm_basis='synthetic harm', factors=[dict(id='occupancy', probability=0.5, kind='occupancy', basis='synthetic presence')]), dict(id='other', conditional_probability=0.8, probability_basis='synthetic complement', probability_factor_ids=['no-ignition'], harm_probability=0.0, harm_factor_id='no-harm', harm_basis='synthetic zero')])
    assert run(context, 'risk/conditional', **args)['annual_harm_frequency_per_year'] == pytest.approx(0.0005)
    args['branches'][0]['factors'][0]['id'] = 'IPL-1'
    with pytest.raises(ValueError, match='duplicate'):
        run(context, 'risk/conditional', **args)
    args['branches'][0]['factors'][0]['id'] = 'occupancy'
    args['branches'][1]['conditional_probability'] = 0.7
    with pytest.raises(ValueError, match='sum to one'):
        run(context, 'risk/conditional', **args)

@pytest.mark.parametrize('bad', [-1.0, float('nan'), float('inf'), True, '2'])
def test_invalid_values_fail_closed(context, bad):
    with pytest.raises(ValueError):
        run(context, 'source/inventory', mass_rate_kg_s=bad, duration_s=1.0, inventory_kg=2.0)

def test_receipt_reproducible_and_tamper_checked(context):
    receipt = calculate('source/inventory', dict(mass_rate_kg_s=1.0, duration_s=2.0, inventory_kg=3.0), context=context)
    assert verify_receipt(receipt) == receipt
    assert calculate(receipt.calculation_id, receipt.normalized_inputs, context=context) == receipt
    payload = receipt.model_dump(mode='json')
    payload['outputs']['released_mass_kg'] = 0.0
    with pytest.raises(ValueError, match='hash'):
        Receipt.model_validate_json(__import__('json').dumps(payload))
    payload['output_digest'] = digest(payload['outputs'])
    with pytest.raises(ValueError, match='reproducible'):
        verify_receipt(Receipt.model_validate_json(__import__('json').dumps(payload)))
    with pytest.raises(UnsupportedCalculation, match='no fallback'):
        calculate('dispersion/dense-gas', {}, context=context)

def test_catalog_traceability_targets_exist():
    from pathlib import Path
    from ccps_consequence.catalog import calculation_catalog
    assert len(calculation_catalog()) == len(CALCULATIONS) == 23
    for c in CALCULATIONS.values():
        text = (Path(__file__).parents[1] / c.test_file).read_text(encoding='utf-8')
        assert f'def {c.test}(' in text

def test_richardson_screen(context):
    args = dict(cloud_density_kg_m3=2.0, air_density_kg_m3=1.0, characteristic_dimension_m=0.1, friction_velocity_m_s=1.0, gravity_m_s2=10.0, characteristic_dimension_basis='synthetic height', applicability='noaa_2013_friction_richardson_screen')
    result = run(context, 'dispersion/richardson-screen', **args)
    assert result['friction_richardson_number'] == 1.0
    assert result['screening'] == 'dense_model_required'
    assert result['concentration_prediction_available'] is False
    args['friction_velocity_m_s'] = 2.0
    assert run(context, 'dispersion/richardson-screen', **args)['friction_richardson_number'] == 0.25
    assert run(context, 'dispersion/richardson-screen', **args)['screening'] == 'passive_candidate'
    args['cloud_density_kg_m3'] = 1.0
    assert run(context, 'dispersion/richardson-screen', **args)['friction_richardson_number'] == 0.0
    args['cloud_density_kg_m3'] = 0.5
    assert run(context, 'dispersion/richardson-screen', **args)['screening'] == 'buoyant_review_required'
    args['friction_velocity_m_s'] = 0.0
    with pytest.raises(ValueError):
        run(context, 'dispersion/richardson-screen', **args)

def test_fireball_public_correlations(context):
    args = dict(participating_mass_kg=8.0, mass_basis='synthetic participating fuel only', correlation='noaa_2013_roberts_diameter_dutch_duration')
    result = run(context, 'fire/fireball', **args)
    assert result['diameter_m'] == pytest.approx(11.6)
    assert result['duration_s'] == pytest.approx(0.852 * math.exp(0.26 * math.log(8)))
    args['participating_mass_kg'] = 64.0
    larger = run(context, 'fire/fireball', **args)
    assert larger['diameter_m'] == pytest.approx(2 * result['diameter_m'])
    assert larger['duration_s'] / result['duration_s'] == pytest.approx(8 ** 0.26)
    for bad in [0.0, -1.0, 5000001.0, True]:
        args['participating_mass_kg'] = bad
        with pytest.raises(ValueError):
            run(context, 'fire/fireball', **args)

def test_solid_flame_bounds(context):
    args = dict(surface_emissive_power_w_m2=100000.0, view_factor=0.2, transmissivity=0.8, emissive_power_basis='synthetic supplied power', view_factor_basis='synthetic supplied geometry', applicability='supplied_solid_flame_geometry')
    assert run(context, 'fire/solid-flame', **args)['heat_flux_w_m2'] == 16000.0
    args['view_factor'] = 0.0
    assert run(context, 'fire/solid-flame', **args)['heat_flux_w_m2'] == 0.0
    args['view_factor'] = 1.1
    with pytest.raises(ValueError):
        run(context, 'fire/solid-flame', **args)

def test_sphere_radiation_geometry(context):
    args = dict(diameter_m=4.0, horizontal_distance_m=4.0, surface_emissive_power_w_m2=100000.0, transmissivity=0.5, emissive_power_basis='synthetic power', geometry='ground_tangent_sphere_ground_level_vertical_receptor')
    result = run(context, 'fire/sphere-radiation', **args)
    expected = 2 ** 2 * 4 / (4 ** 2 + 2 ** 2) ** 1.5
    assert result['view_factor'] == pytest.approx(expected)
    assert result['heat_flux_w_m2'] == pytest.approx(expected * 50000)
    args['horizontal_distance_m'] = 8.0
    assert run(context, 'fire/sphere-radiation', **args)['heat_flux_w_m2'] < result['heat_flux_w_m2']
    args['horizontal_distance_m'] = 2.0
    with pytest.raises(ValueError, match='greater than radius'):
        run(context, 'fire/sphere-radiation', **args)

def test_pool_energy_balance(context):
    args = dict(area_m2=10.0, burning_flux_kg_m2_s=0.1, inventory_kg=5.0, duration_s=10.0, heat_of_combustion_j_kg=20000000.0, combustion_efficiency=0.8, burning_flux_basis='synthetic constant flux', applicability='constant_area_constant_burning_flux_no_replenishment')
    result = run(context, 'fire/pool-energy', **args)
    assert result['burned_mass_kg'] + result['remaining_mass_kg'] == 5.0
    assert result['effective_duration_s'] == 5.0
    assert result['heat_release_rate_w'] == 16000000.0
    assert result['released_energy_j'] == result['heat_release_rate_w'] * result['effective_duration_s']
    for field in ['inventory_kg', 'duration_s', 'burning_flux_kg_m2_s']:
        zero = run(context, 'fire/pool-energy', **{**args, field: 0.0})
        assert zero['released_energy_j'] == zero['heat_release_rate_w'] == zero['effective_duration_s'] == 0.0

def test_epa_one_psi_endpoint(context):
    args = dict(flammable_mass_kg=10.0, heat_of_combustion_j_kg=4680000.0, mass_basis='synthetic vapour cloud', applicability='epa_1999_worst_case_vapour_cloud_1psi')
    result = run(context, 'explosion/epa-1psi', **args)
    assert result['equivalent_tnt_mass_kg'] == 1.0
    assert result['endpoint_distance_m'] == 17.0
    assert result['explosion_efficiency'] == 0.1
    args['flammable_mass_kg'] = 80.0
    assert run(context, 'explosion/epa-1psi', **args)['endpoint_distance_m'] == pytest.approx(34.0)
    args['flammable_mass_kg'] = 0.0
    assert run(context, 'explosion/epa-1psi', **args)['endpoint_distance_m'] == 0.0
    with pytest.raises(ValueError):
        run(context, 'explosion/epa-1psi', **args, endpoint_pressure_pa=20000.0)

@pytest.mark.parametrize('identifier,inputs', [('fire/fireball', dict(participating_mass_kg=8.0, mass_basis='synthetic', correlation='noaa_2013_roberts_diameter_dutch_duration')), ('explosion/epa-1psi', dict(flammable_mass_kg=10.0, heat_of_combustion_j_kg=4680000.0, mass_basis='synthetic', applicability='epa_1999_worst_case_vapour_cloud_1psi'))])
def test_public_method_receipt_references_and_replay(context, identifier, inputs):
    receipt = calculate(identifier, inputs, context=context)
    assert receipt.method_references and all((ref.startswith('https://') for ref in receipt.method_references))
    assert verify_receipt(receipt) == receipt
    assert receipt.physical_validation_claim is False
