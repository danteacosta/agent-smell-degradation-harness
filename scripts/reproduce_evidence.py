"""Regenerate the proposal's exploratory evidence table from public packets.

Each row is either recomputed from files in this repository and compared with
the number stated in the proposal, or marked as having no public
machine-readable source. A mismatch exits with status 1, so `make reproduce`
fails loudly when the text and the data drift apart.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def october_replications() -> list[dict]:
    rows = []
    expected = {  # case: stated C target failures out of 6, and A/B all passing
        "openproject-invalid-remaining": 6,
        "paperless-duplicate-consumption": 5,
        "realworld-favorites": 0,
    }
    for case, stated_c_failures in expected.items():
        summary = _load(f"data/e2e-replications-20261001/{case}/summary.json")
        arm = Counter()
        for model_counts in summary["counts"].values():
            for variant, categories in model_counts.items():
                arm.update({(variant, cat): n for cat, n in categories.items()})
        c_fail = arm[("C", "target_only_failure")]
        ab_pass = arm[("A", "pass")] + arm[("B", "pass")]
        rows.append({
            "row": f"October replication, {case}",
            "stated": f"C failed {stated_c_failures}/6; A and B passed 12/12",
            "recomputed": f"C failed {c_fail}/6; A and B passed {ab_pass}/12",
            "status": "reproduced" if (c_fail, ab_pass) == (stated_c_failures, 12) else "mismatch",
            "source": f"data/e2e-replications-20261001/{case}/summary.json",
        })
    return rows


def acceptance_criteria() -> list[dict]:
    data = _load("data/criteria-expansion/results-20260921.json")
    c_target = next(r for r in data["by_arm"] if r["variant"] == "C" and r["is_target"])
    gens = data["generations"]
    total = sum(gens.values())
    rows = [{
        "row": "Acceptance criteria, target rule in arm C",
        "stated": "absent in 47 of 72; 25 unresolved",
        "recomputed": f"absent in {c_target['absent']} of {c_target['planned']}; {c_target['unresolved']} unresolved",
        "status": "reproduced" if (c_target["absent"], c_target["planned"], c_target["unresolved"]) == (47, 72, 25) else "mismatch",
        "source": "data/criteria-expansion/results-20260921.json (by_arm)",
    }, {
        "row": "Acceptance criteria, generations",
        "stated": "216 generations, 212 structurally valid",
        "recomputed": f"{total} generations, {gens.get('valid', 0)} structurally valid",
        "status": "reproduced" if (total, gens.get("valid")) == (216, 212) else "mismatch",
        "source": "data/criteria-expansion/results-20260921.json (generations)",
    }]
    return rows


def decontamination_successors() -> list[dict]:
    accounting = _load("docs/research/2026-10-01-e2e-accounting.json")
    totals, pairs = Counter(), 0
    for path, packet in accounting["paired_packets"].items():
        if "e2e-decontamination-20260929" in path:
            totals.update(packet["comparisons"])
            pairs += packet["pairs"]
    stated = (6, 8, 4, 18)
    got = (totals["improved"], totals["equal"], totals["unknown"], pairs)
    return [{
        "row": "Excerpt successors of three historical requirements",
        "stated": "6 improvements, 8 ties, 4 unknown in 18 pairs",
        "recomputed": f"{got[0]} improvements, {got[1]} ties, {got[2]} unknown in {got[3]} pairs",
        "status": "reproduced" if got == stated else "mismatch",
        "source": "docs/research/2026-10-01-e2e-accounting.json (paired_packets)",
    }]


RECOVERED_PATH = 'data/recovered-evidence-20261002/rows.json'


def _evidence_row(name: str, stated: str, recomputed: str) -> dict:
    return {'row': name, 'stated': stated, 'recomputed': recomputed,
            'status': 'reproduced' if stated == recomputed else 'mismatch',
            'source': RECOVERED_PATH}


def _ordinal_pairs(rows: list[dict]) -> dict:
    groups = {}
    identifiers = set()
    for row in rows:
        if row['id'] in identifiers:
            raise ValueError('duplicate ordinal artifact')
        identifiers.add(row['id'])
        severity = row['severity']
        if severity is not None and (type(severity) is not int or severity not in range(4)):
            raise ValueError('invalid ordinal severity')
        if severity is not None and row['eligible'] is not True:
            raise ValueError('ineligible ordinal artifact cannot have a resolved label')
        key = (row['case_id'], row['model'])
        arms = groups.setdefault(key, {})
        if row['arm'] not in ('A', 'B', 'C') or row['arm'] in arms:
            raise ValueError('duplicate or invalid ordinal arm')
        arms[row['arm']] = row
    if any(set(arms) != {'A', 'B', 'C'} for arms in groups.values()):
        raise ValueError('incomplete ordinal case/model pair')
    for arms in groups.values():
        if len({(r['project_id'], r['replication']) for r in arms.values()}) != 1:
            raise ValueError('ordinal arms have mixed project or replication identity')
    return groups


def _ordinal_counts(groups: dict) -> Counter:
    counts = Counter({key: 0 for key in ('C_worse', 'equal', 'C_better', 'unknown')})
    for arms in groups.values():
        a, c = arms['A']['severity'], arms['C']['severity']
        direction = ('unknown' if a is None or c is None else
                     'C_worse' if c > a else 'C_better' if c < a else 'equal')
        counts[direction] += 1
    return counts


def _ordinal_text(groups: dict) -> str:
    counts = _ordinal_counts(groups)
    return (f"{len(groups)} pairs: {counts['C_worse']} C worse, {counts['equal']} equal, "
            f"{counts['C_better']} C better, {counts['unknown']} unknown")


def recovered_evidence(packet: dict | None = None) -> list[dict]:
    """Recalculate unchanged published labels; scope correction is a separate row.

    A supplied packet supports offline validation. The default public-file path
    additionally checks its receipt before parsing. No LLM or browser is called.
    """
    if packet is None:
        path = ROOT / RECOVERED_PATH
        receipt = _load('data/recovered-evidence-20261002/receipt.json')['files']
        if set(receipt) != {'rows.json'} or hashlib.sha256(path.read_bytes()).hexdigest() != receipt['rows.json']:
            raise ValueError('recovered evidence receipt mismatch')
        packet = _load(RECOVERED_PATH)
    if packet.get('schema_version') != 'recovered-evidence-public/v1' or packet.get('confirmatory_eligible') is not False:
        raise ValueError('wrong recovered evidence schema or scope')
    cases = {case['row_id']: case for case in packet['rows']}
    if len(packet['rows']) != 3 or len(cases) != 3 or set(cases) != {'constructed_demo', 'kanboard_subtasks_minimal_context', 'browser_ordinal_34'}:
        raise ValueError('three distinct recovered cohorts required')

    demo = cases['constructed_demo']['rows']
    grouped = {}
    for row in demo:
        key = (row['project_id'], row['intent_id'], row['constraint_id'], row['replication_id'])
        arms = grouped.setdefault(key, {})
        if row['variant'] not in ('clean', 'defective') or row['variant'] in arms:
            raise ValueError('duplicate or invalid demonstration variant')
        if row['status'] not in ('passed', 'failed'):
            raise ValueError('unresolved demonstration outcome')
        arms[row['variant']] = row['status']
    if any(set(arms) != {'clean', 'defective'} for arms in grouped.values()):
        raise ValueError('incomplete demonstration pair')
    counts = Counter((row['variant'], row['status']) for row in demo)
    demo_text = (f"complete {counts['clean', 'passed']}/{len(grouped)} versus "
                 f"defective {counts['defective', 'passed']}/{len(grouped)}")

    kanboard = cases['kanboard_subtasks_minimal_context']['rows']
    groups = {}
    for row in kanboard:
        key = (row['model'], row['replication'])
        arms = groups.setdefault(key, {})
        if row['arm'] not in ('A', 'B', 'C') or row['arm'] in arms:
            raise ValueError('duplicate or invalid Kanboard arm')
        if (row['generation_status'] != 'valid' or row['browser_status'] != 'complete'
                or row['eligible'] is not True or type(row['severity']) is not int
                or row['severity'] not in range(4) or row['statuses'] != ['valid', 'valid']
                or row['votes'] != [row['severity'], row['severity']]):
            raise ValueError('Kanboard label must be resolved eligible ordinal consensus')
        arms[row['arm']] = row['severity']
    if any(set(arms) != {'A', 'B', 'C'} for arms in groups.values()):
        raise ValueError('incomplete Kanboard pair')
    arm_counts = Counter((row['arm'], row['severity']) for row in kanboard)
    worsened = sum(arms['C'] > arms['A'] for arms in groups.values())
    kanboard_text = (f"{len(kanboard)} ordinal labels: A 0:{arm_counts['A', 0]}; "
                    f"B 0:{arm_counts['B', 0]}; C 2:{arm_counts['C', 2]}; {worsened} C-worse pairs")

    ordinal = cases['browser_ordinal_34']
    base = _ordinal_pairs(ordinal['base']['rows'])
    correction = _ordinal_pairs(ordinal['scope_correction']['rows'])
    replacement = {(r['case_id'], r['model']) for r in ordinal['replacement_keys']}
    required = {('kanboard-duplicate-title', model) for model in ('gpt-5.6-luna', 'gpt-5.6-sol')}
    if replacement != required or set(correction) != required or not replacement <= set(base):
        raise ValueError('scope correction must replace exactly two declared case/model pairs')
    for key in replacement:
        for arm in ('A', 'B', 'C'):
            original, corrected = base[key][arm], correction[key][arm]
            identity_fields = ('case_id', 'project_id', 'model', 'arm', 'replication', 'source_slot')
            if any(original[field] != corrected[field] for field in identity_fields):
                raise ValueError('scope correction artifact identity mismatch')
            if original['original_html_sha256'] != corrected['original_html_sha256']:
                raise ValueError('scope correction HTML hash mismatch')
    diagnostic = {**base, **correction}
    return [
        _evidence_row('Constructed demonstration (not E2E)', 'complete 9/9 versus defective 6/9', demo_text),
        _evidence_row('Kanboard subtasks, minimal-context ordinal consensus',
                      '18 ordinal labels: A 0:6; B 0:6; C 2:6; 6 C-worse pairs', kanboard_text),
        _evidence_row('Severity pairs, original retrospective labels',
                      '34 pairs: 14 C worse, 10 equal, 1 C better, 9 unknown', _ordinal_text(base)),
        _evidence_row('Severity pairs, separate post-hoc scope diagnostic',
                      '34 pairs: 14 C worse, 11 equal, 1 C better, 8 unknown', _ordinal_text(diagnostic)),
    ]


NO_PUBLIC_SOURCE = [
    ("Prospective E2E block, 11 obligations (7 with a C failure)",
     "stated in the evidence matrix document; no machine-readable summary found"),
    ("Historical old/new closure, 60 pairs (11 / 44 / 5)",
     "complete original 60-pair cohort is not public; 42 pairs were recovered privately, 18 originals remain missing"),
]


def build() -> list[dict]:
    rows = october_replications() + acceptance_criteria() + decontamination_successors() + recovered_evidence()
    rows += [{"row": row, "stated": "", "recomputed": "", "status": "no_public_source_found", "source": why}
             for row, why in NO_PUBLIC_SOURCE]
    return rows


def render(rows: list[dict]) -> str:
    lines = ["| Evidence row | Stated | Recomputed | Status | Source |", "| --- | --- | --- | --- | --- |"]
    lines += [f"| {r['row']} | {r['stated']} | {r['recomputed']} | {r['status']} | {r['source']} |" for r in rows]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, help="write the markdown table here")
    args = parser.parse_args(argv)
    rows = build()
    table = render(rows)
    if args.out:
        args.out.write_text(table)
    print(table)
    counts = Counter(r["status"] for r in rows)
    print(dict(counts))
    return 1 if counts["mismatch"] else 0


if __name__ == "__main__":
    sys.exit(main())
