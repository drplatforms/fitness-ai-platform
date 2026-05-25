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
