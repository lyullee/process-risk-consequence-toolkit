# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Install exact wheel into a temporary target outside checkout and exercise it."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--with-optional',action='store_true')
    args=parser.parse_args()
    wheel=ROOT/'dist/process_risk_consequence_toolkit-0.1.0-py3-none-any.whl'
    fixtures={}
    if args.with_optional:
        sys.path.insert(0,str(ROOT/'examples'))
        for label,filename in [('instant','ccps_dense_history.py'),('release','ccps_release_history.py'),('coupled','ccps_coupled_layer.py')]:
            module=runpy.run_path(str(ROOT/'examples'/filename))
            fixtures[label]={'inputs':module['example_inputs']() if label=='coupled' else module['example_inputs']('0'*64),
                'context':module['example_context']().model_dump(mode='json')}
    script='''
import sys,json,io,contextlib
sys.path.insert(0,sys.argv[1])
payload_fixtures=json.loads(sys.argv[2])
import ccps_consequence as package
from ccps_consequence import Context,calculate,verify_receipt,contract_schemas
assert package.__file__.startswith(sys.argv[1])
assert len(contract_schemas()['calculations'])==23
assert not any(n in sys.modules for n in ['slabx','numpy','pha_core','lh2_tno','api581'])
r=calculate('source/inventory',{'mass_rate_kg_s':2.,'duration_s':8.,'inventory_kg':10.},context=Context(asset_id='A',scenario_id='S',operating_case_id='O'))
assert verify_receipt(r)==r and r.outputs['released_mass_kg']==10.
from ccps_consequence.cli import main
sys.argv=['prct','catalog']
buffer=io.StringIO()
with contextlib.redirect_stdout(buffer):main()
assert len(json.loads(buffer.getvalue()))==23
from ccps_consequence import pha_adapter
assert 'pha_core' not in sys.modules
fixtures=payload_fixtures
if fixtures:
    from ccps_consequence.dense import capabilities
    info=capabilities()
    assert info['status']=='available'
    ids={'instant':'dispersion/slabx-instantaneous','release':'dispersion/slabx-release-history','coupled':'dispersion/coupled-layer-1d'}
    for label,fixture in fixtures.items():
        payload=fixture['inputs']
        if label!='coupled':payload['expected_engine_code_digest']=info['engine_code_digest']
        receipt=calculate(ids[label],payload,context=Context.model_validate_json(json.dumps(fixture['context'])))
        assert not receipt.physical_validation_claim
    assert 'slabx' not in sys.modules
'''
    with tempfile.TemporaryDirectory(prefix='prct-wheel-') as target:
        subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-compile','--target',target,str(wheel)],check=True,capture_output=True,text=True)
        completed=subprocess.run([sys.executable,'-I','-c',script,target,json.dumps(fixtures)],cwd=target,capture_output=True,text=True)
        if completed.returncode:
            print(completed.stderr,file=sys.stderr)
            raise SystemExit(completed.returncode)
    report={'wheel':wheel.name,'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'temporary_install':'passed',
        'installed_api_cli_schemas':'passed','optional_native_and_coupled':'passed' if args.with_optional else 'not_requested',
        'pha_core_source_bundled':False,'native_source_bundled':False}
    (ROOT/'verification/wheel-smoke.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
