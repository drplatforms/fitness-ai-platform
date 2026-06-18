from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

NUTRITION_TREND_CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

LOGGING_COMPLETENESS_NO_LOGS = "no_logs"
LOGGING_COMPLETENESS_PARTIAL_DAY = "partial_day"
LOGGING_COMPLETENESS_LIKELY_INCOMPLETE = "likely_incomplete"
LOGGING_COMPLETENESS_REASONABLY_COMPLETE = "reasonably_complete"
LOGGING_COMPLETENESS_COMPLETE_ENOUGH = "complete_enough_for_guidance"

NUTRITION_TREND_LOGGING_COMPLETENESS_VALUES = {
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
}

LOGGING_CONSISTENCY_INSUFFICIENT = "insufficient"
LOGGING_CONSISTENCY_INCONSISTENT = "inconsistent"
LOGGING_CONSISTENCY_USABLE = "usable"
LOGGING_CONSISTENCY_STRONG = "strong"

LOGGING_CONSISTENCY_VALUES = {
    LOGGING_CONSISTENCY_INSUFFICIENT,
    LOGGING_CONSISTENCY_INCONSISTENT,
    LOGGING_CONSISTENCY_USABLE,
    LOGGING_CONSISTENCY_STRONG,
}

BODYWEIGHT_TREND_DECREASING = "decreasing"
BODYWEIGHT_TREND_STABLE = "stable"
BODYWEIGHT_TREND_INCREASING = "increasing"
BODYWEIGHT_TREND_UNAVAILABLE = "unavailable"

BODYWEIGHT_TREND_DIRECTIONS = {
    BODYWEIGHT_TREND_DECREASING,
    BODYWEIGHT_TREND_STABLE,
    BODYWEIGHT_TREND_INCREASING,
    BODYWEIGHT_TREND_UNAVAILABLE,
}

CALIBRATION_READINESS_NOT_READY = "not_ready"
CALIBRATION_READINESS_EARLY_SIGNAL = "early_signal"
CALIBRATION_READINESS_USABLE = "usable"
CALIBRATION_READINESS_STRONG = "strong"

CALIBRATION_READINESS_LEVELS = {
    CALIBRATION_READINESS_NOT_READY,
    CALIBRATION_READINESS_EARLY_SIGNAL,
    CALIBRATION_READINESS_USABLE,
    CALIBRATION_READINESS_STRONG,
}

FORBIDDEN_NUTRITION_TREND_LANGUAGE = {
    "true maintenance is exactly",
    "failed your target",
    "must cut calories",
    "metabolism is damaged",
    "fat-loss guarantee",
    "fat loss guarantee",
    "guaranteed fat loss",
    "medical treatment",
    "disease treatment",
    "ai-generated target",
    "ai generated target",
}


