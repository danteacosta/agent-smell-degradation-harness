# CaSS behavioral expansion: source-bound contracts

This is a pre-collection oracle design for `cass-idata-007` and
`cass-batch-002`, not a qualified instrument or an experimental result. Both
intents were used in the earlier criteria experiment. Their source is the
Apache-2.0 CaSS specification at revision
`97fc0939ca3960504ce8b2f51749881543a4038c`, preserved at
[`data/criteria-expansion/sources/CASS/REQUIREMENTS.md`](../../data/criteria-expansion/sources/CASS/REQUIREMENTS.md)
(SHA-256 `937b1f4ffb35548c4cbb7332e212ae5d52331b9d1ed9c464c0773411421485ce`).
The exact A/B/C excerpts, omission spans and prior-exposure caveat are in the
[corpus](../../data/criteria-expansion/corpus.json). The source says that its
requirements were derived retrospectively from code, tests and other artifacts
(§5.1); this study must not present them as prospective, independently authored
stakeholder requirements.

## IDATA-007: numeric confidence in an assertion

The target obligation is support for a numeric `confidence` field on an
Assertion. The omitted C excerpt removes precisely that field. The source
also requires `subject` and `agent` encrypted separately for readers, a
competency `@id`, and evidence ([IDATA-007, line 647](https://github.com/cassproject/CASS/blob/97fc0939ca3960504ce8b2f51749881543a4038c/REQUIREMENTS.md#L647)).

**Observable target.** Given a valid assertion containing a finite numeric
confidence such as `0.375`, when a permitted caller stores and retrieves it
through the declared public interface, the returned/stored assertion exposes
the same numeric value. A second accepted example with `0` catches a common
truthiness loss. Accept equivalent JSON number representations; do not require
identical serialized bytes, property order or a particular in-memory class.
The source says *support*, not mandatory presence. An assertion without
confidence must remain admissible, and this oracle must not invent a `[0,1]`
range or a rounding rule. It should not mark an implementation faulty merely
because it does not enforce such rules. A present confidence that disappears,
changes numeric value, or is returned only as a string is a target failure.

**Other obligations.** Qualify separate observations for `subject`, `agent`,
`competency` and `evidence`. A permitted reader must recover each of subject
and agent through its own encrypted field; raw persistence or a caller without
the reader key must not reveal either plaintext. Test the two fields
independently, so one encrypted combined blob does not silently satisfy
“individually encrypted.” Do not prescribe ciphertext bytes, encryption
randomness or an exact wrapper representation from IDATA-007 alone. The
related [SEC-032, line 727](https://github.com/cassproject/CASS/blob/97fc0939ca3960504ce8b2f51749881543a4038c/REQUIREMENTS.md#L727)
repeats the individual-encryption rule; [IDATA-011, line 651](https://github.com/cassproject/CASS/blob/97fc0939ca3960504ce8b2f51749881543a4038c/REQUIREMENTS.md#L651)
describes an EncryptedValue wrapper, but does not make that wrapper the only
permitted assertion-field representation.

**Qualification before generation.** An independent reference and an
independently written alternative representation must pass. A mutant that
drops confidence, stringifies it or changes `0` must fail only the target
assertion when all other fields work. A mutant exposing subject or agent in
plaintext must fail a distinct privacy assertion. An assertion without
confidence must pass the support-only control. If public-interface round-trip
and field-level encryption cannot both be observed without prescribing an
unsupported representation, defer this intent rather than weakening the
oracle after seeing outputs.

## BATCH-002: permissions on each object

The exact target is checking KBAC permission separately for each object in
`POST /api/sky/repo/multiPut`; the non-target contract is array input and a
count of successfully stored objects ([BATCH-002, line 241](https://github.com/cassproject/CASS/blob/97fc0939ca3960504ce8b2f51749881543a4038c/REQUIREMENTS.md#L241)).
The linked rules say ownerless objects are publicly writable (SEC-020), an
owned object's `@owner` keys control writes (SEC-021), and admin keys override
ownership (SEC-023), at [lines 714–718](https://github.com/cassproject/CASS/blob/97fc0939ca3960504ce8b2f51749881543a4038c/REQUIREMENTS.md#L714-L718).
Signature sheets are RSA-signed, time-limited identity proofs (SEC-002).
Fix a non-admin caller with a valid signature and three distinct object IDs:
an ownerless object, an object owned by the caller, and an object owned only by
another key. Use an isolated empty store and inspect persisted state, not only
the response count.

**Required observations from BATCH-002.** An all-permitted batch containing
the ownerless and caller-owned objects must store both and report `2`. An
all-denied batch must store none and report `0` when a successful-count
response is returned. For a mixed batch, the denied object must never be
stored, and any returned success count must equal the number actually stored.
Check each position by permuting the denied object through first, middle and
last positions. The all-permitted control is essential: a reject-all service
would pass a denial-only test while failing batch storage. A service checking
only the first object must fail a position permutation. A reported count of
`2` when only one object persisted must fail the count assertion.

**Mixed-batch outcome boundary.** BATCH-002 by itself does not state whether
the permitted members of a mixed batch must be committed when another member
is denied. Its neighboring [BATCH-003, line 242](https://github.com/cassproject/CASS/blob/97fc0939ca3960504ce8b2f51749881543a4038c/REQUIREMENTS.md#L242)
and [SEC-024, line 718](https://github.com/cassproject/CASS/blob/97fc0939ca3960504ce8b2f51749881543a4038c/REQUIREMENTS.md#L718)
explicitly describe excluding denied members and counting them as failures.
That supports a separate *source-family conformity* check expecting permitted
members to succeed. The **primary BATCH-002 omission endpoint** should accept
both an atomic rejection and a partial success on mixed input, provided no
denied object is stored and the count truthfully reflects the store. Otherwise
the oracle would impose a policy not present in the exact tested excerpt.
Record atomic/partial behavior as a descriptive secondary observation. If
the study elects to make BATCH-003/SEC-024 part of the mandatory reference
contract, freeze that decision and its attribution before generation and
report it separately from the BATCH-002 target; never switch after outcomes.
Do not copy those neighboring rules into auxiliary generation context, as
that would give condition C the removed obligation by another route.

**Qualification before generation.** Two valid implementations with different
internal storage and response serialization must pass the primary contract.
In particular, an atomic mixed-batch implementation and a partial mixed-batch
implementation should both pass the conservative primary oracle. A reject-all
mutant must fail the all-permitted control. A no-permission mutant must fail
the mixed/all-denied privacy check; a first-object-only mutant must fail a
position permutation. A false count must fail separately. The qualification
must verify the object state after each call and reset the store between cases.

## Shared prompt context and leakage audit

Use identical auxiliary material, runtime and entry contract for A/B/C; the
only intended difference is the existing requirement variant. Public context
may name the assertion/multiPut function shape, JSON-LD identifiers and a
`signatureSheet` input slot if needed for runnable code. It must not include
the source document, neighboring requirement IDs, examples containing
`confidence`, expected target outputs, permission-decision tables, mixed-batch
fixtures or hidden tests. The generic `signatureSheet` slot is an interface
name, not an instruction to check each object's permissions. The A/B versions
retain their own source text; C does not get the removed phrase through
scaffolding, dependencies, filenames, comments, examples or tool retrieval.

Before freezing, inspect the exact bytes of every prompt, starter file,
dependency documentation and test-visible fixture for `confidence`, `KBAC`,
`@owner`, `permission`, `validate`, `multiPut` and equivalent paraphrases.
Occurrence is not automatically leakage: the endpoint name `multiPut` is
necessary, whereas a per-object authorization rule is not. Record the
decision for each occurrence. The test runner can hold identities and expected
outcomes privately, but generated code must receive a usable public interface
for signed requests. If that interface inherently supplies the omitted rule,
defer this intent before collection. Neither case is qualified merely by this
document; implementation, alternative controls, independent review and an
immutable pre-generation freeze remain required.

## Open source questions for admission

1. Which public API or bounded replica interface exposes assertion creation,
   retrieval and individual reader decryption without dictating a single
   ciphertext representation? Freeze it, including failure responses.
2. What exact successful-count response shape does `multiPut` return? The
   requirement specifies the semantic count, not a JSON field name or HTTP
   status for all cases. Accept semantically equivalent declared shapes or
   derive one from a pinned upstream API schema before qualification.
3. Does the study evaluate only the exact BATCH-002 excerpt or additionally
   the BATCH-003/SEC-024 source-family partial-success policy? Keep the
   primary endpoint conservative unless the expansion protocol explicitly
   changes the scope before any output is generated.
4. Can the signed caller identity and object ownership be represented in the
   shared interface without revealing the target per-object validation rule?
   If not, exclude this case and report why.
