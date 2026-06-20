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


def test_valid_food_rows_stage_successfully(tmp_path: Path) -> None:
    input_path = tmp_path / "foods.csv"
    out_dir = tmp_path / "out"
    write_csv(
        input_path,
        [
            {
                "name": "Chicken Breast",
                "calories_per_100g": "165",
                "protein_g_per_100g": "31",
                "carbs_g_per_100g": "0",
                "fat_g_per_100g": "3.6",
                "aliases": "chicken; lean chicken",
                "category": "protein",
                "source_name": "test fixture",
                "source_policy": "local test data",
                "confidence": "high",
            }
        ],
    )

    result = import_catalog("food", str(input_path), str(out_dir))

    staged_rows = read_staged_rows(result.staged_path)
    assert staged_rows[0]["import_status"] == "accepted_for_review"
    assert staged_rows[0]["normalized_name"] == "chicken breast"
    assert result.report_path.exists()
    assert result.findings_path.exists()


def test_missing_required_food_fields_fail(tmp_path: Path) -> None:
    input_path = tmp_path / "foods.csv"
    out_dir = tmp_path / "out"
    write_csv(
        input_path,
        [
            {
                "name": "Incomplete Food",
                "calories_per_100g": "100",
                "protein_g_per_100g": "10",
                "carbs_g_per_100g": "5",
                "source_name": "test fixture",
                "confidence": "medium",
            }
        ],
    )

    result = import_catalog("food", str(input_path), str(out_dir))
    staged_rows = read_staged_rows(result.staged_path)

    assert staged_rows[0]["import_status"] == "rejected"
    assert "missing_required_field" in staged_rows[0]["validation_errors"]


def test_negative_macro_values_fail(tmp_path: Path) -> None:
    input_path = tmp_path / "foods.csv"
    out_dir = tmp_path / "out"
    write_csv(
        input_path,
        [
            {
                "name": "Bad Macro Food",
                "calories_per_100g": "100",
                "protein_g_per_100g": "-1",
                "carbs_g_per_100g": "5",
                "fat_g_per_100g": "2",
                "source_name": "test fixture",
                "confidence": "medium",
            }
        ],
    )

    result = import_catalog("food", str(input_path), str(out_dir))
    staged_rows = read_staged_rows(result.staged_path)

    assert staged_rows[0]["import_status"] == "rejected"
    assert "negative_value" in staged_rows[0]["validation_errors"]


def test_duplicate_food_names_and_aliases_are_flagged(tmp_path: Path) -> None:
    input_path = tmp_path / "foods.csv"
    out_dir = tmp_path / "out"
    rows = [
        {
            "name": "Greek Yogurt",
            "calories_per_100g": "59",
            "protein_g_per_100g": "10",
            "carbs_g_per_100g": "3.6",
            "fat_g_per_100g": "0.4",
            "aliases": "yogurt cup",
            "source_name": "test fixture",
            "confidence": "high",
        },
        {
            "name": "Greek Yogurt",
            "calories_per_100g": "60",
            "protein_g_per_100g": "9",
            "carbs_g_per_100g": "4",
            "fat_g_per_100g": "0.3",
            "aliases": "yogurt cup",
            "source_name": "test fixture",
            "confidence": "high",
        },
    ]
    write_csv(input_path, rows)

    result = import_catalog("food", str(input_path), str(out_dir))
    staged_rows = read_staged_rows(result.staged_path)

    assert all(row["import_status"] == "review_required" for row in staged_rows)
    assert "duplicate_name" in staged_rows[0]["validation_warnings"]
    assert "duplicate_alias" in staged_rows[1]["validation_warnings"]


def test_suspicious_food_calories_macros_and_serving_data_are_flagged(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "foods.csv"
    out_dir = tmp_path / "out"
    write_csv(
        input_path,
        [
            {
                "name": "Suspicious Bar",
                "calories_per_100g": "80",
                "protein_g_per_100g": "40",
                "carbs_g_per_100g": "40",
                "fat_g_per_100g": "40",
                "serving_size": "1 bar",
                "source_name": "test fixture",
                "confidence": "low",
            }
        ],
    )

    result = import_catalog("food", str(input_path), str(out_dir))
    staged_rows = read_staged_rows(result.staged_path)
    warnings = staged_rows[0]["validation_warnings"]

    assert staged_rows[0]["import_status"] == "review_required"
    assert "macro_total_over_100g" in warnings
    assert "calories_macro_mismatch" in warnings
    assert "serving_data_present" in warnings


def test_missing_food_source_confidence_is_flagged(tmp_path: Path) -> None:
    input_path = tmp_path / "foods.csv"
    out_dir = tmp_path / "out"
    write_csv(
        input_path,
        [
            {
                "name": "Unknown Source Food",
                "calories_per_100g": "100",
                "protein_g_per_100g": "5",
                "carbs_g_per_100g": "15",
                "fat_g_per_100g": "2",
            }
        ],
    )

    result = import_catalog("food", str(input_path), str(out_dir))
    staged_rows = read_staged_rows(result.staged_path)

    assert staged_rows[0]["import_status"] == "review_required"
    assert "missing_source_name" in staged_rows[0]["validation_warnings"]
    assert "missing_confidence" in staged_rows[0]["validation_warnings"]


def test_food_import_writes_report_findings_and_no_canonical_changes(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "foods.json"
    out_dir = tmp_path / "out"
    input_path.write_text(
        json.dumps(
            [
                {
                    "name": "Oats",
                    "calories_per_100g": "389",
                    "protein_g_per_100g": "16.9",
                    "carbs_g_per_100g": "66.3",
                    "fat_g_per_100g": "6.9",
                    "source_name": "test fixture",
                    "confidence": "high",
                }
            ]
        ),
        encoding="utf-8",
    )
    canonical_path = tmp_path / "canonical_food_catalog.csv"
    canonical_path.write_text("do not touch\n", encoding="utf-8")
    before = canonical_path.read_bytes()

    result = import_catalog("food", str(input_path), str(out_dir))

    assert result.staged_path.exists()
    assert result.report_path.exists()
    assert result.findings_path.exists()
    assert canonical_path.read_bytes() == before
    findings = json.loads(result.findings_path.read_text(encoding="utf-8"))
    assert findings["canonical_catalog_modified"] is False


def test_food_import_cli_rejects_unsupported_input(tmp_path: Path) -> None:
    input_path = tmp_path / "foods.txt"
    out_dir = tmp_path / "out"
    input_path.write_text("not supported", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "tools/import_food_catalog.py",
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
