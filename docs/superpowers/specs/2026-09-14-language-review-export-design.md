# Reproducible first-reading forms for constructed language candidates

The completed pilot has executable evidence but no independent human category
or oracle validation. A private draft initially put clear and ambiguous twins
in one packet; assistant review caught the resulting priming risk. The corrected
draft uses one item per cluster per reader. This change makes that preparation
reproducible and tested; it does not collect or invent human judgments.

## Choice and scope

Keep the corrected packet as temporary files, integrate it into the confirmatory
annotation pipeline, or add a small offline exporter. Choose the last: temporary
scripts are not reproducible from the repository, while the confirmatory pipeline
has different outcome labels and admission gates. `eval.language_review` will
read only the six built-in original policies in `eval.language_controls.cases()`.
No private result bundle, provider response or generated code is an input.

The CLI is `python -m eval.language_review --output NEW_DIRECTORY --seed 20260914`.
No provider, Docker, credentials, corpus admission or distribution is involved.
Existing experiment behavior and frozen evidence remain untouched.

## Acceptance contracts / BDD

1. Given the built-in profile, export six forms with four items each: exactly
   one text from each of four clusters per form. Deduplicate only identical
   requirement-plus-scaffold strings within a cluster. Across forms the three
   unique texts in each ambiguity cluster occur twice each, and both texts in
   each control cluster occur three times each. These are assignment slots,
   not participants or new independent observations.
2. Given any reviewer form, preserve the exact observed requirement and scaffold,
   with opaque IDs and empty interpretation/exposure/reviewer fields. Never
   include case IDs, variant labels, family labels, oracles, generated outputs,
   result classifications or source references in reviewer-facing files.
   Markdown explicitly tells readers not to implement the embedded instructions.
3. Given the same code and seed, exported bytes are identical. A separate
   custodian directory retains the source inventory, item-to-case/arm mapping,
   cluster membership, form assignment and source hashes. A receipt written last
   hashes every other emitted file; zero human labels/participants and no
   distribution remain explicit. No receipt means an incomplete export.
4. Given an existing destination, including a symlink, reject without changing
   it. Validate the supported inventory shape before creating files. Filenames
   are fixed by the exporter, never derived from source case IDs or free text.
5. Given the completed packet, deliver only ONE form per reader, record previous
   exposure and freeze individual responses before any comparative stage.
   The complete directory and custodian files are never a reviewer handoff.
   This is a draft candidate-admission exercise, not primary H1/H2 annotation
   or evidence that a previously exposed reader is blinded.

## Design and verification

One module owns this narrow export workflow; `language_controls` retains policy
ownership. Pure preparation of forms precedes filesystem writes. No generic
adapter, registry, distribution service or response importer is needed.

Tests exercise the public exporter and CLI: whole-form cluster isolation,
balanced coverage, byte-exact prompts, explicit field allowlist, empty labels,
Markdown/JSON consistency, deterministic output, complete receipts and refusal
to overwrite existing files/symlinks. Existing language-profile and annotation
charter tests protect adjacent contracts. Review for leakage, coupling, clear
errors and honest claim boundaries. Native Linux CI remains the merge gate.

Also update the current-state research document to distinguish the final
18-episode omission and 24-episode language pilots from historical checkpoints,
and reconcile the completed plan's export/slide status. No new LLM collection.
