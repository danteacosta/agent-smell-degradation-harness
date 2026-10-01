# Paperless inbox suggestions: prospective E2E contract

The pinned Paperless-ngx usage guide says suggestions are shown on a document detail page and are **requested automatically when an opened document still has an inbox tag**. This case tests that on-open request and its visible result. It does not test the quality of the Paperless machine-learning suggestions, acceptance/rejection, or the separate user setting that replaces automatic requests with a manual Suggest button.

ATDD acceptance: A and B retain the same automatic-on-open sentence; C retains the surrounding suggestion/detail-page description but omits that sentence. All arms receive the same fixed, offline detail-page scaffold, whose `app.document()` exposes only the opened document and whose `app.requestSuggestions(id)` returns a frozen nonempty suggestion list and records calls. The common prompt defines this API but supplies no rule about **when** to call it. With no click, the browser opens two different inbox documents in separate contexts and checks that each makes exactly one request for its own ID and shows the returned suggestion. It also checks stable title, document ID and button semantics. A missing request is a target failure only if the detail page remains evaluable; broken rendering, wrong IDs, wrong title or browser errors remain separate. Prompts, source, license, runner, authored controls, image, seed and randomized 18-slot schedule must be qualified and frozen before generation.

BDD scenarios:

- Given an inbox document and a frozen available suggestion, when its detail page opens without a click, then the request log records one call for that document and the suggestion appears.
- Given another inbox document with a different ID and suggestion, when it opens in a separate context, then the request and visible suggestion refer to the second document.
- Given a model that waits for a Suggest click, when the page opens and no click occurs, then the automatic-request target fails while the page controls remain assessable.
- Given a page that invents a suggestion without making the request, then the request target fails even if the screen appears plausible.
- Given a malformed page, missing document identity, inaccessible suggestion area or browser error, then no target pass or defect is inferred.

This is an exploratory test of one source obligation in one project. A/B/C outputs and repetitions are nested; no result from this page alone confirms H1 or H2. The browser screenshots and request log must be published with all unknowns and failures, without replacing earlier Paperless cases.
