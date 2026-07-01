from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

RECOVERY_AWARE_COACH_COPY_CONTRACT_VERSION = "recovery_aware_coach_copy_contract_v1"

CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}
DATA_QUALITY_STATUS_VALUES = {"missing", "limited", "partial", "usable", "strong"}
RECOVERY_PRESSURE_VALUES = {"unknown", "low", "moderate", "high"}

_FORBIDDEN_COPY_TERMS = (
    "overtraining",
    "injury",
    "illness",
    "diagnosis",
    "sleep disorder",
    "medical risk",
    "treatment",
    "must deload",
    "forced deload",
    "automatic deload",
    "automatic progression",
    "fat gain caused by recovery",
    "fat loss caused by recovery",
    "nutrition blame caused by recovery",
    "you should not train",
    "you are unsafe to train",
)


@dataclass(frozen=True)
class RecoveryAwareCoachCopyContract:
    user_id: int
    target_date: str
    recovery_v2_available: bool
    recovery_classification: str
    recovery_pressure: str
    confidence: str
    data_quality_status: str
    allowed_recovery_claims: list[str] = field(default_factory=list)
    required_caveats: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    copy_tone_guidance: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    source_services: list[str] = field(default_factory=list)
    contract_version: str = RECOVERY_AWARE_COACH_COPY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_date("target_date", self.target_date)
        _validate_bool("recovery_v2_available", self.recovery_v2_available)
        _validate_required_text("recovery_classification", self.recovery_classification)
        _validate_allowed(
            "recovery_pressure", self.recovery_pressure, RECOVERY_PRESSURE_VALUES
        )
        _validate_allowed("confidence", self.confidence, CONFIDENCE_VALUES)
        _validate_allowed(
            "data_quality_status",
            self.data_quality_status,
            DATA_QUALITY_STATUS_VALUES,
        )
        _validate_safe_text_list(
            "allowed_recovery_claims", self.allowed_recovery_claims
        )
        _validate_safe_text_list("required_caveats", self.required_caveats)
        _validate_safe_text_list("forbidden_claims", self.forbidden_claims)
        _validate_safe_text_list("copy_tone_guidance", self.copy_tone_guidance)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        _validate_safe_text_list("source_services", self.source_services)
        _validate_required_text("contract_version", self.contract_version)
        if self.confidence in {"Limited", "Low"} and not (
            self.required_caveats or self.limitations or self.reason_codes
        ):
            raise ValueError(
                "Limited/Low recovery copy contracts require caveats, "
                "reason_codes, or limitations"
            )
        if not self.recovery_v2_available and self.recovery_classification != "unknown":
            raise ValueError(
                "unavailable recovery v2 contracts must use unknown classification"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_positive_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_bool(name: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")


def _validate_date(name: str, value: str) -> None:
    _validate_required_text(name, value)
    parts = value.split("-")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError(f"{name} must use YYYY-MM-DD format")


def _validate_required_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    _validate_safe_text(name, value)


def _validate_allowed(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}")


def _validate_safe_text_list(name: str, values: list[str]) -> None:
    if not isinstance(values, list):
        raise ValueError(f"{name} must be a list")
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"{name} must contain strings")
        _validate_safe_text(name, value)


def _validate_safe_text(name: str, value: str | None) -> None:
    if value is None:
        return
    lowered = value.lower()
    if any(term in lowered for term in _FORBIDDEN_COPY_TERMS):
        raise ValueError(f"{name} contains forbidden recovery copy language")
