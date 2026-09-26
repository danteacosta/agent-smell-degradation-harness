# OpenProject Remaining work: prospective browser pilot

This packet adds one previously unexecuted obligation in a project already
represented in the exploratory six-project series. It does not add a seventh
project or confirm H1/H2. The case came from the OpenProject progress-tracking
guide at upstream revision `de051918ba8771d5415c172cc81bcd49f7d10472`:
with Work already set, entering % Complete derives Remaining work. The local
source and GPL license are hash-bound in the freeze manifest. The A/B/C texts
are controlled reconstructions, not verbatim upstream excerpts.

The browser endpoint is fixed before generation. After saving and reloading,
Work 10 hours with 40% Complete must show Remaining work 6 hours; Work 20
hours with 25% Complete must show 15 hours. Work and % Complete must also
survive the save and reload. A target failure is reported separately from
those controls. Invalid interface, browser errors, missing screenshots, or
malformed reports are not scored as target-only defects.

The pinned image is
`sha256:00d1265095773b7f8a12aa73e81d0bab75563cbd672dd0b5d91783ea1b6d4400`.
Seven authored controls passed in real offline Chromium: two correct
implementations, a target mutant, a non-target mutant, a duplicate visible
control, absent behavior, and a script error. The complete reports, screenshots,
and hash receipt are in
`data/e2e-openproject-remaining/oracle-qualification-20260926/`.
These screenshots validate the oracle; they are not generated-model results.

Before generation, separate `gpt-5.6-luna` and `gpt-5.6-sol` reviewer calls
both returned ACCEPT for the exact A/B/C requirements and scaffold. They judged
A/B equivalent for the target, C limited to deleting the derivation, and found
no formula leakage in the C prompt or scaffold. Their responses are stored in
`data/e2e-openproject-remaining/prompt-review-20260926/`. This is LLM review,
not independent human approval, and it does not establish oracle validity by
itself.

The freeze at `data/e2e-openproject-remaining/freeze-20260926/` contains 18
randomized, balanced slots: three arms, two model configurations, three
repetitions. One call per slot, no retry or repair. All outputs are collected
before any generated page is executed in the browser. The private receipt must
retain invalid outputs, provider failures, and unevaluable slots. C−A is the
browser target-failure contrast, and B−A checks wording sensitivity. This is
exploratory evidence within one project and uses a browser failure endpoint,
not the formal human ordinal-severity H1 endpoint. H2 is not evaluated.
