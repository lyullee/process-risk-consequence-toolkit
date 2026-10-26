# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""JSON-first command line. stdout=data, stderr=errors, no implicit publication."""
import argparse
import json
from pathlib import Path
import sys
from . import calculate,verify_receipt,calculation_catalog,contract_schemas
from .contracts import Context,Receipt
from .workflow import Workflow,run_workflow


def main():
    parser=argparse.ArgumentParser(prog="prct",description=__doc__)
    parser.add_argument("--version",action="version",version="0.1.0")
    commands=parser.add_subparsers(dest="command",required=True)
    commands.add_parser("catalog")
    schema=commands.add_parser("schema")
    schema.add_argument("--calculation")
    calc=commands.add_parser("calculate")
    calc.add_argument("calculation_id")
    calc.add_argument("--input",type=Path,required=True)
    calc.add_argument("--context",type=Path,required=True)
    workflow=commands.add_parser("workflow")
    workflow.add_argument("path",type=Path)
    verify=commands.add_parser("verify")
    verify.add_argument("path",type=Path)
    commands.add_parser("capabilities")
    serve=commands.add_parser("serve")
    serve.add_argument("--host",default="127.0.0.1")
    serve.add_argument("--port",type=int,default=8765)
    args=parser.parse_args()
    try:
        if args.command=="catalog": result=calculation_catalog()
        elif args.command=="schema":
            result=contract_schemas()
            if args.calculation: result=result["calculations"][args.calculation]
        elif args.command=="calculate":
            result=calculate(args.calculation_id,json.loads(args.input.read_text(encoding="utf-8")),
                context=Context.model_validate_json(args.context.read_text(encoding="utf-8"))).model_dump(mode="json")
        elif args.command=="workflow": result=run_workflow(Workflow.model_validate_json(args.path.read_text(encoding="utf-8"))).model_dump(mode="json")
        elif args.command=="verify": result=verify_receipt(Receipt.model_validate_json(args.path.read_text(encoding="utf-8"))).model_dump(mode="json")
        elif args.command=="capabilities":
            from .dense import capabilities
            result=capabilities()
        else:
            import uvicorn
            from .http_api import create_app
            uvicorn.run(create_app(),host=args.host,port=args.port)
            return
        print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    except (ValueError,TypeError,KeyError,OSError,ImportError) as exc:
        print(json.dumps({"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr)
        raise SystemExit(2)
