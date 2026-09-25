# RealWorld article-author admission and prompt freeze

This reviewed packet approves the RealWorld article-author case for the next
execution-freeze preparation step. It binds the qualified browser instrument
to exact source, rights custody, A/B/C prompt bytes and a deterministic
18-position schedule. It makes no provider call and does not freeze the
collector executable or its runtime configuration.

The bounded endpoint status is
`admitted_bounded_exploratory_endpoint`. The prompt packet records
`prompts_and_bounded_endpoint_frozen_not_execution_ready`. The independent
review decision is `approved_for_execution-freeze_preparation`, by
`codex-agent-independent-admission-review-20260925`. This approval covers source
fidelity, semantic preservation in B, the single deletion in C, common-interface
separation and the balanced schedule. There are zero human approvals.

## Source and manipulation

The preserved source is
`docs/src/content/docs/specifications/frontend/routing.md` from
`realworld-apps/realworld` at revision
`ebbcdeb8d55b42a3a613c787560498b8ef10003f`. Its SHA-256 is
`65fbd975a3ab2021057b1c1944cf66418aa846039e51b166d2a98eb29e7169fb`.
The exact source line contains A:

> Delete article button (only shown to article's author)

The reviewed variants are:

- A: `Delete article button (only shown to article's author)`
- B: `Display the Delete article button only to the article's author.`
- C: `Delete article button`

C removes exactly ` (only shown to article's author)` once from A. B is the
approved minimal meaning-preserving rewrite.

Every arm receives the same interface bytes. The generated artifact must be
self-contained raw HTML with vanilla JavaScript and no external resources. It
consumes the qualified instrument's `window.initialState`, renders the fixed
`/article/bounded-ui-case` page, title and body, and places the article author's
visible username in `[rel~="author"]`. A Delete Article control, if implemented,
must be an accessible button with that exact accessible name. Layout, styling
and internal representation remain open. Requests contain no source URL,
variant or target label, omission annotation, oracle, or expected verdict.

## Qualification custody and scope

The packet binds these already qualified artifacts:

- instrument SHA-256: `526a2aee0264ac81e4c318ad6b9c58d968113bae7dc41d776d40b3500112434e`;
- qualification-manifest SHA-256: `cf5baf358bc64914f16e1023eb48f34d73c9034127d9b02079dcfe8f4006a820`;
- CI artifact archive SHA-256: `2b2b301f21838d515e2ea56636425d0c50f81ae14d73b7f0ba607b9890b368d8`.

The preserved RealWorld MIT license is bound at revision
`ebbcdeb8d55b42a3a613c787560498b8ef10003f`, with SHA-256
`a999311c4ccfecf18b7c7beb7a7a31682bb009839ab3827164fa2f8c333fc9dd`.

The endpoint measures only whether the Delete Article button is perceptible to
the article author and not perceptible to crossed non-author viewers. Clicking,
backend authorization and article deletion are outside scope.

## Frozen prompt artifacts

Seed `20260925` deterministically shuffles A/B/C × `gpt-5.6-luna` and
`gpt-5.6-sol` × three repetitions. The schedule contains 18 unique opaque slot
IDs. Each per-slot request file contains only a `prompt` string.

The reviewed directory is
`data/behavioral-expansion/realworld-author-ui-admission-20260925/`.
At creation time its principal hashes were:

- manifest: `d6734a0265e313da350050cac26874a338b29bf9d6e81b54408dd863579f7cee`;
- independent review: `659c56629edea07eb39e4014d09df315650a413026ac70d4e7c4920d1307aee1`;
- prompt bundle: `d09dc61950d64987d06b294a44acd2296296cf58be87ff4772c39ecdd5876859`;
- schedule: `a57ac56dfcf9a4dd7e96c15e4489874427ed7e7712b1c78fe28d23fdf6b79363`;
- receipt: `bd7a3a13a8f5c481df0908848846f6e4bb644bf52653c128ac532742357f1a0d`.

`scripts/realworld_author_admission.py` reconstructs and validates the package,
rejects preserved-source drift and refuses to overwrite an existing packet. Its
materialized validator compares the prompt bundle, schedule and every request
against canonical reconstructed bytes before checking declared hashes, so a
self-consistent rewritten receipt cannot authorize altered inputs. Changing any
reviewed byte requires a successor packet and a new review.

## Leakage boundary and remaining gate

The common interface necessarily reveals the viewer and article-author
identities, their semantic author relation and the accessible Delete Article
control. The reviewer accepted this bounded residual risk because those
feasibility cues are byte-identical across A/B/C and contain no expected
ownership verdict.

A later step must separately freeze the collector executable, configuration,
browser/runtime bytes and per-request isolation, then verify capacity and
custody. This approval does not authorize dispatch. The packet supplies no
outcome, does not increase the number of projects with collected E2E evidence,
and supports neither H1 nor H2.
