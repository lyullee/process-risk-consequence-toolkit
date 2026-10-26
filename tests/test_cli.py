# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
import json
import pytest
from ccps_consequence.cli import main


def test_cli_catalog(monkeypatch,capsys):
    monkeypatch.setattr('sys.argv',['prct','catalog'])
    main()
    assert len(json.loads(capsys.readouterr().out))==23


def test_cli_error_is_json(monkeypatch,capsys):
    monkeypatch.setattr('sys.argv',['prct','schema','--calculation','missing'])
    with pytest.raises(SystemExit) as exc:main()
    assert exc.value.code==2
    assert 'error' in json.loads(capsys.readouterr().err)


def test_cli_calculation(monkeypatch,capsys,tmp_path):
    (tmp_path/'input.json').write_text(json.dumps(dict(mass_rate_kg_s=2.,duration_s=8.,inventory_kg=10.)),encoding='utf-8')
    (tmp_path/'context.json').write_text(json.dumps(dict(asset_id='A',scenario_id='S',operating_case_id='O')),encoding='utf-8')
    monkeypatch.setattr('sys.argv',['prct','calculate','source/inventory','--input',str(tmp_path/'input.json'),'--context',str(tmp_path/'context.json')])
    main()
    assert json.loads(capsys.readouterr().out)['outputs']['released_mass_kg']==10.
