from agent_harness.types import Episode, Smell, TaskFamily, Variant


def test_episode_roundtrip_fields():
    ep = Episode(
        episode_id="e1",
        intent_id="RF-09",
        variant=Variant.CLEAN,
        smell=None,
        task_family=TaskFamily.CODEGEN,
        policy="direct",
        mode="stub",
        replication_id=0,
    )
    assert ep.intent_id == "RF-09"
    assert ep.semantic_label is None
