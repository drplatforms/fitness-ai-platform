import json
import logging
import os
import time
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from models.user_state_models import UserHealthState
from models.workout_constraint_models import WorkoutConstraints
from models.workout_plan_models import (
    ApprovedWorkoutExercise,
    ApprovedWorkoutExplanation,
    ApprovedWorkoutExplanationResult,
    ApprovedWorkoutPlan,
    ApprovedWorkoutPlanResult,
    CandidateWorkoutExercise,
    CandidateWorkoutExplanation,
    CandidateWorkoutPlan,
    WorkoutContext,
    WorkoutExplanationRuntimeMetadata,
    WorkoutPlanRuntimeMetadata,
)
from services.coaching_decision_service import build_coaching_decision
from services.exercise_catalog_service import (
    find_catalog_entry_by_name,
    get_exercise_catalog,
)
from services.training_constraint_service import build_training_constraints
from services.training_execution_summary_service import build_training_execution_summary
from services.workout_constraint_service import build_workout_constraints

WorkoutCandidateProvider = Callable[[WorkoutContext], str]
WorkoutExplanationProvider = Callable[[ApprovedWorkoutPlan, WorkoutContext], str]
WORKOUT_CANDIDATE_PROVIDER_ENV = "WORKOUT_CANDIDATE_PROVIDER"
WORKOUT_EXPLANATION_PROVIDER_ENV = "WORKOUT_EXPLANATION_PROVIDER"
WORKOUT_PROVIDER_DETERMINISTIC = "deterministic"
WORKOUT_PROVIDER_CREWAI = "crewai"
CREWAI_WORKOUT_MODEL_ENV = "CREWAI_WORKOUT_MODEL"
OLLAMA_BASE_URL_ENV = "OLLAMA_BASE_URL"
CREWAI_WORKOUT_DISABLE_THINKING_ENV = "CREWAI_WORKOUT_DISABLE_THINKING"
CREWAI_WORKOUT_JSON_RESPONSE_FORMAT_ENV = "CREWAI_WORKOUT_JSON_RESPONSE_FORMAT"
CREWAI_WORKOUT_DEFAULT_MODEL = "ollama/qwen3:8b"
CREWAI_WORKOUT_DEFAULT_BASE_URL = "http://localhost:11434"

logger = logging.getLogger(__name__)

FALLBACK_REASON_DETERMINISTIC_SELECTED = "deterministic_selected"
FALLBACK_REASON_INVALID_PROVIDER = "invalid_provider"
FALLBACK_REASON_PROVIDER_EXCEPTION = "provider_exception"
FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT = "provider_non_string_output"
FALLBACK_REASON_MALFORMED_JSON = "malformed_json"
FALLBACK_REASON_SCHEMA_MISMATCH = "schema_mismatch"
FALLBACK_REASON_INVALID_CONFIDENCE = "invalid_confidence"
FALLBACK_REASON_VALIDATION_FAILURE = "validation_failure"

CANDIDATE_PARSE_STATUS_SUCCESS = "success"
CANDIDATE_PARSE_STATUS_FAILED = "failed"
CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED = "not_attempted"
CANDIDATE_VALIDATION_STATUS_SUCCESS = "success"
CANDIDATE_VALIDATION_STATUS_FAILED = "failed"
CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED = "not_attempted"
FINAL_PLAN_SOURCE_DETERMINISTIC = "deterministic"
FINAL_PLAN_SOURCE_CREWAI_APPROVED = "crewai_approved"
FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"
FINAL_EXPLANATION_SOURCE_DETERMINISTIC = "deterministic"
FINAL_EXPLANATION_SOURCE_CREWAI_APPROVED = "crewai_approved"
FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"
RAW_OUTPUT_PREVIEW_LIMIT = 240
ALLOWED_CATALOG_CONTEXT_LIMIT = 12

_CONFIDENCE_RANK = {"Limited": 0, "Low": 1, "Moderate": 2, "High": 3}

_INTERNAL_DEBUG_TERMS = [
    "guardrail",
    "guardrails",
    "validation",
    "validator",
    "fallback",
    "deterministic",
    "backend",
    "schema",
    "source of truth",
    "reason code",
    "reason codes",
    "debug",
    "internal",
    "candidateworkoutplan",
    "approvedworkoutplan",
    "workoutcontext",
    "trainingconstraints",
    "workoutconstraints",
    "coachingdecision",
    "data_quality_limited",
    "aligned_managed",
    "recovery_limited",
    "nutrition_training_mismatch",
    "improving_after_deload",
]

_RECOVERY_LIMITED_FORBIDDEN_TERMS = [
    "max effort",
    "max-effort",
    "all-out",
    "to failure",
]

_ALIGNED_MANAGED_FORBIDDEN_TERMS = [
    "deload",
    "reduce intensity",
    "reduce training",
    "cut volume",
    "back off",
]

_DATA_QUALITY_FORBIDDEN_TERMS = [
    "overtraining",
    "stalled progress",
    "stalled weight loss",
    "stalled fat loss",
    "likely caused",
    "likely causing",
    "likely contribute",
]


_ALLOWED_WORKOUT_PLAN_FIELDS = {
    "title",
    "session_focus",
    "duration_minutes",
    "exercises",
    "warmup",
    "cooldown",
    "progression_guidance",
    "rationale",
    "confidence",
}

_ALLOWED_WORKOUT_EXERCISE_FIELDS = {
    "exercise_name",
    "catalog_exercise_id",
    "movement_pattern",
    "target_zone",
    "sets",
    "reps_min",
    "reps_max",
    "target_rir_min",
    "target_rir_max",
    "required_equipment",
    "notes",
}

_REQUIRED_WORKOUT_PLAN_FIELDS = {
    "title",
    "session_focus",
    "duration_minutes",
    "exercises",
    "warmup",
    "cooldown",
    "progression_guidance",
    "rationale",
    "confidence",
}

_REQUIRED_WORKOUT_EXERCISE_FIELDS = {
    "exercise_name",
    "movement_pattern",
    "sets",
    "reps_min",
    "reps_max",
    "target_rir_min",
    "target_rir_max",
    "required_equipment",
    "notes",
}

_ALLOWED_CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

_ALLOWED_WORKOUT_EXPLANATION_FIELDS = {
    "session_summary",
    "why_this_fits_today",
    "focus_cue",
    "recovery_context",
    "nutrition_or_logging_context",
    "confidence",
}

_REQUIRED_WORKOUT_EXPLANATION_FIELDS = set(_ALLOWED_WORKOUT_EXPLANATION_FIELDS)

_WORKOUT_EXPLANATION_FORBIDDEN_TERMS = [
    "overtraining",
    "stalled progress",
    "stalled weight loss",
    "stalled fat loss",
    "poor adherence",
    "lack of discipline",
    "failed programming",
    "automatic deload",
    "required deload",
    "must deload",
    "automatic load increase",
    "increase load automatically",
    "add weight automatically",
    "injury diagnosis",
    "diagnose",
    "medical",
    "pain means injury",
    "calorie target",
    "macro target",
    "protein target",
    "carb target",
    "fat target",
    "replace the exercise",
    "swap the exercise",
    "change the exercise",
    "add an exercise",
    "remove the exercise",
]

_EXPLANATION_PRESCRIPTION_CHANGE_TERMS = [
    "change your sets",
    "change sets",
    "change your reps",
    "change reps",
    "change your rir",
    "change rir",
    "different exercise",
    "instead of the approved",
    "ignore the approved",
    "override the plan",
]

_WORKOUT_CANDIDATE_FORBIDDEN_TERMS = [
    "overtraining",
    "stalled progress",
    "stalled weight loss",
    "stalled fat loss",
    "automatic deload",
    "required deload",
    "must deload",
    "automatic load increase",
    "increase load automatically",
    "add weight automatically",
    "injury diagnosis",
    "diagnose",
    "medical",
    "pain means injury",
]


def _normalize_equipment(equipment: str) -> str:
    return equipment.strip().lower().replace(" ", "_")


def _text_blob(plan: CandidateWorkoutPlan) -> str:
    exercise_text = " ".join(
        f"{exercise.name} {exercise.notes}" for exercise in plan.exercises
    )
    return " ".join(
        [
            plan.title,
            plan.session_focus,
            plan.warmup,
            plan.cooldown,
            plan.progression_guidance,
            plan.rationale,
            exercise_text,
        ]
    ).lower()


def build_workout_context(health_state: UserHealthState) -> WorkoutContext:
    coaching_decision = build_coaching_decision(health_state)
    training_constraints = build_training_constraints(health_state, coaching_decision)
    workout_constraints = build_workout_constraints(health_state)

    return WorkoutContext(
        user_id=health_state.user_id,
        scenario=coaching_decision.scenario,
        primary_goal=health_state.primary_goal,
        training_load=health_state.training_state.training_load,
        recovery_demand=health_state.training_state.recovery_demand,
        avg_rir=health_state.training_state.avg_rir,
        workout_count=health_state.training_state.workout_count,
        training_constraints=training_constraints,
        workout_constraints=workout_constraints,
        confidence=coaching_decision.confidence,
        reason_codes=list(
            dict.fromkeys(
                coaching_decision.reason_codes
                + training_constraints.reason_codes
                + workout_constraints.reason_codes
            )
        ),
    )


def _movement_pattern_targets_for_context(context: WorkoutContext) -> list[str]:
    if context.scenario == "recovery_limited":
        return ["hinge", "horizontal_push", "horizontal_pull", "core"]

    if context.scenario == "nutrition_training_mismatch":
        return ["squat", "horizontal_push", "horizontal_pull", "core"]

    if context.scenario == "improving_after_deload":
        return ["hinge", "vertical_push", "vertical_pull", "core"]

    if context.scenario == "data_quality_limited":
        return ["squat", "horizontal_push", "horizontal_pull", "core"]

    return [
        "squat",
        "hinge",
        "lunge",
        "horizontal_push",
        "vertical_push",
        "horizontal_pull",
        "vertical_pull",
        "core",
        "carry",
        "conditioning",
    ]


def _compact_safety_constraints(context: WorkoutContext) -> list[str]:
    constraints = [
        "Use only provided exercises.",
        "Respect equipment and RIR bounds.",
        "Return JSON only; no markdown or commentary.",
    ]
    if context.scenario == "recovery_limited":
        constraints.append("Keep effort controlled; no max-effort language.")
    elif context.scenario == "nutrition_training_mismatch":
        constraints.append("Avoid aggressive conditioning.")
    elif context.scenario == "improving_after_deload":
        constraints.append("Use controlled progression.")
    elif context.scenario == "data_quality_limited":
        constraints.append(
            "Keep plan simple; no overtraining or stalled-progress claims."
        )
    elif context.scenario == "aligned_managed":
        constraints.append("Use normal variety; no deload framing.")
    return constraints


def _scenario_safety_constraints(context: WorkoutContext) -> list[str]:
    base_constraints = [
        "Exercises must come from allowed_exercises only.",
        "Required equipment must be currently available.",
        "Unavailable equipment must not be used.",
        "Target RIR must remain within TrainingConstraints.",
        "Do not include overtraining, stalled-progress, poor-adherence, medical, injury, automatic-deload, or automatic-load-increase claims.",
    ]

    scenario_constraints = {
        "recovery_limited": [
            "Keep effort controlled and avoid max-effort or failure language.",
            "Prefer manageable volume and recovery-aware exercise choices.",
        ],
        "aligned_managed": [
            "Use normal variety without deload or reduce-intensity framing unless constraints explicitly require it.",
        ],
        "nutrition_training_mismatch": [
            "Avoid aggressive conditioning volume while nutrition support is being reviewed.",
        ],
        "improving_after_deload": [
            "Use controlled progression and avoid aggressive ramping language.",
        ],
        "data_quality_limited": [
            "Keep the plan simple and manageable while logging quality improves.",
            "Do not claim overtraining, stalled progress, or failed programming.",
        ],
    }
    return base_constraints + scenario_constraints.get(context.scenario, [])


