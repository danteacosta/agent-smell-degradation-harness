# RealWorld article-author collection freeze

Goal: prepare an execution packet for the reviewed RealWorld article-author UI
case without dispatching a provider, then provide a single-attempt collector
whose generation and browser phases remain separated.

Architecture: keep a narrow RealWorld collector. Reuse the existing private
write, inventory, fresh-preflight and raw-HTML admission primitives from the
persistence collector. Validate the canonical PR79 admission package directly,
freeze its exact schedule and requests, bind the complete Python and RealWorld
browser runtime, and invoke the qualified RealWorld executor only after the
generation phase has ended. No generalized endpoint framework is introduced.

Acceptance scenarios:

1. Given the canonical reviewed admission, fresh ChatGPT-authenticated preflight
   and a selected CLI, preparation creates a new private packet outside the
   repository and binds exact parent, executable, runtime, image and schedule
   bytes, including the independently reviewed local qualification's exact
   image and manifest SHA-256. Preparation performs zero provider calls.
2. Given an unchanged frozen packet, run validates all custody before writing
   its durable run marker or invoking a provider. It calls each planned request
   at most once, sequentially and in frozen order, with low reasoning effort,
   one-call concurrency and no API-key fallback, retry, resume or repair.
3. Given valid raw HTML, all generation finishes before the first browser
   execution. Given invalid output, its raw response remains evidence and its
   row remains unknown. Given provider infrastructure failure, that attempt is
   recorded and every later slot remains `not_attempted`.
4. Given generated artifacts, the qualified RealWorld executor evaluates them
   with the frozen image. Schedule arms are normalized to analyzer variants and
   the fixed denominator remains 18, including missing and invalid outcomes.
5. Given interruption, executable/runtime/parent drift, or self-consistent
   tampering with schedule or requests, no provider call occurs. A second run
   fails rather than resuming or overwriting evidence.

This step freezes collection machinery only. It produces no experimental
result, executes no real model call, and supports no H1/H2 conclusion.
