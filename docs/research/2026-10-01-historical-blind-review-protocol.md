# Blind review of the ten historical requirement changes

This is an exploratory source review, not a new E2E run or an H1/H2 result.
The ten cases were fixed by the [historical closure](2026-09-30-natural-e2e-closure.md)
before this review. Their known browser outcomes must not determine admission or
the smell category. The primary unit is the requirement change, not one of its
six model/repetition pairs.
Published category definitions and their scope limits are cataloged in the
[literature-mapping audit](2026-09-30-literature-validated-smell-audit.md).

## Acceptance contract

For each of the ten changes, a reviewer first receives only the old source
excerpt and states the behavior it requires, plausible alternative readings,
and missing information. That answer is sealed before the reviewer receives
the old/new comparison. The second reading records every changed information
channel, a literature-defined smell or `none/uncertain`, a specific evidence
span, a contemporary behavioral reference, whether the browser oracle tests
the changed obligation, and whether the old model input exposed the answer
elsewhere. Missing references and disputed mappings remain unresolved. No
reviewer receives model outputs, E2E categories, or the historical scorecard.

Two independent source reviews are preferred. A model-only consensus may be
reported as an exploratory triage, never as independent human adjudication.
Prior exposure to the historical results must be recorded. A reviewer who has
read the outcome-bearing audit cannot be called outcome-blind. The custodian
keeps source identities, forms, responses and the stage-release record outside
the public repository. Never distribute the whole bundle to a reviewer.

The existing `repository-review-source/v1` contract requires a canonical,
rewrite and smelly A/B/C triplet. These historical old/new pairs do not have
that structure. The existing `natural-rubric-v1` does not cover all the proposed
incompleteness categories. Neither contract is repurposed for this review.

## What is decided after review

1. Report how many of the ten changes are supported, rejected or unresolved as
   literature-mapped smells. Keep factual corrections and scope edits visible.
2. Reveal E2E outcomes only after source judgments are sealed. Cross-tabulate
   by **requirement**, and show the six nested pairs beneath each requirement.
   Do not estimate a population-wide effect from these selected cases.
3. Qualify a prospective A/B/C case only if the reference, changed obligation,
   allowed context and independent browser oracle are fixed before generation.
   Include null cases under a predeclared selection rule. A case with a leaked
   answer needs a separately frozen cue-ablation arm, not a retrospective relabel.

The [recoverability audit](2026-10-01-e2e-recoverability-audit.md) names two
calibration questions: whether Kanboard's “three statuses” genuinely permits
simultaneous states, and whether the Paperless Rotate wording specifies the
tested action. Nextcloud retention changes a sentence and linked guidance
together. These uncertainties must be resolved before interpreting those
contrasts as isolated smell effects.

## Exploratory two-model source triage, 1 October

An offline packet held ten old excerpts. `gpt-5.6-luna` and `gpt-5.6-sol`
each interpreted the old text before either saw a paired revision. Both first
readings were hashed and sealed before the comparative prompts were sent.
The comparative responses were sealed before the outcome table below was
reopened. The models were told not to access tools, source files, later
commits or results. Their exact prompts, responses, source identities and
SHA-256 seals are in a private local bundle. The first-reading seal hashes to
`a69bbdafd28be4baeba398e23ba37c2a6f7f1b30afb5560dc341a1f36484f3aa`;
the comparative seal hashes to
`07f962ad975acf43a17ba47fad1fe0aa03fb3daa228d75070b6a4a4800b5e6b1`.
No model label is a human label.
The operator had prior access to the historical outcomes. Only the model
prompts hid those outcomes; this is not researcher blinding, and both models
belong to the same provider family.

Eight pairs draw from frozen historical source excerpts. OpenProject uses exact
commit-patch lines plus an unchanged formula from a local source snapshot;
Paperless new-user uses exact commit-patch lines and adjacent context. The
complete historical pages for those two still need restoration. Excerpts do
not establish what other guidance was in the model's full input.

