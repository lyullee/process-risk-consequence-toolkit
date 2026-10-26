# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
import copy
import json
import pytest
from fastapi.testclient import TestClient
from ccps_consequence import Context, Evidence, calculate
from ccps_consequence.contracts import digest
from ccps_consequence.integrations import ExternalSource, ProviderRequest, ProviderResult, evaluate_provider, api581_release_source

def provider_context():
    return Context(asset_id='tank', scenario_id='leak', operating_case_id='normal', evidence=(Evidence(id='source', kind='synthetic', citation='Synthetic source', locator='fixture'),))

def provider_request():
    context = provider_context()
    source = ExternalSource(asset_id='tank', scenario_id='leak', operating_case_id='normal', origin='prism', source_digest='0' * 64, source_code_digest='1' * 64, evidence_ids=('source',), phase='two_phase', mass_rate_kg_s=2.0, duration_s=5.0, released_mass_kg=10.0, history_basis='constant_rate')
    return ProviderRequest(context=context, source=source, engine='prism', model_id='explicit-dense-model', expected_engine_code_digest='2' * 64, receptor_id='R1', distance_m=100.0, quantity='concentration_kg_m3', settings={'weather_case': 'synthetic'})

class SyntheticProvider:
    """Contract double, explicitly not a PRISM engine test."""

    def evaluate(self, request):
        return ProviderResult(request_digest=request.digest(), engine=request.engine, model_id=request.model_id, engine_version='synthetic-test-double', engine_code_digest=request.expected_engine_code_digest, receptor_id=request.receptor_id, quantity=request.quantity, value=0.01, evidence_ids=('source',), limitations=('Synthetic provider; no physical validation.',))

def test_explicit_provider_and_binding_failures():
    request = provider_request()
    assert evaluate_provider(request, SyntheticProvider()).value == 0.01
    with pytest.raises(ValueError, match='unavailable'):
        evaluate_provider(request, None)

    class WrongProvider(SyntheticProvider):

        def evaluate(self, request):
            return super().evaluate(request).model_copy(update={'request_digest': 'f' * 64})
    with pytest.raises(ValueError, match='binding'):
        evaluate_provider(request, WrongProvider())
    with pytest.raises(ValueError, match='mass/rate'):
        ExternalSource.model_validate_json(request.source.model_copy(update={'released_mass_kg': 1.0}).model_dump_json())

def test_api581_wire_mapping_is_explicit():
    context = provider_context()
    receipt = dict(calculation_id='release/gas', code_fingerprint='3' * 64, engine_version='synthetic', input_hash='4' * 64, context={'asset_id': 'tank'}, outputs={'mass_rate_kg_s': 2.0})
    source = api581_release_source(receipt, context=context, phase='vapour', duration_s=10.0, expected_code_digest='3' * 64, evidence_ids=('source',))
    assert source.released_mass_kg == 20.0
    assert source.source_digest == digest(receipt)
    receipt['calculation_id'] = 'consequence/area'
    with pytest.raises(ValueError, match='only API-581'):
        api581_release_source(receipt, context=context, phase='vapour', duration_s=10.0, expected_code_digest='3' * 64, evidence_ids=('source',))
