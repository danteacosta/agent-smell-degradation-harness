# TodoMVC: post-hoc scaffold-guard diagnostic

Removing the `commitEdit` guard changed the saved exit-only handler from passing
28/28 tests to failing only the Escape title assertion (27/28). Two saved handler
bodies that explicitly reset the draft still passed 28/28 in both contexts.
Native captures show `feed the cat` with the guard and `foo` without it after the
same edit-and-Escape interaction.

This supports context compensation for that saved implementation in this
journey. It is a post-hoc execution intervention on the scaffold, not a new
requirement-to-generation experiment. The [original pilot](../todomvc-exploratory-pilot.md)
still has nine passing supplementary executions and no observed omission effect.
No new model calls, retries, human labels or independent source intents were added.

## Design frozen before these executions

The hypothesis was that the guard `if (!editing.value) return;` in `commitEdit`
may protect a saved Escape handler that only exits editing. Its removal was the
single scaffold change. Handlers, `startEdit`, template, tests, image and
dependencies remained identical across the two conditions. No source or earlier
receipt was overwritten. A second assistant reviewed the plan and input bindings
before execution; this is technical review, not human semantic validation.

The nine original outputs contain three byte-distinct handler bodies. We selected
the lexicographically first original slot for each body before this diagnostic,
then executed each once on the baseline and once with the guard removed. The
mapping below is code identity, not six or nine new generations.

| Saved handler behavior | Representative and original slots with identical body | Baseline | Guard removed |
| --- | --- | --- | --- |
| Reset draft, then exit editing | complete-1 | 28/28 | 28/28 |
| Exit editing, then reset draft | complete-2; also complete-3, rewrite-2, rewrite-3 | 28/28 | 28/28 |
| Only exit editing | missing_condition-1; also missing_condition-2, missing_condition-3, rewrite-1 | 28/28 | 27/28; Escape only |

Crucially, the exit-only body also occurred in one proposed equivalent-rewrite
output. The changed-context failure is therefore not unique to omitted prompts.
We observed one representative execution of this body per context, not three
separately observed omission failures. No binary smell-effect rate is computed.

Two fresh controls preceded the six diagnostic executions: reference 28/28 and
manual mutant 27/28 with the exact Escape failure. Both qualified the runtime and
native media path. The frozen rule would stop the diagnostic if either control
failed qualification. All 28 tests were retained, including non-Escape flows;
unrelated failures and infrastructure errors were not eligible to count as the
targeted effect. Neither occurred in the six completed diagnostic executions.

## Interpretation and limits

The same saved body changes its observable result when one contextual guard is
removed, while the two bodies that reset the draft preserve the behavior. This
supports the guard-compensation explanation more directly than source inspection
alone. It does not demonstrate what the model would generate if it received the
changed scaffold: every original response was generated in the original context.

Order was fixed and each program/context combination ran once. No blur-event
instrumentation was added; the test and screenshot establish external behavior,
not a complete internal event trace. The common source, saved programs and
post-hoc selection limit generalization. Passing tests establish only tested
behavior. We do not pool these runs with the original study, claim equivalence,
admit a smell category or infer H1/H2. No additional scaffold intervention was
introduced after seeing the result.

## Evidence and reproduction

Private packet: `todomvc-context-diagnostic-20260921-v1`.
The pre-execution manifest SHA-256 is
`7648c307eba29d229f1e1304617cbead186dbc036f3778e3650d8fffbc66507a`.
The final receipt covers 120 files and has SHA-256
`c1602c4c935cd8fff18381bafcc23b0a16abc1ff6265fb2f544d2ffbc74daf30`.
It retains the exact one-line diff, both scaffolds, eight bound input sets,
executor commands/logs, JUnit, per-run classifications and native media.

The image was fixed to
`sha256:b1a64a469e36f9b4b4756917b4c0cfa6bed7bb6790ae63505a582aadd017363c`.
Containers ran offline, non-root, with read-only input/root, no capabilities or
credentials and bounded resources. The existing executor and classifier were
reused unchanged. All eight full videos and ten screenshots decoded; the two
exit-only captures were visually inspected. All 120 file hashes/sizes and the
224 original/supplementary files were verified. Directories use 0700, files 0600.

The retained `reproduce.py` is an operator script for this fixed diagnostic,
not a general collector. Its original destination is intentionally non-overwritable.
Reproduction requires a separately named destination, retained source packets
and the exact image. Do not run with Python `-O`: integrity assertions must run.
No provider SDK or live-dispatch path is imported.
