# OpenProject candidate boundary correction

Status: **prospective narrowing completed before oracle construction and A/B/C generation for this case**. No generated implementation or browser outcome was available to the reviewers.

A cross-candidate audit found that `openproject-reject-remaining-over-work` treated two independently deletable behaviors as verdict-bearing: visible error feedback and prevention of saving an invalid value. The frozen source documents both, but one implementation could satisfy either without the other.

The replacement `openproject-invalid-remaining-not-saved` scores only persistence. Given Work=8h and stored Remaining work=7h, the user enters 9h and attempts to save. After the UI settles and the page is refreshed, Remaining work must still be 7h. Work and successful reload are controls. The target makes no assertion about the presence, absence or wording of error feedback.

The first review wording called error feedback a control and received a 2–1 decision, so it was not admitted. After error feedback was removed from the contract entirely, three isolated configurations unanimously accepted the corrected boundary:

| Reviewer | Verdict | Evidence SHA-256 |
| --- | --- | --- |
| GPT-6 Astra | ACCEPT | `0e7942ed2b00c94a05d2b393dc0878b97192d16f7dd6aa516ad7cf663fa8fbc0` |
| GPT-6 Sol | ACCEPT | `f8a662dc2b2592929102c72bac45cd16c307e841bd362633df84b6d7faaff20a` |
| GPT-6 Luna | ACCEPT | `821df6144637840bb68b3d4b08e1b72562ae9a623b1c5ceeaf45d7d8fc9bd7ae` |

Final prompt SHA-256: `d51097b6d51578f657ccf53064038d25c65df1c575845dcae9f2da4e67e14af3`. Private custody manifest SHA-256: `6c190973770c8621dcf031e1b0d4a48342bc3e8813bc34efb9338c766504e3bf`.

The pool remains **12 eligible obligation slots across six projects**, two per project, with a ceiling of **216 positions**: 11 previously unexecuted obligations and one TodoMVC persistence bridge replication. The bridge does not add requirement diversity. This correction changes the identity and scoring boundary of one prospective OpenProject case. It produces no E2E result and adds no evidence for H1 or H2.
