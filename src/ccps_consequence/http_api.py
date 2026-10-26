# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Optional standalone HTTP interface; no PHA host/database is bundled."""
import json
from . import calculate,calculation_catalog,contract_schemas
from .contracts import Context,Model
from .workflow import Workflow,run_workflow


class CalculateRequest(Model):
    calculation_id: str
    context: Context
    inputs: dict


def create_app():
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app=FastAPI(title="Process Risk Consequence Toolkit",version="0.1.0")

    @app.exception_handler(ValueError)
    async def invalid(request,exc):
        return JSONResponse(status_code=422,content={"error":str(exc)})

    @app.get("/api/ccps/catalog")
    def catalog():
        return calculation_catalog()

    @app.get("/api/ccps/schemas")
    def schemas():
        return contract_schemas()

    @app.get("/api/ccps/dense/capabilities")
    def dense_capabilities():
        from .dense import capabilities
        return capabilities()

    @app.post("/api/ccps/calculate")
    def execute(payload: dict):
        request=CalculateRequest.model_validate_json(json.dumps(payload,allow_nan=False))
        return calculate(request.calculation_id,request.inputs,context=request.context).model_dump(mode="json")

    @app.post("/api/ccps/workflow")
    def workflow(payload: dict):
        return run_workflow(Workflow.model_validate_json(json.dumps(payload,allow_nan=False))).model_dump(mode="json")
    return app