def _catalog_entry_allowed_for_context(entry, context: WorkoutContext) -> bool:
    catalog_equipment = _normalize_required_equipment(entry.equipment_required)
    if not _equipment_allowed(catalog_equipment, context.workout_constraints):
        return False

    avoid_movements = {
        movement.strip().lower()
        for movement in context.workout_constraints.avoid_movements
        + context.workout_constraints.movement_restrictions
        if movement.strip()
    }
    return entry.movement_pattern not in avoid_movements


def _allowed_catalog_exercise_slice(context: WorkoutContext) -> list[dict[str, Any]]:
    target_patterns = _movement_pattern_targets_for_context(context)
    target_pattern_set = set(target_patterns)
    scored_entries: list[tuple[int, dict[str, Any]]] = []

    for index, entry in enumerate(get_exercise_catalog()):
        if not _catalog_entry_allowed_for_context(entry, context):
            continue

        score = 1000 - index
        if entry.movement_pattern in target_pattern_set:
            score += 250
        score += _difficulty_score(entry.difficulty, context.workout_constraints)

        equipment = {_normalize_equipment(item) for item in entry.equipment_required}
        if _is_home_gym_like(context.workout_constraints):
            score += 10 * len(
                equipment
                & {
                    "barbell",
                    "cable",
                    "dumbbell",
                    "ez_bar",
                    "pull_up_bar",
                    "resistance_band",
                    "rope_cable_attachment",
                }
            )

        scored_entries.append(
            (
                score,
                {
                    "catalog_exercise_id": entry.id,
                    "exercise_name": entry.name,
                    "movement_pattern": entry.movement_pattern,
                    "required_equipment": [
                        _normalize_equipment(item) for item in entry.equipment_required
                    ],
                    "target_zone": (
                        "core"
                        if entry.movement_pattern.startswith("core")
                        else (
                            "conditioning"
                            if entry.movement_pattern == "conditioning"
                            else (
                                "carry" if entry.movement_pattern == "carry" else "main"
                            )
                        )
                    ),
                },
            )
        )

    scored_entries.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in scored_entries[:ALLOWED_CATALOG_CONTEXT_LIMIT]]


def workout_context_to_llm_json(context: WorkoutContext) -> dict[str, Any]:
    """Build the compact, LLM-safe workout context for a candidate provider.

    The runtime provider only needs a small planning brief, a bounded exercise
    list, and the required JSON shape.  This intentionally excludes raw
    actual-set rows, raw notes, unbounded workout history, internal debug
    payloads, backend-only metadata, and verbose architecture details.
    """

    training_constraints = context.training_constraints
    rir_min = training_constraints.recommended_rir_min or 2
    rir_max = training_constraints.recommended_rir_max or 4

    return {
        "scenario": context.scenario,
        "confidence": context.confidence,
        "allowed_rir_range": {
            "target_rir_min": rir_min,
            "target_rir_max": rir_max,
        },
        "exercise_count": {"min": 3, "target": 4, "max": 5},
        "duration_minutes": {"min": 30, "target": 45, "max": 60},
        "available_equipment": list(context.workout_constraints.available_equipment),
        "unavailable_equipment": list(
            context.workout_constraints.unavailable_equipment
        ),
        "movement_pattern_targets": _movement_pattern_targets_for_context(context)[:6],
        "allowed_exercises": _allowed_catalog_exercise_slice(context),
        "execution_summary": {
            "completed_execution_count": build_training_execution_summary(
                context.user_id
            ).completed_execution_count,
        },
        "safety_constraints": _compact_safety_constraints(context),
        "required_top_level_keys": [
            "title",
            "session_focus",
            "duration_minutes",
            "exercises",
            "warmup",
            "cooldown",
            "progression_guidance",
            "rationale",
            "confidence",
        ],
        "required_exercise_keys": [
            "exercise_name",
            "catalog_exercise_id",
            "movement_pattern",
            "target_zone",
            "sets",
            "reps_min",
            "reps_max",
            "target_rir_min",
            "target_rir_max",
            "required_equipment",
            "notes",
        ],
    }


def _equipment_allowed(
    equipment_required: list[str], workout_constraints: WorkoutConstraints
) -> bool:
    if not equipment_required:
        return True

    required = {_normalize_equipment(item) for item in equipment_required}
    available = {
        _normalize_equipment(item) for item in workout_constraints.available_equipment
    }
    unavailable = {
        _normalize_equipment(item) for item in workout_constraints.unavailable_equipment
    }

    if required & unavailable:
        return False

    if available and not required.issubset(available):
        return False

    return True


def _catalog_equipment_for_option(
    name: str,
    fallback_equipment_required: list[str],
) -> tuple[str, list[str]]:
    catalog_entry = find_catalog_entry_by_name(name)
    if catalog_entry is None:
        return name, [
            _normalize_equipment(item) for item in fallback_equipment_required
        ]

    return (
        catalog_entry.name,
        [_normalize_equipment(item) for item in catalog_entry.equipment_required],
    )


def _normalize_exercise_name(name: str) -> str:
    return name.strip().lower().replace("-", " ").replace("_", " ")


def _recent_exercise_names(workout_constraints: WorkoutConstraints) -> set[str]:
    return set(_recent_exercise_counts(workout_constraints))


def _recent_exercise_counts(workout_constraints: WorkoutConstraints) -> dict[str, int]:
    counts: dict[str, int] = {}
    for name in workout_constraints.recent_exercises:
        if not name:
            continue
        normalized = _normalize_exercise_name(name)
        counts[normalized] = counts.get(normalized, 0) + 1
    return counts


def _most_recent_plan_names(
    workout_constraints: WorkoutConstraints, slot_count: int = 4
) -> set[str]:
    """Return normalized names from the most recent selected workout plan.

    build_workout_constraints() orders selected-plan exercises newest-first and
    preserves duplicates. The first four names therefore represent the most
    recent generated plan for the current deterministic preview flow.
    """

    return {
        _normalize_exercise_name(name)
        for name in workout_constraints.recent_exercises[:slot_count]
        if name
    }


def _recent_history_depth(workout_constraints: WorkoutConstraints) -> int:
    return len([name for name in workout_constraints.recent_exercises if name])


def _recent_movement_patterns(workout_constraints: WorkoutConstraints) -> set[str]:
    return set(_recent_movement_pattern_counts(workout_constraints))


