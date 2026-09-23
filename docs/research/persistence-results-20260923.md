# Persistence UI pilot: no observed target failure, five unknowns

All 18 frozen prompts were attempted once through Codex subscription in 18 distinct
sessions. All returned admissible raw HTML. The offline browser recorded **13 target
passes, zero target failures and five unknowns**. No provider error, output repair
or wrapper retry occurred. Internal transport retries remain unobservable.

**This does not demonstrate an omission effect for persistence, absence of defects,
or equivalence of A/B/C.** Five unknown outcomes and one exposed requirement limit
interpretation; no H1/H2 or cross-project conclusion follows.

## Fixed planned denominator

| Model | Arm | Planned | Target passed | Target failed | Unknown |
| --- | --- | ---: | ---: | ---: | ---: |
| gpt-5.6-luna | A | 3 | 3 | 0 | 0 |
| gpt-5.6-luna | B | 3 | 0 | 0 | 3 |
| gpt-5.6-luna | C | 3 | 2 | 0 | 1 |
| gpt-5.6-sol | A | 3 | 2 | 0 | 1 |
| gpt-5.6-sol | B | 3 | 3 | 0 | 0 |
| gpt-5.6-sol | C | 3 | 3 | 0 | 0 |

A is the complete requirement, B the preserving rewrite, C the omission.
The C−A failure difference bounds are [0, 1/3] for Luna and [−1/3, 0] for Sol.
These are missingness bounds over three positions per arm, not confidence
intervals. Repetitions do not provide independent requirements or projects.

## Measurement audit: screenshots contradict the “missing” wording

Four rows (Luna B repetitions 1–3 and Luna C repetition 1) were recorded as
`target_not_evaluable` with `todo_missing_after_reload`. Visual inspection shows
`persist-target-row` **present** in their second-page screenshots. Exact source
inspection confirms that the generated title labels are `<span>` elements, while
the frozen runner's `row()` recognizes HTML `<label>` elements or editing inputs.
The runner consequently does not recognize the initial row or enter editing in
These four cases. Its todo/completion failures are not proof of persistence loss.
The common prompt says “visible label” without unambiguously requiring the HTML
`<label>` tag; this is an instrument-coverage/interface ambiguity.

Keep all original reports, categories and hashes unchanged. This post-hoc audit
does **not** convert the four unknowns into passes or target defects. A revised
selector/interface contract needs independently constructed alternative-DOM
controls, explicit admission and a new frozen runtime before future collection.
Replaying saved artifacts under a revised oracle would be labelled post-hoc
diagnostic evidence, not a new prospective replication.

The fifth unknown (Sol A repetition 2) is `interface_error`: a visible editable
input was not observed after double-click. Its initial persistence assertions
passed. A checkbox-linked title and rerender may explain the interaction, but
that static-code hypothesis has not been independently reproduced.

## Evidence and verification

- 52 native PNGs: 17 complete before/edit/second-page sets (51 images), plus one
  partial pre-edit screenshot for the interface-error execution.
- Preselected illustration: Luna repetition 1, A and C. A passed; C is unknown
  due to the span-selector limitation. Do not replace C with a more favorable
  example or present the pair as an observed omission defect.
- Independent assistant audit and parent recomputation verified both packet
  inventories, unchanged runtime/executable, unique sessions, exact raw answer
  to HTML bytes, report classifications and the fixed-denominator analysis.
- 55 focused tests passed; collector CI passed 1,774 tests, with 12 skips and
  nine subtests. The nine prior authored qualification controls were preserved.
- Observed experimental usage: 338,728 input tokens (141,696 reported cached),
  52,271 output tokens. Two separate READY availability calls are not among
  the 18 experimental observations. No monetary API cost is inferred.

Packet receipt SHA-256: `06917820f30abcd2e00e0e288afa36601dc63df2333522378ca38ab678b46df2`.
Frozen runtime receipt SHA-256: `0c15879f34448f9d5b85bcfb5816e81d512ca4bf314375c2477318e0b55a0ed8`.

Private packet: `.private-research-evidence/persistence-collection-20260923-v1`.
Interactive evidence index: `.private-research-evidence/persistence-execution-status-20260923/evidence.html`.

[Machine-readable results](../../data/behavioral-expansion/persistence-results-20260923.json) ·
[Frozen method](persistence-collection-method-20260923.md) ·
[Implementation](https://github.com/danteacosta/agent-smell-degradation-harness/pull/73).

Next: correct and qualify semantic row recognition for future execution; admit
new licensed UI requirements from additional projects. The prior focus result
and this bounded persistence result must both remain visible in the thesis.
