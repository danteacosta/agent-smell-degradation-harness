"""Declarative readiness audit for the 144-episode temporal engineering pilot.

No provider is called and no approval is created. Receipt metadata cannot prove
reviewer independence, annotation quality or authentic provider qualification;
those claims require external review. The historical 120-episode gate is not
used or modified by this audit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path
from eval.temporal_cohort_candidate import candidate_content_digest, validate_candidate


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON object member: {key}')
        result[key] = value
    return result


def _bound_file(reference, root):
    if not isinstance(reference, dict):
        raise ValueError('hash-bound artifact reference required')
    path = (root / reference['path']).resolve()
    if not path.is_relative_to(root):
        raise ValueError('artifact path or hash mismatch')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != reference['sha256']:
        raise ValueError('artifact path or hash mismatch')
    return json.loads(data, object_pairs_hook=_unique_json_object)


def _qualification_report_matches(configuration, root):
    """Check receipt bytes, not provider behavior or qualification authenticity."""
    try:
        path = (root / configuration['qualification_report_path']).resolve()
        return (path.is_relative_to(root) and path.is_file()
                and hashlib.sha256(path.read_bytes()).hexdigest()
                == configuration['qualification_report_sha256'])
    except (OSError, ValueError, TypeError):
        return False


def assess(plan, root):
    root = Path(root).resolve(); blockers = []
    if plan.get('schema_version') != 'temporal-warning-cohort-candidate/v1':
        raise ValueError('wrong temporal cohort schema')
    if plan.get('confirmatory_eligible') is not False:
        raise ValueError('engineering pilot cannot be promoted to confirmatory')
    source = _bound_file(plan['candidate_source_manifest'], root)
    audit = _bound_file(plan['exposure_audit'], root)
    counts = validate_candidate(source, root)
    design = plan['design_candidate']
    if (counts != {'pairs_verified': 12, 'projects': 6}
            or design.get('variants') != ['clean', 'defective']
            or design.get('new_intents') != 12 or design.get('projects') != 6
            or design.get('distinct_providers') != 2
            or design.get('replications_per_provider_variant') != 3
            or design.get('planned_episodes') != 144):
        raise ValueError('design differs from the declared 144-episode engineering pilot')
    intents = {r['intent_id'] for r in source['records']}
    if set(plan.get('selected_requirements', [])) != intents or len(plan['selected_requirements']) != 12:
        raise ValueError('selected intent list differs from source manifest')
    if audit.get('pairs_verified') != 12 or set(audit.get('exact_or_contained_clean_input_matches', {})) != intents:
        raise ValueError('exposure audit does not cover the candidate cohort')
    if audit.get('candidate_content_sha256') != candidate_content_digest(source):
        blockers.append('exposure_audit_not_bound_to_candidate')
    if any(audit['exact_or_contained_clean_input_matches'].values()):
        blockers.append('prior_complete_input_match_requires_candidate_replacement_or_explicit_review')
    if plan.get('selection_frozen') is not True:
        blockers.append('selection_not_frozen')
    projects = {r['project_id'] for r in source['records']}
    split = plan.get('project_split', {})
    if (plan.get('split_frozen') is not True or set(split) != projects
            or sorted(split.values()) != ['calibration','test','test','train','train','train']):
        blockers.append('project_and_related_intent_split_not_frozen')
    reviewers_by_intent = {intent_id: set() for intent_id in intents}
    unresolved_intents = set()
    source_hash = plan['candidate_source_manifest']['sha256']
    for review in plan.get('independent_human_reviews', []):
        if (isinstance(review, dict) and review.get('intent_id') in intents
                and review.get('source_manifest_sha256') == source_hash
                and isinstance(review.get('reviewer_id'), str) and review['reviewer_id'].strip()):
            reviewer = unicodedata.normalize('NFKC', review['reviewer_id']).strip().casefold()
            if reviewer:
                intent_id = review['intent_id']
                if all(review.get(field) is True for field in (
                    'mapping_approved', 'manipulation_approved', 'rights_approved',
                    'prior_exposure_and_residual_cues_reviewed', 'independent_of_author',
                )):
                    reviewers_by_intent[intent_id].add(reviewer)
                else:
                    unresolved_intents.add(intent_id)
    reviewed = {intent_id for intent_id, reviewers in reviewers_by_intent.items()
                if len(reviewers) >= 2 and intent_id not in unresolved_intents}
    if reviewed != intents:
        blockers.append('independent_reviews_incomplete_or_not_bound_to_source')
    configurations = plan.get('qualified_provider_configurations', [])
    qualified = set()
    for c in configurations:
        if (isinstance(c, dict) and all(isinstance(c.get(k), str) and c[k].strip() for k in ['provider','model','model_version'])
                and c.get('mode') == 'runtime' and c.get('checkpoint_source') == 'runtime_native'
                and c.get('qualification_passed') is True and c.get('t1_t3_before_t4') is True
                and c.get('prompted_snapshot') is False
                and re.fullmatch('[0-9a-f]{64}', str(c.get('configuration_hash','')))
                and re.fullmatch('[0-9a-f]{64}', str(c.get('qualification_report_sha256','')))
                and isinstance(c.get('qualification_report_path'), str) and c['qualification_report_path'].strip()
                and _qualification_report_matches(c, root)):
            qualified.add(c['provider'].strip().casefold())
    if len(qualified) != 2:
        blockers.append('two_distinct_runtime_native_providers_not_qualified')
    for field in ['rubric_frozen','annotation_blinding_verified','independent_annotators_ready',
                  'prefix_clock_and_collector_qualified','feature_and_score_policy_frozen',
                  'schedule_frozen','launch_authorized']:
        if plan.get(field) is not True:
            blockers.append(field+'_missing')
    budget = plan.get('budget', {})
    values = [budget.get(k) for k in ['estimated_provider_cost_usd','contingency_fraction','approved_cap_usd']]
    if (any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
            or values[0] <= 0 or values[1] < 0 or values[2] <= 0 or values[0]*(1+values[1]) > values[2]):
        blockers.append('finite_cost_envelope_and_approved_cap_missing')
    return {'schema_version':'temporal-warning-readiness/v1', 'decision':'no_go' if blockers else 'prerequisites_declared',
            'collection_authorized_by_this_report':False, 'confirmatory_eligible':False,
            'planned_episodes':144, 'pairs_verified':12, 'reviewed_intents':len(reviewed),
            'review_status_by_intent': {
                intent_id: ('unresolved' if intent_id in unresolved_intents
                            else 'complete' if intent_id in reviewed
                            else 'awaiting_approvals')
                for intent_id in sorted(intents)
            },
            'qualified_distinct_providers':len(qualified), 'blockers':blockers,
            'limitations':['Declarative receipts require independent authenticity verification before launch.',
                           'This audit neither runs providers nor validates scientific labels.',
                           'Train-only detector fitting follows training collection; freeze the feature/score policy before that collection.']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,default=Path('data/prepilot/temporal-warning-plan.candidate.json'))
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_bytes(), object_pairs_hook=_unique_json_object)
        report = assess(plan, Path.cwd())
    except (OSError, ValueError) as error:
        parser.error(str(error))
    rendered=json.dumps(report,indent=2,allow_nan=False)+'\n'
    if args.output:
        try:
            with args.output.open('x',encoding='utf-8') as stream:
                stream.write(rendered)
        except OSError as error:
            parser.error(f'cannot create readiness report: {error}')
    print(rendered,end='')
    return 2 if report['decision']=='no_go' else 0


if __name__=='__main__':
    raise SystemExit(main())
