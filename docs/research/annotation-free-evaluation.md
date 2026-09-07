# Evaluation while human annotation is unavailable

Status: 2026-09-06. Provider-backed controls completed: OpenAI 18/36 and
DeepSeek 25/36 construction-oracle matches; both missed all deletion controls.
See [results](evaluator-control-results.md) and the
[temporal protocol](temporal-warning-protocol.md). Human calibration remains
pending. H1, H2, the primary
missing-condition family and the no-compaction primary condition are unchanged.

A subsequent [prompt comparison and schema smoke](judge-prompt-comparison-results.md)
found a field/value ambiguity in the first evidence prompt. Evidence v2 passed
16/16 small-smoke checks, with four deletions detected by each provider. The
original v1 comparison was interrupted by unverified call usage and is not complete;
neither configuration has human calibration or natural-artifact qualification.

The later [expanded v2 comparison](judge-v2-expanded-results.md) completed all
384 calls. Each provider matched 96/96 construction oracles with v2, including
24/24 deletions and no false alarms on 48 complete/paraphrased occurrences.
The historical prompt detected only 2/24 and 0/24 deletions, respectively.
This completed study does not reconcile the earlier ambiguous call or establish
natural-artifact validity.

## Thesis: distinguish three evidence levels

1. **Instrument correctness:** executable contracts, lineage, isolation and
   synthetic controls can expose bugs without new human labels.
2. **Exploratory behavior:** report per-configuration machine judgments,
   disagreement, abstention, failures and sensitivity. Agreement is not truth.
3. **Confirmatory semantic validity:** the registered blinded human labels and
   adjudication remain required. No automatic conversion from levels 1 or 2.

Suggested thesis text: "While independent annotation was unavailable, we
evaluated instrument correctness and evaluator failure modes using constructed
controls with explicit expected relations. These controls establish neither
natural-language label validity nor external effectiveness. Results on natural
requirements remain exploratory. The confirmatory hypotheses retain their
registered independent-outcome and project-held-out evaluation requirements."

## Executable controls

`label_plane/judge_controls.py` creates three original toy scenarios with four
operations each: literal coverage, line reordering, deletion, and explicit
opposite behavior. Exactly six cases cover the reference and six do not.
The oracle is construction-based, not human ground truth. These cases do not
enter the confirmatory corpus, feature extraction, model selection for H2,
calibration or project holdouts. They are public regression fixtures, not a
secret benchmark or an estimate of natural requirement prevalence.

The current judge status vocabulary lacks `contradicted`; in this control suite
an explicit opposite behavior must be classified as `omitted` (the required
behavior is not operationalized) with a non-clean label. This mapping is a
diagnostic convention, not an extension of the smell taxonomy. Report these
cases separately; do not confuse contradiction with the primary manipulation.

```sh
python scripts/judge_controls.py requests
python scripts/judge_controls.py manifest
python scripts/judge_controls.py score --responses /approved/private/control-responses.jsonl --configuration CONFIGURATION_SHA256 --repetitions 3
```

`requests` emits only validated judge inputs. `manifest` includes the expected
answers and must NEVER be given to the judge. The caller uses the existing
`build_judge_prompt` and authorized provider adapter for each request. This CLI
does not make network calls or spend money. The separate
`python -m eval.live_judge_controls --output-dir /approved/private/new-run`
command performs a no-network preflight. Add `--live --env-file PRIVATE_ENV`
only for an authorized run. It reuses the existing cost and provider gates,
disables hidden SDK retries, and refuses repository output or an existing run
directory. Its 72-call subset conservatively reserves the full US$0.988200
pre-pilot envelope. Private configuration, usage and response records stay
outside version control; no supplied hash proves vendor-weight immutability.

Before collecting responses, freeze a configuration record containing exact
provider/model version, prompt, rubric, decoding settings and source revision;
compute its canonical JSON SHA-256 with `fingerprint`. Keep that record with the
private response ledger. A supplied hash binds records by identifier but does
not itself verify the operator's configuration or prove model immutability.
Each JSONL response has exactly these fields:

