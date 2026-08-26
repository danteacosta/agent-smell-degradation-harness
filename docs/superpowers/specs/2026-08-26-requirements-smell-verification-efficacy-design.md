# Requirements-smell verification efficacy design

**Status:** approved working design for the discovery track; non-confirmatory

## Goal

Add a second phase after the clean-versus-smelly demonstration. The phase must
measure whether a verifier can flag an episode with a requirement smell before
the generated artifact is evaluated, while an independent behavioral oracle
confirms the label only after the decision. The result must report operational
effectiveness rather than a single pass rate.

## Boundary and terminology

The experiment has two planes:

1. **Observable plane:** T0 input receipt, T1 interpretation, T2 plan, and T3
   execution evidence. The verifier can consume only this plane plus the
   requirement text and task family. It cannot read `variant`, `smell`,
   `oracle_passed`, hidden tests, generated code, or terminal evaluation.
2. **Evaluation plane:** the generated artifact and hidden behavioral tests are
   used after the verifier decision to produce a binary label: target semantic
   degradation or no target degradation. This plane is never a verifier input.

The current corpus is discovery evidence. A positive result means “promising on
this versioned set of source-traceable cases”; it is not a universal claim
about all requirements, agents, models, or domains.

## Components and data flow

```text
discovery run
  -> compact episodes + portable observable traces
  -> oracle-free verifier score/decision
  -> independent behavior report label
  -> efficacy report (confusion matrix, pairwise, timing, cost, strata)
```

The primary harness owns the corpus, generation, behavioral sandbox, feature
extraction, verifier policy, metrics, and tracked artifact bundle. The
`agent-reliability-protocol` repository remains the lifecycle/interchange
boundary: ARP identity, checkpoint order, timestamps, source hashes, and
evidence references. No thesis-specific outcome is added to ARP core.

The bundle must contain `observable-traces/` with only pre-final records. The
episode record may retain terminal results for audit, but the verifier receives
an allowlisted projection. If an observable trace contains a terminal key, the
verifier fails closed instead of silently continuing.

## Verifier contract

`eval.discovery_verifier` exposes a deterministic discovery policy with a
versioned rule pack. It derives transparent signals from:

- measurable or bounded language indicators from the requirement text, such as
  vague threshold words, missing response outcomes, unbounded cardinality, or
  missing conditions in a conditional action;
- T1/T2/T3 fields already allowed by the deployable feature plane; and
- operational timestamps and provider metadata for latency/cost reporting,
  never for the semantic label.

The policy produces a risk score in `[0, 1]` and an action: `approve`, `warn`,
or `block`. The threshold is frozen in the run manifest and is not fitted on
the evaluated terminal labels in the default discovery command. A future
confirmatory run may fit a threshold on calibration data and evaluate it once
on a grouped holdout.

## Metrics and interpretation

For eligible behavior episodes, the report includes:

- true positives, false positives, true negatives, and false negatives;
- recall/warning coverage, precision, F1, accuracy, and balanced accuracy;
- false-alert rate on clean episodes and the alert rate overall;
- paired discrimination: how often the smelly variant scores higher than its
  clean counterpart, plus the mean paired score delta;
- first-signal checkpoint and lead time before artifact completion when valid
  timestamps are available;
- verifier runtime, provider latency, reported cost, and alerts per detected
  failure;
- coverage of portable observable traces and count of rejected leakage cases;
- stratified results by project, smell family, task family, and checkpoint.

The report marks the pilot `promising` only when the frozen rule pack has no
leakage, all eligible cases have labels, recall is at least 0.80, clean
false-alert rate is at most 0.20, and paired discrimination is at least 0.80.
Otherwise it reports `inconclusive` or `fail` with the failed criteria. These
are development gates for deciding what to investigate next, not population
confidence intervals.

## Failure handling and negative controls

- Missing or unsafe observable traces are ineligible and are counted; they are
  not converted to a passing verifier decision.
- `oracle_passed`, hidden-test names/results, artifact fields, smell labels,
  and variant labels are prohibited from the verifier projection.
- A clean episode that receives `warn`/`block` is a false alert; a smelly
  episode that receives `approve` is a miss.
- The report includes a deterministic repeated-run hash check and the existing
  replay negative-control benchmark remains separate. No post-hoc score is
  allowed to alter the decision.

## Tests and acceptance criteria

Given a portable pre-final trace and an allowlisted episode projection, when
the verifier runs, then it produces a deterministic score and decision without
terminal fields.

Given a trace containing a terminal field, when the verifier runs, then it
fails closed and reports a leakage rejection.

Given paired clean/smelly episodes with independent behavioral labels, when
the efficacy evaluator runs, then it reports a confusion matrix, paired
discrimination, timing/cost fields, and per-project/per-smell strata.

Given the tracked discovery run, when the verification command runs, then it
creates `verification/decisions.jsonl`, `verification/metrics.json`, and
`verification/README.md` inside the versioned experiment bundle.

The implementation must preserve the existing core gate, legacy `codegen` and
`test_gen` adapters, and confirmatory ARP/feature-plane leakage checks.
