# Product pilot protocol

This is the executable plan for validating the gate with real teams. It is a
measurement protocol, not customer evidence.

## Pilot unit

For each pre-merge run, retain only a run ID, requirement hash, trace source,
policy version, decision, review duration, model/provider version, cost, and
the eventual outcome. Do not upload prompts, secrets, customer code, or final
artifacts by default.

## Primary product metrics

- semantic regressions captured before merge;
- false alerts per 100 runs, split by team and policy version;
- median review time and lead time before the eventual failure;
- escaped incidents after an approve decision;
- cost per run and cost per prevented incident.

The `replay.utility.summarize_outcomes` function computes the metric schema.
Before/after comparisons must freeze the policy version and report confidence
intervals; a synthetic fixture result is never counted as customer evidence.

## User-validation sequence

1. Shadow mode: emit artifact-only reports for one repository and collect
   reviewer disposition without blocking merges.
2. Warn mode: measure false alerts and review time for at least two policy
   versions; expose the constraint, checkpoint, evidence, and confidence.
3. Block mode: enable only after a human owner accepts the false-alert budget
   and has a documented override path.
4. Review the anonymized aggregate with the team; export accepted failure
   cases into the versioned registry only with permission.

The primary interview hypothesis is now teams using coding agents whose tickets
may omit obligations from a written specification. The
[07/10 market kit and interview draft](product-market-kit-20261007.md) records the
5.5 comparison and the proposed reference-based audit, whose utility remains
unvalidated. Measure confirmed loss detection and false alarms separately per
rule, including correct and recovered implementations.

Conversational agents following an external policy remain a second market
hypothesis by analogy, without direct evidence from the coding-test battery.
A trace-export pilot could use Phoenix, Langfuse, or Braintrust through the
SDK-free normalization boundary in `replay.integrations`; vendor credentials
remain outside the replay process. This possibility does not establish its
commercial priority.
