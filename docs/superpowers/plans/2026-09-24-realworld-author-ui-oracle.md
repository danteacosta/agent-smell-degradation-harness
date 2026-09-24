# RealWorld Article-Author UI Oracle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and qualify a deterministic four-context browser oracle for the pinned RealWorld obligation that the Delete Article button is shown only to the article author.

**Architecture:** A trusted Python executor validates a closed `realworld-author-ui-browser/v1` report and runs a pinned offline Playwright container. The container serves one untrusted HTML artifact in four fresh contexts formed by two crossed Alice/Bob author-viewer pairs, applies the frozen perceptibility predicate, and emits observations plus screenshots. An authored-control qualifier checks positive, negative, non-evaluable, mixed and operational cases without admitting a study case or calling a model provider.

**Tech Stack:** Python 3.12, pytest, Node.js CommonJS, Playwright 1.58.2 with pinned Chromium container, Docker, GitHub Actions.

---

## Scope and contracts

Implement the approved design in `docs/superpowers/specs/2026-09-24-realworld-author-ui-oracle-design.md`. Keep these boundaries:

- fixed route and slug: `/article/bounded-ui-case` and `bounded-ui-case`;
- target IDs: `author_sees_delete_article` and `non_author_does_not_see_delete_article`;
- page preservation is a measurement prerequisite, not a non-target requirement;
- no provider call, prompt A/B/C freeze, corpus admission, result rescoring or H1/H2 claim;
- generated HTML remains untrusted and never executes in the Python process;
- browser sandbox state and container limits remain explicit in evidence.

## File map

- `eval/realworld_author_ui_executor.py`: strict report validation, scientific classification, operational outcomes, bounded Docker execution and evidence validation.
- `tests/test_realworld_author_ui_executor.py`: public-behavior tests for schema, precedence, process outcomes, screenshots and hashes.
- `eval/fixtures/realworld-author-ui/runner.cjs`: trusted fixture validation, offline serving, four fresh browser contexts, perceptibility sampling and report creation.
- `eval/fixtures/realworld-author-ui/Dockerfile`: pinned Playwright runtime under `pwuser`.
- `eval/fixtures/realworld-author-ui/package.json` and `package-lock.json`: exact runtime dependency lock.
- `eval/fixtures/realworld-author-ui/qualify.py`: authored-control execution, expected receipt checks and immutable evidence manifest.
- `eval/fixtures/realworld-author-ui/*.html`: small standalone positive and adversarial controls.
- `.github/workflows/realworld-author-ui-oracle-qualification.yml`: supported Linux/Python qualification and artifact retention.
- `docs/research/realworld-author-ui-oracle-qualification-20260924.md`: source, runtime, results, screenshot inspection and limitations after CI qualification.
- `docs/research/README.md`: index the qualification record.

### Task 1: Lock the Python report contract with failing tests

**Files:**
- Create: `tests/test_realworld_author_ui_executor.py`
- Create: `eval/realworld_author_ui_executor.py`

- [ ] **Step 1: Write report builders and the passing classification test**

Create a test helper that returns a complete four-observation report. Each observation has exactly:

```python
{
    "fixture_id": "article-alice",
    "context_id": "author",
    "route_ok": True,
    "title": {"matched": 1, "perceptible": 1},
    "body": {"matched": 1, "perceptible": 1},
    "article_author": {"matched": 1, "perceptible": 1},
    "delete_buttons": {"matched": 1, "perceptible": 1},
    "console_errors": [],
    "screenshot": "article-alice-author.png",
}
```

Use `article-alice`/`article-bob` and `author`/`non-author`; author contexts have one perceptible delete button and non-author contexts have zero. Assert:

```python
assert oracle.classify_report(report(), 0) == {
    "category": "pass",
    "target_failed": [],
    "target_not_evaluable": [],
    "not_evaluable_reasons": [],
}
```

- [ ] **Step 2: Run the focused test and verify the expected import failure**

Run: `python -m pytest tests/test_realworld_author_ui_executor.py::test_crossed_author_and_non_author_contexts_pass -q`

