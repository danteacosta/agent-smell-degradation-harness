# RealWorld comment Delete visibility: admission deferred

> **Custody correction (2026-10-01):** this note records the earlier admission state. Two later 27 September pilots each attempted 18 generations and browser checks. See the [later-pilot audit](2026-10-01-unreported-browser-pilots-custody.md); the zero-generation statement below is no longer current.

The [source](../../data/criteria-expansion/sources/realworld/docs__src__content__docs__specifications__frontend__routing.md)
requires the Delete comment button to be shown only to the comment author.
The [A/B/C arms](../../data/e2e-realworld-comment-delete/arms-20260927.json)
preserve the article comment and remove only author-only visibility in C.
The browser replica compares an author and another authenticated viewer in
separate contexts on the same comment, with two sets of identities. Comment,
article and viewer visibility are controls. The generated handler alone
decides whether to show Delete.

The first qualification attempt expected a duplicated comment row to be a
non-target failure, but exact identity became ambiguous, correctly producing
an interface error. The failed packet remains private. The next qualification
passed **10/10 controls** (receipt
`e6c25cd0d84d2afdb1f976b25a9cf583d461273e0324b178f8e4e01ac22fcb78`).
Its review returned one ACCEPT and two DEFER: one reviewer questioned A/B
equivalence and another found that the oracle required button enablement and
appeared to reject a hidden non-author button. Review receipt:
`c6d774c779ea98bdbec4ff9e494ca62b018cc12c8ecfaf1ea30c56f8f5f3892c`.

Before any generation, the prompts were clarified and the oracle changed to
score visible buttons only, without requiring enablement. A new hidden-button
control passed; the revised oracle qualified **11/11 controls**, receipt
`2c99f25b0a9abf8b7bfe273cddd0d7e5d13ffc26cb8a214518e1c93811da0ca0`.
A separate review returned **2 ACCEPT and 1 DEFER**, receipt
`9040159068e44fd9f9fe56f7bf1ac13b22d96abe381eb815df34c4192c552b50`.
The dissent reason treated C's omission of the author-only clause as a reason
for deferral; the other two reviewers viewed it as the intended single
manipulation. The strict unanimous gate did not pass. Repeating an unchanged
vote to obtain agreement would not resolve the methodological disagreement.

**No experimental generation was dispatched.** This is an instrument and
admission result only. It does not increase the count of executed obligations
or provide evidence for H1/H2.
