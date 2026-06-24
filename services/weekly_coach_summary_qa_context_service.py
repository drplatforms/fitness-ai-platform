from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from models.weekly_coach_summary_models import (
    WeeklyCoachSummaryConfidence,
    WeeklyCoachSummaryContext,
    WeeklyCoachSummaryFactBoundary,
    WeeklyCoachSummaryPeriod,
)
from services.qa_seed_data_verification_service import (
    resolve_verification_db_path,
    validate_date_range,
)
from services.weekly_coach_summary_qa_data_service import (
    WeeklyCoachSummaryQAInventory,
    inspect_weekly_summary_qa_range,
)

SOURCE_IDENTIFIER = "qa_date_range_debug"


@dataclass(frozen=True)
class WeeklyCoachSummaryQAContextSignals:
    """Safe aggregate context signals for QA date-range weekly summaries.

    This is not a raw row container. It may carry counts, averages, labels,
    provenance, and limitations only. Raw notes, raw food logs, raw set rows,
    prompts, and provider outputs are deliberately excluded.
    """

    user_id: int
    scenario: str
    start_date: str
    end_date: str
    source: str
    data_quality_label: str
    recovery_checkins_count: int
    nutrition_entries_count: int
    nutrition_logged_days: int
    workout_sessions_count: int
    workout_execution_sessions_count: int
    completed_workout_execution_sessions: int
    actual_sets_count: int
    planned_workouts_count: int
    average_sleep_hours: float | None = None
    average_energy_level: float | None = None
    average_soreness_level: float | None = None
    average_training_rir: float | None = None
    selected_range_has_data: bool = False
    available_start_date: str | None = None
    available_end_date: str | None = None
    limitations: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _connect_readonly(db_path: str | Path | None) -> sqlite3.Connection | None:
    resolved = resolve_verification_db_path(db_path)
    if not resolved.exists():
        return None
    connection = sqlite3.connect(f"file:{resolved}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return {str(row["name"]) for row in rows}


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row["name"]) for row in rows}


def _has_columns(
    all_columns: dict[str, set[str]], table: str, required: set[str]
) -> bool:
    return required.issubset(all_columns.get(table, set()))


def _query_one(
    connection: sqlite3.Connection, sql: str, parameters: tuple[Any, ...]
) -> sqlite3.Row | None:
    try:
        return connection.execute(sql, parameters).fetchone()
    except sqlite3.Error:
        return None


def _rounded_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None


def _recovery_aggregates(
    connection: sqlite3.Connection | None,
    *,
    user_id: int,
    start_date: str,
    end_date: str,
) -> dict[str, float | None]:
    if connection is None:
        return {
            "average_sleep_hours": None,
            "average_energy_level": None,
            "average_soreness_level": None,
        }
    tables = _table_names(connection)
    if "daily_checkins" not in tables:
        return {
            "average_sleep_hours": None,
            "average_energy_level": None,
            "average_soreness_level": None,
        }
    columns = {"daily_checkins": _table_columns(connection, "daily_checkins")}
    required = {"user_id", "checkin_date"}
    if not _has_columns(columns, "daily_checkins", required):
        return {
            "average_sleep_hours": None,
            "average_energy_level": None,
            "average_soreness_level": None,
        }

    select_parts = []
    for column, alias in (
        ("sleep_hours", "average_sleep_hours"),
        ("energy_level", "average_energy_level"),
        ("soreness_level", "average_soreness_level"),
    ):
        if column in columns["daily_checkins"]:
            select_parts.append(f"AVG({column}) AS {alias}")
        else:
            select_parts.append(f"NULL AS {alias}")

    row = _query_one(
        connection,
        f"""
        SELECT {", ".join(select_parts)}
        FROM daily_checkins
        WHERE user_id = ?
          AND date(checkin_date) BETWEEN date(?) AND date(?)
        """,
        (user_id, start_date, end_date),
    )
    if row is None:
        return {
            "average_sleep_hours": None,
            "average_energy_level": None,
            "average_soreness_level": None,
        }
    return {
        "average_sleep_hours": _rounded_float(row["average_sleep_hours"]),
        "average_energy_level": _rounded_float(row["average_energy_level"]),
        "average_soreness_level": _rounded_float(row["average_soreness_level"]),
    }


