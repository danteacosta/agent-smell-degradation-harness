# Persistence Semantic Row Recognition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Qualify a successor persistence browser instrument that recognizes one exact visible todo title across equivalent DOM structures and fails closed on absence or ambiguity.

**Architecture:** Keep report adaptation in Python and browser observation in the pinned JavaScript runner. Replace the runner's nullable row lookup with a three-state semantic recognition result, then exercise it through authored HTML modes in the real offline browser image. Historical packets and classifications remain unchanged.

**Tech Stack:** Python 3.14, pytest, Node.js, Playwright, Docker

---

### Task 1: Admit the new unknown reason at the trusted report boundary

**Files:**
- Modify: `eval/persistence_executor.py`
- Modify: `tests/test_persistence_executor.py`

- [ ] **Step 1: Write the failing report-classification test**

Add a test that creates a complete report with
`editing_not_restored.status = "not_evaluable"` and
`reason = "todo_ambiguous_after_reload"`. Assert the result is
`target_not_evaluable`, with `target_failed: None` and the supplied
non-target failures.

- [ ] **Step 2: Run the focused test and verify RED**

Run:
`/private/tmp/masters-next-venv/bin/python -m pytest tests/test_persistence_executor.py -q`

Expected: FAIL because the new reason is not in `UNKNOWN_REASONS`.

- [ ] **Step 3: Implement the minimal adapter change**

Add `todo_ambiguous_after_reload` to `UNKNOWN_REASONS`. Do not alter category
or return-code logic.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run the command from Step 2. Expected: all persistence executor tests pass.

- [ ] **Step 5: Commit**

`git add eval/persistence_executor.py tests/test_persistence_executor.py && git commit -m "test: classify ambiguous persistence rows as unknown"`

### Task 2: Add alternative-DOM and ambiguity controls

**Files:**
- Modify: `eval/fixtures/persistence/control.html`
- Modify: `eval/fixtures/persistence/qualify.py`

- [ ] **Step 1: Extend the qualification matrix before changing the runner**

Add modes and exact vectors from the approved design:

- `span-title`, `div-title`, and `nested-title`: `pass`, no failures;
- `hidden-exact-title`, `accessible-only-title`, `control-value-title`,
  `substring-title`, `duplicate-rows`, and `duplicate-titles`:
  `interface_error`, no assertion failures;
- `duplicate-after-reload`: `target_not_evaluable`, failures
  `todo_survives_reload` and `completed_survives_reload`, reason
  `todo_ambiguous_after_reload`.

Render each title structure directly in `control.html`. The ordinary edit
handler must be attached to the visible title element or an ancestor reached by
event bubbling. The control-value mode must use an unrelated non-editing
`input` that is visible and editable; it must never satisfy edit-input
recognition because it is not the row's active editor.

Apply the six initial-recognition-invalid mutations only when
`item.title === "persist-target-row"`. The three earlier non-target scenarios
must retain the ordinary valid title structure, so their successful assertions
remain meaningful before the target scenario returns `interface_error`.
`duplicate-after-reload` is the exception: duplicate every restored row only
after loading from storage so the two non-target reload assertions fail and the
target becomes ambiguous on the second page.

Add an expected screenshot inventory per category to the qualification matrix.
Complete and target-not-evaluable controls require exactly
`before-edit.png`, `editing.png`, and `after-reload.png`.
Initial-recognition `interface_error` controls require exactly
`before-edit.png`. Qualification must compare this expected filename set with
the actual regular PNG files; screenshot hashes alone are evidence, not the
predicate.

- [ ] **Step 2: Build a temporary successor image**

Run:
`docker build -f eval/fixtures/persistence/Dockerfile -t persistence-semantic-selector-red eval/fixtures/persistence`

- [ ] **Step 3: Run qualification and verify RED**

Resolve the immutable image ID with `docker image inspect`, then run
`eval/fixtures/persistence/qualify.py` into a fresh private directory.

Expected: the existing label-only runner fails the new passing controls and
does not produce the exact ambiguity vectors.

- [ ] **Step 4: Commit the failing behavioral controls**

`git add eval/fixtures/persistence/control.html eval/fixtures/persistence/qualify.py && git commit -m "test: add semantic persistence selector controls"`

