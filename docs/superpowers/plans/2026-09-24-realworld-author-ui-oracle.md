# RealWorld Article-Author UI Oracle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and qualify a deterministic four-context browser oracle for the pinned RealWorld obligation that the Delete Article button is shown only to the article author.

**Architecture:** A trusted Python executor validates a closed `realworld-author-ui-browser/v1` report and runs a pinned offline Playwright container. The container serves one untrusted HTML artifact in four fresh contexts formed by two crossed Alice/Bob author-viewer pairs, applies the frozen perceptibility predicate, and emits observations plus screenshots. An authored-control qualifier checks positive, negative, non-evaluable, mixed and operational cases without admitting a study case or calling a model provider.

**Tech Stack:** Python 3.12, pytest, Node.js CommonJS, Playwright 1.58.2 with pinned Chromium container, Docker, GitHub Actions.

---

## Scope and contracts

Implement the approved design in `docs/superpowers/specs/2026-09-24-realworld-author-ui-oracle-design.md`. Keep these boundaries:

- fixed route and slug: `/article/bounded-ui-case` and `bounded-ui-case`;
- public article-author relation: visible exact username inside an element whose
  `rel` token list contains `author`;
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

## Closed browser-report schema

`classify_report(raw: bytes | None, returncode: int)` parses raw JSON bytes with
duplicate-key rejection. All report forms share exactly these fields:

```text
schema_version: "realworld-author-ui-browser/v1"
status: "complete" | "interface_failure" | "browser_failure"
app_sha256: 64 lowercase hex characters
runner_version: "1"
browser_sandbox: false
isolation: non-empty string, at most 500 characters
```

A `complete` report has exactly these additional fields:

```text
browser_version: non-empty string, at most 200 characters
viewport: {width: 1000, height: 720}
sample_grid: {dimension: 5, inset_ratio: 0.08}
observations: exactly four observation objects in canonical fixture/context order
target_failed: sorted unique subset of the two assertion IDs
target_not_evaluable: sorted unique subset of the two assertion IDs
not_evaluable_reasons: sorted unique reason objects
screenshots: exactly the four canonical PNG filenames
```

Each observation has exactly:

```text
fixture_id: "article-alice" | "article-bob"
context_id: "author" | "non-author"
final_url: "http://fixture.invalid/article/bounded-ui-case"
title/body/article_author/delete_buttons: {matched: int 0..20, perceptible: int 0..matched}
runtime_errors: at most 20 exact {kind: "console" | "page", message: string <= 500} objects
screenshot: "<fixture_id>-<context_id>.png"
```

Python recomputes route validity from `final_url`; the runner does not emit a
`route_ok` Boolean. A violated prerequisite emits one reason object per violated
field and dependent assertion/context, so simultaneous route/body failures are
preserved rather than collapsed.

An operational report has no observations, target sets, screenshots, viewport,
grid or browser-version fields. It has exactly the common fields plus
`error: string <= 1500` and `browser_started: bool`. `interface_failure`
requires `browser_started:false` and return code `20`; `browser_failure` accepts
either Boolean and requires return code `21`. Operational reports never require
screenshots and never enter scientific classification.

### Task 1: Lock the Python report contract with failing tests

**Files:**
- Create: `tests/test_realworld_author_ui_executor.py`
- Create: `eval/realworld_author_ui_executor.py`

- [ ] **Step 1: Write the complete classifier contract before implementation**

Create a test helper that serializes a complete four-observation report to
bytes. Each observation has exactly:

```python
{
    "fixture_id": "article-alice",
    "context_id": "author",
    "final_url": "http://fixture.invalid/article/bounded-ui-case",
    "title": {"matched": 1, "perceptible": 1},
    "body": {"matched": 1, "perceptible": 1},
    "article_author": {"matched": 1, "perceptible": 1},
    "delete_buttons": {"matched": 1, "perceptible": 1},
    "runtime_errors": [],
    "screenshot": "article-alice-author.png",
}
```

Use `article-alice`/`article-bob` and `author`/`non-author`; author contexts have one perceptible delete button and non-author contexts have zero. Assert:

```python
assert oracle.classify_report(report_bytes(), 0) == {
    "category": "pass",
    "target_failed": [],
    "target_not_evaluable": [],
    "not_evaluable_reasons": [],
}
```

