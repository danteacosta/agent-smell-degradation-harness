# Dissertation export

This directory documents how to produce an offline thesis bundle from the harness.

## Generate bundle

```bash
make mitigation          # eval/mitigation_report.json (H5 trade-off)
python -m eval.dissertation_bundle
```

Outputs:

| Artifact | Path |
|----------|------|
| JSON bundle | `eval/dissertation_bundle.json` |
| Markdown summary | `docs/dissertation/BUNDLE_SUMMARY.md` (generated; gitignored) |

The bundle aggregates pair inventory, taxonomy mode counts, analysis summary,
mitigation trade-off (rewrite vs clarify vs direct under smell-blind), paired
stats, and a **synthetic** reliability demo. The synthetic `agreement_rate` is
not human IRR — see `protocol/reliability.py` for the documented limitation.

## Related commands

```bash
make analysis            # eval/analysis_report.json (C4 effect + observability)
python -m eval.mitigation_report
```

Design spec and tier mapping: [design spec](../superpowers/specs/2026-07-20-agent-smell-degradation-harness-design.md).
