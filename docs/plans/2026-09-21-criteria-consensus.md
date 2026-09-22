# Bounded exploratory criteria consensus pilot

The user authorized an exploratory LLM consensus panel on 2026-09-21. This does
not approve human review, rights/governance forms, or confirmatory inference.
SRS163 is one source intent; repeated outputs and six category labels are not
independent source cases. Previous offline preparation remains immutable.

## Acceptance contract and behavior scenarios

1. Given an intact offline receipt and the official CLI, preparing a new private
   packet freezes the exact nine prompts, source, schedule, code and binary
   hashes, three judge models and generator model before any provider call.
   Existing destinations and tampered inputs are rejected.
2. Given eight authored calibration fixtures, each of three isolated judges must
   return all expected category labels and valid literal criteria citations.
   Any invalid or unexpected result stops generation. Expected labels remain
   local; they are never shown to the judges. Calibration is not human validity.
3. Given passing calibration, exactly nine generation slots are attempted once;
   invalid outputs remain invalid with their judgment slots not attempted.
   Each valid artifact receives three fresh isolated judgments in a fixed
   shuffled order. A provider infrastructure error stops all remaining calls.
4. Given three valid votes, only 3/3 labels enter the primary endpoint; 2/3 is a
   separate sensitivity endpoint. Missing votes and disagreements remain visible.
   Every category is reported by arm with denominators and missingness bounds.
5. Given a started packet, another run is rejected, including after interruption.
   Raw captures and original responses remain private, and final receipts bind
   all results. No automatic retry, replacement, API fallback or human approval.

## Design

`scripts/criteria_consensus.py` owns preparation, strict response validation,
run orchestration and deterministic analysis. It reuses `CodexCLIProvider` as
the existing external adapter; no new provider abstraction is needed. Tests
inject a small fake provider factory at this boundary to prove observable call
budgets, stopping, masking, custody and denominators without live expenditure.

Three calibration batch calls (eight fixtures each), nine generation calls and
27 one-artifact judge calls give a maximum of 39 calls, 180 seconds each.
The CLI fixes low reasoning and does not expose immutable model snapshots or
an enforceable output-token limit; these limitations are recorded. All models
share a provider and possible training lineage; fresh calls are operationally
isolated, not statistically independent human raters. A calibration failure
stops the pilot without tuning or substitution in the same packet.

The six categories are about, version, title, current_version, license, links.
Only acceptance criteria establish coverage, not uncertainty questions.
Supported requires an explicit assessable obligation; absent uses null evidence;
unclear requires a literal span documenting ambiguity or contradiction. The
source does not settle per-command versus collective scope. Specific URLs,
exit codes and other additions do not improve source category coverage; judges
record additions separately. Eight fixtures cover full coverage, omitted links,
generic information, links only in uncertainties, paraphrase, negation,
contradiction and unsupported additions. Calibration labels are author-created.

The frozen offline order is preserved. Judge artifact IDs are opaque and
judge orders are shuffled using fixed seeds. No arm, generator model, paired
output, calibration answer key, or previous vote is sent to judges. The rubric
and complete source are necessary reference information. Consensus is computed
without a debate round. Bounds count unclear, unresolved and missing artifacts as either
unsupported or supported, with all three planned repetitions per arm retained.

## Verification

Run `python -m pytest -q tests/test_criteria_consensus.py tests/test_codex_cli.py`.
Review the final diff for readable functions, explicit failures, privacy,
no unrelated changes, and no hidden paid-provider fallback before collection.

## Operator commands

From the repository root, use the existing Python environment. Preparation
performs no model calls. Choose a new destination for each prospective protocol;
never overwrite or resume a started collection, including after interruption.

```sh
umask 077
python scripts/criteria_consensus.py prepare \
  --source /absolute/private/criteria-offline-preparation-20260921-v1 \
  --output /absolute/private/criteria-consensus-20260921-v1 \
  --executable /Applications/ChatGPT.app/Contents/Resources/codex
python scripts/criteria_consensus.py run \
  --packet /absolute/private/criteria-consensus-20260921-v1
python scripts/criteria_consensus.py analyze \
  --packet /absolute/private/criteria-consensus-20260921-v1
```

`run` makes the authorized live subscription calls; there is no paid-key route.
Do not edit the frozen code or binary between prepare and run. After completion,
`receipt.json` binds all files; verify with `verify(Path(packet))` before moving
or publishing derivative summaries. Analyze prints a derived report without
writing. Raw responses, custody keys and captures remain private. Public or
Drive reporting should use aggregate results and limitations, not dump raw
captures. Calibration failure is a reportable outcome, not permission to tune
this same collection. A process interruption leaves a single-attempt marker;
manual forensic review is required before designing a separate collection.