In the same test-first change, add all failure-direction, prerequisite,
mixed-evaluability, schema and return-code tests before creating the executor.
Cover:

- zero perceptible author buttons, perceptible non-author buttons, both target
  directions together, two valid author buttons, and hidden/removed non-author
  buttons;
- each closed prerequisite reason and simultaneous prerequisite reasons;
- the mixed case where Bob's author page lacks its body while Alice viewing
  Bob's article exposes a delete button;
- duplicate keys as raw bytes, unknown schema, extra/missing fields, booleans as
  counts, negative/oversized counts, `perceptible > matched`, duplicate pairs,
  bad final URLs, malformed screenshot names, unsupported IDs/reasons, unsorted
  sets, inconsistent reason/set membership, oversized runtime errors, wrong
  operational fields and return-code contradictions.

- [ ] **Step 2: Run the complete classifier contract and verify it is red**

Run: `python -m pytest tests/test_realworld_author_ui_executor.py -q`

Expected: collection/import FAIL because
`eval.realworld_author_ui_executor` does not exist. Preserve this red result.

- [ ] **Step 3: Implement the closed classifier contract**

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

Parse with an `object_pairs_hook` that rejects duplicate fields. Apply the
closed schema above, including canonical screenshot names and observation
ordering. Compute the classification from observations and require the
runner-declared target sets, reasons and return code to match it exactly.

- [ ] **Step 4: Implement exact prerequisite reasoning and precedence**

For each violated prerequisite, derive a reason object shaped as:

```python
{
    "assertion_id": "author_sees_delete_article",
    "fixture_id": "article-bob",
    "context_id": "author",
    "reason": "body_missing",
}
```

Implement category precedence so any non-evaluable assertion produces
`target_not_evaluable` while retaining evaluable target failures. A complete
report does not carry a category field: category is adapter-only. The adapter
recomputes sets/reasons, validates the runner declarations and derives category
plus the required `0`, `10` or `11` return code.

- [ ] **Step 5: Run the previously red contract and make it green**

Run: `python -m pytest tests/test_realworld_author_ui_executor.py -q`

Expected: every prewritten classifier test passes.

- [ ] **Step 6: Commit the classifier contract**

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

### Task 3: Write browser acceptance controls before the controller

**Files:**
- Create: `eval/fixtures/realworld-author-ui/runner.cjs`
- Create: `eval/fixtures/realworld-author-ui/package.json`
- Create: `eval/fixtures/realworld-author-ui/package-lock.json`
- Create: `eval/fixtures/realworld-author-ui/Dockerfile`
- Create: `eval/fixtures/realworld-author-ui/qualify.py`
- Create: `eval/fixtures/realworld-author-ui/reference-explicit.html`
- Create: `eval/fixtures/realworld-author-ui/reference-derived-hidden.html`
- Create: `eval/fixtures/realworld-author-ui/reference-two-buttons.html`
- Create: `eval/fixtures/realworld-author-ui/reference-transparent-nonauthor.html`
- Create: `eval/fixtures/realworld-author-ui/reference-partial-occlusion.html`
- Create: `eval/fixtures/realworld-author-ui/reference-pointer-events-button.html`
- Create: `eval/fixtures/realworld-author-ui/reference-pointer-events-prerequisites.html`
- Create: `eval/fixtures/realworld-author-ui/reference-fresh-context.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-always-visible.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-never-visible.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-wrong-identity.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-hardcoded-alice.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-transparent-author.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-visible-and-transparent-nonauthor.html`
- Create: `eval/fixtures/realworld-author-ui/mutant-fully-occluded-author.html`
- Create: `eval/fixtures/realworld-author-ui/control-broken-article.html`
- Create: `eval/fixtures/realworld-author-ui/control-mixed-evaluability.html`
- Create: `eval/fixtures/realworld-author-ui/control-viewer-only-author-text.html`
- Create: `eval/fixtures/realworld-author-ui/control-hidden-author-text.html`
- Modify: `tests/test_realworld_author_ui_executor.py`

- [ ] **Step 1: Write the nineteen self-contained HTML acceptance controls**

