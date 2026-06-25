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
    workout_size_preference: str = "standard"
    requested_exercise_count: int = 5
    final_target_exercise_count: int = 5
    exercise_count_reason: str = "standard_session"
    exercise_count_user_reason: str = "Built as a standard 5-exercise session."
    preview_variation_index: int = 0


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
    catalog_exercise_id: int | None = None
    movement_pattern: str | None = None
    target_zone: str | None = None


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
    workout_size_preference: str = "standard"
    requested_exercise_count: int = 5
    final_target_exercise_count: int = 5
    exercise_count_reason: str = "standard_session"
    exercise_count_user_reason: str = "Built as a standard 5-exercise session."


@dataclass
class CandidateWorkoutExplanation:
    session_summary: str
    why_this_fits_today: str
    focus_cue: str
    recovery_context: str
    nutrition_or_logging_context: str
    confidence: str


@dataclass
class ApprovedWorkoutExplanation:
    session_summary: str
    why_this_fits_today: str
    focus_cue: str
    recovery_context: str
    nutrition_or_logging_context: str
    confidence: str


@dataclass
class WorkoutExplanationRuntimeMetadata:
    configured_provider: str
    selected_provider: str
    crewai_attempted: bool
    fallback_used: bool
    fallback_reason: str | None
    explanation_valid: bool
    validation_errors: list[str] = field(default_factory=list)
    candidate_parse_status: str = "not_attempted"
    candidate_validation_status: str = "not_attempted"
    final_explanation_source: str = "deterministic"
    raw_output_length: int | None = None
    raw_output_preview_truncated: str | None = None
    markdown_wrapper_detected: bool = False


@dataclass
class ApprovedWorkoutExplanationResult:
    approved_workout_explanation: ApprovedWorkoutExplanation
    runtime_metadata: WorkoutExplanationRuntimeMetadata


@dataclass
class WorkoutPlanRuntimeMetadata:
    configured_provider: str
    selected_provider: str
    crewai_attempted: bool
    fallback_used: bool
    fallback_reason: str | None
    candidate_valid: bool
    validation_errors: list[str] = field(default_factory=list)
    candidate_parse_status: str = "not_attempted"
    candidate_validation_status: str = "not_attempted"
    final_plan_source: str = "deterministic"
    raw_output_length: int | None = None
    raw_output_preview_truncated: str | None = None
    markdown_wrapper_detected: bool = False


@dataclass
class ApprovedWorkoutPlanResult:
    approved_workout_plan: ApprovedWorkoutPlan
    runtime_metadata: WorkoutPlanRuntimeMetadata


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


@dataclass
class CandidatePostWorkoutReviewSummary:
    session_summary: str
    completion_reflection: str
    effort_reflection: str
    reps_or_volume_reflection: str
    substitutions_or_skips_context: str
    logging_quality_note: str
    next_time_focus: str
    confidence: str


@dataclass
class ApprovedPostWorkoutReviewSummary:
    session_summary: str
    completion_reflection: str
    effort_reflection: str
    reps_or_volume_reflection: str
    substitutions_or_skips_context: str
    logging_quality_note: str
    next_time_focus: str
    confidence: str


@dataclass
class PostWorkoutReviewRuntimeMetadata:
    configured_provider: str
    selected_provider: str
    crewai_attempted: bool
    fallback_used: bool
    fallback_reason: str | None
    review_valid: bool
    validation_errors: list[str] = field(default_factory=list)
    candidate_parse_status: str = "not_attempted"
    candidate_validation_status: str = "not_attempted"
    final_review_source: str = "deterministic"
    raw_output_length: int | None = None
    raw_output_preview_truncated: str | None = None
    markdown_wrapper_detected: bool = False


@dataclass
class ApprovedPostWorkoutReviewSummaryResult:
    approved_post_workout_review_summary: ApprovedPostWorkoutReviewSummary
    runtime_metadata: PostWorkoutReviewRuntimeMetadata


@dataclass
class PostWorkoutReviewContext:
    user_id: int
    execution_id: int
    plan_instance_id: int
    scenario: str
    confidence: str
    workout_title: str
    planned_duration_minutes: int
    completed_at: str | None
    completion_status: str
    exercise_count_planned: int
    exercise_count_completed: int
    planned_sets: int
    completed_sets: int
    skipped_exercise_count: int
    substitution_count: int
    planned_rir_range: list[float | None]
    actual_rir_average: float | None
    actual_rir_min: int | None
    actual_rir_max: int | None
    effort_delta_summary: str
    reps_completed_summary: str
    volume_completion_summary: str
    logging_completeness: str
    safety_constraints: list[str]
    approved_summary_facts: list[str]
    approved_workout_plan: ApprovedWorkoutPlan
    planned_vs_actual_summary: WorkoutPlannedVsActualSummary
