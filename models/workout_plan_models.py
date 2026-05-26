from dataclasses import dataclass, field

from models.training_constraint_models import TrainingConstraints
from models.workout_constraint_models import WorkoutConstraints


@dataclass
class WorkoutContext:
    user_id: int
    scenario: str
    primary_goal: str
    training_load: str
    recovery_demand: str
    avg_rir: float | str
    workout_count: int
    training_constraints: TrainingConstraints
    workout_constraints: WorkoutConstraints
    confidence: str
    reason_codes: list[str] = field(default_factory=list)


@dataclass
class CandidateWorkoutExercise:
    name: str
    sets: int
    reps_min: int
    reps_max: int
    rir_min: int
    rir_max: int
    notes: str
    equipment_required: list[str] = field(default_factory=list)


@dataclass
class CandidateWorkoutPlan:
    title: str
    session_focus: str
    duration_minutes: int
    exercises: list[CandidateWorkoutExercise]
    warmup: str
    cooldown: str
    progression_guidance: str
    rationale: str
    confidence: str


@dataclass
class ApprovedWorkoutExercise:
    name: str
    sets: int
    reps_min: int
    reps_max: int
    rir_min: int
    rir_max: int
    notes: str
    equipment_required: list[str] = field(default_factory=list)


@dataclass
class ApprovedWorkoutPlan:
    title: str
    session_focus: str
    duration_minutes: int
    exercises: list[ApprovedWorkoutExercise]
    warmup: str
    cooldown: str
    progression_guidance: str
    rationale: str
    confidence: str
    scenario: str
    reason_codes: list[str] = field(default_factory=list)


@dataclass
class PlannedWorkoutExercise:
    id: int
    workout_plan_instance_id: int
    exercise_order: int
    name: str
    sets: int
    reps_min: int
    reps_max: int
    rir_min: int
    rir_max: int
    notes: str
    equipment_required: list[str] = field(default_factory=list)


@dataclass
class WorkoutPlanInstance:
    id: int
    user_id: int
    status: str
    scenario: str
    confidence: str
    title: str
    approved_workout_plan: ApprovedWorkoutPlan
    selected_at: str | None = None
    completed_at: str | None = None
    abandoned_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class WorkoutExecutionSession:
    id: int
    workout_plan_instance_id: int
    user_id: int
    status: str
    workout_session_id: int | None = None
    started_at: str | None = None
    completed_at: str | None = None
    abandoned_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class WorkoutExecutionSetActual:
    id: int
    workout_execution_session_id: int
    planned_workout_exercise_id: int | None
    workout_session_id: int | None
    workout_set_id: int | None
    exercise_name: str
    set_number: int
    planned_reps_min: int | None = None
    planned_reps_max: int | None = None
    planned_rir_min: int | None = None
    planned_rir_max: int | None = None
    actual_reps: int | None = None
    actual_weight: float | None = None
    actual_rir: int | None = None
    completed: bool = False
    skipped: bool = False
    substitution_for_planned_exercise_id: int | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class WorkoutPlanExerciseSubstitution:
    id: int
    workout_plan_instance_id: int
    workout_execution_session_id: int | None
    planned_workout_exercise_id: int
    original_exercise_name: str
    replacement_exercise_name: str
    replacement_catalog_exercise_id: int
    original_movement_pattern: str
    replacement_movement_pattern: str
    substitution_reason: str
    status: str
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class WorkoutPlannedVsActualSummary:
    workout_plan_instance_id: int
    workout_execution_session_id: int | None
    planned_exercise_count: int
    completed_exercise_count: int
    skipped_exercise_count: int
    substituted_exercise_count: int
    planned_set_count: int
    actual_set_count: int
    completed_set_count: int
    skipped_set_count: int
    completion_percentage: float
    average_planned_rir: float | None
    average_actual_rir: float | None
    rir_deviation: float | None
    rep_deviation: dict[str, int]
    sets_below_planned_reps: int
    sets_inside_planned_reps: int
    sets_above_planned_reps: int
    notes: list[str] = field(default_factory=list)
    deviation_flags: list[str] = field(default_factory=list)
