# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Synthetic PRISM row contracts and actual SLABx plume-to-puff integration."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest
from ccps_consequence import calculate, verify_receipt
from ccps_consequence.contracts import digest
from ccps_consequence.dense import capabilities
from ccps_consequence.release_history import ReleaseHistory, ReleaseHistoryInput, ReleaseHistoryOutput, history_from_prism_rows
sys.path.insert(0, str(Path(__file__).parents[1] / 'examples'))
import ccps_release_history as example

@pytest.fixture(scope='module')
def engine():
    info = capabilities()
    if info['status'] != 'available':
        pytest.skip(f'optional SLABx unavailable: {info}')
    return info

@pytest.fixture(scope='module')
def finite(engine):
    return calculate('dispersion/slabx-release-history', example.example_inputs(engine['engine_code_digest']), context=example.example_context())

def test_prism_left_hold_endpoint_and_canonicalization():
    source = ReleaseHistory.model_validate_json(json.dumps(example.example_inputs('0' * 64)['source']))
    assert source.declared_mass_within_history_kg == 10.0
    assert source.cumulative_mass(5.0) == 2.5
    assert source.cumulative_mass(100.0) == 10.0
    payload = source.model_dump(mode='json')
    payload['intervals'] = [dict(start_s=0.0, end_s=10.0, mass_rate_kg_s=0.5), dict(start_s=10.0, end_s=20.0, mass_rate_kg_s=0.5)]
    split = ReleaseHistory.model_validate_json(json.dumps(payload))
    assert split.canonical_intervals() == source.canonical_intervals()

@pytest.mark.parametrize('mutation,match', [(lambda p: p['source'].update(declared_mass_within_history_kg=9.0), 'declared mass'), (lambda p: p['source']['intervals'][0].update(start_s=1.0), 'start at zero'), (lambda p: p['source'].update(temperature_k=250.0), 'normal boiling'), (lambda p: p.update(simulation_end_s=20.0, sample_times_s=[0.0, 20.0]), 'stop before'), (lambda p: p['source'].update(mode='continuous_through_window'), 'whole observation')])
def test_history_contract_rejections(mutation, match):
    payload = example.example_inputs('0' * 64)
    mutation(payload)
    with pytest.raises(ValueError, match=match):
        ReleaseHistoryInput.model_validate_json(json.dumps(payload))

def test_prism_liquid_and_digest_rejected():
    rows = example.example_rows()
    kwargs = dict(duration_s=20.0, mode='finite', asset_id='A', scenario_id='S', operating_case_id='O', source_code_digest='0' * 64, evidence_ids=('E',), area_m2=25.0, temperature_k=230.0, qualification_basis='explicit synthetic ground qualification')
    with pytest.raises(ValueError, match='digest'):
        history_from_prism_rows(rows, expected_rows_digest='0' * 64, **kwargs)
    rows[0]['ground_liquid_mass_flow_kg_s'] = 0.1
    with pytest.raises(ValueError, match='liquid'):
        history_from_prism_rows(rows, expected_rows_digest=digest(rows), **kwargs)

@pytest.mark.dense_native
def test_real_finite_plume_to_puff(finite):
    result = ReleaseHistoryOutput.model_validate_json(json.dumps(finite.outputs))
    assert result.source_mass_within_window_kg == 10.0
    assert result.maximum_reconstruction_mass_relative_residual < 1e-10
    segment = result.segments[0]
    assert segment.transition_time_s == 20.0
    assert set(segment.native_modes) == {'plume', 'puff'}
    assert segment.maximum_puff_mass_relative_residual < 1e-10
    assert segment.maximum_plume_flux_relative_residual < 1e-10
    assert segment.transition_mass_relative_residual < 1e-10
    assert result.cumulative_emitted_mass_kg[10] == 5.0
    assert result.cumulative_emitted_mass_kg[20] == 10.0
    assert result.cumulative_emitted_mass_kg[-1] == 10.0
    assert result.source_active_at_window_end is False
    assert all((h.sampled_peak_kg_m3 > h.concentration_kg_m3[-1] for h in result.histories))
    assert verify_receipt(finite) == finite

@pytest.mark.dense_native
def test_continuous_steady_limit_and_mass(engine):
    result = calculate('dispersion/slabx-release-history', example.example_inputs(engine['engine_code_digest'], 'continuous_through_window'), context=example.example_context()).outputs
    assert result['source_active_at_window_end'] is True
    assert result['source_mass_within_window_kg'] == 60.0
    assert result['cumulative_emitted_mass_kg'][-1] == 60.0
    assert result['segments'][0]['transition_time_s'] is None
    assert set(result['segments'][0]['native_modes']) == {'plume'}
    for h in result['histories']:
        assert h['concentration_kg_m3'][-1] == h['concentration_kg_m3'][-10] == h['sampled_peak_kg_m3']