Each file reads only `window.initialState`, renders the fixed title/body/author
with semantic markup, and varies only the ownership/presentation behavior under
test. Use `button` elements with accessible text `Delete Article`. Do not put
source URLs, condition labels, oracle IDs or fixture expectations in
candidate-visible bytes.

Implement explicit equality, derived ownership with hidden non-author state,
two author buttons, transparent non-author, partial overlay, pointer-disabled
button, pointer-disabled prerequisite text, and a local-storage fresh-context
sentinel as eight passing references. Implement unconditional show,
unconditional hide, inverted equality, hard-coded Alice, transparent author,
visible plus transparent non-author, and fully covering hit-testable overlay as
seven target mutants. Omit the body in every context for the broken-article
control. For mixed evaluability, omit the body only for Bob's author context and
expose a button for Alice viewing Bob's article. In the viewer-only-author-text
control, display the expected username in viewer navigation but omit every
`[rel~="author"]` element; both target assertions must be not evaluable with
`article_author_missing` in their applicable contexts. In the hidden-author-text
control, render a visible `[rel~="author"]` container whose matching username is
present only in a hidden descendant; require the same not-evaluable reasons.

- [ ] **Step 2: Write custody and matrix declarations as failing tests**

Before creating `qualify.py`, add tests that import it and require the exact
nineteen-control ID set, expected target sets/reason arrays, two operational
controls, mutual exclusion of `--provisional`/`--git-commit`, rejection of a
non-HEAD commit, rejection of dirty hashed paths, and the invariant that
provisional output can never be qualified.

Run: `python -m pytest tests/test_realworld_author_ui_executor.py -q`

Expected: FAIL because `qualify.py` does not exist. Preserve this red result.

- [ ] **Step 3: Implement the executable qualifier and exact expectations**

Create the full `EXPECTED` map before writing runner code. The seven target
mutants declare the exact failed assertion sets. The broken-article reasons are
exactly these four canonically sorted objects:

```python
[
  {"assertion_id": "author_sees_delete_article", "fixture_id": "article-alice",
   "context_id": "author", "reason": "body_missing"},
  {"assertion_id": "author_sees_delete_article", "fixture_id": "article-bob",
   "context_id": "author", "reason": "body_missing"},
  {"assertion_id": "non_author_does_not_see_delete_article",
   "fixture_id": "article-alice", "context_id": "non-author", "reason": "body_missing"},
  {"assertion_id": "non_author_does_not_see_delete_article",
   "fixture_id": "article-bob", "context_id": "non-author", "reason": "body_missing"},
]
```

The mixed control has only the second object above and also fails
`non_author_does_not_see_delete_article`. The viewer-only-author-text control
uses the same four assertion/fixture/context tuples as the broken control with
reason `article_author_missing` instead of `body_missing`; the hidden-author-text
control has the identical expected reason array. Add two operational runs. For invalid
interface, mount `reference-explicit.html` as `/input/app.html` and execute:

```python
[*container_command(image, inputs, output, name), "--qualify-invalid-interface"]
```

Expect the exact operational shape, `status:interface_failure`,
`browser_started:false`, return code `20`, no observations and no screenshots.
Use `--qualify-browser-failure` similarly, deliberately throw immediately after
browser launch, and require `status:browser_failure`, `browser_started:true`,
return code `21`, no observations and no screenshots.

The qualifier accepts mutually exclusive custody modes. `--provisional` can
exercise dirty worktree bytes but must emit `matrix_matches` separately and
must set `qualified:false`. `--git-commit <40 lowercase hex>` requires the value
to equal `git rev-parse HEAD`, requires every hashed instrument path to be clean
according to `git status --porcelain -- <paths>`, and may set `qualified:true`.
Require an immutable image ID matching `sha256:<64 hex>`, confirm it with
`docker image inspect`, create a mode-`0700` output directory, and write
`realworld-author-ui-qualification/v1` with custody mode/commit, image ID, one
row per expected control, exact observed/expected category/sets/reasons,
receipt/report/screenshot hashes, every fixture/runtime/executor input hash,
the pinned source revision/SHA, and narrow limitation text.

- [ ] **Step 4: Make the custody tests green, then add a deliberately incomplete runner**

