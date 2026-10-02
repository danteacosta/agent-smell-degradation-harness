# Omission Bench reference results

Target-rule failures by arm. A good model fails rarely in A and B; C shows how often a missing rule is also missing from the interface.

| Model | A failures | B failures | C failures | Cases with a C failure |
| --- | ---: | ---: | ---: | ---: |
| gpt-5.6-luna | 1/21 | 0/21 | 13/21 | 5/7 |
| gpt-5.6-sol | 0/21 | 0/21 | 15/21 | 5/7 |

Per case and arm: `reference-leaderboard.json`. Runs are repetitions of the same case, not independent requirements.
