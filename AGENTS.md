# Development entry point

Read README.md, docs/DEVELOPMENT.md, docs/COPYRIGHT_REVIEW.md and
verification/VALIDATION.md before edits. Respect the original author/source
boundary. This project is Apache-2.0, not an official CCPS/AIChE product.

- Preserve the23 registered contracts or version intentional breaking changes.
- Update registry, schemas, module references, example/tests and evidence together.
- Never add purchased PDFs, OCR, figures, proprietary coefficient tables,
  worked examples, private plant data, secrets or external-engine source.
- Public equations must have direct primary references; citations are not licenses.
- No silent model substitution or automatic relaxation of physics gates.
- Keep coupled1D research scope explicit. Do not claim2D/thermal/site validation.
- Keep optional engines isolated/lazy; base import/schema should need only Pydantic.
- Run appropriate tests, generation and archive audits before publishing.
- Publishing instructions and observed external states belong in docs/RELEASING.md
  and verification/publication.json; never fabricate a DOI/index release.
- Do not rewrite the originating host repository or copy its history here.
