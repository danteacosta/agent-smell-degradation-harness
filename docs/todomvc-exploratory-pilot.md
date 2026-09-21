# TodoMVC exploratory requirement-to-handler pilot

This lane completes only the Vue Escape handler from one of three requirements:
complete, a meaning-preserving rewrite, or omission of the discard condition.
The scaffold, 28 executed Cypress tests, and three calls per arm are fixed.
Nine fresh Codex ChatGPT-subscription calls use a seeded order. There is no API
key fallback, generated-code repair, or outcome-driven generation retry.

This is not confirmatory admission. Mapping, manipulation, oracle and rights
reviews remain pending. A manually seeded code defect qualifying an oracle does
not establish that a requirement smell causes generated defects.

## Collection and execution

`python -m eval.collect_todomvc_pilot --help` describes the collection interface.
It needs the frozen upstream component, an immutable local Docker image ID, and
reference/mutant qualification evidence. Qualification must exercise the same
`response.json` body-validation path and produce native media. The collector
freezes prompts, order, source/runtime hashes and qualification before calls.
Every planned slot remains in the result, including provider and executor errors.

Build the dependency image using the four files in `eval/fixtures` named
`todomvc-pilot.Dockerfile`, `todomvc-pilot-run.sh`,
`todomvc-escape-oracle.patch`, and `todomvc-visual-support.js` as build context.
Dependency preparation needs network access. Generated execution has no network,
credentials or Docker socket, runs as a non-root user with a read-only root and
input, and has bounded time, memory, CPU, process count and temporary storage.
Only its private output directory is writable on the host.

The original frozen TodoMVC revision is
`1f2bd7f0a1fa8c602284451d282c3821d0d96aec`. The oracle's 28 executed tests have
inventory SHA-256 `4cab322b79ed8d48bdd335d3d70deaeaf6ae68ec524ea10b19f49bbd7b4be734`.
The upstream Cypress summary also lists one pending placeholder, absent from the
JUnit executed-test inventory; it is not counted as a passed or executed test.

## Infrastructure correction in the first pilot

All nine original executions failed resolving Acorn before build or E2E. The
first reference/mutant qualification had bypassed response-body validation,
so it did not detect the missing parser. All original errors, raw CLI output,
responses, assembled components and the receipt are retained unchanged.

The corrected image explicitly installs Acorn 8.15.0 and resolves it by absolute
path. Qualification then traverses response validation, assembly, build and E2E
for both the reference and manual mutant. The collection gate now requires
evidence that body validation was exercised.

`python -m eval.replay_todomvc_pilot --help` implements a narrowly scoped,
provider-free supplementary execution. It accepts only the complete unchanged
nine-response collection with the diagnosed pre-build Acorn failures. Before
execution it freezes an amendment with original receipt/input hashes, corrected
image, qualification, code hashes and original order. It evaluates every original
response once and preserves the initial record. These are supplementary
exploratory results, not preregistered primary results.

## Interpretation and evidence

Each execution retains the raw response, component, exit status, JUnit, logs,
viewport screenshot after Escape and full video. Missing media, incomplete test
inventories, skips, malformed XML or inconsistent exit status cannot become a
successful result. The exact original-title assertion is distinguished from
other test failures. Raw CLI captures are optional, bounded, private files and
are saved before response parsing, including failed and timed-out calls.

Report all three arms and every slot. No failure implies no demonstrated effect
in this narrow pilot, not equivalence or absence of effects in other tasks. The
visible scaffold and familiar Escape convention may supply omitted behavior;
one task and three repetitions per arm cannot support population inference.

Verification: `python -m pytest tests/test_codex_cli.py tests/test_todomvc_pilot.py
tests/test_todomvc_pilot_executor.py tests/test_collect_todomvc_pilot.py
tests/test_replay_todomvc_pilot.py -q`.
