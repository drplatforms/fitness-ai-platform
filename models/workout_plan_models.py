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
