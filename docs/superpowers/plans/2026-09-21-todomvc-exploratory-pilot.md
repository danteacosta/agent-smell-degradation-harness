# TodoMVC exploratory pilot implementation plan

**Goal:** Execute and preserve nine isolated requirement-to-handler generations
and compare them under one frozen E2E oracle, explicitly exploratory.

**Architecture:** Existing subscription provider; small separate pilot module;
pinned dependency image and offline container entrypoint; private evidence bundle.
**Tech stack:** Python/pytest, Codex CLI, Docker/Linux, Vue/Vite/Cypress/Electron.

- Review the spec and independently assess leakage, failure classification and
  execution isolation before generation.
- Test-first implement `eval/todomvc_pilot.py` and
  `tests/test_todomvc_pilot.py`: fixed three-arm prompts/scaffold, nine scheduled
  slots, substitution, hash validation and strict JUnit classification.
- Prepare the frozen dependency image and `eval/fixtures/todomvc-pilot-run.sh`;
  execute known reference/manual mutant in the exact offline runtime, retaining
  logs, reports, screenshots and videos.
- Run focused tests, compile/diff checks and code/security review. Freeze all
  protocol/runtime/source bindings before the first provider call.
- Collect nine calls using the existing adapter without automatic retries or
  feedback. Preserve every slot/error; execute accepted bodies in the qualified
  container and build a descriptive report plus inventory receipt.
- Independently verify results and media. Update the Drive report and slides
  with observed outcomes and limitations; export deliverables. Open/merge the
  implementation PR only on reviewed green CI, under continuing authorization.

No user approval is needed again: the user selected the exploratory option.
Human reviews are neither fabricated nor reclassified as completed.
