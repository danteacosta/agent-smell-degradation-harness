# Acceptance-criteria pilot: offline preparation

Historical preparation record. The separately authorized successor is documented
in [the criteria consensus results](criteria-consensus-results-20260921.md).
The original packet and its zero-call preparation status remain unchanged.

This draft prepares the next source-to-acceptance-criteria experiment without
collecting model responses or resolving human review. It follows the
[SRS-163 screening](2026-09-21-strictdoc-exposure-and-case-preparation.md).
The user authorized advancing all work that does not require human judgment.
That permits this preparation; it does not supply independent labels.

## Contract and scope

The preparation succeeds when the original source packet remains unchanged,
each request contains exactly one supplied variant and the same instructions,
all planned positions have an explicit not-attempted record, and synthetic
format checks remain separate from scientific outcomes. An existing output
directory, changed source receipt, extra source file or symlink must stop the
preparation. No provider, credential, network call or executable generated code
is needed. Private source text stays outside Git.

Three options were considered: restart the stopped source-based collector,
implement a new live collector now, or prepare an isolated offline packet.
The first would violate the failed diagnostic gate and the second would
prematurely fix unreviewed design choices. The third is the current scope.
The existing 24-intent preparer and binary/confirmatory analysis contracts are
unchanged. A small retained standard-library preparation script is sufficient;
no new production adapter or design pattern is needed.

## Draft generation contract

Use the complete requirement, proposed equivalent rewrite and omitted-links
variant exactly as retained in the private predecessor. Normalize neither
wording nor whitespace. The common instruction asks for assessable acceptance
criteria grounded only in the supplied requirement, with unresolved ambiguities
reported separately. Output is one JSON object containing `criteria` (a nonempty
list of nonempty strings) and `uncertainties` (a list of nonempty strings, possibly
empty). Do not request a fixed number of criteria or a word limit that would
force loss of source obligations. Maximum retained response size in the offline
format rehearsal is 32 KiB; this is not a provider token-limit decision.

Requests contain no variant name, paired input, complete-source reference,
category inventory, rubric, target omission, expected answer or past result.
The project name is retained because it is part of the source. The instruction
to report uncertainty is an elicitation choice, not neutral measurement; it must
remain identical across arms and be reviewed before collection. Shape checking
does not establish entailment, testability or correctness.

For pipeline rehearsal only, use three repetitions per variant, nine positions,
shuffled once with seed 20260921. These are proposed positions, not an approved
sample size, collected artifacts or nine independent requirements. Store the
arm/repetition key outside request payloads. No temporal common-random-number
pairing or matched stochastic draws is implied by equal repetition indices.
The live protocol must explicitly freeze sample, requested model, reasoning,
runtime version, token/time limits and stop policy after reviews. ChatGPT-backed
Codex with no API-key fallback remains the intended route; no adapter is invoked
here and subscription cost is not asserted to be zero.

## Outcomes and analysis tables prepared before generation

Maintain one row for every scheduled position, including not attempted,
provider error, missing output and invalid output. Preserve raw responses and
usage separately; never repair malformed JSON, regenerate a favorable response,
replace failed slots or count an error as a semantic omission. Missing usage
and unreported monetary cost remain null. Operational format status is distinct
from all scientific labels.

For each schema-valid artifact, independent outcome review records evidence
spans and supported/absent/unclear for two command categories and four information
categories. All 54 category rows in the nine-position draft stay null until
review. Scope, unsupported additions, reviewer identity and rationale also stay
null. Six categories are not six independent requirements. Do not map these
draft labels into the adjudicated `covered/omitted/uncertain` analysis API.

The primary descriptive contrast is links-category preservation in omitted
versus complete input. Rewrite versus complete describes wording sensitivity;
omitted versus rewrite is supplementary. Report every category and every arm,
not only favorable differences. After labels exist, report category counts with
explicit denominators for planned, attempted, schema-valid, labeled, unclear
and missing positions. Include lower/upper descriptive bounds treating unresolved
positions as not supported/all supported, respectively; these are missingness
bounds, not confidence intervals. A point rate among labeled artifacts alone
must not hide operational failures. No hypothesis test, pooled smell effect,
power claim or population interval is justified by one purposively selected
source intent.

The source does not resolve whether all four information categories apply to
each command or collectively. Preserve this uncertainty; do not create eight
command-by-field obligations. Coverage loss relative to the full source is
neither necessarily disobedience to the shortened prompt nor a runtime defect.

## Offline verification and launch boundary

Synthetic responses exercise valid JSON, empty uncertainty, absent output,
malformed JSON, wrong fields/types, empty criteria, duplicate keys, nonstandard
numeric constants, fences and oversized output. They test format handling only.
Even a generic criterion may pass the shape contract without covering any
source category. Synthetic examples carry no human labels and never enter the
empty outcome table.

Verify exact predecessor receipt and inventory, deterministic request order,
byte-preserved variants, payload isolation, unchanged source files, private
permissions, output hashes and refusal to overwrite. Receipt hashes establish
custody, not scientific validity or immunity from complete bundle rewriting.

Mapping, rewrite/manipulation, scope/rubric and rights reviews remain pending.
The packet is not distributed and has no dispatch command. After review, revise
as required into a new version and freeze a separate live protocol. Do not unlock
the old failed source-based study or relabel preparation as preregistration.

## Work still requiring people

Human work is now a set of decisions rather than an unprepared implementation:
source-to-task mapping; rewrite equivalence and intervention scope; command/field
scope and outcome rubric; rights disposition; reviewer assignment and independent
responses. Confirmatory work additionally requires its study charter, governance,
sampling and adjudication. No software test substitutes for these decisions.

## Retained preparation evidence

Private packet: `criteria-offline-preparation-20260921-v1`, 30 files plus its
receipt. Receipt SHA-256:
`62c95f8c4ff605b143b1af9d78c900b0182503321e2103cf7d2b86e2f290cb08`.
The core generated files reproduced byte for byte. Four format-test methods
passed, including twelve invalid-output subcases and an isolated-surrogate
regression. Custody checks rejected overwrite, extra files, symlinks, modified
variant bytes and a modified predecessor receipt. All directories are 0700 and
files 0600. The independent technical review found and prompted correction of
invalid-Unicode handling and inherited directory permissions before freezing.
This is review by another assistant, not independent human validation.
