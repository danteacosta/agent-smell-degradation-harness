# Claude shared-omission replication: generation complete, evaluation unavailable

The replication generated 297 test suites in 300 unique research attempts, but it produced **no browser verdicts**. Docker was inaccessible during the entire evaluation. This packet cannot answer whether complete requirements detect more shared omissions than incomplete requests. It does not replicate or refute the earlier OpenAI results.

The study used the same frozen 25 requirements from eight projects, three sources and two suites per source, separately for `claude-sonnet-4-6` and `claude-opus-4-6`. The code source received the selected confirmed mutant, not a correct reference. No implementation was generated. The protocol and subscription integration are in [PR #188](https://github.com/danteacosta/agent-smell-degradation-harness/pull/188), runner revision `b53eb9e`.

## What actually ran

| Model | Unique calls attempted | Suites ready | Generation failures | Planned suite/page pairs | Docker launch attempts | Browser reports | Generation-failure placeholders |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sonnet 4.6 | 150 | 148 | 2 | 1,146 | 1,132 | 0 | 14 |
| Opus 4.6 | 150 | 149 | 1 | 1,146 | 1,138 | 0 | 8 |
| Total | 300 | 297 | 3 | 2,292 | 2,270 | 0 | 22 |

A Docker launch attempt is not a browser test execution. Every captured Docker stderr reports that it cannot connect to the Docker daemon. There are no `report.json` browser reports. The 22 generation-failure rows are placeholders, not Docker attempts. The executor caught launch failures, classified them as `runner_error`, continued through the schedule and wrote a terminal completion marker. That marker proves the orchestration ended, not that the study was successfully evaluated.

The three failed generations remain failures. One Sonnet stream was refused by the earlier telemetry parser; its later offline parser diagnostic did not replace the original label. The other Sonnet failure and the Opus failure occurred at five-hour quota exhaustion. None was retried.

## Accounting by source

| Model | Test source | Suites ready / planned | Runner-error pairs | Generation-failure pairs | Selected mutant: runner error / generation failure |
| --- | --- | ---: | ---: | ---: | ---: |
| Sonnet | Complete requirement | 49/50 | 374 | 8 | 49 / 1 |
| Sonnet | Incomplete request | 49/50 | 376 | 6 | 49 / 1 |
| Sonnet | Incomplete request + mutant code | 50/50 | 382 | 0 | 50 / 0 |
| Opus | Complete requirement | 50/50 | 382 | 0 | 50 / 0 |
| Opus | Incomplete request | 50/50 | 382 | 0 | 50 / 0 |
| Opus | Incomplete request + mutant code | 49/50 | 374 | 8 | 49 / 1 |

Each source has 382 planned suite/page pairs per model and 50 planned pairs against the selected mutant. No source has an evaluable reference/mutant pair. There are no observed quiet verdicts, assertion alarms or error alarms from the browser. This is missing evaluation, not observed quietude.

## MA1, MA2 and false alarms

MA1 (complete minus incomplete) and MA2 (complete minus incomplete plus mutant code) are **not estimable as behavioral contrasts** for either model. Conditional false-alarm rates have zero eligible denominators; unconditional false-alarm rates also cannot be estimated because no planned pair has an observed browser verdict. Reference/mutant discrimination and selected-mutant quietude are likewise unavailable.

The frozen scorer mechanically assigns every unusable suite a zero score. Regenerating that unchanged analysis reproduces MA1 = MA2 = 0, project-bootstrap intervals [0, 0], and exact project sign-flip p = 1. Those values are retained in each published `results.json` for provenance, with explicit `evaluation_status` and `analysis_interpretation` warnings. They are **not evidence of no effect**, and must not enter a scientific results table as a null finding. The separate accounting files use null for unavailable behavioral estimates. Confirmed and naive mutation scores are equally uninformative here; equal requirement weighting cannot recover absent observations.

## Quota and continuation amendments

The collection initially reserved 30% in every exposed subscription window. After collection began, Dante authorized consuming the five-hour window to zero while keeping at least 30% in every other window, with no API or extra usage. A versioned parser accepted bounded thinking-token telemetry without changing earlier outcomes, and a versioned quota reader accepted `allowed_warning` while retaining the same budget boundaries. Prior packets and receipts were imported by hash, not counted as additional research calls.

Journaled stage 000 stopped at 112 unique attempts, then resumed after the observed reset at 14:31 America/Maceio on 6 October. Stage 001 stopped at 255 attempts, then resumed at 19:31 after the next reset. Stage 002 completed the remaining 45 slots. Failed attempts were excluded from every continuation. Two separate, one-shot `QUOTA_RESET_OK` technical qualifications preceded the two reset continuations; these are not included in the 300 research calls. The last research-call quota was 77% remaining in the five-hour window and 84% weekly. There was no research retry.

## Integrity and disposition

The frozen manifests, chained imports, journal receipts and per-model collection receipts were verified. Each model has exactly 150 distinct attempt markers and matching generation outcomes; the published schedules contain the same slots. Analyses were regenerated from the rows using the frozen code without model calls or browser reruns. Every captured Docker stderr was inspected mechanically for the same daemon-connection failure, and the absence of browser reports was checked independently of the orchestration markers.

The public packet contains structured outcomes, sanitized manifests, aggregate accounting and receipt hashes. Prompts, generated suites, pages, raw provider streams, identities and private paths remain private. The original private packets were not changed.

The automation is paused after this failure report. Any later evaluation of the saved suites needs an explicitly recorded new evaluation stage and Docker qualification; it must preserve this failed execution and make no new generation calls. No such rerun was performed here.

This remains an exploratory study with repeated suites nested within 25 requirements and eight projects. It changes neither H1 nor H2, preserves the previous OpenAI studies, and does not satisfy the pending human audit or confirmatory selection decisions.

Public evidence: [collection accounting](../../data/shared-omission-e2e/claude-v1/collection-accounting.json), [Sonnet outcomes](../../data/shared-omission-e2e/claude-v1/claude-sonnet-4-6/results.json), [Opus outcomes](../../data/shared-omission-e2e/claude-v1/claude-opus-4-6/results.json).
