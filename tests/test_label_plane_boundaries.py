from __future__ import annotations

from eval.mutation import score_test_gen_mutation as legacy_mutation_score
from eval.oracles import score_artifact as legacy_executable_score


def test_label_plane_exposes_independent_executable_and_reference_scorers():
    from label_plane.executable import score_artifact
    from label_plane.reference_based import score_test_gen_mutation

    assert score_artifact is legacy_executable_score
    assert score_test_gen_mutation is legacy_mutation_score


def test_label_plane_supports_human_adjudication_and_secondary_judging_boundaries():
    from label_plane.adjudication import adjudicate
    from label_plane.human_annotation import HumanAnnotation
    from label_plane.llm_judge_secondary import secondary_judge

    annotations = [
        HumanAnnotation(annotator_id="a", label="degraded"),
        HumanAnnotation(annotator_id="b", label="degraded"),
    ]

    assert adjudicate(annotations).label == "degraded"
    assert secondary_judge(lambda _artifact: "ok", {"artifact": "value"}).label == "ok"