def _training_rir_aggregate(
    connection: sqlite3.Connection | None,
    *,
    user_id: int,
    start_date: str,
    end_date: str,
) -> float | None:
    if connection is None:
        return None
    tables = _table_names(connection)
    if not {"workout_sessions", "workout_sets"}.issubset(tables):
        return None
    columns = {
        "workout_sessions": _table_columns(connection, "workout_sessions"),
        "workout_sets": _table_columns(connection, "workout_sets"),
    }
    if not _has_columns(columns, "workout_sessions", {"id", "user_id", "workout_date"}):
        return None
    if not _has_columns(columns, "workout_sets", {"workout_session_id", "rir"}):
        return None

    row = _query_one(
        connection,
        """
        SELECT AVG(workout_sets.rir) AS average_training_rir
        FROM workout_sets
        JOIN workout_sessions
          ON workout_sessions.id = workout_sets.workout_session_id
        WHERE workout_sessions.user_id = ?
          AND workout_sets.rir IS NOT NULL
          AND date(workout_sessions.workout_date) BETWEEN date(?) AND date(?)
        """,
        (user_id, start_date, end_date),
    )
    if row is None:
        return None
    return _rounded_float(row["average_training_rir"])


def _count(inventory: WeeklyCoachSummaryQAInventory, domain: str) -> int:
    return int(inventory.fact_counts.get(domain, 0) or 0)


def _distinct_days(inventory: WeeklyCoachSummaryQAInventory, domain: str) -> int:
    return int(inventory.distinct_logged_days.get(domain) or 0)


def _completed_count(inventory: WeeklyCoachSummaryQAInventory, domain: str) -> int:
    return int(inventory.completed_counts.get(domain) or 0)


def _confidence_from_quality(label: str) -> WeeklyCoachSummaryConfidence:
    normalized = str(label).strip().lower()
    if normalized == "strong":
        return WeeklyCoachSummaryConfidence.HIGH
    if normalized == "usable":
        return WeeklyCoachSummaryConfidence.MODERATE
    if normalized == "limited":
        return WeeklyCoachSummaryConfidence.LIMITED
    return WeeklyCoachSummaryConfidence.LIMITED


def _recovery_summary(signals: WeeklyCoachSummaryQAContextSignals) -> str | None:
    if signals.recovery_checkins_count <= 0:
        return None
    parts = [f"Recovery coverage includes {signals.recovery_checkins_count} check-ins."]
    if signals.average_sleep_hours is not None:
        parts.append(f"Average sleep was about {signals.average_sleep_hours} hours.")
    if signals.average_energy_level is not None:
        parts.append(
            f"Average energy was about {signals.average_energy_level} out of 10."
        )
    if signals.average_soreness_level is not None:
        parts.append(
            f"Average soreness was about {signals.average_soreness_level} out of 10."
        )
    return " ".join(parts)


def _nutrition_summary(signals: WeeklyCoachSummaryQAContextSignals) -> str | None:
    if signals.nutrition_entries_count <= 0:
        return None
    return (
        f"Nutrition coverage includes {signals.nutrition_entries_count} entries "
        f"across {signals.nutrition_logged_days} logged days."
    )


def _training_summary(signals: WeeklyCoachSummaryQAContextSignals) -> str | None:
    training_sessions = max(
        signals.workout_sessions_count,
        signals.workout_execution_sessions_count,
        signals.completed_workout_execution_sessions,
    )
    if training_sessions <= 0 and signals.actual_sets_count <= 0:
        return None
    parts = [
        f"Training coverage includes {training_sessions} sessions and "
        f"{signals.actual_sets_count} actual sets."
    ]
    if signals.average_training_rir is not None:
        parts.append(f"Average logged RIR was about {signals.average_training_rir}.")
    return " ".join(parts)


