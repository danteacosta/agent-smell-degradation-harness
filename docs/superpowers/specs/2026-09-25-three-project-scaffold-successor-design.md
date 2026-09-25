# Three-project fixed-scaffold successor design

## Decision

Run a separately declared successor pilot for Paperless-ngx, Nextcloud, and
OpenProject. The first six-project collection remains immutable. Its 54 rows
for these projects stay in the denominator and are reported as observed. The
successor addresses the observed interface failure by freezing the rendered UI
and asking the model to provide only behavior logic inside one marked script
region.

This is a post-outcome redesign. It may show whether omission affects behavior
when DOM invention is removed, but it must not be pooled with or substituted
for the original 72-call collection.

## ATDD contract

Preparation is accepted when:

1. The three source requirements, A/B/C variants, source revisions, licenses,
   and deletion spans remain byte-identical to the first freeze.
2. Each project has one arm-invariant HTML scaffold with exactly one behavior
   insertion marker and a narrow JavaScript contract.
3. The scaffold owns visible structure, accessible names, rendering, and test
   identifiers; generated code owns state transitions only.
4. Browser assertions exercise the visible user journey and classify target,
   non-target, interface, and browser failures without guessing.
5. Reference, alternative, target-mutant, non-target-mutant, malformed, and
   missing-behavior controls are qualified before any provider call.
6. A seeded schedule contains 54 opaque slots: three projects, three arms, two
   model configurations, and three repetitions.
7. Prompt bytes, scaffold bytes, runner bytes, qualification evidence, and
   every request are hash-bound before generation.
8. All generation finishes before browser outcomes are inspected. Missing and
   invalid outputs remain in the fixed denominator.

## Behavior contracts

The model receives the frozen page and replaces only `/* MODEL_BEHAVIOR */`.
It may use the documented page API but must not replace the scaffold.

| Project | Generated behavior | Browser endpoint |
| --- | --- | --- |
| Paperless-ngx | Register upload and optional page-level drop behavior through the supplied API | Dropping `Invoice.pdf` anywhere makes one visible document row |
| Nextcloud | Apply Delete and optional Restore commands to the supplied file state | Restoring `Project Plan.md` makes it visible in All files again |
| OpenProject | Return saved field values from the supplied form state | Saving Work `8` makes Remaining Work visibly equal `8` |

The API exposes mechanics needed to integrate with the frozen UI. It does not
state which optional target transition is required. This reduces invalid DOM
outputs but may cue available actions. That cue is shared across A/B/C and is a
documented construct-validity limitation.

## Analysis and stopping rules

Report all 54 planned rows by project, model, and arm. C-A is the primary
contrast and B-A is the wording control. Report complete-case outcomes and
fixed-denominator bounds. Preserve recovered target behavior in C, null effects,
reverse effects, invalid output, and provider failure. Do not claim a general
H1 from this convenience sample. H2 remains unevaluated.

