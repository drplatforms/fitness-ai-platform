from __future__ import annotations

from dataclasses import asdict

from models.equipment_profile_models import EquipmentProfile
from models.exercise_catalog_models import (
    ExerciseCatalogEntry,
    ExerciseSubstitutionCandidate,
)
from models.workout_plan_models import PlannedWorkoutExercise
from services.equipment_profile_service import get_effective_equipment_profile
from services.exercise_catalog_service import (
    find_catalog_entry_by_name,
    get_exercise_catalog,
)
from services.workout_plan_persistence_service import (
    WorkoutPlanInvalidStatusError,
    WorkoutPlanNotFoundError,
    WorkoutPlanValidationError,
    create_substitution_record,
    get_active_substitution_for_planned_exercise,
    get_planned_workout_exercises,
    get_workout_plan_instance,
)

COMPATIBLE_MOVEMENT_FAMILIES: dict[str, set[str]] = {
    "squat": {"lunge"},
    "lunge": {"squat"},
    "core_anti_extension": {"core_anti_rotation"},
    "core_anti_rotation": {"core_anti_extension"},
    "arms_biceps": set(),
    "arms_triceps": set(),
    "conditioning": {"carry"},
    "carry": {"conditioning"},
}


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_display_name(value: str) -> str:
    return " ".join(value.strip().replace("-", " ").split()).title()


def _equipment_is_compatible(
    entry: ExerciseCatalogEntry,
    equipment_profile: EquipmentProfile,
) -> bool:
    required = {_normalize_token(equipment) for equipment in entry.equipment_required}
    available = {
        _normalize_token(equipment)
        for equipment in equipment_profile.available_equipment
    }
    unavailable = {
        _normalize_token(equipment)
        for equipment in equipment_profile.unavailable_equipment
    }

    if required & unavailable:
        return False

    if available and not required.issubset(available):
        return False

    return True


def _movement_match_reason(
    planned_movement_pattern: str,
    candidate_movement_pattern: str,
) -> str | None:
    planned_pattern = _normalize_token(planned_movement_pattern)
    candidate_pattern = _normalize_token(candidate_movement_pattern)

    if candidate_pattern == planned_pattern:
        return "same_movement_pattern"

    compatible_patterns = COMPATIBLE_MOVEMENT_FAMILIES.get(planned_pattern, set())
    if candidate_pattern in compatible_patterns:
        return "compatible_movement_family"

    return None


def _find_planned_exercise(
    planned_exercises: list[PlannedWorkoutExercise],
    planned_exercise_id: int,
) -> PlannedWorkoutExercise:
    for exercise in planned_exercises:
        if exercise.id == planned_exercise_id:
            return exercise

    raise WorkoutPlanValidationError(
        "planned_workout_exercise_id must belong to the plan instance."
    )


def _candidate_from_catalog_entry(
    entry: ExerciseCatalogEntry,
    reason_codes: list[str],
) -> ExerciseSubstitutionCandidate:
    if entry.id is None:
        raise WorkoutPlanValidationError(
            "Catalog substitution candidates require persisted catalog IDs."
        )

    return ExerciseSubstitutionCandidate(
        catalog_exercise_id=entry.id,
        name=entry.name,
        movement_pattern=entry.movement_pattern,
        required_equipment=list(entry.equipment_required),
        primary_muscle_groups=list(entry.primary_muscle_groups),
        exercise_type=entry.exercise_type,
        difficulty=entry.difficulty,
        compatibility_reason_codes=reason_codes,
    )


