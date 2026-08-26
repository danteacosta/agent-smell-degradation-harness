# Verification efficacy report

This is a discovery-only, oracle-separated benchmark.
The verifier reads only `decisions.jsonl` inputs derived from pre-final observations;
`labels.jsonl` is written after decisions and contains the independent behavior labels.

- Status: `promising`
- Eligible behavior episodes: `24`
- Recall/warning coverage: `0.8333333333333334`
- Clean false-alert rate: `0.0`
- Paired discrimination: `0.8333333333333334`
- Mean lead time before artifact completion (ms): `0.08190909090909092`

The thresholds are frozen in the run output. `promising` means only that this
versioned pilot met the development criteria; it is not a population-level claim.