Run the focused Python suite and make every prewritten custody/matrix test pass.
Then create a buildable `runner.cjs` that only hashes `/input/app.html`, emits a
schema-incomplete browser-failure report and exits `21`. This stub contains no
browser contract behavior and will be replaced, not extended with production
branches.

Create the pinned `package.json`, lock and Dockerfile using the metadata below.

```json
{
  "name": "realworld-author-ui-trusted-runner",
  "private": true,
  "version": "1.0.0",
  "dependencies": {"playwright": "1.58.2"}
}
```

Generate the lock with `npm install --package-lock-only --ignore-scripts`. Use
the same digest-pinned Playwright 1.58.2 Noble base as Mark-all, install with
`npm ci --ignore-scripts --omit=dev --no-audit --no-fund`, copy only
`runner.cjs`, set `HOME=/tmp`, run as `pwuser`, and use the runner as entrypoint.

Build the stub and run the actual qualifier:

```bash
docker build --iidfile /tmp/realworld-author-ui-red-image eval/fixtures/realworld-author-ui
python eval/fixtures/realworld-author-ui/qualify.py \
  --provisional --image "$(cat /tmp/realworld-author-ui-red-image)" \
  --output /tmp/realworld-author-ui-red
```

Expected: FAIL with explicit mismatches for the HTML matrix. This proves the
executable acceptance harness is red because browser behavior is absent, rather
than because a file or image is missing.

- [ ] **Step 5: Replace the stub with the runner and fixture validation**

Embed the two canonical fixtures in trusted runner code. Both use slug `bounded-ui-case`, title `Bounded UI case`, body `Observable article body`; only article/viewer usernames vary. Deep-freeze every nested value and install `window.initialState` with `writable:false` and `configurable:false` via `addInitScript`.

Support the two qualifier-only arguments defined above and reject every other
argument. The invalid-interface mode deletes `article.author.username` and exits
before browser launch or candidate execution. The browser-failure mode launches
Chromium, throws before any page/context is created, and closes the browser in
`finally`.

- [ ] **Step 6: Implement the offline route and fresh-context loop**

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

- [ ] **Step 7: Implement locators and the perceptibility predicate exactly once**

After navigation reaches `load`, wait one fixed 300-ms settle interval, then
enumerate all locators. Resolve buttons with
`getByRole('button', {name:/^Delete\s+Article$/i})`, which anchors the accessible
name while normalizing intervening whitespace and folding case. Resolve title
and body with Playwright `getByText(expected, {exact:true})`, using its smallest
exact text matches instead of scanning ancestor `textContent`. Resolve article
authorship by scoping `getByText(expected, {exact:true})` within each
`[rel~="author"]` element, deduplicating the resulting smallest text-bearing
elements, and applying perceptibility to those matched elements themselves.
Viewer text, unrelated usernames and a username present only in a hidden
descendant are excluded. This `rel="author"` relation is part of the common
public candidate contract, not a fixture-only selector. Duplicates are counted
and at least one perceptible match satisfies each page prerequisite.

For each matched element:

1. require Playwright `isVisible()`;
2. require a finite bounding box at least one CSS pixel in both dimensions;
3. multiply computed opacity from the element through its ancestors and require `> 0.01`;
4. scroll into view and then refresh its bounding box;
5. form the refreshed intersection with the viewport and sample a fixed inset `5 × 5` grid;
6. in `try/finally`, save target/ancestor inline `pointer-events`, apply `pointer-events:auto !important`, accept if one sampled point resolves to the element or descendant, then restore every declaration.

Use this same predicate for the role-based exact accessible-name button and the exact title/body/article-author prerequisite elements. Record both matched and perceptible counts. Keep the documented limitation for non-hit-testable overlays.

- [ ] **Step 8: Emit the closed report and screenshots**

Always write `report.json` in `finally`. A complete report includes exact observations, `browser_sandbox:false`, isolation text, runner/browser versions and four bounded screenshot names. Derive assertion sets and reason objects from observations, sort them, and assign return codes `0`, `10`, or `11`. Use `20` only for interface failure and `21` for browser failure.

- [ ] **Step 9: Build and run every browser acceptance control**

