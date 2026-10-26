# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Numerical verification of an explicitly restricted research PDE, no field data."""
import copy
import json
from pathlib import Path
import sys
import pytest
np = pytest.importorskip('numpy', reason='optional coupled numpy unavailable')
sys.path.insert(0, str(Path(__file__).parents[1] / 'examples'))
import ccps_coupled_layer as example
from ccps_consequence import calculate, verify_receipt
from ccps_consequence.coupled import CoupledInput, CoupledOutput, state_fields, face_flux

def run(payload):
    return calculate('dispersion/coupled-layer-1d', payload, context=example.example_context())

@pytest.fixture(scope='module')
def combined():
    return run(example.example_inputs())

def test_flux_consistency_and_characteristic_speed():
    state = np.array([[2.0, 2.0, 2.0], [0.8, 0.8, 0.8], [3.0, 3.0, 3.0]])
    h, rho, u, p, speed = state_fields(state, 1.2, 2.4, 9.8)
    assert np.allclose(h, 0.8 / 2.4 + 1.2 / 1.2)
    assert np.allclose(p, 0.5 * 9.8 * (rho - 1.2) * h * h)
    assert np.allclose(speed, np.abs(u) + np.sqrt(2 * p / state[0]))
    flux, _ = face_flux(state, 1.2, 2.4, 9.8, 'open_vacuum')
    expected = state[:, 0] * u[0]
    expected[2] += p[0]
    assert np.allclose(flux[:, 1], expected)
    assert flux[0, 0] <= 0.0 and flux[0, -1] >= 0.0

    def physical(v):
        fields = state_fields(v[:, None], 1.2, 2.4, 9.8)
        result = v * fields[2][0]
        result[2] += fields[3][0]
        return result
    v = state[:, 0]
    jac = np.column_stack([(physical(v + np.eye(3)[i] * 1e-06) - physical(v - np.eye(3)[i] * 1e-06)) / 2e-06 for i in range(3)])
    a = (2 * p[0] / v[0]) ** 0.5
    assert np.sort(np.linalg.eigvals(jac)) == pytest.approx(sorted([u[0] - a, u[0], u[0] + a]), rel=1e-06)

def test_coupled_mass_and_interaction(combined):
    result = combined.outputs
    assert result['cumulative_source_mass_kg'][-1] == 10.0
    assert result['maximum_emission_mass_relative_residual'] < 1e-10
    assert result['maximum_mixture_mass_relative_residual'] < 1e-10
    assert result['entrained_air_mass_kg'][-1] > 0.0
    assert result['maximum_observed_cfl'] <= 0.4 + 1e-12
    assert combined.validation_level == 'research_numerical_tests'
    assert verify_receipt(combined) == combined
    first = example.example_inputs()
    second = copy.deepcopy(first)
    first['source']['intervals'][2]['mass_rate_kg_s'] = 0.0
    second['source']['intervals'][0]['mass_rate_kg_s'] = 0.0
    first['source']['declared_mass_within_history_kg'] = 5.0
    second['source']['declared_mass_within_history_kg'] = 5.0
    from ccps_consequence.contracts import digest
    for p in (first, second):
        p['source'].update(origin='user_supplied', source_digest=digest(p['source']['intervals']), qualification_basis='Derived synthetic one-pulse comparison')
    independent = np.array(run(first).outputs['final_emission_column_kg_m2']) + np.array(run(second).outputs['final_emission_column_kg_m2'])
    actual = np.array(result['final_emission_column_kg_m2'])
    relative = np.sum(np.abs(actual - independent)) / np.sum(actual)
    assert relative > 0.01

def test_grid_convergence(combined):
    coarse = example.example_inputs()
    fine = example.example_inputs()
    coarse['cells'] = 100
    fine['cells'] = 400
    c = run(coarse).outputs
    f = run(fine).outputs
    fine_species = np.asarray(f['final_emission_column_kg_m2'])
    reference_mid = fine_species.reshape(200, 2).mean(axis=1)
    reference_coarse = fine_species.reshape(100, 4).mean(axis=1)
    mid_error = np.sum(np.abs(np.asarray(combined.outputs['final_emission_column_kg_m2']) - reference_mid))
    coarse_error = 2 * np.sum(np.abs(np.asarray(c['final_emission_column_kg_m2']) - reference_coarse))
    assert mid_error < coarse_error