```json
{
  "pack_sha256": "COPY_FROM_MANIFEST",
  "configuration_sha256": "SHA256_OF_FROZEN_CONFIGURATION",
  "replication_id": 0,
  "occurrence_id": "COPY_FROM_REQUEST",
  "raw_response": "{\"label\":\"clean\",\"status\":\"covered\"}"
}
```

Use `null` for failed calls and retain detailed errors privately. Repetitions
are zero-indexed. A default comparison of two configurations at three repetitions
requires 72 judge calls, **not an authorization to spend**. Preflight and approve
its actual token envelope before execution. Do not rerun the 120-episode agent
experiment merely to test this evaluator. Do not mix historical responses from
different protocol/configuration hashes.

The report retains planned denominators, missing/invalid calls, abstentions,
false coverage and inconsistent `clean/non-covered` responses. Accuracy here
means correspondence to the toy construction oracle only. It also reports label
and status switches under line reordering, with completed and planned pair
counts. Zero completed pairs yields null stability, not perfect stability.
Always inspect accuracy and stability together: a constant-clean judge has zero
order switches and misses every negative control. Results stay separated by
configuration and operation; no pseudoreplicated confidence intervals are given
for these three templates.

## Next steps while human annotation is unavailable

- The original fixed controls exposed zero deletion sensitivity in both historical judge configurations.
  The hard-coded `clean/covered` example is an anchoring risk to test, not a
  demonstrated explanation of the historical label distribution.
- A separately fingerprinted rubric/evidence prompt has now been tested,
  without evaluation examples in the prompt. The corrected v2 contract passed
  a small smoke and the separately frozen 384-call comparison. Quote presence
  verifies grounding only, not entailment. Do not tune on the confirmatory
  holdout or silently overwrite the historical configuration.
- Treat uncertain, inconsistent or failed judgments as review-needed; never
  impute them as clean or drop them from denominators. Repeat sensitivity
  analyses with both pessimistic and optimistic assignments before interpreting
  exploratory contrasts. Bounds do not repair systematic errors in agreed labels.
- Prepare the existing blinded packets, but keep an eventual random audit sample
  separate from a disagreement-enriched troubleshooting queue. Enrichment cannot
  estimate prevalence or general judge accuracy without a sampling correction.
- When humans become available, freeze the calibration design before seeing
  their labels. A researcher-only review may help debug examples but is not two
  independent annotators. Advisor approval is needed for any alternate thesis
  design if independent labels remain permanently unavailable.

## Threats to validity and related work

[Lee et al., NAACL 2025](https://doi.org/10.18653/v1/2025.naacl-long.452)
motivate evaluator sensitivity checks. We do not automatically treat epistemic
hedges as meaning-preserving in requirements: changing obligation strength can
change the requirement itself. The implemented invariant is limited to reordering
independent lines. This is an adaptation, not an EMBER replication.

Additional threats are toy-template simplicity, public fixture contamination,
shared generator/judge biases, prompt anchoring, and construct mismatch between
syntactic checks and semantic condition preservation. Stable machine judgments
and 100% toy performance cannot resolve these threats.

## Product track: review-needed diagnostics, not compliance certification

The near-term product hypothesis is an integrity triage component for engineering
teams operating requirement-to-artifact agents. It can show which constraint lost
an auditable link, the earliest observed checkpoint, missing evidence, estimated
review priority and replay context. A failed evaluator-control suite should flag
the configuration as unqualified for automated semantic decisions; a passing
suite is necessary debugging evidence only, never a guarantee of correctness.

Keep deterministic contract failures distinct from semantic warnings. Default to
advisory review-needed status; do not autonomously rewrite requirements or block
production on an uncalibrated semantic score. Candidate product metrics are
reproducible incident rate, replay completeness, cost and time-to-diagnosis.
Precision, avoided defects and time saved require independently reviewed cases
or user studies. Customer willingness to pay and workflow fit remain unvalidated.
