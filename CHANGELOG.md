# Changelog

## Unreleased

### Changed

- H2 project-bootstrap inference now fails closed whenever project-label support can produce a one-class resample, and the confirmatory gate verifies v3 precision-simulation accounting.

### Added

- Wedge reliability check CLI (`python -m wedge`) with `approve` / `warn` / `clarify` decisions and demo fixtures.
- Tier A/B provenance tagging in `ProvenanceRecorder`; `observability.features.extract_tier_a_features` excludes oracle labels.
- Mutation scoring for `test_gen` episodes (`eval/mutation.py`, `mutation_score` on episodes).
- RF-11 numerical inconsistency pair (10 vs 15 minute refund window).
- H2 group-split detector script (`python -m eval.h2_detection`).
- GitHub workflow `wedge-check.yml`, consumer guide `docs/wedge.md`, and `make wedge-check`.
- Wedge-first README positioning and design spec link.
