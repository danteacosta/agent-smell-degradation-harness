# OpenProject Remaining work: post-outcome label audit

This is a **complementary, post-outcome** review of the 18 generated behavior
snippets from the [browser pilot](openproject-remaining-pilot-20260926.md).
The reviewers saw the source obligation, frozen scaffold, and anonymized
snippets. They did not see the A/B/C arm, generation model, or browser label.
The browser oracle remains the primary outcome; this audit does not replace
the pre-generation prompt review or an independent human review.

The first prompt did not show the exact `app.apply` behavior. `gpt-6-luna`
agreed with 11/18 browser labels and `gpt-6-astra` with 18/18. Luna called
seven cases `OTHER_FAILURE`, including five passing snippets that returned
only the derived field and two target failures. Its explanation assumed that
omitted returned keys erase the other saved values. The frozen scaffold
updates only returned keys. After this discrepancy was observed, the prompt
was revised to include that exact behavior. This revision is **post hoc**.

With the revised prompt, `gpt-6-sol` and `gpt-6-astra` each agreed with all
18 browser labels. `gpt-6-luna` agreed with 13/18 and labeled five passing
snippets (`s03`, `s06`, `s10`, `s14`, `s16`) as target failures, although its
own explanations say they derive 6 and 15 hours and preserve Work and percent.
Thus the revised panel has a 2/3 majority on every slot, but not unanimity.
The panel is not an independent, preregistered ground truth and does not
establish H1 or H2.

| Blinded slot | Arm | Browser | Luna v1 | Astra v1 | Luna v2 | Sol v2 | Astra v2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| s01 | C | target | target | target | target | target | target |
| s02 | B | pass | pass | pass | pass | pass | pass |
| s03 | A | pass | other | pass | target | pass | pass |
| s04 | C | target | target | target | target | target | target |
| s05 | B | pass | pass | pass | pass | pass | pass |
| s06 | B | pass | other | pass | target | pass | pass |
| s07 | C | target | other | target | target | target | target |
| s08 | B | pass | pass | pass | pass | pass | pass |
| s09 | C | target | target | target | target | target | target |
| s10 | A | pass | other | pass | target | pass | pass |
| s11 | B | pass | pass | pass | pass | pass | pass |
| s12 | C | target | other | target | target | target | target |
| s13 | A | pass | pass | pass | pass | pass | pass |
| s14 | A | pass | other | pass | target | pass | pass |
| s15 | A | pass | pass | pass | pass | pass | pass |
| s16 | B | pass | other | pass | target | pass | pass |
| s17 | A | pass | pass | pass | pass | pass | pass |
| s18 | C | target | target | target | target | target | target |

`target` means `TARGET_ONLY_FAILURE`; `other` means `OTHER_FAILURE`.
The mapping from blinded IDs to the public slot IDs, prompts, and raw reviewer
responses is retained in the private audit packet. SHA-256 commitments:

| Private file | SHA-256 |
| --- | --- |
| ID mapping | `636f3ccbcbdeaf050a9f7a0835d820ccddf4ae797c7e6e78891a74139b4c7d93` |
| Prompt v1 | `e9b12d66d83e00cc7286ad9a583a3cfe3994c363973eb8a3458eac00974b3873` |
| Prompt v2 | `99836c4293e8254fca5d4cd292fefefb6e540ba2e8080ab780339ad329c669a1` |
| Luna v1 | `e40ce3886d3186b0234438583e1050d6b210293c0e5c5939370868b792ee79dc` |
| Astra v1 | `239fca196171cbaae20edb9ada59e3c0544002324aec1d6aea3dfd214fb9af9d` |
| Luna v2 | `fa879b4ea55152fa13803033f878c6781697994d0a27b968778c818b1e16fde1` |
| Sol v2 | `a45b71a38f9f93fd4db5894c8a606661a3d03819b624abbff24cda923e6ebc24` |
| Astra v2 | `d413457a3d4d6eadf76883b4f99fb42d66b0735c5c5c9a006fcfb3b14d8a40a3` |

The audit explains the judge disagreement and leaves the frozen browser
outcomes unchanged. A human adjudication remains useful, especially for the
five contradictory Luna v2 labels and the post hoc prompt revision.
