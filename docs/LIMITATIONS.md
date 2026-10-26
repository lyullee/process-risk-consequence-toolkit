# Engineering and numerical limits

- Screening code and synthetic software verification do not establish field
  validity, standard conformity, approval to operate or complete facility QRA.
- No chemical property, toxicity, probit, ignition or proprietary coefficient
  database. Caller supplies and qualifies inputs/coefficients and evidence.
- Ideal-gas/nonflashing source assumptions are not a real-fluid/2phase tank model.
- Passive Gaussian sigmas are supplied; no dense-gas physics is inferred.
- Richardson is diagnostic only, not an automatic concentration-model switch.
- Fire geometry and fixed EPA1psi scope are explicit; no arbitrary blast curve,
  complete jet model, evacuation, confined explosion or full BLEVE rupture model.
- Optional SLABx is separately installed and pinned. Native execution is not a
  certification, and its provenance/known limitations remain external.
- Finite/variable native source bridge uses declared pretransition/independent
  segment approximations. Strong cloud interaction is not resolved in that route.
- Coupled1D resolves shared nonlinear fields but remains isothermal, fixed width,
  flat ground, vertically uniform, with user-qualified entrainment/relaxation.
  No2D spreading, upper-air momentum dynamics, energy, phase change or obstacles.
- All histories have finite windows and sampled extrema/integrals. Tail flags,
  source-active status, numerical diffusion, domain limits and refinement matter.
- Hashes establish reproducibility, not authentication or evidentiary truth.
- Known-unit checks are not exhaustive physical/semantic validation. Different
  physical quantities may share SI dimensions.
- Conditional risk is one explicit scenario/receptor contribution. Exhaustive
  branches and independence declarations require engineering review.
- The optional local HTTP service is not a hardened multi-user deployment.