@pytest.mark.dense_native
def test_variable_rates_and_equal_rate_split_invariance(engine, finite):
    inputs = example.example_inputs(engine['engine_code_digest'], 'variable')
    variable = calculate('dispersion/slabx-release-history', inputs, context=example.example_context()).outputs
    assert variable['source_mass_within_window_kg'] == 8.0
    assert len(variable['segments']) == 2
    assert [s['transition_time_s'] for s in variable['segments']] == [10.0, 25.0]
    assert variable['maximum_reconstruction_mass_relative_residual'] < 1e-10
    inputs = example.example_inputs(engine['engine_code_digest'])
    inputs['source']['intervals'] = [dict(start_s=0.0, end_s=10.0, mass_rate_kg_s=0.5), dict(start_s=10.0, end_s=20.0, mass_rate_kg_s=0.5)]
    split = calculate('dispersion/slabx-release-history', inputs, context=example.example_context()).outputs
    assert split['histories'] == finite.outputs['histories']

@pytest.mark.dense_native
def test_transition_continuity_and_refinement(engine, finite):
    inputs = example.example_inputs(engine['engine_code_digest'])
    inputs['sample_times_s'] = [0.0, 19.999, 20.0, 20.001, 120.0]
    edge = calculate('dispersion/slabx-release-history', inputs, context=example.example_context()).outputs
    for h in edge['histories']:
        assert h['concentration_kg_m3'][1] == pytest.approx(h['concentration_kg_m3'][2], rel=0.01)
        assert h['concentration_kg_m3'][3] == pytest.approx(h['concentration_kg_m3'][2], rel=0.01)
    inputs = example.example_inputs(engine['engine_code_digest'])
    inputs['native_puff_steps'] = 480
    inputs['sample_times_s'] = [i * 0.5 for i in range(241)]
    refined = calculate('dispersion/slabx-release-history', inputs, context=example.example_context()).outputs
    for a, b in zip(refined['histories'], finite.outputs['histories']):
        assert a['sampled_peak_kg_m3'] == pytest.approx(b['sampled_peak_kg_m3'], rel=0.05)
        assert a['sampled_integral_kg_s_m3'] == pytest.approx(b['sampled_integral_kg_s_m3'], rel=0.05)

@pytest.mark.dense_native
def test_inadequate_native_grid_fails(engine):
    inputs = example.example_inputs(engine['engine_code_digest'])
    inputs['plume_distance_limit_m'] = 5.0
    with pytest.raises(ValueError, match='distance limit|transition'):
        calculate('dispersion/slabx-release-history', inputs, context=example.example_context())

def test_segment_mass_tampering(finite):
    payload = copy.deepcopy(finite.outputs)
    payload['segments'][0]['source_mass_within_window_kg'] = 8.0
    with pytest.raises(ValueError, match='mass'):
        ReleaseHistoryOutput.model_validate_json(json.dumps(payload))

@pytest.mark.dense_native
def test_zero_rate_gap_keeps_mass(engine):
    inputs = example.example_inputs(engine['engine_code_digest'])
    inputs['source']['intervals'] = [dict(start_s=0.0, end_s=10.0, mass_rate_kg_s=0.5), dict(start_s=10.0, end_s=20.0, mass_rate_kg_s=0.0), dict(start_s=20.0, end_s=25.0, mass_rate_kg_s=0.2)]
    inputs['source']['declared_mass_within_history_kg'] = 6.0
    result = calculate('dispersion/slabx-release-history', inputs, context=example.example_context()).outputs
    assert result['cumulative_emitted_mass_kg'][10] == result['cumulative_emitted_mass_kg'][20] == 5.0
    assert result['cumulative_emitted_mass_kg'][-1] == 6.0
    assert len(result['segments']) == 2

@pytest.mark.dense_native
def test_http_history_to_dose_dag(engine, tmp_path):
    from fastapi.testclient import TestClient
    from ccps_consequence.http_api import create_app
    payload = dict(context=example.example_context().model_dump(mode='json'), steps=[dict(id='release', calculation_id='dispersion/slabx-release-history', inputs=example.example_inputs(engine['engine_code_digest'])), dict(id='dose', calculation_id='dispersion/history-dose', inputs=dict(sample_times_s={'$ref': 'release.sample_times_s'}, histories={'$ref': 'release.histories'}, receptor_id='R60', exponent=1.0, reference_value_kg_m3=1.0, integration='sampled_trapezoid'))])
    with TestClient(create_app()) as client:
        response = client.post('/api/ccps/workflow', json=payload)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result['steps'][1]['receipt']['outputs']['normalized_dose_s'] == pytest.approx(result['steps'][0]['receipt']['outputs']['histories'][1]['sampled_integral_kg_s_m3'])

def test_context_identity_fail_before_engine():
    inputs = example.example_inputs('0' * 64)
    inputs['source']['scenario_id'] = 'other'
    with pytest.raises(ValueError, match='identity'):
        calculate('dispersion/slabx-release-history', inputs, context=example.example_context())
