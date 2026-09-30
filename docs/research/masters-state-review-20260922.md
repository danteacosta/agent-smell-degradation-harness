# Master's project status — focus pilot and instrument quality

There is now local behavioral evidence that a textual omission can propagate:
on the direct route, removing the focus obligation produced 6/6 failures, while
the complete and rewritten variants passed. On the saved-criteria route, 10/12
omissions failed and two preserved focus. All 52 code artifacts were generated
before any test was run; two positions without valid criteria remain absent from
the 54 denominator. All other checks passed. The pair of screenshots was chosen
before collection.

[Results, limits and screenshots](focus-chain-results-20260922.md) preserve the
six configuration strata, the hashes, the absences and the non-defective cases.
The case is an already exposed TodoMVC requirement, chosen for feasibility. It
does not confirm H1/H2 or a general smell effect, and it is not an estimate of
causal mediation. The limitation of the auxiliary empty-list test was recorded
without altering the package.

[Infrastructure and measurement corrections](research-stack-audit-20260922.md)
were integrated after CI: ARP 20, MergeWave 24 and RAG 16. RAG has a versioned
metrics contract and a new baseline, with historical artifacts preserved. The
Drive proposal and report distinguish old checkpoints from the current state.

The next step requires prospective selection of new requirements/projects and
oracles derived from each source, with controls that also cover correct
alternative implementations. For H2, keep the B3 versus B0 comparison before the
final artifact and independent evaluation by project. Automated consensus does
not replace human validation and does not allow this pilot to be called a
confirmatory study.

Integration of this stage: [PR 67](https://github.com/danteacosta/agent-smell-degradation-harness/pull/67), conditional on CI of the final commit.

Later E2E pilots (through 26 September 2026) are synthesized, without pooling,
in the [E2E evidence matrix](../thesis/e2e-evidence-matrix-20260925.md).
