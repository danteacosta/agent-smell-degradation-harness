"""Prospective E2E test-source extension using the selected mutant's own code."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import mutation_adequacy as ma

SEED = 2026100508
SCHEMA = 'shared-omission-e2e/v1'


def transform_plan(calls: list[dict], records: list[dict], incomplete: dict[str, str]) -> tuple[list[dict], dict]:
    """Freeze a seeded confirmed mutant per case and contemporaneous prompt sources."""
    selected = {r['case']: random.Random(f'{SEED}:{r["case"]}').choice(sorted(r['roles']['mutant']))
                for r in records}
    by_case = {r['case']: r for r in records}
    transformed = []
    for original in calls:
        call = dict(original)
        call['call_id'] = 'so-' + hashlib.sha256(json.dumps(
            [call['case'], call['source'], call['suite_index'], SEED]).encode()).hexdigest()[:20]
        if call['source'] == 'code_incomplete':
            case = by_case[call['case']]
            code = Path(case['artifacts'][selected[call['case']]]['artifact_path']).read_text()
            call['prompt'] = ma.ta.tester_prompt('code_request', incomplete[call['case']], code)
        transformed.append(call)
    random.Random(SEED).shuffle(transformed)
    return transformed, selected


def prepare(out: Path, packets: dict[str, Path], model: str, executable: Path) -> dict:
    """Bind source pages, the new adapter and every prompt before any generation."""
    if out.exists():
        raise FileExistsError('fresh output directory required; no resume or retry')
    controls_path = out.parent / 'controls/controls.json'
    controls = json.loads(controls_path.read_text())
    validate_controls(controls)
    cases = ma.eligible_cases()
    if set(packets) != {c['case'] for c in cases}:
        raise ValueError('packets must cover exactly the eligible cases')
    calls, records = ma.plan(cases, packets)
    incomplete = {c['case']: json.loads((ma.CASES_DIR / f'{c["case"]}.json').read_text())['arms']['C'] for c in cases}
    calls, selected = transform_plan(calls, records, incomplete)
    out.mkdir(mode=0o700, parents=True)
    ma.ta.put(out / 'frozen/controls.json', controls)
    for call in calls:
        ma.ta.put(out / 'frozen/prompts' / f'{call["call_id"]}.txt', call['prompt'])
    manifest = {
        'schema_version': SCHEMA, 'seed': SEED, 'model': model, 'executable': str(executable),
        'image': ma.ta.IMAGE, 'sources': ma.SOURCES, 'suites_per_source': 2,
        'runner_sha256': ma.ta.sha256_file(ma.ta.RUNNER),
        'script_sha256': ma.ta.sha256_file(Path(ma.__file__)),
        'test_anchor_script_sha256': ma.ta.sha256_file(Path(ma.ta.__file__)),
        'extension_script_sha256': ma.ta.sha256_file(Path(__file__)),
        'cases': records, 'selected_mutants': selected, 'code_context_role': 'confirmed_mutant',
        'schedule': [{k: v for k, v in c.items() if k != 'prompt'} for c in calls],
        'retry_policy': 'no_retry_no_repair', 'confirmatory_eligible': False,
        'ground_truth': 'published 20261003 oracle categories; hash-bound',
    }
    ma.ta.put(out / 'frozen/manifest.json', manifest)
    ma.ta.put(out / 'frozen/receipt.json', {'files': ma.ta.inventory(out / 'frozen')})
    return {'calls': len(calls), 'cases': len(records), 'executions': sum(len(c['targets']) for c in calls)}


def validate_controls(controls: dict) -> None:
    """Require the three authored browser controls before any generated suite."""
    expected = {'broken_save': 'assertion_alarm', 'keeps_rule': 'quiet', 'lost_rule': 'assertion_alarm'}
    if (controls.get('qualified') is not True or controls.get('expected') != expected
            or controls.get('observed') != expected
            or controls.get('runner_sha256') != ma.ta.sha256_file(ma.ta.RUNNER)):
        raise ValueError('runner controls are not qualified')


def verify(out: Path) -> dict:
    """Reject adapter drift in addition to the original collector's integrity checks."""
    manifest = ma.verify(out)
    validate_controls(json.loads((out / 'frozen/controls.json').read_text()))
    if manifest.get('extension_script_sha256') != ma.ta.sha256_file(Path(__file__)):
        raise ValueError('extension script drift since freeze')
    if manifest['schema_version'] != SCHEMA or manifest['code_context_role'] != 'confirmed_mutant':
        raise ValueError('wrong experiment identity')
    for case in manifest['cases']:
        if manifest['selected_mutants'][case['case']] not in case['roles']['mutant']:
            raise ValueError('selected code is not a confirmed mutant')
    return manifest


