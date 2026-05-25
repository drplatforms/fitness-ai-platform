from __future__ import annotations

from models.user_state_models import UserHealthState
from models.workout_constraint_models import WorkoutConstraints
from services.workout_service import get_recent_workouts

DEFAULT_AVAILABLE_EQUIPMENT = [
    "barbell",
    "bodyweight",
    "cable",
    "dumbbell",
    "machine",
]


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


def build_workout_constraints(health_state: UserHealthState) -> WorkoutConstraints:
    """Build v1 exercise-selection boundaries for workout plan previews.

    Explicit equipment/profile tables do not exist yet, so v1 uses conservative
    default gym/home equipment assumptions and recent workout history when it is
    available. Training intensity and recovery limits stay in TrainingConstraints.
    """

    recent_exercises = _recent_exercise_names(health_state.user_id)
    reason_codes = [
        "no_explicit_equipment_profile",
        "safe_default_equipment_assumptions",
    ]

    if recent_exercises:
        reason_codes.append("recent_exercise_history_available")
    else:
        reason_codes.append("recent_exercise_history_unavailable")

    available_equipment = [
        _normalize_equipment(item) for item in DEFAULT_AVAILABLE_EQUIPMENT
    ]

    return WorkoutConstraints(
        available_equipment=available_equipment,
        unavailable_equipment=[],
        preferred_movements=[],
        avoid_movements=[],
        movement_restrictions=[],
        sore_regions=[],
        recent_exercises=recent_exercises,
        confidence="Low",
        reason_codes=reason_codes,
    )