def _workout_execution_summary(
    signals: WeeklyCoachSummaryQAContextSignals,
) -> str | None:
    if signals.workout_execution_sessions_count <= 0 and signals.actual_sets_count <= 0:
        return None
    return (
        f"Workout execution coverage includes "
        f"{signals.completed_workout_execution_sessions} completed execution sessions "
        f"and {signals.actual_sets_count} actual sets."
    )


def _recommendation_summary(signals: WeeklyCoachSummaryQAContextSignals) -> str:
    if signals.data_quality_label == "strong":
        return "Use the selected QA range as a strong deterministic weekly baseline."
    if signals.data_quality_label == "usable":
        return "Use the selected QA range for cautious deterministic weekly guidance."
    if signals.selected_range_has_data:
        return "Treat the selected QA range as limited and avoid strong conclusions."
    return "Selected range has insufficient data; use fallback guidance."


def _base_reason_codes(
    inventory: WeeklyCoachSummaryQAInventory,
) -> tuple[str, ...]:
    codes = [
        "qa_date_range_context_built",
        "qa_date_range_debug_source",
        "approved_backend_facts_only",
        "provider_free_context",
        f"data_quality_{inventory.data_quality_label}",
        *inventory.diagnosis_codes,
    ]
    if inventory.selected_range_has_data:
        codes.append("selected_range_has_data")
    else:
        codes.append("selected_range_insufficient_data")
    return tuple(dict.fromkeys(codes))


def _base_limitations(
    inventory: WeeklyCoachSummaryQAInventory,
) -> tuple[str, ...]:
    limitations = list(inventory.limitations)
    limitations.append(
        "QA selected-range context uses safe aggregate facts only; raw rows, notes, "
        "logs, prompts, and provider output are excluded."
    )
    limitations.append(
        f"Context source: {SOURCE_IDENTIFIER}; data quality: "
        f"{inventory.data_quality_label}."
    )
    if (
        not inventory.selected_range_has_data
        and inventory.available_start_date
        and inventory.available_end_date
    ):
        limitations.append(
            "Selected range has no data for this user. Available data exists from "
            f"{inventory.available_start_date} to {inventory.available_end_date}."
        )
    return tuple(dict.fromkeys(limitations))


def build_weekly_summary_qa_context_signals(
    inventory: WeeklyCoachSummaryQAInventory,
    *,
    db_path: str | Path | None = None,
) -> WeeklyCoachSummaryQAContextSignals:
    """Build safe aggregate signals from selected-range QA inventory."""

    connection = _connect_readonly(db_path)
    try:
        recovery = _recovery_aggregates(
            connection,
            user_id=inventory.user_id,
            start_date=inventory.start_date,
            end_date=inventory.end_date,
        )
        average_rir = _training_rir_aggregate(
            connection,
            user_id=inventory.user_id,
            start_date=inventory.start_date,
            end_date=inventory.end_date,
        )
    finally:
        if connection is not None:
            connection.close()

    return WeeklyCoachSummaryQAContextSignals(
        user_id=inventory.user_id,
        scenario=inventory.scenario,
        start_date=inventory.start_date,
        end_date=inventory.end_date,
        source=SOURCE_IDENTIFIER,
        data_quality_label=inventory.data_quality_label,
        recovery_checkins_count=_count(inventory, "recovery"),
        nutrition_entries_count=_count(inventory, "nutrition"),
        nutrition_logged_days=_distinct_days(inventory, "nutrition"),
        workout_sessions_count=_count(inventory, "workout_sessions"),
        workout_execution_sessions_count=_count(
            inventory, "workout_execution_sessions"
        ),
        completed_workout_execution_sessions=_completed_count(
            inventory, "workout_execution_sessions"
        ),
        actual_sets_count=_count(inventory, "actual_sets"),
        planned_workouts_count=_count(inventory, "planned_workouts"),
        average_sleep_hours=recovery["average_sleep_hours"],
        average_energy_level=recovery["average_energy_level"],
        average_soreness_level=recovery["average_soreness_level"],
        average_training_rir=average_rir,
        selected_range_has_data=inventory.selected_range_has_data,
        available_start_date=inventory.available_start_date,
        available_end_date=inventory.available_end_date,
        limitations=_base_limitations(inventory),
        reason_codes=_base_reason_codes(inventory),
    )


