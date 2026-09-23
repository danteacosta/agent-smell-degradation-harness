# StrictDoc statistics: bounded browser qualification

The pinned StrictDoc source at revision `abf7be7daa2a25721a56980b5be15845336ea0b8`
requires a Project Statistics screen (SDOC-SRS-97), including the date of
generation. The omission arm deletes only that date bullet. The common
standalone HTML interface supplies fixture statistics and non-target DOM
observation handles without instructing the date obligation.

The oracle runs generated-interface candidates in an offline, bounded
Playwright container. Two private UTC clocks test whether a rendered date
tracks first render, the operational definition of generation in this replica.
Separate assertions observe project identity, totals, status breakdown and
TBD/TBC totals. Missing or invisible required observation handles invalidate
the interface; they are not target defects. A visible but wrong neutral value
is a non-target failure. Native screenshots and hashed observations accompany
each complete execution.

## Authored controls and independent review

Final local v4 qualification matched **21/21 expected vectors**: nine valid
references (ISO, Portuguese, French, abbreviated month, full ISO timestamp,
below-fold, pointer-events:none, aria-hidden, callable Date()), eight target-only
mutants (omitted, wrong, hidden, transparent, clipped, covered, partially clipped,
and hardcoded first-clock date), two non-target-only mutants (revision/count),
and two invalid interfaces (transparent neutral value/missing handle).
The hardcoded control passes clock one and fails clock two.

Independent review reproduced and closed visibility, date-format and report
consistency defects found in earlier local candidates. Final review matched
source/report hashes and reproduced fail-closed rejection of contradictory
visible-text evidence. Earlier diagnostic packets remain retained separately.
The adapter rejects missing observations, incorrect hashes, inconsistent
failure vectors, missing screenshots and executed-artifact hash mismatches.

Final image: `sha256:c2ff39b383bb43258b358abe342a45edc642fa847bc5f9d8ccc46cb86a68c80d`.
Private packet: `.private-research-evidence/strictdoc-stats-qualification-20260923-v4`.
144 evidence files; qualification SHA-256
`7237037a70580dab80d0983d8522b9e6124b582da75a383ef97192724f6a0028`;
receipt SHA-256
`4083ea8e8bd18cca86a3e012111716cc7e4f401c7c7419bfdb04aa2092e4c5b3`.

## Limits and admission

This qualifies the instrument on authored controls, not generated code or H1/H2.
The source does not define date formatting or precisely define the generation
event. The current observer is bounded to DOM text and a frozen finite date
lexicon, a 1,000-pixel viewport width, 8,000-pixel document height and 20,000
observed characters. It is not universal visual/OCR or semantic validation.
Relative dates, unsupported locales, canvas-rendered text and complex styling
may remain unassessable. A pre-generation admission review must either justify
and freeze these operational limits with an explicit unassessable policy, or
defer this intent. Do not post-hoc classify unfamiliar valid renderings as
omission defects. No candidate is admitted by this qualification alone.

The updated source screen retains three prospective UI intents across two
already exposed projects, conditionally 54 direct-code generations. It
supersedes the mixed API/UI 144-slot proposal for the primary E2E endpoint.
The scheduler checks UI/E2E declarations and receipt-shaped identifiers;
actual receipt integrity still requires the preflight custody verification.
Further project diversity, independent prompt-leakage review and the frozen
cohort/runtime/schedule are outstanding. Historical results remain unchanged.
