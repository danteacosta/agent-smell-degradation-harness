# Wedge reliability check — consumer guide

The wedge is a **local/CI reliability layer** for coding-agent workflows. It does not replace your test suite; it adds a pre-merge signal when requirement smells or semantic degradation may slip past naive checks.

## What it returns

```json
{
  "decision": "approve",
  "reasons": [],
  "static_smell": false,
  "tier_a_risk": 0.0,
  "tier_b_degraded": false,
  "oracle_passed": true,
  "mutation_score": null
}
```

| Decision | Meaning |
|----------|---------|
| `approve` | No smell-driven clarification needed; Tier A/B signals clean |
| `clarify` | Static smell on input with direct policy — ask before codegen |
| `warn` | Tier B oracle/mutation degradation or elevated Tier A provenance risk |

## Local usage

```bash
pip install -e ".[dev]"
python -m wedge --fixture demo-clean
python -m wedge --fixture demo-smelly
python -m wedge --fixture demo-degraded
make wedge-check
```

Exit code `0` only for `approve`; non-zero for `warn` or `clarify`.

## Wiring into CI

### GitHub Actions (this repo)

The workflow `.github/workflows/wedge-check.yml` runs wedge tests and a smelly fixture smoke check on every PR.

### Your repository

1. Install this package (or vendor `wedge/`).
2. After an agent run, write provenance JSONL with Tier A events only in features; log oracle verdict as Tier B.
3. Invoke the check:

```yaml
- name: Agent reliability wedge
  run: |
    pip install -e ".[dev]"
    python -m wedge --fixture demo-smelly
    pytest -q tests/test_wedge.py
```

Replace `--fixture` with your own integration once you pass requirement text, artifact, and provenance path into `wedge.check.evaluate_episode`.

## Temporal cut (leakage control)

| Tier | Use in features | Examples |
|------|-----------------|----------|
| **A** | Yes | `constraint_extract`, operational latency before oracle |
| **B** | Labels only | `oracle_verdict`, `mutation_score` |

Feature export: `observability.features.extract_tier_a_features` — never reads Tier B events.

## Thesis alignment

H2 evaluation offline: `python -m eval.h2_detection` — group-split AUROC by `intent_id` comparing static, operational, and Tier A provenance families.

See [design spec](../superpowers/specs/2026-07-22-wedge-first-reliability-check-design.md) for full strategy.
