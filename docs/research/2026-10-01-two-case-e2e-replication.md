# Fresh E2E replication of one null and one positive omission case

On 2026-10-01, two previously qualified A/B/C cases were collected again from
new provider calls and executed in the qualified, network-disabled browser
image. This is an **exploratory replication of two existing requirements**, not
two new requirements, an ablation of contextual cues, or a confirmatory H1
estimate. The raw responses, HTML artifacts and full collection receipts remain
in private packets; public per-run browser reports and screenshots are linked
below.

| Requirement and omitted condition | A complete | B rewrite | C omission | New local result |
| --- | ---: | ---: | ---: | --- |
| RealWorld Favorites must list articles favorited by the profile owner | 6/6 pass | 6/6 pass | 6/6 pass | No observed target defect; all six A/C comparisons tie in success. |
| OpenProject must reject an invalid Remaining work value on Save | 6/6 pass | 6/6 pass | 6/6 target-only failure | The omitted obligation again coincides with a browser-visible target defect in all six A/C comparisons. |

Each cell pools three replications of each of `gpt-5.6-luna` and
`gpt-5.6-sol`. The schedules and exact request bytes were frozen before the
new calls. The collectors made 18 sequential calls per case, without retry,
API-key fallback, response repair or browser execution during generation. All
36 outputs were admitted and evaluated; there were no missing or unknown
outcomes in these two packets. The local qualified image and Codex executable
hashes match their respective September pilots. The provider does not expose
an exact model snapshot through this CLI.

The [RealWorld public packet](../../data/e2e-replications-20261001/realworld-favorites/summary.json)
and [OpenProject public packet](../../data/e2e-replications-20261001/openproject-invalid-remaining/summary.json)
contain all 36 outcome rows, report hashes, screenshot hashes, the frozen and
collection receipt hashes, and executable/image identities. Each packet has
18 browser JSON reports and 36 PNGs. A SHA-256 inventory in its `receipt.json`
checks the public files. The private collection inventories also verified
after execution.

The new provider responses are not a replay of the September files: only
1/18 RealWorld and 2/18 OpenProject raw responses had the same SHA-256 as
their matching previous slot. This is a check of byte differences, not a
claim that the model snapshot changed. The September and October outcomes
agree at the category level for both requirements.

These results strengthen **within-case reproducibility** of one null and one
positive contrast. They do not identify why RealWorld C succeeded: the page
still exposes `favoritedBy` and the Favorites route, and no cue was removed in
this replication. The six repeated runs per case share a requirement,
scaffold and oracle; they are not six independent requirements. The two cases
must remain separate from the 60 historical old/new pairs and the 18 excerpt
successors. No natural requirement-smell mapping or severity label was
independently adjudicated here. H1 and H2 therefore remain unconfirmed.
