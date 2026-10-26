# Third-party boundaries

The project's own code and documentation are Apache-2.0, copyright 2026
Ugwiyeon Lee. The author confirmed authority to distribute and license this
new consequence package. This statement does not grant rights in references,
trademarks, third-party software or separately owned PHA/PRISM projects.

| Item | Role | License / treatment |
|---|---|---|
| Python | Runtime | PSF; not vendored |
| Pydantic | Base contracts | MIT; installed dependency, not vendored |
| NumPy | Optional coupled numerical arrays | BSD-3-Clause; not vendored |
| SLABx 1.0.8 | Optional separate dense-gas engine | Installed metadata: MIT; source not included |
| SciPy | SLABx transitive numerical dependency | BSD-3-Clause; not vendored |
| FastAPI / Starlette | Optional HTTP service | MIT / BSD-3-Clause; not vendored |
| Uvicorn | Optional HTTP runner | BSD-3-Clause; not vendored |
| pytest / HTTPX | Test dependencies | MIT / BSD-3-Clause; not vendored |
| PHA Core / PRISM / API-581 | Separately installed or wire-level interfaces | No source or rights included |
| AIChE/CCPS 1999 consequence-analysis book | Bibliographic/topic mapping only | Copyrighted; no source content or worked examples included |
| NOAA NOS OR&R 43 (2013) | Direct public equation references | URL and equation-location citations; document not bundled |
| EPA-550-B-99-009 (1999) Appendix C | Fixed 1 psi screening equation reference | URL and equation locator; no tables/database bundled |
| Research papers / Clawpack documentation | Model-family / numerical-method context | Citations only; no paper, code or figures copied |

SLABx explicitly documents consultation of original Fortran and does not claim
clean-room status. We do not relicense or characterize its provenance as our
own. Optional use requires the recipient's separate dependency review.
The authored reconstruction/adapters are not original SLAB, TWODEE, or a full
implementation of a cited two-layer paper. No dependency/source license is
overridden by Apache-2.0 for this project.

No institutional logos, protected source PDFs, extracted text/OCR, book
correlation tables, chemical/probit databases, original example answers,
private plant records, credentials, or local machine logs are distributed.

See docs/COPYRIGHT_REVIEW.md for review methodology, exclusions and unresolved
legal questions. Public availability is not treated as blanket permission.
