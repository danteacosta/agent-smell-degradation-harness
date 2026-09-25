# RealWorld article-author E2E: heterogeneous omission effect

This bounded exploratory collection is the research program's **second project
with generated-code browser evidence**, after TodoMVC. It tests one requirement:
the `Delete Article` button is visible only to the article author. A is the
complete wording, B is a meaning-preserving rewrite, and C omits the author-only
condition.

All 18 frozen requests were attempted once in separate Codex CLI sessions: nine
with `gpt-5.6-luna` and nine with `gpt-5.6-sol`. Every response was admitted as
unchanged HTML and evaluated only after all generation had finished. The
qualified browser instrument produced 72 screenshots at 1000 × 720. Seventeen
outcomes were evaluable and one was unknown.

## Fixed-denominator results

| Model | Arm | Planned | Target passed | Target failed | Unknown |
| --- | --- | ---: | ---: | ---: | ---: |
| gpt-5.6-luna | A | 3 | 3 | 0 | 0 |
| gpt-5.6-luna | B | 3 | 1 | 1 | 1 |
| gpt-5.6-luna | C | 3 | 0 | 3 | 0 |
| gpt-5.6-sol | A | 3 | 2 | 1 | 0 |
| gpt-5.6-sol | B | 3 | 3 | 0 | 0 |
| gpt-5.6-sol | C | 3 | 3 | 0 | 0 |

For Luna, the C−A target-failure difference was **+1**: every omission output
exposed the button to a non-author, while every complete-requirement output
passed. For Sol, C−A was **−1/3**: all three omission outputs passed and one of
the three complete-requirement outputs failed. The observed effect is therefore
**heterogeneous across these two model configurations**. It is evidence that
the omission can matter in a second E2E project, but it is not a general effect
estimate and does not confirm H1 or H2.

## Unknown outcome and rewrite sensitivity

Luna B repetition 2 (`rw-1fcb4ac2a7f9d19e22d0dca0`) was not evaluable. The
page visibly rendered “By alice/Bob”, but the qualified prerequisite did not
find the exact author username as the article-author element text in any of the
four author/viewer contexts. The instrument therefore recorded
`article_author_missing` and withheld both target verdicts. The button behavior
looked correct in the published sample, but the outcome remains unknown and in
the planned denominator; it was not recoded after inspection.

B is a sensitivity control, not an interchangeable duplicate. Luna B produced
one failure, one pass and one unknown; Sol B produced three passes while Sol A
included one failure. These differences show that wording and model
configuration can change outcomes even when the intended obligation is
preserved. They weaken any simple attribution of every A/C difference to the
omitted clause alone.

## Reproducibility and custody

The public materializer independently verified:

- the exact private root receipt, frozen manifest and frozen receipt;
- the exact collection, results and analysis files;
- 18 call attempts, 18 admitted artifacts and 18 browser executions;
- equality of each saved response, the final captured agent message and the
  evaluated `app.html` bytes;
- all 18 browser reports through `classify_report`;
- exact recomputation through `scripts.behavioral_expansion.summarize`;
- 72 PNGs at 1000 × 720, generation-before-browser ordering, the 9+9 model
  allocation and provider-reported token usage.

Observed experimental usage was 392,267 input tokens, including 150,144 cached
input tokens, and 25,845 output tokens, including 3,444 reasoning tokens. These
are provider-reported token counts; no monetary API cost is inferred.

Private packet receipt SHA-256:
`1bb56d83986f8d3ff6e50f2005da68382116ea8e6a5f2919a13f9f9e1552a625`.
Public bundle receipt SHA-256:
`2f20545d2119f660965db81ca838eb4c4c8c6563b918e627fd505f9db054a988`.

The [public result bundle](../../data/behavioral-expansion/realworld-author-ui-results-20260925/manifest.json)
contains only a manifest, row ledger, analysis, receipt and four preselected
screenshots. It excludes prompts, generated HTML, raw provider captures and
private filesystem paths. The samples show a Luna C failure, a Sol A failure, a
Sol C pass and the Luna B unknown; they illustrate the heterogeneous result and
do not replace the 18-position ledger.

## Claim boundary

This is one obligation in one additional project, with three repetitions per
cell and two model configurations. Repetitions do not substitute for new
requirements or projects. The study still requires more independently sourced
E2E obligations before estimating a general requirement-smell effect. No H1 or
H2 conclusion follows from this bundle.
