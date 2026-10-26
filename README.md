# Process Risk Consequence Toolkit

**23 discoverable Python calculations, strict SI contracts, reproducible
receipts, JSON Schemas and dependency-traced workflows.** Apache-2.0.

The toolkit covers release/source screening, passive dispersion, fire and
explosion effects, normalized exposure, conditional risk, optional SLABx
dense-gas histories and an explicitly restricted coupled-layer research model.

This is an independent project. It is **not an official CCPS/AIChE product**,
an endorsed standard implementation, or a safety certification. The legacy
`ccps_consequence` import and schema IDs are compatibility identifiers.
No purchased standards, book text, tables, figures, worked examples or external
engine source are distributed. [Rights review](docs/COPYRIGHT_REVIEW.md).

## Start here

```bash
python -m pip install process-risk-consequence-toolkit
# Optional features, installed explicitly:
python -m pip install 'process-risk-consequence-toolkit[http,coupled,dense]'
```

**Publication status:** [Zenodo 0.1.0](https://doi.org/10.5281/zenodo.23659682) is available. PyPI publication is pending. The optional pinned `slabx==1.0.8` engine was locally tested but is not currently published on PyPI; the dense extra cannot yet be installed from PyPI alone. Base, HTTP and coupled features do not require it. Public CI runs without the native engine and reports native tests as skips. Do not substitute another version silently.

Python 3.12+. Base dependency: Pydantic. `coupled` adds NumPy, `dense` adds the
pinned separate `slabx==1.0.8` engine, and `http` adds FastAPI/Uvicorn.

```python
from ccps_consequence import Context, calculate, verify_receipt

context = Context(asset_id="T1", scenario_id="leak", operating_case_id="normal")
receipt = calculate("source/inventory", {
    "mass_rate_kg_s": 2.0, "duration_s": 8.0, "inventory_kg": 10.0
}, context=context)
assert receipt.outputs["released_mass_kg"] == 10.0
verify_receipt(receipt)
```

## Human and machine interfaces

| Need | Entry point |
|---|---|
| Complete user guide | [Manual](docs/MANUAL.md) / [한국어 안내](docs/MANUAL_KO.md) |
| Every module and all input/output fields | [Module index](docs/MODULES.md) / [shared models](docs/REFERENCE_MODELS.md) |
| Python discovery | `calculation_catalog()`, `contract_schemas()` |
| Command line | `prct --help`, `prct catalog`, `prct schema` |
| Typed request / response | Each module's `*Input` / output models |
| Machine contracts | [Schema index](contracts/ccps.contracts.v1.schema.json) |
| Dependency workflows | `Workflow`, `run_workflow`; [workflow guide](docs/MANUAL.md#workflows) |
| HTTP / interactive API docs | `prct serve`; `/docs`, `/openapi.json` |
| Maintenance / next session | [AGENTS.md](AGENTS.md), [developer handoff](docs/DEVELOPMENT.md) |
| Test evidence | [Validation](verification/VALIDATION.md), `verification/release.json` |

```bash
prct catalog
prct schema --calculation source/liquid
prct workflow examples/ccps_screening.workflow.json
prct capabilities
prct serve --host 127.0.0.1 --port 8765
```

CLI results are JSON on stdout, errors are JSON on stderr with a nonzero exit
code. HTTP calculation failures use 422; no silent fallback engine/model.

## Model map

| Family | Registered calculations | Scope |
|---|---:|---|
| Source | 5 | liquid/gas orifices, inventory, sensible-heat flash, supplied-flux evaporation |
| Dispersion / histories | 7 | Gaussian plume/puff, Richardson screen, SLABx instantaneous/release histories, sampled dose, coupled 1D layer |
| Fire | 4 | fireball size/duration, supplied solid flame, sphere radiation, pool energy |
| Effects / explosion | 6 | point radiation, dose, probit, threshold, TNT scaling, fixed EPA 1 psi endpoint |
| Conditional risk | 1 | explicit LOC frequency and mutually exclusive branches |

All 23 calculations and their parameters are documented individually in the
[generated module reference](docs/MODULES.md). Inputs use Pa absolute, K, kg,
m and s. Molecular weight for native dense contracts is **kg/mol**.
Evidence, applicability literals and basis fields are part of the contract,
not optional engineering judgments inferred by the software.

## Three different dense-gas routes

| Route | Calculation | Meaning |
|---|---|---|
| Instantaneous | `dispersion/slabx-instantaneous` | actual isolated SLABx puff dynamics plus authored receptor reconstruction |
| Finite / continuous histories | `dispersion/slabx-release-history` | native constant-segment plume-to-puff; pretransition reconstruction and segment independence are explicit approximations |
| Coupled research layer | `dispersion/coupled-layer-1d` | one shared nonlinear mass/species/momentum grid; **1D, isothermal, fixed width, vertically mixed** |

The coupled route is not a 2D/thermal/two-layer solver or a validated replacement
for SLAB/TWODEE. Entrainment and wind-relaxation closures require explicit user
qualification. Software conservation/refinement tests are not field validation.
Passive Gaussian routes do not become dense models because a screen is passed.

## Examples and interoperability

```bash
python examples/ccps_dense_history.py
python examples/ccps_release_history.py --mode variable
python examples/ccps_coupled_layer.py --compare-independent
```

All examples are newly authored synthetic data. PRISM left-held rows, API-581
release receipts and PHA LOC-frequency boundaries preserve source hashes and
ownership. External engine/software source is not included. The optional
`ccps_consequence.pha_adapter` requires a separately installed compatible PHA
Core; this distribution does not relicense or ship PHA Core or its UI/database.
[Integration manual](docs/INTEGRATIONS.md).

## Development and release

```bash
git clone https://github.com/lyullee/process-risk-consequence-toolkit.git
cd process-risk-consequence-toolkit
python -m pip install -e '.[dev,dense]'
python scripts/build_ccps_contracts.py
python scripts/build_manual.py
python -m pytest -q
python -m build
python -m twine check dist/*
python scripts/release_audit.py --dist
```

See [implementation history](docs/IMPLEMENTATION_HISTORY.md), [limitations](docs/LIMITATIONS.md),
[contribution rules](CONTRIBUTING.md) and [release checklist](docs/RELEASING.md).
Validation counts in this portable distribution are reported separately from
the earlier host PHA integration runs. Do not reuse old counts as release proof.

## License and citation

Copyright 2026 Ugwiyeon Lee. [Apache-2.0](LICENSE); [NOTICE](NOTICE) and
[third-party boundaries](THIRD_PARTY_NOTICES.md) apply. Referenced organizations'
names and marks remain theirs; no logo or endorsement rights are granted.
Use [CITATION.cff](CITATION.cff) for citation metadata. DOI and index publication
links are added only after their publication is verified.
