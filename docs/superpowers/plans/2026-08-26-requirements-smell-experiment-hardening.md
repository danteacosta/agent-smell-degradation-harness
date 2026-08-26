# Requirements-smell experiment hardening Implementation Plan

> For agentic workers: use the subagent-driven-development or executing-plans skill to implement this plan task by task. Steps use checkbox syntax for tracking.

Goal: Correct the known requirements-smell detector and artifact defects, add honest uncertainty/stability reporting, and produce a verified five-repeat offline discovery bundle ready for later live-model evaluation.

Architecture: Keep the verifier, runner, and materializer as separate owners. Add a small uncertainty module for Wilson intervals, deduplicate repeated offline rows in the verifier using the key (intent_id, variant, task_family), and expose deterministic-repeat stability separately from efficacy. Normalize generated source at the materialization boundary and retain provider/configuration identity as non-secret hashes.

Tech stack: Python 3.11+, pytest, JSON/JSONL experiment artifacts, existing discovery runner/verifier, difflib, statistics.NormalDist, and GitHub Actions.

---

## File map

- Modify tests/test_discovery_verifier.py: detector, interval, deduplication, and stability behavior tests.
- Modify tests/test_discovery.py: five-repeat bundle counts, run metadata, and newline/diff artifact tests.
- Modify tests/test_live_agent.py: prompt-hash metadata contract.
- Modify tests/test_episode_identity.py: full configuration hash stability contract if the identifier implementation changes.
- Create eval/uncertainty.py: pure Wilson interval helpers and binary/paired interval assembly.
- Modify eval/discovery_verifier.py: deduplicate repeated rows, compute interval output, report raw/unique counts and stability, and clarify the verification README.
- Modify eval/discovery.py: normalize generated source and diff inputs, add deterministic-repeat metadata, and export configuration identity.
- Modify eval/runner.py: carry non-secret prompt-hash metadata into episode and provider-run exports.
- Modify agents/live.py: record a SHA-256 hash of the exact prompt bytes without exporting prompt content.
- Modify eval/identity.py: retain canonical configuration hashing while avoiding secrets and making the identifier collision-resistant.
- Modify README.md and/or the experiment report source identified by the repository: explain the 48-vs-24 denominator, five deterministic repeats, interval unit, and trusted_fixture limitation.
- Create tasks/todo.md: track this implementation and verification run.
- Update tasks/lessons.md only if a new durable lesson is discovered during execution; do not create unrelated task history.

## Task 1: Add failing regression tests for detector and artifact boundaries

Files:
- Modify tests/test_discovery_verifier.py
- Modify tests/test_discovery.py

- [ ] Step 1: Add the detector regression test.

Add a test that calls derive_observable_signals with the requirement
"The system shall consider anticipated user requests." and asserts that
incomplete_completeness_scope is present. Add the clean counterpart with
"both anticipated and unanticipated" and assert that signal is absent. Use the
existing feature fixture style; do not test private implementation details.

- [ ] Step 2: Run the detector test and verify the expected failure.

Run:

    python -m pytest -q tests/test_discovery_verifier.py -k completeness_scope

Expected: the smelly-case assertion fails because the current unbounded all
match can be satisfied by the all suffix in shall.

- [ ] Step 3: Add artifact-boundary tests.

Extend the discovery test to run one offline case bundle, assert every generated
Python file ends with exactly one LF newline, and inspect one comparison file to
assert the fenced diff contains distinct minus and plus source lines rather than
a concatenated source boundary.

- [ ] Step 4: Add interval and repeated-row contract tests.

In tests/test_discovery_verifier.py, add a small labeled matrix with known
TP=2, FP=0, TN=2, FN=0 and assert interval objects contain successes, trials,
method wilson, confidence 0.95, and bounds. Add five identical rows per unique
(intent_id, variant, task_family), including replication_id values 0 through 4,
and assert the helper used by verify_bundle returns one unique row per key,
detects the complete replication set, and reports agreement. Add a
missing-replication and duplicate-replication case that must report instability
rather than passing silently.

- [ ] Step 5: Run the new focused tests and verify only the intended failures.

Run:

    python -m pytest -q tests/test_discovery_verifier.py tests/test_discovery.py

Expected: the detector regression and any not-yet-implemented interval or
deduplication assertions fail; unrelated existing tests remain green.

- [ ] Step 6: Commit the red tests.

    git add tests/test_discovery_verifier.py tests/test_discovery.py
    git commit -m "test: specify hardened discovery measurements"

