# Standalone release verification

Initial0.1.0 standalone preparation,2026-10-26. Python3.14.8 on Windows.
The portable suite passed **84 tests**, no failures/skips,23.22s, including
actual optional SLABx histories, coupled conservation/refinement, new own
HTTP and CLI interfaces.50 dependency deprecation warnings were observed.

The originating PHA host's183 tests are historical host evidence, not this
distribution's CI claim. Host-only PHA tests and fixtures were deliberately
excluded; public tests were ported to the newly authored standalone HTTP host.
All23 registered calculations retain their direct test/section/reference map.

Validated boundaries: synthetic analytic identities; mass/partition/flux
ledgers; Gaussian/fire geometry; exposure/probability ownership; DAG failures
and lineage; native engine pin/clock/domain/transition/refinement; coupled
characteristic speed, positivity/CFL, shared-pulse non-superposition, boundaries,
grid/time refinement; HTTP/CLI JSON behavior and optional dependency isolation.

`python -m build` produced wheel and source distribution. `twine check` passed
both. `release_audit.py --dist` found no denied file category, credential-like
string or local user path in the scanned source and archives. This bounded
scan and source-provenance review do not establish legal immunity.

Installed-wheel smoke is recorded in wheel-smoke.json. Source/package audit
and hashes are in release-audit.json/source-manifest.json. Final test counts,
dependency versions and external publication state are machine-readable in
release.json/publication.json. Raw JUnit logs remain local in ignored artifacts
because they can contain machine-specific paths.

Software checks are not independent experimental evaluation, closure
qualification, field/site validation or CCPS conformity. The coupled model
retains a restricted research status. Dependency model claims are not adopted
as this package's own certification.
