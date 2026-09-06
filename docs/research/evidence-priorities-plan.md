# Evidence priorities and acceptance contract

Scope: auxiliary instrument evidence while human annotation is unavailable.
The historical judge prompt and primary H1/H2 protocol remain frozen.

1. Execute the 12 PR #39 controls with both existing provider configurations,
   three repetitions each (72 calls). Freeze requests, prompt, rubric, source,
   prices and decoding before execution. Keep responses and cost ledger private.
   Accept only an explicit report retaining all missing/failed cases. Reuse the
   existing US$0.988200 conservative ledger envelope under the US$1 cap; it
   reserves the larger pre-pilot plan although this runner issues only 72 calls.
2. Build four original executable contracts for numeric limits, permissions,
   states and preconditions. Test both satisfying and violating inputs and a
   deliberate mutation for each. Reject unsupported operators and malformed
   inputs. These construction oracles do not validate natural-language meaning.
3. Freeze and implement an offline temporal analysis for T1, T1+T2 and T1–T3.
   Accept only stage observations strictly before the terminal timestamp.
   Report first alert, lead time, terminal-label availability, false alerts and
   measured cumulative observation cost with explicit denominators. Missing
   observations/cost/outcomes stay missing. No threshold fitting on outcomes.

Behavioral acceptance tests:

- Given a constant-clean judge, controls expose all negative-control misses.
- Given missing usage or an interrupted call, collection stops and cannot
  silently retry, overwrite the run or report success.
- Given a frozen contract, boundary pass/fail vectors kill its specified mutant.
- Given a post-final stage, the temporal analyzer rejects the episode.
- Given incomplete stages, unknown outcomes or costs, reports retain missing
  denominators rather than assigning zero error/cost.

Implementation uses existing provider adapters, cost ledger and judge scorer.
Contracts and temporal analysis remain small pure functions; no new framework.
Verification: targeted pytest tests, full CI gates, private preflight/readback,
and document/slide readback. Review interfaces, error paths and secret boundaries.

Roadmap (outside the immediate three priorities):

4. Future human calibration: a separately frozen random audit sample and an
   enriched disagreement queue; independent labels and adjudication when
   available. No claim of human agreement before that study.
5. Product diagnostic study: traceability loss, checkpoint and evidence display;
   evaluate task usefulness and investigation time with participants. Claims of
   prevention, automated approval or time saved require that separate study.
