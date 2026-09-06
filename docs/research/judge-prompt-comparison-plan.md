# Judge prompt comparison implementation plan

Goal: test whether explicit coverage instructions and grounded evidence improve
omission detection without increasing false alarms on complete criteria.
Architecture: an auxiliary runner uses the existing provider adapters, pricing,
cost ledger and request validator. The historical prompt, parser and 120-episode
protocol stay unchanged. A separate evidence response contract is not promoted
into the pre-pilot automatically. Implementation and review run sequentially.

## Investigation and design

The old prompt specifies JSON labels but never defines the comparison between
criteria and reference. It shows only a clean/covered response and omits the
rubric's severity anchors. These are observable specification gaps. Whether
anchoring caused past errors remains an untested explanation.

Alternatives: retain the two-key response and add instructions; add explicit
instructions plus a short criterion quote; or delegate every atomic clause to
a separate judge call. Use the second approach approved in the discussion.
It makes grounding auditable at modest cost. It changes both instructions and
response requirements, so the experiment cannot isolate their individual effects.

Compare two arms: historical prompt verbatim versus rubric/evidence prompt.
Both use 96 output tokens to avoid confounding the within-run comparison with
output limits; the earlier historical experiment used 48 and stays separate.
Models, prices and decoding settings otherwise come from the frozen config.
No examples from the evaluation controls appear in the new prompt.

Construct six new templates before collection, each with literal coverage,
meaning-preserving paraphrase, deletion and opposite behavior. Include the 12
old controls as a separate development stratum. Total: 36 cases, two arms, two
providers, two repetitions = 288 calls. Order is seeded and frozen before any
response. New templates have not received provider responses, but authoring is
not an independent/blinded natural-language validation.

Primary diagnostic: omission detection on new deletion cases (12 occurrences,
six templates, per arm/provider). Also retain coverage false alarms, abstention,
invalid/missing calls, contradiction, paraphrase sensitivity, evidence validity
and cost. A constant-omitted judge must fail the complete-case controls. Report
counts by stratum and operation; no pseudoreplicated confidence intervals.

The evidence arm must assess all clauses of the one supplied reference, use
covered only when all are operationalized, use omitted for absent/opposite
behavior, and reserve uncertain for genuine ambiguity. A quote must come from
the criteria, never the reference; quotation presence does not prove entailment.
Covered requires a nonempty quote. Absence may have an empty quote. Missing or
fabricated evidence is reported separately from semantic classification.

## Cost and privacy

Keep the US$1 cap. No retries or generation calls. Freeze a direct experiment
envelope from each prompt's UTF-8 byte size plus a 64-token framing allowance,
96 output tokens and the existing prices, with 25% contingency. The allowance
is an accounting assumption, not vendor-tokenizer certification.
Also reuse the conservative Task 3 ledger with judge bounds 512/96; unused
generation slots have 1/1 bounds and are never dispatched. Its 1,296-slot
envelope over-reserves this judge-only subset. Do not use this auxiliary budget
configuration to launch the 120-episode protocol. Actual usage above the ledger
bound or missing usage stops collection with planned denominators retained.

Freeze source/configuration/prompt/pack/order hashes before collection. Reject
output in any checkout or existing run directory. Never expose control oracles,
arm names, model identities or stage labels to the judge. Keep raw responses,
usage and ledgers private. Publish aggregate results only.

## ATDD / BDD and work sequence

- [ ] Add `tests/test_judge_prompt_comparison.py`: given the frozen pack, requests
      have only the existing allowlisted fields and no condition/arm identity.
      Given complete/omitted replies, report correct and false-alarm denominators.
      Given fabricated quotes or duplicate JSON keys, report invalid evidence.
- [ ] Implement `label_plane/judge_prompt_comparison.py`: immutable prompt,
      36-case pack, strict evidence response parsing and stratified scoring.
- [ ] Add `tests/test_judge_comparison_runner.py`: preflight never creates clients;
      the fake live path records 288 calls, refuses overwrite and repository
      storage; unknown usage stops after one attempt without retries.
- [ ] Implement `eval/judge_prompt_comparison.py`: frozen order, price envelopes,
      existing adapters/ledger, append-only private records, aggregate report.
- [ ] Run targeted tests red then green; review security, SOLID and clean code.
      Run full pytest, eval/gates/wedge and compile checks; commit before live use.
- [ ] Run one preflight and one authorized live comparison; no adaptive prompt
      edits or repeated search for a favorable result. Preserve all failures.
- [ ] Publish aggregate results and limitations in research docs and a follow-up
      PR. Update the task list. H1/H2 and human calibration remain unchanged.
