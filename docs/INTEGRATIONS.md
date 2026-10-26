# Integration ownership

## PHA / FTA / LOPA / SIL

`ccps_consequence.pha_adapter.frequency_from_study` and
`run_consequence_workflow` are optional, lazily importing a separately
installed compatible PHA host. The host must expose `StudySnapshot`,
`application.analyze` and its code-digest functions. No PHA distribution,
database/UI or PRISM patch is included or automatically installed.
The adapter recomputes FTA/LOPA/SIL, checks stale/tampered analysis and accepts
only LOC frequency before ignition/occupancy. Source context/evidence must
match. Risk factors already applied upstream cannot be applied again.
Historical host-specific tests remain in the originating private/local host;
their results are not counted as standalone release tests.

## API-581

`integrations.api581_release_source` maps a trusted, pinned release/gas or
release/liquid Python receipt. Duration and evidence are explicit. COF areas
or failure probabilities are not interpreted as rates. Wire hashes cannot
authenticate an untrusted producer and do not recompute the API-581 engine.
No API standard, table, API-581 engine or chemical database is shipped.

## PRISM histories

`release_history.history_from_prism_rows` requires the original row digest,
provider code digest, context IDs, evidence, source area/temperature and
qualification. It preserves left-held rates and excludes a terminal endpoint
from further integration. Gas-only partition and mass residuals are checked.
Jet momentum, liquid/ground partitions and thermodynamic conversions require
their own qualified physical boundary; they are not inferred automatically.
Use `ReleaseHistory` as input to the SLABx constant-segment or authored coupled
route. Synthetic PRISM-shaped rows are not a new actual PRISM source run.

## Generic providers

`ExternalSource`, `ProviderRequest`, `ProviderResult`, `Provider` Protocol and
`evaluate_provider` retain explicit model/engine/receptor/quantity/hash binding.
Missing providers fail, no fallback. Status remains provider-reported/unverified.
Scalar provider results are distinct from dense typed history results; do not
pack a time-dependent field into an unqualified scalar.

## Native versus authored solver

SLABx runs in a new isolated interpreter, checks1.0.8 and a pinned Python-source
fingerprint, and records dependency versions. Its external source/provenance
remains separate. Authored coupled1D uses optional NumPy in the calling process,
declares its own model status/equations, and is not silently substituted for
SLABx. Both routes preserve histories usable by the sampled-dose calculation.
