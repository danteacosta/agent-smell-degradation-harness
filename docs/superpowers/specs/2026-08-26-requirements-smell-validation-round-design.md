# Requirements-smell validation round v8 design

## Context

The v7 discovery bundle validated the local pipeline and produced a visual degradation demonstration, but it used a small controlled corpus, a deterministic stub, and source-derived labels. The next round must execute a stronger screening experiment without presenting screening evidence as confirmatory evidence.

## Objective

Run a reproducible natural-requirement screening round that:

1. uses public requirements rather than only controlled mutations;
2. includes at least ten positive cases and ten clean controls for each supported smell family;
3. keeps complete projects in exactly one split;
4. evaluates a frozen, transparent baseline without reading source markers;
5. probes sensitivity to controlled paraphrases while excluding unvalidated paraphrases from primary metrics;
6. records the two real-model slots, agent conditions, provenance, and blocking conditions;
7. produces artifacts that can be audited and extended with independent expert labels.

This round is a screening execution, not a claim that the detector or agent is effective on new requirements.

## Scope and evidence boundary

The ARTA public evaluation workbook supplies natural requirement text and dataset markers. Those markers are source labels from the published dataset, not independent annotations for this thesis. They may be used for a private local source-label screening run, but the primary confirmatory result remains blocked until at least two independent annotators label a blinded duplicate-aware sample.

The repository's corpus policy currently rejects ARTA for redistribution because the landing page does not establish rights for the underlying requirement excerpts or their transformations. Every case therefore carries a license gate (`license_status`, `redistribution_allowed`, `derivative_use_allowed`, and `permission_record`). The executable permits `private_use_only` input only when the caller opts into private execution; committed GitHub artifacts contain hashes and source coordinates, not requirement excerpts.

The six supported families are the families with at least ten single-marker positives and enough clean controls in the downloaded ARTA source: subjective language, ambiguous adjective/adverb, non-verifiable term, vague pronoun, uncertain verb, and polysemy. Comparative, negative, superlative, and loophole are recorded as underrepresented in this source and are not silently treated as supported.

No live model request is made without an explicit provider configuration and API credential. The artifact records two model slots as `not_run` when credentials are absent. Any agent-with-alert comparison based on the v7 deterministic behavior fixture is labeled `simulation_only`; it is not a model evaluation.

The primary estimand is named `agreement_with_arta_source_labels`. It must never be described as smell validity, detector efficacy, generalization, or agent effectiveness. A `smelly` case is a single-marker source-positive for the target family; a `clean_control` is a requirement with no marker in any supported or unsupported ARTA smell column. Multi-marker records are excluded from the primary selected corpus rather than assigned to an arbitrary family. Missing or malformed source labels fail validation.

## Acceptance contract

Given a versioned JSONL corpus with source provenance, source-label type, and project IDs, when the round runner executes in offline screening mode, then it must:

- reject duplicate case IDs, missing required provenance, missing project IDs, or missing source-label typing;
- report at least ten source-labeled positives and ten clean controls per supported family;
- write a deterministic project-disjoint split manifest and fail if a project appears in more than one split;
- run the baseline using requirement text only, with predictions unchanged if source marker fields are mutated;
- keep paraphrase probes out of the primary confusion matrices unless they carry independent labels;
- write a readiness report that distinguishes screening completion from confirmatory readiness;
- preserve model, prompt, annotation, and execution status without fabricating values.

## Data flow

```text
ARTA XLSX/JSON source
        |
        v
selected natural JSONL corpus -- strict schema --> project-disjoint splits
        |                                            |
        +--> frozen text-only baseline ----------------+--> primary screening metrics
        |
        +--> controlled paraphrase probe -------------> secondary robustness signal
        |
        +--> v7 behavior fixture ---------------------> simulation-only agent conditions
        |
        +--> readiness manifest ----------------------> expert/model blockers
```

## Components

### Corpus manifest

`data/pairs/discovery-natural-v8/manifest.json` records the ARTA repository commit, downloaded source file hash, selected families, quota, split policy, annotation state, licensing gate, and real-model slots. The checked-in selection manifest repeats case hashes and source coordinates without redistributing text. A local private JSONL corpus is required for the actual baseline execution until reuse permission is documented.

### Baseline

`baselines/natural_smell.py` contains a versioned lexicon baseline. It returns one binary prediction per family from normalized requirement text. The lexicon is intentionally simple and frozen for this round; it is a comparator, not the proposed agent. It must never inspect `source_smell_markers` or `source_label`.

### Runner

`eval/validation_round.py` validates the corpus, builds the project split, computes source-label screening metrics on the held-out test projects, generates a clearly marked paraphrase probe, summarizes the v7 simulation conditions, and writes a complete artifact bundle. It does not call external model providers in offline mode.

### Annotation handoff

The runner records `expert_annotation_status=pending` and the planned duplicate fraction/annotator count from `tasks/annotation_rubric.json`. A future annotation import can replace source labels for primary metrics without changing the split or baseline code.

## Splitting policy

The split is by complete project, never by individual requirement. The deterministic assignment is train/calibration/test. The held-out test is used for the screening report; source markers are not used by the baseline. A future confirmatory run must calibrate thresholds only on train/calibration and keep test projects untouched.

## Metrics and interpretation

For each supported family, the artifact reports confusion counts, precision, recall, specificity, F1, and the number of cases in the denominator. Point estimates are descriptive agreement measures. The runner also writes naive binomial Wilson intervals; these intervals do not compensate for source-label dependence, project/document clustering, selection design, or the absence of independent annotation. The test split reports per-family denominators and marks a family non-evaluable if its held-out denominator is too small.

Paraphrase results are a robustness probe only because the deterministic rewrite does not have independent labels. Agent-condition results are a deterministic control on the v7 fixture only. Neither is included in the natural source-label baseline’s primary confusion matrix.

## Failure modes

- insufficient family quota: fail the run before reporting metrics;
- project overlap: fail the run before reporting test metrics;
- missing source provenance or licensing fields: fail corpus validation;
- no redistribution permission: allow only explicitly private execution and redact text from committed artifacts;
- no credentials/provider config: keep real-model slots `not_run` and mark confirmatory readiness blocked;
- missing expert labels: keep source-label screening status separate from confirmatory status;
- underrepresented smell family: list it as pending instead of padding or duplicating cases.

## Non-goals

- claiming the ARTA markers are thesis ground truth;
- claiming that the baseline is an LLM agent;
- claiming production latency, cost, sandboxing, or generalization;
- treating the v7 stub or simulation control as a real-provider evaluation;
- silently expanding the supported taxonomy with duplicated or synthetic examples.
