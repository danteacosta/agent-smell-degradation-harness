# Requirements-smell discovery corpus

This directory contains the approved 12-case discovery corpus. It exceeds the
advisor's minimum of ten cases and covers two source requirements from each of
six projects in the public ARTA dataset: NFR, CCTNS, ERTMS, EIRENE/FUN,
GAMMA-J and Peering.

Each JSON record keeps four different things separate:

- `source_excerpt`: the requirement text found in the ARTA source JSON;
- `clean_requirement`: a controlled, testable reconstruction;
- `smelly_requirement`: the same intended feature after one condition is
  removed or weakened; and
- `oracle_spec.behavior_codegen._execution`: private local-evaluator metadata
  containing hidden inputs, expected outputs and small reference functions.

The historical `codegen` and `test_gen` families remain declarative and do not
contain executable metadata. The discovery-only `behavior_codegen` family
emits one `source_code` field containing a side-effect-free Python function
named `evaluate`.

Run the corpus validator from the repository root:

```text
python3 data/pairs/discovery/loader.py
```

It checks that there are exactly twelve records, that the manifest matches the
records, that all six projects are represented, that ERTMS-002 points to source
requirement 16, and that executable evaluator metadata appears only under
`behavior_codegen`.

These are discovery artifacts, not confirmatory results. The source provides
ecological provenance; the clean/smelly pair is a controlled experimental
contrast. `natural_variant: false` records that the pair was constructed for
the experiment rather than copied as an originally published pair.

## Provenance and licensing

The records point to the ARTA repository commit and the ARTA Zenodo dataset
record. The repository is MIT-licensed, but several underlying requirements
come from external standards, procurement documents or project specifications
whose terms may differ. The `licensing_notes` field records that uncertainty.
Before publishing the excerpts or redistributing the complete source text,
check the license of each original document and prefer links, hashes and short
research excerpts where full-text redistribution is not clearly permitted.