def _recent_movement_pattern_counts(
    workout_constraints: WorkoutConstraints,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for name in workout_constraints.recent_exercises:
        catalog_entry = find_catalog_entry_by_name(name)
        if catalog_entry is not None:
            counts[catalog_entry.movement_pattern] = (
                counts.get(catalog_entry.movement_pattern, 0) + 1
            )
    return counts


def _equipment_modality(equipment_required: list[str]) -> str:
    equipment = {_normalize_equipment(item) for item in equipment_required}
    if equipment == {"bodyweight"}:
        return "bodyweight"

    for modality in [
        "barbell",
        "dumbbell",
        "cable",
        "pull_up_bar",
        "resistance_band",
        "ez_bar",
        "kettlebell",
        "treadmill",
        "bike",
        "exercise_ball",
        "machine",
    ]:
        if modality in equipment:
            return modality

    if equipment:
        return sorted(equipment)[0]
    return "unknown"


def _recent_equipment_modality_counts(
    workout_constraints: WorkoutConstraints,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for name in workout_constraints.recent_exercises:
        catalog_entry = find_catalog_entry_by_name(name)
        if catalog_entry is None:
            continue
        modality = _equipment_modality(catalog_entry.equipment_required)
        counts[modality] = counts.get(modality, 0) + 1
    return counts


def _stable_rotation_index(seed: str, count: int, user_id: int | None = None) -> int:
    if count <= 1:
        return 0
    user_offset = user_id or 0
    seed_offset = sum((index + 1) * ord(char) for index, char in enumerate(seed))
    return (user_offset + seed_offset) % count


def _selection_slot_key(options: list[tuple[str, list[str]]]) -> str:
    catalog_patterns: list[str] = []
    for name, _equipment_required in options[:4]:
        catalog_entry = find_catalog_entry_by_name(name)
        if catalog_entry is not None:
            catalog_patterns.append(catalog_entry.movement_pattern)
    return "|".join(catalog_patterns or [name for name, _ in options[:4]])


def _is_home_gym_like(workout_constraints: WorkoutConstraints) -> bool:
    available = {
        _normalize_equipment(item) for item in workout_constraints.available_equipment
    }
    return bool(
        available
        & {
            "barbell",
            "cable",
            "dumbbell",
            "ez_bar",
            "pull_up_bar",
            "resistance_band",
        }
    )


def _difficulty_score(
    difficulty: str | None, workout_constraints: WorkoutConstraints
) -> int:
    normalized = (difficulty or "intermediate").strip().lower()
    if workout_constraints.confidence == "Low":
        return {"beginner": 12, "intermediate": 2, "advanced": -18}.get(normalized, 0)

    return {"beginner": 2, "intermediate": 12, "advanced": 4}.get(normalized, 0)


def _option_score(
    name: str,
    equipment_required: list[str],
    workout_constraints: WorkoutConstraints,
    option_index: int,
    recent_name_counts: dict[str, int],
    recent_pattern_counts: dict[str, int],
    recent_modality_counts: dict[str, int],
    most_recent_plan_names: set[str],
) -> int:
    catalog_entry = find_catalog_entry_by_name(name)
    catalog_name, normalized_equipment = _catalog_equipment_for_option(
        name, equipment_required
    )
    score = 1000 - (option_index * 4)

    normalized_name = _normalize_exercise_name(catalog_name)
    recent_name_count = recent_name_counts.get(normalized_name, 0)
    if recent_name_count:
        score -= 700 + (220 * (recent_name_count - 1))
    else:
        score += 35

    if normalized_name in most_recent_plan_names:
        score -= 950

    if catalog_entry is not None:
        recent_pattern_count = recent_pattern_counts.get(
            catalog_entry.movement_pattern, 0
        )
        if recent_pattern_count:
            score -= min(recent_pattern_count, 4) * 85
        score += _difficulty_score(catalog_entry.difficulty, workout_constraints)

    equipment = set(normalized_equipment)
    modality = _equipment_modality(normalized_equipment)
    recent_modality_count = recent_modality_counts.get(modality, 0)
    if recent_modality_count:
        score -= min(recent_modality_count, 5) * 45

    if "machine" in equipment:
        score -= 90

    if _is_home_gym_like(workout_constraints):
        score += 12 * len(
            equipment
            & {
                "barbell",
                "cable",
                "dumbbell",
                "ez_bar",
                "pull_up_bar",
                "resistance_band",
                "rope_cable_attachment",
                "treadmill",
                "bike",
                "exercise_ball",
            }
        )
        if equipment == {"bodyweight"}:
            score -= 8

    return score


def _select_from_rotated_top_options(
    allowed_options: list[tuple[int, str, list[str]]],
    *,
    user_id: int | None,
    slot_key: str,
    recent_name_counts: dict[str, int],
    most_recent_plan_names: set[str],
    history_depth: int,
) -> tuple[str, list[str]]:
    ranked = sorted(allowed_options, key=lambda item: item[0], reverse=True)
    best_score = ranked[0][0]
    top_options = [item for item in ranked[:5] if best_score - item[0] <= 180]

    primary_slot_pattern = (slot_key or "").split("|", 1)[0]
    if primary_slot_pattern:
        same_pattern_options = []
        for item in top_options:
            _score, option_name, _equipment_required = item
            catalog_entry = find_catalog_entry_by_name(option_name)
            if (
                catalog_entry is not None
                and catalog_entry.movement_pattern == primary_slot_pattern
            ):
                same_pattern_options.append(item)
        if same_pattern_options:
            top_options = same_pattern_options

    if most_recent_plan_names and len(top_options) > 1:
        non_recent_options = [
            item
            for item in top_options
            if _normalize_exercise_name(item[1]) not in most_recent_plan_names
        ]
        if non_recent_options:
            top_options = non_recent_options

    if user_id is None or len(top_options) <= 1:
        _score, name, equipment_required = top_options[0]
        return name, equipment_required

    recent_seed = "|".join(
        f"{name}:{count}" for name, count in sorted(recent_name_counts.items())[:16]
    )
    rotation_seed = f"{slot_key}:{history_depth}:{recent_seed}"
    rotation_index = _stable_rotation_index(
        rotation_seed, len(top_options), user_id=user_id
    )
    _score, name, equipment_required = top_options[rotation_index]
    return name, equipment_required


def _select_exercise(
    workout_constraints: WorkoutConstraints,
    options: list[tuple[str, list[str]]],
    *,
    user_id: int | None = None,
    slot_key: str | None = None,
) -> tuple[str, list[str]]:
    allowed_options: list[tuple[int, str, list[str]]] = []
    recent_name_counts = _recent_exercise_counts(workout_constraints)
    recent_pattern_counts = _recent_movement_pattern_counts(workout_constraints)
    recent_modality_counts = _recent_equipment_modality_counts(workout_constraints)
    most_recent_plan_names = _most_recent_plan_names(workout_constraints)
    history_depth = _recent_history_depth(workout_constraints)

    for index, (name, equipment_required) in enumerate(options):
        catalog_name, catalog_equipment_required = _catalog_equipment_for_option(
            name,
            equipment_required,
        )
        if _equipment_allowed(catalog_equipment_required, workout_constraints):
            allowed_options.append(
                (
                    _option_score(
                        name,
                        equipment_required,
                        workout_constraints,
                        index,
                        recent_name_counts,
                        recent_pattern_counts,
                        recent_modality_counts,
                        most_recent_plan_names,
                    ),
                    catalog_name,
                    catalog_equipment_required,
                )
            )

    if allowed_options:
        return _select_from_rotated_top_options(
            allowed_options,
            user_id=user_id,
            slot_key=slot_key or _selection_slot_key(options),
            recent_name_counts=recent_name_counts,
            most_recent_plan_names=most_recent_plan_names,
            history_depth=history_depth,
        )

    name, equipment_required = options[-1]
    return _catalog_equipment_for_option(name, equipment_required)


def _prefer_alternate_template(context: WorkoutContext) -> bool:
    recent_patterns = _recent_movement_patterns(context.workout_constraints)
    return bool(
        {"hinge", "vertical_push", "vertical_pull"}.issubset(recent_patterns)
        or {"squat", "horizontal_push", "horizontal_pull"}.issubset(recent_patterns)
    )


def _exercise(
    name: str,
    sets: int,
    reps_min: int,
    reps_max: int,
    rir_min: int,
    rir_max: int,
    notes: str,
    equipment_required: list[str],
) -> CandidateWorkoutExercise:
    return CandidateWorkoutExercise(
        name=name,
        sets=sets,
        reps_min=reps_min,
        reps_max=reps_max,
        rir_min=rir_min,
        rir_max=rir_max,
        notes=notes,
        equipment_required=[_normalize_equipment(item) for item in equipment_required],
    )


def _exercise_from_options(
    context: WorkoutContext,
    options: list[tuple[str, list[str]]],
    sets: int,
    reps_min: int,
    reps_max: int,
    rir_min: int,
    rir_max: int,
    notes: str,
) -> CandidateWorkoutExercise:
    name, equipment_required = _select_exercise(
        context.workout_constraints,
        options,
        user_id=context.user_id,
        slot_key=_selection_slot_key(options),
    )
    return _exercise(
        name,
        sets,
        reps_min,
        reps_max,
        rir_min,
        rir_max,
        notes,
        equipment_required,
    )


def generate_candidate_workout_plan(context: WorkoutContext) -> CandidateWorkoutPlan:
    constraints = context.training_constraints
    rir_min = constraints.recommended_rir_min or 2
    rir_max = constraints.recommended_rir_max or 4

    if context.scenario == "recovery_limited":
        return CandidateWorkoutPlan(
            title="Recovery-Aware Strength Session",
            session_focus="Maintain movement quality while reducing recovery cost.",
            duration_minutes=40,
            exercises=[
                _exercise_from_options(
                    context,
                    [
                        ("Goblet Squat", ["dumbbell"]),
                        ("Dumbbell Split Squat", ["dumbbell"]),
                        ("Stability Ball Wall Squat", ["exercise_ball"]),
                        ("Reverse Lunge", ["bodyweight"]),
                        ("Bodyweight Squat", ["bodyweight"]),
                        ("Leg Press", ["machine"]),
                    ],
                    3,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Use a controlled tempo and stop with reps in reserve.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Dumbbell Floor Press", ["dumbbell"]),
                        ("Dumbbell Bench Press", ["dumbbell"]),
                        ("Band Resisted Push-Up", ["bodyweight", "resistance_band"]),
                        ("Push-Up", ["bodyweight"]),
                        ("Machine Chest Press", ["machine"]),
                    ],
                    3,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Keep effort moderate and avoid grinding reps.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Band Row", ["resistance_band"]),
                        ("Cable Row", ["cable"]),
                        ("One-Arm Dumbbell Row", ["dumbbell"]),
                        ("Chest-Supported Row", ["dumbbell"]),
                        ("Inverted Row", ["bodyweight"]),
                        ("Machine Row", ["machine"]),
                    ],
                    3,
                    10,
                    12,
                    rir_min,
                    rir_max,
                    "Prioritize smooth reps and steady breathing.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Bird Dog", ["bodyweight"]),
                        ("Band Face Pull", ["resistance_band"]),
                        ("Stability Ball Dead Bug", ["exercise_ball"]),
                        ("Dead Bug", ["bodyweight"]),
                        ("Bike Recovery Ride", ["bike"]),
                        ("Farmer Carry", ["dumbbell"]),
                    ],
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Keep this easy and restorative; it should feel light.",
                ),
            ],
            warmup="Start with 5-8 minutes of easy cardio and light ramp-up sets.",
            cooldown="Finish with easy walking and relaxed mobility work.",
            progression_guidance=constraints.low_rir_guidance,
            rationale=(
                "Recovery markers suggest the session should preserve consistency "
                "without adding aggressive training stress."
            ),
            confidence=context.confidence,
        )

    if context.scenario == "nutrition_training_mismatch":
        return CandidateWorkoutPlan(
            title="Controlled Strength Practice",
            session_focus="Train productively while nutrition support is reviewed.",
            duration_minutes=45,
            exercises=[
                _exercise_from_options(
                    context,
                    [
                        ("Dumbbell RDL", ["dumbbell"]),
                        ("Cable Pull-Through", ["cable", "rope_cable_attachment"]),
                        ("Stability Ball Hamstring Curl", ["exercise_ball"]),
                        ("Goblet Squat", ["dumbbell"]),
                        ("Reverse Lunge", ["bodyweight"]),
                        ("Bodyweight Squat", ["bodyweight"]),
                        ("Leg Press", ["machine"]),
                    ],
                    3,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Keep the final reps controlled and repeatable.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Incline Dumbbell Press", ["dumbbell"]),
                        ("Dumbbell Floor Press", ["dumbbell"]),
                        ("Single-Arm Cable Press", ["cable"]),
                        ("Push-Up", ["bodyweight"]),
                        ("Machine Chest Press", ["machine"]),
                    ],
                    3,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Use a load that allows consistent technique.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Cable Lat Pulldown", ["cable"]),
                        ("Band Lat Pulldown", ["resistance_band"]),
                        ("Cable Row", ["cable"]),
                        ("Dumbbell Row", ["dumbbell"]),
                        ("Inverted Row", ["bodyweight"]),
                    ],
                    3,
                    10,
                    12,
                    rir_min,
                    rir_max,
                    "Stop before form breaks down.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Cable Woodchop", ["cable"]),
                        ("Band Pallof Press", ["resistance_band"]),
                        ("Dead Bug", ["bodyweight"]),
                        ("Band Face Pull", ["resistance_band"]),
                        ("Bike Steady State", ["bike"]),
                    ],
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    (
                        "Keep the accessory work low-to-moderate while nutrition "
                        "support is clarified."
                    ),
                ),
            ],
            warmup="Use progressive warm-up sets before the first two movements.",
            cooldown="Log performance, effort, and post-workout energy.",
            progression_guidance=constraints.progression_guidance,
            rationale=(
                "Training can continue, but progression should stay controlled "
                "while nutrition support is clarified."
            ),
            confidence=context.confidence,
        )

    if context.scenario == "improving_after_deload":
        return CandidateWorkoutPlan(
            title="Controlled Progression Session",
            session_focus="Build on the improving trend without ramping too quickly.",
            duration_minutes=50,
            exercises=[
                _exercise_from_options(
                    context,
                    [
                        ("Romanian Deadlift", ["barbell"]),
                        ("Barbell Squat", ["barbell"]),
                        ("Dumbbell Split Squat", ["dumbbell"]),
                        ("Dumbbell Single-Leg RDL", ["dumbbell"]),
                        ("Goblet Squat", ["dumbbell"]),
                        ("Bodyweight Squat", ["bodyweight"]),
                        ("Leg Press", ["machine"]),
                    ],
                    3,
                    5,
                    8,
                    rir_min,
                    rir_max,
                    "Use a conservative load and leave room to progress next session.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Overhead Press", ["barbell"]),
                        ("Dumbbell Shoulder Press", ["dumbbell"]),
                        ("Dumbbell Bench Press", ["dumbbell"]),
                        ("Barbell Bench Press", ["barbell"]),
                        ("Dumbbell Floor Press", ["dumbbell"]),
                        ("Push-Up", ["bodyweight"]),
                    ],
                    3,
                    6,
                    8,
                    rir_min,
                    rir_max,
                    "Keep speed consistent across sets.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Pull-Up", ["pull_up_bar"]),
                        ("Cable Lat Pulldown", ["cable"]),
                        ("Cable High Row", ["cable"]),
                        ("Cable Row", ["cable"]),
                        ("Barbell Row", ["barbell"]),
                        ("Dumbbell Row", ["dumbbell"]),
                        ("Band Row", ["resistance_band"]),
                        ("Inverted Row", ["bodyweight"]),
                    ],
                    3,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Keep reps crisp and avoid forcing load jumps.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Farmer Carry", ["dumbbell"]),
                        ("Suitcase Carry", ["dumbbell"]),
                        ("Cable Pallof Press", ["cable"]),
                        ("Cable Woodchop", ["cable"]),
                        ("EZ-Bar Curl", ["ez_bar"]),
                        ("Stability Ball Rollout", ["exercise_ball"]),
                        ("Dead Bug", ["bodyweight"]),
                    ],
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Use controlled accessory work and avoid turning it into a ramp-up test.",
                ),
            ],
            warmup="Ramp gradually and keep early sets easy.",
            cooldown="Record soreness, energy, and performance after training.",
            progression_guidance=constraints.progression_guidance,
            rationale=(
                "Recent improvement supports training, but the next step should be "
                "gradual rather than a fast return to frequent high-effort work."
            ),
            confidence=context.confidence,
        )

    if context.scenario == "data_quality_limited":
        return CandidateWorkoutPlan(
            title="Manageable Baseline Session",
            session_focus="Keep training simple while logging quality improves.",
            duration_minutes=35,
            exercises=[
                _exercise_from_options(
                    context,
                    [
                        ("Goblet Squat", ["dumbbell"]),
                        ("Leg Press", ["machine"]),
                        ("Bodyweight Squat", ["bodyweight"]),
                    ],
                    2,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Choose a comfortable load and focus on repeatable movement.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Push-Up", ["bodyweight"]),
                        ("Dumbbell Shoulder Press", ["dumbbell"]),
                        ("Machine Chest Press", ["machine"]),
                    ],
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Use a variation that feels controlled today.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Cable Row", ["cable"]),
                        ("Dumbbell Row", ["dumbbell"]),
                        ("Machine Row", ["machine"]),
                        ("Inverted Row", ["bodyweight"]),
                    ],
                    2,
                    10,
                    12,
                    rir_min,
                    rir_max,
                    "Keep effort manageable and log how the session feels.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Dead Bug", ["bodyweight"]),
                        ("Treadmill Walk", ["treadmill"]),
                        ("Bike Steady State", ["bike"]),
                        ("Band Pull-Apart", ["resistance_band"]),
                    ],
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Keep this simple and manageable so the session is easy to log consistently.",
                ),
            ],
            warmup="Start with easy movement and one light practice set per exercise.",
            cooldown="Log exercise, sets, reps, load, RIR, soreness, and energy.",
            progression_guidance=constraints.progression_guidance,
            rationale=(
                "Data quality limits confidence, so the session should establish a "
                "clear baseline before stronger training conclusions are made."
            ),
            confidence=context.confidence,
        )

    alternate_template = _prefer_alternate_template(context)
    lower_body_options = (
        [
            ("Romanian Deadlift", ["barbell"]),
            ("Dumbbell Single-Leg RDL", ["dumbbell"]),
            ("Front Squat", ["barbell"]),
            ("Goblet Squat", ["dumbbell"]),
            ("Stability Ball Wall Squat", ["exercise_ball"]),
            ("Bodyweight Squat", ["bodyweight"]),
            ("Leg Press", ["machine"]),
        ]
        if alternate_template
        else [
            ("Romanian Deadlift", ["barbell"]),
            ("Dumbbell Single-Leg RDL", ["dumbbell"]),
            ("Cable Pull-Through", ["cable", "rope_cable_attachment"]),
            ("Barbell Squat", ["barbell"]),
            ("Goblet Squat", ["dumbbell"]),
            ("Bodyweight Squat", ["bodyweight"]),
            ("Leg Press", ["machine"]),
        ]
    )
    push_options = (
        [
            ("Barbell Bench Press", ["barbell"]),
            ("Dumbbell Bench Press", ["dumbbell"]),
            ("Dumbbell Floor Press", ["dumbbell"]),
            ("Single-Arm Cable Press", ["cable"]),
            ("Push-Up", ["bodyweight"]),
        ]
        if alternate_template
        else [
            ("Overhead Press", ["barbell"]),
            ("Dumbbell Shoulder Press", ["dumbbell"]),
            ("Arnold Press", ["dumbbell"]),
            ("Barbell Bench Press", ["barbell"]),
            ("Push-Up", ["bodyweight"]),
        ]
    )
    pull_options = (
        [
            ("Cable Row", ["cable"]),
            ("Barbell Row", ["barbell"]),
            ("One-Arm Dumbbell Row", ["dumbbell", "adjustable_bench"]),
            ("Dumbbell Row", ["dumbbell"]),
            ("Band Row", ["resistance_band"]),
            ("Inverted Row", ["bodyweight"]),
        ]
        if alternate_template
        else [
            ("Pull-Up", ["pull_up_bar"]),
            ("Chin-Up", ["pull_up_bar"]),
            ("Cable Lat Pulldown", ["cable"]),
            ("Band Lat Pulldown", ["resistance_band"]),
            ("Cable Row", ["cable"]),
            ("Inverted Row", ["bodyweight"]),
        ]
    )
    accessory_options = (
        [
            ("Cable Woodchop", ["cable"]),
            ("Cable Pallof Press", ["cable"]),
            ("EZ-Bar Curl", ["ez_bar"]),
            ("Dumbbell Lateral Raise", ["dumbbell"]),
            ("Dead Bug", ["bodyweight"]),
        ]
        if alternate_template
        else [
            ("Farmer Carry", ["dumbbell"]),
            ("Suitcase Carry", ["dumbbell"]),
            ("Stability Ball Rollout", ["exercise_ball"]),
            ("Rope Face Pull", ["cable", "rope_cable_attachment"]),
            ("Dead Bug", ["bodyweight"]),
        ]
    )

    return CandidateWorkoutPlan(
        title="Gradual Progression Strength Session",
        session_focus="Maintain consistency and progress gradually.",
        duration_minutes=50,
        exercises=[
            _exercise_from_options(
                context,
                lower_body_options,
                3,
                5,
                8,
                rir_min,
                rir_max,
                "Add load only if the previous session felt stable.",
            ),
            _exercise_from_options(
                context,
                push_options,
                3,
                6,
                8,
                rir_min,
                rir_max,
                "Keep one or more clean reps in reserve on working sets.",
            ),
            _exercise_from_options(
                context,
                pull_options,
                3,
                8,
                10,
                rir_min,
                rir_max,
                "Progress gradually while recovery markers remain stable.",
            ),
            _exercise_from_options(
                context,
                accessory_options,
                2,
                8,
                12,
                rir_min,
                rir_max,
                "Use accessory work to round out the session without forcing progression.",
            ),
        ],
        warmup="Use 5-10 minutes of easy movement and progressive ramp-up sets.",
        cooldown="Log performance and recovery markers after the session.",
        progression_guidance=constraints.progression_guidance,
        rationale=(
            "Recovery, training, and available context support a normal gradual "
            "progression session."
        ),
        confidence=context.confidence,
    )


