# Constructed language controls pilot

Authorized continuation: 30 minutes of autonomous work on the thesis experiment.
This is an assistant-reviewed engineering pilot of original policies, not
admission to the natural corpus or independent human smell validation.

## Design decision

Repeating omission with another model would measure model configuration rather
than language-category coverage. Forcing every catalog entry into pure Python
would invent oracles for usability or underspecified optimization. Instead add
one small named profile to the existing bounded Codex demo runner: coordination
ambiguity, vague pronoun, and meaning-preserving negative-wording controls.

The profile has six case IDs but only two ambiguous stems and two controls.
Each ambiguous stem has two explicit intended policies and the same rewritten
prompt. These twins deliberately expose non-identifiability of the intent,
not four independent application domains. Keep them in the same family/cluster.

## Case contracts (author-defined originals)

Coordination: explicit `(a or b) and c` versus explicit `a or (b and c)`.
Rewritten text removes the parentheses, making both prompts identical. Evaluate
all eight Boolean triples. The other grouping is a documented interpretation,
not an independently known defective program.

Pronoun: a sender is paired with a receiver; explicit response depends on the
sender being enabled or on the receiver being enabled. Replace only the named
actor in the response with `it`, making both rewritten prompts identical.
Evaluate all four Boolean input pairs. The other antecedent is a documented
interpretation. Both named input arguments are kept in both variants.

Controls: express `x >= 5` affirmatively and `x < 5` negatively with complementary
responses, on integer x; test -1..10. Express Boolean enabled affirmatively and
negatively with complementary responses; test both values. Both rewritten
controls have exactly the same truth table as their explicit counterparts.

## Acceptance criteria / BDD

1. Given this named profile, preparation freezes six cases, case roles, twin
   cluster IDs, intended and alternative truth tables, exact prompts, source
   hashes, random schedule, two repetitions and configuration before generation.
   The ordinary omission profile remains the default; unknown profiles fail
   before creating an output directory or invoking a provider.
2. Given original reference functions, all explicit policies pass their intended
   truth tables; alternate interpretations disagree only on the expected rows.
   Both negative-wording controls preserve their complete tables. These are
   instrument tests, not LLM results.
3. Given a model completion, provider-visible input contains only one variant
   plus its shared interface/scaffold. No case ID, role, twin policy, alternative
   tests or labels enter the prompt. Retain existing CLI subscription-only auth,
   no tools or API fallback, isolated executor and error accounting.
4. Given a successfully parsed artifact, execute intended tests and each
   documented alternative in the same isolated runtime. Save both reports and
   classify intended-only, alternative-only, both, neither, or execution-unknown.
   Never call an alternative-only result disobedience to ambiguous text. Preserve
   errors, null/reverse contrasts and all planned episodes; do not retry failures.
5. Summarize by role/family/cluster and variant. Internal legacy `defective`
   means rewritten arm and is not a defect label for equivalence controls.
   Do not pool controls with ambiguity pairs into a causal smell-effect estimate.
   Do not count twins/repetitions as independent intents. No H1/H2 or provider
   diversity claim. Use requested model gpt-5.6-luna, low reasoning; 24 scheduled
   calls, no unplanned generation retries. Stop dispatching on a provider error;
   mark remaining scheduled episodes not executed with a reason.

## Modules and verification

`eval/language_controls.py` owns only original policies and truth tables.
`eval/codex_demo.py` selects the profile, freezes it and orchestrates existing
provider/executor interfaces. `tests/test_language_controls.py` checks public
contracts, full Boolean domains, missing-profile rejection, hidden metadata,
alternative interpretation reporting and error preservation. No new provider,
framework, generic corpus loader or arbitrary Python execution route.

Run focused tests first, Linux executor controls, then the frozen pilot only
after the profile and code review pass. Preserve private receipts and publish
aggregate outcomes, including failures and limits, in repository/Drive/slides.
The primary taxonomy references and caveats are in the existing
[coverage matrix](../../research/2026-09-14-smell-coverage-and-construct-validity.md).

## Non-identifiability and stopping rules

The same rewritten prompt corresponds to distinct author intents in each twin
cluster, so no deterministic interpretation can satisfy both incompatible
policies on distinguishing inputs. This is a property of the constructed
design, independent of observed model performance. Report any empirical
interpretation preference separately from that construction proof.

No new live dispatch after 21:08 UTC in this session, leaving time to reconcile
results and update artifacts before the 21:15 UTC work window ends. A timeout
or unavailable model ends dispatch without fallback; preserve partial evidence.
