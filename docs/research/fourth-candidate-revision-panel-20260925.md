# Final prospective obligation replacement panel

Status: **pre-oracle and pre-generation screening completed**. No generated implementation or E2E outcome was available to the reviewers.

The only case still deferred after the third panel, `paperless-accept-suggestion`, depended on an inferred post-acceptance state. It was replaced within the same project by `paperless-nested-tag-adds-parent`, grounded in the frozen Paperless-ngx usage source. The source directly states that adding a tag to a document automatically adds all parent tags.

The bounded browser contract uses a document with no tags and a two-level `Parent → Child` hierarchy. Assigning `Child` and the pre-existing hierarchy are controls. The only scored endpoint is that `Parent` becomes visibly assigned after the UI settles.

Three isolated Codex configurations reviewed the candidate under the same strict rule:

| Reviewer | Verdict | Evidence SHA-256 |
| --- | --- | --- |
| GPT-6 Astra | ACCEPT | `06b4fd78cfcdc7bc16da779500fc35e6caec956d356dada689fd2b8e315b1fae` |
| GPT-6 Sol | ACCEPT | `3329bccf9cb1f5728c79fb28ed1a1eeda1569b6bea76c0db3ed311e35b37a031` |
| GPT-6 Luna | ACCEPT | `a85a3a2015f5f772307b377533ef1f9b2f77a099e03e2e635521527b0099687b` |

The prompt hash is `524bd6e8b08aa6e04e1cc258018187191375988adf4c020cebc37e49e0d4ccd9`. Raw prompt, schema, register and responses remain under the private evidence directory.

## Result and limit

The complete prospective pool now contains **12 eligible obligations across six projects**, balanced at two per project. Under three A/B/C arms, two model configurations and three repetitions, the ceiling is **216 planned positions**.

This closes candidate selection only. None of the 12 obligations becomes an E2E result until its browser oracle, target and non-target mutants, A/B/C prompts, runtime, schedule and custody bundle are frozen and qualified. The panel therefore does not add evidence for H1 or H2.
