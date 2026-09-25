# Independent integrity audit of the 11-obligation pool

Three isolated high-reasoning Codex configurations audited the complete checked-in screening chain read-only. All three independently recomputed the same current result: **11 distinct prospective obligations, six represented projects, and a ceiling of 198 positions**. None treated this as qualified or executed E2E evidence.

- Prompt SHA-256: `aabb866e2fb08775a4f23982c075fb4a9c3f3f49c16ccda49bc6930d85c54483`
- Astra response SHA-256: `2a53925374e9547cf75ed19c83b75fc2f58ba4aa4339ef0eec546d04ef3335b5`
- Sol response SHA-256: `5b2dd079ac42af39dcdcf7cd1b2813511c119256e9dcf9d8a9a06acc2f6d85a5`
- Luna response SHA-256: `a7a9f2963de724e043329e477f30c2e5863e2afa61f053fbd1d83676cb8af9bc`

Raw audit inputs and outputs remain outside Git under `.private-research-evidence/eleven-obligation-audit-20260925/`.

## Findings and corrections

The checked-in data contained no actual duplicate, cross-project replacement, or project-count error. The audit nevertheless reproduced validator blind spots that could have allowed such drift later:

- a newly accepted ID could collide with a prior eligible ID while the list length still reported 11;
- predecessor IDs could be swapped across projects because only their set was checked;
- the declared represented-project list could contain duplicates or disagree with the accepted candidates;
- first-panel reviewer totals and early-panel project metadata were not recomputed;
- the command-line entry point validated only the original 12-candidate register instead of the complete chain.

The validator now rejects all of these cases. It derives project counts from the deduplicated eligibility chain, enforces project-continuous predecessor mappings, matches replacement links in consensus rows, recomputes reviewer totals, validates project metadata at every stage, and exposes a complete-chain default result. Regression tests reproduce the previously accepted corruptions.

The reviewers also agreed that stage labels and well-formed hashes do not independently prove chronology. The research notes now describe pre-oracle timing as a recorded custody claim supported by retained private evidence and commit order. They no longer claim that outcome-based selection is impossible merely because a stage field says so.

## Residual limitation

CI can validate the embedded public decisions, source locators and declared digests, but it cannot recompute hashes of private prompt and response files that are intentionally excluded from Git. Independent custody review of those private files remains necessary before treating chronology and session isolation as externally verified.
