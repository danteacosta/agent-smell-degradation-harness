import pytest

from eval.provider_balance import provider_balance_report


def _rows(spec):
    rows, labels = [], {}
    for i, (project, provider, label) in enumerate(spec):
        eid = f"E{i}"
        rows.append({"episode_id": eid, "project_id": project, "provider": provider})
        labels[eid] = label
    return {"test": rows}, labels


def test_balanced_providers_have_no_flags():
    spec = [(p, prov, lab) for p in ("P1", "P2") for prov in ("a", "b") for lab in (0, 1)]
    parts, labels = _rows(spec)
    out = provider_balance_report(parts, labels)
    assert out["splits"]["test"]["flags"] == []
    assert out["any_flag"] is False
    assert out["splits"]["test"]["per_provider"]["a"] == {"clean": 2, "degraded": 2}


def test_provider_confounded_with_label_is_flagged():
    spec = [("P1", "a", 1)] * 4 + [("P1", "a", 0)] + [("P2", "b", 0)] * 4 + [("P2", "b", 1)]
    parts, labels = _rows(spec)
    flags = provider_balance_report(parts, labels)["splits"]["test"]["flags"]
    assert "provider_label_rate_gap" in flags
    assert "project_missing_a_provider" in flags


def test_single_provider_and_missing_class_flagged():
    parts, labels = _rows([("P1", "a", 0), ("P2", "a", 0)])
    flags = provider_balance_report(parts, labels)["splits"]["test"]["flags"]
    assert {"single_provider", "provider_missing_a_class"} <= set(flags)


def test_missing_provider_and_bad_labels_rejected():
    parts, labels = _rows([("P1", "", 0), ("P1", "a", 1)])
    assert "missing_provider" in provider_balance_report(parts, labels)["splits"]["test"]["flags"]
    parts, labels = _rows([("P1", "a", 2)])
    with pytest.raises(ValueError, match="binary"):
        provider_balance_report(parts, labels)
    parts, _ = _rows([("P1", "a", 0)])
    with pytest.raises(ValueError, match="missing label"):
        provider_balance_report(parts, {})
