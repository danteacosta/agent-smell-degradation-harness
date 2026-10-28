# Omitted-mention triage for generated test suites

Date: 2026-10-28. Status: triage tool, exploratory. Script:
`scripts/omitted_mention_triage.py`; tests: `tests/test_omitted_mention_triage.py`.

The blind human audit of the shared-omission suites (#185) is postponed. This script is
a lexical proxy to prioritise that audit, not a substitute: it lists the words of the
complete requirement that the incomplete request lacks (after removing stop words,
inflections of words in the request and the project name) and reports which of them
appear in a suite's source. A suite that names none of them is unlikely to check the
obligation; a suite that names one may still not check it.

## Check on public suites

The only public suites are the 81 of the 2 October test-anchor diagnostic. For
openproject-invalid-remaining, the omitted tokens are `greater` and `cannot`. Against the
origin-diagnostic results for the confirmed target failure:

| Strategy | Mentions, detects | No mention, no detection | No mention, detects |
|---|---:|---:|---:|
| code_request | 0 | 6 | 0 |
| code_spec | 6 | 0 | 0 |
| spec_only | 2 | 0 | 1 |

14 of 15 suites agree; the disagreement is a spec-only suite that detected the failure
without using either word. This is one requirement and is not a validation of the proxy.

## How to run on the private shared-omission suites

Write a manifest with one entry per suite file
(`{"suite": path, "case": case, "source": source, "id": call_id}`) and run
`python scripts/omitted_mention_triage.py scan --manifest M.json --out OUT.json`. Arm
texts come from `data/abc-cases/`. Report mention rates by source and their
cross-tabulation with kills; keep the human audit pending.

Known weaknesses: single-word omissions (`always` for zulip-unsubscribe-self) and
numbers (`10` for grist-billing-managers-limit) produce one token, so a single
incidental match decides the label; synonyms are missed.
