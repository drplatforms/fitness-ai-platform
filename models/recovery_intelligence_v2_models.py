from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

READINESS_CLASSIFICATION_VALUES = {
    "unknown",
    "recovery_limited",
    "manageable",
    "supportive",
    "improving",
    "mixed",
}
RECOVERY_PRESSURE_VALUES = {"unknown", "low", "moderate", "high"}
INDICATOR_STATUS_VALUES = {"unknown", "low", "borderline", "normal", "high", "mixed"}
TREND_DIRECTION_VALUES = {"unknown", "improving", "stable", "worsening", "mixed"}
DATA_QUALITY_STATUS_VALUES = {"missing", "limited", "partial", "usable", "strong"}
CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}
FATIGUE_SUPPORT_VALUES = {"unknown", "supportive", "limiting", "mixed"}
INDICATOR_NAME_VALUES = {
    "sleep",
    "energy",
    "soreness",
    "body_weight",
    "checkin_consistency",
}

_FORBIDDEN_RECOVERY_TEXT = (
    "overtraining",
    "injury",
    "illness",
    "diagnosis",
    "sleep disorder",
    "medical risk",
    "you must deload",
    "must deload",
    "you are not recovering",
    "failed recovery",
    "this caused stalled progress",
    "this caused fat gain",
    "this caused fat loss",
    "this proves nutrition is inadequate",
)


