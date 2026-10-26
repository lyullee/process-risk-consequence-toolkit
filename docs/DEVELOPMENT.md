# Developer handoff

## Architecture

`source`, `dispersion`, `fire`, `effects`, `explosion`, `risk`: typed numeric
modules. `dense`/`dense_profile`/`dense_worker`: optional native boundary and
authored spatial reconstruction. `release_history`/worker: left-held mapping,
qualified native transitions and explicit approximation. `coupled`: shared
research finite-volume field. `contracts`/`catalog`/`api`/`workflow`: validation,
dispatch, source fingerprints, evidence and DAG receipts. `integrations` and
lazy `pha_adapter`: interoperability. `cli`, optional `http_api`: user interfaces.

## Reproduce from a new session

```text
python -m pip install -e ".[dev,dense]"
python scripts/build_ccps_contracts.py
python scripts/build_manual.py
python -m pytest -q
python -m build
python -m twine check dist/*
python scripts/release_audit.py --dist
```

Tests needing the separate native engine skip when unavailable; record skips
explicitly. Coupled tests need NumPy. The base path needs only Pydantic.
Test CLI/HTTP interfaces and installed wheels outside the source checkout.

## Change checklist

1. Explain applicability and equation/reference provenance before adding a model.
2. Add strict input/output contracts; do not weaken shared gates for convenience.
3. Register the calculation, scope, execution kind, direct tests and references.
4. Add synthetic analytic/limit/conservation tests and relevant negative tests.
5. For PDE changes, check characteristic speeds, positivity/CFL, source timing,
   boundary budgets, grid/time refinement and the coupling/non-superposition case.
6. Regenerate schemas/manuals; check diffs and imported installed package.
7. Update validation and implementation/release notes; audit source and artifacts.

## Known priorities

Independent model evaluation/field benchmarks are not completed. Coupled1D
closure qualification, energy and upper-layer dynamics,2D spreading and real
PRISM source qualification require separate development/evidence. Preserve
the research label; do not broaden it because numerical tests pass.
Use physically qualified near-source boundaries, not inferred nozzle-to-pool
or2phase-to-gas conversions. Do not treat old historical host tests as portable CI.

## Reproducibility caveats

Changing any package source invalidates code fingerprints. Start a fresh Python
process after edits. Native package fingerprints cover that engine's Python
source; dependency versions are recorded separately. Hashes are not signatures.
Generated documentation is a deterministic view of actual contracts, not a
replacement for Python relational validation. Raw test logs are kept in ignored
artifacts; only sanitized evidence summaries are published.