Expected: FAIL because `eval.realworld_author_ui_executor` does not exist.

- [ ] **Step 3: Add closed schema constants and the minimal passing classifier**

Define:

```python
SCHEMA_VERSION = "realworld-author-ui-browser/v1"
ASSERTION_IDS = (
    "author_sees_delete_article",
    "non_author_does_not_see_delete_article",
)
FIXTURE_IDS = ("article-alice", "article-bob")
CONTEXT_IDS = ("author", "non-author")
REASON_IDS = (
    "route_mismatch",
    "title_missing",
    "body_missing",
    "article_author_missing",
)
```

Parse with an `object_pairs_hook` that rejects duplicate fields. Require exact top-level and observation field sets, exact four fixture/context pairs, bounded integer counts `0..20`, SHA-256 strings, at most 20 console errors of at most 500 characters, and sorted unique target sets. Compute the classification from observations; never trust target sets supplied by the runner.

- [ ] **Step 4: Add failure-direction and multiplicity tests**

Assert these public outcomes:

- any author context with `perceptible == 0` fails only `author_sees_delete_article`;
- any non-author context with `perceptible >= 1` fails only `non_author_does_not_see_delete_article`;
- failures in both directions produce both sorted IDs;
- two perceptible author buttons still pass;
- matched-but-hidden or removed non-author buttons pass.

Run: `python -m pytest tests/test_realworld_author_ui_executor.py -q`

Expected: PASS for the implemented cases.

- [ ] **Step 5: Add prerequisite and mixed-evaluability tests**

For each closed prerequisite reason, mutate one observation and assert the dependent assertion ID appears in `target_not_evaluable` with an exact reason object:

```python
{
    "assertion_id": "author_sees_delete_article",
    "fixture_id": "article-bob",
    "context_id": "author",
    "reason": "body_missing",
}
```

Add a mixed case where the Bob-author page lacks its body while an Alice non-author context exposes a delete button. Assert category `target_not_evaluable`, return code `11`, `target_failed == ["non_author_does_not_see_delete_article"]`, and `target_not_evaluable == ["author_sees_delete_article"]`.

- [ ] **Step 6: Add fail-closed schema and return-code tests**

Parameterize duplicate keys, unknown schema, extra/missing fields, booleans used as counts, negative/oversized counts, duplicate fixture/context pairs, unsupported IDs/reasons, unsorted sets, inconsistent reason/set membership, oversized errors and category/return-code mismatches. Require `malformed_report` and preserve the observed subprocess return code as diagnostic data.

Run: `python -m pytest tests/test_realworld_author_ui_executor.py -q`

Expected: PASS.

- [ ] **Step 7: Commit the classifier contract**

```bash
git add eval/realworld_author_ui_executor.py tests/test_realworld_author_ui_executor.py
git commit -m "Add RealWorld author UI report contract"
```

### Task 2: Add bounded execution and evidence checks

**Files:**
- Modify: `eval/realworld_author_ui_executor.py`
- Modify: `tests/test_realworld_author_ui_executor.py`

- [ ] **Step 1: Write failing process-boundary tests**

Mock only `subprocess.run` and filesystem outputs, not classifier internals. Cover:

- `TimeoutExpired` becomes executor outcome `timeout` and triggers forced container removal;
- missing, symlinked or larger-than-100-KiB `report.json` becomes `malformed_report`;
- report-bearing runner return codes are restricted to `0`, `10`, `11`, `20`, `21`;
- all four required PNGs must be regular, non-symlinked PNG files no larger than 4 MiB;
- report `app_sha256` must equal the executor's hash of `app.html`;
- `interface_failure` and `browser_failure` never become target failures.

- [ ] **Step 2: Run the boundary tests and verify they fail for missing execution behavior**

Run: `python -m pytest tests/test_realworld_author_ui_executor.py -q`

Expected: FAIL in the new `execute` tests.

- [ ] **Step 3: Implement `execute` using the existing container policy**

