import json

from scripts import check_current_documentation as ccd


def test_presence_ignores_markup_padding_and_case():
    texts = [ccd.norm("| `MP2T`   | `.mts` `.m2ts` `.m2t` | :white_check_mark: |  |")]
    assert ccd.is_present("MP2T | .mts .m2ts .m2t | :white_check_mark: | |", texts)
    assert not ccd.is_present("MP2T | .mts .m2ts .m2t .ts", [ccd.norm("MP2T .mts .m2ts")])
    assert not ccd.is_present("   ", texts)


def test_published_check_covers_every_admitted_candidate():
    data = json.loads((ccd.ROOT / "data/requirement-selection/current-doc-check.json").read_text())
    admitted = {r["candidate_id"] for p in ccd.SCREENING for r in json.loads(p.read_text())["rows"]
                if r["consensus"] == "admit"}
    assert {r["candidate_id"] for r in data["rows"]} == admitted
    assert data["frame_end"] == ccd.FRAME_END
    assert len(data["snapshots"]) == len({r["project"] for r in data["rows"]})


def _commit_document(repo, sentence, timestamp):
    import os
    import subprocess
    document = repo / "docs/user-guide/rule.md"
    document.parent.mkdir(parents=True, exist_ok=True)
    document.write_text(sentence + "\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "Document rule"], env={**os.environ, "GIT_AUTHOR_DATE": timestamp, "GIT_COMMITTER_DATE": timestamp}, check=True, capture_output=True)
    return ccd.git(repo, "rev-parse", "HEAD").strip()


def test_snapshot_uses_default_branch_when_checkout_has_an_unmerged_rule(tmp_path):
    import subprocess
    repo = tmp_path / "project"
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    default_sha = _commit_document(repo, "Only administrators may create a template.", "2026-09-29T12:00:00Z")
    ccd.git(repo, "update-ref", "refs/remotes/origin/main", default_sha)
    ccd.git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    ccd.git(repo, "checkout", "-b", "feature")
    _commit_document(repo, "Every user may create a template.", "2026-09-30T12:00:00Z")
    sha, texts = ccd.snapshot_texts(repo, "openproject")
    assert sha == default_sha
    assert ccd.is_present("Only administrators may create a template.", texts)
    assert not ccd.is_present("Every user may create a template.", texts)


def test_snapshot_rejects_a_clone_without_default_branch_identity(tmp_path):
    import subprocess
    import pytest
    repo = tmp_path / "project"
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    _commit_document(repo, "Only administrators may create a template.", "2026-09-29T12:00:00Z")
    with pytest.raises(ValueError, match="default branch"):
        ccd.snapshot_texts(repo, "openproject")


def test_snapshot_rejects_missing_document_blob_instead_of_marking_rule_absent(tmp_path):
    import subprocess
    import pytest
    repo = tmp_path / "project"
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    sha = _commit_document(repo, "Only administrators may create a template.", "2026-09-29T12:00:00Z")
    ccd.git(repo, "update-ref", "refs/remotes/origin/main", sha)
    ccd.git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    blob = ccd.git(repo, "rev-parse", f"{sha}:docs/user-guide/rule.md").strip()
    (repo / ".git/objects" / blob[:2] / blob[2:]).unlink()
    with pytest.raises(ValueError, match="blob"):
        ccd.snapshot_texts(repo, "openproject")