## Task 2: Implement detector fix and source/diff normalization

Files:
- Modify eval/discovery_verifier.py
- Modify eval/discovery.py

- [ ] Step 1: Fix the minimal detector rule.

Change the completeness exception from an unbounded alternation to a
word-bounded expression such as r"\b(?:unanticipated|both|all)\b", preserving
the current rule code, weight, message, and checkpoint.

- [ ] Step 2: Add one source normalization helper at the materialization boundary.

Normalize CRLF/CR to LF, remove trailing blank lines, and append exactly one
final LF. Apply it to source_code before writing generated files and before
feeding splitlines(keepends=True) to difflib.unified_diff. Do not mutate the
episode artifact or change internal source content beyond line-ending and
trailing-blank normalization.

- [ ] Step 3: Run focused tests to verify green.

    python -m pytest -q tests/test_discovery_verifier.py -k completeness_scope
    python -m pytest -q tests/test_discovery.py -k artifact

Expected: both detector and newline/diff tests pass.

- [ ] Step 4: Commit the minimal correctness fixes.

    git add eval/discovery_verifier.py eval/discovery.py
    git commit -m "fix: harden discovery signal and diff materialization"

## Task 3: Add uncertainty and repeated-pipeline accounting

Files:
- Create eval/uncertainty.py
- Modify eval/discovery_verifier.py
- Modify tests/test_discovery_verifier.py

- [ ] Step 1: Implement pure Wilson interval helpers.

Create wilson_interval(successes: int, trials: int, confidence: float = 0.95)
using statistics.NormalDist().inv_cdf; validate non-negative counts and
successes <= trials. Return a JSON-ready object with estimate, successes,
trials, confidence, method, lower, and upper. Return None bounds and status
inconclusive when trials == 0.

- [ ] Step 2: Implement unique-row and stability helpers.

In discovery_verifier.py, group labeled rows by the exact analysis key
(intent_id, variant, task_family) and separately index each group by
replication_id. Select the row from replication 0 as representative when it is
present, otherwise the first stable row. Require the observed replication IDs
to equal the expected set from run.json; detect duplicate rows for the same
analysis key and replication ID. Compare all available repetitions on
risk_score, decision, and label; report key_count, expected_replications,
observed_replications, missing_replications, duplicate_replications,
unstable_key_count, and all_repetitions_agree. Do not silently discard rows.

- [ ] Step 3: Add interval output to efficacy metrics.

Compute Wilson intervals for recall (TP / positives), precision (TP / alerts),
specificity (TN / negatives), false-alert rate (FP / negatives), and paired
discrimination (wins / complete pairs). Keep ties as non-wins. Label the
interval block with unit unique_behavior_case_or_pair and interpretation
descriptive_until_independent_replications.

- [ ] Step 4: Make verify_bundle use the correct analysis unit.

Read run.json when present, derive expected_episode_count as
case_count × 2 × task_family_count × replications, and validate the observed
episode count against it. Preserve all raw decisions and labels, but pass the
unique representative rows to primary efficacy metrics. Add raw_eligible_count,
unique_eligible_count, non_behavior_decision_count, and the stability block. For
a one-repetition bundle, values remain unchanged; for v7, efficacy denominator
is 24 while raw behavior rows are 120.

- [ ] Step 5: Update verification README text.

State explicitly that total decisions include test_gen, only behavior_codegen
enters the binary efficacy matrix, and repeated offline rows are not independent
samples. Include interval method/unit and the macOS trusted_fixture explanation
from the spec.

- [ ] Step 6: Run the focused measurement tests and commit.

    python -m pytest -q tests/test_discovery_verifier.py
    git add eval/uncertainty.py eval/discovery_verifier.py tests/test_discovery_verifier.py
    git commit -m "feat: report honest discovery uncertainty"

Expected: all focused verifier tests pass.

## Task 4: Record provider/configuration identity without secrets

Files:
- Modify agents/live.py
- Modify eval/identity.py
- Modify eval/discovery.py
- Modify tests/test_live_agent.py
- Modify tests/test_episode_identity.py

- [ ] Step 1: Add a prompt-hash test.

Update the mock transport metadata test to assert prompt_sha256 is a
64-hex-character SHA-256 digest, prompt_template_version is stable, and no
prompt text is present in the metadata. Add assertions that two equivalent
configurations with different key order have the same full digest, that a
changed configuration has a different digest, and that credential-like fields
are rejected or excluded. Keep the existing provider/model/latency/parse-retry
assertions.