Reuse `container_command` from `eval.focus_chain_executor`. Create a unique `realworld-author-ui-<uuid>` name; require a new output directory; persist `container-command.json` and `container.log`; call Docker with a 90-second default timeout; always force-remove the named container; then validate report, hash and screenshots before writing `executor.json`.

Keep executor-only outcomes separate from report categories:

```python
if timed_out:
    outcome = {"category": "timeout"}
elif raw is None or invalid_json_or_schema:
    outcome = {"category": "malformed_report"}
else:
    outcome = classify_report(raw, returncode)
```

- [ ] **Step 4: Run focused checks**

Run:

```bash
python -m pytest tests/test_realworld_author_ui_executor.py -q
python -m compileall -q eval/realworld_author_ui_executor.py tests/test_realworld_author_ui_executor.py
```

Expected: all tests pass and compilation exits zero.

- [ ] **Step 5: Commit the process boundary**

```bash
git add eval/realworld_author_ui_executor.py tests/test_realworld_author_ui_executor.py
git commit -m "Bound RealWorld browser execution"
```

### Task 3: Build the trusted four-context browser controller

**Files:**
- Create: `eval/fixtures/realworld-author-ui/runner.cjs`
- Create: `eval/fixtures/realworld-author-ui/package.json`
- Create: `eval/fixtures/realworld-author-ui/package-lock.json`
- Create: `eval/fixtures/realworld-author-ui/Dockerfile`

- [ ] **Step 1: Add the pinned package and image files**

Use package metadata:

```json
{
  "name": "realworld-author-ui-trusted-runner",
  "private": true,
  "version": "1.0.0",
  "dependencies": {"playwright": "1.58.2"}
}
```

Generate the lock with `npm install --package-lock-only --ignore-scripts`, then use the same digest-pinned Playwright 1.58.2 Noble base as the qualified Mark-all runner. Install with `npm ci --ignore-scripts --omit=dev --no-audit --no-fund`, copy only `runner.cjs`, set `HOME=/tmp`, run as `pwuser`, and use the runner as entrypoint.

- [ ] **Step 2: Implement fixture validation before Chromium starts**

Embed the two canonical fixtures in trusted runner code. Both use slug `bounded-ui-case`, title `Bounded UI case`, body `Observable article body`; only article/viewer usernames vary. Deep-freeze every nested value and install `window.initialState` with `writable:false` and `configurable:false` via `addInitScript`.

Support only the qualifier argument `--qualify-invalid-interface`; it deletes `article.author.username`, must produce a schema-valid `interface_failure` report with return code `20`, and must exit before browser launch or candidate execution. Reject every other argument.

- [ ] **Step 3: Implement the offline route and fresh-context loop**

Launch headless Chromium with `chromiumSandbox:false`. For each ordered pair:

```javascript
[
  ['article-alice', 'author', 'alice', 'alice'],
  ['article-alice', 'non-author', 'alice', 'bob'],
  ['article-bob', 'author', 'bob', 'bob'],
  ['article-bob', 'non-author', 'bob', 'alice'],
]
```

create a fresh context at viewport `1000 × 720`, block service workers/downloads, fulfill only the exact navigation URL `http://fixture.invalid/article/bounded-ui-case`, attach a CSP denying network, frames, objects and forms, and abort every other request. Bound default and navigation timeouts; dismiss dialogs; record capped console/page errors.

- [ ] **Step 4: Implement the perceptibility predicate exactly once**

For each matched element:

1. require Playwright `isVisible()`;
2. require a finite bounding box at least one CSS pixel in both dimensions;
3. multiply computed opacity from the element through its ancestors and require `> 0.01`;
4. scroll into view;
5. form the intersection with the viewport and sample a fixed inset `5 × 5` grid;
6. in `try/finally`, save target/ancestor inline `pointer-events`, apply `pointer-events:auto !important`, accept if one sampled point resolves to the element or descendant, then restore every declaration.

Use this same predicate for the role-based exact accessible-name button and the exact title/body/article-author prerequisite elements. Record both matched and perceptible counts. Keep the documented limitation for non-hit-testable overlays.

- [ ] **Step 5: Emit the closed report and screenshots**

