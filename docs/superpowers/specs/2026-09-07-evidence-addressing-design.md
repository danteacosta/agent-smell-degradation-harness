# Artifact-addressed evidence: offline design

Date: 2026-09-07. Scope: a separately versioned, offline diagnostic contract.
The user approved both the direction and this written specification in the
research task before implementation. Review is inline, not independent.

## Problem and intended result

The [v3 development comparison](../../research/scoped-judge-results.md) failed
its frozen gate. Twelve responses exceeded the quote-length contract; two
quoted reference text absent from the artifact, with one overlapping response.
These observations motivate development, not retrospective rescoring.

An investigator should be able to resolve a judgment's cited evidence to exact
bytes of the artifact that the judge received. The result must distinguish
locator integrity, agreement with a construction answer, and semantic validity.
The first is mechanically testable. The last is not established by this design.

## Alternatives and decision

1. Use immutable artifact segment IDs. This removes quote transcription from
   the response contract and rejects evidence outside the supplied artifact.
   It changes the presentation of evidence and still permits irrelevant cites.
2. Raise the v3 quote cap. This is smaller, but cannot address reference-only
   citations and would require a new version rather than changing the old gate.
3. Add an entailment model. This introduces another uncalibrated evaluator,
   dependency, and possible inference cost. It is outside this offline step.

Implement option 1. The attribution literature distinguishes identified sources
from support judgments; the [research note](../../research/2026-09-07-evidence-attribution.md)
records the sources and the limited design inference.

## Contracts and ownership

- `label_plane/artifact_segments.py` owns a versioned snapshot and exact text
  resolution. Input is nonblank Unicode text of at most 20,000 code points,
  encoded as UTF-8 without normalization. Segments follow newline boundaries
  within a fixed 400-code-point window, splitting longer lines as needed.
  Whitespace, line endings, punctuation, and order are preserved.
- Each segment has a deterministic opaque ID and start-inclusive/end-exclusive
  byte offsets. Identity binds the policy version, full artifact SHA-256, and
  offsets. A different artifact must not accept stale IDs, even when a quoted
  phrase occurs in both. The hash is an integrity identifier, not an attestation
  of authorship or independence.
- A serialized snapshot is accepted only if it exactly matches a fresh
  derivation from its text, including field types. Resolution returns the
  original spans; it never searches the reference, retrieves a URL, or repairs
  a response. This is not an implementation of W3C Web Annotation conformance.
- `label_plane/addressed_judge.py` owns the experimental prompt and parser.
  The trusted caller supplies the existing item contract: criteria, reference,
  observation scope, and one to six obligations. The judge sees separate
  artifact segments and reference fields, without oracles or source identities.
- Output has exactly `checks`, with ordered `id`, `status`, and `evidence_ids`
  per obligation. Statuses retain the complete/partial-scope semantics of v3.
  Covered requires at least one nonblank artifact segment; omitted and uncertain
  may have no citation. Up to eight unique segment IDs per obligation are
  allowed, including multiple spans for distributed support. This is an
  operational bound, not a validated definition of sufficient evidence.
- The parser resolves all cited IDs against the current snapshot. An irrelevant
  but real citation may pass locator validation. Reports must expose that limit
  and must never label the parser result as semantic correctness.
- `eval/evidence_addressing.py` provides an offline audit of supplied JSON
  records and an explicit toy demonstration. The aggregate report includes
  attempted/valid/invalid counts, bounded error categories, status distributions,
  and optional construction agreement with its own denominator. Semantic
  validity is always `not_measured`; main collection is always unreleased.
  Raw text, IDs, hashes, responses, paths, and exception messages are absent
  from the public report. No provider adapter or budget ledger is invoked.

Pure functions are sufficient. No new framework, external model, storage layer,
or design-pattern hierarchy is needed. Existing hashed-path traceability is a
useful precedent, but its JSON-object paths do not resolve spans in raw text.
The experimental code remains in the label plane and is not imported by
pre-final features. Existing frozen modules remain unchanged.

## Acceptance scenarios

1. Given Unicode, repeated text, CRLF, and long lines, building and resolving a
   snapshot returns exact original bytes deterministically, without omissions.
2. Given tampered text, offsets, policy, or identity, or IDs from another
   artifact/reference, resolution fails visibly and does not repair the input.
3. Given distributed support, a judgment can cite multiple current segments.
   Missing checks, duplicate keys/IDs, unknown fields, invalid statuses, and
   empty covered evidence are rejected. A real but irrelevant citation remains
   locator-valid and explicitly semantically unvalidated.
4. Given valid, invalid, and unlabeled records, the report retains all attempted
   observations and separates schema/locator failures from construction
   disagreement. It cannot report perfect performance by dropping failures.
5. Given the CLI and synthetic fixtures, a user obtains an aggregate diagnostic
   with zero provider calls and no private payload. Prior v2/v3 responses and
   ledgers are unchanged; no main-cohort launch becomes possible.

## Scientific and product boundaries

This increment tests software behavior only. Toy tests are not new experimental
evidence, and the four locked evaluation locators are not development material.
Any paid comparison needs a new frozen protocol, source/environment identity,
matched inputs, planned denominators, and explicit shared-budget disposition.
It must acknowledge presentation changes and retain failures. Existing failed
studies remain failed; neither a new directory nor this parser releases funds.

The product direction is advisory trace inspection: obligation, observation
scope, selected source spans, and reason for uncertainty or rejection. Future
utility studies should measure investigation time and appropriate reliance,
including convincing but unsupported judgments. Automated semantic approval,
claims of defect prevention, and replacing H1/H2 outcomes remain out of scope.

## Verification and review

Use behavior-first pytest tests for pure contracts and CLI integration, then
the full suite, compilation, eval/constraint-replay/wedge gates, privacy review,
and SOLID/clean-code review. No browser, new package installation, or subagent
is needed. Review is performed inline to respect the user's memory constraint;
it is not independent review or advisor authorization.