class WorkoutCandidateParseError(ValueError):
    """Raised when a CrewAI workout candidate cannot be parsed safely."""


def _normalize_required_equipment(values: list[str]) -> list[str]:
    return [_normalize_equipment(item) for item in values if str(item).strip()]


def _require_string(payload: dict, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise WorkoutCandidateParseError(f"Missing or invalid string field: {key}")
    return value.strip()


def _require_int(payload: dict, key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise WorkoutCandidateParseError(f"Missing or invalid integer field: {key}")
    return value


def _require_string_list(payload: dict, key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise WorkoutCandidateParseError(f"Missing or invalid string list field: {key}")
    return [item.strip() for item in value if item.strip()]


def _reject_unapproved_fields(
    payload: dict,
    allowed_fields: set[str],
    field_path: str,
) -> None:
    extra_fields = set(payload) - allowed_fields
    if extra_fields:
        formatted = ", ".join(sorted(extra_fields))
        raise WorkoutCandidateParseError(
            f"Unexpected field(s) in {field_path}: {formatted}"
        )


def parse_candidate_workout_plan_json(
    raw_output: str,
    *,
    strict: bool = True,
) -> CandidateWorkoutPlan:
    """Parse strict CandidateWorkoutPlan JSON from a provider output string.

    CrewAI workout generation is expected to return one JSON object only. Markdown
    wrappers and commentary are rejected here so the backend never has to guess at
    user-facing workout intent.
    """

    if not isinstance(raw_output, str) or not raw_output.strip():
        raise WorkoutCandidateParseError("Candidate workout output is empty.")

    stripped_output = raw_output.strip()
    if stripped_output.startswith("```") or stripped_output.endswith("```"):
        raise WorkoutCandidateParseError(
            "Candidate workout output must be raw JSON, not markdown."
        )

    try:
        payload = json.loads(stripped_output)
    except json.JSONDecodeError as exc:
        raise WorkoutCandidateParseError(
            "Malformed CandidateWorkoutPlan JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise WorkoutCandidateParseError("CandidateWorkoutPlan JSON must be an object.")

    missing_fields = _REQUIRED_WORKOUT_PLAN_FIELDS - set(payload)
    if missing_fields:
        formatted = ", ".join(sorted(missing_fields))
        raise WorkoutCandidateParseError(
            f"CandidateWorkoutPlan missing required field(s): {formatted}"
        )

    if strict:
        _reject_unapproved_fields(payload, _ALLOWED_WORKOUT_PLAN_FIELDS, "plan")

    confidence = _require_string(payload, "confidence")
    if confidence not in _ALLOWED_CONFIDENCE_VALUES:
        raise WorkoutCandidateParseError("CandidateWorkoutPlan confidence is invalid.")

    exercises_payload = payload.get("exercises")
    if not isinstance(exercises_payload, list) or not exercises_payload:
        raise WorkoutCandidateParseError(
            "CandidateWorkoutPlan exercises must be a non-empty list."
        )

    exercises: list[CandidateWorkoutExercise] = []
    for index, exercise_payload in enumerate(exercises_payload, start=1):
        if not isinstance(exercise_payload, dict):
            raise WorkoutCandidateParseError(f"Exercise {index} must be a JSON object.")

        missing_exercise_fields = _REQUIRED_WORKOUT_EXERCISE_FIELDS - set(
            exercise_payload
        )
        if missing_exercise_fields:
            formatted = ", ".join(sorted(missing_exercise_fields))
            raise WorkoutCandidateParseError(
                f"Exercise {index} missing required field(s): {formatted}"
            )

        if strict:
            _reject_unapproved_fields(
                exercise_payload,
                _ALLOWED_WORKOUT_EXERCISE_FIELDS,
                f"exercise {index}",
            )

        catalog_exercise_id = exercise_payload.get("catalog_exercise_id")
        if catalog_exercise_id is not None and (
            isinstance(catalog_exercise_id, bool)
            or not isinstance(catalog_exercise_id, int)
        ):
            raise WorkoutCandidateParseError(
                f"Exercise {index} catalog_exercise_id must be an integer when present."
            )

        exercises.append(
            CandidateWorkoutExercise(
                name=_require_string(exercise_payload, "exercise_name"),
                sets=_require_int(exercise_payload, "sets"),
                reps_min=_require_int(exercise_payload, "reps_min"),
                reps_max=_require_int(exercise_payload, "reps_max"),
                rir_min=_require_int(exercise_payload, "target_rir_min"),
                rir_max=_require_int(exercise_payload, "target_rir_max"),
                notes=_require_string(exercise_payload, "notes"),
                equipment_required=_normalize_required_equipment(
                    _require_string_list(exercise_payload, "required_equipment")
                ),
                catalog_exercise_id=catalog_exercise_id,
                movement_pattern=_require_string(exercise_payload, "movement_pattern"),
                target_zone=(
                    str(exercise_payload.get("target_zone")).strip()
                    if exercise_payload.get("target_zone") is not None
                    else None
                ),
            )
        )

    return CandidateWorkoutPlan(
        title=_require_string(payload, "title"),
        session_focus=_require_string(payload, "session_focus"),
        duration_minutes=_require_int(payload, "duration_minutes"),
        exercises=exercises,
        warmup=_require_string(payload, "warmup"),
        cooldown=_require_string(payload, "cooldown"),
        progression_guidance=_require_string(payload, "progression_guidance"),
        rationale=_require_string(payload, "rationale"),
        confidence=confidence,
    )


def _catalog_entry_for_candidate_exercise(exercise: CandidateWorkoutExercise):
    return find_catalog_entry_by_name(exercise.name)


def _catalog_validation_violations(
    exercise: CandidateWorkoutExercise,
    context: WorkoutContext,
) -> list[str]:
    violations: list[str] = []
    catalog_entry = _catalog_entry_for_candidate_exercise(exercise)
    if catalog_entry is None:
        return [f"{exercise.name} does not exist in the exercise catalog."]

    if (
        exercise.catalog_exercise_id is not None
        and catalog_entry.id is not None
        and exercise.catalog_exercise_id != catalog_entry.id
    ):
        violations.append(
            f"{exercise.name} catalog_exercise_id does not match the exercise catalog."
        )

    if (
        exercise.movement_pattern is not None
        and exercise.movement_pattern != catalog_entry.movement_pattern
    ):
        violations.append(
            f"{exercise.name} movement pattern must match the exercise catalog."
        )

    catalog_equipment = _normalize_required_equipment(catalog_entry.equipment_required)
    candidate_equipment = _normalize_required_equipment(exercise.equipment_required)
    if set(candidate_equipment) != set(catalog_equipment):
        violations.append(
            f"{exercise.name} required equipment must match the exercise catalog."
        )

    if not _equipment_allowed(catalog_equipment, context.workout_constraints):
        violations.append(
            f"{exercise.name} requires equipment outside current workout constraints."
        )

    avoid_movements = {
        movement.strip().lower()
        for movement in context.workout_constraints.avoid_movements
        + context.workout_constraints.movement_restrictions
        if movement.strip()
    }
    if catalog_entry.movement_pattern in avoid_movements:
        violations.append(
            f"{exercise.name} uses a movement pattern outside current constraints."
        )

    return violations


def build_approved_workout_plan_from_candidate_output(
    raw_output: str,
    context: WorkoutContext,
) -> ApprovedWorkoutPlan:
    """Parse/validate provider output, with deterministic fallback on failure."""

    return approve_workout_candidate_json_or_fallback(
        raw_output,
        context,
    )


def validate_candidate_workout_plan(
    candidate: CandidateWorkoutPlan,
    context: WorkoutContext,
) -> list[str]:
    violations: list[str] = []

    if not candidate.exercises:
        violations.append("Workout plan must include at least one exercise.")

    if len(candidate.exercises) < 3:
        violations.append("Workout plan must include at least three exercises.")

    if len(candidate.exercises) > 6:
        violations.append("Workout plan must not include more than six exercises.")

    if candidate.duration_minutes < 20 or candidate.duration_minutes > 90:
        violations.append("Workout plan duration must be realistic for a preview.")

    if _CONFIDENCE_RANK.get(candidate.confidence, -1) > _CONFIDENCE_RANK.get(
        context.confidence,
        -1,
    ):
        violations.append("Workout plan confidence must not exceed context confidence.")

    training_constraints = context.training_constraints
    for exercise in candidate.exercises:
        if exercise.sets < 1 or exercise.sets > 6:
            violations.append(f"Invalid set count for {exercise.name}.")

        if exercise.reps_min < 1 or exercise.reps_max < exercise.reps_min:
            violations.append(f"Invalid rep range for {exercise.name}.")

        if (
            exercise.rir_min < 0
            or exercise.rir_max > 5
            or exercise.rir_max < exercise.rir_min
        ):
            violations.append(f"Invalid RIR range for {exercise.name}.")

        if training_constraints.recommended_rir_min is not None:
            if exercise.rir_min < training_constraints.recommended_rir_min:
                violations.append(
                    f"{exercise.name} uses lower RIR than current constraints allow."
                )

        if training_constraints.recommended_rir_max is not None:
            if exercise.rir_max > training_constraints.recommended_rir_max:
                violations.append(
                    f"{exercise.name} uses higher RIR than current constraints allow."
                )

        violations.extend(_catalog_validation_violations(exercise, context))

    text = _text_blob(candidate)

    for term in _INTERNAL_DEBUG_TERMS:
        if term in text:
            violations.append("Workout plan contains internal/debug language.")
            break

    for term in _WORKOUT_CANDIDATE_FORBIDDEN_TERMS:
        if term in text:
            violations.append("Workout plan contains forbidden workout guidance.")
            break

    if context.scenario == "recovery_limited":
        for term in _RECOVERY_LIMITED_FORBIDDEN_TERMS:
            if term in text:
                violations.append(
                    "Recovery-limited workout plans must avoid max-effort language."
                )
                break

    if context.scenario == "aligned_managed":
        for term in _ALIGNED_MANAGED_FORBIDDEN_TERMS:
            if term in text:
                violations.append(
                    "Aligned workout plans must avoid unnecessary intervention framing."
                )
                break

    if context.scenario == "data_quality_limited":
        for term in _DATA_QUALITY_FORBIDDEN_TERMS:
            if term in text:
                violations.append(
                    "Data-quality-limited workout plans must avoid "
                    "overconfident claims."
                )
                break

    return violations


def approve_candidate_workout_plan(
    candidate: CandidateWorkoutPlan,
    context: WorkoutContext,
) -> ApprovedWorkoutPlan:
    violations = validate_candidate_workout_plan(candidate, context)
    if violations:
        raise ValueError(
            "CandidateWorkoutPlan failed validation: " + "; ".join(violations)
        )

    return ApprovedWorkoutPlan(
        title=candidate.title,
        session_focus=candidate.session_focus,
        duration_minutes=candidate.duration_minutes,
        exercises=[
            ApprovedWorkoutExercise(
                name=exercise.name,
                sets=exercise.sets,
                reps_min=exercise.reps_min,
                reps_max=exercise.reps_max,
                rir_min=exercise.rir_min,
                rir_max=exercise.rir_max,
                notes=exercise.notes,
                equipment_required=exercise.equipment_required,
            )
            for exercise in candidate.exercises
        ],
        warmup=candidate.warmup,
        cooldown=candidate.cooldown,
        progression_guidance=candidate.progression_guidance,
        rationale=candidate.rationale,
        confidence=candidate.confidence,
        scenario=context.scenario,
        reason_codes=context.reason_codes,
    )


def parse_candidate_workout_explanation_json(
    raw_output: str,
    *,
    strict: bool = True,
) -> CandidateWorkoutExplanation:
    """Parse strict CandidateWorkoutExplanation JSON from provider output."""

    if not isinstance(raw_output, str) or not raw_output.strip():
        raise WorkoutCandidateParseError(
            "Candidate workout explanation output is empty."
        )

    stripped_output = raw_output.strip()
    if stripped_output.startswith("```") or stripped_output.endswith("```"):
        raise WorkoutCandidateParseError(
            "Candidate workout explanation output must be raw JSON, not markdown."
        )

    try:
        payload = json.loads(stripped_output)
    except json.JSONDecodeError as exc:
        raise WorkoutCandidateParseError(
            "Malformed CandidateWorkoutExplanation JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise WorkoutCandidateParseError(
            "CandidateWorkoutExplanation JSON must be an object."
        )

    missing_fields = _REQUIRED_WORKOUT_EXPLANATION_FIELDS - set(payload)
    if missing_fields:
        formatted = ", ".join(sorted(missing_fields))
        raise WorkoutCandidateParseError(
            "CandidateWorkoutExplanation missing required field(s): " + formatted
        )

    if strict:
        _reject_unapproved_fields(
            payload,
            _ALLOWED_WORKOUT_EXPLANATION_FIELDS,
            "explanation",
        )

    confidence = _require_string(payload, "confidence")
    if confidence not in _ALLOWED_CONFIDENCE_VALUES:
        raise WorkoutCandidateParseError(
            "CandidateWorkoutExplanation confidence is invalid."
        )

    return CandidateWorkoutExplanation(
        session_summary=_require_string(payload, "session_summary"),
        why_this_fits_today=_require_string(payload, "why_this_fits_today"),
        focus_cue=_require_string(payload, "focus_cue"),
        recovery_context=_require_string(payload, "recovery_context"),
        nutrition_or_logging_context=_require_string(
            payload,
            "nutrition_or_logging_context",
        ),
        confidence=confidence,
    )


def _explanation_text_blob(explanation: CandidateWorkoutExplanation) -> str:
    return " ".join(
        [
            explanation.session_summary,
            explanation.why_this_fits_today,
            explanation.focus_cue,
            explanation.recovery_context,
            explanation.nutrition_or_logging_context,
        ]
    ).lower()


def _sentence_count(value: str) -> int:
    markers = [".", "!", "?"]
    count = sum(value.count(marker) for marker in markers)
    return max(1, count)


def validate_candidate_workout_explanation(
    candidate: CandidateWorkoutExplanation,
    approved_plan: ApprovedWorkoutPlan,
    context: WorkoutContext,
) -> list[str]:
    """Validate optional AI workout explanation copy.

    Explanation copy may describe an already-approved plan, but it must never
    prescribe changes to exercises, sets, reps, RIR, equipment, progression, or
    deload decisions. ApprovedWorkoutPlan remains the source of truth.
    """

    violations: list[str] = []
    fields = [
        candidate.session_summary,
        candidate.why_this_fits_today,
        candidate.focus_cue,
        candidate.recovery_context,
        candidate.nutrition_or_logging_context,
    ]

    for value in fields:
        if len(value) > 320:
            violations.append("Workout explanation fields must stay concise.")
            break
        if _sentence_count(value) > 2:
            violations.append("Workout explanation fields must be 1-2 sentences.")
            break

    if _CONFIDENCE_RANK.get(candidate.confidence, -1) > _CONFIDENCE_RANK.get(
        approved_plan.confidence,
        -1,
    ):
        violations.append(
            "Workout explanation confidence must not exceed plan confidence."
        )

    text = _explanation_text_blob(candidate)

    for term in _INTERNAL_DEBUG_TERMS:
        if term in text:
            violations.append("Workout explanation contains internal/debug language.")
            break

    for term in _WORKOUT_EXPLANATION_FORBIDDEN_TERMS:
        if term in text:
            violations.append(
                "Workout explanation contains forbidden coaching language."
            )
            break

    for term in _EXPLANATION_PRESCRIPTION_CHANGE_TERMS:
        if term in text:
            violations.append("Workout explanation must not change the approved plan.")
            break

    if context.scenario == "data_quality_limited":
        for term in _DATA_QUALITY_FORBIDDEN_TERMS:
            if term in text:
                violations.append(
                    "Data-quality-limited workout explanations must avoid "
                    "overconfident claims."
                )
                break

    if context.scenario == "aligned_managed":
        for term in _ALIGNED_MANAGED_FORBIDDEN_TERMS:
            if term in text:
                violations.append(
                    "Aligned workout explanations must avoid unnecessary "
                    "intervention framing."
                )
                break

    if context.scenario == "recovery_limited":
        for term in _RECOVERY_LIMITED_FORBIDDEN_TERMS:
            if term in text:
                violations.append(
                    "Recovery-limited workout explanations must avoid "
                    "max-effort language."
                )
                break

    return violations


def approve_candidate_workout_explanation(
    candidate: CandidateWorkoutExplanation,
    approved_plan: ApprovedWorkoutPlan,
    context: WorkoutContext,
) -> ApprovedWorkoutExplanation:
    violations = validate_candidate_workout_explanation(
        candidate, approved_plan, context
    )
    if violations:
        raise ValueError(
            "CandidateWorkoutExplanation failed validation: " + "; ".join(violations)
        )

    return ApprovedWorkoutExplanation(
        session_summary=candidate.session_summary,
        why_this_fits_today=candidate.why_this_fits_today,
        focus_cue=candidate.focus_cue,
        recovery_context=candidate.recovery_context,
        nutrition_or_logging_context=candidate.nutrition_or_logging_context,
        confidence=candidate.confidence,
    )


def build_deterministic_workout_explanation(
    approved_plan: ApprovedWorkoutPlan,
    context: WorkoutContext,
) -> ApprovedWorkoutExplanation:
    if context.scenario == "recovery_limited":
        recovery_context = (
            "Recovery signals suggest keeping the session controlled and leaving "
            "reps in reserve today."
        )
        nutrition_context = (
            "Keep nutrition and logging steady so recovery trends are easier to "
            "interpret after the session."
        )
    elif context.scenario == "nutrition_training_mismatch":
        recovery_context = (
            "The session stays productive without adding aggressive training stress."
        )
        nutrition_context = (
            "Nutrition support and training demand should be reviewed together, so "
            "log meals and workout effort carefully today."
        )
    elif context.scenario == "improving_after_deload":
        recovery_context = (
            "Recent recovery looks more stable, so the plan supports controlled "
            "progression rather than a fast ramp-up."
        )
        nutrition_context = (
            "Consistent logging will help confirm whether the improved trend holds "
            "after training."
        )
    elif context.scenario == "data_quality_limited":
        recovery_context = (
            "The session is intentionally manageable because logging quality limits "
            "stronger training conclusions."
        )
        nutrition_context = (
            "Focus on recording the workout and nutrition clearly before making "
            "stronger adjustments."
        )
    else:
        recovery_context = (
            "Current context supports a normal session while monitoring effort and "
            "recovery afterward."
        )
        nutrition_context = (
            "Keep logging consistent so future recommendations can stay grounded."
        )

    return ApprovedWorkoutExplanation(
        session_summary=(
            f"{approved_plan.title} is an approved {approved_plan.duration_minutes}-minute "
            "session built from the current training and equipment context."
        ),
        why_this_fits_today=approved_plan.rationale,
        focus_cue=(
            "Focus on clean execution, honest effort logging, and stopping within "
            "the approved plan targets."
        ),
        recovery_context=recovery_context,
        nutrition_or_logging_context=nutrition_context,
        confidence=approved_plan.confidence,
    )


def _deterministic_workout_explanation_result(
    approved_plan: ApprovedWorkoutPlan,
    context: WorkoutContext,
    metadata: WorkoutExplanationRuntimeMetadata,
) -> ApprovedWorkoutExplanationResult:
    return ApprovedWorkoutExplanationResult(
        approved_workout_explanation=build_deterministic_workout_explanation(
            approved_plan,
            context,
        ),
        runtime_metadata=metadata,
    )


def workout_explanation_context_to_llm_json(
    approved_plan: ApprovedWorkoutPlan,
    context: WorkoutContext,
) -> dict[str, Any]:
    training_execution_summary = build_training_execution_summary(context.user_id)
    return {
        "scenario": context.scenario,
        "confidence": approved_plan.confidence,
        "approved_plan": {
            "title": approved_plan.title,
            "session_focus": approved_plan.session_focus,
            "duration_minutes": approved_plan.duration_minutes,
            "exercise_count": len(approved_plan.exercises),
            "movement_patterns": _movement_pattern_targets_for_context(context)[:5],
        },
        "allowed_explanation_fields": sorted(_ALLOWED_WORKOUT_EXPLANATION_FIELDS),
        "constraints": [
            "Explain only the approved plan.",
            "Do not change exercises, sets, reps, RIR, equipment, progression, or deload decisions.",
            "Use concise user-facing coaching language only.",
        ],
        "training_execution_summary": {
            "completed_execution_count": training_execution_summary.completed_execution_count,
            "confidence": training_execution_summary.confidence,
            "execution_quality": training_execution_summary.execution_quality,
        },
    }


def build_crewai_workout_explanation_prompt(
    approved_plan: ApprovedWorkoutPlan,
    context: WorkoutContext,
) -> str:
    safe_context = workout_explanation_context_to_llm_json(approved_plan, context)
    return f"""
/no_think
Return one raw JSON object only. No markdown. No commentary. No reasoning.
Explain the already-approved workout plan. Do not change the plan.

Use this exact key set only:
session_summary, why_this_fits_today, focus_cue, recovery_context,
nutrition_or_logging_context, confidence

Each field must be 1-2 concise user-facing sentences.
Do not prescribe exercises, sets, reps, RIR, equipment, progression, deloads, medical guidance, or nutrition targets.
Do not mention overtraining, stalled progress, poor adherence, failure, discipline, or internal backend terms.

Compact valid example:
{{
  "session_summary": "This is a controlled strength session built from today's approved plan.",
  "why_this_fits_today": "It matches the current recovery, equipment, and training constraints without adding unnecessary stress.",
  "focus_cue": "Keep the work clean and log effort honestly after each exercise.",
  "recovery_context": "The session is designed to support consistency while respecting current recovery signals.",
  "nutrition_or_logging_context": "Consistent logging today will make the next recommendation more useful.",
  "confidence": "Moderate"
}}

Context:
{json.dumps(safe_context, separators=(",", ":"), sort_keys=True)}
""".strip()


def generate_crewai_workout_explanation_json(
    approved_plan: ApprovedWorkoutPlan,
    context: WorkoutContext,
) -> str:
    """Run optional CrewAI workout explanation generation.

    The returned text is untrusted and must pass strict parse/validation before it
    can be returned from a debug path. The ApprovedWorkoutPlan remains the source
    of truth.
    """
    from crewai import LLM, Agent, Crew, Task

    llm_kwargs = _crewai_workout_llm_kwargs()
    try:
        llm = LLM(**llm_kwargs)
    except TypeError:
        logger.warning(
            "crewai_workout_explanation_llm_rejected_no_think_kwargs",
            extra={
                "model": llm_kwargs.get("model"),
                "base_url": llm_kwargs.get("base_url"),
            },
        )
        llm = LLM(**_fallback_crewai_workout_llm_kwargs(llm_kwargs))

    explanation_agent = Agent(
        role="Workout Explanation JSON Generator",
        goal="Explain an already-approved workout plan without changing it.",
        backstory=(
            "You create concise coaching explanations for approved workout plans. "
            "You never create or alter the workout structure."
        ),
        llm=llm,
        verbose=False,
    )

    explanation_task = Task(
        description=build_crewai_workout_explanation_prompt(approved_plan, context),
        expected_output="Raw CandidateWorkoutExplanation JSON object only. No markdown.",
        agent=explanation_agent,
    )

    crew = Crew(agents=[explanation_agent], tasks=[explanation_task], verbose=False)
    result = crew.kickoff()
    return _crew_result_to_raw_json(result)


def _log_workout_explanation_runtime(
    context: WorkoutContext,
    metadata: WorkoutExplanationRuntimeMetadata,
    elapsed_ms: int,
) -> None:
    logger.info(
        "workout_explanation_provider_result",
        extra={
            "user_id": context.user_id,
            "scenario": context.scenario,
            "configured_provider": metadata.configured_provider,
            "selected_provider": metadata.selected_provider,
            "crewai_attempted": metadata.crewai_attempted,
            "candidate_parse_status": metadata.candidate_parse_status,
            "candidate_validation_status": metadata.candidate_validation_status,
            "final_explanation_source": metadata.final_explanation_source,
            "fallback_used": metadata.fallback_used,
            "fallback_reason": metadata.fallback_reason,
            "validation_violations": metadata.validation_errors,
            "raw_output_length": metadata.raw_output_length,
            "raw_output_preview_truncated": metadata.raw_output_preview_truncated,
            "markdown_wrapper_detected": metadata.markdown_wrapper_detected,
            "elapsed_ms": elapsed_ms,
        },
    )


def approve_workout_explanation_json_or_fallback_with_metadata(
    raw_json: str,
    approved_plan: ApprovedWorkoutPlan,
    context: WorkoutContext,
    *,
    configured_provider: str = WORKOUT_PROVIDER_DETERMINISTIC,
    selected_provider: str = WORKOUT_PROVIDER_DETERMINISTIC,
    crewai_attempted: bool = False,
) -> ApprovedWorkoutExplanationResult:
    start_time = time.perf_counter()
    raw_diagnostics = _raw_output_diagnostics(raw_json)
    try:
        candidate = parse_candidate_workout_explanation_json(raw_json)
        violations = validate_candidate_workout_explanation(
            candidate,
            approved_plan,
            context,
        )
        if violations:
            metadata = WorkoutExplanationRuntimeMetadata(
                configured_provider=configured_provider,
                selected_provider=selected_provider,
                crewai_attempted=crewai_attempted,
                fallback_used=True,
                fallback_reason=FALLBACK_REASON_VALIDATION_FAILURE,
                explanation_valid=False,
                validation_errors=violations,
                candidate_parse_status=CANDIDATE_PARSE_STATUS_SUCCESS,
                candidate_validation_status=CANDIDATE_VALIDATION_STATUS_FAILED,
                final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
                **raw_diagnostics,
            )
            result = _deterministic_workout_explanation_result(
                approved_plan,
                context,
                metadata,
            )
        else:
            metadata = WorkoutExplanationRuntimeMetadata(
                configured_provider=configured_provider,
                selected_provider=selected_provider,
                crewai_attempted=crewai_attempted,
                fallback_used=False,
                fallback_reason=None,
                explanation_valid=True,
                validation_errors=[],
                candidate_parse_status=CANDIDATE_PARSE_STATUS_SUCCESS,
                candidate_validation_status=CANDIDATE_VALIDATION_STATUS_SUCCESS,
                final_explanation_source=(
                    FINAL_EXPLANATION_SOURCE_CREWAI_APPROVED
                    if crewai_attempted
                    else FINAL_EXPLANATION_SOURCE_DETERMINISTIC
                ),
                **raw_diagnostics,
            )
            result = ApprovedWorkoutExplanationResult(
                approved_workout_explanation=approve_candidate_workout_explanation(
                    candidate,
                    approved_plan,
                    context,
                ),
                runtime_metadata=metadata,
            )
    except (ValueError, WorkoutCandidateParseError) as exc:
        metadata = WorkoutExplanationRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=crewai_attempted,
            fallback_used=True,
            fallback_reason=_fallback_reason_for_parse_error(exc),
            explanation_valid=False,
            validation_errors=[str(exc)],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_FAILED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
            **raw_diagnostics,
        )
        result = _deterministic_workout_explanation_result(
            approved_plan,
            context,
            metadata,
        )

    _log_workout_explanation_runtime(
        context,
        result.runtime_metadata,
        elapsed_ms=round((time.perf_counter() - start_time) * 1000),
    )
    return result


def _provider_exception_summary(exc: Exception, *, limit: int = 300) -> str:
    """Return a bounded provider exception summary for debug metadata.

    Runtime metadata should help QA identify missing/incompatible dependencies,
    but it should not expose full tracebacks or unbounded provider output.
    """

    message = " ".join(str(exc).split())[:limit]
    if not message:
        return type(exc).__name__
    return f"{type(exc).__name__}: {message}"


def approve_workout_explanation_provider_or_fallback_with_metadata(
    explanation_provider: WorkoutExplanationProvider,
    approved_plan: ApprovedWorkoutPlan,
    context: WorkoutContext,
    *,
    configured_provider: str = WORKOUT_PROVIDER_CREWAI,
    selected_provider: str = WORKOUT_PROVIDER_CREWAI,
) -> ApprovedWorkoutExplanationResult:
    start_time = time.perf_counter()
    try:
        raw_json = explanation_provider(approved_plan, context)
    except Exception as exc:
        exception_summary = _provider_exception_summary(exc)
        logger.exception(
            "workout_explanation_provider_exception",
            extra={
                "user_id": context.user_id,
                "scenario": context.scenario,
                "configured_provider": configured_provider,
                "selected_provider": selected_provider,
                "exception_type": type(exc).__name__,
                "exception_summary": exception_summary,
            },
        )
        metadata = WorkoutExplanationRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            explanation_valid=False,
            validation_errors=[exception_summary],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
        )
        result = _deterministic_workout_explanation_result(
            approved_plan,
            context,
            metadata,
        )
        _log_workout_explanation_runtime(
            context,
            result.runtime_metadata,
            elapsed_ms=round((time.perf_counter() - start_time) * 1000),
        )
        return result

    if not isinstance(raw_json, str):
        metadata = WorkoutExplanationRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT,
            explanation_valid=False,
            validation_errors=[
                "CandidateWorkoutExplanation provider returned non-string output."
            ],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
        )
        result = _deterministic_workout_explanation_result(
            approved_plan,
            context,
            metadata,
        )
        _log_workout_explanation_runtime(
            context,
            result.runtime_metadata,
            elapsed_ms=round((time.perf_counter() - start_time) * 1000),
        )
        return result

    return approve_workout_explanation_json_or_fallback_with_metadata(
        raw_json,
        approved_plan,
        context,
        configured_provider=configured_provider,
        selected_provider=selected_provider,
        crewai_attempted=True,
    )


def _configured_workout_explanation_provider() -> str:
    return (
        os.getenv(WORKOUT_EXPLANATION_PROVIDER_ENV, WORKOUT_PROVIDER_DETERMINISTIC)
        .strip()
        .lower()
    )


def build_configured_workout_explanation_with_metadata(
    approved_plan: ApprovedWorkoutPlan,
    context: WorkoutContext,
) -> ApprovedWorkoutExplanationResult:
    provider = _configured_workout_explanation_provider()

    if provider == WORKOUT_PROVIDER_DETERMINISTIC:
        metadata = WorkoutExplanationRuntimeMetadata(
            configured_provider=provider,
            selected_provider=WORKOUT_PROVIDER_DETERMINISTIC,
            crewai_attempted=False,
            fallback_used=False,
            fallback_reason=FALLBACK_REASON_DETERMINISTIC_SELECTED,
            explanation_valid=True,
            validation_errors=[],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC,
        )
        result = _deterministic_workout_explanation_result(
            approved_plan,
            context,
            metadata,
        )
        _log_workout_explanation_runtime(context, result.runtime_metadata, elapsed_ms=0)
        return result

    if provider == WORKOUT_PROVIDER_CREWAI:
        return approve_workout_explanation_provider_or_fallback_with_metadata(
            generate_crewai_workout_explanation_json,
            approved_plan,
            context,
            configured_provider=provider,
            selected_provider=WORKOUT_PROVIDER_CREWAI,
        )

    metadata = WorkoutExplanationRuntimeMetadata(
        configured_provider=provider,
        selected_provider=WORKOUT_PROVIDER_DETERMINISTIC,
        crewai_attempted=False,
        fallback_used=True,
        fallback_reason=FALLBACK_REASON_INVALID_PROVIDER,
        explanation_valid=True,
        validation_errors=[f"Unsupported workout explanation provider: {provider}"],
        candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
        candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
        final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
    )
    result = _deterministic_workout_explanation_result(approved_plan, context, metadata)
    _log_workout_explanation_runtime(context, result.runtime_metadata, elapsed_ms=0)
    return result


def _crew_result_to_raw_json(result: Any) -> str:
    raw = getattr(result, "raw", None)
    if raw is not None:
        return str(raw)
    return str(result)


def _env_flag_enabled(env_var: str, *, default: bool) -> bool:
    raw_value = os.getenv(env_var)
    if raw_value is None:
        return default
    return raw_value.strip().lower() not in {"0", "false", "no", "off"}


def _crewai_workout_llm_kwargs() -> dict[str, Any]:
    """Build CrewAI/LiteLLM kwargs for the workout candidate LLM.

    Qwen3 thinking models served by Ollama can emit reasoning before the final
    answer unless the native Ollama `think` flag is disabled.  Keep the parser
    strict and ask the runtime to disable thinking instead of trying to recover
    JSON from reasoning text.  Several fields are included intentionally because
    the exact pass-through path can differ between CrewAI/LiteLLM/Ollama
    adapters.
    """

    llm_kwargs: dict[str, Any] = {
        "model": os.getenv(CREWAI_WORKOUT_MODEL_ENV, CREWAI_WORKOUT_DEFAULT_MODEL),
        "base_url": os.getenv(OLLAMA_BASE_URL_ENV, CREWAI_WORKOUT_DEFAULT_BASE_URL),
        "temperature": 0,
    }

    if _env_flag_enabled(CREWAI_WORKOUT_JSON_RESPONSE_FORMAT_ENV, default=True):
        llm_kwargs["response_format"] = {"type": "json_object"}

    if _env_flag_enabled(CREWAI_WORKOUT_DISABLE_THINKING_ENV, default=True):
        no_think_payload = {"think": False}
        llm_kwargs["think"] = False
        llm_kwargs["options"] = dict(no_think_payload)
        llm_kwargs["extra_body"] = {
            "think": False,
            "options": dict(no_think_payload),
        }
        llm_kwargs["additional_params"] = {
            "think": False,
            "options": dict(no_think_payload),
        }

    return llm_kwargs


def _fallback_crewai_workout_llm_kwargs(llm_kwargs: dict[str, Any]) -> dict[str, Any]:
    """Return conservative kwargs if a CrewAI version rejects pass-through keys."""

    allowed_fallback_keys = {"model", "base_url", "temperature", "response_format"}
    return {
        key: value for key, value in llm_kwargs.items() if key in allowed_fallback_keys
    }


def build_crewai_candidate_workout_plan_prompt(context: WorkoutContext) -> str:
    safe_context = workout_context_to_llm_json(context)
    return f"""
/no_think
Return one raw JSON object only. Do not think aloud. No markdown. No commentary. No reasoning.
The first character must be {{. Do not wrap the object.

Use this exact top-level key set only:
title, session_focus, duration_minutes, exercises, warmup, cooldown,
progression_guidance, rationale, confidence

Never use these top-level wrapper keys:
workout_plan, plan, response, result, data

Each exercise must use this exact key set only:
exercise_name, catalog_exercise_id, movement_pattern, target_zone, sets, reps_min,
reps_max, target_rir_min, target_rir_max, required_equipment, notes

Never use these exercise keys:
equipment, reps, rir_target, rir, exercise, name

Compact valid example:
{{
  "title": "Controlled Strength Session",
  "session_focus": "Train productively within today's constraints.",
  "duration_minutes": 45,
  "exercises": [
    {{
      "exercise_name": "Goblet Squat",
      "catalog_exercise_id": 1,
      "movement_pattern": "squat",
      "target_zone": "main",
      "sets": 3,
      "reps_min": 8,
      "reps_max": 10,
      "target_rir_min": 2,
      "target_rir_max": 4,
      "required_equipment": ["dumbbell"],
      "notes": "Keep reps controlled."
    }}
  ],
  "warmup": "Use easy movement and ramp-up sets.",
  "cooldown": "Log performance and recovery markers.",
  "progression_guidance": "Progress gradually within the approved RIR range.",
  "rationale": "This session uses only the provided exercise list and equipment.",
  "confidence": "Moderate"
}}

Rules:
- Choose only from allowed_exercises.
- Copy exercise_name, catalog_exercise_id, movement_pattern, and required_equipment exactly.
- Use 3-5 exercises.
- Keep duration between 30 and 60 minutes.
- Keep target_rir_min and target_rir_max inside allowed_rir_range.
- Keep notes short.
- Do not mention overtraining, stalled progress, injury, medical advice, automatic deload, or automatic load increase.

Context:
{json.dumps(safe_context, separators=(",", ":"), sort_keys=True)}
""".strip()


def generate_crewai_candidate_workout_plan_json(context: WorkoutContext) -> str:
    """Run the CrewAI CandidateWorkoutPlan task and return raw JSON output.

    The returned string is intentionally untrusted. It must pass through
    parse_candidate_workout_plan_json(), validate_candidate_workout_plan(), and
    approval before it can become user-facing.
    """
    from crewai import LLM, Agent, Crew, Task

    llm_kwargs = _crewai_workout_llm_kwargs()
    try:
        llm = LLM(**llm_kwargs)
    except TypeError:
        logger.warning(
            "crewai_workout_llm_rejected_no_think_kwargs",
            extra={
                "model": llm_kwargs.get("model"),
                "base_url": llm_kwargs.get("base_url"),
            },
        )
        llm = LLM(**_fallback_crewai_workout_llm_kwargs(llm_kwargs))

    workout_agent = Agent(
        role="Workout Candidate JSON Generator",
        goal="Generate safe CandidateWorkoutPlan JSON from approved context only.",
        backstory=(
            "You create candidate workout plans from structured training, "
            "equipment, exercise catalog, and execution-summary context."
        ),
        llm=llm,
        verbose=False,
    )

    workout_task = Task(
        description=build_crewai_candidate_workout_plan_prompt(context),
        expected_output="Raw CandidateWorkoutPlan JSON object only. No markdown.",
        agent=workout_agent,
    )

    crew = Crew(agents=[workout_agent], tasks=[workout_task], verbose=False)
    result = crew.kickoff()
    return _crew_result_to_raw_json(result)


def _markdown_wrapper_detected(raw_output: str) -> bool:
    stripped = raw_output.strip().lower()
    return stripped.startswith("```") or "```json" in stripped or "```" in stripped


def _truncate_raw_output_preview(raw_output: str) -> str:
    compact = " ".join(raw_output.split())
    if len(compact) <= RAW_OUTPUT_PREVIEW_LIMIT:
        return compact
    return compact[:RAW_OUTPUT_PREVIEW_LIMIT] + "..."


def _raw_output_diagnostics(raw_output: str | None) -> dict[str, Any]:
    if raw_output is None:
        return {
            "raw_output_length": None,
            "raw_output_preview_truncated": None,
            "markdown_wrapper_detected": False,
        }

    return {
        "raw_output_length": len(raw_output),
        "raw_output_preview_truncated": _truncate_raw_output_preview(raw_output),
        "markdown_wrapper_detected": _markdown_wrapper_detected(raw_output),
    }


def _fallback_reason_for_parse_error(exc: Exception) -> str:
    message = str(exc).lower()
    if "malformed" in message or "markdown" in message or "empty" in message:
        return FALLBACK_REASON_MALFORMED_JSON
    if "confidence is invalid" in message:
        return FALLBACK_REASON_INVALID_CONFIDENCE
    return FALLBACK_REASON_SCHEMA_MISMATCH


def _deterministic_workout_result(
    context: WorkoutContext,
    metadata: WorkoutPlanRuntimeMetadata,
) -> ApprovedWorkoutPlanResult:
    return ApprovedWorkoutPlanResult(
        approved_workout_plan=approve_candidate_workout_plan(
            generate_candidate_workout_plan(context),
            context,
        ),
        runtime_metadata=metadata,
    )


def _log_workout_candidate_runtime(
    context: WorkoutContext,
    metadata: WorkoutPlanRuntimeMetadata,
    elapsed_ms: int,
) -> None:
    logger.info(
        "workout_candidate_provider_result",
        extra={
            "user_id": context.user_id,
            "scenario": context.scenario,
            "configured_provider": metadata.configured_provider,
            "selected_provider": metadata.selected_provider,
            "model": os.getenv(CREWAI_WORKOUT_MODEL_ENV, CREWAI_WORKOUT_DEFAULT_MODEL),
            "context_confidence": context.confidence,
            "crewai_attempted": metadata.crewai_attempted,
            "candidate_parse_status": metadata.candidate_parse_status,
            "candidate_validation_status": metadata.candidate_validation_status,
            "final_plan_source": metadata.final_plan_source,
            "fallback_used": metadata.fallback_used,
            "fallback_reason": metadata.fallback_reason,
            "validation_violations": metadata.validation_errors,
            "raw_output_length": metadata.raw_output_length,
            "raw_output_preview_truncated": metadata.raw_output_preview_truncated,
            "markdown_wrapper_detected": metadata.markdown_wrapper_detected,
            "elapsed_ms": elapsed_ms,
        },
    )


def approve_workout_candidate_json_or_fallback_with_metadata(
    raw_json: str,
    context: WorkoutContext,
    *,
    configured_provider: str = WORKOUT_PROVIDER_DETERMINISTIC,
    selected_provider: str = WORKOUT_PROVIDER_DETERMINISTIC,
    crewai_attempted: bool = False,
) -> ApprovedWorkoutPlanResult:
    """Approve CandidateWorkoutPlan JSON or fall back deterministically."""

    start_time = time.perf_counter()
    raw_diagnostics = _raw_output_diagnostics(raw_json)
    try:
        candidate = parse_candidate_workout_plan_json(raw_json)
        violations = validate_candidate_workout_plan(candidate, context)
        if violations:
            metadata = WorkoutPlanRuntimeMetadata(
                configured_provider=configured_provider,
                selected_provider=selected_provider,
                crewai_attempted=crewai_attempted,
                fallback_used=True,
                fallback_reason=FALLBACK_REASON_VALIDATION_FAILURE,
                candidate_valid=False,
                validation_errors=violations,
                candidate_parse_status=CANDIDATE_PARSE_STATUS_SUCCESS,
                candidate_validation_status=CANDIDATE_VALIDATION_STATUS_FAILED,
                final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK,
                **raw_diagnostics,
            )
            result = _deterministic_workout_result(context, metadata)
        else:
            metadata = WorkoutPlanRuntimeMetadata(
                configured_provider=configured_provider,
                selected_provider=selected_provider,
                crewai_attempted=crewai_attempted,
                fallback_used=False,
                fallback_reason=None,
                candidate_valid=True,
                validation_errors=[],
                candidate_parse_status=CANDIDATE_PARSE_STATUS_SUCCESS,
                candidate_validation_status=CANDIDATE_VALIDATION_STATUS_SUCCESS,
                final_plan_source=(
                    FINAL_PLAN_SOURCE_CREWAI_APPROVED
                    if crewai_attempted
                    else FINAL_PLAN_SOURCE_DETERMINISTIC
                ),
                **raw_diagnostics,
            )
            result = ApprovedWorkoutPlanResult(
                approved_workout_plan=approve_candidate_workout_plan(
                    candidate,
                    context,
                ),
                runtime_metadata=metadata,
            )
    except (ValueError, WorkoutCandidateParseError) as exc:
        metadata = WorkoutPlanRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=crewai_attempted,
            fallback_used=True,
            fallback_reason=_fallback_reason_for_parse_error(exc),
            candidate_valid=False,
            validation_errors=[str(exc)],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_FAILED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK,
            **raw_diagnostics,
        )
        result = _deterministic_workout_result(context, metadata)

    _log_workout_candidate_runtime(
        context,
        result.runtime_metadata,
        elapsed_ms=round((time.perf_counter() - start_time) * 1000),
    )
    return result


