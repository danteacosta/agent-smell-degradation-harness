# Next step: admission of language candidates

Operational draft following the [constructed pilot](codex-language-controls-results-20260914.md).
It contains no human labels, admits no case to the corpus, and does not replace
the existing confirmatory annotation charter. No invitation has been sent.

## Reproducible form preparation and return

Create the packet under an existing private parent, outside the repository:

```bash
python -m eval.language_review --output /absolute/new/private/review-packet --seed 20260914
python -m eval.language_review --output /absolute/new/private/review-packet --verify-existing
```

The first command creates six four-item forms, one text from each cluster per
form and ten unique texts overall. The second independently verifies the file
inventory, hashes, form topology, prompt-to-custody links, and empty draft
fields. Relative paths and paths resolving inside the public repository fail
closed.

Give each reviewer only one form; never distribute the whole packet or
`custodian/`. Record the assignment and prior exposure before freezing the
individual response. Set the returned form status to `completed`, use a
pseudonymous reviewer ID, answer every field explicitly (use `none` when
applicable), and choose confidence `low`, `medium`, or `high`. Record it without
overwriting an earlier response:

```bash
python -m eval.language_review \
  --output /absolute/private/review-packet \
  --record-completed /absolute/private/returned-FORM-A.json \
  --response-output /absolute/new/private/responses/FORM-A-reviewer-01.json
```

The immutable response envelope binds the returned content to the exact source
form and export receipt. It rejects changed prompts, item identities, incomplete
answers, invalid confidence, missing exposure disclosure, and reused output
paths. It does not compute agreement, adjudicate, create a confirmatory label,
or validate the candidate.

The receipt keeps participants and human labels at zero. The 24 form positions
are neither new observations nor a sample-size recommendation. Rubric,
independence, named roles, governance, and distribution remain pending.

## What independent review must decide

1. **Coordination:** Does the unparenthesized sentence admit both groupings in
   the supplied context? Does the audience's logical-precedence convention
   eliminate the ambiguity or merely favor one reading? Justify the category
   and record whether the construction is too artificial for the intended domain.
2. **Pronoun:** Which antecedents of “it” are plausible? Can it refer to the
   pair or the link? Do not force a choice between sender-only and recipient-only:
   record additional readings and decide whether a future collection must
   broaden its alternatives.
3. **Controls:** Do both wordings preserve behavior across the declared domain?
   Is the complementary form a sufficient wording control, or is a distinct
   lexical control needed to study the literature category?
4. **Cues and fidelity:** Do argument names favor a reading? Does the
   intervention change only the declared span? Does the oracle represent the
   author's intent without inventing information absent from the observed
   requirement?

## Candidate record required before new generations

| Field | Required content |
|---|---|
| Identity | Opaque ID, constructed or natural origin, project/intent, and dependent cluster |
| Available context | Observed requirement, interface, and every attachment actually visible |
| Definition | Proposed category, primary source, exact span, and applied operation |
| Behavior | Reference intent, domain, expected decision table, and plausible alternatives |
| Decision | Accept, revise, or reject; textual rationale; preserved uncertainty |
| Provenance | Reviewer identifier, rubric version, date, packet hash, and response-envelope hash |

Reviewers must not see model results, generated code, or model preferences.
This pilot's examples and results are already public; an exposed reviewer must
not be described as blind to those items. Record prior exposure and recruit new
cases when needed. Requirement-candidate admission and artifact-outcome judging
are distinct tasks; never reuse one task's judgment as the other's outcome.

Preserve individual responses before adjudication. Resolve disagreements with
rationale and version every oracle or category change. Later review does not
retroactively change the manifest or make the pilot confirmatory. Expanding
alternatives or ablating interface cues requires a new configuration, manifest,
and separate results.

## Criterion for advancing

Only after candidate review, population and sampling-unit definition, real
participant/role registration, governance approval, and protocol freeze should
a new collection be sized. The sample must vary projects and intents; additional
replications or test inputs do not substitute for that diversity. Do not estimate
power by treating this pilot's twins as independent projects.
