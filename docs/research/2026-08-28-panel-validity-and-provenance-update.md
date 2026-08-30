# Panel validity and constraint-lineage update

This update implements the validity safeguards identified in the August 2026
literature review. It does not change the confirmatory estimands: H1 remains
the reviewed, single-defect clean-versus-defective comparison, and H2 remains
the held-out B3 minus B0 PR-AUC comparison.

## Panel launch gate

`scripts/run_llm_panel.py --full-run --confirm-cost` now fails closed unless
the private runtime configuration declares `max_total_cost_usd`, complete input
and output pricing for every judge, and a conservative preflight estimate that
fits below the cap. It also records the configured maximum attempts and a
minimum per-judge request interval. The manifest records the safe configuration
identity, conservative ceiling, measured usage and measured cost; prompts,
responses, endpoints and API keys remain private.

The panel still supplies exploratory `panel_consensus`, never ground truth.
`merge_llm_panel.py` sends all disagreements and uncertain cases to human
review, then adds a reproducible audit that is stratified by smell family,
consensus outcome and apparent difficulty. This guards against a reassuring
overall agreement rate hiding family-specific judge failure.

## Pre-final constraint lineage

The staged runtime now creates a bounded lineage for every interpreted
constraint at T3:

`constraint_id -> constraint_sha256 -> planned_check_ids -> observation_id -> status`

The lineage is built from T1/T2/T3 only. It contains no chain-of-thought, final
acceptance criterion, oracle result, outcome label, mutation identity or
defect-family label. `status` is only `covered` or `uncovered` according to the
deterministic semantic-plan contract validator. T4 may join independent
reference constraints after the feature-plane cutoff, but that join cannot be
used as a deployable feature.

Consequently, H2 tests the added value of traceable pre-final evidence rather
than the mere presence of telemetry. The lineage counts and uncovered lineage
counts are derived features; their interpretation remains associational for H2,
not proof that provenance causes better detection.

## Required operational sequence

1. Freeze judge model IDs, endpoints, pricing, prompt/task hashes, split and
   annotation rubric.
2. Run the 10-task-per-judge smoke test and inspect error, latency, token,
   cost and judge-format distributions.
3. Approve a private cost/attempt cap, then run the 720 total blind tasks
   (approximately 240 per judge before retries), not 720 per provider.
4. Merge only private normalized responses; conduct the mandatory review plus
   stratified audit before treating any candidate as confirmed.
5. Keep panel outputs out of T1--T3 and out of the final confirmatory detector
   labels until independent human adjudication is complete.

## Evidence boundary

Korn et al. (AIRE 2026) motivates independent human review because allegedly
clean requirement corpora can contain smells and inter-rater agreement can be
low. He et al. (TOSEM 2026) and REFLECT (2026 preprint) motivate calibration and
disagreement-aware auditing of LLM judges. Wang et al.'s provenance survey
(2026 preprint) motivates typed links but does not establish a causal PR-AUC
gain. These sources justify safeguards and measurement changes, not a new
causal claim.
