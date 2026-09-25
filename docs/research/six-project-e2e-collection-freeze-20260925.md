# Six-project E2E collection freeze

The four-project expansion collector is ready to execute the 72 positions frozen
in `data/e2e-six-projects/freeze-20260925`. It performs no outcome-dependent
selection: Paperless-ngx, Kanboard, Nextcloud, and OpenProject were selected and
their A/B/C prompts, source custody, browser endpoints, models, repetitions, and
random order were fixed before generation.

## Acceptance contract

Given the reviewed freeze and the qualified four-project browser image, when the
collector is prepared and run once, then it must:

1. bind all 72 exact request bytes, the complete parent and qualification
   inventories, the Codex CLI executable, and every runtime file used for
   generation or classification;
2. use saved ChatGPT authentication, sequential calls, low reasoning effort,
   and no API-key fallback, retry, resume, response extraction, normalization,
   or repair;
3. finish the generation phase before opening any generated artifact in a
   browser;
4. stop the packet after the first provider infrastructure error and preserve
   the remaining positions as `not_attempted`;
5. execute admitted raw HTML in the immutable, network-disabled Docker image
   and verify the project identity, staged HTML digest, report schema, return
   code, assertion inventory, and PNG signature;
6. retain failures of non-target behavior separately from failures of the
   omitted target obligation; and
7. report fixed-denominator missingness bounds for every project, model, and
   A/B/C cell.

The collector refuses a second run of the same packet. A provider failure or
interruption therefore requires a newly frozen successor packet; the partial
packet is evidence of missingness and is never silently resumed.

## Verification before live collection

The behavior suite covers a complete successful run, exact prompt and model
order, the generation-before-browser barrier, project binding, invalid output,
provider failure, no-resume behavior, and drift in requests, executable,
runtime, parent freeze, and qualification evidence. The existing freeze and
oracle qualification suites run beside it. A local Docker smoke test reproduced
the qualified Nextcloud reference report and screenshot hashes exactly.

This remains an exploratory, purposively sampled pilot. Completing its 72
positions expands browser evidence to six projects, but does not by itself
confirm H1, evaluate H2, or estimate a population-wide effect of requirement
smells.