def approve_workout_candidate_json_or_fallback(
    raw_json: str,
    context: WorkoutContext,
) -> ApprovedWorkoutPlan:
    """Approve CandidateWorkoutPlan JSON or fall back deterministically."""

    return approve_workout_candidate_json_or_fallback_with_metadata(
        raw_json,
        context,
    ).approved_workout_plan


def approve_workout_candidate_provider_or_fallback_with_metadata(
    candidate_provider: WorkoutCandidateProvider,
    context: WorkoutContext,
    *,
    configured_provider: str = WORKOUT_PROVIDER_CREWAI,
    selected_provider: str = WORKOUT_PROVIDER_CREWAI,
) -> ApprovedWorkoutPlanResult:
    """Run a workout candidate provider behind the backend safety boundary."""

    start_time = time.perf_counter()
    try:
        raw_json = candidate_provider(context)
    except Exception as exc:
        metadata = WorkoutPlanRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            candidate_valid=False,
            validation_errors=[type(exc).__name__],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK,
        )
        result = _deterministic_workout_result(context, metadata)
        _log_workout_candidate_runtime(
            context,
            result.runtime_metadata,
            elapsed_ms=round((time.perf_counter() - start_time) * 1000),
        )
        return result

    if not isinstance(raw_json, str):
        metadata = WorkoutPlanRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT,
            candidate_valid=False,
            validation_errors=[
                "CandidateWorkoutPlan provider returned non-string output."
            ],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK,
        )
        result = _deterministic_workout_result(context, metadata)
        _log_workout_candidate_runtime(
            context,
            result.runtime_metadata,
            elapsed_ms=round((time.perf_counter() - start_time) * 1000),
        )
        return result

    return approve_workout_candidate_json_or_fallback_with_metadata(
        raw_json,
        context,
        configured_provider=configured_provider,
        selected_provider=selected_provider,
        crewai_attempted=True,
    )


