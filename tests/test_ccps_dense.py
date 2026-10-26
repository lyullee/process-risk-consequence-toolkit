# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Authored analytic shape checks and actual optional SLABx integration tests."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import pytest
from ccps_consequence import calculate, verify_receipt
from ccps_consequence.dense import DenseInput, DenseOutput, DenseEngineError, capabilities, history_dose_input
from ccps_consequence.dense_profile import horizontal_shape, normalized_profile
spec = importlib.util.spec_from_file_location('dense_example', Path(__file__).parents[1] / 'examples/ccps_dense_history.py')
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)

@pytest.fixture(scope='module')
def engine():
    info = capabilities()
    if info['status'] != 'available':
        pytest.skip(f'optional SLABx 1.0.8 unavailable: {info}')
    return info

@pytest.fixture(scope='module')
def native_receipt(engine):
    return calculate('dispersion/slabx-instantaneous', example.example_inputs(engine['engine_code_digest']), context=example.example_context())

def test_horizontal_shape_normalization_and_tails():
    for beta in [0.3, 2.0]:
        dx = 0.01
        integral = math.fsum((horizontal_shape(-20 + (i + 0.5) * dx, 2.0, beta) * dx for i in range(4000)))
        assert integral == pytest.approx(8.0, rel=1e-09)
    assert horizontal_shape(8.0, 1.0, 1.0) > 0.0
    assert horizontal_shape(-8.0, 1.0, 1.0) == horizontal_shape(8.0, 1.0, 1.0)

def test_puff_profile_mass_normalization():
    bx, by, bex, bey, sz, zc = (2.0, 3.0, 0.7, 1.2, 2.0, 1.0)
    h = 0.02
    ix = math.fsum((horizontal_shape(-20 + (i + 0.5) * h, bx, bex) * h for i in range(2000)))
    iy = math.fsum((horizontal_shape(-20 + (i + 0.5) * h, by, bey) * h for i in range(2000)))
    iz = math.fsum(((math.exp(-0.5 * ((i + 0.5) * h - zc) ** 2 / sz ** 2) + math.exp(-0.5 * ((i + 0.5) * h + zc) ** 2 / sz ** 2)) * h for i in range(1000)))
    assert ix * iy * iz / (16 * bx * by * math.sqrt(2 * math.pi) * sz) == pytest.approx(1.0, rel=1e-09)
    center = normalized_profile(dx=0.0, y=0.0, z=0.0, center_z=0.0, bx=bx, by=by, beta_x=bex, beta_y=bey, sigma_z=sz)
    assert center > normalized_profile(dx=10.0, y=0.0, z=0.0, center_z=0.0, bx=bx, by=by, beta_x=bex, beta_y=bey, sigma_z=sz)

@pytest.mark.parametrize('mutation,match', [(lambda p: p.update(sample_times_s=[0.0, 2.0, 1.0]), 'strictly increase'), (lambda p: p.update(sample_times_s=[0.0, 1.0]), 'end at'), (lambda p: p['source'].update(temperature_k=200.0), 'boiling'), (lambda p: p['source'].update(release_kind='continuous'), 'literal'), (lambda p: p['atmosphere'].update(wind_speed_m_s=0.0), 'greater')])
def test_dense_input_failures(mutation, match):
    payload = example.example_inputs('0' * 64)
    mutation(payload)
    with pytest.raises(ValueError, match=match):
        DenseInput.model_validate_json(json.dumps(payload))

@pytest.mark.dense_native
def test_real_dense_history(native_receipt):
    receipt = native_receipt
    result = DenseOutput.model_validate_json(json.dumps(receipt.outputs))
    assert result.initial_source_density_kg_m3 > result.ambient_density_kg_m3
    assert result.maximum_mass_relative_residual < 1e-10
    assert all((m == pytest.approx(20.0) for m in result.native_emission_mass_kg))
    rows = {h.receptor_id: h for h in result.histories}
    assert rows['R60'].sampled_peak_time_s > rows['R20'].sampled_peak_time_s > 0.0
    assert 0 < rows['R60-side'].sampled_peak_kg_m3 < rows['R60'].sampled_peak_kg_m3
    assert rows['R60'].concentration_kg_m3[-1] < rows['R60'].sampled_peak_kg_m3
    assert receipt.validation_level == 'native_engine_executed'
    assert receipt.physical_validation_claim is False
    assert verify_receipt(receipt) == receipt

