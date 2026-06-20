from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from tools.catalog_import_common import import_catalog


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_staged_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_valid_exercise_rows_stage_successfully(tmp_path: Path) -> None:
    input_path = tmp_path / "exercises.csv"
    out_dir = tmp_path / "out"
    write_csv(
        input_path,
        [
            {
                "name": "Goblet Squat",
                "equipment": "dumbbell",
                "movement_pattern": "squat",
                "primary_muscle_group": "legs",
                "aliases": "db goblet squat",
                "source_name": "test fixture",
                "source_policy": "local test data",
                "confidence": "high",
            }
        ],
    )

    result = import_catalog("exercise", str(input_path), str(out_dir))
    staged_rows = read_staged_rows(result.staged_path)

    assert staged_rows[0]["import_status"] == "accepted_for_review"
    assert staged_rows[0]["normalized_name"] == "goblet squat"
    assert result.report_path.exists()
    assert result.findings_path.exists()


def test_missing_required_exercise_fields_fail(tmp_path: Path) -> None:
    input_path = tmp_path / "exercises.csv"
    out_dir = tmp_path / "out"
    write_csv(
        input_path,
        [
            {
                "name": "Incomplete Exercise",
                "equipment": "dumbbell",
                "source_name": "test fixture",
                "confidence": "medium",
            }
        ],
    )

    result = import_catalog("exercise", str(input_path), str(out_dir))
    staged_rows = read_staged_rows(result.staged_path)

    assert staged_rows[0]["import_status"] == "rejected"
    assert "missing_required_field" in staged_rows[0]["validation_errors"]


def test_unknown_equipment_and_movement_pattern_are_flagged(tmp_path: Path) -> None:
    input_path = tmp_path / "exercises.csv"
    out_dir = tmp_path / "out"
    write_csv(
        input_path,
        [
            {
                "name": "Mystery Lift",
                "equipment": "gravity boots",
                "movement_pattern": "anti-gravity",
                "source_name": "test fixture",
                "confidence": "low",
            }
        ],
    )

    result = import_catalog("exercise", str(input_path), str(out_dir))
    staged_rows = read_staged_rows(result.staged_path)
    warnings = staged_rows[0]["validation_warnings"]

    assert staged_rows[0]["import_status"] == "review_required"
    assert "unknown_equipment" in warnings
    assert "unknown_movement_pattern" in warnings


def test_duplicate_exercise_names_and_aliases_are_flagged(tmp_path: Path) -> None:
    input_path = tmp_path / "exercises.csv"
    out_dir = tmp_path / "out"
    rows = [
        {
            "name": "Bench Press",
            "equipment": "barbell",
            "movement_pattern": "push",
            "aliases": "barbell bench",
            "source_name": "test fixture",
            "confidence": "high",
        },
        {
            "name": "Bench Press",
            "equipment": "barbell",
            "movement_pattern": "push",
            "aliases": "barbell bench",
            "source_name": "test fixture",
            "confidence": "high",
        },
    ]
    write_csv(input_path, rows)

    result = import_catalog("exercise", str(input_path), str(out_dir))
    staged_rows = read_staged_rows(result.staged_path)

    assert all(row["import_status"] == "review_required" for row in staged_rows)
    assert "duplicate_name" in staged_rows[0]["validation_warnings"]
    assert "duplicate_alias" in staged_rows[1]["validation_warnings"]


def test_unsafe_medical_language_is_flagged(tmp_path: Path) -> None:
    input_path = tmp_path / "exercises.csv"
    out_dir = tmp_path / "out"
    write_csv(
        input_path,
        [
            {
                "name": "Shoulder Rehab Cure Press",
                "equipment": "dumbbell",
                "movement_pattern": "push",
                "notes": "Guaranteed pain-free rehab treatment.",
                "source_name": "test fixture",
                "confidence": "low",
            }
        ],
    )

    result = import_catalog("exercise", str(input_path), str(out_dir))
    staged_rows = read_staged_rows(result.staged_path)

    assert staged_rows[0]["import_status"] == "review_required"
    assert "unsafe_or_medical_language" in staged_rows[0]["validation_warnings"]


def test_missing_exercise_source_confidence_is_flagged(tmp_path: Path) -> None:
    input_path = tmp_path / "exercises.csv"
    out_dir = tmp_path / "out"
    write_csv(
        input_path,
        [
            {
                "name": "Source Missing Row",
                "equipment": "bodyweight",
                "movement_pattern": "core",
            }
        ],
    )

    result = import_catalog("exercise", str(input_path), str(out_dir))
    staged_rows = read_staged_rows(result.staged_path)

    assert staged_rows[0]["import_status"] == "review_required"
    assert "missing_source_name" in staged_rows[0]["validation_warnings"]
    assert "missing_confidence" in staged_rows[0]["validation_warnings"]


def test_exercise_import_writes_report_findings_and_no_canonical_changes(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "exercises.json"
    out_dir = tmp_path / "out"
    input_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "name": "Romanian Deadlift",
                        "equipment": "barbell",
                        "movement_pattern": "hinge",
                        "source_name": "test fixture",
                        "confidence": "high",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    canonical_path = tmp_path / "canonical_exercise_catalog.csv"
    canonical_path.write_text("do not touch\n", encoding="utf-8")
    before = canonical_path.read_bytes()

    result = import_catalog("exercise", str(input_path), str(out_dir))

    assert result.staged_path.exists()
    assert result.report_path.exists()
    assert result.findings_path.exists()
    assert canonical_path.read_bytes() == before
    findings = json.loads(result.findings_path.read_text(encoding="utf-8"))
    assert findings["canonical_catalog_modified"] is False


def test_exercise_import_cli_rejects_unsupported_input(tmp_path: Path) -> None:
    input_path = tmp_path / "exercises.txt"
    out_dir = tmp_path / "out"
    input_path.write_text("not supported", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "tools/import_exercise_catalog.py",
            "--input",
            str(input_path),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Unsupported input type" in result.stderr
    assert not out_dir.exists()