def analyse_selected(rows: list[dict], manifest: dict) -> dict:
    """Count quiet outcomes on the selected confirmed defect, with explicit eligibility."""
    sound = {s['call_id'] for s in ma.suite_scores(rows) if s['sound']}
    result = {}
    for source in ma.SOURCES:
        selected = [r for r in rows if r['source'] == source and
                    r['slot_id'] == manifest['selected_mutants'][r['case']]]
        eligible = [r for r in selected if r['call_id'] in sound]
        source_rows = [r for r in rows if r['source'] == source and r['call_id'] in sound]
        discrimination = {}
        for role in ('mutant', 'correct', 'recovered'):
            group = [r for r in source_rows if r['role'] == role and not r['is_reference']]
            alarms = sum(r['verdict'] in ma.ALARMS for r in group)
            discrimination[role] = {'alarms': alarms, 'pairs': len(group),
                                    'rate': alarms / len(group) if group else None}
        result[source] = {'conditional_discrimination': discrimination, 'planned_selected_pairs': len(selected),
                          'verdicts': dict(Counter(r['verdict'] for r in selected)),
                          'quiet': sum(r['verdict'] == 'quiet' for r in selected),
                          'eligible_pairs': len(eligible),
                          'eligible_quiet': sum(r['verdict'] == 'quiet' for r in eligible)}
    return result


def publish(out: Path, public: Path) -> dict:
    """Export structured outcomes only, without prompts, pages or private paths."""
    manifest = verify(out)
    data = json.loads((out / 'results.json').read_text())
    receipt = json.loads((out / 'receipt.json').read_text())['files']
    if {k:v for k,v in ma.ta.inventory(out).items() if k != 'receipt.json'} != receipt:
        raise ValueError('collection packet drift')
    if ma.analyse(data['rows']) != data['analysis']:
        raise ValueError('analysis mismatch')
    data['schema_version'] = SCHEMA + '-results'
    data['selected_mutant_analysis'] = analyse_selected(data['rows'], manifest)
    ma.ta.put(public / 'results.json', data)
    keys = ('schema_version', 'seed', 'model', 'image', 'runner_sha256', 'script_sha256',
            'test_anchor_script_sha256', 'extension_script_sha256', 'selected_mutants',
            'code_context_role', 'schedule', 'retry_policy', 'confirmatory_eligible')
    safe = {k:manifest[k] for k in keys}
    safe['cases'] = [{k:c[k] for k in ('case','project_id','reference','results_sha256','roles')} for c in manifest['cases']]
    ma.ta.put(public / 'frozen-manifest-public.json', safe)
    return {k:v for k,v in data.items() if k != 'rows' and k != 'analysis'} | {
        'analysis': {k:v for k,v in data['analysis'].items() if k != 'suites'}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare','generate','execute','publish'))
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--packets', type=Path)
    parser.add_argument('--model', default='gpt-6-astra')
    parser.add_argument('--executable', type=Path, default=Path('/opt/homebrew/bin/codex'))
    parser.add_argument('--public', type=Path)
    args = parser.parse_args()
    if args.mode == 'prepare':
        result = prepare(args.out, {k:Path(v) for k,v in json.loads(args.packets.read_text()).items()}, args.model, args.executable)
    else:
        verify(args.out)
        if args.mode == 'generate':
            result = ma.generate(args.out)
        elif args.mode == 'execute':
            result = {k:v for k,v in ma.execute(args.out).items() if k != 'suites'}
        else:
            result = publish(args.out, args.public)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
