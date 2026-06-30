from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SLEEP_SIGNAL_VALUES = {"unknown", "low", "borderline", "adequate"}
ENERGY_SIGNAL_VALUES = {"unknown", "low", "usable", "strong"}
SORENESS_SIGNAL_VALUES = {"unknown", "low", "moderate", "high"}
READINESS_LEVEL_VALUES = {"unknown", "low", "moderate", "high"}
FATIGUE_RISK_VALUES = {"unknown", "low", "moderate", "high"}
TREND_DIRECTION_VALUES = {"unknown", "improving", "stable", "worsening", "mixed"}
CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}


@dataclass(frozen=True)
class RecoverySignalDay:
    date: str
    sleep_hours: float | None
    energy_level: float | None
    soreness_level: float | None
    body_weight_lb: float | None
    mood: str | None
    notes_present: bool
    data_quality_flags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_date(self.date)
        _validate_optional_non_negative("sleep_hours", self.sleep_hours)
        _validate_optional_non_negative("energy_level", self.energy_level)
        _validate_optional_non_negative("soreness_level", self.soreness_level)
        _validate_optional_non_negative("body_weight_lb", self.body_weight_lb)
        _validate_safe_text_list("data_quality_flags", self.data_quality_flags)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecoveryWindowSummary:
    window_days: int
    start_date: str
    end_date: str
    expected_days: int
    checkin_days: int
    checkin_rate: float
    average_sleep_hours: float | None
    average_energy_level: float | None
    average_soreness_level: float | None
    latest_body_weight_lb: float | None
    body_weight_delta_lb: float | None
    sleep_signal: str
    energy_signal: str
    soreness_signal: str
    readiness_level: str
    fatigue_risk: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("window_days", self.window_days)
        _validate_date(self.start_date)
        _validate_date(self.end_date)
        _validate_positive_int("expected_days", self.expected_days)
        _validate_non_negative_int("checkin_days", self.checkin_days)
        _validate_rate("checkin_rate", self.checkin_rate)
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
        _validate_optional_number("body_weight_delta_lb", self.body_weight_delta_lb)
        _validate_allowed("sleep_signal", self.sleep_signal, SLEEP_SIGNAL_VALUES)
        _validate_allowed("energy_signal", self.energy_signal, ENERGY_SIGNAL_VALUES)
        _validate_allowed(
            "soreness_signal", self.soreness_signal, SORENESS_SIGNAL_VALUES
        )
        _validate_allowed(
            "readiness_level", self.readiness_level, READINESS_LEVEL_VALUES
        )
        _validate_allowed("fatigue_risk", self.fatigue_risk, FATIGUE_RISK_VALUES)
        _validate_allowed("confidence", self.confidence, CONFIDENCE_VALUES)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        if self.confidence in {"Limited", "Low"} and not (
            self.reason_codes or self.limitations
        ):
            raise ValueError(
                "Limited/Low recovery windows require reason_codes or limitations"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecoveryTrendComparison:
    recent_window_days: int
    prior_window_days: int
    sleep_delta: float | None
    energy_delta: float | None
    soreness_delta: float | None
    body_weight_delta: float | None
    trend_direction: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("recent_window_days", self.recent_window_days)
        _validate_positive_int("prior_window_days", self.prior_window_days)
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
        if self.confidence in {"Limited", "Low"} and not (
            self.reason_codes or self.limitations
        ):
            raise ValueError(
                "Limited/Low recovery trend comparisons require reason_codes or limitations"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecoveryIntelligenceSummary:
    user_id: int
    target_date: str
    generated_at: str
    source_table: str
    model_version: str
    current_day: RecoverySignalDay | None
    windows: dict[str, RecoveryWindowSummary]
    trend_comparison: RecoveryTrendComparison | None
    readiness_level: str
    fatigue_risk: str
    confidence: str
    source_facts: list[str] = field(default_factory=list)
    coach_safe_summary: str = ""
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_date(self.target_date)
        _validate_required_text("generated_at", self.generated_at)
        _validate_required_text("source_table", self.source_table)
        _validate_required_text("model_version", self.model_version)
        _validate_allowed(
            "readiness_level", self.readiness_level, READINESS_LEVEL_VALUES
        )
        _validate_allowed("fatigue_risk", self.fatigue_risk, FATIGUE_RISK_VALUES)
        _validate_allowed("confidence", self.confidence, CONFIDENCE_VALUES)
        _validate_safe_text_list("source_facts", self.source_facts)
        _validate_safe_text("coach_safe_summary", self.coach_safe_summary)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)

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
    forbidden = ("overtraining", "injury", "illness", "sleep disorder", "diagnosis")
    if any(term in lowered for term in forbidden):
        raise ValueError(f"{name} contains diagnostic language")


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