def get_substitution_candidates(
    plan_instance_id: int,
    planned_exercise_id: int,
) -> list[ExerciseSubstitutionCandidate]:
    """Return read-only catalog candidates for replacing a planned exercise.

    This service intentionally does not mutate the approved workout snapshot,
    planned exercise rows, actual set rows, or planned-vs-actual summaries.
    It only evaluates catalog entries against the original planned exercise and
    the user's current equipment profile.
    """

    plan_instance = get_workout_plan_instance(plan_instance_id)
    if plan_instance is None:
        raise WorkoutPlanNotFoundError(
            f"Workout plan instance {plan_instance_id} was not found."
        )

    planned_exercises = get_planned_workout_exercises(plan_instance_id)
    planned_exercise = _find_planned_exercise(
        planned_exercises,
        planned_exercise_id,
    )

    planned_catalog_entry = find_catalog_entry_by_name(planned_exercise.name)
    if planned_catalog_entry is None:
        raise WorkoutPlanValidationError(
            "Planned exercise must exist in the exercise catalog before "
            "substitution candidates can be generated."
        )

    equipment_profile = get_effective_equipment_profile(plan_instance.user_id)
    planned_name = _normalize_display_name(planned_catalog_entry.name)

    exact_matches: list[ExerciseSubstitutionCandidate] = []
    family_matches: list[ExerciseSubstitutionCandidate] = []

    for entry in get_exercise_catalog():
        if _normalize_display_name(entry.name) == planned_name:
            continue

        movement_reason = _movement_match_reason(
            planned_catalog_entry.movement_pattern,
            entry.movement_pattern,
        )
        if movement_reason is None:
            continue

        if not _equipment_is_compatible(entry, equipment_profile):
            continue

        reason_codes = [
            "catalog_backed_substitution_candidate",
            movement_reason,
            "equipment_compatible_with_current_profile",
        ]

        candidate = _candidate_from_catalog_entry(entry, reason_codes)
        if movement_reason == "same_movement_pattern":
            exact_matches.append(candidate)
        else:
            family_matches.append(candidate)

    return exact_matches + family_matches


def apply_substitution(
    plan_instance_id: int,
    planned_exercise_id: int,
    replacement_catalog_exercise_id: int,
    substitution_reason: str | None = "user_selected",
) -> dict:
    """Apply a catalog-approved substitution to an active workout plan.

    The apply step uses overlay semantics. It creates an active substitution
    record beside the immutable approved workout snapshot and original planned
    exercise row. It does not mutate planned exercises, approved workout JSON,
    actual-set rows, planned-vs-actual summaries, recommendations, or reports.
    """

    plan_instance = get_workout_plan_instance(plan_instance_id)
    if plan_instance is None:
        raise WorkoutPlanNotFoundError(
            f"Workout plan instance {plan_instance_id} was not found."
        )

    if plan_instance.status not in {"selected", "started", "in_progress"}:
        raise WorkoutPlanInvalidStatusError(
            "Substitutions can only be applied to selected, started, or "
            f"in-progress workout plans. Plan {plan_instance_id} is currently "
            f"{plan_instance.status}."
        )

    planned_exercises = get_planned_workout_exercises(plan_instance_id)
    planned_exercise = _find_planned_exercise(planned_exercises, planned_exercise_id)

    candidates = get_substitution_candidates(plan_instance_id, planned_exercise_id)
    selected_candidate = next(
        (
            candidate
            for candidate in candidates
            if candidate.catalog_exercise_id == int(replacement_catalog_exercise_id)
        ),
        None,
    )
    if selected_candidate is None:
        raise WorkoutPlanValidationError(
            "replacement_catalog_exercise_id must be one of the approved "
            "substitution candidates for this planned exercise."
        )

    previous_active_substitution = get_active_substitution_for_planned_exercise(
        plan_instance_id,
        planned_exercise_id,
    )

    active_substitution = create_substitution_record(
        plan_instance_id=plan_instance_id,
        planned_exercise_id=planned_exercise_id,
        replacement_catalog_exercise_id=selected_candidate.catalog_exercise_id,
        substitution_reason=substitution_reason or "user_selected",
        status="active",
    )

    return {
        "workout_plan_instance": get_workout_plan_instance(plan_instance_id),
        "planned_workout_exercise": planned_exercise,
        "active_substitution": active_substitution,
        "previous_active_substitution_replaced": previous_active_substitution
        is not None,
        "selected_candidate": selected_candidate,
    }


def get_substitution_candidate_dicts(
    plan_instance_id: int,
    planned_exercise_id: int,
) -> list[dict]:
    """Return JSON-serializable candidate dictionaries for API responses."""

    return [
        asdict(candidate)
        for candidate in get_substitution_candidates(
            plan_instance_id,
            planned_exercise_id,
        )
    ]
