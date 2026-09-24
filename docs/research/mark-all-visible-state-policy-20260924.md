# TodoMVC Mark all visible-state successor

Status: **successor instrument implemented; endpoint admission remains deferred
until the rebuilt browser qualification passes and the successor evidence is
reviewed**. This change does not replay or rescore prior artifacts, make a model
call, or add evidence for H1/H2.

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

## Admission consequence

The historical v1 packet and every prior model result remain immutable. A green
successor qualification would remove the hidden/removed/replacement policy
defect, but it would not by itself admit Mark all. Admission still requires an
independent review of the exact endpoint and prompts, a frozen runtime and
schedule, evidence custody, and explicit treatment of any unassessable output.
Project diversity remains unresolved because Mark all and persistence are both
TodoMVC requirements.

