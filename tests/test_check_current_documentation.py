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
