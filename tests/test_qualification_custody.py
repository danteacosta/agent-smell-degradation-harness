"""A second successor retains earlier evidence and rejects ambiguous ownership."""
import copy
import json
import os

import pytest

from eval import qualification_plan, scoped_judge_study
from test_addressed_comparison_plan import snapshot
from test_qualification_plan import make_plan


def api():
    from eval import qualification_custody
    return qualification_custody


def prepared_qualification(tmp_path):
    plan=make_plan(tmp_path/'old')
    directory=tmp_path/'qualified'
    manifest=api().create_run(plan,directory,approval=True)
    return directory,manifest


def test_exclusive_closure_preserves_old_bytes_and_records_actual_disposition(tmp_path):
    plan=make_plan(tmp_path/'old'); before=snapshot(tmp_path/'old')
    directory=tmp_path/'qualified'
    manifest=api().create_run(plan,directory,approval=True)
    after=snapshot(tmp_path/'old')
    assert all(after[k]==value for k,value in before.items())
    assert len(after)==len(before)+1
    assert api().load_run(directory)==manifest
    closure=json.loads((directory/'closure.json').read_text())
    assert closure['retained_predecessor_spent_microusd']==plan['budget']['predecessor_spent_microusd']
    assert closure['cancelled_direct_microusd']==plan['budget']['cancelled_direct_microusd']
    assert closure['released_contingency_microusd']==plan['budget']['released_contingency_microusd']
    assert os.stat(directory).st_mode&0o777==0o700
    assert os.stat(directory/'manifest.json').st_mode&0o777==0o600
    assert os.stat(api().claim_path(plan)).st_mode&0o777==0o600
    with pytest.raises(ValueError,match='successor_already_claimed'):
        api().create_run(plan,tmp_path/'second',approval=True)
    assert not (tmp_path/'second').exists()


def test_missing_approval_has_no_write(tmp_path):
    plan=make_plan(tmp_path/'old'); before=snapshot(tmp_path)
    with pytest.raises(ValueError,match='approval_required'):
        api().create_run(plan,tmp_path/'qualified')
    assert snapshot(tmp_path)==before


@pytest.mark.parametrize('name',['manifest.json','manifest-integrity.json','closure.json','ledger.jsonl','ledger.jsonl.lock'])
def test_deleted_durable_file_is_not_recreated(tmp_path,name):
    directory,_=prepared_qualification(tmp_path); (directory/name).unlink()
    before=snapshot(tmp_path)
    with pytest.raises((ValueError,OSError)): api().load_run(directory)
    assert snapshot(tmp_path)==before


@pytest.mark.parametrize('target',['claim','closure','source','environment','predecessor'])
def test_changed_custody_rejects_loading(tmp_path,monkeypatch,target):
    directory,manifest=prepared_qualification(tmp_path)
    if target=='claim': api().claim_path(manifest['plan']).write_text('{}')
    elif target=='closure': (directory/'closure.json').write_text('{}')
    elif target=='source': monkeypatch.setattr(scoped_judge_study,'source_hashes',lambda:{})
    elif target=='environment': monkeypatch.setattr(scoped_judge_study,'environment',lambda:{})
    else:
        from pathlib import Path
        (Path(manifest['plan']['lineage']['directory'])/'ledger.jsonl').write_text('{}\n')
    with pytest.raises(ValueError): api().load_run(directory)


def test_partial_preparation_and_symlink_targets_are_preserved_without_claim(tmp_path):
    plan=make_plan(tmp_path/'old'); directory=tmp_path/'partial'; directory.mkdir()
    (directory/'manifest.json').write_text('{}')
    with pytest.raises(ValueError): api().create_run(plan,directory,approval=True)
    assert (directory/'manifest.json').read_text()=='{}'
    link=tmp_path/'linked'; link.symlink_to(directory,target_is_directory=True)
    with pytest.raises(ValueError): api().create_run(plan,link/'new',approval=True)
    assert not api().claim_path(plan).exists()


def test_locked_predecessor_prevents_a_successor(tmp_path):
    from pathlib import Path
    plan=make_plan(tmp_path/'old')
    with scoped_judge_study.parent_lock(Path(plan['lineage']['directory'])):
        with pytest.raises((ValueError,OSError)):
            api().create_run(plan,tmp_path/'qualified',approval=True)
    assert not (tmp_path/'qualified').exists()


def test_changed_approved_plan_is_not_prepared(tmp_path):
    plan=make_plan(tmp_path/'old'); plan=copy.deepcopy(plan); plan['budget']['retained_shared_microusd']=0
    with pytest.raises(ValueError): api().create_run(plan,tmp_path/'qualified',approval=True)