@dataclass
class NutritionTrendDay:
    date: str
    logged_calories: float | None = None
    logged_protein: float | None = None
    logged_carbohydrate: float | None = None
    logged_fat: float | None = None
    logging_completeness: str = LOGGING_COMPLETENESS_NO_LOGS
    confidence: str = "Limited"
    bodyweight_lb: float | None = None
    training_day: bool = False
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_required_text("date", self.date)
        _validate_logging_completeness(self.logging_completeness)
        _validate_confidence(self.confidence)
        _validate_optional_non_negative("logged_calories", self.logged_calories)
        _validate_optional_non_negative("logged_protein", self.logged_protein)
        _validate_optional_non_negative("logged_carbohydrate", self.logged_carbohydrate)
        _validate_optional_non_negative("logged_fat", self.logged_fat)
        _validate_optional_non_negative("bodyweight_lb", self.bodyweight_lb)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)

        if self.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS:
            logged_values = (
                self.logged_calories,
                self.logged_protein,
                self.logged_carbohydrate,
                self.logged_fat,
            )
            if any(value is not None for value in logged_values):
                raise ValueError("No-log days must not include logged nutrient values")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NutritionIntakeTrendSummary:
    average_calories: float | None = None
    average_protein_g: float | None = None
    average_carbohydrate_g: float | None = None
    average_fat_g: float | None = None
    calorie_target_hit_rate: float | None = None
    protein_target_hit_rate: float | None = None
    complete_logging_rate: float | None = None
    logging_consistency_status: str = LOGGING_CONSISTENCY_INSUFFICIENT
    confidence: str = "Limited"
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_optional_non_negative("average_calories", self.average_calories)
        _validate_optional_non_negative("average_protein_g", self.average_protein_g)
        _validate_optional_non_negative(
            "average_carbohydrate_g", self.average_carbohydrate_g
        )
        _validate_optional_non_negative("average_fat_g", self.average_fat_g)
        _validate_optional_rate("calorie_target_hit_rate", self.calorie_target_hit_rate)
        _validate_optional_rate("protein_target_hit_rate", self.protein_target_hit_rate)
        _validate_optional_rate("complete_logging_rate", self.complete_logging_rate)
        _validate_logging_consistency_status(self.logging_consistency_status)
        _validate_confidence(self.confidence)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)

        if self.logging_consistency_status in {
            LOGGING_CONSISTENCY_INSUFFICIENT,
            LOGGING_CONSISTENCY_INCONSISTENT,
        } and not (self.reason_codes or self.limitations):
            raise ValueError(
                "Insufficient or inconsistent logging summaries require reason_codes or limitations"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BodyweightTrendSummary:
    weigh_in_count: int = 0
    start_weight_lb: float | None = None
    end_weight_lb: float | None = None
    average_weight_lb: float | None = None
    trend_direction: str = BODYWEIGHT_TREND_UNAVAILABLE
    weekly_rate_lb: float | None = None
    confidence: str = "Limited"
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_non_negative_int("weigh_in_count", self.weigh_in_count)
        _validate_optional_non_negative("start_weight_lb", self.start_weight_lb)
        _validate_optional_non_negative("end_weight_lb", self.end_weight_lb)
        _validate_optional_non_negative("average_weight_lb", self.average_weight_lb)
        _validate_bodyweight_trend_direction(self.trend_direction)
        _validate_optional_number("weekly_rate_lb", self.weekly_rate_lb)
        _validate_confidence(self.confidence)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)

        if self.trend_direction == BODYWEIGHT_TREND_UNAVAILABLE:
            if self.weigh_in_count > 0 or any(
                value is not None
                for value in (
                    self.start_weight_lb,
                    self.end_weight_lb,
                    self.average_weight_lb,
                    self.weekly_rate_lb,
                )
            ):
                raise ValueError(
                    "Unavailable bodyweight trend must not include trend values"
                )
            if not (self.reason_codes or self.limitations):
                raise ValueError(
                    "Unavailable bodyweight trend requires reason_codes or limitations"
                )
        elif self.weigh_in_count <= 0:
            raise ValueError("Available bodyweight trends require weigh_in_count")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NutritionCalibrationReadiness:
    calibration_allowed: bool
    readiness_level: str
    minimum_window_met: bool
    preferred_window_met: bool
    logging_quality_met: bool
    bodyweight_trend_available: bool
    goal_context_available: bool
    training_context_available: bool
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_readiness_level(self.readiness_level)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)

        if (
            self.readiness_level == CALIBRATION_READINESS_NOT_READY
            and self.calibration_allowed
        ):
            raise ValueError("not_ready calibration readiness cannot allow calibration")

        if self.calibration_allowed and self.readiness_level not in {
            CALIBRATION_READINESS_USABLE,
            CALIBRATION_READINESS_STRONG,
        }:
            raise ValueError("calibration_allowed requires usable or strong readiness")

        if self.calibration_allowed and not all(
            (
                self.minimum_window_met,
                self.logging_quality_met,
                self.bodyweight_trend_available,
                self.goal_context_available,
            )
        ):
            raise ValueError(
                "calibration_allowed requires minimum window, logging quality, "
                "bodyweight trend, and goal context"
            )

        if not self.calibration_allowed and not (self.reason_codes or self.limitations):
            raise ValueError(
                "Readiness states that do not allow calibration require reason_codes or limitations"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NutritionTrendWindowMetadata:
    model_name: str = "deterministic_nutrition_trend_window"
    model_version: str = "v1"
    generated_at: str | None = None
    inputs_used: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_required_text("model_name", self.model_name)
        _validate_required_text("model_version", self.model_version)
        _validate_safe_text_list("inputs_used", self.inputs_used)
        _validate_safe_text_list("assumptions", self.assumptions)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)

        if self.assumptions and not self.limitations:
            raise ValueError("limitations are required when assumptions are used")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NutritionTrendWindow:
    user_id: int
    start_date: str
    end_date: str
    window_days: int
    logged_day_count: int
    complete_logging_day_count: int
    partial_logging_day_count: int
    no_log_day_count: int
    intake_trend_summary: NutritionIntakeTrendSummary
    bodyweight_trend_summary: BodyweightTrendSummary
    calibration_readiness: NutritionCalibrationReadiness
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    trend_days: list[NutritionTrendDay] = field(default_factory=list)
    metadata: NutritionTrendWindowMetadata = field(
        default_factory=NutritionTrendWindowMetadata
    )

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_required_text("start_date", self.start_date)
        _validate_required_text("end_date", self.end_date)
        _validate_positive_int("window_days", self.window_days)
        _validate_non_negative_int("logged_day_count", self.logged_day_count)
        _validate_non_negative_int(
            "complete_logging_day_count", self.complete_logging_day_count
        )
        _validate_non_negative_int(
            "partial_logging_day_count", self.partial_logging_day_count
        )
        _validate_non_negative_int("no_log_day_count", self.no_log_day_count)
        _validate_confidence(self.confidence)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        _validate_type(
            "intake_trend_summary",
            self.intake_trend_summary,
            NutritionIntakeTrendSummary,
        )
        _validate_type(
            "bodyweight_trend_summary",
            self.bodyweight_trend_summary,
            BodyweightTrendSummary,
        )
        _validate_type(
            "calibration_readiness",
            self.calibration_readiness,
            NutritionCalibrationReadiness,
        )
        _validate_type("metadata", self.metadata, NutritionTrendWindowMetadata)
        _validate_list_items("trend_days", self.trend_days, NutritionTrendDay)
        self._validate_day_counts()

        if self.confidence in {"Limited", "Low"} and not (
            self.reason_codes or self.limitations
        ):
            raise ValueError(
                "Limited/Low trend windows require reason_codes or limitations"
            )

    def _validate_day_counts(self) -> None:
        if self.logged_day_count != (
            self.complete_logging_day_count + self.partial_logging_day_count
        ):
            raise ValueError(
                "logged_day_count must equal complete_logging_day_count + partial_logging_day_count"
            )

        counted_days = self.logged_day_count + self.no_log_day_count
        if counted_days != self.window_days:
            raise ValueError(
                "window_days must equal logged_day_count + no_log_day_count"
            )

        if self.trend_days and len(self.trend_days) > self.window_days:
            raise ValueError("trend_days cannot exceed window_days")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["intake_trend_summary"] = self.intake_trend_summary.to_dict()
        payload["bodyweight_trend_summary"] = self.bodyweight_trend_summary.to_dict()
        payload["calibration_readiness"] = self.calibration_readiness.to_dict()
        payload["trend_days"] = [day.to_dict() for day in self.trend_days]
        payload["metadata"] = self.metadata.to_dict()
        return payload


