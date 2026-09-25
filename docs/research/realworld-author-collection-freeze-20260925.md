# RealWorld article-author collection freeze status

The RealWorld article-author collector is implemented and covered by offline
provider/executor doubles. No real provider call or browser experiment was run
in this step, and no private execution packet has been declared as collected
evidence.

## Preparation boundary

Preparation accepts the reviewed PR79 admission packet only after its canonical
source, review, prompt bundle, schedule, requests and receipt validate. It then
requires:

- a fresh preflight recording ordinary-use permission, ChatGPT authentication,
  required CLI flags, image verification and isolation verification;
- an explicit Codex executable whose path, SHA-256 and reported version are
  frozen, and whose live `login status` reports ChatGPT authentication;
- an explicit immutable local image ID;
- a local `realworld-author-ui-qualification/v1` manifest with
  `qualified:true`, `matrix_matches:true`, the exact 20 scientific and four
  operational cases, that exact image ID, and instrument SHA-256
  `526a2aee0264ac81e4c318ad6b9c58d968113bae7dc41d776d40b3500112434e`;
- a new private destination outside the repository.

The current operator preflight identified
`/Applications/ChatGPT.app/Contents/Resources/codex` version
`0.155.0-alpha.16.4` as the ChatGPT-authenticated CLI. The global
`/opt/homebrew/bin/codex` version `0.3.0` is incompatible. A local linux/amd64
rebuild produced image
`sha256:ed4bc5071528d2340f1353d78adce12ba9a9993edffff97b1e89cbfb97ada441`
with the same instrument digest. Its successful local qualification manifest
has SHA-256
`98f4b6feec928291133187a2e9dfa4c83d08563d93671d584a30b139fb78f992`,
`qualified:true`, `matrix_matches:true`, and git-commit custody. `prepare`
recomputes the 34-file instrument digest, case observations, receipts, reports,
screenshots and closed 201-file evidence inventory before freezing those exact
manifest bytes. Minimal manifests, changed evidence and added or missing files
fail closed. This collection freeze also binds that exact qualification SHA-256
and local image ID as approved constants. A different image or qualification
requires a successor freeze.

Qualification custody may name an earlier commit after the collector itself is
committed. The validator requires that commit to exist, be an ancestor of the
current `HEAD`, have no committed differences from `HEAD` across the exact 34
instrument paths, and have no working-tree changes on those paths. A missing,
unrelated or instrument-changing commit fails closed.

The CI image
`sha256:bfa780d015f8549cd70f4ece4d48e2fa51a4d8399322661314001e564021f617`
and CI qualification manifest
`cf5baf358bc64914f16e1023eb48f34d73c9034127d9b02079dcfe8f4006a820`
remain separate provenance. The collector never substitutes that CI image ID
for a locally qualified executable image.

## Frozen execution policy

The private packet freezes the exact 18-slot schedule and request bytes, local
qualification evidence, complete Python and RealWorld browser runtime, CLI
identity and the following policy: sequential concurrency one, low reasoning
effort, maximum 18 attempts, ChatGPT subscription authentication, no API-key
fallback, retry, resume, output repair or normalization.

At run time all custody is validated before the durable run marker and first
provider attempt. Generation follows the frozen order exactly once. Every raw
response is retained; only an unchanged bounded standalone HTML document is
admitted. All generation ends before browser execution begins. Provider
infrastructure failure stops dispatch and leaves later positions
`not_attempted`; interruption leaves an attempt marker and makes the packet
non-resumable.

The browser phase uses `eval.realworld_author_ui_executor.execute` with the
locally qualified image. The collector maps admission `arm` to analyzer
`variant`, adds the fixed RealWorld intent/project identifiers and reports all
18 positions through `scripts.behavioral_expansion.summarize`. Operational and
invalid outcomes remain unknown rather than becoming target failures. A known
target failure remains a failure when a different target assertion in the same
artifact is not evaluable.

## Prepared private packets

The first packet,
`.private-research-evidence/realworld-author-collection-freeze-20260925-v1`
remains unexecuted and is superseded. Review found that it admitted a generated
`__pycache__` artifact, accepted an underspecified local-qualification manifest,
and did not enforce the complete frozen execution policy independently of its
self-consistent receipt. It must not be run.

Preparation then created
`.private-research-evidence/realworld-author-collection-freeze-20260925-v2`
with the generated-artifact and manifest-policy corrections. It remains
unexecuted and is superseded because review demonstrated that a semantically
altered qualification report could be rehashed consistently through the
qualification and packet receipts.

The next packet,
`.private-research-evidence/realworld-author-collection-freeze-20260925-v3`,
is also unexecuted and superseded. Its custody check required the qualification
commit to equal `HEAD`, which would make the packet unverifiable immediately
after committing the collector even when all qualified instrument bytes stayed
unchanged.

The current successor is
`.private-research-evidence/realworld-author-collection-freeze-20260925-v4`,
outside the repository with mode `0700`. It contains 185 frozen files: 160
source/runtime files, 18 requests and seven custody/control files. No
`__pycache__`, `.pyc` or run marker is present. Its frozen manifest SHA-256 is
`28279a032fb7118f33d47dfd8815b26b030f995f682ff603911541d1eee2354d`;
its frozen receipt SHA-256 is
`3ad5fa5f4244de8df0b00792c1bed0ca3512c2cf653de659ee385513b3b482f1`.
Post-write verification recovered all 18 positions, all 160 current runtime
bindings, exact approved local qualification SHA-256, and `provider_calls:0`.
It enforces the canonical manifest shape and values, so a resealed packet
cannot change local qualification, image, billing, call limits, output policy,
retry behavior or scientific-claim flags.

The preflight is intentionally time-bounded. If it becomes stale before an
authorized live run, v4 must remain unexecuted and a new successor freeze must
be prepared.

## Current claim boundary

This work validates collection mechanics with doubles. It reports no RealWorld
generation, E2E outcome, smell effect, H1 support or H2 support. Remaining risks
before a live run are the freshness and custody of the operator preflight, the
exact local qualification evidence, account capacity, and the provider's
unobservable internal transport behavior and model snapshot.
