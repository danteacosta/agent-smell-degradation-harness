# Pending human decisions register (2026-11-07)

Status: non-confirmatory working document. It consolidates decisions that the dated entries of
`docs/research/literature-matrix.md` flagged as "human decision" so that they can be settled in one meeting
instead of being rediscovered one pull request at a time. **Nothing below is adopted.** No hypothesis, estimand,
B0/B3 definition, split, metric or frozen material changes by merging this file. Sources are public literature
only; no private Drive content is included.

Origin: the open stack of draft pull requests #235-#242 (literature-only), plus the 2026-10-28 section 13 decisions.
Recommendations are the maintainer-assistant's reading, not decisions.

| # | Decision | Raised by (matrix entry) | Option A | Option B | Recommendation | Cost if undecided | Decider |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | State that trajectory length / event count stays in B0 and that the B3 gain is reported conditional on it | 2026-10-31 (Majgaonkar, TrajMark) | Add one sentence to the pre-registration | Leave implicit | A: consistent with B3 = B0 + provenance already | Reviewer can claim B3 gain is a length proxy | Dante + advisor |
| 2 | Provider-stratified or leave-one-provider-out reporting of the B3 gain; adopt a gap threshold | 2026-11-04 (ProcGrep), 2026-11-05 | Require both reporting and a threshold (0.20 is only a repository default, not published) | Report descriptively with `eval/provider_balance.py`, no threshold | B for now; threshold needs pilot data | Pooled contrast may encode provider identity | Dante + advisor |
| 3 | Record confirmatory T1-T4 episodes with no online intervention or rollback | 2026-11-03 (Graphectory, ContrAgent) | Protocol rule | Allow monitored-intervention arm later as a separate study | A for the confirmatory run | An intervening monitor changes the trajectory it measures | Dante |
| 4 | Whether graph/process metrics belong in B0 | 2026-11-03 | Include (stronger B0, harder H2) | Exclude, register as exploratory B0+ | B: keep H2 contrast simple; B0+ as sensitivity | Moving B0 after seeing data invalidates the contrast | Dante + advisor |
| 5 | Tester prompts must not contain generated code | 2026-10-29 (Konstantinou) | Protocol rule | Leave as is | A, checkable by a prompt-content lint | Coupling confound in QP4 | Dante |
| 6 | May QP4 related work cite 2607.05139, 2610.36584, 2610.28679 as context | 2026-10-29, 2026-10-30 | Context only, never for section-13 numbers | Do not cite | A | None | Dante |
| 7 | Add a specificity check on valid variants of the target condition to oracle qualification | 2026-10-30 | Design change | Not adopted | Decide after corpus freeze | Oracle may reject valid implementations | Dante |
| 8 | LLM smell suggestions are not shown to blind annotators | 2026-11-01 (Broccia) | Protocol rule | Allow, report as assisted | A | Contaminates blind adjudication | Dante |
| 9 | Report omission-type and over-specification-type tester failures separately | 2026-11-07 (Chen et al.) | Add to analysis plan | Pool | A; already implied by per-constraint_id reporting | Pooled error rate hides the mechanism | Dante |
| 10 | Second human coder for audit #185; reviewers for the 20% panel audit | Proposal section 13 and section 9 | Name persons and dates | Keep conditional claims | Blocking for any QP4 mechanism claim | QP4 mechanism claims stay conditional | Dante + advisor |
| 11 | Freeze candidate corpus, bind content and provenance hashes, obtain independent blinded reviews | Proposal section 12 | Start now | Wait for ISSTA 2027 timeline check (abstract 2027-01-08) | Start now: this is the critical path | Confirmatory collection cannot start | Dante |

## Dependency order

Decisions 1-5, 8 and 9 are single-sentence protocol rules and can be settled together before the corpus freeze.
Decisions 10-11 are the real critical path to the ISSTA 2027 target and require people, not code.
Decisions 4 and 7 should wait for the frozen corpus so they are not tuned on outcomes.

## Verification

`tests/test_decision_register.py` checks that every row has a decider and a recommendation and that the file states
that nothing is adopted. It does not check the scientific content.