Build the pinned image, then run the qualifier with `--provisional`. Expected:
all nineteen HTML controls plus both operational controls match, while the
manifest remains explicitly unqualified because custody is provisional. This
run must prove crossed identities, transparency, partial/full occlusion,
pointer-event independence, multiplicity, exact route/final URL, fresh-context
isolation, mixed evaluability, interface failure and browser failure.

- [ ] **Step 10: Check JavaScript and package integrity**

Run:

```bash
node --check eval/fixtures/realworld-author-ui/runner.cjs
npm ci --ignore-scripts --omit=dev --no-audit --no-fund --prefix eval/fixtures/realworld-author-ui
git diff --check
```

Expected: syntax succeeds, lockfile install succeeds, diff check is clean.

- [ ] **Step 11: Commit the complete browser instrument**

```bash
git add eval/fixtures/realworld-author-ui
git commit -m "Add crossed-identity RealWorld browser instrument"
```

### Task 4: Bind the qualification matrix to committed custody

**Files:**
- Modify: `eval/fixtures/realworld-author-ui/qualify.py`
- Modify: `tests/test_realworld_author_ui_executor.py`

- [ ] **Step 1: Verify the prewritten matrix and custody regression tests**

Confirm the tests written before `qualify.py` assert `EXPECTED` contains
exactly the nineteen HTML IDs from Task 3. Assert all eight `reference-*`
controls pass and the seven target mutants have these exact failed sets:

```python
ONE_AUTHOR = ["author_sees_delete_article"]
ONE_NON_AUTHOR = ["non_author_does_not_see_delete_article"]
BOTH = sorted(ONE_AUTHOR + ONE_NON_AUTHOR)
MUTANT_FAILURES = {
    "mutant-always-visible": ONE_NON_AUTHOR,
    "mutant-never-visible": ONE_AUTHOR,
    "mutant-wrong-identity": BOTH,
    "mutant-hardcoded-alice": BOTH,
    "mutant-transparent-author": ONE_AUTHOR,
    "mutant-visible-and-transparent-nonauthor": ONE_NON_AUTHOR,
    "mutant-fully-occluded-author": ONE_AUTHOR,
}
```

Assert the broken and mixed reason objects equal the exact arrays from Task 3.
Test that `--git-commit` rejects a non-HEAD SHA and any dirty hashed path, while
`--provisional` can run but can never emit `qualified:true`.

- [ ] **Step 2: Run the regression tests**

Run: `python -m pytest tests/test_realworld_author_ui_executor.py -q`

Expected: PASS.

- [ ] **Step 3: Commit any custody-test corrections before qualification**

If Task 4 changes any hashed instrument byte, commit it and rebuild the image.
Do not produce a custody-bearing manifest from dirty instrument paths.

- [ ] **Step 4: Build and execute the custody-bearing matrix locally**

Run:

```bash
realworld_evidence_dir="$(mktemp -d /private/tmp/realworld-author-ui-qualification.XXXXXX)"
realworld_instrument_digest="$(python eval/fixtures/realworld-author-ui/qualify.py --print-instrument-digest)"
realworld_head="$(git rev-parse HEAD)"
docker build \
  --build-arg REALWORLD_INSTRUMENT_SHA256="$realworld_instrument_digest" \
  --iidfile "$realworld_evidence_dir/image-id" \
  eval/fixtures/realworld-author-ui
python - "$realworld_evidence_dir" "$realworld_instrument_digest" "$realworld_head" <<'PY'
import json
from pathlib import Path
import sys

evidence_dir = Path(sys.argv[1])
instrument_digest = sys.argv[2]
head = sys.argv[3]
receipt = {
    "build_command": [
        "docker", "build", "--build-arg",
        f"REALWORLD_INSTRUMENT_SHA256={instrument_digest}",
        "--iidfile", str(evidence_dir / "image-id"),
        "eval/fixtures/realworld-author-ui",
    ],
    "instrument_sha256": instrument_digest,
    "image_id": (evidence_dir / "image-id").read_text().strip(),
    "git_commit": head,
}
(evidence_dir / "build-command.json").write_text(
    json.dumps(receipt, indent=2) + "\n"
)
PY
python eval/fixtures/realworld-author-ui/qualify.py \
  --image "$(cat "$realworld_evidence_dir/image-id")" \
  --git-commit "$realworld_head" \
  --output "$realworld_evidence_dir/qualification"
```