@pytest.mark.dense_native
def test_native_refinement_and_history_dose(engine, native_receipt):
    request = example.example_inputs(engine['engine_code_digest'])
    request['native_puff_steps'] = 480
    refined = calculate('dispersion/slabx-instantaneous', request, context=example.example_context())
    for original, fine in zip(native_receipt.outputs['histories'], refined.outputs['histories']):
        assert fine['sampled_peak_kg_m3'] == pytest.approx(original['sampled_peak_kg_m3'], rel=0.04)
        assert fine['sampled_integral_kg_s_m3'] == pytest.approx(original['sampled_integral_kg_s_m3'], rel=0.04)
    result = DenseOutput.model_validate_json(json.dumps(native_receipt.outputs))
    dose_input = history_dose_input(result, 'R60', exponent=1.0, reference_value=1.0)
    dose_receipt = calculate('effects/dose', dose_input, context=example.example_context())
    assert dose_receipt.outputs['normalized_dose_s'] == pytest.approx(result.histories[1].sampled_integral_kg_s_m3)

@pytest.mark.dense_native
def test_native_wrong_digest_and_context(engine):
    request = example.example_inputs('0' * 64)
    with pytest.raises(DenseEngineError, match='fingerprint'):
        calculate('dispersion/slabx-instantaneous', request, context=example.example_context())
    request = example.example_inputs(engine['engine_code_digest'])
    request['source']['asset_id'] = 'wrong'
    with pytest.raises(ValueError, match='identity'):
        calculate('dispersion/slabx-instantaneous', request, context=example.example_context())

def test_native_protocol_errors(monkeypatch):
    import subprocess
    from ccps_consequence.dense import _call

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired('worker', 1)
    monkeypatch.setattr(subprocess, 'run', timeout)
    with pytest.raises(DenseEngineError, match='timeout'):
        _call({'operation': 'capabilities'}, 1.0)
    from types import SimpleNamespace
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(stdout='not json', returncode=0))
    with pytest.raises(DenseEngineError, match='invalid JSON'):
        _call({'operation': 'capabilities'}, 1.0)

@pytest.mark.dense_native
def test_output_tampering_rejected(native_receipt):
    payload = copy.deepcopy(native_receipt.outputs)
    payload['histories'][0]['concentration_kg_m3'].pop()
    with pytest.raises(ValueError, match='shape'):
        DenseOutput.model_validate_json(json.dumps(payload))

def test_history_dose_trapezoid():
    histories = [dict(receptor_id='R1', concentration_kg_m3=[0.0, 2.0, 0.0], volume_fraction=[0.0, 0.2, 0.0], sampled_peak_kg_m3=2.0, sampled_peak_time_s=1.0, sampled_integral_kg_s_m3=2.0, tail_status='end_below_threshold')]
    inputs = dict(sample_times_s=[0.0, 1.0, 2.0], histories=histories, receptor_id='R1', exponent=2.0, reference_value_kg_m3=1.0, integration='sampled_trapezoid')
    receipt = calculate('dispersion/history-dose', inputs, context=example.example_context())
    assert receipt.outputs['normalized_dose_s'] == 4.0
    assert receipt.outputs['observation_end_s'] == 2.0
    inputs['sample_times_s'] = [0.0, 1.0]
    with pytest.raises(ValueError, match='unpaired'):
        calculate('dispersion/history-dose', inputs, context=example.example_context())

@pytest.mark.dense_native
def test_finite_window_censor_and_sample_refinement(engine, native_receipt):
    inputs = example.example_inputs(engine['engine_code_digest'])
    inputs['sample_times_s'] = [i * 0.5 for i in range(241)]
    fine = calculate('dispersion/slabx-instantaneous', inputs, context=example.example_context())
    for h, ref in zip(fine.outputs['histories'], native_receipt.outputs['histories']):
        assert h['sampled_peak_kg_m3'] == pytest.approx(ref['sampled_peak_kg_m3'], rel=0.03)
        assert h['sampled_integral_kg_s_m3'] == pytest.approx(ref['sampled_integral_kg_s_m3'], rel=0.02)
    inputs['sample_times_s'] = [float(i) for i in range(11)]
    inputs['simulation_end_s'] = 10.0
    short = calculate('dispersion/slabx-instantaneous', inputs, context=example.example_context())
    assert any((h['tail_status'] != 'end_below_threshold' for h in short.outputs['histories']))

