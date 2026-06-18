"""Seed canonical planned-execution rows for training report runtime QA.

Run from the project root:
    python scripts/seed_training_execution_qa.py

This seed uses the existing workout plan/execution service contracts to create
clean completed planned executions for QA users 101-105. It is safe to rerun:
it only removes rows marked by this seed's workout session note marker.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database  # noqa: E402
from services.workout_plan_persistence_service import (  # noqa: E402
    complete_workout_plan,
    log_actual_set,
    select_current_workout_plan,
    start_selected_workout_plan,
)

SEED_MARKER = "canonical_training_execution_qa_seed_v1"
QA_USER_IDS = (101, 102, 103, 104, 105)


@dataclass(frozen=True)
class SeededTrainingExecution:
    user_id: int
    workout_plan_instance_id: int
    workout_execution_session_id: int
    workout_session_id: int | None
    title: str
    actual_set_count: int


def _bridge_plan_ids(cursor) -> list[int]:
    """Return malformed/manual bridge rows from the prior invalid runtime QA path."""

    cursor.execute(
        """
        SELECT id
        FROM workout_plan_instances
        WHERE scenario = ?
        """,
        ("qa_legacy_execution_bridge",),
    )
    return [int(row["id"]) for row in cursor.fetchall()]


def _seed_plan_ids(cursor) -> list[int]:
    """Return plan ids created by this official canonical seed."""

    marker = f"{SEED_MARKER}:%"
    cursor.execute(
        """
        SELECT DISTINCT execution.workout_plan_instance_id AS plan_id
        FROM workout_execution_sessions AS execution
        JOIN workout_sessions AS session
            ON session.id = execution.workout_session_id
        WHERE session.notes LIKE ?
        """,
        (marker,),
    )
    return [int(row["plan_id"]) for row in cursor.fetchall()]


def _delete_plan_graph(cursor, plan_ids: list[int]) -> None:
    if not plan_ids:
        return

    placeholders = ",".join("?" for _ in plan_ids)

    cursor.execute(
        f"""
        DELETE FROM workout_execution_set_actuals
        WHERE workout_execution_session_id IN (
            SELECT id
            FROM workout_execution_sessions
            WHERE workout_plan_instance_id IN ({placeholders})
        )
        """,
        plan_ids,
    )
    cursor.execute(
        f"""
        DELETE FROM workout_execution_sessions
        WHERE workout_plan_instance_id IN ({placeholders})
        """,
        plan_ids,
    )
    cursor.execute(
        f"""
        DELETE FROM planned_workout_exercises
        WHERE workout_plan_instance_id IN ({placeholders})
        """,
        plan_ids,
    )
    cursor.execute(
        f"""
        DELETE FROM workout_plan_instances
        WHERE id IN ({placeholders})
        """,
        plan_ids,
    )


def clear_seeded_training_execution_qa(
    *, remove_invalid_bridge_rows: bool = True
) -> int:
    """Remove rows created by this seed and optionally the known invalid bridge rows."""

    database.initialize_database()
    conn = database.get_connection()
    cursor = conn.cursor()

    plan_ids = _seed_plan_ids(cursor)
    if remove_invalid_bridge_rows:
        plan_ids.extend(_bridge_plan_ids(cursor))

    unique_plan_ids = sorted(set(plan_ids))
    _delete_plan_graph(cursor, unique_plan_ids)

    # Delete only workout_sessions created by this seed marker. The invalid bridge
    # reused legacy workout_sessions, so those are intentionally not removed here.
    cursor.execute(
        """
        DELETE FROM workout_sets
        WHERE workout_session_id IN (
            SELECT id FROM workout_sessions WHERE notes LIKE ?
        )
        """,
        (f"{SEED_MARKER}:%",),
    )
    cursor.execute(
        "DELETE FROM workout_sessions WHERE notes LIKE ?",
        (f"{SEED_MARKER}:%",),
    )

    conn.commit()
    conn.close()

    return len(unique_plan_ids)


def _mark_seed_workout_session(
    *,
    user_id: int,
    workout_session_id: int | None,
    workout_plan_instance_id: int,
    title: str,
) -> None:
    if workout_session_id is None:
        return

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE workout_sessions
        SET notes = ?
        WHERE id = ?
          AND user_id = ?
        """,
        (
            f"{SEED_MARKER}: planned execution seed for runtime QA; "
            f"plan_instance_id={workout_plan_instance_id}; title={title}",
            workout_session_id,
            user_id,
        ),
    )
    conn.commit()
    conn.close()