def approve_workout_candidate_provider_or_fallback(
    candidate_provider: WorkoutCandidateProvider,
    context: WorkoutContext,
) -> ApprovedWorkoutPlan:
    return approve_workout_candidate_provider_or_fallback_with_metadata(
        candidate_provider,
        context,
    ).approved_workout_plan


def build_crewai_approved_workout_plan_with_metadata(
    health_state: UserHealthState,
) -> ApprovedWorkoutPlanResult:
    context = build_workout_context(health_state)
    return approve_workout_candidate_provider_or_fallback_with_metadata(
        generate_crewai_candidate_workout_plan_json,
        context,
        configured_provider=WORKOUT_PROVIDER_CREWAI,
        selected_provider=WORKOUT_PROVIDER_CREWAI,
    )


def build_crewai_approved_workout_plan(
    health_state: UserHealthState,
) -> ApprovedWorkoutPlan:
    return build_crewai_approved_workout_plan_with_metadata(
        health_state,
    ).approved_workout_plan


def _configured_workout_candidate_provider() -> str:
    return (
        os.getenv(WORKOUT_CANDIDATE_PROVIDER_ENV, WORKOUT_PROVIDER_DETERMINISTIC)
        .strip()
        .lower()
    )


def build_configured_approved_workout_plan_with_metadata(
    health_state: UserHealthState,
) -> ApprovedWorkoutPlanResult:
    """Build an ApprovedWorkoutPlan and runtime metadata for debug inspection."""

    context = build_workout_context(health_state)
    provider = _configured_workout_candidate_provider()

    if provider == WORKOUT_PROVIDER_DETERMINISTIC:
        metadata = WorkoutPlanRuntimeMetadata(
            configured_provider=provider,
            selected_provider=WORKOUT_PROVIDER_DETERMINISTIC,
            crewai_attempted=False,
            fallback_used=False,
            fallback_reason=FALLBACK_REASON_DETERMINISTIC_SELECTED,
            candidate_valid=True,
            validation_errors=[],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC,
        )
        result = _deterministic_workout_result(context, metadata)
        _log_workout_candidate_runtime(context, result.runtime_metadata, elapsed_ms=0)
        return result

    if provider == WORKOUT_PROVIDER_CREWAI:
        return approve_workout_candidate_provider_or_fallback_with_metadata(
            generate_crewai_candidate_workout_plan_json,
            context,
            configured_provider=provider,
            selected_provider=WORKOUT_PROVIDER_CREWAI,
        )

    metadata = WorkoutPlanRuntimeMetadata(
        configured_provider=provider,
        selected_provider=WORKOUT_PROVIDER_DETERMINISTIC,
        crewai_attempted=False,
        fallback_used=True,
        fallback_reason=FALLBACK_REASON_INVALID_PROVIDER,
        candidate_valid=True,
        validation_errors=[f"Unsupported workout candidate provider: {provider}"],
        candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
        candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
        final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK,
    )
    result = _deterministic_workout_result(context, metadata)
    _log_workout_candidate_runtime(context, result.runtime_metadata, elapsed_ms=0)
    return result


