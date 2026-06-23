from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from typing import Any

from database import get_connection
from models.weekly_coach_summary_models import WeeklyCoachSummaryContext
from services.weekly_coach_summary_service import (
    build_weekly_summary_context_from_fixture,
)

QA_USER_SCENARIOS: dict[int, str] = {
    101: "recovery_limited",
    102: "aligned_managed",
    103: "nutrition_training_mismatch",
    104: "improving_after_deload",
    105: "data_quality_limited",
}

QA_DEBUG_RANGE_OPTIONS: dict[str, tuple[str, str]] = {
    "Latest seeded week: 2026-06-08 to 2026-06-14": (
        "2026-06-08",
        "2026-06-14",
    ),
    "Previous seeded week: 2026-06-01 to 2026-06-07": (
        "2026-06-01",
        "2026-06-07",
    ),
    "Last 14 seeded days: 2026-06-01 to 2026-06-14": (
        "2026-06-01",
        "2026-06-14",
    ),
    "Last 28 seeded days: 2026-05-18 to 2026-06-14": (
        "2026-05-18",
        "2026-06-14",
    ),
    "Full seeded range: 2025-12-17 to 2026-06-14": (
        "2025-12-17",
        "2026-06-14",
    ),
    "Custom": ("2026-06-08", "2026-06-14"),
}


class WeeklyCoachSummaryQADataError(ValueError):
    """Raised when QA date-range inspection input is invalid."""


@dataclass(frozen=True)
class WeeklyCoachSummaryQAUserOption:
    user_id: int
    scenario: str
    label: str
    present: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "scenario": self.scenario,
            "label": self.label,
            "present": self.present,
        }


@dataclass(frozen=True)
class WeeklyCoachSummaryUserDateBounds:
    user_id: int
    earliest_recovery_date: str | None = None
    latest_recovery_date: str | None = None
    earliest_nutrition_date: str | None = None
    latest_nutrition_date: str | None = None
    earliest_workout_date: str | None = None
    latest_workout_date: str | None = None

    @property
    def overall_earliest_date(self) -> str | None:
        values = [
            value
            for value in (
                self.earliest_recovery_date,
                self.earliest_nutrition_date,
                self.earliest_workout_date,
            )
            if value
        ]
        return min(values) if values else None

    @property
    def overall_latest_date(self) -> str | None:
        values = [
            value
            for value in (
                self.latest_recovery_date,
                self.latest_nutrition_date,
                self.latest_workout_date,
            )
            if value
        ]
        return max(values) if values else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "earliest_recovery_date": self.earliest_recovery_date,
            "latest_recovery_date": self.latest_recovery_date,
            "earliest_nutrition_date": self.earliest_nutrition_date,
            "latest_nutrition_date": self.latest_nutrition_date,
            "earliest_workout_date": self.earliest_workout_date,
            "latest_workout_date": self.latest_workout_date,
            "overall_earliest_date": self.overall_earliest_date,
            "overall_latest_date": self.overall_latest_date,
        }


@dataclass(frozen=True)
class WeeklyCoachSummaryFactInventory:
    user_id: int
    start_date: str
    end_date: str
    scenario: str
    recovery_checkins_count: int = 0
    nutrition_logged_days_count: int = 0
    nutrition_entries_count: int = 0
    completed_workouts_count: int = 0
    actual_sets_count: int = 0
    planned_workouts_count: int = 0
    skipped_sets_count: int = 0
    average_sleep_hours: float | None = None
    average_energy_level: float | None = None
    average_soreness_level: float | None = None
    data_quality_label: str = "insufficient"
    reason_codes: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "scenario": self.scenario,
            "recovery_checkins_count": self.recovery_checkins_count,
            "nutrition_logged_days_count": self.nutrition_logged_days_count,
            "nutrition_entries_count": self.nutrition_entries_count,
            "completed_workouts_count": self.completed_workouts_count,
            "actual_sets_count": self.actual_sets_count,
            "planned_workouts_count": self.planned_workouts_count,
            "skipped_sets_count": self.skipped_sets_count,
            "average_sleep_hours": self.average_sleep_hours,
            "average_energy_level": self.average_energy_level,
            "average_soreness_level": self.average_soreness_level,
            "data_quality_label": self.data_quality_label,
            "reason_codes": self.reason_codes,
            "limitations": self.limitations,
        }