- [ ] Step 2: Record the exact prompt hash.

Hash the UTF-8 bytes of the prompt built for the request and include only the
digest plus a stable prompt-template version in generate_with_meta metadata.
Propagate these two fields through runner.py into the episode provider_meta and
the non-secret provider-run extra metadata. The provider-run summary should
retain the stable template version and the set of observed prompt digests,
without storing prompt text, response text, API keys, or generated artifacts.

- [ ] Step 3: Strengthen canonical configuration identity.

Keep sorted-key compact JSON canonicalization and change the derived
configuration identifier to retain the complete SHA-256 digest with a stable
prefix. Update only tests that assert the identifier shape; preserve the
existing identity inputs and episode naming semantics.

- [ ] Step 4: Export discovery run configuration identity and run kind.

Compute one configuration id for the discovery execution and add
configuration_id, replication_kind, independent_replication_claim, and the
replication-aware expected_episode_count to run.json. Set offline values to
deterministic_pipeline_repeat and false; set live values to
live_provider_replication and true only when mode is live.

- [ ] Step 5: Run provider/identity tests and commit.

    python -m pytest -q tests/test_live_agent.py tests/test_episode_identity.py tests/test_provider_run_manifest.py
    git add agents/live.py eval/identity.py eval/discovery.py tests/test_live_agent.py tests/test_episode_identity.py
    git commit -m "feat: record reproducible non-secret run identity"

## Task 5: Add the v7 run, documentation, and repository task tracking

Files:
- Modify tests/test_discovery.py
- Modify README.md and/or the current experiment report source
- Create tasks/todo.md

- [ ] Step 1: Add five-repeat assertions.

Extend the discovery integration test to run with replications=5 and assert
episode_count == 240, decision_count == 240, behavior_decision_count == 120,
non_behavior_decision_count == 120, raw_eligible_count == 120, and
unique_eligible_count == 24. Assert run metadata says deterministic pipeline
repeat and no independent claim.

- [ ] Step 2: Update the experiment-facing explanation.

Document the v7 interpretation in the repository's experiment-facing text: the
corrected PEERING completeness signal, the possible ERTMS omission false
negative, 48/24 at one repetition, 240/120/24 at five repeats, Wilson
intervals on unique cases, and why the Mac trusted fixture is not production
sandbox evidence. Keep the proposal/report style and language consistent with
the existing repository document.

- [ ] Step 3: Create task tracking with a verification checkpoint.

Create tasks/todo.md with the approved plan, completed implementation steps, the
bundle run id, test commands, and remaining live-model work. Do not add personal
notes or unrelated tasks.

- [ ] Step 4: Run the v7 offline bundle.

    python -m eval.discovery --mode offline --replications 5 --run-id discovery-20260826-v7
    python -m eval.discovery --verify-artifacts --bundle-dir artifacts/experiments/runs/discovery-20260826-v7

Expected: artifact verification returns status ok; the run has 240 episodes, all
generated-code files end with LF, and verification metrics use 24 unique
eligible behavior cases.

- [ ] Step 5: Inspect the generated evidence.

Inspect run.json, metrics.json, verification/metrics.json, one generated file,
one comparison, and verification/README.md. Confirm no labels in
verification/decisions.jsonl, no prompts/secrets in provider metadata, and no
malformed diff boundaries.

- [ ] Step 6: Run repository verification.

Use the supported Python 3.11/3.12 environment for:

    python -m pytest -q
    python -m eval.discovery_verifier --bundle-dir artifacts/experiments/runs/discovery-20260826-v7
    make wedge-check

If the workstation interpreter is older or lacks the ARP dependency, record that
limitation and rely on the matching CI gate rather than claiming a local full
suite pass.

- [ ] Step 7: Review the diff and commit the bundle/documentation.

    git status --short
    git diff --check
    git add README.md tasks/todo.md tests/test_discovery.py artifacts/experiments/runs/discovery-20260826-v7
    git commit -m "chore: rerun hardened discovery experiment"

## Definition of done

- Detector regression is covered by a test that failed before the fix.
- Generated code and comparison diffs are newline-safe and auditable.
- Primary efficacy metrics use unique behavior cases, with explicit raw counts
  and Wilson 95% intervals.
- Deterministic repeats are labeled as pipeline stability, not independent model
  evidence.
- v7 artifact verification, focused tests, full supported CI tests, and wedge
  checks pass.
- The remaining gap is explicit: real providers, two configurations, genuine
  repeated model calls, and Linux/CI sandbox execution still require the key
  and a later run.
