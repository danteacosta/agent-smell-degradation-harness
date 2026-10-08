# Final adjudication must preserve the frozen item groups

Date: 2026-10-08. Scope: offline shared-omission test audit.

## Problem and correction

The scorer checked each individual coder's item group against the private frozen key, but did not apply the same check to final adjudication. Moving an item from P to R (or R to P), with a valid destination category, retained all 104 IDs and passed validation. Aggregation then used the original group, potentially omitting the incompatible category from reported counts. This is a reproduced input-validation defect, not evidence that any existing human workbook was corrupted.

`scripts/test_omission_audit.py` now rejects final group mismatches before aggregation. The frozen key remains authoritative. Two regression cases move an actual XLSX row between sheets, align columns by header, preserve every item and supply a valid destination label and literal quote. Both failed before the correction because the scorer accepted the workbook; both pass after it. Existing valid end-to-end scoring and separate calibration tests remain green.

Validation: `python -m pytest tests/test_test_omission_audit.py -q`: **13 passed**. No provider calls or experimental reruns.

## Literature bridge and remaining gate

Klie et al. (2024), [DOI 10.1162/coli_a_00516](https://doi.org/10.1162/coli_a_00516), motivates auditing annotation postprocessing as well as agreement. It does not validate this study's labels. See the canonical literature matrix for evidence status and limitations.

Next: independent human coding after the six-item calibration, then explicit adjudication and scoring with the frozen key. This change does not supply those labels, establish H1/H2, change the measurement policy or decide the pending primary-task choice. New tester results reuse the same requirements and implementations; they do not add independent projects.