Always write `report.json` in `finally`. A complete report includes exact observations, `browser_sandbox:false`, isolation text, runner/browser versions and four bounded screenshot names. Derive assertion sets and reason objects from observations, sort them, and assign return codes `0`, `10`, or `11`. Use `20` only for interface failure and `21` for browser failure.

- [ ] **Step 6: Check JavaScript and package integrity**

Run:

```bash
node --check eval/fixtures/realworld-author-ui/runner.cjs
npm ci --ignore-scripts --omit=dev --no-audit --no-fund --prefix eval/fixtures/realworld-author-ui
git diff --check
```

Expected: syntax succeeds, lockfile install succeeds, diff check is clean.

- [ ] **Step 7: Commit the runner**

```bash
git add eval/fixtures/realworld-author-ui
git commit -m "Add crossed-identity RealWorld browser runner"
```

### Task 4: Add the authored-control qualification matrix

**Files:**
- Create: `eval/fixtures/realworld-author-ui/qualify.py`
- Create: `eval/fixtures/realworld-author-ui/reference-explicit.html`
- Create: `eval/fixtures/realworld-author-ui/reference-derived-hidden.html`
- Create: `eval/fixtures/realworld-author-ui/reference-two-buttons.html`
- Create: `eval/fixtures/realworld-author-ui/reference-transparent-nonauthor.html`
- Create: `eval/fixtures/realworld-author-ui/reference-partial-occlusion.html`
- Create: `eval/fixtures/realworld-author-ui/reference-pointer-events-button.html`
- Create: `eval/fixtures/realworld-author-ui/reference-pointer-events-prerequisites.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-always-visible.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-never-visible.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-wrong-identity.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-hardcoded-alice.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-transparent-author.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-visible-and-transparent-nonauthor.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-fully-occluded-author.html`
- Create: `eval/fixtures/realworld-author-ui/control-broken-article.html`
- Create: `eval/fixtures/realworld-author-ui/control-mixed-evaluability.html`
- Modify: `tests/test_realworld_author_ui_executor.py`

- [ ] **Step 1: Write a failing matrix-completeness test**

Import `qualify.py` and assert its `EXPECTED` dictionary contains exactly the sixteen HTML IDs above. Assert the expected outcomes:

```python
PASS = ("pass", [], [])
EXPECTED["mutant-always-visible"] = (
    "target_only_failure", ["non_author_does_not_see_delete_article"], [])
EXPECTED["mutant-never-visible"] = (
    "target_only_failure", ["author_sees_delete_article"], [])
EXPECTED["mutant-wrong-identity"] = (
    "target_only_failure", list(ASSERTION_IDS), [])
EXPECTED["mutant-hardcoded-alice"] = (
    "target_only_failure", list(ASSERTION_IDS), [])
EXPECTED["mutant-transparent-author"] = (
    "target_only_failure", ["author_sees_delete_article"], [])
EXPECTED["mutant-visible-and-transparent-nonauthor"] = (
    "target_only_failure", ["non_author_does_not_see_delete_article"], [])
EXPECTED["mutant-fully-occluded-author"] = (
    "target_only_failure", ["author_sees_delete_article"], [])
EXPECTED["control-broken-article"] = (
    "target_not_evaluable", [], list(ASSERTION_IDS))
EXPECTED["control-mixed-evaluability"] = (
    "target_not_evaluable",
    ["non_author_does_not_see_delete_article"],
    ["author_sees_delete_article"],
)
```

All seven `reference-*` controls use `PASS`.

- [ ] **Step 2: Run the matrix test and verify it fails**

Run: `python -m pytest tests/test_realworld_author_ui_executor.py::test_qualification_matrix_is_complete -q`

Expected: FAIL because the qualifier and controls do not exist.

- [ ] **Step 3: Implement minimal self-contained HTML controls**

Each file must read only `window.initialState`, render the fixed title/body/author with stable semantic markup, and vary only the ownership/presentation behavior under test. Use `button` elements with accessible text `Delete Article`. Do not include source URLs, condition labels, oracle IDs or fixture expectations in candidate-visible bytes.

