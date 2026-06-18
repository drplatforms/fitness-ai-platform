from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any

from database import get_connection
from models.workout_plan_models import (
    ApprovedWorkoutExercise,
    ApprovedWorkoutPlan,
    PlannedWorkoutExercise,
    WorkoutExecutionSession,
    WorkoutExecutionSetActual,
    WorkoutPlanExerciseSubstitution,
    WorkoutPlanInstance,
    WorkoutPlannedVsActualSummary,
)
from services.user_state_service import build_user_health_state
from services.workout_plan_service import build_approved_workout_plan

WORKOUT_PLAN_STATUSES = {
    "selected",
    "started",
    "in_progress",
    "completed",
    "abandoned",
    "cancelled",
}

WORKOUT_PLAN_SUBSTITUTION_STATUSES = {
    "active",
    "replaced",
    "cancelled",
}

WORKOUT_PLAN_SUBSTITUTION_ALLOWED_PLAN_STATUSES = {
    "selected",
    "started",
    "in_progress",
}


class WorkoutPlanPersistenceError(Exception):
    """Base error for workout plan persistence workflows."""


class WorkoutPlanNotFoundError(WorkoutPlanPersistenceError):
    """Raised when a workout plan instance cannot be found."""


class WorkoutPlanInvalidStatusError(WorkoutPlanPersistenceError):
    """Raised when a workout plan instance cannot transition as requested."""


class WorkoutPlanValidationError(WorkoutPlanPersistenceError):
    """Raised when execution logging payloads are invalid."""


def _encode_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _decode_json(raw_value: str | None, default: Any) -> Any:
    if raw_value is None:
        return default

    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def ensure_workout_plan_persistence_tables() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_plan_instances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        scenario TEXT NOT NULL,
        confidence TEXT NOT NULL,
        title TEXT NOT NULL,
        approved_workout_plan_json TEXT NOT NULL,
        selected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT,
        abandoned_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planned_workout_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_plan_instance_id INTEGER NOT NULL,
        exercise_order INTEGER NOT NULL,
        name TEXT NOT NULL,
        sets INTEGER NOT NULL,
        reps_min INTEGER NOT NULL,
        reps_max INTEGER NOT NULL,
        rir_min INTEGER NOT NULL,
        rir_max INTEGER NOT NULL,
        notes TEXT NOT NULL,
        equipment_required_json TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (workout_plan_instance_id)
            REFERENCES workout_plan_instances(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_execution_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_plan_instance_id INTEGER NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        workout_session_id INTEGER,
        started_at TEXT,
        completed_at TEXT,
        abandoned_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (workout_plan_instance_id)
            REFERENCES workout_plan_instances(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (workout_session_id)
            REFERENCES workout_sessions(id)
    )
    """)

    cursor.execute("PRAGMA table_info(workout_plan_instances)")
    workout_plan_columns = {row["name"] for row in cursor.fetchall()}
    if "completed_at" not in workout_plan_columns:
        cursor.execute(
            "ALTER TABLE workout_plan_instances ADD COLUMN completed_at TEXT"
        )
    if "abandoned_at" not in workout_plan_columns:
        cursor.execute(
            "ALTER TABLE workout_plan_instances ADD COLUMN abandoned_at TEXT"
        )

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_execution_set_actuals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_execution_session_id INTEGER NOT NULL,
        planned_workout_exercise_id INTEGER,
        workout_session_id INTEGER,
        workout_set_id INTEGER,
        exercise_name TEXT NOT NULL,
        set_number INTEGER NOT NULL,
        planned_reps_min INTEGER,
        planned_reps_max INTEGER,
        planned_rir_min INTEGER,
        planned_rir_max INTEGER,
        actual_reps INTEGER,
        actual_weight REAL,
        actual_rir INTEGER,
        completed INTEGER NOT NULL DEFAULT 0,
        skipped INTEGER NOT NULL DEFAULT 0,
        substitution_for_planned_exercise_id INTEGER,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (workout_execution_session_id)
            REFERENCES workout_execution_sessions(id),
        FOREIGN KEY (planned_workout_exercise_id)
            REFERENCES planned_workout_exercises(id),
        FOREIGN KEY (workout_session_id)
            REFERENCES workout_sessions(id),
        FOREIGN KEY (workout_set_id)
            REFERENCES workout_sets(id),
        FOREIGN KEY (substitution_for_planned_exercise_id)
            REFERENCES planned_workout_exercises(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_plan_exercise_substitutions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_plan_instance_id INTEGER NOT NULL,
        workout_execution_session_id INTEGER,
        planned_workout_exercise_id INTEGER NOT NULL,
        original_exercise_name TEXT NOT NULL,
        replacement_exercise_name TEXT NOT NULL,
        replacement_catalog_exercise_id INTEGER NOT NULL,
        original_movement_pattern TEXT NOT NULL,
        replacement_movement_pattern TEXT NOT NULL,
        substitution_reason TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (workout_plan_instance_id)
            REFERENCES workout_plan_instances(id),
        FOREIGN KEY (workout_execution_session_id)
            REFERENCES workout_execution_sessions(id),
        FOREIGN KEY (planned_workout_exercise_id)
            REFERENCES planned_workout_exercises(id),
        FOREIGN KEY (replacement_catalog_exercise_id)
            REFERENCES exercise_catalog_exercises(id)
    )
    """)

    conn.commit()
    conn.close()


def _approved_workout_plan_from_dict(raw_plan: dict) -> ApprovedWorkoutPlan:
    exercises = [
        ApprovedWorkoutExercise(
            name=str(exercise["name"]),
            sets=int(exercise["sets"]),
            reps_min=int(exercise["reps_min"]),
            reps_max=int(exercise["reps_max"]),
            rir_min=int(exercise["rir_min"]),
            rir_max=int(exercise["rir_max"]),
            notes=str(exercise["notes"]),
            equipment_required=[
                str(equipment) for equipment in exercise.get("equipment_required", [])
            ],
        )
        for exercise in raw_plan.get("exercises", [])
    ]

    return ApprovedWorkoutPlan(
        title=str(raw_plan["title"]),
        session_focus=str(raw_plan["session_focus"]),
        duration_minutes=int(raw_plan["duration_minutes"]),
        exercises=exercises,
        warmup=str(raw_plan["warmup"]),
        cooldown=str(raw_plan["cooldown"]),
        progression_guidance=str(raw_plan["progression_guidance"]),
        rationale=str(raw_plan["rationale"]),
        confidence=str(raw_plan["confidence"]),
        scenario=str(raw_plan["scenario"]),
        reason_codes=[str(code) for code in raw_plan.get("reason_codes", [])],
    )


