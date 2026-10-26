# User manual

This manual covers the standalone0.1.0 distribution. Start with README, then
[all 23 module pages](MODULES.md). Exact required fields, defaults, enums,
bounds and nested contracts come from the generated schemas, not paraphrases.

## Installation and model selection

Base: `pip install process-risk-consequence-toolkit` (Python3.12+, Pydantic).
Use `[http]`, `[coupled]`, `[dense]` only for the corresponding feature. A base
import/schema query does not import SLABx, NumPy, PHA, API-581 or PRISM engines.
Missing optional packages fail explicitly; a model is never silently replaced.

| Task | Select | Read before use |
|---|---|---|
| Orifice/inventory/flash | source/* | Public primitive assumptions on the individual page |
| Passive concentration | dispersion/plume or puff | Supply sigmas; no dense-gas or stability inference |
| Dense applicability only | dispersion/richardson-screen | Screen is not a concentration model or auto-router |
| Instantaneous dense history | dispersion/slabx-instantaneous | [Dense history](CCPS_DENSE_HISTORY.md) |
| Finite/continuous history | dispersion/slabx-release-history | [Release history](CCPS_RELEASE_HISTORY.md); explicit approximations |
| Interacting time-variable source | dispersion/coupled-layer-1d | [Coupled layer](CCPS_COUPLED_LAYER.md); restricted research model |
| Fire/endpoint | fire/*, effects/*, explosion/* | Geometry, coefficient source, fixed endpoint limits |
| Conditional contribution | risk/conditional | LOC frequency, exhaustive branches, once-only factor ownership |

## Units and validation

SI names are literal: Pa absolute, K, kg, m, s, W, J. Probabilities and
fractions are dimensionless. Native molecular weight is kg/mol, while a
separately supplied API-581 input may use kg/kmol: no automatic conversion is
inferred. Angular, gauge-pressure and Celsius conversions must be explicit.
NaN/Inf, booleans as numbers, numeric strings, out-of-range values and unknown
fields are rejected. Python models are strict/frozen; tuple-valued Python
fields require tuples. Use `model_validate_json` for JSON arrays.

Applicability/phase/correlation literals, basis strings and evidence references
are required engineering declarations, not inferred endorsements. Unsupported
IDs, missing engines or invalid ledgers yield errors, not default zero values.

## Python

```python
from ccps_consequence import Context, calculate, verify_receipt
ctx=Context(asset_id="T1", scenario_id="S1", operating_case_id="normal")
r=calculate("source/inventory", {
    "mass_rate_kg_s":2.0, "duration_s":8.0, "inventory_kg":10.0
}, context=ctx)
assert r.outputs["released_mass_kg"]==10.0
verify_receipt(r)
```

Typed `*Input` objects also work. Call `calculate` for receipts; raw domain
functions return typed numerical outputs without the receipt envelope.
`calculation_catalog()` and `contract_schemas()` discover all capabilities.
The schema bundle is an index of standalone schemas, not itself a single
request-validator schema. Relational constraints are enforced in Python.

## Receipts and evidence

Context identifies asset/scenario/operating case and synthetic or engineering
review status. Evidence records contain id, kind, citation, locator and optional
SHA256/URL. Duplicate/missing references are rejected at applicable boundaries.
Engineering input status requires non-synthetic evidence; it does not grant
model/site validation. Hashes establish reproducibility, not authenticity.

Receipts include normalized inputs, input/output/code digests, version,
context/evidence IDs, topic references, direct public method sources and
limitations. `verify_receipt` recomputes against current code. A changed source
tree is stale; source changes after process startup require restart.
Do not edit nested dicts or use `model_copy(update=...)` as validation.
Store the request, workflow, receipt and environment versions together.

Validation levels distinguish synthetic analytic tests, actual optional native
engine execution and restricted research numerical tests. None is field
validation, whole-facility QRA, SIL certification or regulatory approval.

## Workflows

```python
from pathlib import Path
from ccps_consequence.workflow import Workflow, run_workflow
w=Workflow.model_validate_json(
    Path("examples/ccps_screening.workflow.json").read_text(encoding="utf-8")
)
result=run_workflow(w)
```

Each step has id, calculation_id and inputs. `{"$ref":"gas.mass_rate_kg_s"}`
selects a named output field, including inside arrays/nested inputs. Forward
references execute in DAG order. Missing fields, duplicate IDs and cycles fail.
Known dimensions are checked; no conversion or complete semantic proof occurs.
Each step retains parent receipt digests. A failed step yields WorkflowError
with its step_id and no success workflow receipt. Preserve original workflow
JSON to retain the original reference expressions.

Histories connect through `sample_times_s` and `histories` to
`dispersion/history-dose`; dose can feed supplied-coefficient probit and then
conditional risk. Tail flags and source-active-at-window-end must be reviewed;
unsampled peaks/infinite tails are not inferred or zero-filled.

## CLI and HTTP

`prct catalog`, `prct schema --calculation source/liquid`,
`prct calculate ID --input input.json --context context.json`,
`prct workflow workflow.json`, `prct verify receipt.json`, `prct capabilities`.
Successful stdout is JSON. Errors go to stderr with exit2. `prct --version`
prints the distribution version. `prct serve` needs `[http]`.

HTTP routes: GET `/api/ccps/catalog`, `/api/ccps/schemas`,
`/api/ccps/dense/capabilities`; POST `/api/ccps/calculate` with
`{calculation_id,context,inputs}` and `/api/ccps/workflow` with Workflow JSON.
`/docs` is interactive documentation; `/openapi.json` is machine-readable.
Default bind127.0.0.1:8765. The standalone service has no account system,
authentication, job scheduler, PHA baseline store or production deployment
hardening. Do not expose it as a public service without an appropriate host.

## Reproduction and maintenance

Run examples from a checkout. Native examples explicitly probe/pin an engine
fingerprint; production workflows should use a reviewed saved fingerprint,
not automatically trust a newly discovered installation. NumPy/SLABx outputs
depend on recorded versions and sampling resolution.

See [validation evidence](../verification/VALIDATION.md), [limitations](LIMITATIONS.md),
[integrations](INTEGRATIONS.md), [developer handoff](DEVELOPMENT.md),
[rights review](COPYRIGHT_REVIEW.md) and [release procedure](RELEASING.md).
