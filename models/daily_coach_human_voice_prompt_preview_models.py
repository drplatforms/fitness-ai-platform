from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

DAILY_COACH_HUMAN_VOICE_PROMPT_PREVIEW_RESULT_VERSION = (
    "daily_coach_human_voice_prompt_preview_result_v1"
)


@dataclass(frozen=True)
class DailyCoachHumanVoicePromptPreviewResult:
    result_version: str
    user_id: int
    target_date: str
    model_name: str
    provider_name: str
    prompt_file: str
    prompt_sha256: str
    generated_at: str
    elapsed_seconds: float
    latency_ms: int
    developer_preview_only: bool
    provider_call_was_opt_in: bool
    persistence_allowed: bool
    product_surface_allowed: bool
    normal_today_surface_allowed: bool
    payload_version: str
    source_snapshot_version: str
    raw_model_output: str
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        _validate_required_text("result_version", self.result_version)
        _validate_positive_int("user_id", self.user_id)
        _validate_required_text("target_date", self.target_date)
        _validate_required_text("model_name", self.model_name)
        _validate_required_text("provider_name", self.provider_name)
        _validate_required_text("prompt_file", self.prompt_file)
        _validate_required_text("prompt_sha256", self.prompt_sha256)
        _validate_required_text("generated_at", self.generated_at)
        _validate_non_negative_number("elapsed_seconds", self.elapsed_seconds)
        _validate_non_negative_int("latency_ms", self.latency_ms)
        _validate_required_text("payload_version", self.payload_version)
        _validate_required_text("source_snapshot_version", self.source_snapshot_version)
        _validate_hard_boundaries(
            developer_preview_only=self.developer_preview_only,
            provider_call_was_opt_in=self.provider_call_was_opt_in,
            persistence_allowed=self.persistence_allowed,
            product_surface_allowed=self.product_surface_allowed,
            normal_today_surface_allowed=self.normal_today_surface_allowed,
        )
        if not isinstance(self.raw_model_output, str):
            raise ValueError("raw_model_output must be a string")
        if self.error_type is not None and not isinstance(self.error_type, str):
            raise ValueError("error_type must be a string when provided")
        if self.error_message is not None and not isinstance(self.error_message, str):
            raise ValueError("error_message must be a string when provided")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_required_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def _validate_positive_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_non_negative_number(name: str, value: float) -> None:
    if not isinstance(value, int | float) or value < 0:
        raise ValueError(f"{name} must be a non-negative number")


def _validate_non_negative_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_hard_boundaries(
    *,
    developer_preview_only: bool,
    provider_call_was_opt_in: bool,
    persistence_allowed: bool,
    product_surface_allowed: bool,
    normal_today_surface_allowed: bool,
) -> None:
    if developer_preview_only is not True:
        raise ValueError("developer_preview_only must be true")
    if provider_call_was_opt_in is not True:
        raise ValueError("provider_call_was_opt_in must be true")
    if persistence_allowed is not False:
        raise ValueError("persistence_allowed must be false")
    if product_surface_allowed is not False:
        raise ValueError("product_surface_allowed must be false")
    if normal_today_surface_allowed is not False:
        raise ValueError("normal_today_surface_allowed must be false")
