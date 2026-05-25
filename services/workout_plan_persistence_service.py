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
    WorkoutPlanInstance,
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


class WorkoutPlanPersistenceError(Exception):
    """Base error for workout plan persistence workflows."""


class WorkoutPlanNotFoundError(WorkoutPlanPersistenceError):
    """Raised when a workout plan instance cannot be found."""


class WorkoutPlanInvalidStatusError(WorkoutPlanPersistenceError):
    """Raised when a workout plan instance cannot transition as requested."""


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