def _row_value(row, key: str, default=None):
    try:
        if key in row.keys():
            return row[key]
    except AttributeError:
        pass
    return default


def _row_to_workout_plan_instance(row) -> WorkoutPlanInstance:
    approved_workout_plan = _approved_workout_plan_from_dict(
        _decode_json(row["approved_workout_plan_json"], {})
    )

    return WorkoutPlanInstance(
        id=row["id"],
        user_id=row["user_id"],
        status=row["status"],
        scenario=row["scenario"],
        confidence=row["confidence"],
        title=row["title"],
        approved_workout_plan=approved_workout_plan,
        selected_at=row["selected_at"],
        completed_at=_row_value(row, "completed_at"),
        abandoned_at=_row_value(row, "abandoned_at"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_planned_exercise(row) -> PlannedWorkoutExercise:
    return PlannedWorkoutExercise(
        id=row["id"],
        workout_plan_instance_id=row["workout_plan_instance_id"],
        exercise_order=row["exercise_order"],
        name=row["name"],
        sets=row["sets"],
        reps_min=row["reps_min"],
        reps_max=row["reps_max"],
        rir_min=row["rir_min"],
        rir_max=row["rir_max"],
        notes=row["notes"],
        equipment_required=[
            str(equipment)
            for equipment in _decode_json(row["equipment_required_json"], [])
        ],
    )


def _row_to_execution_session(row) -> WorkoutExecutionSession:
    return WorkoutExecutionSession(
        id=row["id"],
        workout_plan_instance_id=row["workout_plan_instance_id"],
        user_id=row["user_id"],
        status=row["status"],
        workout_session_id=row["workout_session_id"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        abandoned_at=row["abandoned_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_actual_set(row) -> WorkoutExecutionSetActual:
    return WorkoutExecutionSetActual(
        id=row["id"],
        workout_execution_session_id=row["workout_execution_session_id"],
        planned_workout_exercise_id=row["planned_workout_exercise_id"],
        workout_session_id=row["workout_session_id"],
        workout_set_id=row["workout_set_id"],
        exercise_name=row["exercise_name"],
        set_number=row["set_number"],
        planned_reps_min=row["planned_reps_min"],
        planned_reps_max=row["planned_reps_max"],
        planned_rir_min=row["planned_rir_min"],
        planned_rir_max=row["planned_rir_max"],
        actual_reps=row["actual_reps"],
        actual_weight=row["actual_weight"],
        actual_rir=row["actual_rir"],
        completed=bool(row["completed"]),
        skipped=bool(row["skipped"]),
        substitution_for_planned_exercise_id=row[
            "substitution_for_planned_exercise_id"
        ],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_substitution(row) -> WorkoutPlanExerciseSubstitution:
    return WorkoutPlanExerciseSubstitution(
        id=row["id"],
        workout_plan_instance_id=row["workout_plan_instance_id"],
        workout_execution_session_id=row["workout_execution_session_id"],
        planned_workout_exercise_id=row["planned_workout_exercise_id"],
        original_exercise_name=row["original_exercise_name"],
        replacement_exercise_name=row["replacement_exercise_name"],
        replacement_catalog_exercise_id=row["replacement_catalog_exercise_id"],
        original_movement_pattern=row["original_movement_pattern"],
        replacement_movement_pattern=row["replacement_movement_pattern"],
        substitution_reason=row["substitution_reason"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _planned_exercises_by_id(
    planned_exercises: list[PlannedWorkoutExercise],
) -> dict[int, PlannedWorkoutExercise]:
    return {exercise.id: exercise for exercise in planned_exercises}


def _validate_non_negative_int(value: int | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise WorkoutPlanValidationError(f"{field_name} must be non-negative.")


def _validate_non_negative_float(value: float | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise WorkoutPlanValidationError(f"{field_name} must be non-negative.")


def _validate_actual_rir(value: int | None) -> None:
    if value is not None and not 0 <= value <= 10:
        raise WorkoutPlanValidationError("actual_rir must be between 0 and 10.")


def get_planned_workout_exercises(
    workout_plan_instance_id: int,
) -> list[PlannedWorkoutExercise]:
    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM planned_workout_exercises
        WHERE workout_plan_instance_id = ?
        ORDER BY exercise_order
        """,
        (workout_plan_instance_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [_row_to_planned_exercise(row) for row in rows]


def get_workout_execution_session(
    workout_plan_instance_id: int,
) -> WorkoutExecutionSession | None:
    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM workout_execution_sessions
        WHERE workout_plan_instance_id = ?
        """,
        (workout_plan_instance_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return _row_to_execution_session(row)


def get_workout_execution_session_by_id(
    execution_session_id: int,
) -> WorkoutExecutionSession | None:
    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM workout_execution_sessions
        WHERE id = ?
        """,
        (execution_session_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return _row_to_execution_session(row)


def get_workout_plan_instance(
    workout_plan_instance_id: int,
) -> WorkoutPlanInstance | None:
    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM workout_plan_instances
        WHERE id = ?
        """,
        (workout_plan_instance_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return _row_to_workout_plan_instance(row)


def count_workout_plan_instances(user_id: int) -> int:
    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS instance_count
        FROM workout_plan_instances
        WHERE user_id = ?
        """,
        (user_id,),
    )

    count = cursor.fetchone()["instance_count"]
    conn.close()

    return int(count)


def get_workout_plan_history(user_id: int) -> list[dict]:
    """Return recent workout plan execution history for a user.

    The history endpoint is read-only. It does not mutate plan state, persist
    planned-vs-actual summaries, or interact with manual workout logging.
    Summaries are dynamically recomputed only for in-progress and completed
    planned workouts.
    """

    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM workout_plan_instances
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (user_id,),
    )
    instance_rows = cursor.fetchall()
    conn.close()

    history_items: list[dict] = []
    for instance_row in instance_rows:
        instance = _row_to_workout_plan_instance(instance_row)
        execution_session = get_workout_execution_session(instance.id)
        summary = None

        if instance.status in {"in_progress", "completed"}:
            try:
                summary = build_planned_vs_actual_summary(instance.id)
            except WorkoutPlanPersistenceError:
                summary = None

        history_items.append(
            {
                "workout_plan_instance": instance,
                "execution_session": execution_session,
                "approved_workout_title": instance.approved_workout_plan.title,
                "approved_workout_session_focus": (
                    instance.approved_workout_plan.session_focus
                ),
                "planned_vs_actual_summary": summary,
            }
        )

    return history_items


def get_actual_sets(
    plan_instance_id: int | None = None,
    execution_session_id: int | None = None,
) -> list[WorkoutExecutionSetActual]:
    if plan_instance_id is None and execution_session_id is None:
        raise WorkoutPlanValidationError(
            "plan_instance_id or execution_session_id is required."
        )

    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    if execution_session_id is not None:
        cursor.execute(
            """
            SELECT *
            FROM workout_execution_set_actuals
            WHERE workout_execution_session_id = ?
            ORDER BY id
            """,
            (execution_session_id,),
        )
    else:
        cursor.execute(
            """
            SELECT actuals.*
            FROM workout_execution_set_actuals AS actuals
            JOIN workout_execution_sessions AS execution
                ON actuals.workout_execution_session_id = execution.id
            WHERE execution.workout_plan_instance_id = ?
            ORDER BY actuals.id
            """,
            (plan_instance_id,),
        )

    rows = cursor.fetchall()
    conn.close()

    return [_row_to_actual_set(row) for row in rows]


def _catalog_entry_by_id(catalog_exercise_id: int):
    from services.exercise_catalog_service import get_exercise_catalog

    for entry in get_exercise_catalog():
        if entry.id == catalog_exercise_id:
            return entry

    raise WorkoutPlanValidationError(
        "replacement_catalog_exercise_id must reference an exercise catalog entry."
    )


def _catalog_entry_by_name(exercise_name: str):
    from services.exercise_catalog_service import find_catalog_entry_by_name

    return find_catalog_entry_by_name(exercise_name)


def _get_plan_row_or_raise(cursor, plan_instance_id: int):
    cursor.execute(
        """
        SELECT *
        FROM workout_plan_instances
        WHERE id = ?
        """,
        (plan_instance_id,),
    )
    instance_row = cursor.fetchone()

    if instance_row is None:
        raise WorkoutPlanNotFoundError(
            f"Workout plan instance {plan_instance_id} was not found."
        )

    return instance_row


def _get_planned_exercise_row_or_raise(
    cursor,
    plan_instance_id: int,
    planned_exercise_id: int,
):
    cursor.execute(
        """
        SELECT *
        FROM planned_workout_exercises
        WHERE id = ?
            AND workout_plan_instance_id = ?
        """,
        (planned_exercise_id, plan_instance_id),
    )
    planned_exercise_row = cursor.fetchone()

    if planned_exercise_row is None:
        raise WorkoutPlanValidationError(
            "planned_workout_exercise_id must belong to the plan instance."
        )

    return planned_exercise_row


def _get_execution_row_for_substitution(cursor, plan_instance_id: int):
    cursor.execute(
        """
        SELECT *
        FROM workout_execution_sessions
        WHERE workout_plan_instance_id = ?
        """,
        (plan_instance_id,),
    )
    execution_row = cursor.fetchone()

    if execution_row is None:
        raise WorkoutPlanInvalidStatusError(
            f"Workout plan instance {plan_instance_id} has no execution session."
        )

    return execution_row


def create_substitution_record(
    plan_instance_id: int,
    planned_exercise_id: int,
    replacement_catalog_exercise_id: int,
    substitution_reason: str = "user_selected",
    status: str = "active",
) -> WorkoutPlanExerciseSubstitution:
    """Create a durable substitution record without mutating the plan.

    This helper is the schema foundation for future apply-substitution behavior.
    It records a candidate replacement beside the immutable approved workout
    snapshot and original planned exercise row. It does not change planned
    exercises, approved workout JSON, actual-set rows, planned-vs-actual
    summaries, recommendations, or reports.
    """

    if status not in WORKOUT_PLAN_SUBSTITUTION_STATUSES:
        raise WorkoutPlanValidationError(
            "status must be one of: "
            f"{', '.join(sorted(WORKOUT_PLAN_SUBSTITUTION_STATUSES))}."
        )

    replacement_entry = _catalog_entry_by_id(int(replacement_catalog_exercise_id))

    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        instance_row = _get_plan_row_or_raise(cursor, plan_instance_id)
        if (
            instance_row["status"]
            not in WORKOUT_PLAN_SUBSTITUTION_ALLOWED_PLAN_STATUSES
        ):
            raise WorkoutPlanInvalidStatusError(
                "Substitution records can only be created for selected, started, "
                "or in-progress workout plans. "
                f"Plan {plan_instance_id} is currently {instance_row['status']}."
            )

        planned_exercise_row = _get_planned_exercise_row_or_raise(
            cursor,
            plan_instance_id,
            planned_exercise_id,
        )
        execution_row = _get_execution_row_for_substitution(cursor, plan_instance_id)

        original_entry = _catalog_entry_by_name(planned_exercise_row["name"])
        original_movement_pattern = (
            original_entry.movement_pattern if original_entry is not None else "unknown"
        )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if status == "active":
            cursor.execute(
                """
                UPDATE workout_plan_exercise_substitutions
                SET status = ?, updated_at = ?
                WHERE workout_plan_instance_id = ?
                    AND planned_workout_exercise_id = ?
                    AND status = ?
                """,
                (
                    "replaced",
                    now,
                    plan_instance_id,
                    planned_exercise_id,
                    "active",
                ),
            )

        cursor.execute(
            """
            INSERT INTO workout_plan_exercise_substitutions (
                workout_plan_instance_id,
                workout_execution_session_id,
                planned_workout_exercise_id,
                original_exercise_name,
                replacement_exercise_name,
                replacement_catalog_exercise_id,
                original_movement_pattern,
                replacement_movement_pattern,
                substitution_reason,
                status,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_instance_id,
                execution_row["id"],
                planned_exercise_id,
                planned_exercise_row["name"],
                replacement_entry.name,
                replacement_entry.id,
                original_movement_pattern,
                replacement_entry.movement_pattern,
                substitution_reason,
                status,
                now,
            ),
        )
        substitution_id = cursor.lastrowid
        conn.commit()

        cursor.execute(
            """
            SELECT *
            FROM workout_plan_exercise_substitutions
            WHERE id = ?
            """,
            (substitution_id,),
        )
        row = cursor.fetchone()

        return _row_to_substitution(row)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_substitutions_for_plan(
    plan_instance_id: int,
) -> list[WorkoutPlanExerciseSubstitution]:
    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    _get_plan_row_or_raise(cursor, plan_instance_id)

    cursor.execute(
        """
        SELECT *
        FROM workout_plan_exercise_substitutions
        WHERE workout_plan_instance_id = ?
        ORDER BY created_at, id
        """,
        (plan_instance_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_substitution(row) for row in rows]


def get_active_substitution_for_planned_exercise(
    plan_instance_id: int,
    planned_exercise_id: int,
) -> WorkoutPlanExerciseSubstitution | None:
    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        _get_plan_row_or_raise(cursor, plan_instance_id)
        _get_planned_exercise_row_or_raise(
            cursor,
            plan_instance_id,
            planned_exercise_id,
        )

        cursor.execute(
            """
            SELECT *
            FROM workout_plan_exercise_substitutions
            WHERE workout_plan_instance_id = ?
                AND planned_workout_exercise_id = ?
                AND status = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (plan_instance_id, planned_exercise_id, "active"),
        )
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    return _row_to_substitution(row)


def get_execution_state(plan_instance_id: int) -> dict:
    instance = get_workout_plan_instance(plan_instance_id)
    if instance is None:
        raise WorkoutPlanNotFoundError(
            f"Workout plan instance {plan_instance_id} was not found."
        )

    execution_session = get_workout_execution_session(plan_instance_id)
    if execution_session is None:
        raise WorkoutPlanInvalidStatusError(
            f"Workout plan instance {plan_instance_id} has no execution session."
        )

    planned_exercises = get_planned_workout_exercises(plan_instance_id)
    actual_sets = get_actual_sets(execution_session_id=execution_session.id)
    active_substitutions = [
        substitution
        for substitution in get_substitutions_for_plan(plan_instance_id)
        if substitution.status == "active"
    ]

    return {
        "workout_plan_instance": instance,
        "execution_session": execution_session,
        "planned_exercises": planned_exercises,
        "actual_sets": actual_sets,
        "active_substitutions": active_substitutions,
        "approved_workout_plan": instance.approved_workout_plan,
    }


def _get_required_started_execution_rows(cursor, plan_instance_id: int):
    cursor.execute(
        """
        SELECT *
        FROM workout_plan_instances
        WHERE id = ?
        """,
        (plan_instance_id,),
    )
    instance_row = cursor.fetchone()

    if instance_row is None:
        raise WorkoutPlanNotFoundError(
            f"Workout plan instance {plan_instance_id} was not found."
        )

    if instance_row["status"] not in {"started", "in_progress"}:
        raise WorkoutPlanInvalidStatusError(
            "Actual sets can only be logged for started or in-progress "
            f"workout plans. Plan {plan_instance_id} is currently "
            f"{instance_row['status']}."
        )

    cursor.execute(
        """
        SELECT *
        FROM workout_execution_sessions
        WHERE workout_plan_instance_id = ?
        """,
        (plan_instance_id,),
    )
    execution_row = cursor.fetchone()

    if execution_row is None:
        raise WorkoutPlanInvalidStatusError(
            f"Workout plan instance {plan_instance_id} has no execution session."
        )

    if execution_row["status"] not in {"started", "in_progress"}:
        raise WorkoutPlanInvalidStatusError(
            "Actual sets can only be logged for started or in-progress "
            f"execution sessions. Execution session {execution_row['id']} "
            f"is currently {execution_row['status']}."
        )

    return instance_row, execution_row


def _get_planned_exercises_for_validation(
    cursor,
    plan_instance_id: int,
) -> dict[int, PlannedWorkoutExercise]:
    cursor.execute(
        """
        SELECT *
        FROM planned_workout_exercises
        WHERE workout_plan_instance_id = ?
        ORDER BY exercise_order
        """,
        (plan_instance_id,),
    )
    return _planned_exercises_by_id(
        [_row_to_planned_exercise(row) for row in cursor.fetchall()]
    )


def _validate_actual_set_payload(
    payload: dict,
    planned_exercises: dict[int, PlannedWorkoutExercise],
) -> PlannedWorkoutExercise | None:
    planned_exercise_id = payload.get("planned_workout_exercise_id")
    substitution_for_id = payload.get("substitution_for_planned_exercise_id")

    planned_exercise = None
    if planned_exercise_id is not None:
        planned_exercise_id = int(planned_exercise_id)
        planned_exercise = planned_exercises.get(planned_exercise_id)
        if planned_exercise is None:
            raise WorkoutPlanValidationError(
                "planned_workout_exercise_id must belong to the plan instance."
            )

    if substitution_for_id is not None:
        substitution_for_id = int(substitution_for_id)
        if substitution_for_id not in planned_exercises:
            raise WorkoutPlanValidationError(
                "substitution_for_planned_exercise_id must belong to the "
                "same plan instance."
            )
        if planned_exercise is None:
            planned_exercise = planned_exercises[substitution_for_id]

    completed = bool(payload.get("completed", True))
    skipped = bool(payload.get("skipped", False))

    if completed and skipped:
        raise WorkoutPlanValidationError("completed and skipped cannot both be true.")

    actual_reps = payload.get("actual_reps")
    actual_weight = payload.get("actual_weight")
    actual_rir = payload.get("actual_rir")

    if actual_reps is not None:
        actual_reps = int(actual_reps)
    if actual_weight is not None:
        actual_weight = float(actual_weight)
    if actual_rir is not None:
        actual_rir = int(actual_rir)

    _validate_non_negative_int(actual_reps, "actual_reps")
    _validate_non_negative_float(actual_weight, "actual_weight")
    _validate_actual_rir(actual_rir)

    if completed and not skipped and (actual_reps is None or actual_rir is None):
        raise WorkoutPlanValidationError(
            "completed actual sets require actual_reps and actual_rir."
        )

    if planned_exercise is None and not payload.get("exercise_name"):
        raise WorkoutPlanValidationError(
            "exercise_name is required when no planned exercise is referenced."
        )

    return planned_exercise


def log_actual_set(plan_instance_id: int, payload: dict) -> dict:
    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        instance_row, execution_row = _get_required_started_execution_rows(
            cursor, plan_instance_id
        )
        planned_exercises = _get_planned_exercises_for_validation(
            cursor, plan_instance_id
        )
        planned_exercise = _validate_actual_set_payload(payload, planned_exercises)

        planned_exercise_id = payload.get("planned_workout_exercise_id")
        substitution_for_id = payload.get("substitution_for_planned_exercise_id")
        exercise_name = payload.get("exercise_name")
        if exercise_name is None and planned_exercise is not None:
            exercise_name = planned_exercise.name

        set_number = payload.get("set_number")
        if set_number is None:
            set_number = (
                len(get_actual_sets(execution_session_id=execution_row["id"])) + 1
            )
        set_number = int(set_number)
        if set_number <= 0:
            raise WorkoutPlanValidationError("set_number must be positive.")

        completed = bool(payload.get("completed", True))
        skipped = bool(payload.get("skipped", False))
        actual_reps = payload.get("actual_reps")
        actual_weight = payload.get("actual_weight")
        actual_rir = payload.get("actual_rir")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO workout_execution_set_actuals (
                workout_execution_session_id,
                planned_workout_exercise_id,
                workout_session_id,
                workout_set_id,
                exercise_name,
                set_number,
                planned_reps_min,
                planned_reps_max,
                planned_rir_min,
                planned_rir_max,
                actual_reps,
                actual_weight,
                actual_rir,
                completed,
                skipped,
                substitution_for_planned_exercise_id,
                notes,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_row["id"],
                planned_exercise_id,
                execution_row["workout_session_id"],
                None,
                str(exercise_name),
                set_number,
                planned_exercise.reps_min if planned_exercise else None,
                planned_exercise.reps_max if planned_exercise else None,
                planned_exercise.rir_min if planned_exercise else None,
                planned_exercise.rir_max if planned_exercise else None,
                actual_reps,
                actual_weight,
                actual_rir,
                1 if completed else 0,
                1 if skipped else 0,
                substitution_for_id,
                payload.get("notes"),
                now,
            ),
        )
        actual_set_id = cursor.lastrowid

        if instance_row["status"] == "started":
            cursor.execute(
                """
                UPDATE workout_plan_instances
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                ("in_progress", now, plan_instance_id),
            )

        if execution_row["status"] == "started":
            cursor.execute(
                """
                UPDATE workout_execution_sessions
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                ("in_progress", now, execution_row["id"]),
            )

        conn.commit()

        cursor.execute(
            "SELECT * FROM workout_execution_set_actuals WHERE id = ?",
            (actual_set_id,),
        )
        actual_set = _row_to_actual_set(cursor.fetchone())
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "actual_set": actual_set,
        "execution_state": get_execution_state(plan_instance_id),
    }


def _get_required_editable_actual_set_rows(
    cursor,
    plan_instance_id: int,
    actual_set_id: int,
):
    cursor.execute(
        """
        SELECT *
        FROM workout_plan_instances
        WHERE id = ?
        """,
        (plan_instance_id,),
    )
    instance_row = cursor.fetchone()

    if instance_row is None:
        raise WorkoutPlanNotFoundError(
            f"Workout plan instance {plan_instance_id} was not found."
        )

    if instance_row["status"] not in {"in_progress", "completed"}:
        raise WorkoutPlanInvalidStatusError(
            "Actual sets can only be edited for in-progress or completed "
            f"workout plans. Plan {plan_instance_id} is currently "
            f"{instance_row['status']}."
        )

    cursor.execute(
        """
        SELECT *
        FROM workout_execution_sessions
        WHERE workout_plan_instance_id = ?
        """,
        (plan_instance_id,),
    )
    execution_row = cursor.fetchone()

    if execution_row is None:
        raise WorkoutPlanInvalidStatusError(
            f"Workout plan instance {plan_instance_id} has no execution session."
        )

    if execution_row["status"] not in {"in_progress", "completed"}:
        raise WorkoutPlanInvalidStatusError(
            "Actual sets can only be edited for in-progress or completed "
            f"execution sessions. Execution session {execution_row['id']} "
            f"is currently {execution_row['status']}."
        )

    cursor.execute(
        """
        SELECT *
        FROM workout_execution_set_actuals
        WHERE id = ?
          AND workout_execution_session_id = ?
        """,
        (actual_set_id, execution_row["id"]),
    )
    actual_set_row = cursor.fetchone()

    if actual_set_row is None:
        raise WorkoutPlanValidationError(
            "actual_set_id must belong to the workout plan instance."
        )

    return instance_row, execution_row, actual_set_row


def update_actual_set(
    plan_instance_id: int,
    actual_set_id: int,
    payload: dict,
) -> dict:
    """Correct a logged actual set without changing execution completion state."""

    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        _instance_row, execution_row, actual_set_row = (
            _get_required_editable_actual_set_rows(
                cursor,
                plan_instance_id,
                actual_set_id,
            )
        )
        planned_exercises = _get_planned_exercises_for_validation(
            cursor, plan_instance_id
        )

        candidate = {
            "planned_workout_exercise_id": actual_set_row[
                "planned_workout_exercise_id"
            ],
            "exercise_name": actual_set_row["exercise_name"],
            "set_number": actual_set_row["set_number"],
            "actual_reps": actual_set_row["actual_reps"],
            "actual_weight": actual_set_row["actual_weight"],
            "actual_rir": actual_set_row["actual_rir"],
            "completed": bool(actual_set_row["completed"]),
            "skipped": bool(actual_set_row["skipped"]),
            "substitution_for_planned_exercise_id": actual_set_row[
                "substitution_for_planned_exercise_id"
            ],
            "notes": actual_set_row["notes"],
        }

        for key, value in payload.items():
            if key in candidate:
                candidate[key] = value

        planned_exercise = _validate_actual_set_payload(
            candidate,
            planned_exercises,
        )

        set_number = int(candidate["set_number"])
        if set_number <= 0:
            raise WorkoutPlanValidationError("set_number must be positive.")

        planned_exercise_id = candidate.get("planned_workout_exercise_id")
        substitution_for_id = candidate.get("substitution_for_planned_exercise_id")

        if planned_exercise_id is not None:
            planned_exercise_id = int(planned_exercise_id)
        if substitution_for_id is not None:
            substitution_for_id = int(substitution_for_id)

        exercise_name = candidate.get("exercise_name")
        if (not exercise_name) and planned_exercise is not None:
            exercise_name = planned_exercise.name

        if not exercise_name:
            raise WorkoutPlanValidationError(
                "exercise_name is required when no planned exercise is referenced."
            )

        actual_reps = candidate.get("actual_reps")
        actual_weight = candidate.get("actual_weight")
        actual_rir = candidate.get("actual_rir")
        if actual_reps is not None:
            actual_reps = int(actual_reps)
        if actual_weight is not None:
            actual_weight = float(actual_weight)
        if actual_rir is not None:
            actual_rir = int(actual_rir)

        completed = bool(candidate.get("completed", False))
        skipped = bool(candidate.get("skipped", False))
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            UPDATE workout_execution_set_actuals
            SET
                planned_workout_exercise_id = ?,
                exercise_name = ?,
                set_number = ?,
                planned_reps_min = ?,
                planned_reps_max = ?,
                planned_rir_min = ?,
                planned_rir_max = ?,
                actual_reps = ?,
                actual_weight = ?,
                actual_rir = ?,
                completed = ?,
                skipped = ?,
                substitution_for_planned_exercise_id = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
              AND workout_execution_session_id = ?
            """,
            (
                planned_exercise_id,
                str(exercise_name),
                set_number,
                planned_exercise.reps_min if planned_exercise else None,
                planned_exercise.reps_max if planned_exercise else None,
                planned_exercise.rir_min if planned_exercise else None,
                planned_exercise.rir_max if planned_exercise else None,
                actual_reps,
                actual_weight,
                actual_rir,
                1 if completed else 0,
                1 if skipped else 0,
                substitution_for_id,
                candidate.get("notes"),
                now,
                actual_set_id,
                execution_row["id"],
            ),
        )

        conn.commit()

        cursor.execute(
            """
            SELECT *
            FROM workout_execution_set_actuals
            WHERE id = ?
            """,
            (actual_set_id,),
        )
        actual_set = _row_to_actual_set(cursor.fetchone())
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    execution_state = get_execution_state(plan_instance_id)
    return {
        "actual_set": actual_set,
        "workout_plan_instance": execution_state["workout_plan_instance"],
        "execution_session": execution_state["execution_session"],
        "planned_vs_actual_summary": build_planned_vs_actual_summary(plan_instance_id),
    }


def select_current_workout_plan(user_id: int) -> dict:
    """Persist the current server-built ApprovedWorkoutPlan as selected.

    The caller never submits a workout plan JSON payload in v1. The backend
    rebuilds the current approved preview, snapshots it immutably, extracts
    planned exercise rows, and creates a future execution-session bridge in
    selected status.
    """

    ensure_workout_plan_persistence_tables()
    health_state = build_user_health_state(user_id)
    approved_plan = build_approved_workout_plan(health_state)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO workout_plan_instances (
            user_id,
            status,
            scenario,
            confidence,
            title,
            approved_workout_plan_json,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            user_id,
            "selected",
            approved_plan.scenario,
            approved_plan.confidence,
            approved_plan.title,
            _encode_json(asdict(approved_plan)),
        ),
    )
    instance_id = cursor.lastrowid

    for index, exercise in enumerate(approved_plan.exercises, start=1):
        cursor.execute(
            """
            INSERT INTO planned_workout_exercises (
                workout_plan_instance_id,
                exercise_order,
                name,
                sets,
                reps_min,
                reps_max,
                rir_min,
                rir_max,
                notes,
                equipment_required_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                instance_id,
                index,
                exercise.name,
                exercise.sets,
                exercise.reps_min,
                exercise.reps_max,
                exercise.rir_min,
                exercise.rir_max,
                exercise.notes,
                _encode_json(exercise.equipment_required),
            ),
        )

    cursor.execute(
        """
        INSERT INTO workout_execution_sessions (
            workout_plan_instance_id,
            user_id,
            status,
            updated_at
        )
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (instance_id, user_id, "selected"),
    )
    execution_session_id = cursor.lastrowid

    conn.commit()

    cursor.execute("SELECT * FROM workout_plan_instances WHERE id = ?", (instance_id,))
    instance = _row_to_workout_plan_instance(cursor.fetchone())

    cursor.execute(
        """
        SELECT *
        FROM planned_workout_exercises
        WHERE workout_plan_instance_id = ?
        ORDER BY exercise_order
        """,
        (instance_id,),
    )
    planned_exercises = [_row_to_planned_exercise(row) for row in cursor.fetchall()]

    cursor.execute(
        "SELECT * FROM workout_execution_sessions WHERE id = ?",
        (execution_session_id,),
    )
    execution_session = _row_to_execution_session(cursor.fetchone())
    conn.close()

    return {
        "workout_plan_instance": instance,
        "planned_exercises": planned_exercises,
        "execution_session": execution_session,
        "approved_workout_plan": approved_plan,
    }


def start_selected_workout_plan(workout_plan_instance_id: int) -> dict:
    """Transition a selected workout plan into a started execution session.

    This is the first execution transition only. It creates a draft
    workout_sessions row so future actual-set logging can attach to the
    existing workout logging path, but it does not create actual workout sets
    or complete the workout.
    """

    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM workout_plan_instances
        WHERE id = ?
        """,
        (workout_plan_instance_id,),
    )
    instance_row = cursor.fetchone()

    if instance_row is None:
        conn.close()
        raise WorkoutPlanNotFoundError(
            f"Workout plan instance {workout_plan_instance_id} was not found."
        )

    if instance_row["status"] != "selected":
        status = instance_row["status"]
        conn.close()
        raise WorkoutPlanInvalidStatusError(
            "Only selected workout plans can be started. "
            f"Plan {workout_plan_instance_id} is currently {status}."
        )

    approved_plan = _approved_workout_plan_from_dict(
        _decode_json(instance_row["approved_workout_plan_json"], {})
    )

    cursor.execute(
        """
        SELECT *
        FROM workout_execution_sessions
        WHERE workout_plan_instance_id = ?
        """,
        (workout_plan_instance_id,),
    )
    execution_row = cursor.fetchone()

    if execution_row is None:
        conn.close()
        raise WorkoutPlanInvalidStatusError(
            "Selected workout plan is missing its execution session."
        )

    if execution_row["status"] != "selected":
        status = execution_row["status"]
        conn.close()
        raise WorkoutPlanInvalidStatusError(
            "Only selected execution sessions can be started. "
            f"Execution session {execution_row['id']} is currently {status}."
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    workout_date = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        """
        INSERT INTO workout_sessions (
            user_id,
            workout_date,
            workout_name,
            duration_minutes,
            notes
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            instance_row["user_id"],
            workout_date,
            approved_plan.title,
            approved_plan.duration_minutes,
            (
                "Draft session created from selected workout plan "
                f"instance {workout_plan_instance_id}. Actual set logging "
                "against planned exercises is not implemented yet."
            ),
        ),
    )
    workout_session_id = cursor.lastrowid

    cursor.execute(
        """
        UPDATE workout_plan_instances
        SET status = ?, updated_at = ?
        WHERE id = ?
        """,
        ("started", now, workout_plan_instance_id),
    )

    cursor.execute(
        """
        UPDATE workout_execution_sessions
        SET
            status = ?,
            workout_session_id = ?,
            started_at = ?,
            updated_at = ?
        WHERE workout_plan_instance_id = ?
        """,
        (
            "started",
            workout_session_id,
            now,
            now,
            workout_plan_instance_id,
        ),
    )

    conn.commit()

    cursor.execute(
        "SELECT * FROM workout_plan_instances WHERE id = ?",
        (workout_plan_instance_id,),
    )
    instance = _row_to_workout_plan_instance(cursor.fetchone())

    cursor.execute(
        """
        SELECT *
        FROM planned_workout_exercises
        WHERE workout_plan_instance_id = ?
        ORDER BY exercise_order
        """,
        (workout_plan_instance_id,),
    )
    planned_exercises = [_row_to_planned_exercise(row) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT *
        FROM workout_execution_sessions
        WHERE workout_plan_instance_id = ?
        """,
        (workout_plan_instance_id,),
    )
    execution_session = _row_to_execution_session(cursor.fetchone())
    conn.close()

    return {
        "workout_plan_instance": instance,
        "planned_exercises": planned_exercises,
        "execution_session": execution_session,
        "approved_workout_plan": instance.approved_workout_plan,
    }


def complete_workout_plan(plan_instance_id: int) -> dict:
    """Complete an in-progress planned workout execution.

    Completion is intentionally narrow in v1. Only in-progress plan and
    execution-session rows can complete. Started sessions with no actual rows,
    selected sessions, completed sessions, and abandoned/cancelled sessions are
    rejected. Actual execution rows are preserved and summarized after the
    status transition.
    """

    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM workout_plan_instances
            WHERE id = ?
            """,
            (plan_instance_id,),
        )
        instance_row = cursor.fetchone()

        if instance_row is None:
            raise WorkoutPlanNotFoundError(
                f"Workout plan instance {plan_instance_id} was not found."
            )

        if instance_row["status"] != "in_progress":
            raise WorkoutPlanInvalidStatusError(
                "Only in-progress workout plans can be completed. "
                f"Plan {plan_instance_id} is currently {instance_row['status']}."
            )

        cursor.execute(
            """
            SELECT *
            FROM workout_execution_sessions
            WHERE workout_plan_instance_id = ?
            """,
            (plan_instance_id,),
        )
        execution_row = cursor.fetchone()

        if execution_row is None:
            raise WorkoutPlanInvalidStatusError(
                f"Workout plan instance {plan_instance_id} has no execution session."
            )

        if execution_row["status"] != "in_progress":
            raise WorkoutPlanInvalidStatusError(
                "Only in-progress execution sessions can be completed. "
                f"Execution session {execution_row['id']} is currently "
                f"{execution_row['status']}."
            )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            UPDATE workout_plan_instances
            SET status = ?, completed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            ("completed", now, now, plan_instance_id),
        )
        cursor.execute(
            """
            UPDATE workout_execution_sessions
            SET status = ?, completed_at = ?, updated_at = ?
            WHERE workout_plan_instance_id = ?
            """,
            ("completed", now, now, plan_instance_id),
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    execution_state = get_execution_state(plan_instance_id)
    summary = build_planned_vs_actual_summary(plan_instance_id)

    return {
        "workout_plan_instance": execution_state["workout_plan_instance"],
        "execution_session": execution_state["execution_session"],
        "planned_vs_actual_summary": summary,
    }


def _average_planned_rir(
    planned_exercises: list[PlannedWorkoutExercise],
) -> float | None:
    rir_total = 0.0
    set_count = 0

    for exercise in planned_exercises:
        rir_midpoint = (exercise.rir_min + exercise.rir_max) / 2
        rir_total += rir_midpoint * exercise.sets
        set_count += exercise.sets

    if set_count == 0:
        return None

    return round(rir_total / set_count, 2)


def _average_actual_rir(actual_sets: list[WorkoutExecutionSetActual]) -> float | None:
    actual_rirs = [
        actual_set.actual_rir
        for actual_set in actual_sets
        if actual_set.completed
        and not actual_set.skipped
        and actual_set.actual_rir is not None
    ]

    if not actual_rirs:
        return None

    return round(sum(actual_rirs) / len(actual_rirs), 2)


def build_planned_vs_actual_summary(
    plan_instance_id: int,
) -> WorkoutPlannedVsActualSummary:
    """Build the descriptive planned-vs-actual summary for a plan instance.

    This function is intentionally read-only. It does not complete workouts,
    mutate execution state, mirror rows into manual workout_sets, or feed the
    recommendation engine. It summarizes the current execution bridge rows.
    """

    execution_state = get_execution_state(plan_instance_id)
    execution_session = execution_state["execution_session"]
    planned_exercises = execution_state["planned_exercises"]
    actual_sets = execution_state["actual_sets"]

    planned_exercise_count = len(planned_exercises)
    planned_set_count = sum(exercise.sets for exercise in planned_exercises)

    completed_actual_sets = [
        actual_set
        for actual_set in actual_sets
        if actual_set.completed and not actual_set.skipped
    ]
    non_skipped_actual_sets = [
        actual_set for actual_set in actual_sets if not actual_set.skipped
    ]
    skipped_actual_sets = [
        actual_set for actual_set in actual_sets if actual_set.skipped
    ]

    completed_exercise_ids = {
        actual_set.planned_workout_exercise_id
        for actual_set in completed_actual_sets
        if actual_set.planned_workout_exercise_id is not None
    }
    skipped_exercise_ids = {
        actual_set.planned_workout_exercise_id
        for actual_set in skipped_actual_sets
        if actual_set.planned_workout_exercise_id is not None
    }
    substituted_exercise_ids = {
        actual_set.substitution_for_planned_exercise_id
        for actual_set in actual_sets
        if actual_set.substitution_for_planned_exercise_id is not None
    }

    sets_below_planned_reps = 0
    sets_inside_planned_reps = 0
    sets_above_planned_reps = 0

    missing_actual_rir = False
    missing_actual_reps = False

    for actual_set in non_skipped_actual_sets:
        if actual_set.actual_rir is None:
            missing_actual_rir = True
        if actual_set.actual_reps is None:
            missing_actual_reps = True

        if (
            actual_set.actual_reps is None
            or actual_set.planned_reps_min is None
            or actual_set.planned_reps_max is None
        ):
            continue

        if actual_set.actual_reps < actual_set.planned_reps_min:
            sets_below_planned_reps += 1
        elif actual_set.actual_reps > actual_set.planned_reps_max:
            sets_above_planned_reps += 1
        else:
            sets_inside_planned_reps += 1

    average_planned_rir = _average_planned_rir(planned_exercises)
    average_actual_rir = _average_actual_rir(actual_sets)
    rir_deviation = None
    if average_planned_rir is not None and average_actual_rir is not None:
        rir_deviation = round(average_actual_rir - average_planned_rir, 2)

    completed_set_count = len(completed_actual_sets)
    actual_set_count = len(non_skipped_actual_sets)
    skipped_set_count = len(skipped_actual_sets)

    if planned_set_count > 0:
        completion_percentage = round(
            (completed_set_count / planned_set_count) * 100, 2
        )
    else:
        completion_percentage = 0.0

    deviation_flags: list[str] = []
    notes: list[str] = []

    if not actual_sets:
        deviation_flags.append("empty_completion")
        notes.append("No actual workout execution rows have been logged yet.")

    if completed_set_count < planned_set_count:
        deviation_flags.append("incomplete_logging")
        notes.append("Completed actual sets are fewer than planned sets.")

    if skipped_set_count > 0:
        deviation_flags.append("skipped_exercises_present")
        notes.append("One or more planned sets or exercises were skipped.")

    if substituted_exercise_ids:
        deviation_flags.append("substitutions_present")
        notes.append("One or more planned exercises had substitutions logged.")

    if rir_deviation is not None:
        if rir_deviation < 0:
            deviation_flags.append("actual_effort_harder_than_planned")
        elif rir_deviation > 0:
            deviation_flags.append("actual_effort_easier_than_planned")

    if sets_below_planned_reps > 0:
        deviation_flags.append("reps_below_plan")
    if sets_above_planned_reps > 0:
        deviation_flags.append("reps_above_plan")
    if missing_actual_rir:
        deviation_flags.append("missing_actual_rir")
    if missing_actual_reps:
        deviation_flags.append("missing_actual_reps")

    rep_deviation = {
        "sets_below_planned_reps": sets_below_planned_reps,
        "sets_inside_planned_reps": sets_inside_planned_reps,
        "sets_above_planned_reps": sets_above_planned_reps,
    }

    return WorkoutPlannedVsActualSummary(
        workout_plan_instance_id=plan_instance_id,
        workout_execution_session_id=(
            execution_session.id if execution_session else None
        ),
        planned_exercise_count=planned_exercise_count,
        completed_exercise_count=len(completed_exercise_ids),
        skipped_exercise_count=len(skipped_exercise_ids),
        substituted_exercise_count=len(substituted_exercise_ids),
        planned_set_count=planned_set_count,
        actual_set_count=actual_set_count,
        completed_set_count=completed_set_count,
        skipped_set_count=skipped_set_count,
        completion_percentage=completion_percentage,
        average_planned_rir=average_planned_rir,
        average_actual_rir=average_actual_rir,
        rir_deviation=rir_deviation,
        rep_deviation=rep_deviation,
        sets_below_planned_reps=sets_below_planned_reps,
        sets_inside_planned_reps=sets_inside_planned_reps,
        sets_above_planned_reps=sets_above_planned_reps,
        notes=notes,
        deviation_flags=deviation_flags,
    )