def build_weekly_summary_context_from_qa_inventory(
    inventory: WeeklyCoachSummaryQAInventory,
    *,
    db_path: str | Path | None = None,
) -> WeeklyCoachSummaryContext:
    """Convert selected-range QA inventory into bounded weekly context."""

    signals = build_weekly_summary_qa_context_signals(inventory, db_path=db_path)
    confidence = _confidence_from_quality(signals.data_quality_label)
    fact_boundary = WeeklyCoachSummaryFactBoundary(
        recovery_facts_available=signals.recovery_checkins_count > 0,
        nutrition_facts_available=signals.nutrition_entries_count > 0,
        training_facts_available=(
            signals.workout_sessions_count > 0
            or signals.workout_execution_sessions_count > 0
            or signals.actual_sets_count > 0
        ),
        workout_execution_facts_available=(
            signals.workout_execution_sessions_count > 0
            or signals.actual_sets_count > 0
        ),
        daily_recommendation_facts_available=False,
        profile_context_available=False,
        data_quality_limited=signals.data_quality_label in {"limited", "insufficient"},
        limitations=signals.limitations,
    )
    return WeeklyCoachSummaryContext(
        user_id=signals.user_id,
        period=WeeklyCoachSummaryPeriod(
            user_id=signals.user_id,
            week_start=signals.start_date,
            week_end=signals.end_date,
            generated_for_date=signals.end_date,
        ),
        fact_boundary=fact_boundary,
        confidence=confidence,
        scenario=signals.scenario,
        recovery_summary=_recovery_summary(signals),
        nutrition_summary=_nutrition_summary(signals),
        training_summary=_training_summary(signals),
        workout_execution_summary=_workout_execution_summary(signals),
        recommendation_summary=_recommendation_summary(signals),
        limitations=signals.limitations,
        reason_codes=signals.reason_codes,
    )


def build_weekly_summary_context_from_qa_range(
    *,
    user_id: int,
    start_date: date | str,
    end_date: date | str,
    db_path: str | Path | None = None,
) -> WeeklyCoachSummaryContext:
    """Build deterministic WeeklyCoachSummaryContext from selected QA range."""

    selected_start, selected_end = validate_date_range(str(start_date), str(end_date))
    inventory = inspect_weekly_summary_qa_range(
        user_id=int(user_id),
        start_date=selected_start,
        end_date=selected_end,
        db_path=db_path,
    )
    return build_weekly_summary_context_from_qa_inventory(
        inventory,
        db_path=db_path,
    )


def weekly_summary_context_to_safe_metadata(
    context: WeeklyCoachSummaryContext,
) -> dict[str, Any]:
    """Return sanitized context metadata for Developer Mode display/debug."""

    return {
        "user_id": context.user_id,
        "scenario": context.scenario,
        "start_date": context.period.week_start.isoformat(),
        "end_date": context.period.week_end.isoformat(),
        "source": SOURCE_IDENTIFIER,
        "confidence": context.confidence.value,
        "data_quality_limited": context.fact_boundary.data_quality_limited,
        "recovery_facts_available": context.fact_boundary.recovery_facts_available,
        "nutrition_facts_available": context.fact_boundary.nutrition_facts_available,
        "training_facts_available": context.fact_boundary.training_facts_available,
        "workout_execution_facts_available": (
            context.fact_boundary.workout_execution_facts_available
        ),
        "provider_attempted": False,
        "deterministic_provider_free": True,
        "reason_codes": context.reason_codes,
        "limitations": context.limitations,
    }