Implement the controls literally:

- explicit equality, derived `isOwner`, two author buttons, hidden/transparent non-author button, partial overlay, pointer-disabled button and pointer-disabled prerequisite text as passing structures;
- unconditional show, unconditional hide, inverted equality, hard-coded Alice, transparent author, visible plus transparent non-author, and fully covering hit-testable overlay as target mutants;
- omit the body in every context for `control-broken-article`;
- for `control-mixed-evaluability`, omit the body only for Bob's author context and expose a button for Alice viewing Bob's article.

- [ ] **Step 4: Implement the qualifier**

Require an immutable image ID matching `sha256:<64 hex>`, verify `docker image inspect` returns the same ID, create a mode-`0700` output directory, copy each control to `input/app.html`, execute it, and compare category plus both target sets and exact reason objects. Run the interface-boundary control separately with the runner's trusted qualification argument and assert `interface_failure`, return code `20`, and absence of screenshots.

Accept a required `--git-commit <40 lowercase hex>` argument and write
`realworld-author-ui-qualification/v1` with:

- `qualified` boolean;
- qualified Git commit;
- image ID;
- one row per expected control;
- receipt/report/screenshot SHA-256 values;
- hashes for every fixture/runtime/executor input;
- the pinned source revision and preserved source SHA;
- explicit limitation text denying smell-causality and browser-escape claims.

- [ ] **Step 5: Build and execute the full matrix locally**

Run:

```bash
docker build --iidfile /tmp/realworld-author-ui-image eval/fixtures/realworld-author-ui
python eval/fixtures/realworld-author-ui/qualify.py \
  --image "$(cat /tmp/realworld-author-ui-image)" \
  --git-commit "$(git rev-parse HEAD)" \
  --output /tmp/realworld-author-ui-qualification
```

Expected: JSON reports `"qualified": true`; sixteen HTML controls and one interface-boundary control match exactly.

- [ ] **Step 6: Inspect representative visual evidence**

Open and inspect at minimum these PNGs: explicit author/non-author, two-button author, transparent non-author, partial occlusion, pointer-disabled button, fully occluded author, hard-coded Alice in both crossed fixture pairs, broken article and mixed evaluability. Record any visual/structured discrepancy as a failed qualification and fix the root cause before continuing.

- [ ] **Step 7: Run focused regression checks and commit**

Run:

```bash
python -m pytest tests/test_realworld_author_ui_executor.py -q
python -m compileall -q eval/realworld_author_ui_executor.py eval/fixtures/realworld-author-ui/qualify.py
node --check eval/fixtures/realworld-author-ui/runner.cjs
git diff --check
```

Expected: all pass.

```bash
git add eval/fixtures/realworld-author-ui tests/test_realworld_author_ui_executor.py
git commit -m "Qualify RealWorld author UI controls"
```

### Task 5: Add supported CI qualification

**Files:**
- Create: `.github/workflows/realworld-author-ui-oracle-qualification.yml`

- [ ] **Step 1: Add the path-scoped workflow**

Mirror the established qualification workflow structure. Trigger on `workflow_dispatch` and pull requests touching the executor, fixture directory, focused test or workflow. Use `ubuntu-24.04`, Python `3.12`, `contents: read`, a 20-minute job timeout and `persist-credentials:false`.

- [ ] **Step 2: Run static/focused checks before the Docker build**

Add steps for:

```bash
python -m pytest tests/test_realworld_author_ui_executor.py -q
python -m compileall -q eval/realworld_author_ui_executor.py eval/fixtures/realworld-author-ui/qualify.py
node --check eval/fixtures/realworld-author-ui/runner.cjs
```

- [ ] **Step 3: Build by digest, qualify and always upload evidence**

Write the Docker image ID to `$RUNNER_TEMP/realworld-author-ui-image`, invoke
the qualifier with that immutable ID and `$GITHUB_SHA`, and upload the entire
qualification directory as artifact `realworld-author-ui-qualification` for
30 days under `if: always()`.

