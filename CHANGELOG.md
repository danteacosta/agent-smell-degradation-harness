# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Pre-experiment tooling: `LiveAgent` with injectable `MockTransport`, JSON parse retries, and `generate_with_meta`.
- Experiment preflight modes: `--dry-run` (prompts + manifest under `runs/`) and `--mock-live` (offline live-path coverage).
- Pair schema validation on load; alternate RF-09 wording and soft-cardinality pair variants.
- Tolerant oracle scoring (required-key subset; extra artifact keys allowed) with per-key `checks`.
- IRR import utilities (`protocol/irr.py`) with Cohen's kappa and percent agreement on annotation CSVs.
- Offline thesis analysis CLI (`python -m eval.thesis_analysis`) for H1 paired degradation summaries.
- Template-based mitigation rewrite mode reconstructing requirements from oracle specs (non-blind).
- Release hygiene: `CITATION.cff`, Makefile `dry-run` / `thesis-analysis` targets, `runs/` gitignore.

### Tier summary

- **Tier 0–1:** Offline stub harness, injectable failure modes, CI gate (secret-free).
- **Tier 2:** Taxonomy, baselines, analysis report, optional live experiment path.
- **Tier 3:** Mitigation policies, dissertation packaging, trade-off reporting.
- **Pre-experiment:** Mock live path, manifesto, IRR, thesis tables, template mitigation — live runs need only an API key.

## [0.1.0] - 2026-07-20

### Added

- Initial MesaFlow seed pairs, stub agent, oracle validators, and offline `make all` gate.
- Tier 2 overlays: taxonomy labels, observability baselines, analysis report.
- Tier 3 overlays: rewrite/clarify mitigation, mitigation report, dissertation bundle export.

[Unreleased]: https://github.com/danteacosta/agent-smell-degradation-harness/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/danteacosta/agent-smell-degradation-harness/releases/tag/v0.1.0
