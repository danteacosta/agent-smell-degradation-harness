# Focus-chain browser instrument

This is an authored standalone implementation of the TodoMVC New todo subsection,
not upstream TodoMVC or a complete TodoMVC application. The qualification controls
are instrument checks, not research outcomes. Source mapping: the pinned
`todomvc-new-todo` record in `data/criteria-expansion/corpus.json`.

The only target assertion is `initial_focus`: 500 ms after load, before any input,
the visible `.new-todo` input is the active element. That horizon is a harness
convention, not a source-specified SLA. Six independent non-target assertions
check input layout above the list, Enter append/order, clearing, trim, empty
rejection and whitespace rejection. Each uses a fresh browser context. Observe each Enter action after a fixed
500 ms settling interval; this is an instrument convention, not a source-defined
latency requirement. The shared interface requires each direct `li` child to
contain one visible direct-child `label`. Compare exact label text, so whitespace
formatting outside the label is harmless and missing input trimming remains
detectable. Hidden labels cannot count as successfully displayed todos.

The trusted Playwright controller runs in Node outside the generated page.
Generated HTML is delivered only as a browser document at an inert HTTP origin;
other requests are aborted and CSP blocks network, frames, external resources
and form navigation. No generated content is executed as Node. Focus is observed
through a CDP isolated world to avoid page-overridden DOM getters. Screenshot is
captured externally before any interaction. Controls include a page that spoofs
`document.activeElement`, `window.report`, `process` and `require`; it must still
fail focus. This is bounded tamper testing, not comprehensive adversarial proof.

Runtime: Playwright npm1.58.2 and matching official image1.58.2, digest pinned in
Dockerfile, npm lockfile integrity retained. Official guidance consulted2026-09-22:
https://playwright.dev/docs/docker. The executor accepts only an immutable built
image ID, runs non-root with no network, read-only root, dropped capabilities,
no-new-privileges, bounded CPU/memory/processes, and a timeout. Only one app.html
input and one dedicated output directory are mounted. Chromium's inner sandbox
is disabled; Docker is the containment boundary. No credential or Docker-socket
mounts; this is not proof against browser/container escape exploits.

Build with `docker build -t focus-chain:20260922 eval/fixtures/focus-chain`.
Resolve `docker image inspect --format '{{.Id}}' focus-chain:20260922`, then run
`python eval/fixtures/focus-chain/qualify.py --image sha256:... --output NEW_DIR`.
All nine expected outcomes and exact failed assertion IDs must match.
Additional controls accept outer label formatting, reject invisible labels,
reject omitted trimming, and classify a missing label as interface error. Qualification records hashes of runtime
files, the exact image ID and original trusted reports. Do not change any frozen
runtime file between qualification and collection; requalify after changes.

`execute(image, inputs, output, timeout=90)` writes report.json, executor.json,
initial-focus.png, container-command.json and container.log. Complete reports
have schema focus-chain-browser/v1 and all seven exact assertion IDs. Wrong
exit status, missing assertions, malformed reports, app-hash mismatch, missing
screenshot, interface failure or runtime failure are not requirement failures.
Generated outputs receive no trusted-fixture fallback or implicit repair.
