from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

COMPLETION_INDICATOR_VALUES = {
    "unknown",
    "no_planned_execution_data",
    "limited_data",
    "mostly_completed",
    "partially_completed",
    "frequently_incomplete",
}
EFFORT_INDICATOR_VALUES = {
    "unknown",
    "as_planned",
    "harder_than_planned",
    "easier_than_planned",
    "mixed",
    "limited_effort_data",
}
REP_RANGE_INDICATOR_VALUES = {
    "unknown",
    "mostly_inside_range",
    "often_below_range",
    "often_above_range",
    "mixed",
    "limited_rep_data",
}
LOAD_INDICATOR_VALUES = {
    "unknown",
    "increasing",
    "stable",
    "decreasing",
    "mixed",
    "insufficient_comparable_load_data",
}
LOGGING_QUALITY_VALUES = {
    "unknown",
    "complete",
    "mostly_complete",
    "incomplete",
    "limited",
}
CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

_FORBIDDEN_COACH_TEXT = (
    "overtraining",
    "injury",
    "medical",
    "failed",
    "failure",
    "lack of discipline",
    "poor adherence",
    "automatic deload",
    "must deload",
    "add weight automatically",
    "increase load automatically",
    "programming failure",
)


@dataclass(frozen=True)
class WorkoutSetSessionSummary:
    workout_plan_instance_id: int
    workout_execution_session_id: int | None
    workout_date: str | None
    workout_title: str | None
    planned_exercise_count: int
    planned_set_count: int
    completed_set_count: int
    skipped_set_count: int
    completion_percentage: float | None
    average_planned_rir: float | None
    average_actual_rir: float | None
    rir_delta: float | None
    sets_below_planned_reps: int
    sets_inside_planned_reps: int
    sets_above_planned_reps: int
    missing_actual_reps_count: int
    missing_actual_rir_count: int
    missing_actual_weight_count: int
    completion_indicator: str
    effort_indicator: str
    rep_range_indicator: str
    logging_quality: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int(
            "workout_plan_instance_id", self.workout_plan_instance_id
        )
        _validate_optional_positive_int(
            "workout_execution_session_id", self.workout_execution_session_id
        )
        _validate_optional_text("workout_date", self.workout_date)
        _validate_optional_text("workout_title", self.workout_title)
        _validate_non_negative_int(
            "planned_exercise_count", self.planned_exercise_count
        )
        _validate_non_negative_int("planned_set_count", self.planned_set_count)
        _validate_non_negative_int("completed_set_count", self.completed_set_count)
        _validate_non_negative_int("skipped_set_count", self.skipped_set_count)
        _validate_optional_rate_percent(
            "completion_percentage", self.completion_percentage
        )
        _validate_optional_number("average_planned_rir", self.average_planned_rir)
        _validate_optional_number("average_actual_rir", self.average_actual_rir)
        _validate_optional_number("rir_delta", self.rir_delta)
        _validate_non_negative_int(
            "sets_below_planned_reps", self.sets_below_planned_reps
        )
        _validate_non_negative_int(
            "sets_inside_planned_reps", self.sets_inside_planned_reps
        )
        _validate_non_negative_int(
            "sets_above_planned_reps", self.sets_above_planned_reps
        )
        _validate_non_negative_int(
            "missing_actual_reps_count", self.missing_actual_reps_count
        )
        _validate_non_negative_int(
            "missing_actual_rir_count", self.missing_actual_rir_count
        )
        _validate_non_negative_int(
            "missing_actual_weight_count", self.missing_actual_weight_count
        )
        _validate_allowed(
            "completion_indicator",
            self.completion_indicator,
            COMPLETION_INDICATOR_VALUES,
        )
        _validate_allowed(
            "effort_indicator", self.effort_indicator, EFFORT_INDICATOR_VALUES
        )
        _validate_allowed(
            "rep_range_indicator",
            self.rep_range_indicator,
            REP_RANGE_INDICATOR_VALUES,
        )
        _validate_allowed(
            "logging_quality", self.logging_quality, LOGGING_QUALITY_VALUES
        )
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkoutExerciseSetIndicator:
    exercise_name: str
    planned_session_count: int
    planned_set_count: int
    completed_set_count: int
    skipped_set_count: int
    completion_percentage: float | None
    latest_actual_weight: float | None
    prior_actual_weight: float | None
    weight_delta: float | None
    average_actual_reps: float | None
    average_actual_rir: float | None
    average_planned_rir: float | None
    rir_delta: float | None
    sets_below_planned_reps: int
    sets_inside_planned_reps: int
    sets_above_planned_reps: int
    completion_indicator: str
    effort_indicator: str
    rep_range_indicator: str
    load_indicator: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_required_text("exercise_name", self.exercise_name)
        _validate_non_negative_int("planned_session_count", self.planned_session_count)
        _validate_non_negative_int("planned_set_count", self.planned_set_count)
        _validate_non_negative_int("completed_set_count", self.completed_set_count)
        _validate_non_negative_int("skipped_set_count", self.skipped_set_count)
        _validate_optional_rate_percent(
            "completion_percentage", self.completion_percentage
        )
        _validate_optional_number("latest_actual_weight", self.latest_actual_weight)
        _validate_optional_number("prior_actual_weight", self.prior_actual_weight)
        _validate_optional_number("weight_delta", self.weight_delta)
        _validate_optional_number("average_actual_reps", self.average_actual_reps)
        _validate_optional_number("average_actual_rir", self.average_actual_rir)
        _validate_optional_number("average_planned_rir", self.average_planned_rir)
        _validate_optional_number("rir_delta", self.rir_delta)
        _validate_non_negative_int(
            "sets_below_planned_reps", self.sets_below_planned_reps
        )
        _validate_non_negative_int(
            "sets_inside_planned_reps", self.sets_inside_planned_reps
        )
        _validate_non_negative_int(
            "sets_above_planned_reps", self.sets_above_planned_reps
        )
        _validate_allowed(
            "completion_indicator",
            self.completion_indicator,
            COMPLETION_INDICATOR_VALUES,
        )
        _validate_allowed(
            "effort_indicator", self.effort_indicator, EFFORT_INDICATOR_VALUES
        )
        _validate_allowed(
            "rep_range_indicator", self.rep_range_indicator, REP_RANGE_INDICATOR_VALUES
        )
        _validate_allowed("load_indicator", self.load_indicator, LOAD_INDICATOR_VALUES)
        _validate_allowed("confidence", self.confidence, CONFIDENCE_VALUES)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        if self.confidence in {"Limited", "Low"} and not (
            self.reason_codes or self.limitations
        ):
            raise ValueError(
                "Limited/Low exercise indicators require reason or limitation"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkoutSetIntelligenceSummary:
    user_id: int
    target_date: str
    generated_at: str
    source_tables: list[str]
    model_version: str
    completed_execution_count: int
    recent_plan_instance_ids: list[int]
    session_summaries: list[WorkoutSetSessionSummary]
    exercise_indicators: list[WorkoutExerciseSetIndicator]
    overall_completion_indicator: str
    overall_effort_indicator: str
    overall_rep_range_indicator: str
    overall_logging_quality: str
    confidence: str
    source_facts: list[str] = field(default_factory=list)
    coach_safe_summary: str = ""
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_required_text("target_date", self.target_date)
        _validate_required_text("generated_at", self.generated_at)
        if not self.source_tables:
            raise ValueError("source_tables are required")
        _validate_safe_text_list("source_tables", self.source_tables)
        _validate_required_text("model_version", self.model_version)
        _validate_non_negative_int(
            "completed_execution_count", self.completed_execution_count
        )
        for plan_id in self.recent_plan_instance_ids:
            _validate_positive_int("recent_plan_instance_id", plan_id)
        _validate_allowed(
            "overall_completion_indicator",
            self.overall_completion_indicator,
            COMPLETION_INDICATOR_VALUES,
        )
        _validate_allowed(
            "overall_effort_indicator",
            self.overall_effort_indicator,
            EFFORT_INDICATOR_VALUES,
        )
        _validate_allowed(
            "overall_rep_range_indicator",
            self.overall_rep_range_indicator,
            REP_RANGE_INDICATOR_VALUES,
        )
        _validate_allowed(
            "overall_logging_quality",
            self.overall_logging_quality,
            LOGGING_QUALITY_VALUES,
        )
        _validate_allowed("confidence", self.confidence, CONFIDENCE_VALUES)
        _validate_safe_text_list("source_facts", self.source_facts)
        _validate_safe_text("coach_safe_summary", self.coach_safe_summary)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        if self.confidence in {"Limited", "Low"} and not (
            self.reason_codes or self.limitations
        ):
            raise ValueError("Limited/Low summaries require reason or limitation")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_required_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    _validate_safe_text(name, value)


def _validate_optional_text(name: str, value: str | None) -> None:
    if value is not None:
        _validate_required_text(name, value)


def _validate_safe_text(name: str, value: str | None) -> None:
    if value is None:
        return
    lowered = value.lower()
    if any(term in lowered for term in _FORBIDDEN_COACH_TEXT):
        raise ValueError(f"{name} contains forbidden training language")


def _validate_safe_text_list(name: str, values: list[str]) -> None:
    if not isinstance(values, list):
        raise ValueError(f"{name} must be a list")
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"{name} must contain strings")
        _validate_safe_text(name, value)


def _validate_allowed(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}")


def _validate_positive_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_optional_positive_int(name: str, value: int | None) -> None:
    if value is not None:
        _validate_positive_int(name, value)


def _validate_non_negative_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_optional_number(name: str, value: float | None) -> None:
    if value is not None and not isinstance(value, int | float):
        raise ValueError(f"{name} must be numeric when present")


def _validate_optional_rate_percent(name: str, value: float | None) -> None:
    _validate_optional_number(name, value)
    if value is not None and (value < 0 or value > 100):
        raise ValueError(f"{name} must be between 0 and 100")
