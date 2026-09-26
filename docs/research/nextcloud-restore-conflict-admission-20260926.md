# Nextcloud restore-name conflict: admission deferred

The [Nextcloud source](../../data/e2e-six-projects/sources/nextcloud/deleted_file_management.rst)
states that a restored item receives a unique name when an item of the same
name already exists. The planned bounded browser journey presents a deleted
file and an active collision in the Files view, clicks Restore, reloads, and
checks both file identities and names. This candidate passed the earlier
source-screening panel, but **no experimental generation was admitted**.

The [A/B/C texts](../../data/e2e-nextcloud-restore-conflict/arms-20260926.json)
keep the restore operation in every arm and remove only the collision-name
clause in C. An authored browser fixture and oracle passed eight controls in
each of three versions. The current v3 distinguishes a same-name mutation
from no restore, unrelated-file corruption, failure to remove from trash,
missing action and script error. Its private qualification receipt is
`6b1fe343cc2e3880c57f60f4d86c6f6df128069f140a3c6a21f956c815a773d7`.

Independent pre-generation review exposed contract defects:

| Version | Review outcome | Preserved review receipt |
| --- | --- | --- |
| v1 | Luna DEFER: oracle inspected a private handler state rather than only UI readiness. | `94819066b118ab935e0bdbe03fde4be51a96b595e5870386095396b80fc3` |
| v2 | Luna ACCEPT, Sol DEFER: missing location/writability representation and target/non-target conflation. | `e5207d1a149611ee097c51c24c33735a7f067ba8a3d16d5434f03969cc0685d9` |
| v3 | Luna DEFER: original destination still not established as a real path, and the target assertion compares only with the colliding file rather than every active name. | `c843a2323279ffac5cdd49d5aa8c0164473a5b66cfef1e16b10f916163300a14` |

The v3 qualifier demonstrates sensitivity for its **current** contract, but
does not establish source-to-oracle validity. Further local edits after three
review cycles risk patching symptoms. A new design should model file location
as data, exercise a writable original directory, and compare the restored
name against the entire active-file namespace. It should then get a fresh
independent review and qualification before any A/B/C generation. The
candidate remains among the seven new obligations pending; it contributes no
E2E outcome to H1 or H2.
