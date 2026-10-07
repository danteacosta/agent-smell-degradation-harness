# Claude shared-omission E2Es: complete requirements outperform incomplete requests

With the same 25 frozen requirements and eight projects, suites generated from the complete requirement had a higher mutation-adequacy score than suites generated from the incomplete request in both Claude models. Adding the shown mutant's code to the incomplete request did not produce any confirmed kills under the reference-quiet rule. This is an exploratory cross-provider replication on the same implementations, not an independent confirmatory sample or a test of H2.

| Model | Complete requirement score | Incomplete request score | Incomplete request + mutant code score |
| --- | ---: | ---: | ---: |
| Sonnet 4.6 | 0.400 | 0.050 | 0.000 |
| Opus 4.6 | 0.800 | 0.085 | 0.000 |

These are equal-requirement scores, not pooled percentages of all page pairs. A mutant counts as killed only when the suite is quiet on its correct reference. Unsound and unusable suites remain in the planned denominator. There are two suites per source per requirement; repetitions are not independent requirements.

## Execution and preservation

The first evaluation failed because Docker was inaccessible. Its original packets and public outcomes remain unchanged in [PR #189](https://github.com/danteacosta/agent-smell-degradation-harness/pull/189). Dante then authorized starting Docker and evaluating the saved suites. The new stage copied the frozen prompts, generation outcomes and suites by hash and used the same collector, runner and image. All three authored runner controls qualified before evaluation.

No new model calls occurred in this stage. The original 300 distinct generation attempts produced 148 Sonnet suites and 149 Opus suites; the three generation failures stayed failed. There were no generation retries. Earlier quota continuations preserved attempted slots, and parser/quota amendments did not relabel old failures. The setup/protocol remains in [PR #188](https://github.com/danteacosta/agent-smell-degradation-harness/pull/188), revision `b53eb9e`.

| Model | Planned pairs | Browser reports | Runner-error rows | Generation-failure placeholders |
| --- | ---: | ---: | ---: | ---: |
| Sonnet | 1,146 | 1,132 | 0 | 14 |
| Opus | 1,146 | 1,131 | 7 | 8 |
| Total | 2,292 | 2,263 | 7 | 22 |

All seven runner errors belong to one Opus incomplete-request suite for `zulip-unsubscribe-self`. No browser report exists for those pairs; captured stderr is empty, so the retained evidence does not establish their specific cause. They remain unusable, and none was rerun. A completed orchestration does not imply every pair was evaluable.

## Desvios operacionais

All times below are on 6 October 2026, America/Maceio (UTC−03). T0 is the protocol commit `e946c0b`, published at 10:11:20, before generation began at 10:11:42. Commit times identify publication of an amendment; launch times identify the subsequent execution. These amendments occurred after the original freeze and are operational deviations, not changes to the scientific contrasts.

| Time (relative to T0) | Amendment or execution | Previously attempted slots carried forward | Outcome |
| --- | --- | ---: | --- |
| 10:31:29 (+20m09s) | `2c376d1`: authorized consumption of the five-hour window to zero, preserving 30% in every other exposed window | 74 | The original stage had stopped at 10:30:38 at its original 30% five-hour reserve. |
| 10:31:47 (+20m27s) | First quota continuation launched | 74 | Stopped at 77 attempts at 10:32:26 because the adapter rejected unexpected system telemetry; that failed attempt was preserved. |
| 10:48:36 (+37m16s) | `82bc5da`: adapter V2 accepted bounded `thinking_tokens` telemetry | — | Versioned parser amendment; it did not reclassify the previously rejected response. |
| 10:48:58 (+37m38s) | V2 continuation launched | 77 | Stopped at 98 attempts at 10:54:56 because subscription quota status `allowed_warning` was not accepted. |
| 11:07:49 (+56m29s) | `b53eb9e`: V3 accepted `allowed_warning` with valid quota, and journaled continuations after reset | — | Five-hour reserve remained zero; other windows retained their 30% reserve. API/extra usage remained disallowed. |
| 11:08:14 (+56m54s) | V3 segment 000 launched | 98 | Stopped at 112 attempts at 11:11:31 on five-hour exhaustion: 110 ready suites, 2 preserved failures. |
| 14:32:18 (+4h20m58s) | Segment 001 launched after the 14:30 reset and a new quota qualification | 112 | Stopped at 255 attempts at 15:10:26 on five-hour exhaustion: 252 ready suites, 3 preserved failures. |
| 19:31:50 (+9h20m30s) | Segment 002 launched after the 19:30 reset and a new quota qualification | 255 | Generation completed at 19:43:48 with 300 unique attempts: 297 ready suites and 3 preserved failures. |

The carried-forward counts are cumulative, not additional calls. Quota qualifications were separate public setup probes, not research slots. Every continuation excluded all previously attempted slots, including failures. Receipt/hash verification confirmed that imported evidence, frozen prompts, selected mutants and schedules were preserved; no already-attempted slot was replaced. The analysis scripts `scripts/mutation_adequacy.py` and `scripts/shared_omission_e2e.py` did not change between `e946c0b` and `b53eb9e`. Versioned adapter/quota wrappers changed as listed above. The later Docker evaluation was a separate authorized offline stage and made no model calls.

These results concern **Sonnet 4.6 and Opus 4.6**, the explicitly requested IDs in this frozen collection. The choice did not establish that they were the current Claude releases. A replication with Sonnet 5.5 and Opus 5.5 must be frozen and reported separately; it cannot replace or relabel these outcomes.

## MA1 and MA2

MA1 compares complete requirements with incomplete requests; MA2 compares complete requirements with incomplete requests plus the selected mutant's code. The analysis uses the frozen estimator, equal weight per requirement, bootstrap resampling of projects and an exact two-sided sign-flip test that swaps signs by project.

| Model | Contrast | Mean difference | 95% project-bootstrap interval | Exact project p | Requirements higher / lower / tied |
| --- | --- | ---: | --- | ---: | --- |
| Sonnet | MA1 | 0.350 | [0.2235, 0.4747] | 0.0078125 | 14 / 0 / 11 |
| Sonnet | MA2 | 0.400 | [0.2917, 0.5000] | 0.0078125 | 14 / 0 / 11 |
| Opus | MA1 | 0.715 | [0.5598, 0.8750] | 0.0078125 | 20 / 0 / 5 |
| Opus | MA2 | 0.800 | [0.6957, 0.9091] | 0.0078125 | 21 / 0 / 4 |

Each contrast meets the exploratory protocol's joint criterion: the project-bootstrap interval is above zero and the project-level p is below 0.05. With eight projects, 0.0078125 is the smallest possible two-sided sign-flip p. This does not turn the collection into confirmation of H1 or validate its labels independently.

## Soundness and conditional discrimination

A sound suite is usable and quiet on the correct reference. The following counts include only such suites. Correct pages exclude the reference itself; recovered pages are C implementations that retained the obligation despite its omission.

| Model | Source | Sound suites / 50 | Confirmed mutants alarm / eligible pairs | Other correct pages false alarm / eligible pairs | Recovered pages false alarm / eligible pairs |
| --- | --- | ---: | --- | --- | --- |
| Sonnet | Complete | 26 | 66/87 (75.9%) | 6/68 (8.8%) | 0/14 |
| Sonnet | Incomplete | 22 | 9/74 (12.2%) | 3/60 (5.0%) | 0/13 |
| Sonnet | Incomplete + code | 17 | 0/57 | 0/45 | 0/9 |
| Opus | Complete | 46 | 132/149 (88.6%) | 7/124 (5.6%) | 0/31 |
| Opus | Incomplete | 33 | 13/110 (11.8%) | 4/91 (4.4%) | 0/20 |
| Opus | Incomplete + code | 15 | 0/51 | 0/40 | 0/7 |

The zero conditional false-alarm rates for the code source do not establish usefulness: the surviving sound suites also detected zero confirmed mutants. Conditional rates describe a selected subset and must be read alongside unconditional alarms and the planned scores.

## Unconditional false alarms

These rates include all suites, without requiring reference quietude. Denominators below are observed browser verdicts; the public descriptive accounting also records planned denominators. Missing generation and runner outcomes are not treated as observed quiet results.

| Model | Source | Other correct pages: alarms / observed | Recovered pages: alarms / observed |
| --- | --- | --- | --- |
| Sonnet | Complete | 67/129 (51.9%) | 17/31 (54.8%) |
| Sonnet | Incomplete | 74/131 (56.5%) | 19/32 (59.4%) |
| Sonnet | Incomplete + code | 83/132 (62.9%) | 25/34 (73.5%) |
| Opus | Complete | 13/132 (9.8%) | 3/34 (8.8%) |
| Opus | Incomplete | 42/129 (32.6%) | 11/32 (34.4%) |
| Opus | Incomplete + code | 89/129 (69.0%) | 25/32 (78.1%) |

Every source/model has 132 planned other-correct and 34 planned recovered pairs. Rates over those planned denominators differ where observations are missing; they are included separately in the JSON and should not be mistaken for observed false-alarm probabilities. Sonnet's complete-source result is substantially noisier and less sound than Opus's. This comparison is descriptive, not a randomized model-ranking study.

## Correct-reference verdict versus shown-mutant verdict

Each row represents 50 planned suites. Alarm includes assertion and test-execution errors. Generation and runner failures are separate from both quiet and alarm.

| Model | Source | Reference quiet, mutant alarm | Both quiet | Both alarm | Reference alarm, mutant quiet | Generation failure | Runner failure |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sonnet | Complete | 20 | 6 | 19 | 4 | 1 | 0 |
| Sonnet | Incomplete | 2 | 20 | 21 | 6 | 1 | 0 |
| Sonnet | Incomplete + code | 0 | 17 | 3 | 30 | 0 | 0 |
| Opus | Complete | 40 | 6 | 3 | 1 | 0 | 0 |
| Opus | Incomplete | 4 | 29 | 5 | 11 | 0 | 1 |
| Opus | Incomplete + code | 0 | 15 | 3 | 31 | 1 | 0 |

Of the code-source suites, 27/50 for Sonnet and 28/50 for Opus rejected the correct reference by assertion while accepting the shown mutant. The pattern of a correct reference rejected by assertion and a shown mutant accepted also appears in the incomplete source (Sonnet 5/50, Opus 11/50); it is not exclusive to the code source. This pattern is compatible with tests fixing the behavior of the code they were shown, but only an audit of the suites can establish whether each assertion concerns the target obligation. It is not proof of that mechanism by itself.

The selected mutant was quiet in 47/50 planned Sonnet code-source pairs and 46/50 Opus pairs (one Opus generation failure). Among sound suites, selected-mutant quietude was 17/17 and 15/15. Complete-source selected-mutant quietude was 10/50 and 7/50 overall, or 6/26 and 6/46 among sound suites. Incomplete-only quietude was 26/50 and 40/50 overall, or 20/22 and 29/33 among sound suites.

## Confirmed versus naive scores

Using identical equal-requirement weighting, the complete-source confirmed score was 0.400 versus a naive 0.345 for Sonnet, and 0.800 versus 0.680 for Opus. The naive score treats every C page as a mutant, including recovered pages. Incomplete-only scores were 0.050 versus 0.050 and 0.085 versus 0.075. Code-source scores were 0.000 confirmed versus 0.010 naive in both models; the naive value does not represent a confirmed target defect detected.

## Integrity and limits

Verification covered the original collection receipts, the copy linkage, all frozen/call inventories, per-model evaluation receipts, exact schedule/target coverage, and every browser report's correspondence to its public row. Frozen analyses were regenerated from saved rows without provider calls or browser reruns. Public receipts bind the exported JSONs and preserve hashes of the private collection/evaluation receipts. The original failure was not overwritten.

The public export contains outcomes, sanitized manifests and descriptive aggregates. Prompts, pages, generated suites, provider responses, private paths and identities remain private. No runtime code changed in this results PR.

The models use another provider, but the implementations, oracles, requirement selection and known outcomes are reused. There are only two suites per source; the samples are dependent within requirements and projects. The reference-quiet gate can reject suites for incidental implementation differences. Human review of requirement mappings, oracle labels and the reversed assertions remains pending. These results support the narrower shared-omission mechanism in this exploratory setting, not all requirement smells, production agents or H2.

Public data: [evaluation accounting](../../data/shared-omission-e2e/claude-evaluation-v1/evaluation-accounting.json), [Sonnet](../../data/shared-omission-e2e/claude-evaluation-v1/claude-sonnet-4-6/results.json), [Opus](../../data/shared-omission-e2e/claude-evaluation-v1/claude-opus-4-6/results.json). The paused monitor can be resumed only for further explicitly authorized work; this evaluation is complete.
