# Fixed-scaffold successor results

This exploratory successor keeps the visible interface fixed and varies only
the behavioral logic generated from the complete requirement (A), equivalent
rewrite (B), or requirement with one obligation omitted (C). The schedule,
prompts, three browser oracles, and 18 qualification controls were frozen
before the 54 generations. All generations finished before browser execution.

## Result

- 54 calls were attempted; 53 outputs were executable and one was retained as
  invalid/unknown.
- All 17 evaluable A outputs and all 18 B outputs passed.
- C produced 11 target-only failures among 18 executions. No non-target or
  mixed failure was observed.
- OpenProject C failed 3/3 under both models. Nextcloud C failed 2/3 under Sol,
  and Paperless-ngx C failed 3/3 under Sol.
- Luna recovered the omitted obligation in all Nextcloud and Paperless-ngx C
  repetitions. This model interaction is part of the result.

Project-weighted C−A was +33.3 percentage points for Luna. For Sol it was
between +77.8 and +88.9 points because one OpenProject A output was invalid.
B−A was zero for Luna and between −11.1 and 0 points for Sol for the same
missing A observation. These missingness bounds are not confidence intervals.

The pilot supplies prospective browser evidence that omission can cause a
visible defect in three additional projects. It does not estimate a population
effect or confirm H1/H2: projects and obligations were purposively selected,
repetitions are nested, and this fixed-scaffold successor was designed after
the earlier collection exposed an interface-conformance problem.

`analysis.json` preserves all per-stratum contrasts and bounds. `rows.json`
links each result to its browser report and screenshot hashes. Raw generations,
prompts, and provider captures remain private.
