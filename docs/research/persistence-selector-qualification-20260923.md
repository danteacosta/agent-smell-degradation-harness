# TodoMVC Persistence: semantic selector qualification

**Status, 2026-09-23:** the successor browser instrument matched the expected
outcomes of **27/27 authored controls**. This is an instrument qualification,
not a new model collection or an experimental result.

## Why the selector changed

The frozen persistence pilot used a row selector that recognized an HTML
`<label>` or edit input. In four of its five unknown outcomes, second-page
screenshots show the named todo, but the generated page rendered the title in a
`<span>`. The runner could not identify that row or enter editing. The recorded
`todo_missing_after_reload` reason therefore does not establish that the todo
was lost. A separate visibility correction had already qualified a nine-control
successor against a hidden restored row. Neither correction changes the frozen
pilot observations.

The current contract identifies one **visible** todo row by its exact rendered
title and requires a title element that can receive the edit action. It checks
the visible edit input before opening a second page at the same origin, then
checks the restored row and edit state there. A hidden, substring-only,
accessible-name-only, control-value-only, ambiguous, or non-actionable title
cannot silently satisfy that contract. Missing or ambiguous prerequisites are
classified as interface errors or an unevaluable target, with their stated
reasons; they are not target passes or target defects. Todo survival, completed
state, and nonempty storage remain separate observations. The target is visible
restoration of editing mode, not literal absence of edit-related serialized
bytes.

## Qualification evidence

The 27 authored controls cover ordinary and encoded storage references,
edit-restoration and completed-state mutants, missing and hidden restoration,
alternative `<span>`, `<div>`, nested, wrapped and checkbox-linked title
markup, and misleading or duplicate titles. Expected and observed categories,
failure IDs, target reasons, and screenshot inventories matched exactly in all
27 cases; the qualification also verified source hashes. An actionability RED
run caught the `non-actionable-title` control as `browser_error` where
`interface_error` was expected. The final GREEN run corrected that boundary.
These controls establish sensitivity to the authored cases only.

The final browser image ID is
`sha256:7ec0ab7cde9cf5b84b0ee5d4c07e86a94f1a696c8a26c6ccdbd73569ae460d4a`.
The full GREEN input, report, receipt and screenshot tree is preserved outside
the repository at
`.private-research-evidence/persistence-selector-qualification-20260923-v1`.
Its `SHA256SUMS` covers 193 evidence files in sorted path order. The copied
`qualification.json` SHA-256 is
`f543e369dc544ab43510e515ed59ae490a4fda51a8e1659931edec4c752ef88b`;
the manifest SHA-256 is
`9f764251d03e8513e9bea2ede9745d5a6c0e6a3483d763f64f63d198e7987f5d`,
and the top-level `receipt.json` SHA-256 is
`52a53a231bbe06b1c47c1a29ce562e7e38f17d37749dda8da3511dab0cc76dda`.
The receipt records the source qualification path and hash, image ID, control
count, UTC creation time and scientific boundary. All copied evidence hashes
were verified against the manifest.

## Interpretation and next step

The [18-generation pilot](persistence-results-20260923.md) remains **13 target
passes, zero target failures and five unknowns**. In particular, its four
`<span>`-labelled unknowns remain unknown. Replaying saved HTML with this
successor may diagnose selector behavior, but cannot create prospective evidence
or revise the frozen reports. The older [v4 and nine-control qualification
history](persistence-oracle-qualification-20260922.md) also remains intact.

For another collection, independently review the exact prompts for target
leakage, freeze the eligible cohort, instrument bytes, runtime and schedule,
then collect prospectively. The authored controls alone say nothing about the
frequency of generated-code defects, a requirement-smell effect, or H1/H2.
