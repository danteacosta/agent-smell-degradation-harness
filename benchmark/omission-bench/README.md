# Omission Bench

When a requirement leaves out one rule, does an AI-generated interface still follow it?

Each case is a real rule from an open-source project's documentation, written three ways:

| Arm | Requirement |
| --- | --- |
| A | Complete |
| B | Reworded, same meaning |
| C | The same text with one testable rule removed |

A model receives each prompt (`cases/<case>/<arm>.prompt.txt`) and returns a complete HTML page. A browser oracle, frozen and qualified with authored controls before any generation, checks the target rule in a network-disabled container. A model that follows the rule in A and B but breaks it in C did not recover the missing rule from context.

## Reference results

See `LEADERBOARD.md`. For the two reference models, the target rule failed in 13 and 15 of 21 C runs, against at most 1 of 21 in A. Five of the seven cases had at least one C failure for each model; two cases (Kanboard closed filter, RealWorld comment delete) were recovered every time.

## Scoring a new model

1. For every case and arm, send the prompt to your model and save the HTML as `<case>__<arm>__<run>.html` in one folder.
2. Build the oracle image used by the reference runs (`IMAGE` in `manifest.json`).
3. Run:

```sh
python scripts/omission_bench.py score --outputs path/to/pages --results path/to/results
```

Each page is first checked with the case's own scaffold rules (a page that changes the frozen scaffold is `invalid_output`), then executed by the case's oracle. `scores.json` lists every page's category and the counts per case and arm.

## Scope and limits

Seven cases from six projects; repetitions are not independent requirements. The cases were chosen by hand during the thesis pilots; the pre-registered sampling frame (`docs/preregistration/`) will add cases chosen by rule. Requirement texts are excerpts of each project's documentation under its own license.

Rebuild everything in this folder with `python scripts/omission_bench.py build`.
