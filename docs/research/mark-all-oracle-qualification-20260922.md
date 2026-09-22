# TodoMVC Mark all: browser oracle qualification

Status: **instrument qualified on authored controls; candidate not yet admitted
for model collection**. This is no new generation or omission-effect result.
The source is TodoMVC `app-spec.md` at revision
`ff43b02e59dfa604386bb382034b2cd07c2bcd8a`; A/B/C already appeared
in the 216-generation criteria pilot. The [UI contract](ui-behavioral-contracts-20260922.md)
records the target, other obligations and admission limits.

The trusted Playwright controller runs each authored HTML program as an offline
page in a fresh browser context. All arms would receive the same neutral
interface: one `#toggle-all` checkbox, `#clear-completed` button, `#todo-list`
with two active fixture todos, and `window.initialTodos`. The Clear completed
button may start hidden. Each direct todo `li` may nest its checkbox and label;
row order is not fixed. The generator must not receive the hidden assertions,
control programs or omitted target description in auxiliary context. Exact
prompt bytes remain to be written and reviewed before admission.

The target is checked state of the master after selecting both items and
clearing completed. It is evaluated only if both items became checked and
Clear completed removed them **in that same context**. Failed prerequisites
produce `not_evaluable` with a reason, never a target defect. If the original
master remains, its checked state decides. If it was removed, no checked
checkbox outside the todo list supports a pass; a different checked checkbox
makes master identity ambiguous rather than a defect. Screenshots before and
after target action, independent clear-action capture, DOM counts/states and
bounded console errors are retained. Images illustrate the DOM assertion;
checkbox state is not inferred from pixels alone.

The final authored qualification passed **11/11 controls**:

| Controls | Expected observation |
| --- | --- |
| Explicit state, derived state, initially hidden Clear button, nested/reversed rows, extra unrelated checked checkbox | All assertions pass |
| Master left checked after clear | Target-only failure |
| Single-item synchronization disabled | Non-target-only failure |
| Bulk selection disabled | Bulk failure; clear and target not evaluable |
| Clear action disabled | Clear failure; target not evaluable |
| Master removed with another checked checkbox outside list | Target identity ambiguous, not evaluable |
| Required initial master absent | Interface error |

The first seven-control version was superseded after independent review found
a false interface error for a hidden Clear button, direct-child/order
assumptions, missing local target prerequisites and insufficient target evidence.
The eleven-control version also separates an unexercised Clear action from an
observed Clear failure and treats unrelated checkboxes conservatively. Earlier
qualification runs remain development history; only the final packet below
should be used for this instrument version.

- Browser image ID: `sha256:76660c8b86cf518a43c334374d3a6c556f442878f05c007731c8d595b4409a7e`.
- Private qualification packet at `.private-research-evidence/mark-all-qualification-20260922-v1/qualification.json` in the shared workspace: report, original control HTML, external browser reports, three screenshots for each completed control, Docker commands/logs and file hashes. The private path is available in this workspace; it is not a public Git artifact.
- Qualification JSON SHA-256: `294087f7d3125123820d61dd5b708a7bc0225ca99afc158fa05e2065618c03a5`.
- Private packet receipt SHA-256: `459610e32a1ce74dfe036571f8b1d05a7883dc8735e67a21454451e2cb088032`; 86 files plus receipt, copied byte-for-byte from the final local run.
- Focused tests: 95 passed, 9 skipped at the final local checkpoint; `node --check` and `git diff --check` passed.
- [CI workflow](../../.github/workflows/mark-all-oracle-qualification.yml) rebuilds the pinned image and reruns all authored controls without provider calls.

This qualifies sensitivity and specificity on these controls only. It does not
prove correctness for arbitrary generated HTML, source-semantics approval by a
human expert, safety against browser escape, or a general smell effect. The
external Docker boundary uses non-root, no network, read-only input,
dropped capabilities and bounded resources; Chromium's own sandbox is disabled.
Before live collection, independently review exact prompt and leakage,
freeze the cohort/runtime/schedule, and ensure sufficient subscription
capacity. Other candidate oracles remain unqualified.
