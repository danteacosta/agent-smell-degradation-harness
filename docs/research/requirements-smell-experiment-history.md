# Requirements-smell experiment history

This document is the chronological ledger for the requirements-smell research
track. It separates three things that must not be conflated:

- a research version or milestone;
- the code commit that produced it;
- the immutable experiment bundle and its interpretation.

Historical results are append-only. A later run may supersede or invalidate an
earlier interpretation, but it must not rewrite the earlier number. Every new
run receives a new `run_id` and a new history entry.

## Status vocabulary

`discovery_only` means that the pipeline produced artifacts, not that a
detector was validated. `descriptive_only` means that a controlled result is
auditable, but its estimate is not a claim about new requirements or a real
agent. `diagnostic_source_label_screening` means that the result agrees with
source markers used for screening; those markers are not independent expert
labels. `blocked_until_external_validation` means that the artifact is useful
for development but cannot support the planned confirmatory claim. `invalid`
means that the execution must not be used as a published result.

## Version ledger

| Version | Exact artifact or milestone | What changed and why | Data and execution | Result and interpretation |
|---|---|---|---|---|
| v3 | [`discovery-20260826-v3`](../../artifacts/experiments/runs/discovery-20260826-v3/) | First tracked discovery pipeline: paired clean/smelly requirements, generated code, hidden tests and provenance. | 12 controlled pairs; 48 episodes; one offline run. | `discovery_only`. No verifier efficacy matrix was available, so this version cannot support recall/precision claims. |
| v4–v5 | Engineering milestones in commits `315d5f8`, `333557e`, `3f9581d`, `a30e268` and `7c46ace` | Added measurement tests, Wilson intervals, replication identity, isolated reruns and deterministic repeat support. These are hardening milestones, not separate promoted result bundles. | No standalone immutable v4/v5 result bundle. | The change was required because a small one-shot result could look stronger than it was and reruns could reuse stale local state. |
| v6 | [`discovery-20260826-v6`](../../artifacts/experiments/runs/discovery-20260826-v6/) | Introduced the verifier efficacy report and the first confusion matrix. | 12 unique behavior cases; 48 decisions; one deterministic run. | Historical matrix `TP=10, FN=2, FP=0, TN=12`; recall `0.8333`; precision `1.0000`; status was historically `promising`. It was superseded by the more conservative v7 interpretation because the denominator was small and there was only one repetition. |
| v7 | [`discovery-20260826-v7`](../../artifacts/experiments/runs/discovery-20260826-v7/) | Hardened the measurement boundary: five deterministic repeats, deduplication by unique behavior case, oracle-separated decisions, leakage checks and uncertainty intervals. | 240 decisions; 120 `test_gen` observations excluded from binary efficacy; 24 unique behavior cases; 12 clean/smelly pairs. | `TP=11, FN=1, FP=0, TN=12`; recall `0.9167` with Wilson 95% CI `[0.6461, 0.9851]`; precision `1.0000` with CI `[0.7412, 1.0000]`; paired discrimination `11/12`; interval status `inconclusive`; `descriptive_only`. The five repeats show pipeline stability, not independent model evidence. |
| v8 | [`discovery-20260826-v8-screening`](../../artifacts/experiments/runs/discovery-20260826-v8-screening/) | Moved from controlled mutation pairs to natural requirements, added project-held-out splitting, a lexical baseline and a contextual linguistic comparator. | 144 source-labelled screening cases across six projects and six smell families; no real model run; expert annotation pending. | On the held-out test strata, the lexical baseline aggregated to `TP=10, FP=2, TN=39, FN=28` (recall `0.2632`, precision `0.8333`). The retrospective contextual comparator aggregated to `TP=27, FP=2, TN=39, FN=11` (recall `0.7105`, precision `0.9310`). Both are descriptive/diagnostic source-label results, not expert-validated efficacy; status `blocked_until_external_validation`. This round exposed why keyword matching is insufficient. |
| v9 | Local intermediate attempt; not a published bundle | Re-ran the v7 protocol after moving terminal timing into a portable sidecar. | Same 240-decision deterministic design as v7/v10. | `invalid` for publication because `episodes.jsonl` still retained absolute machine-specific provenance paths. Its metrics are not part of the evidence history and must not be cited. |
| v10 | [`discovery-20260827-v10-portable-timestamps`](../../artifacts/experiments/runs/discovery-20260827-v10-portable-timestamps/) | Corrected the v9 portability defect. Terminal timestamps are stored in `evaluation-metadata.jsonl` and joined only after the oracle-free verifier decision; tracked episode records no longer depend on the original worktree path. | 240 decisions; five deterministic pipeline repeats; 24 unique behavior cases; 240 portable timing records; 120 labelled behavior rows. | The detector result is unchanged from v7: `TP=11, FN=1, FP=0, TN=12`; recall `0.9167`; precision `1.0000`; paired discrimination `11/12`; interval status `inconclusive`; `descriptive_only`. Lead time is available for 12 observations with mean `0.078 ms`, but this is the local deterministic fixture, not LLM or production latency. |

## What the sequence establishes

The sequence supports three bounded conclusions:

1. The pipeline can generate a visible clean-versus-smelly code degradation
   and verify it with hidden tests in a controlled fixture.
2. A fixed lexical vocabulary is a weak detector on the natural screening
   split. Contextual linguistic signals improve the diagnostic screen, but the
   v8 comparator was designed retrospectively and still lacks independent
   semantic labels.
3. Portable, oracle-separated artifacts are now reproducible at the repository
   level, but no version yet demonstrates generalization of an LLM agent or
   the causal benefit of showing a verifier alert to that agent.

The single false negative in v7/v10 is retained as evidence, not treated as a
minor anomaly. It is concentrated in the incomplete-condition family and
illustrates a limitation of text-only cues: a missing condition may not be
recoverable from the final requirement wording. The zero false-alert count is
also not evidence of production specificity because the clean controls are
small and deliberately balanced.

## Change-control protocol for future versions

Before starting a run:

1. Fetch the remote state and record the exact base commit.
2. Create a new branch/worktree and a new `run_id`; never overwrite a prior
   bundle.
3. Freeze the corpus hash, split, detector/rule-pack version, prompt version,
   provider/model configuration and execution command.

After running:

1. Verify the artifact schema, hashes, leakage boundary, counts and required
   metadata before interpreting any metric.
2. Add the bundle, code change, tests and the corresponding history entry in
   the same commit whenever licensing and privacy gates permit publication.
3. Record denominators, confidence intervals, failed cases, exclusions,
   replication type and the reason for every change from the previous version.
4. Treat missing or machine-specific measurements as unavailable; never fill
   them from an old run or from an absolute local path.

The synchronization check is explicit and must happen before publication:

```bash
git fetch origin
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git diff --check origin/main..HEAD
```

If the working tree contains unrelated user changes, stop and preserve them.
If `origin/main` has advanced, record the new base and integrate through a
reviewable branch/PR rather than silently rebasing an already interpreted
experiment. After an authorized push, fetch again and confirm that the local
commit and its remote counterpart resolve to the same hash. A local commit
that has not been pushed is not described as synchronized or published.

## Current repository state

The v10 changes are recorded locally in commit `7bcf85d` on
`codex/portable-efficacy-timestamps`. At the time of this entry,
`origin/main` remains at `6e0c8ed`; no push has been performed. The main
worktree's pre-existing generated v7 verification changes were preserved and
were not folded into the v10 commit.

Before publishing the ARTA-derived bundle, confirm the permitted use and
redistribution terms. Until that gate is resolved, the v8 source-text
screening remains a development artifact even though its redacted outputs are
tracked.
