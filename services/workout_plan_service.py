from dataclasses import asdict

from models.user_state_models import UserHealthState
from models.workout_constraint_models import WorkoutConstraints
from models.workout_plan_models import (
    ApprovedWorkoutExercise,
    ApprovedWorkoutPlan,
    CandidateWorkoutExercise,
    CandidateWorkoutPlan,
    WorkoutContext,
)
from services.coaching_decision_service import build_coaching_decision
from services.exercise_catalog_service import find_catalog_entry_by_name
from services.training_constraint_service import build_training_constraints
from services.workout_constraint_service import build_workout_constraints

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


def _select_exercise(
    workout_constraints: WorkoutConstraints,
    options: list[tuple[str, list[str]]],
) -> tuple[str, list[str]]:
    for name, equipment_required in options:
        catalog_name, catalog_equipment_required = _catalog_equipment_for_option(
            name,
            equipment_required,
        )
        if _equipment_allowed(catalog_equipment_required, workout_constraints):
            return catalog_name, catalog_equipment_required

    name, equipment_required = options[-1]
    return _catalog_equipment_for_option(name, equipment_required)


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
    name, equipment_required = _select_exercise(context.workout_constraints, options)
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
                        ("Leg Press", ["machine"]),
                        ("Bodyweight Squat", ["bodyweight"]),
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
                        ("Dumbbell Bench Press", ["dumbbell"]),
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
                        ("Chest-Supported Row", ["dumbbell"]),
                        ("Cable Row", ["cable"]),
                        ("Machine Row", ["machine"]),
                        ("Inverted Row", ["bodyweight"]),
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
                        ("Band Face Pull", ["resistance_band"]),
                        ("Dead Bug", ["bodyweight"]),
                        ("Farmer Carry", ["dumbbell"]),
                        ("Bike Steady State", ["bike"]),
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
                        ("Goblet Squat", ["dumbbell"]),
                        ("Leg Press", ["machine"]),
                        ("Bodyweight Squat", ["bodyweight"]),
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
                        ("Lat Pulldown", ["cable"]),
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
                        ("Dead Bug", ["bodyweight"]),
                        ("Band Face Pull", ["resistance_band"]),
                        ("Bike Steady State", ["bike"]),
                    ],
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Keep the accessory work low-to-moderate while nutrition support is clarified.",
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
                        ("Barbell Squat", ["barbell"]),
                        ("Goblet Squat", ["dumbbell"]),
                        ("Leg Press", ["machine"]),
                        ("Bodyweight Squat", ["bodyweight"]),
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
                        ("Dumbbell Bench Press", ["dumbbell"]),
                        ("Barbell Bench Press", ["barbell"]),
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
                        ("Cable Row", ["cable"]),
                        ("Barbell Row", ["barbell"]),
                        ("Dumbbell Row", ["dumbbell"]),
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
                        ("Cable Woodchop", ["cable"]),
                        ("EZ-Bar Curl", ["ez_bar"]),
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

    return CandidateWorkoutPlan(
        title="Gradual Progression Strength Session",
        session_focus="Maintain consistency and progress gradually.",
        duration_minutes=50,
        exercises=[
            _exercise_from_options(
                context,
                [
                    ("Romanian Deadlift", ["barbell"]),
                    ("Barbell Squat", ["barbell"]),
                    ("Goblet Squat", ["dumbbell"]),
                    ("Leg Press", ["machine"]),
                    ("Bodyweight Squat", ["bodyweight"]),
                ],
                3,
                5,
                8,
                rir_min,
                rir_max,
                "Add load only if the previous session felt stable.",
            ),
            _exercise_from_options(
                context,
                [
                    ("Overhead Press", ["barbell"]),
                    ("Barbell Bench Press", ["barbell"]),
                    ("Dumbbell Bench Press", ["dumbbell"]),
                    ("Push-Up", ["bodyweight"]),
                ],
                3,
                6,
                8,
                rir_min,
                rir_max,
                "Keep one or more clean reps in reserve on working sets.",
            ),
            _exercise_from_options(
                context,
                [
                    ("Pull-Up", ["pull_up_bar"]),
                    ("Cable Row", ["cable"]),
                    ("Barbell Row", ["barbell"]),
                    ("Dumbbell Row", ["dumbbell"]),
                    ("Inverted Row", ["bodyweight"]),
                ],
                3,
                8,
                10,
                rir_min,
                rir_max,
                "Progress gradually while recovery markers remain stable.",
            ),
            _exercise_from_options(
                context,
                [
                    ("Farmer Carry", ["dumbbell"]),
                    ("Cable Woodchop", ["cable"]),
                    ("EZ-Bar Curl", ["ez_bar"]),
                    ("Dumbbell Lateral Raise", ["dumbbell"]),
                    ("Dead Bug", ["bodyweight"]),
                ],
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


def validate_candidate_workout_plan(
    candidate: CandidateWorkoutPlan,
    context: WorkoutContext,
) -> list[str]:
    violations: list[str] = []

    if not candidate.exercises:
        violations.append("Workout plan must include at least one exercise.")

    training_constraints = context.training_constraints
    workout_constraints = context.workout_constraints
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

        if not _equipment_allowed(exercise.equipment_required, workout_constraints):
            violations.append(
                f"{exercise.name} requires equipment outside current workout constraints."
            )

    text = _text_blob(candidate)

    for term in _INTERNAL_DEBUG_TERMS:
        if term in text:
            violations.append("Workout plan contains internal/debug language.")
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
