# Intermediate omission pilot: outcome-blind source review

Status: source preparation by an assistant, before generation. No human approval,
no generated outcome labels, and no claim of confirmatory admission. The corpus
contains 12 distinct intent units in four already screened projects. Intents
remain clustered by project; they are not 12 statistically independent projects.

The user authorized 12 requirements × three conditions × two generation
configurations × three repetitions = 216 generations. This source review supplies
the immutable-input candidate; the execution protocol separately determines
models, labels, missingness, collection limits and analysis.

## Sources and provenance

All source files were downloaded anonymously from public GitHub, with commit IDs
resolved before extraction. Exact source bytes, license notices, revisions and
SHA-256 hashes are retained in [the corpus](corpus.json).
A is always a literal, contiguous excerpt, never an assistant-authored substitute.
B is an explicitly authored paraphrase, not another natural source observation.
C deletes one contiguous span from A without any punctuation or whitespace repair.
Character offsets use zero-based Unicode code points with an exclusive end.

| Project | Pinned revision | Selected natural source intents | License |
| --- | --- | --- | --- |
| StrictDoc | `abf7be7daa2a25721a56980b5be15845336ea0b8` | SRS-47 test provision; SRS-97 statistics screen; SRS-157 tree map | Apache-2.0 |
| TodoMVC | `ff43b02e59dfa604386bb382034b2cd07c2bcd8a` | New todo; Mark all as complete; Persistence | MIT |
| RealWorld | `ebbcdeb8d55b42a3a613c787560498b8ef10003f` | List Articles; Follow user; Add Comments to an Article | MIT |
| CaSS | `97fc0939ca3960504ce8b2f51749881543a4038c` | IDATA-007 assertion fields; DATA-011 uniform type support; BATCH-002 batch storage | Apache-2.0 |

Primary sources: [StrictDoc SRS](https://github.com/strictdoc-project/strictdoc/blob/abf7be7daa2a25721a56980b5be15845336ea0b8/docs/strictdoc_21_l2_high_level_requirements.sdoc),
[TodoMVC specification](https://github.com/tastejs/todomvc/blob/ff43b02e59dfa604386bb382034b2cd07c2bcd8a/app-spec.md),
[RealWorld endpoints](https://github.com/realworld-apps/realworld/blob/ebbcdeb8d55b42a3a613c787560498b8ef10003f/docs/src/content/docs/specifications/backend/endpoints.md),
and [CaSS SRS](https://github.com/cassproject/CASS/blob/97fc0939ca3960504ce8b2f51749881543a4038c/REQUIREMENTS.md).
The CaSS source expressly describes code-derived requirements and an initially
auto-generated document, subsequently reviewed by its upstream architect. This
is a retrospective documentation stratum; upstream review does not constitute
human review of our transformations, rubric or study.

Licenses are retained alongside sources. StrictDoc's NOTICE is preserved, as is
the full Apache 2.0 license text. RealWorld excludes third-party framework logos
from MIT; no logos or excluded media are copied. No private Drive documents,
private research source text or credentials enter this source corpus.

## Interventions and scoring boundary

| Intent | Deleted obligation | Examples of retained obligations |
| --- | --- | --- |
| StrictDoc SRS-47 | CLI changes receive a black-box integration test | Web E2E, internal Python unit tests, generic test/merge provision |
| StrictDoc SRS-97 | Statistics screen shows generation date | Title, revision, counts and status breakdown |
| StrictDoc SRS-157 | Tree map shows test-file coverage | Document tree map and source-code coverage |
| TodoMVC New todo | Input focus on page load, preferably autofocus | Enter creation/appending, input clearing, trim/nonempty check |
| TodoMVC Mark all | Clear checkbox state after Clear completed | Bulk toggle and single-item synchronization |
| TodoMVC Persistence | Do not persist editing mode | localStorage, framework preference, conditional keys, storage name |
| RealWorld List Articles | Offset parameter with default 0 | Filters, limit 20, optional authentication, ordering |
| RealWorld Follow user | No additional parameters required | Endpoint, required authentication, Profile response |
| RealWorld Add comment | Authentication required | Endpoint, required body, created Comment response |
| CaSS IDATA-007 | Numeric confidence field | Subject, agent, competency, evidence, individual encryption |
| CaSS DATA-011 | Search applies uniformly across JSON-LD types | Acceptance, storage, indexing, KBAC, version history |
| CaSS BATCH-002 | Validate each object's KBAC permissions | Endpoint, array input and successful-storage count |

The rubric is relative to the supplied source excerpt. It does not expand linked
schemas or inspect implementations. RealWorld paraphrases retain the exact
response-format links so A and B preserve the same contextual references; no
runtime follow-up fetch is part of generation or judgment. Examples remain
examples. Conditional preferences remain conditional: TodoMVC `should`, preferred
`autofocus`, and `if possible` field keys must not become unconditional `must`.
Neutral obligation identifiers (`o01`, etc.) are bookkeeping, not target hints.
The target ID and omission offsets must remain outside generator and judge input.

There is no explicit equivalent target clause left in C. Domain associations may
still permit recovery: API authentication, conventional pagination, automatic UI
state synchronization, test-type conventions, and fields in familiar models can
all be guessed. Such recovery is an outcome to retain, not a post-hoc exclusion.
A loss against full-source coverage does not show disobedience to C or a runtime
implementation defect. Non-target coverage must also be reported.

## Screening and exclusions before any new outcome

Earlier repository screening considered these same four projects. We excluded
StrictDoc SRS-110 and SRS-163 and TodoMVC Editing/Escape because they were already
used in the earlier research sequence. We then searched retained JSON/JSONL
before freezing. Actual prior launch/candidate records additionally exposed
SRS-151, SRS-125, SRS-206 and CaSS ST-008. Each was removed before generation;
both intermediate exposure diagnostics are retained. CaSS DATA-002 was rejected
because exact deletion left an awkward two-item Oxford comma; no generated
outcome motivated that replacement. RealWorld OpenAPI was inspected as a
candidate source, but the natural endpoint prose was selected instead.

The final bounded search examined 1,006 JSON/JSONL files and 403,105 eligible
string values with zero selected-ID/exact-excerpt matches. It excludes archives,
files over 20 MB, strings over 12,000 characters, non-JSON text, other directories,
paraphrased references and model pretraining. For StrictDoc/CaSS it searched IDs;
for TodoMVC/RealWorld it searched exact A text. This asymmetry is conservative in
its claims, not proof of equivalent detection power. Full-source custody and
project exposure are already known. Do not call this corpus pristine held-out
data or claim that a negative bounded search proves independence.

All 66 pairwise A/A comparisons are retained. Maximum token-set Jaccard is 0.265
(Follow user / Add comment); maximum character SequenceMatcher similarity may
reflect shared specification boilerplate. These are descriptive near-clone
signals with no post-hoc acceptance threshold. StrictDoc statistics and tree-map
screens concern different screens and obligations but share UI vocabulary;
RealWorld endpoints share protocol conventions. Project clustering remains.

## Mechanical checks and remaining interpretation

Preparation checks confirmed 12/12 exact source excerpts, source file hashes,
source offsets, single-span deletions and target membership. Every case retains
at least two non-target obligations. Rewrites and rubric entailment still require
independent assistant review before freeze; this is not human validation. No
source review score should be mistaken for an outcome judge score.

Selection is purposive, English-only, public documentation with conveniently
separable obligations. Three intents per project cannot represent every project
or every smell. Enumerations, prose and API documentation differ in length,
modality and familiarity; report results by intent/project and model, and avoid
a pooled population effect or H1/H2 confirmation from this pilot alone.
