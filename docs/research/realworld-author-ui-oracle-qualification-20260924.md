# RealWorld article-author UI oracle: CI qualification

Status: **qualified on authored controls; no study case admitted and no model
output collected**. The pinned RealWorld obligation is:

> Delete article button (only shown to article's author)

The source is the maintainers' [frontend routing specification](https://github.com/realworld-apps/realworld/blob/ebbcdeb8d55b42a3a613c787560498b8ef10003f/docs/src/content/docs/specifications/frontend/routing.md)
at revision `ebbcdeb8d55b42a3a613c787560498b8ef10003f`. Its preserved raw
SHA-256 is `65fbd975a3ab2021057b1c1944cf66418aa846039e51b166d2a98eb29e7169fb`.

## Contract and result

The browser oracle crosses two article fixtures with two viewers in four fresh
contexts: Alice viewing Alice's article, Bob viewing Alice's article, Bob
viewing Bob's article, and Alice viewing Bob's article. It evaluates the exact
target assertion IDs `author_sees_delete_article` and
`non_author_does_not_see_delete_article`. Route, title, body and the article
author identified by a perceptible `[rel~="author"]` element are measurement
prerequisites. A missing prerequisite makes the dependent target assertion not
evaluable rather than failed.

CI reproduced the complete declared matrix:

| Evidence class | Exact outcome |
| --- | --- |
| Passing references | 8/8 |
| Target mutants discriminated | 7/7 |
| Expected not-evaluable controls | 4/4 |
| Operational diagnostics | 2/2: one `interface_failure`, one `browser_failure` |
| Screenshots | 76/76 present, valid PNG, 1000 x 720, and hash-matched |

All 19 HTML cases had exact expected/observed vectors, complete reports and
exact receipt fields. The two operational cases had their exact expected
status, browser-started state, return code and category, without screenshots.
The qualification manifest records `qualified:true` and
`matrix_matches:true`.

## CI and custody

The successful [workflow run 36027518118](https://github.com/danteacosta/agent-smell-degradation-harness/actions/runs/36027518118)
and [qualification job 107727703132](https://github.com/danteacosta/agent-smell-degradation-harness/actions/runs/36027518118/job/107727703132)
were triggered for pull-request head
`b12b25a4b445d90b704e78fa17e044bd38f3351f`. GitHub Actions checked out the
synthetic pull-request merge commit
`750fdda8b6ff6037437de8e5397a54d276cd5202`, whose parents are base
`9eb9d69952d36cf230fe25eedd8466a60da96f22` and that exact head. The
qualification and build receipt correctly bind to the checked-out merge
commit. A direct tree comparison found no differences in the 31 hashed
instrument files between the pull-request head and qualified merge checkout.

The immutable image ID is
`sha256:7bad7454229a355ebedef92678d540778aa2cc9c3ebfb281d0455e874aa0dd59`.
The recomputed canonical instrument SHA-256 is
`18a1c3d32cccd26c896f3539b6a776034be3ab82a35bfb79996d5e78bfb68e11`.
The build receipt and qualification manifest agree on both the image ID and
instrument digest. The `image-id` file and every executor receipt agree on the
image ID; the `instrument-digest` file agrees on the instrument digest.
Commit-mode qualification also inspected the OCI label
`org.opencontainers.image.realworld-instrument-sha256` and required it to equal
that digest before any control ran, binding the verified image to the verified
instrument bytes.

GitHub artifact `10820860904`, `realworld-author-ui-qualification`, was 666,453
bytes when uploaded. GitHub reports archive digest
`sha256:8627c7405c70112cad0bc82205989d536edd359938adc231aa4bb3e3b4979a65`.
The independently downloaded payload contains exactly 185 files: three
top-level custody files, one qualification manifest, 21 inputs, 21 reports, 21
receipts, 21 container commands, 21 logs and 76 screenshots. No unlisted or
missing file was found. The recomputed qualification-manifest SHA-256 is
`a56fc961fdf8bfe509890a802f8fa906479afc267fe868e424226fdd989d0358`.
Every manifest report, receipt and screenshot hash was recomputed; every input
hash matched both its browser report and executor receipt; and all 31 manifest
instrument hashes matched the committed files.

The report hashes below follow the qualification manifest's canonical order.
They cover all 19 HTML cases followed by both operational diagnostics.

| Case ID | Report SHA-256 |
| --- | --- |
| `reference-explicit` | `af92417e52ddbc3a1eb644eb60e5b75a198ca37768f069c531c7985a6b11a451` |
| `reference-derived-hidden` | `3c0442d863e69cf3d965103e4f8715dd8514eb88029fdd4aeae9b150adb78e2a` |
| `reference-two-buttons` | `8ece36a1f7345f362d6241197109e87e3a734bf93b02b0001fd4235c5f2ca061` |
| `reference-transparent-nonauthor` | `d069c68acd4e7e65292536e197dccbbb5eb571ee25f21d4655e6e34ad4d35765` |
| `reference-partial-occlusion` | `c1c77a4c1513c8dc6db853d84ce7a5232a49089cd8016e7fbba3d359982dcdb2` |
| `reference-pointer-events-button` | `a839c872a2e888de1aaa9f53adc75cb39712304ee7713a2536ba6f204a848809` |
| `reference-pointer-events-prerequisites` | `058de271b169705d4135b516d37b78f768f3e51d5f4184adab4911293c4ad275` |
| `reference-fresh-context` | `7f1c103ea6791d168cdd6e763d30236701cc5e4e536874e2cdd137def72ed497` |
| `mutant-always-visible` | `f2108e1bf09e08193a6c7d3922b5a5be5aab556081e00349e20dec0a46b629c3` |
| `mutant-never-visible` | `6704498676d27c9ba224f279ef95771fac6a6d3f04c8dcec8e6abf91cee8e686` |
| `mutant-wrong-identity` | `b396c1687089fc1536eedbd8ad2af86a30e6f34a1707ec6a6d08a90aea0705a3` |
| `mutant-hardcoded-alice` | `ee1cbca1d986ef684fd38403afe96372a0f932b2996e5511f187c429cb83574a` |
| `mutant-transparent-author` | `442aea26eb6023098f5d9c50ad6ebbab278567a3b2f685345a91c48bd2c75f24` |
| `mutant-visible-and-transparent-nonauthor` | `01aa87bc899bd8d8262cba81093c82b5d15fc0c97f81e60b59237532175bfc38` |
| `mutant-fully-occluded-author` | `a47e433fef50c44c8da523dbf779d31769e4e4db6dc027d1c54498e9ff565717` |
| `control-broken-article` | `c5ca3646eec9f7c7a4651220cc1bfaea9fcdd98457b6b174a0cc7f411ba378bd` |
| `control-mixed-evaluability` | `6677529c9954fc64f57481d069fc5d302f679085e458da16c14317dd9f5ae572` |
| `control-viewer-only-author-text` | `aaa85ea47a77945c65a329aa2aba9c798d6a3bdabfb40a4bbb1bb0cf3a481929` |
| `control-hidden-author-text` | `9dee86534a7197c67bcbae9d78e2c4f814caed288f89a9374fbb23f5497f3679` |
| `operational-invalid-interface` | `d6418389a80df1f49c060afd1b08cf0698435a283d2ce2de09deec622ec310e6` |
| `operational-browser-failure` | `2cbd6c968307e6e5ff0491809396e4e9e8f6e125d31ff63732bd5cac074148b0` |

The runtime was Playwright 1.58.2 with Chromium `145.0.7632.6`, a 1000 x 720
viewport and a fixed 5 x 5 inset sampling grid. Each fixture/viewer pair used a
fresh browser context in a non-root, offline, read-only, capability-dropped,
resource-bounded Docker container. Chromium reported
`browser_sandbox:false`; this state is explicit rather than treated as a
browser-escape guarantee.

## Direct screenshot inspection (31/76)

This qualification review selected a representative 31-file visual sample by
taking all four contexts for the explicit reference and hardcoded-Alice mutant,
then targeted author/context frames for multiplicity, transparency, partial and
full occlusion, pointer-events, broken and mixed pages, viewer-only author text
and hidden authorship. This was a coverage-directed review sample, not a
preregistered or random sample. The following artifact screenshots were
inspected directly. Paths are relative to `qualification/`; hashes were
recomputed from the inspected files.

| Screenshot | SHA-256 |
| --- | --- |
| `reference-explicit/output/article-alice-author.png` | `f06a3d147c3df6d0ecca7824f56990ce19bf483825f4ffe94f98318664933514` |
| `reference-explicit/output/article-alice-non-author.png` | `9c3084e33066a5cd93986b992b5274e7ba16095fe09ce60bad980f783b658595` |
| `reference-explicit/output/article-bob-author.png` | `14623b516f665a71ebf02cefcba5148022e94383f72099965b31cbd1f6dd719e` |
| `reference-explicit/output/article-bob-non-author.png` | `981f3f5ace18976e8fd1ba9c4bfe2c59cd14abccf38701353b23b571041223fc` |
| `reference-two-buttons/output/article-alice-author.png` | `fbce65177682382fb29430b5983a7e744e3eb93dfe95a06b9093229f01f59c4d` |
| `reference-transparent-nonauthor/output/article-alice-author.png` | `cbb75f2c49819b5d718a1b29565584105b19b818d4540f3dc9b6731ecc83cd50` |
| `mutant-transparent-author/output/article-alice-author.png` | `f3de1eb6659b433abf3c937f9f0ff05be722e6ea6ba8ea152a4d7797f1ca44bf` |
| `reference-partial-occlusion/output/article-alice-author.png` | `d8230e825e1f9a65f58cdaf35dd62d100a88f2d88185f401307cce13d33fca71` |
| `reference-pointer-events-button/output/article-alice-author.png` | `cbb75f2c49819b5d718a1b29565584105b19b818d4540f3dc9b6731ecc83cd50` |
| `reference-pointer-events-prerequisites/output/article-alice-author.png` | `670cd1f8daf032afcf8d56d0a2152c36de59e421ed5b7548e71076a7f8338de0` |
| `mutant-fully-occluded-author/output/article-alice-author.png` | `38b62c94ff65e3e9540bfad516c1d16ded38340458580603a50004016af06937` |
| `mutant-hardcoded-alice/output/article-alice-author.png` | `e0dd9ba5fc17a69c2c884e582af6bd428a7002457862e44ef32eaee859c7c4e6` |
| `mutant-hardcoded-alice/output/article-alice-non-author.png` | `79ea30d3235becd0dd36ee41fbdf3b1e71fcc661e0cd40b1a337e4c1929c4f40` |
| `mutant-hardcoded-alice/output/article-bob-author.png` | `3a23e4f2e6a239a75e3642eb3a3baa2d0e06059fa47d06a8c24bd72a5443b2f0` |
| `mutant-hardcoded-alice/output/article-bob-non-author.png` | `a9b656947778cf4429d271f0ad6136c2790599dd747873871f0a90869930d094` |
| `control-broken-article/output/article-alice-author.png` | `498349626712591c6fc1cdc1befe67ad296a900f9521bc3ca950ce43ed9ff260` |
| `control-broken-article/output/article-alice-non-author.png` | `6bac3f5753d0bfa9237aeefbb25abc2afa640f034e64694ba2aeadad17da08f2` |
| `control-broken-article/output/article-bob-author.png` | `7d118051bc84bbbc00cad0266c0f9d0a76a3098f7f83af665ccc6759a95bc06a` |
| `control-broken-article/output/article-bob-non-author.png` | `999cb67de18c3038fe5de8a68d092e0977d30c6e386343ef3ab80a828cc769ad` |
| `control-mixed-evaluability/output/article-alice-author.png` | `e0dd9ba5fc17a69c2c884e582af6bd428a7002457862e44ef32eaee859c7c4e6` |
| `control-mixed-evaluability/output/article-alice-non-author.png` | `79ea30d3235becd0dd36ee41fbdf3b1e71fcc661e0cd40b1a337e4c1929c4f40` |
| `control-mixed-evaluability/output/article-bob-author.png` | `7d118051bc84bbbc00cad0266c0f9d0a76a3098f7f83af665ccc6759a95bc06a` |
| `control-mixed-evaluability/output/article-bob-non-author.png` | `a9b656947778cf4429d271f0ad6136c2790599dd747873871f0a90869930d094` |
| `control-viewer-only-author-text/output/article-alice-author.png` | `79d1583e3797a5e3e87c95662c309d42558f57bd431481de1b876812957a59cf` |
| `control-viewer-only-author-text/output/article-alice-non-author.png` | `da4d83b34d67918e17a19dc064b93e89fd64a8d37b71abf23944dee90ddefff8` |
| `control-viewer-only-author-text/output/article-bob-author.png` | `080101c0ea798c0363a63492bd9d9d15914b4f89f2ece8b49f92dfca8868c455` |
| `control-viewer-only-author-text/output/article-bob-non-author.png` | `4e8a678a4e4bce9552f7fc5b5ff0ad1590b6b422416cf726d350ccd4731cf6e4` |
| `control-hidden-author-text/output/article-alice-author.png` | `41a514f4945c53c39363a6154b1d5b0d999a306594a43fbcc03e7e805935f3ed` |
| `control-hidden-author-text/output/article-alice-non-author.png` | `4df5d2887f2fa5446efef52dfe16c79c1a31296cc34ea6ea3f111d8aa986ff28` |
| `control-hidden-author-text/output/article-bob-author.png` | `41a514f4945c53c39363a6154b1d5b0d999a306594a43fbcc03e7e805935f3ed` |
| `control-hidden-author-text/output/article-bob-non-author.png` | `4df5d2887f2fa5446efef52dfe16c79c1a31296cc34ea6ea3f111d8aa986ff28` |

The four explicit-reference images show a delete button only in the two author
contexts, matching structured delete counts `1/1`, `0/0`, `1/1`, `0/0`
(`matched/perceptible`). The two-button reference visibly has two controls and
reports `2/2`. The transparent-author and fully occluded mutants leave a matched
button that is not perceptible (`1/0`); partial occlusion remains perceptible
(`1/1`). Both pointer-event cases preserve perceptibility (`1/1`), as specified
by this visual predicate.

Across all four hardcoded-Alice images, the button follows the crossed identity
incorrectly: visible for Alice as article author, absent for Bob viewing
Alice's article, absent for Bob as article author, and visible for Alice viewing
Bob's article. Structured counts are respectively `1/1`, `0/0`, `0/0`, `1/1`,
so both target assertions fail. Every broken-article image lacks the article
body. The mixed control lacks the body only for Bob's author context while its
Bob non-author context exposes a button, preserving one not-evaluable target
and one target failure. Viewer-only images visibly repeat usernames outside the
semantic author relation but report article-author `0/0`; hidden-author images
show only “Written by” and report matched/perceptible article-author `1/0`.
These comparisons agree with the closed structured observations.

Screenshots are diagnostic records, not the source of verdicts. The structured
browser observations and the Python classifier determine each result.
The remaining 45 screenshots received automated PNG-signature, 1000 x 720
dimension, canonical-filename and SHA-256 validation only; they were not part
of the direct visual review.

## Audit and reproduce

The authenticated [artifact download](https://github.com/danteacosta/agent-smell-degradation-harness/actions/runs/36027518118/artifacts/10820860904)
expires at `2026-10-24T16:29:48Z`. Download the exact artifact and verify its
qualification hash, flags and 185-file denominator with:

```bash
set -euo pipefail
artifact='/tmp/realworld-author-ui-ci-36027518118'
test ! -e "$artifact"
gh run download 36027518118 \
  --repo danteacosta/agent-smell-degradation-harness \
  --name realworld-author-ui-qualification \
  --dir "$artifact"
(cd "$artifact" && printf '%s  %s\n' \
  'a56fc961fdf8bfe509890a802f8fa906479afc267fe868e424226fdd989d0358' \
  'qualification/qualification.json' | shasum -a 256 -c -)
jq -e '.qualified == true and .matrix_matches == true' \
  "$artifact/qualification/qualification.json"
test "$(find "$artifact" -type f | wc -l | tr -d ' ')" = 185
```

From the repository root, this command verifies that the report table above is
identical to the manifest's canonical case order, recomputes each report hash
against both, and recomputes every screenshot signature, dimension and hash
against the manifest:

```bash
set -euo pipefail
artifact='/tmp/realworld-author-ui-ci-36027518118'
python3 - "$artifact" \
  docs/research/realworld-author-ui-oracle-qualification-20260924.md <<'PY'
from pathlib import Path
import hashlib
import json
import re
import struct
import sys

artifact = Path(sys.argv[1])
document = Path(sys.argv[2]).read_text(encoding="utf-8")
manifest = json.loads(
    (artifact / "qualification/qualification.json").read_text(encoding="utf-8")
)
section = document.split("| Case ID | Report SHA-256 |", 1)[1].split(
    "The runtime was", 1
)[0]
table = re.findall(
    r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", section, re.MULTILINE
)
rows = manifest["cases"] + manifest["operational_cases"]
expected = [(row["id"], row["report_sha256"]) for row in rows]
assert len(expected) == 21
assert table == expected

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for case_id, expected_hash in expected:
    report = artifact / "qualification" / case_id / "output/report.json"
    assert sha256(report) == expected_hash
screenshots = [
    (row["id"], name, expected_hash)
    for row in rows
    for name, expected_hash in row["screenshot_sha256"].items()
]
assert len(screenshots) == 76
for case_id, name, expected_hash in screenshots:
    image = artifact / "qualification" / case_id / "output" / name
    raw = image.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", raw[16:24]) == (1000, 720)
    assert sha256(image) == expected_hash
print("21 reports and 76 PNGs verified")
PY
```

The exact qualified checkout is
[`750fdda8b6ff6037437de8e5397a54d276cd5202`](https://github.com/danteacosta/agent-smell-degradation-harness/commit/750fdda8b6ff6037437de8e5397a54d276cd5202),
and the qualification definition is the pinned
[workflow](https://github.com/danteacosta/agent-smell-degradation-harness/blob/b12b25a4b445d90b704e78fa17e044bd38f3351f/.github/workflows/realworld-author-ui-oracle-qualification.yml).
To rebuild the digest-bound image and rerun the qualifier in a clean detached
worktree:

```bash
set -euo pipefail
git fetch origin refs/pull/77/merge
test ! -e /tmp/realworld-author-ui-qualified
git worktree add --detach /tmp/realworld-author-ui-qualified \
  750fdda8b6ff6037437de8e5397a54d276cd5202
cd /tmp/realworld-author-ui-qualified
test -z "$(git status --porcelain)"
python3 scripts/dependency_bundle.py
evidence_root=$(mktemp -d /tmp/realworld-author-ui-rerun.XXXXXX)
instrument_digest=$(dependency-bundle/runtime/bin/python \
  eval/fixtures/realworld-author-ui/qualify.py --print-instrument-digest)
test "$instrument_digest" = \
  '18a1c3d32cccd26c896f3539b6a776034be3ab82a35bfb79996d5e78bfb68e11'
docker build \
  --build-arg "REALWORLD_INSTRUMENT_SHA256=$instrument_digest" \
  --iidfile "$evidence_root/image-id" \
  eval/fixtures/realworld-author-ui
dependency-bundle/runtime/bin/python \
  eval/fixtures/realworld-author-ui/qualify.py \
  --image "$(tr -d '\n' < "$evidence_root/image-id")" \
  --git-commit 750fdda8b6ff6037437de8e5397a54d276cd5202 \
  --output "$evidence_root/qualification"
```

No durable copy of the 185-file artifact is currently archived beyond
GitHub's 30-day retention. The committed hashes, pinned source and procedure
remain, but direct screenshot audit requires downloading before expiry or
rerunning the qualification.

## Current check state and limits

At `2026-09-24T16:35:50Z`, the qualification, constraint-replay and wedge
checks were green. The pull-request and push `eval-gate` jobs were still in
progress. Both later passed for head
`b12b25a4b445d90b704e78fa17e044bd38f3351f`: the
[pull-request eval job](https://github.com/danteacosta/agent-smell-degradation-harness/actions/runs/36027518035/job/107727702739)
completed at `2026-09-24T16:36:19Z`, and the
[push eval job](https://github.com/danteacosta/agent-smell-degradation-harness/actions/runs/36027511488/job/107727681268)
completed at `2026-09-24T16:36:50Z`. These checks qualify that code head; this
record's later documentation-only commits are distinct Git heads.

This qualification measures authored controls only. It does not establish
general sensitivity, specificity or completeness; establish requirement-smell
effects or smell causality; prove browser-escape safety; contain
provider-generated output; admit this case to collection; or add H1/H2
evidence. TodoMVC remains the only project with collected end-to-end evidence
until the prospective RealWorld A/B/C prompts, cohort, runtime and schedule are
reviewed, frozen and run.
