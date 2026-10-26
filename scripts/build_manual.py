# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Generate complete field references from the actual registered contracts."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from ccps_consequence.catalog import CALCULATIONS,calculation_catalog
from ccps_consequence.workflow import UNITS

UNITS={**UNITS,"molecular_weight_kg_mol":"kg/mol","height_m":"m","rate_kg_s":"kg/s","start_s":"s","end_s":"s",
    "simulation_end_s":"s","timeout_s":"s","plume_distance_limit_m":"m","width_m":"m","source_start_m":"m",
    "x_min_m":"m","x_max_m":"m","maximum_step_s":"s","wind_relaxation_time_s":"s","injection_velocity_m_s":"m/s",
    "pure_vapour_density_kg_m3":"kg/m3","tail_threshold_kg_m3":"kg/m3","annual_frequency_per_year":"year^-1",
    "sampled_integral_kg_s_m3":"kg*s/m3","surface_emissive_power_w_m2":"W/m2"}


def unit(name):
    if name in UNITS:return UNITS[name]
    for suffix,value in [("_kg_m2_s","kg/m2/s"),("_kg_s_m3","kg*s/m3"),("_kg_m2","kg/m2"),("_j_kg_k","J/kg/K"),
        ("_kg_mol","kg/mol"),("_kg_m3","kg/m3"),("_m_s2","m/s2"),("_m_s","m/s"),("_w_m2","W/m2"),
        ("_pa_abs","Pa absolute"),("_j_kg","J/kg"),("_kg_s","kg/s"),("_m2","m2"),("_kg","kg"),("_s","s"),("_m","m"),("_k","K"),("_pa","Pa"),("_j","J"),("_w","W")]:
        if name.endswith(suffix):return value
    return "dimensionless / metadata / nested; see contract"


def kind(field):
    if "$ref" in field:return field["$ref"].split("/")[-1]
    if "anyOf" in field:return " or ".join(kind(x) for x in field["anyOf"])
    if field.get("type")=="array":return "array["+kind(field.get("items",{}))+"]"
    if "const" in field:return "literal "+str(field["const"])
    if "enum" in field:return "enum "+", ".join(map(str,field["enum"]))
    return field.get("type","object")


def table(schema):
    lines=["| Field | Type / allowed values | Required / default | Unit | Bounds |","|---|---|---|---|---|"]
    for name,field in schema.get("properties",{}).items():
        required="required" if name in schema.get("required",[]) else "default `"+json.dumps(field.get("default"),ensure_ascii=False)+"`"
        bounds="; ".join(f"{k}={field[k]}" for k in ["minimum","exclusiveMinimum","maximum","exclusiveMaximum","minLength","maxLength","minItems","maxItems","pattern"] if k in field)
        lines.append(f"| `{name}` | {kind(field).replace('|','/')} | {required} | {unit(name)} | {bounds} |")
    return lines


def main():
    folder=ROOT/"docs/modules"
    folder.mkdir(parents=True,exist_ok=True)
    index=["# Complete module reference","","Generated from the 23 actual Python input/output contracts; regenerate, do not edit field tables by hand.",
        "Nested types are documented in [shared models](REFERENCE_MODELS.md). SI suffixes are authoritative; schema carries exact enums/bounds.","",
        "| ID | Input model | Output model | Execution |","|---|---|---|---|"]
    definitions={}
    for item in calculation_catalog():
        key=item["calculation_id"]
        calc=CALCULATIONS[key]
        filename=key.replace("/","__")+".md"
        inp,out=calc.input_type.model_json_schema(),calc.output_type.model_json_schema()
        for schema in (inp,out): definitions.update(schema.get("$defs",{}))
        lines=[f"# `{key}`","",f"Python: `{item['python_path']}`.","",f"Execution: `{calc.execution_kind}`. Coverage: `{item['coverage']}`.","",
            "## Purpose and limitations","",calc.limitation,"","## Input",""]+table(inp)+["","## Output",""]+table(out)
        lines += ["","## Evidence and traceability","",f"CCPS topic section identifiers: {calc.section}. These locate topics, not copied book equations.","",
            f"Direct tests: `{item['test']}`.","","Direct references:",""]+["- "+ref for ref in calc.method_references]
        if not calc.method_references: lines.append("- Independently authored public-physics primitive; see [rights/provenance review](../COPYRIGHT_REVIEW.md) and general NOAA context in the catalog.")
        lines += ["","## Failure and integration behavior","","Finite SI values and forbidden extra fields are checked by Pydantic. Relational checks, source/context identities, evidence references, mass ledgers and model-specific assumptions are checked in Python. See [manual](../MANUAL.md), [shared nested contracts](../REFERENCE_MODELS.md), and the standalone JSON Schema index.",
            "","Call with `calculate(id, inputs, context=context)` to obtain a hashed receipt. Direct numeric functions do not add receipt provenance. No calculation establishes field validation or standard conformity.",""]
        (folder/filename).write_text("\n".join(lines),encoding="utf-8")
        index.append(f"| [{key}](modules/{filename}) | `{calc.input_type.__name__}` | `{calc.output_type.__name__}` | `{calc.execution_kind}` |")
    index += ["","Other public infrastructure: `contracts`, `catalog`, `api`, `workflow`, `integrations`, optional `pha_adapter`, `cli`, `http_api`; see [manual](MANUAL.md) and [integration contracts](INTEGRATIONS.md).",""]
    (ROOT/"docs/MODULES.md").write_text("\n".join(index),encoding="utf-8")
    lines=["# Nested input/output contracts","","Generated definitions include every nested field used by registered calculations. JSON Schema relational limits also apply in Python.",""]
    for name,schema in sorted(definitions.items()): lines += [f"## {name}",""]+table(schema)+[""]
    (ROOT/"docs/REFERENCE_MODELS.md").write_text("\n".join(lines),encoding="utf-8")


if __name__=="__main__": main()
