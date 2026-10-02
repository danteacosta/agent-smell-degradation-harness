# Test-anchor: requirements given to the test writer matter locally

The local run completed **81/81 tester calls with 81 valid suites** and **180/180 browser suite/artifact evaluations**. The requested tester model was `gpt-6-astra`, through saved ChatGPT Codex authentication, with no retry or API-key fallback. The CLI does not expose a pinned response-model snapshot. The study reused 36 A/C interfaces from three October replication packets: 11 target failures and 25 target passes, representing **three requirements**, not 36 independent requirements. No new H1 implementation was generated.

Tests written from the implementation and its received request (`code_request`) detected **0/11** known target failures. Tests written from the implementation and the complete requirement (`code_spec`) detected **11/11**, all by explicit assertion failure. Tests written from the complete requirement and scaffold (`spec_only`) alarmed on **33/33** evaluations of the same 11 failures, using three suites per case. Of those alarms, 18 were assertion failures on OpenProject and 15 were timeouts waiting for a third document on Paperless. This is a behavioral difference in two requirements with known target failures; RealWorld had no such failures and contributes only target-pass observations.

## Frozen result and separate diagnostic

The original generic runner served only the exact root URL. Every RealWorld suite navigated to a legitimate profile route, which it aborted. The three authored OpenProject controls had passed, but they did not qualify deep navigation. Thus all 60 RealWorld evaluations originally errored before assessing their journeys. The original packet, suite code, results and receipt remain unchanged. Its alarm rates on previously passing artifacts were 13/25, 12/25 and 36/75 for the three strategies, respectively; these totals include the known routing defect and must not be presented as a valid estimate of test quality.

A new authored same-origin deep-route control reproduced the defect on a correct implementation. The corrected runner serves the frozen HTML for navigation within the exact `http://localhost` origin, preserving the CSP and blocking subresources and other origins, including a deceptive `localhost.evil.invalid` host. All three category expectations passed with the added deep-route and external-origin checks. The repaired runner replayed the **same 81 suites against the same 36 interfaces** in a separate 180-pair, browser-only diagnostic. It made **zero additional tester calls** and did not replace the original result.

| Tester inputs | Known target failures alarmed, diagnostic | Alarms on previously passing artifacts, diagnostic |
| --- | --- | --- |
| Implementation + received request | 0/11 (0%) | 5/25 (20%) |
| Implementation + complete requirement | 11/11 (100%) | 5/25 (20%) |
| Complete requirement + scaffold | 33/33 (100%; 11 interfaces × 3 suites) | 4/75 (5.3%) |

All planned pairs were executable, so intention-to-test and usable-only rates coincide. The detection counts are unchanged from the frozen result; the routing repair changes the target-pass alarm counts. The table is **post hoc diagnostic evidence**, not a new prospectively qualified generation run.

## What the remaining alarms mean

All 13 remaining RealWorld alarms across strategies concern Bob or another profile username. The frozen scaffold fixes `owner='alice'`, the displayed profile name and navigation links to Alice. The earlier qualified oracle tested Alice's authored-versus-favorited list, not arbitrary profile owners. These alarms are outside that bounded oracle's scope; they are counted as false alarms relative to its target labels by the registered analysis, but do not establish genuine defects in the generated behavior or a generally applicable false-positive rate. The tester's broader source requirement and this fixed scaffold need an explicitly agreed scope in any future collection.

The remaining Paperless `code_request` alarm is different: a suite expects an upload with identical content to leave two documents and create no copy. Its C interface actually creates the copy and passes the complete-reference oracle. This illustrates a test reproducing the incomplete request's interpretation and then rejecting a compliant implementation. The suite is preserved as generated; it was not repaired.

For the two cases with known target failures, the diagnostic breakdown is:

| Case | Implementation + request | Implementation + complete requirement | Complete requirement + scaffold |
| --- | --- | --- | --- |
| OpenProject remaining-work bound | 0/6 detected; 0/6 target-pass alarms | 6/6 detected; 0/6 target-pass alarms | 18/18 detected; 0/18 target-pass alarms |
| Paperless duplicate consumption | 0/5 detected; 1/7 target-pass alarms | 5/5 detected; 0/7 target-pass alarms | 15/15 alarms by timeout; 0/21 target-pass alarms |

The registered prediction that specification-only tests detect more failures than tests given code plus the complete specification **was not supported**: both alarmed on every known target failure. Specification-only tests had fewer out-of-scope alarms in this diagnostic, but the remaining scope mismatch limits that comparison. The contrast with an incomplete received request was expected by construction; this run quantifies that local blind spot.

## Custody and interpretation

The [public packet](../../data/test-anchor-20261002/README.md) includes all 81 generated suites, the original and diagnostic results, all 360 browser reports, schedule, frozen prompt hashes, control outcomes and a public receipt. Original private packet: **1,374/1,374** file hashes verified. Diagnostic packet: **722/722** verified. The [custody record](../../data/test-anchor-20261002/custody.json) binds both result/receipt hashes and runner versions. All reports' artifact hashes and suite hashes matched; every report completed with one to eight tests. CLI capture streams and private implementation/prompt files are not in the public export.

The packets were found by both published frozen and collection receipts after the original locator proved ambiguous: September pilots and October replications reused the same freeze. That issue stopped the first command before any tester call and was corrected in [PR #130](https://github.com/danteacosta/agent-smell-degradation-harness/pull/130). The running generation used explicit verified packet paths and the original script at `2c4cdca`; its frozen bytes were preserved.

The result supports keeping an independent complete reference available to QA in this bounded setting. It does not confirm general H1, estimate prevalence, or test H2's B0/B3 provenance comparison. Repeated generated suites and implementations are nested in three cases, and the tester and implementation models share one provider family. The next admissible study must freeze a runner qualified for each case's navigation and an explicit common journey scope before tester generation; broader H1 labels and the separate H2 holdout comparison remain pending.
