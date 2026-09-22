# RealWorld behavioral contracts for the proposed expansion

Status: **source review and oracle design, not a qualified instrument or a new result** (2026-09-22). These three intents already appeared in the criteria experiment. They are purposively selected, previously exposed requirements, not unseen source samples. The proposed tasks are bounded API replicas; passing them would not establish compliance of an upstream RealWorld implementation.

## Fixed sources and boundary

All three `A` excerpts in [`corpus.json`](../../data/criteria-expansion/corpus.json) exactly match their recorded Unicode spans in the pinned endpoint file. Their `C` variants equal `A` with only the recorded span removed. Both committed endpoint and OpenAPI files were compared byte for byte with upstream files at `ebbcdeb8d55b42a3a613c787560498b8ef10003f`. The linked response-format page was separately fetched at that same revision. Source hashes below are SHA-256 of raw bytes:

| Source | SHA-256 | Role |
| --- | --- | --- |
| [Endpoints](https://github.com/realworld-apps/realworld/blob/ebbcdeb8d55b42a3a613c787560498b8ef10003f/docs/src/content/docs/specifications/backend/endpoints.md) | `b1aecb6b88c7e7e75b3c7364abbbae4c911ee87bb2841ca486e36db16c6408e7` | Exact A/B/C source and target obligations |
| [OpenAPI](https://github.com/realworld-apps/realworld/blob/ebbcdeb8d55b42a3a613c787560498b8ef10003f/specs/api/openapi.yml) | `227d6983874850d35a883f4486b455cedbb272a0c103008595873c94ae1600ac` | Linked request, response and status contracts; **oracle-only where it reveals a target** |
| [API response format](https://github.com/realworld-apps/realworld/blob/ebbcdeb8d55b42a3a613c787560498b8ef10003f/docs/src/content/docs/specifications/backend/api-response-format.md) | `243cd805ddaa397b8f57c6fd9e1757bcbaa34eb8908a2505600626e1099edd24` | Profile, multiple-article and single-comment examples |

The current [candidate register](../../data/behavioral-expansion/candidates.json) is preparation, not a frozen generation packet. The contracts below refine it before admission. They do not assert outcomes or require generated code to use a particular framework, database, token library or internal storage shape.

Use the same generic request/response and fixture interface across A, B and C for each intent. The request may carry method, path, query, headers and body; fixtures provide articles, users, follow edges and comments. Publish the identical neutral interface to every arm, while keeping reference data, hidden assertions and full source specifications outside model context. A JSON HTTP surface is appropriate, but an in-process adapter may invoke it to make tests deterministic. A model implementation should be assessed by externally visible responses and state, not its helper names.

## `realworld-list-articles`: omitted offset/default-zero obligation

The endpoint excerpt requires `GET /api/articles`, global most-recent-first order, optional tag/author/favorited filters, default limit 20, offset/skip default 0, optional authentication and the multiple-articles response. The pinned OpenAPI declares `offset` as an optional nonnegative integer and `limit` as an optional positive integer with default 20. It requires top-level `articles` and `articlesCount`; the response-format page shows article summaries without `body` for list endpoints. The source does **not** state whether `articlesCount` is a pre-pagination total or page length. Do not infer a count semantic from the example alone.

| ID | Independent behavioral assertion | Classification |
| --- | --- | --- |
| `rw_list_offset_default` | Given 26 articles with distinct creation timestamps, `GET /api/articles` without query or credentials returns the 20 newest summaries; omitting offset selects the same initial slice as explicit `offset=0`. | Target and non-target limit/order |
| `rw_list_offset_nonzero` | On that same immutable fixture, `?offset=7&limit=5` returns exactly ranked articles 8–12, after sorting newest first. | Target |
| `rw_list_order_before_slice` | Choose timestamps and insertion order that differ; the offset slice is taken from newest-first order, not from storage order. | Target interaction with non-target order |
| `rw_list_other_contracts` | Separate fixtures exercise tag, author and favorited filters, optional authentication, default limit 20 and response shape (`articles` array, integer `articlesCount`, summary fields). | Non-target/interface |

Target-only mutants should ignore offset or apply a nonzero implicit default. A sort-after-slice mutant must fail the interaction check. Reference controls should include at least two backing-store approaches that produce the same API observations. Do not require behavior for malformed or negative offsets as part of this target: the excerpt does not specify the rejection policy. Do not turn `articlesCount` into an endpoint target until its intended semantics are independently resolved. Use unique timestamps so tie-breaking is outside the oracle.

## `realworld-follow-user`: omitted no-extra-parameters obligation

The endpoint excerpt requires authenticated `POST /api/profiles/:username/follow`, a Profile response, and **no additional parameters required**. The pinned OpenAPI declares only the required `username` path parameter, no request-body schema, token security and a 200 Profile response. Its Profile schema has `username`, nullable `bio`/`image` and boolean `following` within top-level `profile`. The response-format page agrees on that wrapper.

| ID | Independent behavioral assertion | Classification |
| --- | --- | --- |
| `rw_follow_without_extra_input` | Given authenticated viewer `alice` and existing user `bob`, POST to `/api/profiles/bob/follow` with **no request body** and no extra query fields succeeds, records the follow edge and returns `profile.username = bob` with `following = true`. | Target plus route/response |
| `rw_follow_requires_auth` | The same POST without an authenticated viewer does not create a follow edge; pinned OpenAPI lists 401. | Non-target |
| `rw_follow_profile_shape` | A successful response is JSON with a `profile` object matching the pinned Profile fields. | Non-target/interface |

A mutant that demands an extra body field or query parameter must fail `rw_follow_without_extra_input`. Another mutant that accepts an anonymous follow must fail the non-target control. An explicit empty JSON object (`{}`) is **not a mandatory acceptance case**: “no additional parameters required” proves the absent-body request must work; it does not say every supplied body is accepted. An implementation accepting both forms is a valid qualification alternative, as is one that accepts the absent body but rejects `{}`. Optional parameters must not be prohibited merely because no extra parameter is required. Do not impose a particular outcome for duplicate follows or self-following; neither appears in this excerpt.

## `realworld-add-comment`: omitted authentication obligation

The endpoint excerpt requires authenticated `POST /api/articles/:slug/comments`, a `comment` object with required `body`, and the created Comment response. The pinned OpenAPI specifies a required `NewCommentRequest` wrapper, token security, a 201 `SingleCommentResponse` and a 401 unauthorized response. The Comment schema requires integer `id`, `body`, timestamps and an author Profile. The response-format page confirms top-level `comment`.

| ID | Independent behavioral assertion | Classification |
| --- | --- | --- |
| `rw_comment_reject_anonymous` | Given an existing article and valid `{"comment":{"body":"text"}}`, POST without credentials is rejected and leaves the comment collection unchanged, including after a separate read. | Target |
| `rw_comment_accept_authenticated` | With a valid viewer and the same article/body, POST creates exactly one comment and returns the created comment in the `comment` wrapper. OpenAPI gives 201 for this successful response. | Non-target control |
| `rw_comment_body_and_shape` | A missing `body` is not accepted as a created comment; successful responses carry the pinned Comment fields and the authenticated author. | Non-target/interface |

A mutant that stores an anonymous comment must fail the target. A reject-all server must fail the authenticated control. The target label should depend on unauthorized **creation** (or an unauthorized success response), not solely on a particular error body. The pinned OpenAPI lists 401, so status conformance may be reported separately; the short A/C endpoint excerpts alone do not state its exact status. Use a fixture-level state read so “rejected” cannot mask a storage side effect. Avoid testing a nonexistent article in the auth contrast because 404 precedence could obscure the target.

## Prompt leakage and admission gate

The complete OpenAPI and linked endpoint page are **not neutral auxiliary context** for the C arms. The OpenAPI `offsetParam` directly names the list target; its follow operation omits a request body and thus hints at the no-extra-input target; its comment operation has `security: Token` and 401, directly reinstating the authentication target. The endpoint page itself repeats offset under Feed Articles and authentication in other operations. Those documents may inform the private oracle, but showing them whole to a generator would make an omission contrast uninterpretable.

The common public interface should describe only the transport, fixture access and output serialization. For example, a generic request object can carry `query`, `headers` and `body` for **all three tasks** without declaring which fields an endpoint must use. A generic viewer fixture can represent a request with or without credentials; it must not say that comment creation requires credentials. A generic article response envelope may be exposed only after checking that it contains no deleted target text. Do not include `offsetParam`, comment `security`, 401/201 examples tied to comment creation, or a follow-specific “body optional” instruction in generated prompts. Audit the exact serialized A/B/C prompts and any accessible files/tools before freeze; simple keyword scanning is necessary but not sufficient. If the runner cannot avoid direct target disclosure, defer that intent before generation and record the reason.

## Remaining decisions before qualification

1. Fix the replica adapter and input fixtures, then preserve their bytes and observation semantics. For lists, use distinct times and a fixture exceeding 20 records. For follow/comment, define deterministic authenticated and anonymous callers and read-after-write state checks. These are harness fixtures, not claims about arbitrary implementations.
2. Decide whether OpenAPI-only details such as exact status codes are interface checks or study obligations. Resolve the still-unspecified `articlesCount` semantics before adding a count-value assertion. The deleted target must remain traceable to the exact endpoint excerpt; keep auxiliary conformance failures separate.
3. Run two correct implementations with meaningful variation and target-only plus non-target mutants for each oracle. Only admit an intent when the expected assertion IDs distinguish them. Then independently review the serialized prompts for leakage, freeze the eligible set and budget, and collect once.

No provider calls, generated programs, oracle executions, qualitative judgments or behavioral outcomes are asserted in this document.