def _validate_confidence(confidence: str) -> None:
    if confidence not in NUTRITION_TREND_CONFIDENCE_VALUES:
        raise ValueError(f"Invalid confidence: {confidence}")


def _validate_logging_completeness(logging_completeness: str) -> None:
    if logging_completeness not in NUTRITION_TREND_LOGGING_COMPLETENESS_VALUES:
        raise ValueError(f"Invalid logging_completeness: {logging_completeness}")


def _validate_logging_consistency_status(logging_consistency_status: str) -> None:
    if logging_consistency_status not in LOGGING_CONSISTENCY_VALUES:
        raise ValueError(
            f"Invalid logging_consistency_status: {logging_consistency_status}"
        )


def _validate_bodyweight_trend_direction(trend_direction: str) -> None:
    if trend_direction not in BODYWEIGHT_TREND_DIRECTIONS:
        raise ValueError(f"Invalid trend_direction: {trend_direction}")


def _validate_readiness_level(readiness_level: str) -> None:
    if readiness_level not in CALIBRATION_READINESS_LEVELS:
        raise ValueError(f"Invalid readiness_level: {readiness_level}")


def _validate_required_text(field_name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_positive_int(field_name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_non_negative_int(field_name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_optional_non_negative(field_name: str, value: float | None) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_optional_number(field_name: str, value: float | None) -> None:
    if value is not None and not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be numeric")


def _validate_optional_rate(field_name: str, value: float | None) -> None:
    if value is not None and not 0 <= value <= 1:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _validate_type(field_name: str, value: object, expected_type: type) -> None:
    if not isinstance(value, expected_type):
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def _validate_list_items(field_name: str, values: list, expected_type: type) -> None:
    for value in values:
        if not isinstance(value, expected_type):
            raise ValueError(
                f"{field_name} must contain {expected_type.__name__} items"
            )


def _validate_safe_text_list(field_name: str, values: list[str]) -> None:
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must contain strings")
        normalized_value = value.lower()
        for phrase in FORBIDDEN_NUTRITION_TREND_LANGUAGE:
            if phrase in normalized_value:
                raise ValueError("Forbidden nutrition trend language is not allowed")
