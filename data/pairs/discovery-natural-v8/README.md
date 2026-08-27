# Natural requirements-smell screening corpus (v8)

This directory contains the public, auditable part of the v8 acquisition. It
does not redistribute ARTA requirement excerpts because the rights for the
underlying source documents and derivative transformations are not established
in the ARTA Zenodo record. The checked-in `selection-manifest.json` contains
source coordinates and requirement hashes only.

## What was executed

The local private input had 144 natural requirement records: 12 source-labeled
positive records and 12 clean controls for each of six supported families:

- subjective language
- ambiguous adjective/adverb
- non-verifiable term
- vague pronoun
- uncertain verb
- polysemy

The positive records were single-marker rows in ARTA's `Sheet1`; clean controls
had no marker in any ARTA smell column. The same natural clean source rows may
serve as controls for more than one target family, so family-level counts are
not 144 independent requirements.

Comparative, negative, superlative, and loophole are not padded into this round;
they remain underrepresented in this source selection and are listed as
pending. ARTA markers are source labels, not independent expert annotations.

## Recreate the private input locally

Acquire the exact ARTA workbook separately, then run the acquisition step into
a private path:

```bash
./.venv/bin/python scripts/prepare_natural_v8.py \
  --workbook /private/path/001_dataset1kv1.xlsx \
  --output /private/path/arta-v8-cases.jsonl \
  --selection-manifest data/pairs/discovery-natural-v8/selection-manifest.json
```

The runner requires an explicit private-source flag because this source is not
approved for redistribution:

```bash
./.venv/bin/python -m eval.validation_round \
  --corpus /private/path/arta-v8-cases.jsonl \
  --allow-private-source \
  --run-id discovery-20260826-v8-screening \
  --output-root artifacts/experiments/runs
```

The generated artifact bundle redacts requirement text and keeps only hashes,
split assignments, metrics, provenance, and readiness status.

## Interpretation boundary

The primary estimand is `agreement_with_arta_source_labels`, not detector
validity or agent efficacy. The offline baseline is a frozen lexicon comparator.
The v7 agent-condition comparison is simulation-only. Confirmatory evidence is
blocked until the corpus has independent blinded annotations and at least two
configured real-model runs.
