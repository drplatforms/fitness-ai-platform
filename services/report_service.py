from __future__ import annotations

import json
from typing import Any

from database import get_connection

# -----------------------------
# Public report persistence guardrails
# -----------------------------

_PUBLIC_REPORT_FORBIDDEN_TERMS = [
    "raw_output",
    "raw_output_preview_truncated",
    "model_facing_quote_context",
    "approved_training_quote_context",
    "candidate_parse_status",
    "candidate_validation_status",
    "validation_errors",
    "prompt",
    "schema",
]

_SAFE_REPORT_METADATA_FIELDS = {
    "user_id",
    "report_date",
    "report_job_id",
    "report_status",
    "generated_at",
    "completed_at",
    "provider_enabled",
    "provider_attempted",
    "selected_provider",
    "selected_model",
    "fallback_used",
    "fallback_reason",
    "training_section_source",
    "provider_latency_ms",
    "validation_status",
    "validation_errors_count",
    "report_generation_mode",
    "full_report_composer_source",
    "coordinator_attempted",
    "coordinator_fallback_used",
    "coordinator_fallback_reason",
    "async_job_used",
}


def validate_public_report_content(report_text: str) -> list[str]:
    """Return forbidden public-content terms found in report text."""

    report_lower = report_text.lower()
    return [term for term in _PUBLIC_REPORT_FORBIDDEN_TERMS if term in report_lower]


def _json_safe_value(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    return str(value)


def sanitize_report_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Keep only safe, summary-level report metadata for persistence."""

    if not metadata:
        return {}

    return {
        key: _json_safe_value(metadata[key])
        for key in sorted(_SAFE_REPORT_METADATA_FIELDS)
        if key in metadata
    }


def serialize_report_metadata(metadata: dict[str, Any] | None) -> str | None:
    safe_metadata = sanitize_report_metadata(metadata)
    if not safe_metadata:
        return None
    return json.dumps(safe_metadata, sort_keys=True)


def _health_report_columns(cursor) -> set[str]:
    cursor.execute("PRAGMA table_info(health_reports)")
    return {row[1] for row in cursor.fetchall()}


def _ensure_health_report_persistence_columns(cursor) -> None:
    columns = _health_report_columns(cursor)

    if "report_date" not in columns:
        cursor.execute("ALTER TABLE health_reports ADD COLUMN report_date TEXT")

    if "report_metadata_json" not in columns:
        cursor.execute(
            "ALTER TABLE health_reports ADD COLUMN report_metadata_json TEXT"
        )


# -----------------------------
# Save Health Report
# -----------------------------


def save_health_report(
    user_id,
    report_text,
    model_summary=None,
    *,
    report_date: str | None = None,
    report_metadata: dict[str, Any] | None = None,
):
    forbidden_terms = validate_public_report_content(report_text)
    if forbidden_terms:
        raise ValueError(
            "Public report content contains forbidden debug/provider terms: "
            + ", ".join(forbidden_terms)
        )

    conn = get_connection()
    cursor = conn.cursor()
    _ensure_health_report_persistence_columns(cursor)

    cursor.execute(
        """
    INSERT INTO health_reports (
        user_id,
        report_text,
        model_summary,
        report_date,
        report_metadata_json
    )
    VALUES (?, ?, ?, ?, ?)
    """,
        (
            user_id,
            report_text,
            model_summary,
            report_date,
            serialize_report_metadata(report_metadata),
        ),
    )

    conn.commit()
    conn.close()


# -----------------------------
# Get Latest Health Report
# -----------------------------


def get_latest_health_report(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_health_report_persistence_columns(cursor)

    cursor.execute(
        """
    SELECT *
    FROM health_reports
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT 1
    """,
        (user_id,),
    )

    report = cursor.fetchone()

    conn.commit()
    conn.close()

    return report


# -----------------------------
# Get Health Report History
# -----------------------------


def get_health_report_history(user_id, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_health_report_persistence_columns(cursor)

    cursor.execute(
        """
    SELECT *
    FROM health_reports
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT ?
    """,
        (user_id, limit),
    )

    reports = cursor.fetchall()

    conn.commit()
    conn.close()

    return reports
