# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
import copy
import json
from pathlib import Path
import pytest
from ccps_consequence import Context, contract_schemas
from ccps_consequence.workflow import Workflow, run_workflow, WorkflowError

def workflow_payload():
    return dict(context=dict(asset_id='tank', scenario_id='leak', operating_case_id='normal'), steps=[dict(id='inventory', calculation_id='source/inventory', inputs=dict(mass_rate_kg_s={'$ref': 'release.mass_rate_kg_s'}, duration_s=20.0, inventory_kg=100.0)), dict(id='release', calculation_id='source/liquid', inputs=dict(area_m2=0.001, density_kg_m3=900.0, upstream_pressure_pa_abs=200000.0, downstream_pressure_pa_abs=100000.0, discharge_coefficient=0.6, phase='incompressible_nonflashing_liquid'))])

def parse(payload):
    return Workflow.model_validate_json(json.dumps(payload))

def test_dag_forward_reference_and_lineage():
    workflow = parse(workflow_payload())
    result = run_workflow(workflow)
    assert [r.id for r in result.steps] == ['release', 'inventory']
    assert result.steps[1].receipt.outputs['released_mass_kg'] == 100.0
    assert result.steps[1].dependency_receipt_digests == {'release': result.steps[0].receipt.digest()}
    assert result.workflow_digest == workflow.digest()
    assert result == run_workflow(workflow)

@pytest.mark.parametrize('ref,match', [('missing.mass_rate_kg_s', 'missing'), ('release.unknown', 'unknown'), ('release', 'step.output_field')])
def test_bad_references(ref, match):
    payload = workflow_payload()
    payload['steps'][0]['inputs']['mass_rate_kg_s']['$ref'] = ref
    with pytest.raises(ValueError, match=match):
        parse(payload)

def test_cycle_and_downstream_type_failure():
    payload = workflow_payload()
    payload['steps'][0]['inputs'] = dict(mass_rate_kg_s=1.0, inventory_kg=10.0, duration_s={'$ref': 'release.effective_duration_s'})
    payload['steps'][1]['calculation_id'] = 'source/inventory'
    payload['steps'][1]['inputs'] = dict(mass_rate_kg_s=1.0, inventory_kg=10.0, duration_s={'$ref': 'inventory.effective_duration_s'})
    with pytest.raises(ValueError, match='cycle'):
        parse(payload)
    payload = workflow_payload()
    payload['steps'][0]['inputs']['mass_rate_kg_s'] = {'$ref': 'release.regime'}
    with pytest.raises(WorkflowError, match='inventory'):
        run_workflow(parse(payload))

def test_dimensionally_invalid_float_link_rejected():
    payload = workflow_payload()
    payload['steps'][0]['inputs']['duration_s'] = {'$ref': 'release.mass_rate_kg_s'}
    with pytest.raises(ValueError, match='unit mismatch'):
        parse(payload)

def test_extra_fields_and_model_copy_are_revalidated():
    workflow = parse(workflow_payload())
    bad_step = workflow.steps[1].model_copy(update={'inputs': {**workflow.steps[1].inputs, 'extra': 1}})
    with pytest.raises(WorkflowError):
        run_workflow(workflow.model_copy(update={'steps': (bad_step,)}))

def test_schema_bundle_matches_checked_in_contract():
    root = Path(__file__).parents[1]
    saved = json.loads((root / 'contracts/ccps.contracts.v1.schema.json').read_text(encoding='utf-8'))
    assert saved == contract_schemas()
    for schema in [saved['receipt'], saved['workflow'], saved['frequency'], saved['provider_result']]:
        assert schema['type'] == 'object'

def test_example_executes():
    root = Path(__file__).parents[1]
    example = parse(json.loads((root / 'examples/ccps_screening.workflow.json').read_text(encoding='utf-8')))
    result = run_workflow(example)
    assert {s.id for s in result.steps} == {'gas', 'inventory', 'plume', 'dose', 'probit'}
    p = next((s.receipt.outputs['probability'] for s in result.steps if s.id == 'probit'))
    assert 0.0 <= p <= 1.0

def test_fire_explosion_example_and_dimensions():
    root = Path(__file__).parents[1]
    raw = json.loads((root / 'examples/ccps_fire_explosion.workflow.json').read_text(encoding='utf-8'))
    result = run_workflow(parse(raw))
    rows = {s.id: s for s in result.steps}
    assert rows['sphere'].receipt.outputs['heat_flux_w_m2'] == rows['solid'].receipt.outputs['heat_flux_w_m2']
    assert rows['blast_endpoint'].receipt.outputs['endpoint_distance_m'] == 17.0
    assert rows['dense_screen'].receipt.outputs['screening'] == 'dense_model_required'
    assert rows['thermal_dose'].dependency_receipt_digests.keys() == {'fireball', 'sphere'}
    raw['steps'][1]['inputs']['diameter_m'] = {'$ref': 'fireball.duration_s'}
    with pytest.raises(ValueError, match='unit mismatch'):
        parse(raw)