@pytest.mark.dense_native
def test_http_and_dense_dag(engine, tmp_path):
    from fastapi.testclient import TestClient
    from ccps_consequence.http_api import create_app
    from ccps_consequence.workflow import Workflow, run_workflow
    inputs = example.example_inputs(engine['engine_code_digest'])
    context = example.example_context()
    payload = dict(context=context.model_dump(mode='json'), steps=[dict(id='dense', calculation_id='dispersion/slabx-instantaneous', inputs=inputs), dict(id='dose', calculation_id='dispersion/history-dose', inputs=dict(sample_times_s={'$ref': 'dense.sample_times_s'}, histories={'$ref': 'dense.histories'}, receptor_id='R60', exponent=1.0, reference_value_kg_m3=1.0, integration='sampled_trapezoid'))])
    result = run_workflow(Workflow.model_validate_json(json.dumps(payload)))
    assert result.steps[1].receipt.outputs['normalized_dose_s'] == pytest.approx(result.steps[0].receipt.outputs['histories'][1]['sampled_integral_kg_s_m3'])
    with TestClient(create_app()) as client:
        assert client.get('/api/ccps/dense/capabilities').json()['status'] == 'available'
        response = client.post('/api/ccps/calculate', json=dict(calculation_id='dispersion/slabx-instantaneous', inputs=inputs, context=context.model_dump(mode='json')))
        assert response.status_code == 200, response.text
        assert response.json()['validation_level'] == 'native_engine_executed'
    import sys
    assert 'slabx' not in sys.modules

def test_missing_optional_package_status(monkeypatch):
    from ccps_consequence.dense_worker import engine_info
    import importlib.metadata

    def missing(name):
        raise importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(importlib.metadata, 'version', missing)
    assert engine_info()['status'] == 'missing'

@pytest.mark.dense_native
def test_similarity_matches_native_small_window_reference(engine):
    """Different native postprocessor, near-instantaneous centreline limit; not field validation."""
    import subprocess
    import sys
    script = "\nimport sys\nsys.path.insert(0,sys.argv[1])\nfrom slabx.core.source import InstantaneousRelease\nfrom slabx.core.plume import run_dispersion\nfrom slabx.thermo.base import Substance,LegacyThermo,water_backend\nfrom slabx.submodels.atmosphere import Atmosphere\nfrom slabx.post.concentration import concentration_field\nfrom ccps_consequence.dense_profile import normalized_profile\ns=Substance(name='synthetic',mw=.064,cp_vapour=900.,cp_liquid=1800.,dh_vap=300000.,T_boil=230.,rho_liquid=1200.)\na=Atmosphere(u_ref=3.,z_ref=10.,T=290.,rh=30.,z0=.03,stability='D',p=101325.)\nr=InstantaneousRelease(substance=s,rate=0.,area=25.,duration=0.,mass=20.,T_source=280.,height=0.)\nt,_=run_dispersion(r,a,LegacyThermo(s),water_backend(),x_max=1.,t_max=120.,n_puff_steps=240)\nfield=concentration_field(t,a,z=0.,t_avg=.01,t_release=0.)\nerrors=[]\nfor i,clock in enumerate(t.t):\n    if clock < 10.:\n        continue\n    kernel=normalized_profile(dx=0.,y=0.,z=0.,center_z=float(t.z_c[i]),bx=float(t.b_shape_x[i]),by=float(t.b_shape[i]),beta_x=float(t.beta_x[i]),beta_y=float(t.beta[i]),sigma_z=float(t.sigma_z[i]))\n    own=kernel*4*t.b_half_x[i]*t.b_half[i]*t.h[i]*t.vol_frac[i]\n    if own > 1e-10 and own < .5:\n        errors.append(abs(own/field.peak[i]-1))\nassert errors and max(errors)<1e-3, errors\n"
    completed = subprocess.run([sys.executable, '-I', '-c', script, str(Path(__file__).parents[1] / 'src')], capture_output=True, text=True, timeout=30.0)
    assert completed.returncode == 0, completed.stderr
