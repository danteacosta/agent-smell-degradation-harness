# IRR correction: coincidence weighting and undefined estimates

## Contract and design (before implementation)

Given incomplete independent annotations, alpha uses only units with at least two
observed labels. When annotator counts differ, each ordered within-unit pair has
weight `1 / (m_u - 1)`. Expected disagreement uses the resulting pairable-label
marginals. Ordinal distance is the squared difference of marginal midranks,
not equally spaced label indices. These definitions follow Klaus Krippendorff,
[Computing Krippendorff’s Alpha-Reliability (2011), sections C–D](https://www.statisticshowto.com/wp-content/uploads/2016/07/fulltext.pdf)
(author's University of Pennsylvania postprint, accessed 2026-09-21).

Acceptance scenarios:

- Given the published four-observer missing-data example, nominal alpha matches
  `1 - 312/1216` and ordinal alpha matches the independently tabulated published
  coincidence matrix and ordinal distances.
- Given an extra singleton or unused ordinal rank, the estimate is unchanged.
- Given no pairable values or zero expected disagreement, estimation raises
  `ValueError`; a non-finite decision input cannot become acceptable.
- Given a deterministic unit bootstrap, undefined resamples are counted and
  excluded explicitly; valid resamples supply conditional percentile bounds.
  If none are estimable, bounds are `None`. There are no replacement draws.
- Existing complete, varying-label agreement remains 1; input orientation,
  aliases and valid finite decision thresholds remain compatible.

Implementation stays in `protocol/irr.py`: frequency counts and cumulative
midpoints isolate the statistic without another dependency or design pattern.
Do not materialize all cross-unit label pairs. Tests use public behavior,
exact small-data arithmetic, published examples and missing-data invariants.
Run `python -m pytest tests/test_irr.py tests/test_krippendorff_alpha.py`.

## Interpretation and migration

Previous values from unequal annotator counts, singleton observations, ordinal
scales or degenerate data are not trustworthy estimates of this statistic.
Preserve historical artifacts verbatim, mark affected estimates as requiring
recomputation from original annotations, and record the implementation revision
with corrected outputs. This correction does not re-label or validate any human
annotation, nor does it establish the thesis hypotheses.

Undefined scalar alpha now raises `ValueError`, including through
`compare_annotations`; callers must report unavailable IRR, not substitute zero
or one. `irr_decision` rejects non-finite/out-of-range values. Bootstrap retains
`n_bootstrap` as attempted draws and adds `n_valid` and `n_undefined`; bounds can
be `None`. Bounds after exclusions are conditional on estimability and are not
an unconditional coverage guarantee. The existing unit-resampling scheme is
retained, not advertised as the original author's specialized bootstrap.
The `label_plane.irr` reexports require no code migration; external consumers
must handle the stricter exceptions and nullable bounds.

Known vocabulary and numeric ordinal ordering remain supported for compatibility;
other labels keep the historical deterministic lexical default. Scientific use
must supply the preregistered `ordinal_order`, which must be unique and contain
all pairable labels. Defaults do not establish a scientifically valid scale.
Cohen's kappa and raw agreement are outside this correction's scope.

## Verification on 2026-09-21

The initial regression run produced 16 failing cases and 9 passing cases before
production edits. The final targeted run (`tests/test_irr.py`,
`tests/test_krippendorff_alpha.py`, `tests/test_annotation_rubric.py`) passed 31
cases. The published example's nominal oracle is `1 - 312/1216 = 0.7434210526`;
its ordinal oracle, evaluated separately from the published coincidence table
with exact rational arithmetic, is `108577/133160 = 0.8153875038`. The previous
implementation returned approximately 0.7195782274 and 0.8319009698 respectively.
An additional two-unit unequal-rater-count fixture has exact alpha `1/3`.

Compatibility coverage includes aliases' original tests, permutation invariance,
non-string annotator keys, empty/missing/constant inputs, unused ordinal ranks,
negative estimates, decision boundaries, invalid ordinal configurations, and
bootstrap degeneracy disclosure. The change adds no dependency and changes no
stored result. Review found one pure-statistic owner, no unnecessary abstraction,
and no hidden I/O. Full repository checks and independent review remain part of
the enclosing change's merge gate.

## Annotation ingestion boundary (review follow-up)

Before the follow-up implementation, acceptance was extended: a CSV comparison
must reject duplicate episode IDs, absent cells and blank required values before
computing agreement. A HumanAnnotation sequence must reject repeated
(item_id, annotator_id) observations rather than overwrite a judgment. Missing
values remain supported in alpha's matrix input; a comparison CSV requires one
complete explicit label per episode. These checks prevent artificial agreement
without changing Cohen's kappa formula or silently adjudicating duplicate data.

The ingestion follow-up first reproduced eight failing cases, then passed all
eight after explicit rejection was implemented. Final combined verification with
AP and serialized analysis-report regressions passed 55 cases using the pinned
protocol dependency; IRR/rubric coverage accounts for 39 of them.
