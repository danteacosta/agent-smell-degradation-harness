# Research: Nextcloud permanent deletion as an E2E endpoint

- **Slug:** `2026-09-27-nextcloud-permanent-delete-source`
- **Date:** 2026-09-27
- **Status:** in-progress
- **Triggered by:** The 2–1 pre-generation review of the permanent-delete candidate.
- **Informed:** [candidate admission](nextcloud-permanent-delete-admission-20260926.md)

## Question

Does the official Nextcloud source support observing an item as absent from
the Deleted files interface after selecting **Delete permanently**?

## Sources

### [Deleted files, Nextcloud 36 User Manual](https://docs.nextcloud.com/server/latest/user_manual/en/files/deleted_file_management.html)

- **Authors / Org:** Nextcloud contributors.
- **Type:** vendor documentation, primary source.
- **Published:** ongoing; page displayed Nextcloud 36 when accessed.
- **Accessed:** 2026-09-27.
- **Relevance:** high.
- **What this contributed:** The manual names the Deleted files interface
  as the location for manual permanent deletion and says that selecting
  **Delete permanently** permanently deletes an item in the trash bin.
  It does not spell out a particular DOM disappearance animation. Absence
  after refresh is an operational observation of deletion, still requiring
  independent endpoint review.

## Synthesis

The source supports an item-level deletion claim in the trash context. It
does not explicitly demand an untouched unrelated item or specify the exact
UI timing. A revised endpoint may treat removal after refresh as the target
and another item as a preservation control, but the previous dissent cannot
be considered resolved merely by finding the same manual text online.

## Downstream uses

- [Nextcloud permanent-delete admission](nextcloud-permanent-delete-admission-20260926.md).
