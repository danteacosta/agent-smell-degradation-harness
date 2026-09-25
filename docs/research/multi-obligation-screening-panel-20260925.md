# Multi-obligation E2E candidate screening panel

Status: **pre-oracle, pre-generation screening completed**. The panel changes
candidate priority only. It contains no generated implementation, browser
outcome, or evidence for H1/H2.

## Method

The hash-bound 12-candidate register was sent unchanged to isolated read-only
Codex sessions requesting `gpt-6-astra`, `gpt-6-sol`, and `gpt-6-luna` at high
reasoning effort. Each reviewer assessed whether the supplied excerpt supports
the proposed target, whether a bounded browser journey can observe it, whether
one obligation can be removed cleanly, and whether the endpoint avoids
inventing unspecified presentation or implementation details.

The gate was unanimous: a candidate advances to oracle construction only if all
three configurations return `ACCEPT`.

- Prompt SHA-256: `002aa90e62f6f04067cf27e60ac2d102b1c29554608f3c6460587b0246e6f27b`
- Astra response SHA-256: `14ce363ffe594d42ab7aae6addbc4ac901f16202e59d63b8995af9aa852ebf5e`
- Sol response SHA-256: `326b5d7d0d5a35626f47b3bac57b0aa80e1218fa8f538400c796548e21166881`
- Luna response SHA-256: `2e400614cfe079e2470262c805d22d7eeabd14bc52cbcc005c02797a001053ed`

Raw prompts and responses remain outside Git under
`.private-research-evidence/multi-obligation-screening-panel-20260925/`. The
public structured decisions and hashes are in
`data/e2e-multi-obligation/screening-panel-20260925.json`.

## Result

Only three candidates passed unanimously:

| Candidate | Project | Bounded target |
| --- | --- | --- |
| `kanboard-close-hides-task` | Kanboard | Closing removes the task from the board while the closed-task filter can retrieve it. |
| `nextcloud-restore-name-conflict` | Nextcloud | Restoring into a name collision preserves both files under distinct visible names. |
| `openproject-reject-remaining-over-work` | OpenProject | Remaining work greater than Work is rejected and does not replace stored values. |

The reviewers individually accepted 4, 7, and 6 candidates, but disagreement
defers a case. Nine candidates therefore remain outside oracle construction.
Recurring reasons were that the target added a prerequisite absent from its
excerpt, converted an API or log property into an unsupported visible outcome,
left a copied-property set undefined, or depended on configuration that the
candidate had not frozen.

The unanimously eligible block contains 54 possible positions:

`3 obligations × 3 arms × 2 model configurations × 3 repetitions`.

This is an upper bound before oracle qualification. No generation should begin
until all three common interfaces, A/B/C variants, target and non-target
mutants, browser runtime, schedule, and custody rules are frozen together.

## Consequence

Oracle work should start with these three candidates. The other nine should be
narrowed using fuller source excerpts or replaced with obligations whose UI
preconditions and visible consequences are explicit. Dispatching the original
216-position block would spend calls on cases that failed the prospective
instrument gate; reducing it now protects the causal interpretation rather
than selecting cases after outcomes are known.
