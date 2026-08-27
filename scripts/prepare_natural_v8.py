"""Prepare a private natural-requirement JSONL from the ARTA workbook.

The script is an acquisition step, not the offline runner.  It writes source
text only to the caller-selected output path.  The repository stores the
selection manifest and hashes, not the excerpts, until reuse permission is
documented.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

PARSER_VERSION = "arta-xlsx-xml/v1"
ARTA_COMMIT = "493297655cd653f8ebc797ef5c3c7ee2f736ab4c"
SOURCE_FILE = "dataset/zenodo_r1/DS1_Evaluation/001_dataset1kv1.xlsx"
MARKER_COLUMNS = {
    "subjective_language": "Subjective_lang.",
    "ambiguous_adjective_adverb": "Ambiguous_adv._adj.",
    "nonverifiable_term": "Nonverifiable_term",
    "vague_pronoun": "Vague_pron.",
    "uncertain_verb": "Uncertain_verb",
    "polysemy": "Polysemy",
}
ALL_MARKER_COLUMNS = (
    "Subjective_lang.",
    "Ambiguous_adv._adj.",
    "Loophole",
    "Nonverifiable_term",
    "Superlative",
    "Comparative",
    "Negative",
    "Vague_pron.",
    "Uncertain_verb",
    "Polysemy",
)
PROJECT_BY_FILE = {
    "2007-eirene_fun_7-2.xml": "fun",
    "0000 - cctns.xml": "cctns",
    "0000 - cctns.pdf": "cctns",
    "2007-ertms.xml": "ertms",
    "0000 - gamma j.xml": "gamma",
    "2008 - keepass.xml": "keepass",
    "NEW - 2008 - peering.xml": "peering",
}
PROJECT_ORDER = ("cctns", "ertms", "fun", "gamma", "keepass", "peering")


def _column_index(cell_ref: str) -> int:
    letters = "".join(character for character in cell_ref if character.isalpha())
    result = 0
    for character in letters.upper():
        result = result * 26 + ord(character) - ord("A") + 1
    return result - 1


def read_sheet(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    namespace = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    text_namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
    with ZipFile(path) as workbook:
        shared_root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
        shared_strings = [
            "".join(text.text or "" for text in item.iter(text_namespace))
            for item in shared_root.findall("a:si", namespace)
        ]
        worksheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        for row in worksheet.findall(".//a:sheetData/a:row", namespace):
            values = [""] * 13
            for cell in row.findall("a:c", namespace):
                index = _column_index(cell.get("r", ""))
                if index >= len(values):
                    continue
                value_node = cell.find("a:v", namespace)
                value = "" if value_node is None else value_node.text or ""
                if cell.get("t") == "s":
                    value = shared_strings[int(value)]
                values[index] = value
            rows.append(values)
    header = rows[0]
    return header, [dict(zip(header, row)) for row in rows[1:]]


def _project(file_name: str) -> str:
    if file_name in PROJECT_BY_FILE:
        return PROJECT_BY_FILE[file_name]
    for known_file, project in PROJECT_BY_FILE.items():
        if file_name.casefold() == known_file.casefold():
            return project
    raise ValueError(f"unmapped ARTA project file: {file_name}")


def _marked_columns(row: dict[str, str]) -> list[str]:
    return [column for column in ALL_MARKER_COLUMNS if row.get(column, "") not in {"", "-"}]


def _by_project(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {project: [] for project in PROJECT_ORDER}
    for row in rows:
        grouped[_project(row["File"])].append(row)
    for project_rows in grouped.values():
        project_rows.sort(key=lambda row: int(row["_source_row"]))
    return grouped


def select_rows(
    rows: list[dict[str, str]],
    *,
    count: int,
    exclude_source_rows: set[int] | None = None,
) -> list[dict[str, str]]:
    grouped = _by_project(rows)
    selected: list[dict[str, str]] = []
    used: set[int] = set(exclude_source_rows or set())
    # The deterministic priority gives both test projects at least two rows
    # whenever the source contains them, then rotates across all projects.
    for project in ("cctns", "gamma"):
        for row in grouped[project][:3]:
            source_row = int(row["_source_row"])
            if source_row in used:
                continue
            selected.append(row)
            used.add(source_row)
            if len(selected) >= count:
                return selected
    while len(selected) < count:
        progressed = False
        for project in PROJECT_ORDER:
            for row in grouped[project]:
                source_row = int(row["_source_row"])
                if source_row in used:
                    continue
                selected.append(row)
                used.add(source_row)
                progressed = True
                break
            if len(selected) >= count:
                break
        if not progressed:
            raise ValueError(f"source contains only {len(selected)} candidate rows; requires {count}")
    return selected


def _case(
    row: dict[str, str],
    *,
    family: str,
    source_label: str,
    source_hash: str,
    private_source: bool,
) -> dict[str, object]:
    source_row = int(row["_source_row"])
    project = _project(row["File"])
    text = row["Requirement_text"].strip()
    return {
        "case_id": f"arta-v8-{source_label}-{family}-{source_row:04d}",
        "source_dataset": "ARTA",
        "source_dataset_commit": ARTA_COMMIT,
        "source_file": SOURCE_FILE,
        "source_row": source_row,
        "source_file_sha256": source_hash,
        "source_file_ref": f"{SOURCE_FILE}#Sheet1!A{source_row}",
        "source_intent_id": f"arta-sheet1-row-{source_row:04d}",
        "source_file_id": row["File"],
        "project_id": project,
        "requirement_text": text,
        "requirement_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "target_family": family,
        "source_label": source_label,
        "source_label_type": "arta_dataset_marker",
        "source_smell_markers": [
            {"column": column, "value": row.get(column, "")}
            for column in _marked_columns(row)
        ],
        "clean_control": source_label == "clean",
        "clean_control_definition": "no marker in any ARTA smell column",
        "expert_annotation_status": "pending",
        "paraphrase_status": "not_generated",
        "license_status": "private_use_only" if private_source else "redistributable",
        "redistribution_allowed": False if private_source else True,
        "derivative_use_allowed": False if private_source else True,
        "permission_record": "" if private_source else "replace-with-verified-license-record",
    }


def prepare(
    workbook_path: Path,
    output_path: Path,
    selection_manifest_path: Path,
    *,
    positives_per_family: int = 12,
    clean_controls_per_family: int = 12,
) -> None:
    source_hash = hashlib.sha256(workbook_path.read_bytes()).hexdigest()
    header, raw_rows = read_sheet(workbook_path)
    if header[: len(ALL_MARKER_COLUMNS) + 2] != [
        "Requirement_text",
        "File",
        *ALL_MARKER_COLUMNS,
    ]:
        raise ValueError("unexpected ARTA workbook header; source parser must be reviewed")
    rows = []
    for excel_row, row in enumerate(raw_rows, start=2):
        row["_source_row"] = str(excel_row)
        if row.get("Requirement_text", "").strip() and _project(row.get("File", "")):
            rows.append(row)
    output_cases: list[dict[str, object]] = []
    selection_records: list[dict[str, object]] = []
    used_clean_source_rows: set[int] = set()
    for family, marker_column in MARKER_COLUMNS.items():
        positives = select_rows(
            [row for row in rows if _marked_columns(row) == [marker_column]],
            count=positives_per_family,
        )
        clean = select_rows(
            [row for row in rows if not _marked_columns(row)],
            count=clean_controls_per_family,
            exclude_source_rows=used_clean_source_rows,
        )
        used_clean_source_rows.update(int(row["_source_row"]) for row in clean)
        for source_label, selected in (("smelly", positives), ("clean", clean)):
            for row in selected:
                case = _case(
                    row,
                    family=family,
                    source_label=source_label,
                    source_hash=source_hash,
                    private_source=True,
                )
                output_cases.append(case)
                selection_records.append({
                    "case_id": case["case_id"],
                    "source_row": case["source_row"],
                    "source_file_id": case["source_file_id"],
                    "project_id": case["project_id"],
                    "target_family": family,
                    "source_label": source_label,
                    "requirement_text_sha256": case["requirement_text_sha256"],
                })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(case, sort_keys=True) + "\n" for case in output_cases),
        encoding="utf-8",
    )
    selection_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    selection_manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "requirements-smell-natural-selection/v1",
                "status": "private_input_selection_only",
                "source_dataset": "ARTA",
                "source_dataset_commit": ARTA_COMMIT,
                "source_file": SOURCE_FILE,
                "source_file_sha256": source_hash,
                "parser_version": PARSER_VERSION,
                "sheet": "Sheet1",
                "positive_per_family": positives_per_family,
                "clean_controls_per_family": clean_controls_per_family,
                "license_status": "private_use_only",
                "redistribution_allowed": False,
                "derivative_use_allowed": False,
                "records": selection_records,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--selection-manifest", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.workbook, args.output, args.selection_manifest)
    print(json.dumps({"output": str(args.output), "selection_manifest": str(args.selection_manifest)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