def test_closed_quiescent_symmetry_and_no_entrainment():
    p = example.example_inputs()
    p.update(x_min_m=-50.0, x_max_m=50.0, source_start_m=-5.0, boundary='reflecting', wind_speed_m_s=0.0, wind_relaxation_time_s=None, entrainment_coefficient=0.0, sample_times_s=[float(i) for i in range(21)], receptors=[dict(id='R0', downwind_distance_m=0.0, crosswind_distance_m=0.0, height_m=0.0)])
    r = run(p).outputs
    assert r['domain_emission_mass_kg'][-1] == pytest.approx(10.0)
    assert r['escaped_emission_mass_kg'][-1] == 0.0
    assert r['entrained_air_mass_kg'][-1] == 0.0
    assert np.allclose(r['final_emission_column_kg_m2'], r['final_mixture_column_kg_m2'], atol=1e-14)
    species = np.asarray(r['final_emission_column_kg_m2'])
    assert np.allclose(species, species[::-1], atol=1e-12)

def test_open_boundary_and_source_split_invariance(combined):
    p = example.example_inputs()
    p['source']['intervals'] = [dict(start_s=0.0, end_s=2.0, mass_rate_kg_s=1.0), dict(start_s=2.0, end_s=5.0, mass_rate_kg_s=1.0), dict(start_s=5.0, end_s=8.0, mass_rate_kg_s=0.0), dict(start_s=8.0, end_s=13.0, mass_rate_kg_s=1.0)]
    split = run(p).outputs
    assert split['histories'] == combined.outputs['histories']
    assert split['accepted_steps'] == combined.outputs['accepted_steps']
    p = example.example_inputs()
    p.update(x_max_m=40.0, cells=120, receptors=p['receptors'][:1])
    short = run(p).outputs
    assert short['escaped_emission_mass_kg'][-1] > 1.0
    assert short['domain_emission_mass_kg'][-1] + short['escaped_emission_mass_kg'][-1] == pytest.approx(10.0)

@pytest.mark.parametrize('mutation,match', [(lambda p: p.update(temperature_k=280.0), 'isothermal'), (lambda p: p.update(pure_vapour_density_kg_m3=1.0), 'denser'), (lambda p: p.update(source_start_m=0.3), 'align'), (lambda p: p['receptors'][0].update(crosswind_distance_m=10.0), 'outside'), (lambda p: p.update(cfl=0.9), 'less than or equal')])
def test_scope_and_input_gates(mutation, match):
    p = example.example_inputs()
    mutation(p)
    with pytest.raises(ValueError, match=match):
        CoupledInput.model_validate_json(json.dumps(p))

def test_step_budget_and_output_tamper(combined):
    p = example.example_inputs()
    p['maximum_steps'] = 10
    with pytest.raises(ValueError, match='step budget'):
        run(p)
    bad = copy.deepcopy(combined.outputs)
    bad['domain_emission_mass_kg'][-1] += 1.0
    with pytest.raises(ValueError, match='conservation'):
        CoupledOutput.model_validate_json(json.dumps(bad))

def test_continuous_source_and_time_step_refinement(combined):
    p = example.example_inputs()
    p['source'].update(mode='continuous_through_window', intervals=[dict(start_s=0.0, end_s=60.0, mass_rate_kg_s=1.0)], declared_mass_within_history_kg=60.0)
    result = run(p).outputs
    assert result['source_active_at_window_end']
    assert result['cumulative_source_mass_kg'][-1] == 60.0
    assert result['maximum_emission_mass_relative_residual'] < 1e-10
    p = example.example_inputs()
    p['maximum_step_s'] = 0.125
    finer = run(p).outputs
    a = np.asarray(combined.outputs['final_emission_column_kg_m2'])
    b = np.asarray(finer['final_emission_column_kg_m2'])
    assert np.sum(np.abs(a - b)) / np.sum(a) < 0.05

def test_http_coupled_to_dose_and_context_gate(tmp_path):
    from fastapi.testclient import TestClient
    from ccps_consequence.http_api import create_app
    context = example.example_context()
    inputs = example.example_inputs()
    with TestClient(create_app()) as client:
        payload = dict(context=context.model_dump(mode='json'), steps=[dict(id='coupled', calculation_id='dispersion/coupled-layer-1d', inputs=inputs), dict(id='dose', calculation_id='dispersion/history-dose', inputs=dict(sample_times_s={'$ref': 'coupled.sample_times_s'}, histories={'$ref': 'coupled.histories'}, receptor_id='R20', exponent=1.0, reference_value_kg_m3=1.0, integration='sampled_trapezoid'))])
        response = client.post('/api/ccps/workflow', json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['steps'][1]['receipt']['outputs']['normalized_dose_s'] == pytest.approx(data['steps'][0]['receipt']['outputs']['histories'][0]['sampled_integral_kg_s_m3'])
    inputs['source']['asset_id'] = 'wrong'
    with pytest.raises(ValueError, match='identity'):
        run(inputs)