@contextmanager
def _managed_connection(
    connection: sqlite3.Connection | None = None,
) -> Any:
    if connection is not None:
        yield connection
        return

    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def _parse_date(value: date | str, field_name: str) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise WeeklyCoachSummaryQADataError(
                f"{field_name} must be an ISO date string."
            ) from exc
    raise WeeklyCoachSummaryQADataError(f"{field_name} must be a date or ISO string.")


def _validate_date_range(
    start_date: date | str, end_date: date | str
) -> tuple[str, str]:
    start_iso = _parse_date(start_date, "start_date")
    end_iso = _parse_date(end_date, "end_date")
    if start_iso > end_iso:
        raise WeeklyCoachSummaryQADataError(
            "start_date must be before or equal to end_date."
        )
    return start_iso, end_iso


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _has_column(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    if not _table_exists(conn, table_name):
        return False
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(str(row[1]) == column_name for row in rows)


def _count(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row[0] or 0) if row is not None else 0


def _avg(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> float | None:
    row = conn.execute(sql, params).fetchone()
    if row is None or row[0] is None:
        return None
    return round(float(row[0]), 1)


def _date_bounds_for(
    conn: sqlite3.Connection,
    *,
    table_name: str,
    user_id: int,
    date_column: str,
) -> tuple[str | None, str | None]:
    if not _table_exists(conn, table_name):
        return None, None
    row = conn.execute(
        f"SELECT MIN({date_column}), MAX({date_column}) FROM {table_name} WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None, None
    return row[0], row[1]


def get_qa_user_options(
    connection: sqlite3.Connection | None = None,
) -> tuple[WeeklyCoachSummaryQAUserOption, ...]:
    """Return known QA users with safe scenario labels and DB presence.

    This function returns labels only; it does not expose raw profile data.
    """

    with _managed_connection(connection) as conn:
        present_user_ids: set[int] = set()
        if _table_exists(conn, "users"):
            placeholders = ",".join("?" for _ in QA_USER_SCENARIOS)
            rows = conn.execute(
                f"SELECT id FROM users WHERE id IN ({placeholders})",
                tuple(QA_USER_SCENARIOS),
            ).fetchall()
            present_user_ids = {int(row[0]) for row in rows}

    return tuple(
        WeeklyCoachSummaryQAUserOption(
            user_id=user_id,
            scenario=scenario,
            label=f"{user_id} - {scenario}",
            present=user_id in present_user_ids,
        )
        for user_id, scenario in QA_USER_SCENARIOS.items()
    )


def get_user_data_date_bounds(
    user_id: int,
    connection: sqlite3.Connection | None = None,
) -> WeeklyCoachSummaryUserDateBounds:
    user_id = int(user_id)
    with _managed_connection(connection) as conn:
        recovery_min, recovery_max = _date_bounds_for(
            conn,
            table_name="daily_checkins",
            user_id=user_id,
            date_column="checkin_date",
        )
        nutrition_min, nutrition_max = _date_bounds_for(
            conn,
            table_name="food_entries",
            user_id=user_id,
            date_column="entry_date",
        )
        workout_min, workout_max = _date_bounds_for(
            conn,
            table_name="workout_sessions",
            user_id=user_id,
            date_column="workout_date",
        )

    return WeeklyCoachSummaryUserDateBounds(
        user_id=user_id,
        earliest_recovery_date=recovery_min,
        latest_recovery_date=recovery_max,
        earliest_nutrition_date=nutrition_min,
        latest_nutrition_date=nutrition_max,
        earliest_workout_date=workout_min,
        latest_workout_date=workout_max,
    )


def _quality_label(
    *,
    recovery_checkins_count: int,
    nutrition_logged_days_count: int,
    completed_workouts_count: int,
    actual_sets_count: int,
) -> str:
    if (
        recovery_checkins_count >= 5
        and nutrition_logged_days_count >= 5
        and completed_workouts_count >= 3
        and actual_sets_count > 0
    ):
        return "strong"
    major_categories = sum(
        [
            recovery_checkins_count > 0,
            nutrition_logged_days_count > 0,
            completed_workouts_count > 0,
        ]
    )
    if major_categories >= 2 and completed_workouts_count >= 2:
        return "usable"
    if major_categories >= 1:
        return "limited"
    return "insufficient"


def _reason_codes_for_inventory(
    *,
    recovery_checkins_count: int,
    nutrition_logged_days_count: int,
    completed_workouts_count: int,
    actual_sets_count: int,
    data_quality_label: str,
) -> tuple[str, ...]:
    reason_codes = ["qa_data_range_inspected", "approved_backend_facts_only"]
    if completed_workouts_count >= 3:
        reason_codes.append("weekly_training_consistency_detected")
    elif completed_workouts_count <= 0:
        reason_codes.append("insufficient_weekly_data")
    else:
        reason_codes.append("mixed_signal_week")
    if recovery_checkins_count < 5:
        reason_codes.append("limited_recovery_logging")
    if nutrition_logged_days_count < 5:
        reason_codes.append("limited_nutrition_logging")
    if actual_sets_count <= 0:
        reason_codes.append("limited_workout_execution_logging")
    reason_codes.append(f"data_quality_{data_quality_label}")
    return tuple(dict.fromkeys(reason_codes))


def _limitations_for_inventory(
    *,
    recovery_checkins_count: int,
    nutrition_logged_days_count: int,
    completed_workouts_count: int,
    actual_sets_count: int,
    data_quality_label: str,
) -> tuple[str, ...]:
    limitations: list[str] = []
    if recovery_checkins_count < 5:
        limitations.append("Recovery check-ins are limited for the selected range.")
    if nutrition_logged_days_count < 5:
        limitations.append("Nutrition logging is limited for the selected range.")
    if completed_workouts_count <= 0:
        limitations.append(
            "No completed workouts are available for the selected range."
        )
    elif actual_sets_count <= 0:
        limitations.append(
            "Workout execution set details are limited for the selected range."
        )
    if data_quality_label in {"limited", "insufficient"}:
        limitations.append(
            "Selected range should produce cautious guidance or deterministic fallback."
        )
    return tuple(dict.fromkeys(limitations))


def get_weekly_summary_fact_inventory(
    *,
    user_id: int,
    start_date: date | str,
    end_date: date | str,
    connection: sqlite3.Connection | None = None,
) -> WeeklyCoachSummaryFactInventory:
    """Return sanitized aggregate counts for a selected QA user/date range.

    This function intentionally returns counts and safe aggregate averages only. It
    does not return raw food logs, check-in notes, workout set rows, prompts, or
    provider output.
    """

    user_id = int(user_id)
    start_iso, end_iso = _validate_date_range(start_date, end_date)
    scenario = QA_USER_SCENARIOS.get(user_id, "unknown")

    with _managed_connection(connection) as conn:
        recovery_count = (
            _count(
                conn,
                "SELECT COUNT(*) FROM daily_checkins WHERE user_id = ? AND checkin_date BETWEEN ? AND ?",
                (user_id, start_iso, end_iso),
            )
            if _table_exists(conn, "daily_checkins")
            else 0
        )
        average_sleep = (
            _avg(
                conn,
                "SELECT AVG(sleep_hours) FROM daily_checkins WHERE user_id = ? AND checkin_date BETWEEN ? AND ?",
                (user_id, start_iso, end_iso),
            )
            if _table_exists(conn, "daily_checkins")
            else None
        )
        average_energy = (
            _avg(
                conn,
                "SELECT AVG(energy_level) FROM daily_checkins WHERE user_id = ? AND checkin_date BETWEEN ? AND ?",
                (user_id, start_iso, end_iso),
            )
            if _table_exists(conn, "daily_checkins")
            else None
        )
        average_soreness = (
            _avg(
                conn,
                "SELECT AVG(soreness_level) FROM daily_checkins WHERE user_id = ? AND checkin_date BETWEEN ? AND ?",
                (user_id, start_iso, end_iso),
            )
            if _table_exists(conn, "daily_checkins")
            else None
        )
        nutrition_days = (
            _count(
                conn,
                "SELECT COUNT(DISTINCT entry_date) FROM food_entries WHERE user_id = ? AND entry_date BETWEEN ? AND ?",
                (user_id, start_iso, end_iso),
            )
            if _table_exists(conn, "food_entries")
            else 0
        )
        nutrition_entries = (
            _count(
                conn,
                "SELECT COUNT(*) FROM food_entries WHERE user_id = ? AND entry_date BETWEEN ? AND ?",
                (user_id, start_iso, end_iso),
            )
            if _table_exists(conn, "food_entries")
            else 0
        )
        completed_workouts = (
            _count(
                conn,
                "SELECT COUNT(*) FROM workout_sessions WHERE user_id = ? AND workout_date BETWEEN ? AND ?",
                (user_id, start_iso, end_iso),
            )
            if _table_exists(conn, "workout_sessions")
            else 0
        )
        actual_sets = 0
        skipped_sets = 0
        if _table_exists(conn, "workout_execution_set_actuals") and _table_exists(
            conn, "workout_sessions"
        ):
            actual_sets = _count(
                conn,
                """
                SELECT COUNT(*)
                FROM workout_execution_set_actuals actuals
                JOIN workout_sessions sessions
                  ON sessions.id = actuals.workout_session_id
                WHERE sessions.user_id = ?
                  AND sessions.workout_date BETWEEN ? AND ?
                  AND COALESCE(actuals.completed, 0) = 1
                """,
                (user_id, start_iso, end_iso),
            )
            skipped_sets = _count(
                conn,
                """
                SELECT COUNT(*)
                FROM workout_execution_set_actuals actuals
                JOIN workout_sessions sessions
                  ON sessions.id = actuals.workout_session_id
                WHERE sessions.user_id = ?
                  AND sessions.workout_date BETWEEN ? AND ?
                  AND COALESCE(actuals.skipped, 0) = 1
                """,
                (user_id, start_iso, end_iso),
            )
        planned_workouts = 0
        if _table_exists(conn, "workout_plan_instances"):
            planned_date_column = (
                "selected_at"
                if _has_column(conn, "workout_plan_instances", "selected_at")
                else "created_at"
            )
            planned_workouts = _count(
                conn,
                f"""
                SELECT COUNT(*)
                FROM workout_plan_instances
                WHERE user_id = ?
                  AND date({planned_date_column}) BETWEEN ? AND ?
                """,
                (user_id, start_iso, end_iso),
            )

    data_quality_label = _quality_label(
        recovery_checkins_count=recovery_count,
        nutrition_logged_days_count=nutrition_days,
        completed_workouts_count=completed_workouts,
        actual_sets_count=actual_sets,
    )
    reason_codes = _reason_codes_for_inventory(
        recovery_checkins_count=recovery_count,
        nutrition_logged_days_count=nutrition_days,
        completed_workouts_count=completed_workouts,
        actual_sets_count=actual_sets,
        data_quality_label=data_quality_label,
    )
    limitations = _limitations_for_inventory(
        recovery_checkins_count=recovery_count,
        nutrition_logged_days_count=nutrition_days,
        completed_workouts_count=completed_workouts,
        actual_sets_count=actual_sets,
        data_quality_label=data_quality_label,
    )

    return WeeklyCoachSummaryFactInventory(
        user_id=user_id,
        start_date=start_iso,
        end_date=end_iso,
        scenario=scenario,
        recovery_checkins_count=recovery_count,
        nutrition_logged_days_count=nutrition_days,
        nutrition_entries_count=nutrition_entries,
        completed_workouts_count=completed_workouts,
        actual_sets_count=actual_sets,
        planned_workouts_count=planned_workouts,
        skipped_sets_count=skipped_sets,
        average_sleep_hours=average_sleep,
        average_energy_level=average_energy,
        average_soreness_level=average_soreness,
        data_quality_label=data_quality_label,
        reason_codes=reason_codes,
        limitations=limitations,
    )


def build_weekly_summary_context_from_qa_range(
    *,
    user_id: int,
    start_date: date | str,
    end_date: date | str,
    connection: sqlite3.Connection | None = None,
) -> WeeklyCoachSummaryContext:
    """Map sanitized live QA fact counts into the deterministic summary context."""

    inventory = get_weekly_summary_fact_inventory(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        connection=connection,
    )
    average_energy = (
        int(round(inventory.average_energy_level))
        if inventory.average_energy_level is not None
        else None
    )
    average_soreness = (
        int(round(inventory.average_soreness_level))
        if inventory.average_soreness_level is not None
        else None
    )
    limitations = (
        *inventory.limitations,
        f"QA data quality label: {inventory.data_quality_label}.",
        "Context is derived from sanitized aggregate QA fact counts, not raw rows.",
    )
    return build_weekly_summary_context_from_fixture(
        user_id=inventory.user_id,
        week_start=inventory.start_date,
        week_end=inventory.end_date,
        training_days_logged=inventory.completed_workouts_count,
        workouts_completed=inventory.completed_workouts_count,
        planned_workouts=inventory.planned_workouts_count,
        recovery_notes_available=inventory.recovery_checkins_count > 0,
        nutrition_days_logged=inventory.nutrition_logged_days_count,
        protein_days_logged=min(
            inventory.nutrition_logged_days_count,
            inventory.nutrition_entries_count,
        ),
        average_energy=average_energy,
        average_soreness=average_soreness,
        limitations=limitations,
    )
