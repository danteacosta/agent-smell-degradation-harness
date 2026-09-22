# StrictDoc: prior exposure, historical export and next-case preparation

Historical preparation record. The separately authorized successor is documented
in [the criteria consensus results](criteria-consensus-results-20260921.md).
The original packet and its zero-call preparation status remain unchanged.

## Research question and disposition

Can the next StrictDoc case supply a new, source-grounded test of obligation
preservation after the TodoMVC null result? This follow-up found two reasons not
to launch the previously proposed metadata case: its source requirement was
already selected in earlier studies, and its historical feature commit fails
the proposed classification-only export observation. Neither finding is a new
LLM outcome. No generation calls were made.

This corrects the next-case recommendation in the
[earlier screening](post-todomvc-next-case-20260921.md). Preserve that record and
its private packet; do not treat the correction as retroactive preregistration.
Acceptance-criteria generation remains primary. Repository-level generation is
secondary, and independent human reviews remain pending.

## Exposure audit: SRS-110 is development material

The retained `pilot-curation-inputs-20260906-v2/candidates.json` already contains
`STRICTDOC-SRS-110`, with history explicitly stating that it is previously
selected exploratory material, not fresh test data. Its intervention deletes
Document authors. `pilot-source-faithful-20260906/admission.json` also retains its
operator admission and prior screening references; those are not human labels.

The old and newly extracted complete requirement have identical SHA-256:
`918e6acf95012c4cf0d7238871dd5675368c64749ee60946ef82e3b7620b9824`.
Updating the source revision does not create a new intent or erase exposure.
Deleting classification instead of authors would be a related intervention on
the same source intent, not an independent source sample.

The earlier `strictdoc-metadata-screening-20260921-v1` remains immutable. Its
successor records this exclusion from fresh evaluation. Reuse is possible only
as explicitly exposed development/replication material, retaining project and
source-family clustering.

## Historical export observation

Source: StrictDoc contributors' classification feature commit
`67355ee3b80707639288a83d13f5d7bc5845319d`. We built it from the GitHub source
archive in Python 3.10, retained resolved dependencies and the build log, and ran
its public `strictdoc export` CLI with a read-only root and input, non-root user,
no network, no credentials, bounded resources and a separate writable output.
Dependencies were resolved now: this is not an exact historical environment
reconstruction. The runtime image was addressed by immutable local ID:
`sha256:72b19093e2c9cdbc97f7813c272da9b7f3e9859c3513e540243e58f76e4ab764`.

| Synthetic input | CLI exit | Generated document page | Disposition |
| --- | --- | --- | --- |
| CLASSIFICATION: Restricted, without UID/version | 0 | Restricted absent | Fails proposed visibility contract |
| UID: DOC-1 plus CLASSIFICATION: Restricted | 0 | Restricted visible | Positive transport/render control |
| UID: DOC-1 without classification | 0 | Restricted absent | Negative control |

Native browser inspection confirmed the first two pages; both screenshots are
preserved. The original HTMLs and input bytes are retained. Source inspection
explains the difference: `has_meta()` checks UID/version only; the template's
entire metadata table is inside that guard, including the new classification
row. No upstream source was modified and no patch was submitted upstream.

Consequently this feature commit is rejected as a qualified reference for the
proposed classification-only export contract. This is an observed historical
rendering omission, not a generated-code treatment effect, not a current-version
bug claim, and not evidence for H1/H2. It also does not by itself resolve whether
the proposed UI/export contract is entailed by the metadata-model SRS.

## Provisional next candidate: SRS-163

Pinned revision: `abf7be7daa2a25721a56980b5be15845336ea0b8`; locator
`SDOC-SRS-163`, StrictDoc identification. The source requires about and version
commands displaying the project's title, current version, license and links to
its web pages. The task is to derive acceptance criteria, not implement those
commands or evaluate the current StrictDoc CLI.

Selection was purposive, before generation, for an explicit bounded enumeration
and an auditable omission. It is not a representative or randomized sample.
An independent agent compared three source candidates:

- SRS-2: deleting the definition leaves the meaningful term “incremental”, so
  retained language may reconstruct the target condition.
- SRS-4: deleting “only” changes exclusivity; on-demand context may reconstruct
  it, and scope needs careful interpretation.
- SRS-163: deleting the links category retains two commands and the other three
  information categories. A proposed rewrite supplies a wording control.

A bounded review of 749 retained JSON/JSONL files found no selected exposure of
2/4/163 in the searched IDs and statement prefixes, excluding the full-source
custody file and strings of at least 12,000 characters. This negative search is
limited: archives, long embedded prompts, other storage and model pretraining
are not certified unexposed. It cannot grant held-out or independence status.
The full SRS has been retained in source custody, which is itself disclosed.

The private draft packet has three variants, source/license/NOTICE, a proposed
coverage rubric, constructed rubric exercises and blank review forms. The
complete, rewrite and omitted-link variants have not been sent for generation.
The rewrite is not yet certified equivalent. Removing the links clause does not
prohibit the generator from including links anyway.

## Rubric boundaries and review decisions still needed

Record two command categories and four information categories separately, with
artifact evidence and supported/absent/unclear outcomes. Keep malformed or
missing outputs separate. Lexical matches do not establish assessable criteria.
A loss relative to the complete source is not necessarily disobedience to the
shortened prompt and is not a runtime defect.

The source is ambiguous about whether every information category must be shown
by each command or collectively across them. Keep that scope dimension unclear
until independent adjudication; do not silently create eight command-by-field
obligations. Do not add exact URLs, output formatting, network access, exit
codes, link clickability or exact link counts. Constructed rubric examples are
assistant-authored calibration drafts, never LLM results or human ground truth.

Mapping, manipulation/rewrite equivalence, rubric/scope and rights reviews remain
pending. No forms were filled as if a human had reviewed them; no packet was
distributed. No final sample size, budget, generation prompts or dispatch plan
was approved by this preparation. The next admissible action is completing those
reviews and freezing a separate exploratory protocol, not invoking the old
failed prospective collection or reusing its spending authorization.

## Sources and retained evidence

- StrictDoc contributors, [pinned SRS](https://github.com/strictdoc-project/strictdoc/blob/abf7be7daa2a25721a56980b5be15845336ea0b8/docs/strictdoc_21_l2_high_level_requirements.sdoc): natural statements and candidate comparison.
- StrictDoc contributors, [classification feature diff](https://github.com/strictdoc-project/strictdoc/commit/67355ee3b80707639288a83d13f5d7bc5845319d): historical behavior and implementation boundary.
- [Historical metadata model](https://github.com/strictdoc-project/strictdoc/blob/67355ee3b80707639288a83d13f5d7bc5845319d/strictdoc/backend/sdoc/models/document_config.py) and [HTML template](https://github.com/strictdoc-project/strictdoc/blob/67355ee3b80707639288a83d13f5d7bc5845319d/strictdoc/export/html/templates/single_document/document.jinja.html): guarded rendering mechanism.
- [Source-based pilot protocol](source-based-pilot-protocol.md): prior corpus and failed collection gate, preserved rather than reset.
- Private successor: `strictdoc-followup-preparation-20260921-v1`, 93 recorded files, zero provider calls, zero human approvals; receipt SHA-256 `379a9d1c723dbb60fabb3b4071e4d4554090b44c699c4c0088e0342720c11401`.

The source evidence supports screening decisions, not general performance claims.
The follow-up changes case selection and prevents an invalid reference from
entering the repository experiment; it does not convert the TodoMVC null result
into a positive result.
