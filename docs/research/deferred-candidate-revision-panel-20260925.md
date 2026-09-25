# Deferred E2E candidate revision panel

Status: **prospective revision screening completed before oracle construction and generation**. This panel contains no implementation outcomes and supplies no evidence for H1 or H2.

## Why a second panel was run

The first screening admitted three of twelve candidate obligations. The nine deferred candidates were narrowed using fuller, hash-bound source context. The panel artifacts and commit order record the revisions as preceding oracle construction and A/B/C generation. This is a custody claim supported by the retained private prompt and response hashes; the checked-in stage labels alone are not independent proof of chronology.

Three isolated Codex sessions reviewed the same revision packet at high reasoning effort. A candidate advanced only when `gpt-6-astra`, `gpt-6-sol`, and `gpt-6-luna` all returned `ACCEPT`.

- Revision packet SHA-256: `a162e3f64440630a3d137e774b24b652a37f3052e3e63ec55d878c41f2050454`
- Prompt SHA-256: `df6465fde2c41a966730c2de57ef9ed1df0e676ca8e7570de4fe1f5bdb99d192`
- Astra response SHA-256: `c6a6af8bf04cd387c3e3b892ac7a709f462b508267b6effb2e58724efeb00ee2`
- Sol response SHA-256: `c53765208c3de4f67aedb4ab85bef91cbc334853ab0ca09d329510dad9f4bed2`
- Luna response SHA-256: `61fe00171828538b505446088a506850046b8b85e05127390f1d38ab31e49e4b`

Raw prompts and responses remain outside Git under `.private-research-evidence/deferred-candidate-revision-panel-20260925/`. The public targets, source locators, decisions, reasons, and hashes are recorded in `data/e2e-multi-obligation/deferred-candidate-revision-panel-20260925.json`.

## Result

Two revised candidates passed unanimously:

| Candidate | Project | Bounded target |
| --- | --- | --- |
| `paperless-accept-duplicate` | Paperless-ngx | Under default settings, consuming the same-checksum file twice leaves two document records. |
| `nextcloud-delete-permanently` | Nextcloud | Permanently deleting one selected item removes it after refresh while an unrelated trashed item remains. |

Seven remain deferred. The two RealWorld candidates still lack a source-supported browser journey for the API contracts. Kanboard still lacks a precise visible property set. Paperless suggestions still combine accept and reject obligations. Reviewers disagreed about whether the two TodoMVC targets isolate a single endpoint, and the OpenProject example did not freeze an unambiguous work unit.

Together with the three candidates admitted by the first panel, the prospective pool now contains **five obligations from four projects**:

- Kanboard: close hides a task from the board;
- Paperless-ngx: default duplicate ingestion retains two records;
- Nextcloud: restore into a name conflict, and delete permanently;
- OpenProject: reject Remaining work greater than Work.

This pool represents at most **90 planned positions**: `5 obligations × 3 arms × 2 model configurations × 3 repetitions`. It is still an upper bound. Each obligation requires an independently qualified browser oracle, frozen A/B/C texts, target and non-target mutants, runtime, schedule, and custody record before generation.

## Interpretation

The revision panel increases the prospective pool without weakening the unanimous gate. It does not increase the number of projects already represented by qualified experimental E2E outcomes. TodoMVC and RealWorld still need replacement or further revision if the collection is to cover all six projects. No call from this screening should be counted among the planned 90 generations.

Subsequent prospective work is recorded in `third-candidate-revision-panel-20260925.md`. That panel replaces or narrows the remaining cases before oracle construction and raises the eligible ceiling to 11 obligations across all six projects; it does not change the historical result reported here.
