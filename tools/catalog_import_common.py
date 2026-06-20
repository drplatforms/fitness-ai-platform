"""Deterministic staged catalog import helpers.

These helpers intentionally write review artifacts only. They do not mutate the
canonical food catalog, canonical exercise catalog, database, provider runtime,
or any user-facing product surface.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

STATUS_ACCEPTED_FOR_REVIEW = "accepted_for_review"
STATUS_REVIEW_REQUIRED = "review_required"
STATUS_REJECTED = "rejected"

FINDING_WARN = "WARN"
FINDING_FAIL = "FAIL"

FOOD_OUTPUT_FIELDS = [
    "import_status",
    "validation_warnings",
    "validation_errors",
    "normalized_name",
    "original_name",
    "calories_per_100g",
    "protein_g_per_100g",
    "carbs_g_per_100g",
    "fat_g_per_100g",
    "aliases",
    "category",
    "source_name",
    "source_policy",
    "confidence",
    "notes",
]

EXERCISE_OUTPUT_FIELDS = [
    "import_status",
    "validation_warnings",
    "validation_errors",
    "normalized_name",
    "original_name",
    "equipment",
    "movement_pattern",
    "primary_muscle_group",
    "secondary_muscle_groups",
    "difficulty",
    "modality",
    "recovery_intensity",
    "contraindication_flags",
    "aliases",
    "notes",
    "source_name",
    "source_policy",
    "confidence",
]

FOOD_REQUIRED_FIELDS = [
    "name",
    "calories_per_100g",
    "protein_g_per_100g",
    "carbs_g_per_100g",
    "fat_g_per_100g",
]

EXERCISE_REQUIRED_FIELDS = ["name", "equipment", "movement_pattern"]

KNOWN_EQUIPMENT = {
    "barbell",
    "bench",
    "bike",
    "bodyweight",
    "cable",
    "dumbbell",
    "ez bar",
    "kettlebell",
    "machine",
    "none",
    "pull-up bar",
    "rack",
    "resistance band",
    "treadmill",
}

KNOWN_MOVEMENT_PATTERNS = {
    "cardio",
    "carry",
    "core",
    "hinge",
    "isolation",
    "locomotion",
    "lunge",
    "mobility",
    "pull",
    "push",
    "rotation",
    "squat",
}

UNSAFE_EXERCISE_LANGUAGE = re.compile(
    r"\b("
    r"cure|cures|heal|heals|healing|rehab|rehabilitation|therapy|therapeutic|"
    r"medical|doctor|clinician|prescribe|treat|treats|treatment|diagnose|"
    r"pain[- ]?free|injury[- ]?proof|guaranteed|fatigue[- ]?free"
    r")\b",
    re.IGNORECASE,
)

WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class ImportFinding:
    row_number: int
    field: str
    severity: str
    code: str
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "row_number": self.row_number,
            "field": self.field,
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }


@dataclass
class ImportResult:
    catalog_type: str
    input_path: Path
    out_dir: Path
    staged_filename: str
    report_filename: str
    findings_filename: str
    staged_rows: list[dict[str, str]] = field(default_factory=list)
    findings: list[ImportFinding] = field(default_factory=list)
    total_rows: int = 0

    @property
    def staged_path(self) -> Path:
        return self.out_dir / self.staged_filename

    @property
    def report_path(self) -> Path:
        return self.out_dir / self.report_filename

    @property
    def findings_path(self) -> Path:
        return self.out_dir / self.findings_filename

    def count_status(self, status: str) -> int:
        return sum(1 for row in self.staged_rows if row["import_status"] == status)


def normalize_name(value: Any) -> str:
    return WHITESPACE_RE.sub(" ", str(value or "").strip()).lower()


def normalize_text(value: Any) -> str:
    return WHITESPACE_RE.sub(" ", str(value or "").strip())


def normalize_aliases(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        raw_values = [str(item) for item in value]
    else:
        raw_values = re.split(r"[;,|]", str(value))

    aliases = [normalize_text(alias).lower() for alias in raw_values]
    return sorted({alias for alias in aliases if alias})


def join_aliases(value: Any) -> str:
    return "; ".join(normalize_aliases(value))


def parse_number(value: Any) -> float | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def read_catalog_rows(input_path: Path) -> list[dict[str, Any]]:
    suffix = input_path.suffix.lower()

    if suffix == ".csv":
        with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]

    if suffix == ".json":
        data = json.loads(input_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict) and isinstance(data.get("rows"), list):
            rows = data["rows"]
        else:
            raise ValueError("JSON input must be a list or an object with a rows list.")

        if not all(isinstance(row, dict) for row in rows):
            raise ValueError("JSON input rows must be objects.")

        return [dict(row) for row in rows]

    raise ValueError("Unsupported input type. Use .csv or .json.")


def add_finding(
    findings: list[ImportFinding],
    row_number: int,
    field: str,
    severity: str,
    code: str,
    message: str,
) -> None:
    findings.append(
        ImportFinding(
            row_number=row_number,
            field=field,
            severity=severity,
            code=code,
            message=message,
        )
    )


def build_status(row_findings: list[ImportFinding]) -> str:
    if any(finding.severity == FINDING_FAIL for finding in row_findings):
        return STATUS_REJECTED

    if any(finding.severity == FINDING_WARN for finding in row_findings):
        return STATUS_REVIEW_REQUIRED

    return STATUS_ACCEPTED_FOR_REVIEW


def summarize_row_findings(row_findings: list[ImportFinding], severity: str) -> str:
    return "; ".join(
        finding.code for finding in row_findings if finding.severity == severity
    )


def find_duplicate_values(rows: list[dict[str, Any]], key: str) -> dict[str, list[int]]:
    seen: dict[str, list[int]] = {}
    for index, row in enumerate(rows, start=1):
        normalized = normalize_name(row.get(key))
        if normalized:
            seen.setdefault(normalized, []).append(index)

    return {value: indexes for value, indexes in seen.items() if len(indexes) > 1}


def find_duplicate_aliases(rows: list[dict[str, Any]]) -> dict[str, list[int]]:
    seen: dict[str, list[int]] = {}
    for index, row in enumerate(rows, start=1):
        for alias in normalize_aliases(row.get("aliases")):
            seen.setdefault(alias, []).append(index)

    return {value: indexes for value, indexes in seen.items() if len(indexes) > 1}


def flag_duplicates(
    findings: list[ImportFinding],
    rows: list[dict[str, Any]],
    row_number: int,
) -> None:
    duplicate_names = find_duplicate_values(rows, "name")
    duplicate_aliases = find_duplicate_aliases(rows)

    normalized_name = normalize_name(rows[row_number - 1].get("name"))
    if normalized_name in duplicate_names:
        add_finding(
            findings,
            row_number,
            "name",
            FINDING_WARN,
            "duplicate_name",
            "Duplicate candidate name found. Flagged for human review.",
        )

    row_aliases = normalize_aliases(rows[row_number - 1].get("aliases"))
    for alias in row_aliases:
        if alias in duplicate_aliases:
            add_finding(
                findings,
                row_number,
                "aliases",
                FINDING_WARN,
                "duplicate_alias",
                "Duplicate candidate alias found. Flagged for human review.",
            )
            break


def flag_missing_source_confidence(
    findings: list[ImportFinding], row: dict[str, Any], row_number: int
) -> None:
    if not normalize_text(row.get("source_name")):
        add_finding(
            findings,
            row_number,
            "source_name",
            FINDING_WARN,
            "missing_source_name",
            "Source name is missing. Candidate requires human review.",
        )

    if not normalize_text(row.get("confidence")):
        add_finding(
            findings,
            row_number,
            "confidence",
            FINDING_WARN,
            "missing_confidence",
            "Confidence is missing. Candidate requires human review.",
        )


def validate_required_fields(
    findings: list[ImportFinding],
    row: dict[str, Any],
    row_number: int,
    required_fields: list[str],
) -> None:
    for field_name in required_fields:
        if field_name not in row or not normalize_text(row.get(field_name)):
            add_finding(
                findings,
                row_number,
                field_name,
                FINDING_FAIL,
                "missing_required_field",
                f"Required field is missing: {field_name}.",
            )


def validate_food_row(
    row: dict[str, Any], rows: list[dict[str, Any]], row_number: int
) -> tuple[dict[str, str], list[ImportFinding]]:
    findings: list[ImportFinding] = []
    validate_required_fields(findings, row, row_number, FOOD_REQUIRED_FIELDS)

    numeric_fields = [
        "calories_per_100g",
        "protein_g_per_100g",
        "carbs_g_per_100g",
        "fat_g_per_100g",
    ]
    parsed: dict[str, float] = {}

    for field_name in numeric_fields:
        value = parse_number(row.get(field_name))
        if value is None:
            add_finding(
                findings,
                row_number,
                field_name,
                FINDING_FAIL,
                "invalid_number",
                f"Field must be numeric: {field_name}.",
            )
            continue

        if value < 0:
            add_finding(
                findings,
                row_number,
                field_name,
                FINDING_FAIL,
                "negative_value",
                f"Field must be non-negative: {field_name}.",
            )

        parsed[field_name] = value

    if all(field_name in parsed for field_name in numeric_fields):
        calories = parsed["calories_per_100g"]
        protein = parsed["protein_g_per_100g"]
        carbs = parsed["carbs_g_per_100g"]
        fat = parsed["fat_g_per_100g"]
        macro_total = protein + carbs + fat
        estimated_calories = protein * 4 + carbs * 4 + fat * 9

        if macro_total > 100:
            add_finding(
                findings,
                row_number,
                "protein_g_per_100g,carbs_g_per_100g,fat_g_per_100g",
                FINDING_WARN,
                "macro_total_over_100g",
                "Total protein/carbs/fat grams exceed 100g per 100g.",
            )

        if calories > 950:
            add_finding(
                findings,
                row_number,
                "calories_per_100g",
                FINDING_WARN,
                "calories_high_per_100g",
                "Calories per 100g are unusually high.",
            )

        if estimated_calories > 0:
            tolerance = max(75.0, estimated_calories * 0.35)
            if abs(calories - estimated_calories) > tolerance:
                add_finding(
                    findings,
                    row_number,
                    "calories_per_100g",
                    FINDING_WARN,
                    "calories_macro_mismatch",
                    "Calories are suspicious relative to macro-derived estimate.",
                )

    serving_fields = {
        "serving_size",
        "serving_g",
        "serving_grams",
        "calories_per_serving",
        "protein_g_per_serving",
        "carbs_g_per_serving",
        "fat_g_per_serving",
    }
    if any(normalize_text(row.get(field_name)) for field_name in serving_fields):
        add_finding(
            findings,
            row_number,
            "serving_size",
            FINDING_WARN,
            "serving_data_present",
            "Serving-size data is present and must not be treated as per-100g.",
        )

    flag_duplicates(findings, rows, row_number)
    flag_missing_source_confidence(findings, row, row_number)

    row_findings = findings
    staged_row = {
        "import_status": build_status(row_findings),
        "validation_warnings": summarize_row_findings(row_findings, FINDING_WARN),
        "validation_errors": summarize_row_findings(row_findings, FINDING_FAIL),
        "normalized_name": normalize_name(row.get("name")),
        "original_name": normalize_text(row.get("name")),
        "calories_per_100g": normalize_text(row.get("calories_per_100g")),
        "protein_g_per_100g": normalize_text(row.get("protein_g_per_100g")),
        "carbs_g_per_100g": normalize_text(row.get("carbs_g_per_100g")),
        "fat_g_per_100g": normalize_text(row.get("fat_g_per_100g")),
        "aliases": join_aliases(row.get("aliases")),
        "category": normalize_text(row.get("category")),
        "source_name": normalize_text(row.get("source_name")),
        "source_policy": normalize_text(row.get("source_policy")),
        "confidence": normalize_text(row.get("confidence")),
        "notes": normalize_text(row.get("notes")),
    }
    return staged_row, row_findings


def validate_exercise_row(
    row: dict[str, Any], rows: list[dict[str, Any]], row_number: int
) -> tuple[dict[str, str], list[ImportFinding]]:
    findings: list[ImportFinding] = []
    validate_required_fields(findings, row, row_number, EXERCISE_REQUIRED_FIELDS)

    equipment = normalize_name(row.get("equipment"))
    movement_pattern = normalize_name(row.get("movement_pattern"))

    if equipment and equipment not in KNOWN_EQUIPMENT:
        add_finding(
            findings,
            row_number,
            "equipment",
            FINDING_WARN,
            "unknown_equipment",
            "Equipment is unknown and requires human review.",
        )

    if movement_pattern and movement_pattern not in KNOWN_MOVEMENT_PATTERNS:
        add_finding(
            findings,
            row_number,
            "movement_pattern",
            FINDING_WARN,
            "unknown_movement_pattern",
            "Movement pattern is unknown and requires human review.",
        )

    text_for_safety = " ".join(
        normalize_text(row.get(field_name))
        for field_name in [
            "name",
            "notes",
            "contraindication_flags",
            "recovery_intensity",
            "difficulty",
            "modality",
        ]
    )
    if UNSAFE_EXERCISE_LANGUAGE.search(text_for_safety):
        add_finding(
            findings,
            row_number,
            "notes",
            FINDING_WARN,
            "unsafe_or_medical_language",
            "Unsafe, medical, rehab, or over-specific coaching language found.",
        )

    flag_duplicates(findings, rows, row_number)
    flag_missing_source_confidence(findings, row, row_number)

    row_findings = findings
    staged_row = {
        "import_status": build_status(row_findings),
        "validation_warnings": summarize_row_findings(row_findings, FINDING_WARN),
        "validation_errors": summarize_row_findings(row_findings, FINDING_FAIL),
        "normalized_name": normalize_name(row.get("name")),
        "original_name": normalize_text(row.get("name")),
        "equipment": equipment,
        "movement_pattern": movement_pattern,
        "primary_muscle_group": normalize_text(row.get("primary_muscle_group")),
        "secondary_muscle_groups": join_aliases(row.get("secondary_muscle_groups")),
        "difficulty": normalize_text(row.get("difficulty")),
        "modality": normalize_text(row.get("modality")),
        "recovery_intensity": normalize_text(row.get("recovery_intensity")),
        "contraindication_flags": normalize_text(row.get("contraindication_flags")),
        "aliases": join_aliases(row.get("aliases")),
        "notes": normalize_text(row.get("notes")),
        "source_name": normalize_text(row.get("source_name")),
        "source_policy": normalize_text(row.get("source_policy")),
        "confidence": normalize_text(row.get("confidence")),
    }
    return staged_row, row_findings


def build_import_result(
    catalog_type: str, input_path: Path, out_dir: Path
) -> ImportResult:
    if catalog_type == "food":
        return ImportResult(
            catalog_type=catalog_type,
            input_path=input_path,
            out_dir=out_dir,
            staged_filename="staged_food_catalog.csv",
            report_filename="food_import_report.md",
            findings_filename="food_import_findings.json",
        )

    if catalog_type == "exercise":
        return ImportResult(
            catalog_type=catalog_type,
            input_path=input_path,
            out_dir=out_dir,
            staged_filename="staged_exercise_catalog.csv",
            report_filename="exercise_import_report.md",
            findings_filename="exercise_import_findings.json",
        )

    raise ValueError(f"Unsupported catalog type: {catalog_type}")


def import_catalog(catalog_type: str, input_path: str, out_dir: str) -> ImportResult:
    source_path = Path(input_path)
    artifact_dir = Path(out_dir)
    rows = read_catalog_rows(source_path)
    result = build_import_result(catalog_type, source_path, artifact_dir)
    result.total_rows = len(rows)

    for row_number, row in enumerate(rows, start=1):
        if catalog_type == "food":
            staged_row, row_findings = validate_food_row(row, rows, row_number)
        elif catalog_type == "exercise":
            staged_row, row_findings = validate_exercise_row(row, rows, row_number)
        else:
            raise ValueError(f"Unsupported catalog type: {catalog_type}")

        result.staged_rows.append(staged_row)
        result.findings.extend(row_findings)

    write_import_outputs(result)
    return result


def write_import_outputs(result: ImportResult) -> None:
    result.out_dir.mkdir(parents=True, exist_ok=True)

    fieldnames = (
        FOOD_OUTPUT_FIELDS if result.catalog_type == "food" else EXERCISE_OUTPUT_FIELDS
    )
    with result.staged_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result.staged_rows)

    findings_payload = {
        "catalog_type": result.catalog_type,
        "input_file": str(result.input_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": build_summary(result),
        "findings": [finding.as_dict() for finding in result.findings],
        "outputs": {
            "staged_csv": str(result.staged_path),
            "report_md": str(result.report_path),
            "findings_json": str(result.findings_path),
        },
        "canonical_catalog_modified": False,
    }
    result.findings_path.write_text(
        json.dumps(findings_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result.report_path.write_text(build_report(result), encoding="utf-8")


def build_summary(result: ImportResult) -> dict[str, int]:
    return {
        "total_rows": result.total_rows,
        "accepted_for_review_rows": result.count_status(STATUS_ACCEPTED_FOR_REVIEW),
        "review_required_rows": result.count_status(STATUS_REVIEW_REQUIRED),
        "rejected_rows": result.count_status(STATUS_REJECTED),
        "warning_findings": sum(
            1 for finding in result.findings if finding.severity == FINDING_WARN
        ),
        "error_findings": sum(
            1 for finding in result.findings if finding.severity == FINDING_FAIL
        ),
    }


def count_findings_by_code(result: ImportResult) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in result.findings:
        counts[finding.code] = counts.get(finding.code, 0) + 1
    return dict(sorted(counts.items()))


def build_report(result: ImportResult) -> str:
    summary = build_summary(result)
    finding_counts = count_findings_by_code(result)
    finding_lines = [f"- {code}: {count}" for code, count in finding_counts.items()]
    if not finding_lines:
        finding_lines = ["- None"]

    catalog_label = "Food" if result.catalog_type == "food" else "Exercise"
    duplicate_codes = {"duplicate_name", "duplicate_alias"}
    duplicate_count = sum(
        count for code, count in finding_counts.items() if code in duplicate_codes
    )

    if result.catalog_type == "food":
        suspicious_count = sum(
            finding_counts.get(code, 0)
            for code in [
                "calories_macro_mismatch",
                "macro_total_over_100g",
                "calories_high_per_100g",
                "serving_data_present",
            ]
        )
        domain_lines = [
            f"- duplicate findings: {duplicate_count}",
            f"- suspicious macro findings: {suspicious_count}",
            f"- missing source/confidence findings: {finding_counts.get('missing_source_name', 0) + finding_counts.get('missing_confidence', 0)}",
        ]
    else:
        unknown_equipment = finding_counts.get("unknown_equipment", 0)
        unknown_pattern = finding_counts.get("unknown_movement_pattern", 0)
        unsafe_language = finding_counts.get("unsafe_or_medical_language", 0)
        domain_lines = [
            f"- duplicate findings: {duplicate_count}",
            f"- unknown equipment findings: {unknown_equipment}",
            f"- unknown movement pattern findings: {unknown_pattern}",
            f"- unsafe language findings: {unsafe_language}",
            f"- missing source/confidence findings: {finding_counts.get('missing_source_name', 0) + finding_counts.get('missing_confidence', 0)}",
        ]

    return "\n".join(
        [
            f"# {catalog_label} Catalog Import Report",
            "",
            "This report is a staged import review artifact only.",
            "It is not canonical, not production-approved, and not a production merge.",
            "",
            "## Input",
            "",
            f"- input file: {result.input_path}",
            f"- catalog type: {result.catalog_type}",
            "",
            "## Summary",
            "",
            f"- total rows: {summary['total_rows']}",
            f"- staged rows: {len(result.staged_rows)}",
            f"- accepted_for_review rows: {summary['accepted_for_review_rows']}",
            f"- review_required rows: {summary['review_required_rows']}",
            f"- rejected rows: {summary['rejected_rows']}",
            "",
            "## Domain Findings",
            "",
            *domain_lines,
            "",
            "## Finding Counts",
            "",
            *finding_lines,
            "",
            "## Output Files Written",
            "",
            f"- staged CSV: {result.staged_path}",
            f"- findings JSON: {result.findings_path}",
            f"- report Markdown: {result.report_path}",
            "",
            "## Canonical Catalog Boundary",
            "",
            "No canonical catalog rows were changed.",
            "No staged row is production-approved.",
            "Every candidate row requires human review before any future canonical merge.",
            "",
        ]
    )


def build_catalog_import_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--input", required=True, help="Local CSV or JSON source file.")
    parser.add_argument(
        "--out-dir", required=True, help="Local output directory for review artifacts."
    )
    return parser


def run_catalog_import_cli(catalog_type: str, description: str) -> int:
    parser = build_catalog_import_parser(description)
    args = parser.parse_args()

    try:
        result = import_catalog(catalog_type, args.input, args.out_dir)
    except Exception as exc:
        parser.exit(status=2, message=f"Catalog import failed: {exc}\n")
        return 2

    summary = build_summary(result)
    print(f"{catalog_type.title()} catalog import complete.")
    print(f"Input: {result.input_path}")
    print(f"Staged CSV: {result.staged_path}")
    print(f"Report: {result.report_path}")
    print(f"Findings JSON: {result.findings_path}")
    print(f"accepted_for_review: {summary['accepted_for_review_rows']}")
    print(f"review_required: {summary['review_required_rows']}")
    print(f"rejected: {summary['rejected_rows']}")
    print("Canonical catalog modified: false")
    return 0
