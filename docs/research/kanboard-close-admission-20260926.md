# Kanboard close-task board visibility: admission deferred

The [Kanboard source](../../data/e2e-six-projects/sources/kanboard/tasks.md)
states that closing a task hides it from the board, while Closed tasks remains
accessible. [A/B/C](../../data/e2e-kanboard-close/arms-20260926.json) retain
closed-task reachability in all arms and omit only board hiding in C. The
bounded UI keeps `status` and `boardVisible` independent; only generated
behavior changes either field on a click. The browser checks the board after
reload, then checks the Closed tasks filter, an unrelated task, and two fixture
titles. Eight authored controls passed in the fixed browser image. Qualification
receipt: `a6049c8243518222e0bd3ff850a090339e45c539a1c7771c9009fcf115655d66`.

The independent review gate required unanimity. Two full pre-generation panels
both returned **2 ACCEPT, 1 DEFER**. Sol and Astra accepted the independence of
the two saved fields, source mapping, and visible endpoint. Luna interpreted
the common rendering or the endpoint differently and deferred. The second
review request clarified that the common click handler does not mutate state
and was sent equally to all three models. The dissent remained. Original
panel receipt: `5053420597344e8d822793862826b814506013e0f750c60bea7cc55116f47876`;
clarified panel receipt: `12fa6ce66d61b7ef5e09ffd0c5d02ff7be9b4f07b9cb10254c000f3b23efd044`.

**No experimental generation was dispatched.** The gate is unresolved and
this candidate remains one of the seven pending new obligations. A separate
adjudication of source-to-endpoint validity or a redesigned endpoint is needed
before freezing A/B/C. Repeating the same model vote to chase agreement would
not supply independent evidence.