- [ ] **Step 4: Validate workflow syntax and commit**

Run: `python -c 'import yaml; yaml.safe_load(open(".github/workflows/realworld-author-ui-oracle-qualification.yml"))'`

If PyYAML is unavailable, parse it with the repository's existing workflow validation route and inspect `git diff --check`; do not add a runtime dependency only for this check.

```bash
git add .github/workflows/realworld-author-ui-oracle-qualification.yml
git commit -m "Run RealWorld UI oracle qualification in CI"
```

### Task 6: Publish and verify qualification evidence

**Files:**
- Create: `docs/research/realworld-author-ui-oracle-qualification-20260924.md`
- Modify: `docs/research/README.md`

- [ ] **Step 1: Push the implementation branch and wait for every required check**

Run:

```bash
git push
gh pr checks 77 --watch
```

Expected: focused qualification plus repository eval/replay/wedge gates succeed. Investigate any failure using `superpowers:systematic-debugging`; do not weaken controls to obtain green CI.

- [ ] **Step 2: Download the exact CI artifact and verify custody**

Use the successful workflow run ID:

```bash
gh run download <run-id> --name realworld-author-ui-qualification --dir /tmp/realworld-author-ui-ci
```

Recompute hashes locally, verify `qualified:true`, verify the artifact's image ID and head commit, count expected files, and inspect representative screenshots from the CI artifact rather than relying only on local output.

- [ ] **Step 3: Write the qualification record**

Record source URL/revision/SHA, exact head commit, image ID, qualification/report hashes, artifact digest, control denominator and outcome table, screenshot hashes and the browser-sandbox flag. State explicitly:

- this proves sensitivity/specificity only for authored controls under the bounded endpoint;
- it does not admit RealWorld into the experiment;
- it is not a provider-produced result and does not add evidence for H1/H2;
- TodoMVC remains the only project with collected E2E experimental outputs until a prospective RealWorld A/B/C collection is frozen and run;
- Chromium sandbox is disabled inside the constrained Docker boundary, which is not proof of browser-escape safety.

- [ ] **Step 4: Index, lint and commit evidence**

Run:

```bash
git diff --check
python -m pytest tests/test_realworld_author_ui_executor.py -q
```

Then:

```bash
git add docs/research/realworld-author-ui-oracle-qualification-20260924.md docs/research/README.md
git commit -m "Document RealWorld UI oracle qualification"
git push
```

### Task 7: Final quality and scope gate

**Files:**
- Review all files changed by Tasks 1–6.

- [ ] **Step 1: Run the supported verification set**

Run focused tests, compilation, Node syntax, `npm ci`, Docker qualification and `git diff --check` again. Confirm current PR checks are green at the final head.

- [ ] **Step 2: Run security and trust-boundary review**

Verify exact-route network abortion, CSP, no host execution of candidate code, non-root container, read-only input, bounded output, dropped capabilities/resource limits from `container_command`, report-size caps, screenshot caps, no symlink acceptance, exact image identity, browser sandbox disclosure, and forced container cleanup.

- [ ] **Step 3: Run SOLID and clean-code review**

Confirm the executor owns schema/process policy, the runner owns browser
observation plus its independently declared status, and the qualifier owns
authored expectations. The adapter must recompute and validate runner-declared
sets/category rather than trusting them; this deliberate cross-check is not
shared policy code. Reject generic factories or strategy hierarchies: there is
one fixed oracle and one fixed fixture policy.

- [ ] **Step 4: Check scientific scope and staleness**

Search changed docs and code for accidental claims of admission, project generalization, H1/H2 confirmation or “two E2E projects” before prospective collection. Ensure all denominators say sixteen HTML controls plus one interface-boundary control and that source/runtime/hash values agree across workflow artifact and documentation.

- [ ] **Step 5: Request final code review and update the draft PR**

Use `superpowers:requesting-code-review`, fix any verified blocking findings,
rerun affected checks, and update PR #77 title/body around the final
implementation. Keep it draft until final CI and review are green; then mark it
ready and merge it under the user's existing authorization.
