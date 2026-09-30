# Cross-case read of the new E2E obligation block

Eight new obligations from the planned block have now been executed in
prospective A/B/C browser pilots. They add requirement diversity inside the
same six represented projects; they do not add a seventh project. The
[evidence matrix](../thesis/e2e-evidence-matrix-20260925.md) and linked
per-case reports carry the outcome details and preserved instrument failures.

| Project and obligation | Qualified C outcome | A/B qualification caveat |
| --- | --- | --- |
| OpenProject Remaining derivation | 6/6 target failures | A/B passed |
| Kanboard copied title | 2/6 target failures in clean replication | A/B passed; initial run had unknowns |
| Paperless duplicate consumption | 4/6 target failures | A/B passed; first lot instrument failure |
| RealWorld favorites route | 0/6 target failures | A/B/C passed; first lot instrument failure |
| OpenProject invalid Remaining work | 6/6 target failures | A/B passed |
| Paperless nested tags | 6/6 target failures | B passed; A had one target failure and one browser error |
| Kanboard Closed tasks filter | 0/6 target failures | A/B/C passed; first lot instrument failure |
| Nextcloud restore-name conflict | 6/6 target failures | A/B passed; first lot collector failure |

In this selected block, six of eight obligations had at least one
target-only C failure; two showed recovery. This is a **description of the
chosen cases**, not an estimate that 75% of requirement omissions produce
defects. Repetitions share prompts, scaffold and requirement; treating 48 C
generations as independent requirements would exaggerate precision. A/B/C
contrast strength also varies: Paperless nested tags cannot support the same
clean A/B baseline claim as OpenProject invalid Remaining work or Nextcloud
restore-name conflict.

The useful scientific conclusion is narrower: omission of a source-grounded
clause can produce a browser-observable defect in multiple projects, while
context can also let a model reconstruct an omitted clause. The observed
mechanism depends on the requirement, model and surrounding interface data.
Natural-smell frequency, independent ordinal severity H1, and early-warning
performance H2 remain unanswered. The next decisive collection should use a
frozen case-selection rule and independent labels, including null cases,
rather than selecting only obligations expected to fail.
This endpoint distinction is also consistent with the
[primary-study review](2026-09-27-frattini-pr-review.md), which concerns a
different downstream activity and supplies no transferable agent effect size.
