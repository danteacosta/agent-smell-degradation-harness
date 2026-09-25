# TodoMVC Mark all visible-state successor

> Superseded on 25 September 2026 by the v3 remaining-state policy after the
> [independent LLM instrument review](mark-all-llm-instrument-review-20260925.md)
> failed its unanimity gate. Historical v2 evidence below remains unchanged.

Status: **successor instrument qualified; endpoint admission remains deferred
until the successor evidence and endpoint are independently reviewed**. This
change does not replay or rescore prior artifacts, make a model call, or add
evidence for H1/H2.

## Blocker and observation policy

The first Mark all oracle treated a checked but hidden `#toggle-all` as a target
failure while treating removal of the same control as potentially ambiguous.
Those outcomes are inconsistent at the declared user-visible endpoint: after
Clear completed empties the list, neither a removed nor a hidden master exposes
a checked state to the user.

The successor binds the master role to the public interface's exact
`#toggle-all` identity and evaluates the state only after the same-context
prerequisites succeed:

1. both fixture todos become checked through the visible master;
2. Clear completed is available and removes both rows;
3. zero or one exact master identity remains.

After those prerequisites, one visible exact master must be unchecked. A
removed or hidden exact master passes this bounded user-visible postcondition.
More than one exact identity is unassessable, not a target failure. Other
checkboxes are not reinterpreted as the master because the generator interface
assigns that role only to `#toggle-all`.

This policy does not claim that a hidden DOM node's internal property was reset.
It tests what remains observable at the interface after the list becomes empty.
Any future claim about internal state requires a separately declared endpoint.

## Successor controls and schema

The qualification matrix now adds three adversarial cases to the previous
eleven:

- a checked master hidden after Clear completed, expected to pass the visible
  endpoint;
- a removed original followed by a visible checked replacement with the same
  exact identity, expected to fail the target;
- duplicate exact master identities after clearing, expected to remain
  unassessable.

The former ambiguous-control case now passes because removal of the exact
master is valid even when an unrelated checked setting remains. The browser
report advances to `mark-all-browser/v2`. It records bounded per-master
visibility and checked-state arrays before and after the action. The Python
adapter validates the complete observation shape, count consistency and
bounded console errors before classifying an outcome. Old v1 reports therefore
cannot be silently interpreted under the new policy.

## Methodological bridge

WebTestPilot (Teoh et al., FSE 2026) grounds natural-language E2E assertions in
symbolized GUI elements and evaluates sequential pre/postconditions over
observable states. Its released benchmark contains 100 requirements across
four web applications and uses independent Playwright assertions to evaluate
test traces. This supports making role identity and temporal state explicit in
the oracle. It does not validate this selector, TodoMVC, requirement-smell
causality or the choice to treat hidden and removed controls as equivalent.
Unlike WebTestPilot's learned oracle inference, this study keeps one frozen,
deterministic assertion across A/B/C arms.

## Qualification evidence

The first rebuilt browser qualification matched all 14 authored expectations
under `mark-all-qualification/v2`, with no category, failure-set or reason
mismatch. Its pinned browser image was
`sha256:0d15f621ee19e16acdf496cdb49722de7b03a09d8dd8b7b5d070e2cd5945eb34`.
The qualification JSON digest was
`701f7a607f096ac9a6559ba7c25d2caf6ffb280c213b0ed4b67316b677847d22`,
and the archived 110-file evidence bundle digest was
`c5e7f4e2cd4c6437646e85a5db5d8de6f6fd4d623753cc906da01b9a0d01959d`.

The final-head CI rerun at commit
`1b2d3d916c9040555245423a71af0d48db9afa93` independently matched the same
14 expectations. Its pinned browser image was
`sha256:56798de1b10786ad610c94137da1a161e38a2e533ea2045832389db0c22f0bb5`.
The downloaded `qualification.json` digest was
`0c85112eb3d5a8bb5ddec41cc0d087778fa3af0b4c53c704b765ecffceb28971`,
and GitHub recorded the 110-file artifact digest as
`sha256:4d76c36981524ee2e164698d74cfd90893991933435d057b8fe0ef1193d4ccfb`.
The CI run is
[35993817386](https://github.com/danteacosta/agent-smell-degradation-harness/actions/runs/35993817386).

This qualifies the declared controls and observation adapter; it is not a
completeness claim for TodoMVC or evidence that a requirement smell causes a
generated implementation defect.

## Admission consequence

The historical v1 packet and every prior model result remain immutable. The
green successor qualification removes the known hidden/removed/replacement
policy inconsistency, but it does not by itself admit Mark all. Admission still
requires an independent review of the exact endpoint and prompts, a frozen
runtime and schedule, evidence custody, and explicit treatment of any
unassessable output.
Project diversity remains unresolved because Mark all and persistence are both
TodoMVC requirements.