I/T/U below are previously recorded improved/tied/unknown **old/new E2E
pairs**, revealed only after these judgments were sealed. The two readers
often agreed that a condition was added without agreeing that the old text
was a smell. Their categories therefore remain provisional.

| Historical requirement | Source-only model judgments | Prior E2E I/T/U | Decision for next collection |
| --- | --- | ---: | --- |
| Nextcloud restore collision | Both: candidate `Incomplete System Behavior`; old-only first reading found no issue | 2/4/0 | Review the natural mapping independently; a separate qualified A/B/C omission pilot already exists. |
| Paperless barcode retain | Both: candidate `Incomplete System Behavior`; only one old-only reader flagged missing behavior | 0/6/0 | Verify the retain option existed at the old revision; retain as a null candidate if qualified. |
| Paperless new-user defaults | Both: candidate `Incomplete System Behavior`, but one rated literature fit weak | 0/6/0 | Restore full source, verify historical default and isolate the concurrent UISettings edit. |
| Kanboard subtask cardinality | One old-only reader saw ambiguity; the other read one-of-three. Comparative categories differed | 1/5/0 | Adjudicate cardinality before calling this `Omitted Word`. |
| Nextcloud trash retention | One called missing behavior; the other called a scope clarification | 3/1/2 | Decide whether the treatment includes linked admin guidance; do not attribute to one sentence. |
| Paperless original PDF / Rotate | Both called the change a factual exception; they disagreed on fit to `Negative Statements` | 0/6/0 | Check whether the old revision already had the exception and whether the oracle tests the named action. |
| OpenProject progress | Both: factual correction, not a supported smell category | 5/0/1 | Keep as a non-smell comparator; restore the full old page. |
| Kanboard search | Both: typo in executable example, not a supported smell category | 0/4/2 | Keep outside the smell subset. |
| Paperless profile | Both: scope/wording clarification; literature fit weak or unsupported | 0/6/0 | Keep unresolved until own-profile authority is independently checked. |
| Nextcloud transfer | One called a factual correction, the other a wording clarification | 0/6/0 | Keep unresolved; the old text may already specify transfer of shares. |

The ten rows still total **11/44/5**, but those are nested repetitions. The
two cases with matching, positive literature-fit model judgments contain
**2 improvements and 10 ties in 12 pairs**; this is an outcome description of
two selected requirements, not a smell effect estimate. The new-user case has
agreement on category but weak fit from one reader and six ties. No historical
smell is independently confirmed; source/oracle/context review remains open.
In particular, the first reading of Nextcloud restore did not identify the
missing collision rule from the old excerpt alone. A new sentence can make a
gap obvious retrospectively without proving that a T0-only detector could
have found it.

The two matching-category cases, restore and barcode, were selected for
follow-up after the historical outcomes were reopened. Choosing them as a
positive/null contrast is
**outcome-informed exploratory selection**, even though neither is discarded.
Nextcloud restore already has a separate, qualified
[18-generation A/B/C omission pilot](nextcloud-restore-conflict-20260927.md):
A/B passed and C failed 6/6. That pilot establishes a controlled local
omission effect, not that its natural historical change was a confirmed smell.
The Paperless barcode
[excerpt successor](2026-09-29-natural-e2e-contamination-followup.md)
left four of six pairs unknown, including browser errors and mixed failures.
A new barcode A/B/C run therefore needs fresh source and oracle qualification
before generation. Neither case adds an independent project or permits a
population inference. A confirmatory set must use a selection rule frozen
without inspecting its outcomes.

The frozen parent-version `Trashbin.php` for Nextcloud restore calls
`getUniqueFilename` when an item with the same name exists and falls back to
the root when the old destination is unavailable. That is a contemporary
behavioral reference for the proposed collision and missing-destination
obligations, although an independent reader still needs to approve the
requirement-to-oracle mapping. For Paperless, the frozen old full page says an
ASN barcode can retain its page while the old *Document Splitting* paragraph
says its separator is discarded. This is a real contextual cue, but it does
not state that the separator's `retain` setting places the page at the start
of the next document. The source and assembled input therefore need separate
reviews before an ablation or fresh generation.
