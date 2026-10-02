from __future__ import annotations

import json

from scripts import reproduce_evidence


def test_every_public_row_matches_the_stated_number() -> None:
    rows = reproduce_evidence.build()
    assert [r for r in rows if r["status"] == "mismatch"] == []
    assert sum(r["status"] == "reproduced" for r in rows) == 10


def test_main_exits_nonzero_on_a_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(reproduce_evidence, "build",
                        lambda: [{"row": "x", "stated": "1", "recomputed": "2", "status": "mismatch", "source": "s"}])
    assert reproduce_evidence.main([]) == 1


def test_recovered_rows_preserve_original_and_scope_diagnostic() -> None:
    rows = reproduce_evidence.recovered_evidence()
    assert len(rows) == 4
    assert all(r['status'] == 'reproduced' for r in rows)
    assert rows[0]['recomputed'] == 'complete 9/9 versus defective 6/9'
    assert rows[1]['recomputed'] == '18 ordinal labels: A 0:6; B 0:6; C 2:6; 6 C-worse pairs'
    assert rows[2]['recomputed'] == '34 pairs: 14 C worse, 10 equal, 1 C better, 9 unknown'
    assert rows[3]['recomputed'] == '34 pairs: 14 C worse, 11 equal, 1 C better, 8 unknown'


def test_public_reproduction_retains_unavailable_cohorts() -> None:
    rows = reproduce_evidence.build()
    missing = [r['row'] for r in rows if r['status'] == 'no_public_source_found']
    assert len(missing) == 2
    assert any('11 obligations' in r for r in missing)
    assert any('60 pairs' in r for r in missing)


def test_recovered_reproduction_rejects_changed_html_in_scope_correction() -> None:
    import copy
    import pytest
    packet = copy.deepcopy(json.loads((reproduce_evidence.ROOT / 'data/recovered-evidence-20261002/rows.json').read_text()))
    packet['rows'][2]['scope_correction']['rows'][0]['original_html_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='HTML'):
        reproduce_evidence.recovered_evidence(packet)


def test_recovered_reproduction_rejects_missing_or_duplicate_pairs() -> None:
    import copy
    import pytest
    packet = json.loads((reproduce_evidence.ROOT / 'data/recovered-evidence-20261002/rows.json').read_text())
    for change in ['missing', 'duplicate', 'changed_identity']:
        altered = copy.deepcopy(packet)
        rows = altered['rows'][2]['base']['rows']
        if change == 'missing': rows.pop()
        elif change == 'duplicate': rows.append(copy.deepcopy(rows[0]))
        else: altered['rows'][2]['scope_correction']['rows'][0]['source_slot'] = 'wrong-slot'
        with pytest.raises(ValueError):
            reproduce_evidence.recovered_evidence(altered)


def test_unknown_ordinal_label_is_not_counted_as_zero() -> None:
    import copy
    packet = copy.deepcopy(json.loads((reproduce_evidence.ROOT / 'data/recovered-evidence-20261002/rows.json').read_text()))
    base = packet['rows'][2]['base']['rows']
    row = next(r for r in base if r['case_id'] == 'kanboard-closed-filter' and r['arm'] == 'A' and r['severity'] == 0)
    row['severity'] = None
    rows = reproduce_evidence.recovered_evidence(packet)
    assert rows[2]['status'] == 'mismatch'
    assert rows[3]['status'] == 'mismatch'


def test_recovered_data_receipt_is_checked_before_reproduction(tmp_path, monkeypatch) -> None:
    import shutil
    import pytest
    relative = 'data/recovered-evidence-20261002'
    shutil.copytree(reproduce_evidence.ROOT / relative, tmp_path / relative)
    path = tmp_path / relative / 'rows.json'
    path.write_text(path.read_text() + ' ')
    monkeypatch.setattr(reproduce_evidence, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='receipt'):
        reproduce_evidence.recovered_evidence()


def test_recovered_reproduction_rejects_ineligible_or_mixed_identity_labels() -> None:
    import copy
    import pytest
    original = json.loads((reproduce_evidence.ROOT / 'data/recovered-evidence-20261002/rows.json').read_text())
    for change in ['ineligible', 'severity_boolean', 'project', 'replication']:
        packet = copy.deepcopy(original)
        row = next(r for r in packet['rows'][2]['base']['rows'] if r['severity'] == 0)
        if change == 'ineligible': row['eligible'] = False
        elif change == 'severity_boolean': row['severity'] = False
        elif change == 'project': row['project_id'] = 'wrong-project'
        else: row['replication'] = 999
        with pytest.raises(ValueError):
            reproduce_evidence.recovered_evidence(packet)


def test_reproduction_cli_shows_recovered_and_unavailable_rows() -> None:
    import subprocess
    import sys
    completed = subprocess.run([sys.executable, str(reproduce_evidence.ROOT / 'scripts/reproduce_evidence.py')],
                               capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert 'original retrospective labels' in completed.stdout
    assert 'separate post-hoc scope diagnostic' in completed.stdout
    assert "'reproduced': 10, 'no_public_source_found': 2" in completed.stdout


def test_duplicate_cohort_cannot_silently_replace_an_existing_cohort() -> None:
    import copy
    import pytest
    packet = json.loads((reproduce_evidence.ROOT / 'data/recovered-evidence-20261002/rows.json').read_text())
    packet['rows'].append(copy.deepcopy(packet['rows'][0]))
    with pytest.raises(ValueError, match='three distinct'):
        reproduce_evidence.recovered_evidence(packet)
