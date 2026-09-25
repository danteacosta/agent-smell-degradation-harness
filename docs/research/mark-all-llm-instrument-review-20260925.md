# TodoMVC Mark all: independent LLM instrument review

Status: **review completed before any new generation; no unanimous admission**.
This review concerns source mapping, A/B/C integrity, prompt leakage, and the
browser endpoint. It does not inspect or label generated outcomes.

## Frozen review input

One identical packet was sent in isolated read-only Codex sessions to three
model configurations: `gpt-6-astra`, `gpt-6-sol`, and `gpt-6-luna`. The packet
contained the pinned TodoMVC source excerpt, exact A/B/C requirements, common
implementation interface, v2 endpoint policy, and the 14-control qualification
summary. Reviewers returned only structured verdicts and short reasons.

- Review prompt SHA-256: `a40473367c69c30e0d70b5c6d79fb46da614081ed8c2d23309d5d69253355041`
- Astra response SHA-256: `c3fc92e824e00bfa3104bd5573e1f2b8951f02a9309443ac4053f0f9b94dfa67`
- Sol response SHA-256: `252382db97e7013e6ee9edebfff220149cb861da69fa60067fbe47745fefe19c`
- Luna response SHA-256: `7921059c792ece622789196b31adcd16f269f732414a799365bbbd8a12fe130f`

Raw packets are preserved outside Git under
`.private-research-evidence/mark-all-instrument-panel-20260925/`. The CLI was
`codex-cli 0.157.0`, authenticated with the ChatGPT account rather than an API
key.

## Verdict

| Review dimension | Astra | Sol | Luna |
| --- | --- | --- | --- |
| Source mapping | accept | accept | accept |
| Arm integrity | accept | accept | accept |
| Prompt leakage | accept | accept | accept |
| Endpoint validity | accept | **defer** | accept |
| Overall | accept | **defer** | accept |

The predeclared unanimity rule therefore defers the v2 instrument. All three
reviewers accepted the source mapping, the meaning-preserving B arm, the
single-obligation C deletion, and the fact that the common interface does not
explicitly state the target outcome. The dissent is narrower and substantive:
the source says to clear the checkbox's checked state, while v2 allowed an
exact `#toggle-all` that remained checked but became hidden to pass.

## Instrument consequence

Version 3 removes that construct mismatch. After successful bulk selection and
Clear completed:

- if exactly one exact `#toggle-all` remains, its DOM `checked` property must be
  false whether visible or hidden;
- removal of the exact master passes because no master state remains;
- duplicate exact identities remain unassessable;
- unrelated checkboxes never substitute for the named master;
- failed action preconditions remain invalid or not evaluable rather than
  target defects.

The qualification matrix now separates a correct hidden-and-reset reference
from a hidden-but-stale target-only mutant. Reports advance to
`mark-all-browser/v3` and qualification to `mark-all-qualification/v3`, so v2
evidence cannot be silently interpreted under the revised construct.

This change answers the panel's objection but does not retroactively create
unanimity. The v3 endpoint requires fresh browser qualification and a new
independent review before Mark all can enter a generation schedule.