Expected: JSON reports `"qualified": true`; nineteen HTML controls and two
operational controls match exactly, the supplied commit equals `HEAD`, the
image label equals the computed instrument digest, all hashed instrument paths
are clean, and `build-command.json` records the exact Docker argv, digest,
immutable image ID and head commit used for the run.

- [ ] **Step 5: Inspect representative visual evidence**

Open and inspect at minimum these PNGs: explicit author/non-author, two-button author, transparent non-author, partial occlusion, pointer-disabled button, fully occluded author, hard-coded Alice in both crossed fixture pairs, broken article and mixed evaluability. Record any visual/structured discrepancy as a failed qualification and fix the root cause before continuing.

- [ ] **Step 6: Re-run after any visual or structured correction**

If inspection finds a discrepancy, fix it, commit the fix, rebuild the image
and repeat the complete custody-bearing run. Never relabel an unexpected
outcome to make qualification pass.

- [ ] **Step 7: Run focused regression checks**

Run:

```bash
python -m pytest tests/test_realworld_author_ui_executor.py -q
python -m compileall -q eval/realworld_author_ui_executor.py eval/fixtures/realworld-author-ui/qualify.py
node --check eval/fixtures/realworld-author-ui/runner.cjs
git diff --check
```

Expected: all pass.

### Task 5: Add supported CI qualification

**Files:**
- Create: `.github/workflows/realworld-author-ui-oracle-qualification.yml`

- [ ] **Step 1: Add the path-scoped workflow**

Mirror the established qualification workflow structure. Trigger on `workflow_dispatch` and pull requests touching the executor, fixture directory, focused test or workflow. Use `ubuntu-24.04`, Python `3.12`, `contents: read`, a 20-minute job timeout and `persist-credentials:false`.

- [ ] **Step 2: Run static/focused checks before the Docker build**

Install the repository's locked bundle and use its interpreter:

```bash
python scripts/dependency_bundle.py
dependency-bundle/runtime/bin/python -m pytest tests/test_realworld_author_ui_executor.py -q
dependency-bundle/runtime/bin/python -m compileall -q eval/realworld_author_ui_executor.py eval/fixtures/realworld-author-ui/qualify.py
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

Record source URL/revision/SHA, exact head commit, image ID, qualification/report
hashes, artifact digest, control denominator and outcome table, screenshot
hashes and the browser-sandbox flag. Report the denominators separately as 8/8
passing references, 7/7 detected target mutants, 4/4 expected not-evaluable
controls, 2/2 operational controls and 76/76 expected screenshots. The four
fixed screenshot filenames for every HTML control are
`article-alice-author.png`, `article-alice-non-author.png`,
`article-bob-author.png` and `article-bob-non-author.png`. Describe the two
operational controls as diagnostic checks for interface and browser failure
classification; do not count them as scientific target controls or as evidence
of target sensitivity. State explicitly:

- the oracle produced the expected outcomes for the enumerated nineteen HTML
  controls and two operational controls under the pinned environment;
- it does not admit RealWorld into the experiment;
- it is not a provider-produced result and does not add evidence for H1/H2;
- TodoMVC remains the only project with collected E2E experimental outputs until a prospective RealWorld A/B/C collection is frozen and run;
- the authored matrix provides no general estimate of sensitivity, specificity,
  completeness, smell causality or browser-escape safety;
- Chromium sandbox is disabled inside the constrained Docker boundary.

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
sets and reasons, then derive its own category; this deliberate cross-check is
not shared policy code. Reject generic factories or strategy hierarchies: there is
one fixed oracle and one fixed fixture policy.

- [ ] **Step 4: Check scientific scope and staleness**

Search changed docs and code for accidental claims of admission, project
generalization, H1/H2 confirmation or “two E2E projects” before prospective
collection. Ensure all denominators say nineteen HTML controls plus two
operational controls and that source/runtime/hash values agree across workflow
artifact and documentation.

- [ ] **Step 5: Request final code review and update the draft PR**

Use `superpowers:requesting-code-review`, fix any verified blocking findings,
rerun affected checks, and update PR #77 title/body around the final
implementation. Leave a green, reviewable PR ready for the task owner. Merge
only when explicit authorization is present in the implementing task's own
context.
