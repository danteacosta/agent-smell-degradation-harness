# Immich MP2T draft refreshed from frame-end documentation

Status: draft correction and authored-control qualification, not model-generation evidence or selection approval.

The [frame-end documentation](https://github.com/immich-app/immich/blob/a3c8b359f2fdc47699f1530215a23fe8bd34c454/docs/docs/features/supported-formats.md#L39) lists `.mts .m2ts .m2t .ts` for MP2T. Its Git blob identity is `889a41a9d12831b3d6a114ea751392936e9c5373`. The discovery commit is retained separately from the proposed arm-A snapshot identity in the case config.

A, B and C now all include `.ts`; C omits only `.m2t`. The journey uploads `.ts` in both fixtures and classifies its acceptance as a non-target obligation. A new authored control accepts `.m2t` but rejects `.ts`, separating a stale supported-format list from the experimental omission.

Acceptance contract: reference implementations accept both extensions; omitting `.m2t` fails only the target; rejecting `.ts` fails only non-target obligations. The browser runner reloads the page and checks the saved visible upload decisions.

Eight authored controls qualified in the pinned Docker image, with all expected classifications matched. [Public qualification and reports](../../data/selection-case-qualification/immich-ts-snapshot-20261003/qualification.json) bind the scaffold, runner, qualifier and report hashes. Screenshots and execution receipt remain in the separate private evidence packet. Previous qualification packets remain unchanged; they do not qualify the modified runner.

The new prompt regression failed on the previous arm A and passes after the correction. The complete case-spec suite passed (43 tests). No calls to generation models were made. Selection, independent arm review and freezing remain prerequisites for collection. Security, SOLID and clean-code review found no added provider, storage or access boundary; the change stays within the existing draft-case format.
