# Copyright, provenance and naming review

Reviewed 2026-10-26 for the initial standalone 0.1.0 release. This is a
documented distribution review, not legal representation or a guarantee of
no legal dispute in any jurisdiction.

## Authority and license

The requesting author confirmed ownership/authority for the newly authored
consequence code and selected Apache-2.0. Copyright attribution: Ugwiyeon Lee.
The license covers this project's original expression, not underlying methods,
trademarks, cited books or separately installed engines. Apache-2.0's actual
patent and trademark terms remain those in LICENSE; no broad patent clearance
or permission from a publisher is inferred.

## CCPS book boundary

AIChE/CCPS, *Guidelines for Consequence Analysis of Chemical Releases* (1999),
ISBN 0-8169-0786-2, was examined locally for scope/bibliographic context.
Its copyright reservation was identified. No permission to redistribute its
text or other protected expression has been obtained or implied.

Excluded from source, source archives, wheels and hosted assets:

- The purchased/local PDF and all OCR or extracted text.
- Tables, figures, screenshots, scans, worked-example inputs/answers.
- The book's accompanying programs, databases and empirical coefficient tables.
- Private engineering documents, invention materials, local databases and logs.
- External-engine source, SLAB Fortran and experimental observation datasets.

Section identifiers and a bibliographic title identify topics only. No claim
of complete CCPS coverage or conformity is made. AIChE's permissions guidance
requires permission for use of book content:
https://ccps.aiche.org/ccps-permissions and https://www.aiche.org/permissions .
No institutional logo is used; see https://www.aiche.org/resources/forms/request-logo .

## Methods versus protected expression

The US Copyright Office distinguishes underlying ideas/methods/systems from
their protected literary/graphic expression (Circular33,
https://www.copyright.gov/circs/circ33.pdf). This distinction is a review
principle, not permission to copy book text or a blanket worldwide legal
conclusion. Publication access, citation, attribution or a formula's existence
alone is not treated as a license to reproduce surrounding expression.

Our source was newly authored around declared equations, units, contracts and
synthetic tests. No copyrighted source chapter, example suite or figure was
transcribed into the public project. The review does not prove independent
invention, confer exclusivity in known methods, or comprehensively resolve
patents, contractual use conditions, marks or every country's laws.

## Direct equation/model provenance

| Code family | Direct basis | Distribution decision |
|---|---|---|
| Orifice / inventory / basic Gaussian kernels | Independently authored public physics/conservation | Original code and synthetic analytic identities only |
| Fireball / sphere / solid-flame / Richardson | NOAA NOS OR&R43 (2013), cited sections/pages | Equations implemented independently; no document/database bundled |
| Fixed 1 psi endpoint | EPA-550-B-99-009 AppendixC.1 C-1 (1999) | Fixed scope explicit; no tables or regulatory-compliance claim |
| Dose / probit / risk | Supplied coefficients, normalized mathematics, explicit probability ownership | No chemical/probit coefficient database |
| SLABx histories | Separately installed pinned SLABx1.0.8 plus own normalized reconstruction | No external engine source; preserve its provenance caveats |
| Finite/continuous source bridge | Native constant source plus own qualified closures | Approximation labeled, no claimed full arbitrary-rate solver |
| Coupled layer | Own restricted isothermal 1D conservation equations/numerics; public model-family references | Research only; not copied/complete TWODEE, SLAB or two-layer-paper implementation |

NOAA direct source: https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf ;
catalog/rights metadata: https://repository.library.noaa.gov/view/noaa/2669 .
EPA direct source: https://www.epa.gov/sites/default/files/2017-05/documents/oca-apds.pdf .
Detailed per-calculation equation locators are in each module reference and
receipt, and the machine-readable catalog.

## Name and attribution decision

The proposed public name containing CCPS was replaced with
**Process Risk Consequence Toolkit** (`process-risk-consequence-toolkit`) to
reduce the chance of implying an official product. This is a naming-risk
reduction, not an exhaustive trademark clearance. No logo is used. Historical
`ccps_consequence`, `ccps.*` schemas and `/api/ccps/` routes remain compatibility
identifiers with an explicit non-affiliation statement. Names identify cited
methods and interoperability, not sponsorship or a trademark license.

## Extraction and audit

The standalone repository was created from an explicit allowlist of the new
consequence namespace, its authored tests and synthetic examples. No earlier
PHA repository Git history, PHA UI/database, PRISM patch or local PDF was copied.
An optional newly authored PHA adapter only imports a separately installed host.
Source comments carry SPDX Apache-2.0 identifiers and author attribution.

The release audit scans source and built archives for denied file categories,
credential-like strings and machine-specific user paths. It records file hashes
without capturing credentials. `verification/release-audit.json` is evidence of
that bounded scan, not an exhaustive semantic similarity or legal audit.
Future contributors must document any third-party expression or data and its
permission before adding it. A private GitHub repository is not used as a
workaround for an unlicensed redistribution; excluded material stays local.
