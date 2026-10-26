# Release procedure and destination identities

Project/distribution: process-risk-consequence-toolkit. Python compatibility
namespace: ccps_consequence. Initial version0.1.0. Owner: lyullee.

1. Validate author/license/provenance boundaries; never publish book material.
2. Regenerate contracts/module references, run portable tests and build.
3. Run twine check, archive audit and installed-wheel smoke outside the checkout.
4. Record sanitized counts/versions/source hashes and exact artifact checksums.
5. Commit only the clean source/docs/tests/contracts. Push main and tag v0.1.0.
6. Create the GitHub release with source archive and matching wheel/sdist.
7. Publish the exact verified wheel/sdist to PyPI. Prefer a narrowly configured
   trusted publisher: owner lyullee, repo process-risk-consequence-toolkit,
   workflow publish.yml, environment pypi. Never put a token in source/logs.
8. Deposit the same software release in Zenodo under Apache-2.0 with its
   creators/version and GitHub/PyPI links; verify the record/DOI.
9. Only after observation, update citation/readme/publication.json with actual
   URLs/DOI and status. No fake placeholders that look like a real DOI.

GitHub Actions CI verifies the checkout. The separate publishing workflow uses
OIDC and requires a matching PyPI trusted publisher; a workflow file alone does
not create the PyPI account's publisher. Authentication, MFA and privileged
account changes may require the human account owner. A failed/unconfigured
publisher must be reported, not described as a successful index registration.

`verification/publication.json` is the observed external-state record; the
source version and any later metadata-only changes are distinguished there.

## Observed 0.1.0 publication

PyPI: https://pypi.org/project/process-risk-consequence-toolkit/0.1.0/ . OIDC publisher is limited to lyullee/process-risk-consequence-toolkit, publish.yml, environment pypi. Successful run: https://github.com/lyullee/process-risk-consequence-toolkit/actions/runs/40291493942 . The published source commit is a864f9e6ad4db66f6e29349e1c4c35d4101ff671. Fresh isolated base/HTTP/coupled installation, console CLI, Python inventory/receipt/schema and OpenAPI checks passed; file hashes are in verification/pypi-install.json.

Zenodo DOI 10.5281/zenodo.23659682 preserves earlier local verified artifacts from initial source 64bf14a. The Python implementation is unchanged, while documentation/CI metadata and archive hashes differ. Do not claim byte identity across the two deposits. No GitHub release-triggered rerun is needed: 0.1.0 is already on PyPI and filenames cannot be replaced. Any revised package requires a new version. The optional native slabx 1.0.8 public availability remains unresolved and must not be silently substituted.