def build_configured_approved_workout_plan(
    health_state: UserHealthState,
) -> ApprovedWorkoutPlan:
    """Build an ApprovedWorkoutPlan through the configured provider.

    This remains deterministic by default. CrewAI is opt-in and should be used
    through debug/manual runtime paths until Architecture approves broader use.
    """

    return build_configured_approved_workout_plan_with_metadata(
        health_state,
    ).approved_workout_plan


def build_approved_workout_plan(health_state: UserHealthState) -> ApprovedWorkoutPlan:
    context = build_workout_context(health_state)
    candidate = generate_candidate_workout_plan(context)
    return approve_candidate_workout_plan(candidate, context)


def render_approved_workout_plan(plan: ApprovedWorkoutPlan) -> str:
    lines = [
        "**Workout Plan Preview**",
        "",
        f"**Title:** {plan.title}",
        f"**Focus:** {plan.session_focus}",
        f"**Duration:** About {plan.duration_minutes} minutes",
        "",
        "**Warmup:** " + plan.warmup,
        "",
        "**Exercises:**",
    ]

    for exercise in plan.exercises:
        lines.append(
            "- "
            f"{exercise.name}: {exercise.sets} sets x "
            f"{exercise.reps_min}-{exercise.reps_max} reps, "
            f"RIR {exercise.rir_min}-{exercise.rir_max}. "
            f"{exercise.notes}"
        )

    lines.extend(
        [
            "",
            "**Progression Guidance:** " + plan.progression_guidance,
            "",
            "**Cooldown:** " + plan.cooldown,
            "",
            "**Why:** " + plan.rationale,
            "",
            "**Confidence:** " + plan.confidence,
        ]
    )

    return "\n".join(lines)


def approved_workout_plan_to_dict(plan: ApprovedWorkoutPlan) -> dict:
    return asdict(plan)
