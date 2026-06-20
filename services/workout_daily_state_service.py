from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from database import get_connection
from services.workout_plan_persistence_service import (
    ensure_workout_plan_persistence_tables,
    get_execution_state,
)

UNCOMPLETED_CURRENT_STATUSES = {"selected", "started", "in_progress"}
ACTIVE_STATUSES = {"started", "in_progress"}
CURRENT_PLAN_STATES = {"selected_today", "active_today", "completed_today"}

STALE_WORKOUT_RESET_MESSAGE = "An unfinished workout from a previous day was cleared so you can start fresh today."


@dataclass
class WorkoutDailyState:
    user_id: int
    target_date: str
    state: str
    selected_plan_id: int | None = None
    selected_plan_date: str | None = None
    active_plan_id: int | None = None
    active_plan_date: str | None = None
    completed_workout_id: int | None = None
    completed_plan_date: str | None = None
    expired_plan_id: int | None = None
    expired_plan_date: str | None = None
    stale_state_detected: bool = False
    substitution_state_should_clear: bool = False
    user_safe_message: str | None = None
    developer_metadata: dict[str, Any] = field(default_factory=dict)


def _date_to_string(value: date | datetime | str | None) -> str:
    if value is None:
        return date.today().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)[:10]


def _parse_row_date(*values: str | None) -> date | None:
    for value in values:
        if not value:
            continue
        raw_value = str(value).strip()
        if not raw_value:
            continue
        try:
            return datetime.fromisoformat(raw_value.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                return datetime.strptime(raw_value[:10], "%Y-%m-%d").date()
            except ValueError:
                continue
    return None


def _target_date_object(target_date: date | datetime | str | None) -> date:
    if target_date is None:
        return date.today()
    if isinstance(target_date, datetime):
        return target_date.date()
    if isinstance(target_date, date):
        return target_date
    return datetime.strptime(str(target_date)[:10], "%Y-%m-%d").date()


def _fetch_plan_rows(user_id: int) -> list[dict[str, Any]]:
    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT
                instance.*,
                execution.id AS execution_id,
                execution.status AS execution_status,
                execution.workout_session_id AS execution_workout_session_id,
                execution.started_at AS execution_started_at,
                execution.completed_at AS execution_completed_at,
                execution.abandoned_at AS execution_abandoned_at,
                execution.created_at AS execution_created_at,
                execution.updated_at AS execution_updated_at
            FROM workout_plan_instances AS instance
            LEFT JOIN workout_execution_sessions AS execution
                ON execution.workout_plan_instance_id = instance.id
            WHERE instance.user_id = ?
            ORDER BY instance.created_at DESC, instance.id DESC
            """,
            (user_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def _plan_local_date(row: dict[str, Any]) -> date | None:
    status = str(row.get("status") or "")
    execution_status = str(row.get("execution_status") or "")

    if status == "completed" or execution_status == "completed":
        return _parse_row_date(
            row.get("completed_at"),
            row.get("execution_completed_at"),
            row.get("selected_at"),
            row.get("created_at"),
        )

    if status in ACTIVE_STATUSES or execution_status in ACTIVE_STATUSES:
        return _parse_row_date(
            row.get("execution_started_at"),
            row.get("selected_at"),
            row.get("created_at"),
        )

    return _parse_row_date(row.get("selected_at"), row.get("created_at"))


def _row_has_active_substitutions(plan_instance_id: int) -> bool:
    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*) AS substitution_count
            FROM workout_plan_exercise_substitutions
            WHERE workout_plan_instance_id = ?
                AND status = ?
            """,
            (plan_instance_id, "active"),
        )
        row = cursor.fetchone()
        return bool(row and int(row["substitution_count"]) > 0)
    finally:
        conn.close()


