# Paperless barcode retention: controlled A/B/C browser pilot

This exploratory pilot tests one omitted obligation in a reconstructed Paperless document-splitting interface. It is **not** one of the historical old/new pairs, full Paperless PDF ingestion, an independent confirmation of a natural requirement smell, or a population-level H1 test. The 10-change [source triage](2026-10-01-historical-blind-review-protocol.md) motivated selection after outcomes were known, so selection is outcome-informed.

## Contract frozen before generation

- A says the separator is discarded by default and, with `PAPERLESS_CONSUMER_BARCODE_RETAIN_SPLIT_PAGES`, becomes the first page of the next document. B states the same rule in different words. C is byte-for-byte A with only that retain-on sentence removed.
- A fixed browser page accepts a generated `app.onSplit` JavaScript callback. The browser checks retention on, retention off, and no separator using visible document cards and status text. Expected retention-on output for `Invoice, PATCH-T, Receipt, PATCH-T, Contract` is `[Invoice]`, `[PATCH-T, Receipt]`, `[PATCH-T, Contract]`. The retention-off control expects `[Invoice]`, `[Receipt]`, `[Contract]`.
- Two Codex CLI model aliases (`gpt-5.6-luna`, `gpt-5.6-sol`), three repetitions, randomized A/B/C schedule, one attempt per slot, separate ephemeral contexts and saved ChatGPT authentication: 18 generations. No API key was supplied. Model snapshots are not exposed by the CLI.
- Seven browser controls passed before generation: correct, always discard, retain in the prior document, always retain, missing UI, duplicate UI and runtime error. The frozen runner used a pinned Chromium Docker image. All generations finished before browser observation. Browser, interface and non-target failures remain unknown for the isolated target comparison.

The private frozen source, prompts, schedule, CLI and image metadata, 18 responses, HTMLs, browser reports and PNGs are sealed. V3's pre-generation frozen receipt is `cdf903a999ede12ecb8a8bb6ec1012dff4674e214defe0cfafe6b6a8f7b5b178`; all 377 post-run file hashes verified. The targeted failed screenshot is `retain-on.png` for slot `82b296804ffd338a3e7a6b41`, SHA-256 `bda0ae3134988c913010cfc301cafaedf6975e858406ce774ed30150141f6b70`; it visibly shows three imported documents without either `PATCH-T` separator. The retained screenshot and report hashes can be checked against the private seal.

## Why there are two separately preserved runs

In the first frozen 18-generation run (v2), the shared prompt left the meaning of its boolean parameter ambiguous. All six C generations treated it as the **split enabled** switch: they failed both retention on and the retention-off control. A/B/C comparison was therefore unknown in all six triplets. Its frozen receipt is `ddf03657bdb36c30e6a671f4a6cf02c9d56457b0890b2403c6a1bb358974996b`. V2 was sealed and never relabeled or replaced.

V3 prospectively clarified, in the common prompt for every arm, that document splitting itself was already enabled. It did **not** explain the boolean as separator retention. A, B, C, browser oracle and schedule otherwise stayed the same. The Boolean still cues that some option exists, so a model can recover the omitted condition.

## V3 observed results

All 18 generations produced admitted HTML. The browser results by arm were:

| Arm | Pass | Target-only failure | Non-target-only failure | Browser error |
| --- | ---: | ---: | ---: | ---: |
| A, complete | 5 | 0 | 1 | 0 |
| B, rewrite | 6 | 0 | 0 | 0 |
| C, omission | 3 | 1 | 0 | 2 |

Of the six model/repetition triplets, **one** had A/B pass and a C target-only failure (Luna repetition 2), **two** were three-way passes (Sol repetitions 1–2), and **three** were unknown under the frozen comparison rule (Luna repetitions 1 and 3; Sol repetition 3). In the failed C browser screenshot, the separator pages disappeared although retention was on; retention-off and no-separator controls passed. The two C browser errors were generated callbacks returning invalid groups, not a demonstrated browser-origin malfunction. The Sol repetition 3 A artifact failed the retention-off control. None of those three unknown triplets is counted as degradation or success.

The result is a **local, model-dependent signal**: removing the retain-on sentence coincided with an isolated observable defect once, while Sol still satisfied the obligation in two fully evaluable comparisons. It does not establish that Paperless's historical old text was a literature-defined smell, that omission generally worsens output, or that H1's ordinal quality criterion is met. The unit is one requirement; repetitions are nested observations. The next confirmatory step needs independent review of the historical mapping, multiple prospectively selected requirements and independent ordinal labels. H2 remains untested here.
