# Requirement sampling, first round (2026-10-02)

The pre-registered sampling frame yields **43 suggested requirements from 8
projects** in its first screening round, enough for the 30-requirement,
8-project target once two human reviewers confirm them. With the cap of 6 per
project the confirmatory sample would hold 34 requirements.

The suggestions come from an assistant pre-screen. They are not admissions:
the pre-registration requires two independent human reviewers, blind to any
outcome, and a third to resolve disagreements.

## Frame and screening by project

| Project | Docs license (repository) | Frame candidates | Screened | Suggested |
| --- | --- | ---: | ---: | ---: |
| OpenProject | GPL-3.0 | 204 | 30 | 14 |
| WeKan | MIT | 127 | 30 | 7 |
| Nextcloud (user manual) | CC BY 3.0 | 134 | 30 | 6 |
| Mattermost (end-user guide) | BSD-style (`LICENSE.txt`) | 50 | 30 | 6 |
| Paperless-ngx | GPL-3.0 | 42 | 30 | 4 |
| Mealie | AGPL-3.0 | 10 | 10 | 3 |
| Immich | AGPL-3.0 | 51 | 30 | 2 |
| RealWorld | MIT | 9 | 9 | 1 |
| Joplin | AGPL-3.0 | 16 | 16 | 0 |
| Kanboard | MIT | 15 | 15 | 0 |
| StrictDoc | Apache-2.0 | 3 | 3 | 0 |
| Zammad | AGPL-3.0 | 25 | 25 | 0 |
| TodoMVC | MIT | 0 | 0 | 0 |
| **Total** | | **686** | **258** | **43** |

The license column records the repository license as found; the rights to
transform and process each excerpt still need the same review as the pilot
corpus.

Four projects contribute nothing in this window: Kanboard and Zammad changed
only developer and installation pages, Joplin's user pages describe desktop
or server features, and StrictDoc's changes were configuration. Three
suggested Paperless-ngx rules (inbox suggestions, duplicate consumption,
nested tags) are already pilot cases and are excluded.

## Why candidates were excluded

| Reason | Count |
| --- | ---: |
| No single testable rule (feature description, navigation, examples) | 82 |
| Operations or configuration (install, server, authentication setup) | 68 |
| Not the web interface (mobile, desktop, command line) | 46 |
| No rule change (formatting, images, rewording) | 16 |
| Already used in a pilot | 3 |

Exclusion reasons were assigned by path and text heuristics after the
admission decision, so they describe the pool rather than justify each item.

## What the suggested rules look like

The 43 rules cover state changes caused by another action (duplicating a
board starts a fresh activity history), permissions (only administrators can
mark a project as a template), derived values (a meeting section shows the
sum of its items' durations; 1 cup plus 2 cups of cheese become 3 cups in a
shopping list), defaults (new work packages use automatic scheduling) and
refusals (dropping several boards on Home shows "Please select only one
board" and changes nothing). Each entry in the screening file carries the
target rule and a sketch of the pass and fail observation for its oracle.

About half of the suggested cases (21 of 43) are additions: the
documentation gained the rule sentence in the window, so the older text is a
natural omission of the same rule. That makes these cases usable both for the controlled A/B/C design and
as a natural old/new comparison.

## Files and reproduction

- `scripts/mine_requirement_candidates.py`: the frame, with every filter in
  code.
- `data/requirement-sampling/frame-20261002.jsonl`: all 686 frame candidates.
- `data/requirement-sampling/screening-20261002.json`: the 258 screened
  candidates with the pre-screen suggestion, target rule and oracle sketch.

```sh
# one shallow clone per project under REPOS/<name>, history since 2024-12-15
git clone --shallow-since=2024-12-15 --filter=blob:limit=2m --no-checkout \
  https://github.com/opf/openproject REPOS/openproject
# ... same for the other projects listed in PROJECTS ...
python scripts/mine_requirement_candidates.py --repos REPOS --out candidates.jsonl
```

Commit timestamps and shallow boundaries make the frame reproducible only for
the same window end (2026-09-30).

## Next step

Two reviewers screen the 258 candidates blind to these suggestions, then
code the four recoverability covariates for the admitted ones, before any
generation.
