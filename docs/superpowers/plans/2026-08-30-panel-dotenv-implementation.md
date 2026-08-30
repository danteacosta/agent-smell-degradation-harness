# Panel `.env` Loading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load private panel credentials from a repository-root `.env` without a shell export step, while preserving inherited-environment precedence and secret-free failures.

**Architecture:** Add a focused `label_plane.private_env` module that parses the complete file into an intermediate mapping before mutating `os.environ`. The panel CLI invokes it once before loading runtime configuration; the existing panel runner, adapters, requests, and output schemas remain unchanged.

**Tech Stack:** Python 3.11 standard library, `unittest`/`pytest`, existing panel CLI and runtime.

---

### Task 1: Private environment parser

**Files:**
- Create: `label_plane/private_env.py`
- Create: `tests/test_private_env.py`

- [ ] **Step 1: Add the public API skeleton**

Create `PrivateEnvError(ValueError)` and a no-op `load_private_env(...)` so
subsequent tests fail on behavior rather than collection.

- [ ] **Step 2: Add and run the basic-assignment red tests**

Cover an absent file, blank/full-comment lines, horizontal whitespace,
`KEY=VALUE`, exact `export KEY=VALUE`, empty values, and inherited-value
precedence including empty strings.

Run: `python -m pytest tests/test_private_env.py -q`
Expected: FAIL because the loader is still a no-op.

- [ ] **Step 3: Implement basic assignments and confirm green**

Parse into an intermediate mapping and apply with `setdefault` only after the
whole file is valid.

- [ ] **Step 4: Add and run grammar-edge red tests**

Name cases for whitespace-before-`#` comments versus embedded `#`, quoted
`#`, single/double quotes, escaped matching quotes/backslashes, exact `export`
token boundaries, invalid names, duplicate keys, unsupported escapes, and
trailing garbage after quoted values.

Run: `python -m pytest tests/test_private_env.py -q`
Expected: FAIL on the new grammar cases.

- [ ] **Step 5: Implement the approved grammar and confirm green**

Expose:

```python
def load_private_env(path: str | Path, *, environ: MutableMapping[str, str] | None = None) -> None:
    """Atomically load a narrow, secret-safe dotenv grammar."""
```

Match names with `^[A-Z][A-Z0-9_]*$`, reject duplicates and unsupported
syntax, and keep diagnostics limited to safe names/line numbers.

- [ ] **Step 6: Add and run filesystem/atomicity red tests**

Cover invalid UTF-8, directories, simulated permission/read failures, and a
late malformed line after a valid assignment. Assert no environment mutation
and no raw path, line, or sentinel value in exception text.

- [ ] **Step 7: Translate filesystem failures safely and confirm green**

Read UTF-8 only, require a regular file when present, and translate read,
decode, and path-type failures into generic `PrivateEnvError` messages without
including the path or source bytes.

- [ ] **Step 8: Run the focused tests**

Run: `python -m pytest tests/test_private_env.py -q`
Expected: PASS.

- [ ] **Step 9: Commit parser and tests**

```bash
git add label_plane/private_env.py tests/test_private_env.py
git commit -m "feat: load private panel environment"
```

### Task 2: Panel CLI integration

**Files:**
- Modify: `scripts/run_llm_panel.py`
- Create: `tests/test_run_llm_panel.py`

- [ ] **Step 1: Write failing CLI behavior tests**

Invoke `main()` with a temporary repository root and private task/config paths.
Patch the CLI's `PanelRunner` constructor with a factory that returns the real
`PanelRunner` configured with an injected recording `fake` adapter. This keeps
real judge resolution, request construction, response normalization, output
JSONL, manifest generation, and stdout while avoiding network access. Prove
`.env` is loaded before judge resolution, inherited empty values are not
overwritten, provider prompts/requests and output schemas are unchanged, and
malformed/unreadable `.env` exits with zero adapter calls. Assert stdout/stderr
never contains a sentinel secret, raw malformed line, or private path.

- [ ] **Step 2: Run tests and confirm `.env` is not loaded yet**

Run: `python -m pytest tests/test_run_llm_panel.py -q`
Expected: FAIL with the existing missing-model environment error before the
recording adapter is called.

- [ ] **Step 3: Load the repository `.env` before configuration**

Import `load_private_env` and call:

```python
load_private_env(REPOSITORY_ROOT / ".env")
```

inside the CLI error boundary, before `PanelRunConfig.from_json`.

- [ ] **Step 4: Run CLI and runtime regression tests**

Run: `python -m pytest tests/test_run_llm_panel.py tests/test_private_env.py tests/test_panel_runtime.py -q`
Expected: PASS.

- [ ] **Step 5: Commit CLI integration**

```bash
git add scripts/run_llm_panel.py tests/test_run_llm_panel.py
git commit -m "feat: load panel credentials from dotenv"
```

### Task 3: Verification and bounded real smoke

**Files:**
- Verify only: `.env` (ignored, values never read into output)
- Verify only: `/private/tmp/llm-panel-20260830-smoke-v14.*`

- [ ] **Step 1: Run focused static and test verification**

Run: `python -m compileall -q label_plane scripts tests`

Run: `python -m pytest tests/test_private_env.py tests/test_run_llm_panel.py tests/test_panel_runtime.py -q`

Expected: both commands succeed.

- [ ] **Step 2: Verify private configuration without exposing values**

Check only that `.env` is Git-ignored, mode `0600`, and contains the two required variable names with non-empty values. Do not print values or file contents.

- [ ] **Step 3: Run a no-provider private preflight**

Load the real repository `.env`, private config, and private tasks in a bounded
Python preflight that invokes configuration/task selection and judge resolution
but not adapter completion. Emit only judge IDs, selected counts, and an
`ok`/error classification; never emit prompts, endpoints, models, or values.

- [ ] **Step 4: Execute the authorized smoke run**

Run `scripts/run_llm_panel.py` with run ID `llm-panel-20260830-smoke-v14`, the supplied two-judge private task/config files, `--limit-per-judge 10`, and only the three authorized `/private/tmp` outputs.

- [ ] **Step 5: Verify metadata-only outputs**

Summarize per judge: selected tasks, valid responses, configuration/provider/parsing errors, attempts, latency, input/cached/output/reasoning tokens when reported, and cost. Never print raw prompts, responses, or keys.

- [ ] **Step 6: Review security and cleanliness**

Confirm `.env` is ignored, no secret entered tracked files/logs/manifests, no unrelated changes exist, and no Google Docs update occurred unless the smoke completed and is verifiable.
