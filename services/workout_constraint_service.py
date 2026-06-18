from __future__ import annotations

from database import get_connection
from models.user_state_models import UserHealthState
from models.workout_constraint_models import WorkoutConstraints
from services.equipment_profile_service import get_effective_equipment_profile
from services.workout_service import get_recent_workouts


def _normalize_equipment(equipment: str) -> str:
    return equipment.strip().lower().replace(" ", "_")


def _unique_preserve_order(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _recent_exercise_names(user_id: int, limit: int = 5) -> list[str]:
    try:
        workouts = get_recent_workouts(user_id, limit=limit)
    except Exception:
        return []

    names: list[str] = []
    for workout in workouts:
        for set_row in workout.get("sets", []):
            name = set_row.get("name")
            if name:
                names.append(str(name))

    return _unique_preserve_order(names)


def _recent_planned_exercise_names(user_id: int, limit: int = 40) -> list[str]:
    """Return recent selected/executed plan exercises with repeated exposure intact.

    Workout plan services import this module while building previews, so this
    direct read avoids a circular import. Missing tables are allowed in fresh
    databases and simply mean there is no plan history yet.

    Unlike manual workout history, selected workout-plan history intentionally
    preserves repeated exercise names and plan order. The workout generator uses
    those repeated exposures to penalize recently repeated full-plan loops and
    slot-level choices.
    """

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pwe.name
            FROM planned_workout_exercises pwe
            JOIN workout_plan_instances wpi
                ON wpi.id = pwe.workout_plan_instance_id
            WHERE wpi.user_id = ?
              AND wpi.status IN ('selected', 'started', 'in_progress', 'completed')
            ORDER BY
                COALESCE(wpi.completed_at, wpi.selected_at, wpi.created_at) DESC,
                pwe.exercise_order ASC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
        conn.close()
    except Exception:
        return []

    return [str(row["name"]) for row in rows if row["name"]]


def build_workout_constraints(health_state: UserHealthState) -> WorkoutConstraints:
    """Build exercise-selection boundaries for workout plan previews.

    Explicit user equipment profiles override safe defaults. Training intensity
    and recovery limits stay in TrainingConstraints.
    """

    equipment_profile = get_effective_equipment_profile(health_state.user_id)
    recent_planned_exercises = _recent_planned_exercise_names(health_state.user_id)
    manual_recent_exercises = _recent_exercise_names(health_state.user_id)
    planned_exercise_set = set(recent_planned_exercises)
    recent_exercises = recent_planned_exercises + [
        name for name in manual_recent_exercises if name not in planned_exercise_set
    ]
    reason_codes = list(equipment_profile.reason_codes)

    if recent_exercises:
        reason_codes.append("recent_exercise_history_available")
    else:
        reason_codes.append("recent_exercise_history_unavailable")

    available_equipment = [
        _normalize_equipment(item) for item in equipment_profile.available_equipment
    ]
    unavailable_equipment = [
        _normalize_equipment(item) for item in equipment_profile.unavailable_equipment
    ]

    return WorkoutConstraints(
        available_equipment=available_equipment,
        unavailable_equipment=unavailable_equipment,
        preferred_movements=[],
        avoid_movements=[],
        movement_restrictions=[],
        sore_regions=[],
        recent_exercises=recent_exercises,
        confidence=equipment_profile.confidence,
        reason_codes=list(dict.fromkeys(reason_codes)),
    )