def _actual_weight_for(user_id: int, exercise_index: int, set_index: int) -> float:
    base_by_user = {
        101: 35.0,
        102: 50.0,
        103: 45.0,
        104: 55.0,
        105: 25.0,
    }
    return round(
        base_by_user.get(user_id, 40.0) + (exercise_index * 7.5) + set_index, 1
    )


def _actual_rir_for(user_id: int, planned_rir_min: int, planned_rir_max: int) -> int:
    if user_id == 101:
        return min(max(planned_rir_max, 3), 5)
    if user_id == 102:
        return max(planned_rir_min, 1)
    if user_id == 103:
        return max(planned_rir_min, 1)
    if user_id == 104:
        return max(planned_rir_min, 1)
    return min(max(planned_rir_max, 3), 6)


def _log_seed_actuals(
    user_id: int, plan_instance_id: int, planned_exercises: list
) -> int:
    actual_set_count = 0

    # Log one completed set per planned exercise. This is intentionally enough
    # evidence for training report anchoring without pretending to be a full
    # multi-set training history.
    for exercise_index, planned_exercise in enumerate(planned_exercises, start=1):
        actual_reps = planned_exercise.reps_max
        actual_rir = _actual_rir_for(
            user_id,
            planned_exercise.rir_min,
            planned_exercise.rir_max,
        )
        actual_weight = _actual_weight_for(user_id, exercise_index, actual_set_count)

        log_actual_set(
            plan_instance_id,
            {
                "planned_workout_exercise_id": planned_exercise.id,
                "set_number": 1,
                "actual_reps": actual_reps,
                "actual_weight": actual_weight,
                "actual_rir": actual_rir,
                "completed": True,
                "skipped": False,
                "notes": f"{SEED_MARKER}: completed planned exercise evidence.",
            },
        )
        actual_set_count += 1

    return actual_set_count


def seed_training_execution_qa() -> list[SeededTrainingExecution]:
    """Create canonical completed planned-execution evidence for users 101-105."""

    database.initialize_database()
    clear_seeded_training_execution_qa(remove_invalid_bridge_rows=True)

    seeded: list[SeededTrainingExecution] = []

    for user_id in QA_USER_IDS:
        selected = select_current_workout_plan(user_id)
        instance = selected["workout_plan_instance"]
        plan_instance_id = int(instance.id)

        started = start_selected_workout_plan(plan_instance_id)
        execution_session = started["execution_session"]
        planned_exercises = list(started["planned_exercises"])

        _mark_seed_workout_session(
            user_id=user_id,
            workout_session_id=execution_session.workout_session_id,
            workout_plan_instance_id=plan_instance_id,
            title=instance.title,
        )

        actual_set_count = _log_seed_actuals(
            user_id,
            plan_instance_id,
            planned_exercises,
        )
        completed = complete_workout_plan(plan_instance_id)
        completed_instance = completed["workout_plan_instance"]
        completed_execution_session = completed["execution_session"]

        seeded.append(
            SeededTrainingExecution(
                user_id=user_id,
                workout_plan_instance_id=plan_instance_id,
                workout_execution_session_id=int(completed_execution_session.id),
                workout_session_id=completed_execution_session.workout_session_id,
                title=completed_instance.title,
                actual_set_count=actual_set_count,
            )
        )

    return seeded


def main() -> None:
    seeded = seed_training_execution_qa()
    print("Seeded canonical training execution QA rows:")
    for item in seeded:
        print(
            "- "
            f"user_id={item.user_id} "
            f"plan_id={item.workout_plan_instance_id} "
            f"execution_id={item.workout_execution_session_id} "
            f"actual_sets={item.actual_set_count} "
            f"title={item.title}"
        )


if __name__ == "__main__":
    main()
