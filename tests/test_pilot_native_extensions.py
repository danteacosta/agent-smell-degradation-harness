import json

from agents.staged_runtime import StagedProviderRuntime, GENERATION_PROMPT_TEMPLATES


def test_pilot_templates_are_audited_and_stage_events_arrive_before_artifact():
    observed=[]
    class Provider:
        name='offline'
        def complete(self,request):
            observed.append(request.prompt)
            if request.prompt=='PILOT T1':
                return json.dumps({'constraints':['bounded request'],'quantities':[],
                    'unresolved_references':[],'assumptions':[],'contradictions':[],
                    'conditional_semantics':[],'atomic_obligations':[{'constraint_index':1,'atom_type':'condition','status':'present'}]})
            if request.prompt=='PILOT T2':
                return json.dumps({'validation_checks':['bounded request'],'planned_tools':[],'coverage_targets':['bounded request']})
            assert observed[-2]=='T3'
            return '{"criterion":"bounded request"}'
    templates={**GENERATION_PROMPT_TEMPLATES,'T1':'PILOT T1','T2':'PILOT T2','artifact':'PILOT ARTIFACT'}
    runtime=StagedProviderRuntime(Provider(),prompt_templates=templates,
                                 checkpoint_sink=lambda stage,payload:observed.append(stage))
    result=runtime.execute({'clean_requirement':'bounded request','generation_contract':{'test_gen':{'output_keys':['criterion']}}},'clean','test_gen')
    assert observed==['PILOT T1','T1','PILOT T2','T2','T3','PILOT ARTIFACT']
    assert result.provider_meta['context_management']['compaction_count']==0
    assert GENERATION_PROMPT_TEMPLATES['T1']!='PILOT T1'