@dataclass(frozen=True)
class RecoveryV2IndicatorDay:
    date: str
    sleep_hours: float | None
    energy_level: float | None
    soreness_level: float | None
    body_weight_lb: float | None
    notes_present: bool
    data_quality_status: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_date(self.date)
        _validate_optional_non_negative("sleep_hours", self.sleep_hours)
        _validate_optional_non_negative("energy_level", self.energy_level)
        _validate_optional_non_negative("soreness_level", self.soreness_level)
        _validate_optional_non_negative("body_weight_lb", self.body_weight_lb)
        _validate_bool("notes_present", self.notes_present)
        _validate_allowed(
            "data_quality_status",
            self.data_quality_status,
            DATA_QUALITY_STATUS_VALUES,
        )
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecoveryBaseline:
    baseline_window_days: int
    start_date: str
    end_date: str
    checkin_days: int
    average_sleep_hours: float | None
    average_energy_level: float | None
    average_soreness_level: float | None
    latest_body_weight_lb: float | None
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("baseline_window_days", self.baseline_window_days)
        _validate_date(self.start_date)
        _validate_date(self.end_date)
        _validate_non_negative_int("checkin_days", self.checkin_days)
        _validate_optional_non_negative("average_sleep_hours", self.average_sleep_hours)
        _validate_optional_non_negative(
            "average_energy_level", self.average_energy_level
        )
        _validate_optional_non_negative(
            "average_soreness_level", self.average_soreness_level
        )
        _validate_optional_non_negative(
            "latest_body_weight_lb", self.latest_body_weight_lb
        )
        _validate_allowed("confidence", self.confidence, CONFIDENCE_VALUES)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        _validate_confidence_support(
            self.confidence,
            self.reason_codes,
            self.limitations,
            "Recovery baselines",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecoveryRecentDelta:
    comparison_name: str
    recent_window_days: int
    comparison_window_days: int
    sleep_delta: float | None
    energy_delta: float | None
    soreness_delta: float | None
    body_weight_delta: float | None
    trend_direction: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_required_text("comparison_name", self.comparison_name)
        _validate_positive_int("recent_window_days", self.recent_window_days)
        _validate_positive_int("comparison_window_days", self.comparison_window_days)
        _validate_optional_number("sleep_delta", self.sleep_delta)
        _validate_optional_number("energy_delta", self.energy_delta)
        _validate_optional_number("soreness_delta", self.soreness_delta)
        _validate_optional_number("body_weight_delta", self.body_weight_delta)
        _validate_allowed(
            "trend_direction", self.trend_direction, TREND_DIRECTION_VALUES
        )
        _validate_allowed("confidence", self.confidence, CONFIDENCE_VALUES)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        _validate_confidence_support(
            self.confidence,
            self.reason_codes,
            self.limitations,
            "Recovery deltas",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecoveryIndicatorInterpretation:
    indicator_name: str
    current_value: float | None
    baseline_value: float | None
    recent_average: float | None
    prior_average: float | None
    delta_from_baseline: float | None
    delta_recent_vs_prior: float | None
    status: str
    trend_direction: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_allowed("indicator_name", self.indicator_name, INDICATOR_NAME_VALUES)
        _validate_optional_number("current_value", self.current_value)
        _validate_optional_number("baseline_value", self.baseline_value)
        _validate_optional_number("recent_average", self.recent_average)
        _validate_optional_number("prior_average", self.prior_average)
        _validate_optional_number("delta_from_baseline", self.delta_from_baseline)
        _validate_optional_number("delta_recent_vs_prior", self.delta_recent_vs_prior)
        _validate_allowed("status", self.status, INDICATOR_STATUS_VALUES)
        _validate_allowed(
            "trend_direction", self.trend_direction, TREND_DIRECTION_VALUES
        )
        _validate_allowed("confidence", self.confidence, CONFIDENCE_VALUES)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        _validate_confidence_support(
            self.confidence,
            self.reason_codes,
            self.limitations,
            "Recovery indicator interpretations",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecoveryDataQuality:
    expected_days: int
    checkin_days: int
    checkin_rate: float
    missing_sleep_days: int
    missing_energy_days: int
    missing_soreness_days: int
    duplicate_days_collapsed: int
    stale_current_day: bool
    status: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("expected_days", self.expected_days)
        _validate_non_negative_int("checkin_days", self.checkin_days)
        _validate_rate("checkin_rate", self.checkin_rate)
        _validate_non_negative_int("missing_sleep_days", self.missing_sleep_days)
        _validate_non_negative_int("missing_energy_days", self.missing_energy_days)
        _validate_non_negative_int("missing_soreness_days", self.missing_soreness_days)
        _validate_non_negative_int(
            "duplicate_days_collapsed", self.duplicate_days_collapsed
        )
        _validate_bool("stale_current_day", self.stale_current_day)
        _validate_allowed("status", self.status, DATA_QUALITY_STATUS_VALUES)
        _validate_allowed("confidence", self.confidence, CONFIDENCE_VALUES)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        _validate_confidence_support(
            self.confidence,
            self.reason_codes,
            self.limitations,
            "Recovery data quality",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecoverySourceFact:
    source_table: str
    field_name: str
    observed_date: str | None
    value_summary: str
    confidence: str

    def __post_init__(self) -> None:
        _validate_required_text("source_table", self.source_table)
        _validate_required_text("field_name", self.field_name)
        if self.observed_date is not None:
            _validate_date(self.observed_date)
        _validate_required_text("value_summary", self.value_summary)
        _validate_allowed("confidence", self.confidence, CONFIDENCE_VALUES)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecoveryIntelligenceV2Summary:
    user_id: int
    target_date: str
    generated_at: str
    source_table: str
    model_version: str
    current_day: RecoveryV2IndicatorDay | None
    windows: dict[str, dict[str, Any]]
    baseline: RecoveryBaseline | None
    recent_vs_baseline: RecoveryRecentDelta | None
    recent_vs_prior: RecoveryRecentDelta | None
    sleep_interpretation: RecoveryIndicatorInterpretation
    energy_interpretation: RecoveryIndicatorInterpretation
    soreness_interpretation: RecoveryIndicatorInterpretation
    body_weight_interpretation: RecoveryIndicatorInterpretation | None
    checkin_consistency: RecoveryIndicatorInterpretation
    readiness_classification: str
    recovery_pressure: str
    fatigue_support: str
    data_quality: RecoveryDataQuality
    confidence: str
    source_facts: list[RecoverySourceFact] = field(default_factory=list)
    coach_safe_summary: str = ""
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_date(self.target_date)
        _validate_required_text("generated_at", self.generated_at)
        _validate_required_text("source_table", self.source_table)
        _validate_required_text("model_version", self.model_version)
        if not isinstance(self.windows, dict):
            raise ValueError("windows must be a dictionary")
        _validate_required_mapping_keys("windows", self.windows)
        _validate_allowed(
            "readiness_classification",
            self.readiness_classification,
            READINESS_CLASSIFICATION_VALUES,
        )
        _validate_allowed(
            "recovery_pressure", self.recovery_pressure, RECOVERY_PRESSURE_VALUES
        )
        _validate_allowed(
            "fatigue_support", self.fatigue_support, FATIGUE_SUPPORT_VALUES
        )
        _validate_allowed("confidence", self.confidence, CONFIDENCE_VALUES)
        _validate_safe_text("coach_safe_summary", self.coach_safe_summary)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        _validate_confidence_support(
            self.confidence,
            self.reason_codes,
            self.limitations,
            "Recovery v2 summaries",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_required_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    _validate_safe_text(name, value)


def _validate_date(value: str) -> None:
    _validate_required_text("date", value)
    parts = value.split("-")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError("Dates must use YYYY-MM-DD format")


def _validate_safe_text(name: str, value: str | None) -> None:
    if value is None:
        return
    lowered = value.lower()
    if any(term in lowered for term in _FORBIDDEN_RECOVERY_TEXT):
        raise ValueError(f"{name} contains forbidden recovery language")


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


def _validate_non_negative_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_optional_number(name: str, value: float | None) -> None:
    if value is not None and not isinstance(value, int | float):
        raise ValueError(f"{name} must be numeric when present")


def _validate_optional_non_negative(name: str, value: float | None) -> None:
    _validate_optional_number(name, value)
    if value is not None and value < 0:
        raise ValueError(f"{name} must be non-negative when present")


def _validate_rate(name: str, value: float) -> None:
    if not isinstance(value, int | float) or value < 0 or value > 1:
        raise ValueError(f"{name} must be between 0 and 1")


def _validate_bool(name: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")


def _validate_required_mapping_keys(name: str, value: dict[str, Any]) -> None:
    for key in value:
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"{name} keys must be non-empty strings")


def _validate_confidence_support(
    confidence: str,
    reason_codes: list[str],
    limitations: list[str],
    context: str,
) -> None:
    if confidence in {"Limited", "Low"} and not (reason_codes or limitations):
        raise ValueError(
            f"{context} require reason_codes or limitations when confidence is Limited/Low"
        )
