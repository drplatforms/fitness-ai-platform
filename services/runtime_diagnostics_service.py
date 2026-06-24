from __future__ import annotations

import platform
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import database

QA_USER_SCENARIOS: dict[int, str] = {
    101: "recovery_limited",
    102: "aligned_managed",
    103: "nutrition_training_mismatch",
    104: "improving_after_deload",
    105: "data_quality_limited",
}

EXPECTED_QA_SEED_START = "2025-12-17"
EXPECTED_QA_SEED_END = "2026-06-14"

RELEVANT_TABLES = [
    "users",
    "daily_checkins",
    "food_entries",
    "workout_sessions",
    "workout_sets",
    "workout_plan_instances",
    "planned_workout_exercises",
    "workout_execution_sessions",
    "workout_execution_set_actuals",
]


class RuntimeDiagnosticsError(Exception):
    """Raised only for internal misuse; UI-facing diagnostics stay sanitized."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_git(args: list[str], repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ):
        return None

    value = result.stdout.strip()
    return value or None


def _iso_timestamp_from_stat(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).isoformat(timespec="seconds")


def _resolved_db_path(db_path: str | Path | None = None) -> Path:
    return (
        Path(db_path if db_path is not None else database.DB_PATH)
        .expanduser()
        .resolve()
    )


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _fetch_table_names(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [str(row["name"]) for row in rows]


def _safe_query_single(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[Any, ...],
) -> dict[str, Any] | None:
    try:
        row = connection.execute(sql, parameters).fetchone()
    except sqlite3.Error:
        return None

    return dict(row) if row is not None else None


def build_runtime_identity(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    status = _run_git(["status", "--porcelain"], root)

    return {
        "git_commit_short": _run_git(["rev-parse", "--short", "HEAD"], root),
        "git_commit_full": _run_git(["rev-parse", "HEAD"], root),
        "git_branch": _run_git(["rev-parse", "--abbrev-ref", "HEAD"], root),
        "dirty_working_tree": None if status is None else bool(status),
        "git_metadata_available": _run_git(["rev-parse", "--is-inside-work-tree"], root)
        == "true",
        "repository_root": str(root),
        "current_working_directory": str(Path.cwd()),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "runtime_mode": "local_streamlit_or_fastapi_process",
    }


def build_database_source(db_path: str | Path | None = None) -> dict[str, Any]:
    resolved_path = _resolved_db_path(db_path)
    exists = resolved_path.exists()

    result: dict[str, Any] = {
        "resolved_database_path": str(resolved_path),
        "database_exists": exists,
        "database_file_size_bytes": None,
        "database_modified_at": None,
        "sqlite_connectable": False,
        "available_table_count": None,
        "relevant_tables_found": [],
        "error_category": None,
    }

    if exists:
        try:
            stat = resolved_path.stat()
        except OSError:
            result["error_category"] = "stat_failed"
        else:
            result["database_file_size_bytes"] = stat.st_size
            result["database_modified_at"] = _iso_timestamp_from_stat(stat.st_mtime)
    else:
        result["error_category"] = "database_missing"
        return result

    try:
        with _connect(resolved_path) as connection:
            table_names = _fetch_table_names(connection)
    except sqlite3.Error:
        result["error_category"] = "sqlite_connection_failed"
        return result

    result["sqlite_connectable"] = True
    result["available_table_count"] = len(table_names)
    result["relevant_tables_found"] = [
        table for table in RELEVANT_TABLES if table in table_names
    ]
    result["error_category"] = None
    return result


def _empty_domain_summary(available: bool, reason: str | None = None) -> dict[str, Any]:
    return {
        "available": available,
        "row_count": 0,
        "min_date": None,
        "max_date": None,
        "reason": reason,
    }


def _domain_summary(
    connection: sqlite3.Connection,
    table_names: set[str],
    table: str,
    user_id: int,
    date_column: str,
) -> dict[str, Any]:
    if table not in table_names:
        return _empty_domain_summary(False, f"missing_table:{table}")

    row = _safe_query_single(
        connection,
        f"""
        SELECT
            COUNT(*) AS row_count,
            MIN({date_column}) AS min_date,
            MAX({date_column}) AS max_date
        FROM {table}
        WHERE user_id = ?
        """,
        (user_id,),
    )
    if row is None:
        return _empty_domain_summary(False, f"query_failed:{table}")

    return {
        "available": True,
        "row_count": int(row.get("row_count") or 0),
        "min_date": row.get("min_date"),
        "max_date": row.get("max_date"),
        "reason": None,
    }


def _actual_set_summary(
    connection: sqlite3.Connection,
    table_names: set[str],
    user_id: int,
) -> dict[str, Any]:
    required_tables = {
        "workout_execution_set_actuals",
        "workout_execution_sessions",
    }
    missing_tables = sorted(required_tables.difference(table_names))
    if missing_tables:
        return _empty_domain_summary(False, "missing_table:" + ",".join(missing_tables))

    row = _safe_query_single(
        connection,
        """
        SELECT
            COUNT(*) AS row_count,
            MIN(COALESCE(
                workout_sessions.workout_date,
                date(workout_execution_sessions.completed_at),
                date(workout_execution_sessions.started_at),
                date(workout_execution_set_actuals.created_at)
            )) AS min_date,
            MAX(COALESCE(
                workout_sessions.workout_date,
                date(workout_execution_sessions.completed_at),
                date(workout_execution_sessions.started_at),
                date(workout_execution_set_actuals.created_at)
            )) AS max_date
        FROM workout_execution_set_actuals
        JOIN workout_execution_sessions
            ON workout_execution_sessions.id =
                workout_execution_set_actuals.workout_execution_session_id
        LEFT JOIN workout_sessions
            ON workout_sessions.id = workout_execution_set_actuals.workout_session_id
        WHERE workout_execution_sessions.user_id = ?
        """,
        (user_id,),
    )
    if row is None:
        return _empty_domain_summary(
            False, "query_failed:workout_execution_set_actuals"
        )

    return {
        "available": True,
        "row_count": int(row.get("row_count") or 0),
        "min_date": row.get("min_date"),
        "max_date": row.get("max_date"),
        "reason": None,
    }


def _user_summary(
    connection: sqlite3.Connection,
    table_names: set[str],
    user_id: int,
) -> dict[str, Any]:
    scenario = QA_USER_SCENARIOS.get(user_id, "unknown")
    user_exists = False
    user_name = None

    if "users" in table_names:
        row = _safe_query_single(
            connection,
            "SELECT id, name FROM users WHERE id = ?",
            (user_id,),
        )
        if row is not None:
            user_exists = True
            user_name = row.get("name")

    return {
        "user_id": user_id,
        "scenario": scenario,
        "user_exists": user_exists,
        "user_name": user_name,
        "recovery": _domain_summary(
            connection,
            table_names,
            "daily_checkins",
            user_id,
            "checkin_date",
        ),
        "nutrition": _domain_summary(
            connection,
            table_names,
            "food_entries",
            user_id,
            "entry_date",
        ),
        "workouts": _domain_summary(
            connection,
            table_names,
            "workout_sessions",
            user_id,
            "workout_date",
        ),
        "actual_sets": _actual_set_summary(connection, table_names, user_id),
    }


def build_qa_seed_diagnostics(
    db_path: str | Path | None = None,
    user_ids: list[int] | None = None,
) -> list[dict[str, Any]]:
    resolved_path = _resolved_db_path(db_path)
    ids = user_ids or list(QA_USER_SCENARIOS)

    if not resolved_path.exists():
        return [
            {
                "user_id": user_id,
                "scenario": QA_USER_SCENARIOS.get(user_id, "unknown"),
                "user_exists": False,
                "user_name": None,
                "recovery": _empty_domain_summary(False, "database_missing"),
                "nutrition": _empty_domain_summary(False, "database_missing"),
                "workouts": _empty_domain_summary(False, "database_missing"),
                "actual_sets": _empty_domain_summary(False, "database_missing"),
            }
            for user_id in ids
        ]

    try:
        with _connect(resolved_path) as connection:
            table_names = set(_fetch_table_names(connection))
            return [_user_summary(connection, table_names, user_id) for user_id in ids]
    except sqlite3.Error:
        return [
            {
                "user_id": user_id,
                "scenario": QA_USER_SCENARIOS.get(user_id, "unknown"),
                "user_exists": False,
                "user_name": None,
                "recovery": _empty_domain_summary(False, "sqlite_connection_failed"),
                "nutrition": _empty_domain_summary(False, "sqlite_connection_failed"),
                "workouts": _empty_domain_summary(False, "sqlite_connection_failed"),
                "actual_sets": _empty_domain_summary(False, "sqlite_connection_failed"),
            }
            for user_id in ids
        ]


def _domain_has_rows(user_summary: dict[str, Any]) -> bool:
    for domain in ("recovery", "nutrition", "workouts", "actual_sets"):
        if int(user_summary.get(domain, {}).get("row_count") or 0) > 0:
            return True
    return False


def _date_bounds_overlap_expected(user_summary: dict[str, Any]) -> bool:
    for domain in ("recovery", "nutrition", "workouts"):
        summary = user_summary.get(domain, {})
        min_date = summary.get("min_date")
        max_date = summary.get("max_date")
        if min_date and max_date:
            if (
                str(max_date) >= EXPECTED_QA_SEED_START
                and str(min_date) <= EXPECTED_QA_SEED_END
            ):
                return True
    return False


def build_runtime_warnings(
    database_source: dict[str, Any],
    qa_seed_diagnostics: list[dict[str, Any]],
) -> list[str]:
    warnings: list[str] = []

    if not database_source.get("database_exists"):
        warnings.append("Database file was not found at the resolved path.")
        return warnings

    if not database_source.get("sqlite_connectable"):
        warnings.append("Database file exists but SQLite could not connect to it.")
        return warnings

    if not any(user.get("user_exists") for user in qa_seed_diagnostics):
        warnings.append("QA users 101-105 were not found in this database.")
        return warnings

    users_with_rows = [user for user in qa_seed_diagnostics if _domain_has_rows(user)]
    if not users_with_rows:
        warnings.append("QA users exist, but no QA diagnostic rows were found.")
        return warnings

    if not any(_date_bounds_overlap_expected(user) for user in users_with_rows):
        warnings.append(
            "QA users exist, but date bounds do not overlap the expected seeded range. "
            "Confirm seed script/runtime DB."
        )

    return warnings


def build_runtime_db_diagnostics(
    api_base_url: str | None = None,
    db_path: str | Path | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    runtime_identity = build_runtime_identity(repo_root=repo_root)
    database_source = build_database_source(db_path=db_path)
    qa_seed_diagnostics = build_qa_seed_diagnostics(db_path=db_path)
    warnings = build_runtime_warnings(database_source, qa_seed_diagnostics)

    return {
        "success": True,
        "runtime_identity": runtime_identity,
        "database_source": database_source,
        "streamlit_fastapi": {
            "configured_api_base_url": api_base_url,
            "diagnostic_path": "direct_db_service",
        },
        "qa_seed_diagnostics": qa_seed_diagnostics,
        "warnings": warnings,
    }
