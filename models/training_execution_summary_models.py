from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TrainingExecutionSummary:
    user_id: int
    completed_execution_count: int
    recent_plan_instance_ids: list[int]
    average_completion_percentage: float | None
    average_planned_rir: float | None
    average_actual_rir: float | None
    average_rir_deviation: float | None
    skipped_exercise_count: int
    substituted_exercise_count: int
    sets_below_planned_reps: int
    sets_inside_planned_reps: int
    sets_above_planned_reps: int
    incomplete_logging_count: int
    missing_actual_rir_count: int
    missing_actual_reps_count: int
    execution_quality: str
    execution_effort_trend: str
    execution_completion_trend: str
    confidence: str
    reason_codes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)
