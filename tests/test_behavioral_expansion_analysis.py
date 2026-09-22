"""Behavioral contracts for the uncollected direct-code expansion."""
from collections import Counter
import pytest

from scripts import behavioral_expansion as study


def cases():
    return [
        {'id': 'a1', 'project_id': 'alpha', 'status': 'qualified', 'variants': {'A': 'full', 'B': 'rewrite', 'C': 'omitted'}},
        {'id': 'a2', 'project_id': 'alpha', 'status': 'qualified', 'variants': {'A': 'full', 'B': 'rewrite', 'C': 'omitted'}},
        {'id': 'b1', 'project_id': 'beta', 'status': 'qualified', 'variants': {'A': 'full', 'B': 'rewrite', 'C': 'omitted'}},
    ]


def result(slot, category, target_failed=None):
    return {'slot_id': slot['slot_id'], 'category': category, 'target_failed': target_failed}


def test_schedule_is_balanced_deterministic_and_contains_no_source_or_target_text():
    slots = study.plan_slots(cases(), seed=9)
    assert len(slots) == 54
    assert slots == study.plan_slots(cases(), seed=9)
    assert len({s['slot_id'] for s in slots}) == 54
    assert Counter((s['intent_id'], s['model'], s['variant']) for s in slots) == {
        (case['id'], model, arm): 3 for case in cases()
        for model in study.MODELS for arm in ('A', 'B', 'C')
    }
    assert all(set(s) == {'slot_id', 'intent_id', 'project_id', 'model', 'replication', 'variant'} for s in slots)
    assert all('full' not in str(s) and 'omitted' not in str(s) for s in slots)


@pytest.mark.parametrize('mutate', [
    lambda cs: cs[0].update(status='candidate_pending_qualification'),
    lambda cs: cs[0]['variants'].pop('B'),
    lambda cs: cs[1].update(id='a1'),
])
def test_schedule_rejects_unqualified_or_malformed_cases(mutate):
    cs = cases(); mutate(cs)
    with pytest.raises(ValueError): study.plan_slots(cs)


def test_missing_positions_are_unknown_and_bounds_keep_planned_denominator():
    slots = study.plan_slots(cases(), seed=9)
    selected = [s for s in slots if s['intent_id'] == 'a1' and s['model'] == study.MODELS[0]]
    rows = [result(s, 'pass', False) for s in selected if s['variant'] == 'A']
    c = [s for s in selected if s['variant'] == 'C']
    rows += [result(c[0], 'target_only_failure', True), result(c[1], 'pass', False)]
    report = study.summarize(slots, rows)
    group = next(g for g in report['groups'] if g['intent_id'] == 'a1'
                 and g['model'] == study.MODELS[0] and g['variant'] == 'C')
    assert group['planned'] == 3 and group['target_failed'] == 1
    assert group['target_passed'] == 1 and group['unknown'] == 1
    assert group['target_failure_bounds'] == pytest.approx([1/3, 2/3])
    contrast = next(c for c in report['contrasts'] if c['intent_id'] == 'a1'
                    and c['model'] == study.MODELS[0] and c['comparison'] == 'C-A')
    assert contrast['difference_bounds'] == pytest.approx([1/3, 2/3])
    absent = next(g for g in report['groups'] if g['intent_id'] == 'a2'
                 and g['model'] == study.MODELS[0] and g['variant'] == 'C')
    assert absent['target_failure_bounds'] == [0.0, 1.0]
    assert report['planned'] == 54 and report['recorded_rows'] == 5
    assert report['executable'] == 5 and report['unknown'] == 49


def test_equal_project_weight_differs_from_equal_intent_weight():
    slots = study.plan_slots(cases())
    rows = []
    for s in slots:
        failed = s['variant'] == 'C' and s['project_id'] == 'alpha'
        rows.append(result(s, 'target_only_failure' if failed else 'pass', failed))
    report = study.summarize(slots, rows)
    model = study.MODELS[0]
    project_weight = next(x for x in report['project_weighted'] if x['model'] == model and x['comparison'] == 'C-A')
    intent_weight = next(x for x in report['intent_weighted'] if x['model'] == model and x['comparison'] == 'C-A')
    assert project_weight['difference_bounds'] == [0.5, 0.5]
    assert intent_weight['difference_bounds'] == pytest.approx([2/3, 2/3])


@pytest.mark.parametrize('bad', [
    {'category': 'provider_error', 'target_failed': True},
    {'category': 'pass', 'target_failed': None},
    {'category': 'target_only_failure', 'target_failed': False},
    {'category': 'unknown_category', 'target_failed': None},
])
def test_invalid_observation_contract_fails_closed(bad):
    slots = study.plan_slots(cases())
    with pytest.raises(ValueError): study.summarize(slots, [{'slot_id': slots[0]['slot_id'], **bad}])


def test_duplicate_and_unplanned_observations_fail_closed():
    slots = study.plan_slots(cases()); row=result(slots[0], 'pass', False)
    with pytest.raises(ValueError): study.summarize(slots, [row, row])
    with pytest.raises(ValueError): study.summarize(slots, [dict(row, slot_id='unplanned')])


def test_incomplete_or_repeated_planned_replications_fail_closed():
    slots = study.plan_slots(cases())
    with pytest.raises(ValueError): study.summarize(slots[1:], [])
    changed = [dict(slot) for slot in slots]
    first = changed[0]
    peer = next(slot for slot in changed if slot['intent_id'] == first['intent_id']
                and slot['model'] == first['model'] and slot['variant'] == first['variant']
                and slot['replication'] != first['replication'])
    peer['replication'] = first['replication']
    with pytest.raises(ValueError): study.summarize(changed, [])


def test_one_intent_cannot_be_counted_in_two_projects():
    slots = study.plan_slots(cases())
    copies = []
    for slot in slots:
        if slot['intent_id'] == 'a1':
            copies.append({**slot, 'project_id': 'beta', 'slot_id': slot['slot_id'] + '-copy'})
    with pytest.raises(ValueError): study.summarize(slots + copies, [])


def test_recorded_row_does_not_imply_executed_output():
    slots = study.plan_slots(cases())
    report = study.summarize(slots, [result(slots[0], 'not_attempted')])
    assert report['recorded_rows'] == 1 and report['executable'] == 0
    assert report['unknown'] == 54


def test_unmet_target_prerequisite_remains_unknown_in_analysis():
    slots = study.plan_slots(cases())
    report = study.summarize(slots, [result(slots[0], 'target_not_evaluable')])
    assert report['executable'] == 0 and report['unknown'] == 54