def resolve_workout_daily_state(
    user_id: int,
    target_date: date | datetime | str | None = None,
) -> WorkoutDailyState:
    """Resolve the user's safe current-day workout lifecycle state.

    This service is intentionally read-only. It does not delete completed history,
    mutate selected plans, or change workout generation behavior. Prior-date
    uncompleted selected/active plans are treated as expired for today's UI.
    """

    target = _target_date_object(target_date)
    target_date_text = target.isoformat()
    rows = _fetch_plan_rows(user_id)

    completed_today: dict[str, Any] | None = None
    active_today: dict[str, Any] | None = None
    selected_today: dict[str, Any] | None = None
    expired_prior: dict[str, Any] | None = None
    expired_prior_date: date | None = None

    for row in rows:
        status = str(row.get("status") or "")
        execution_status = str(row.get("execution_status") or "")
        plan_date = _plan_local_date(row)

        if plan_date is None:
            continue

        if plan_date == target and (
            status == "completed" or execution_status == "completed"
        ):
            completed_today = row
            break

        if plan_date == target and (
            status in ACTIVE_STATUSES or execution_status in ACTIVE_STATUSES
        ):
            if active_today is None:
                active_today = row
            continue

        if plan_date == target and status == "selected":
            if selected_today is None:
                selected_today = row
            continue

        if plan_date < target and (
            status in UNCOMPLETED_CURRENT_STATUSES
            or execution_status in UNCOMPLETED_CURRENT_STATUSES
        ):
            if expired_prior is None:
                expired_prior = row
                expired_prior_date = plan_date
            continue

    if completed_today is not None:
        completed_date = _plan_local_date(completed_today)
        return WorkoutDailyState(
            user_id=user_id,
            target_date=target_date_text,
            state="completed_today",
            completed_workout_id=int(completed_today["id"]),
            completed_plan_date=_date_to_string(completed_date),
            developer_metadata={
                "completed_workout_detected": True,
                "completed_plan_status": completed_today.get("status"),
                "completed_execution_status": completed_today.get("execution_status"),
            },
        )

    if active_today is not None:
        active_date = _plan_local_date(active_today)
        return WorkoutDailyState(
            user_id=user_id,
            target_date=target_date_text,
            state="active_today",
            active_plan_id=int(active_today["id"]),
            active_plan_date=_date_to_string(active_date),
            developer_metadata={
                "active_workout_detected": True,
                "active_plan_status": active_today.get("status"),
                "active_execution_status": active_today.get("execution_status"),
            },
        )

    if selected_today is not None:
        selected_date = _plan_local_date(selected_today)
        return WorkoutDailyState(
            user_id=user_id,
            target_date=target_date_text,
            state="selected_today",
            selected_plan_id=int(selected_today["id"]),
            selected_plan_date=_date_to_string(selected_date),
            developer_metadata={
                "selected_workout_detected": True,
                "selected_plan_status": selected_today.get("status"),
                "selected_execution_status": selected_today.get("execution_status"),
            },
        )

    if expired_prior is not None:
        expired_plan_id = int(expired_prior["id"])
        return WorkoutDailyState(
            user_id=user_id,
            target_date=target_date_text,
            state="expired_uncompleted_prior",
            expired_plan_id=expired_plan_id,
            expired_plan_date=_date_to_string(expired_prior_date),
            stale_state_detected=True,
            substitution_state_should_clear=_row_has_active_substitutions(
                expired_plan_id
            ),
            user_safe_message=STALE_WORKOUT_RESET_MESSAGE,
            developer_metadata={
                "expired_prior_uncompleted_state": True,
                "expired_plan_status": expired_prior.get("status"),
                "expired_execution_status": expired_prior.get("execution_status"),
                "completed_workout_detected": False,
            },
        )

    return WorkoutDailyState(
        user_id=user_id,
        target_date=target_date_text,
        state="no_workout_today",
        developer_metadata={
            "completed_workout_detected": False,
            "selected_workout_detected": False,
            "active_workout_detected": False,
            "expired_prior_uncompleted_state": False,
        },
    )


def get_current_day_execution_state(
    user_id: int,
    target_date: date | datetime | str | None = None,
) -> dict | None:
    """Return today's selected/active/completed execution state, never stale prior state."""

    state = resolve_workout_daily_state(user_id, target_date=target_date)
    plan_id = (
        state.selected_plan_id or state.active_plan_id or state.completed_workout_id
    )
    if state.state not in CURRENT_PLAN_STATES or plan_id is None:
        return None

    try:
        return get_execution_state(plan_id)
    except Exception:
        return None


def clear_stale_workout_session_state_if_needed(
    session_state: MutableMapping[str, Any],
    daily_state: WorkoutDailyState,
) -> bool:
    """Clear Streamlit/session transient workout state when prior state expired."""

    if not daily_state.stale_state_detected:
        return False

    session_state["selected_workout_plan_response"] = None
    session_state["started_workout_plan_response"] = None
    session_state["completed_workout_plan_response"] = None
    session_state["visible_substitution_candidates"] = []
    session_state["applied_substitution_responses"] = {}
    session_state["substitution_apply_message"] = None
    session_state["substitution_apply_error"] = None
    session_state["substitution_apply_error_detail"] = None
    session_state["substitution_flow_ready_to_do_workout"] = False
    session_state["actual_set_logging_message"] = None
    session_state["actual_set_editing_message"] = None
    session_state["actual_set_editing_error"] = None
    session_state["actual_set_edit_response"] = None
    return True
