# TodoMVC requirement-completion exploratory pilot

The user explicitly authorized an exploratory pilot on 2026-09-21. This is a
separate engineering study, not repository admission or confirmatory H1/H2
collection. Pending mapping/manipulation/oracle/rights reviews remain pending.

## Frozen comparison

One TodoMVC Vue Escape case; three requirement arms, three repetitions each,
nine generations in seeded random order (20260921), one requested model
gpt-5.6-luna with low reasoning via the existing ChatGPT-authenticated Codex CLI
adapter. No API-key fallback, tools, repository access, oracle or paired text is
given to the generator. The current CLI version and executable hash are recorded.

Complete: If escape is pressed during the edit, the edit state should be left
and any changes be discarded.

Equivalent rewrite candidate: Pressing Escape while editing must exit edit mode
without saving the draft.

Missing-condition candidate: If escape is pressed during the edit, the edit
state should be left.

The task is bounded completion of one handler, not whole-application generation.
The original cancelEdit function is replaced by a neutral handleEscape function
with a body placeholder; the template Escape binding calls handleEscape. All
other component bytes remain fixed. The prompt requests a JSON handler_body
string. The generator sees this same scaffold and one requirement only. It may
use state/helpers visible in the scaffold. No desired implementation is shown.
This narrow scaffold and familiarity with Escape conventions are limitations.

## Acceptance contract

1. Before any generation, freeze exact prompts, scaffold, qualified shared
   strengthened oracle/support, randomized schedule, model, runtime image ID,
   runner/adapter hashes, and engineering reference/mutant execution receipts.
2. Run the unchanged 28-test Cypress suite for every accepted completion, with
   native screenshots/video. Only the handler body varies. Independent fresh
   calls have no history or feedback. No repairs or outcome-driven repetitions.
3. Run generated code only in a fresh Linux container with network disabled,
   non-root user, dropped capabilities, no-new-privileges, read-only root and
   input mount, bounded tmpfs/resources/time, and an isolated output mount. No
   host credentials, Docker socket or parent filesystem enters the container.
4. Preserve raw responses/usage before parsing, source bytes, stdout/stderr,
   JUnit and media; hash all evidence. Separate valid pass, targeted Escape
   defect, other test failure, build/executor error, generation error and
   unattempted slots. An absent/partial/mismatched JUnit cannot be a pass.
5. Report all nine planned slots and null/reverse results. Missing-condition vs
   complete is primary; rewrite vs complete is wording sensitivity. Do not pool
   these repetitions as independent requirements or infer general prevalence.

## Design and verification

A separate eval/todomvc_pilot.py owns freezing, prompt generation, response
assembly and descriptive classification. Existing CodexCLIProvider owns auth and
provider isolation. A fixed container image/entrypoint owns installation and
execution; dependencies are installed before generation, never during offline
execution. Reuse the qualified oracle and capture-only support fixture unchanged.
No changes to repository_case_admission are needed or allowed for this pilot.

Use test-first contracts for prompt isolation, exact body substitution, fresh
immutable output, nine-slot retention, report inventory and failure categories.
Qualify the actual executor on the reference and manual mutant before collecting
any model output. Review source and container isolation before generation.

Official Codex runtime sources rechecked 2026-09-21:
https://learn.chatgpt.com/docs/non-interactive-mode
https://learn.chatgpt.com/docs/auth
Local runtime reports ChatGPT login; consumption is subscription quota, not a
measured zero-dollar API price. The exact immutable model snapshot may remain
unavailable and must not be fabricated.