### Task 3: Implement three-state semantic recognition

**Files:**
- Modify: `eval/fixtures/persistence/runner.cjs`

- [ ] **Step 1: Replace nullable lookup with a structured result**

Implement `recognizeRow(page, title, {visibleOnly = true} = {})` returning:

```javascript
{status: 'matched', row, titleElement}
{status: 'absent'}
{status: 'ambiguous'}
```

For each `ul.todo-list > li`, inspect visible non-form descendants using
rendered `innerText`, trim only surrounding whitespace, require complete
equality, and remove a candidate when it contains a more specific matching
descendant. A match requires one candidate in one row. The edit-input fallback
keeps the existing `editInput(row)` predicate: visible, editable, text-like,
and contained by that row. It qualifies as the row title only when its value
exactly matches and the row exposes no visible non-form element with non-empty
rendered title text. This distinguishes an active edit state from the negative
control's unrelated input plus visible nonmatching title without requiring a
CSS class, ARIA role, or other implementation-specific attribute.

- [ ] **Step 2: Apply the phase-specific handling matrix**

Before edit, `absent` and `ambiguous` throw `InterfaceError`. Non-target
checks return false for either. After second-page navigation, map absence to the
existing missing/hidden reasons and ambiguity to
`todo_ambiguous_after_reload`. Double-click `titleElement`, never a hard-coded
`label` locator.

Keep hidden-row diagnosis separate from semantic recognition. A diagnostic-only
`hasExactDomTitle(page, title)` may inspect normalized `textContent` in
non-visible rows after semantic recognition returns `absent`; it can select
only the unknown reason `todo_not_visible_after_reload` and must never return
a row, pass an assertion, or drive an interaction.

- [ ] **Step 3: Rebuild and rerun qualification**

Build a new immutable image and run the same fresh qualification command.

Expected: every old and new vector matches, all required screenshots exist, and
`qualified` is true.

- [ ] **Step 4: Run focused Python tests**

Run:
`/private/tmp/masters-next-venv/bin/python -m pytest tests/test_persistence_executor.py tests/test_persistence_collection.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

`git add eval/fixtures/persistence/runner.cjs && git commit -m "fix: recognize semantic persistence row titles"`

### Task 4: Preserve qualification evidence and scientific boundaries

**Files:**
- Modify: `docs/research/persistence-oracle-qualification-20260922.md`
- Modify: `docs/research/persistence-results-20260923.md`
- Create: `docs/research/persistence-selector-qualification-20260923.md`
- Modify: `README.md`

- [ ] **Step 1: Record the successor qualification**

Document the new image ID, control count, qualification and packet receipts,
exact selector boundary, visual inspection, and that the successor does not
retroactively reclassify the original five unknowns.

- [ ] **Step 2: Add the post-hoc diagnostic rule**

State that replaying saved HTML with the successor is diagnostic only.
Prospective inference requires a newly admitted frozen collection.

- [ ] **Step 3: Run documentation drift checks**

Run `rg` for old control counts, image IDs, and statements claiming the
label-only runner is current. Update only statements that describe the current
instrument; keep historical packet descriptions intact.

- [ ] **Step 4: Commit**

`git add README.md docs/research && git commit -m "docs: record semantic selector qualification"`

### Task 5: Final verification and integration

**Files:**
- Verify all changed files

- [ ] **Step 1: Run the full repository checks**

Run:

```bash
/private/tmp/masters-next-venv/bin/python -m pytest -q
/private/tmp/masters-next-venv/bin/python -m eval
/private/tmp/masters-next-venv/bin/python -m gates
git diff --check origin/main...HEAD
```

Expected: zero failures and clean diff validation.

- [ ] **Step 2: Review the diff**

Check ATDD criteria, behavior-level coverage, error handling, single
responsibility, dependency clarity, duplication, hidden side effects, and that
the matcher has no test-only production branches.

- [ ] **Step 3: Open a PR**

Push the branch, create a PR describing the measurement defect, successor
behavior, qualification evidence and non-retroactivity boundary, then attach
the PR to the task.

- [ ] **Step 4: Merge only after CI passes**

Verify every required check against the exact head SHA and squash-merge with
head matching. Confirm the integrated `main` tree equals the tested branch.
