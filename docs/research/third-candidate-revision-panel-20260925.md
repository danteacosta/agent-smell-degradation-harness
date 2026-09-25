# Third prospective E2E candidate revision panel

Status: **replacement screening completed before oracle construction and generation**. This panel evaluates instrument eligibility only. It contains no implementation outcome and does not confirm H1 or H2.

## Method

Seven candidates that remained deferred after the second panel were either narrowed or replaced with source-supported browser obligations. The retained artifacts and commit order record this as occurring before oracle construction, A/B/C prompts and generated implementations for these cases; the checked-in stage labels do not independently prove that chronology. Each replacement records the deferred candidate it supersedes.

Three isolated Codex sessions reviewed the same hash-bound packet at high reasoning effort. The gate remained unanimous: `gpt-6-astra`, `gpt-6-sol`, and `gpt-6-luna` all had to return `ACCEPT`.

- Revision packet SHA-256: `ff433c6b0bbed8767fdecc77ef3cbcfd41d2d586927a91ebd72a4a169fbb1ba2`
- Prompt SHA-256: `42fb30f7b16cfc4fa8db50917992949d5f4d7c4d1c2eabfff832ac8ad1d4b1ee`
- Astra response SHA-256: `4f3aaf067f9e26d406d3835402c793a6dd018297611f5b9ddfe81bba3ec43e5a`
- Sol response SHA-256: `5d1b3367579e708a74317016724d66496d6a167cc517c4e4f043589a1a70a54b`
- Luna response SHA-256: `0b10de2e90462cb92e9ada24f9d3f2c0e27c3c797edb66063f016587b85dde31`

Raw inputs and outputs remain outside Git under `.private-research-evidence/third-candidate-revision-panel-20260925/`. The public source locators, replacement mappings, decisions, reasons, and hashes are in `data/e2e-multi-obligation/third-candidate-revision-panel-20260925.json`.

## Result

Six of seven candidates passed unanimously:

| Candidate | Project | Single scored obligation |
| --- | --- | --- |
| `todo-clear-button-hidden` | TodoMVC | Hide Clear completed after the last completed item is removed. |
| `todo-edit-state-not-persisted` | TodoMVC | Do not restore active editing mode in a fresh page. |
| `realworld-favorites-route-populated` | RealWorld | Populate the favorites profile route from favorited articles. |
| `realworld-comment-delete-author-only` | RealWorld | Show a comment's delete action only to its author. |
| `kanboard-duplicate-preserves-title` | Kanboard | Preserve the visible title when duplicating a task. |
| `openproject-derive-remaining-hours` | OpenProject | Derive 6h Remaining work from Work=10h and 40% Complete. |

`paperless-accept-suggestion` remains deferred. Two reviewers found that the source permits acceptance but does not explicitly define the visible post-acceptance state. Treating “accepted” as “tag applied” would therefore add an inferred endpoint.

## Updated prospective pool

Combining all three panels yields **11 eligible obligations across all six projects**, or at most **198 planned positions** under the frozen design: `11 obligations × 3 arms × 2 model configurations × 3 repetitions`.

| Project | Eligible obligations |
| --- | ---: |
| TodoMVC | 2 |
| RealWorld | 2 |
| Kanboard | 2 |
| Paperless-ngx | 1 |
| Nextcloud | 2 |
| OpenProject | 2 |

This count is a candidate ceiling. It does not mean that 11 E2E experiments are ready or that 198 generations are authorized. Each obligation still needs a qualified browser oracle, target and non-target mutants, frozen A/B/C texts, browser/runtime lock, randomized schedule, and custody bundle. The next instrument work should prioritize the four newly represented TodoMVC and RealWorld obligations, because they close the project-coverage gap.
