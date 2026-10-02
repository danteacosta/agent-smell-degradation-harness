# One pipeline for A/B/C browser cases

New cases no longer need a collector script. A case is a JSON file in
`data/abc-cases/` plus a fixture folder, and `scripts/abc_case.py` does the
rest: schedule, frozen requests, one generation per slot, the scaffold check
and the oracle run.

## Why

The per-case collectors copied the same code. All seven public cases use a
byte-identical `admit` function and the same prompt template, differing only
in the instruction sentence that names the app API, the arm texts, the seed
and the fixture. `tests/test_abc_case.py` checks that the generic module
produces exactly the same prompts and accepts and refuses exactly the same
pages as each legacy collector.

## Adding a case

1. Create `eval/fixtures/<case>/` with `page.html` (one `/* MODEL_BEHAVIOR */`
   marker), `runner.cjs` (the browser oracle) and `qualify.py` (its `classify`),
   and qualify the oracle with authored controls as before.
2. Write `data/abc-cases/<case>.json`:

```json
{
  "case": "<case>",
  "intent_id": "<case>",
  "project_id": "<project>",
  "fixture": "eval/fixtures/<case>",
  "marker": "/* MODEL_BEHAVIOR */",
  "instruction": "Implement only the requirement in the frozen browser page. ...",
  "arms": {"A": "...", "B": "...", "C": "..."},
  "models": ["gpt-5.6-luna", "gpt-5.6-sol"],
  "repetitions": 3,
  "seed": 2026100301,
  "image": "sha256:..."
}
```

3. Run on the collection machine:

```sh
python scripts/abc_case.py prepare <case> --packet /absolute/private/path
python scripts/abc_case.py run --packet /absolute/private/path
```

## What stays

The legacy collectors stay in `scripts/` unchanged. Their frozen packets
record the hashes of those exact files, so moving or editing them would make
past packets fail verification. The `migrated_from` field of each config
names the collector it replaces.
