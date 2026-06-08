from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

AI_NUTRITION_EXPLANATION_CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

APPROVED_NUTRITION_EXPLANATION_SOURCES = {
    "deterministic_fallback",
    "ai_validated",
}

NUTRITION_EXPLANATION_FORBIDDEN_LANGUAGE = {
    "your true maintenance is exactly",
    "true maintenance is exactly",
    "your targets have been changed",
    "your targets were changed",
    "your targets have changed",
    "targets have been changed",
    "calibration has been applied",
    "calibration was applied",
    "targets have been calibrated",
    "calibrated targets are active",
    "you failed",
    "you must cut calories",
    "must cut calories",
    "burn this off",
    "compensate tomorrow",
    "skip meals",
    "your metabolism is damaged",
    "metabolism is damaged",
    "medical treatment",
    "disease treatment",
    "medical diagnosis",
    "fat-loss guarantee",
    "fat loss guarantee",
    "guaranteed fat loss",
    "exact physiological certainty",
    "ai-generated target",
    "ai generated target",
    "ai-generated macros",
    "ai generated macros",
    "invented foods",
    "invented servings",
    "invented macros",
    "invented target changes",
    "here is a meal plan",
    "meal plan:",
    "eating-disorder",
    "eating disorder",
}

RAW_OR_INTERNAL_CONTEXT_KEYS = {
    "raw_food_entries",
    "raw_food_entry_rows",
    "raw_daily_checkins",
    "raw_daily_checkin_rows",
    "raw_source_payload",
    "source_payload_json",
    "raw_sql",
    "sql_debug",
    "debug_payload",
    "provider_metadata",
    "crewai_metadata",
    "ollama_metadata",
    "raw_output",
    "raw_provider_output",
    "unapproved_target_values",
}


@dataclass
class NutritionExplanationContext:
    user_id: int
    explanation_date: str
    approved_macro_targets: dict[str, Any] = field(default_factory=dict)
    target_vs_actual_summary: dict[str, Any] = field(default_factory=dict)
    approved_nutrition_guidance: dict[str, Any] = field(default_factory=dict)
    approved_food_suggestions: dict[str, Any] = field(default_factory=dict)
    trend_summary: dict[str, Any] = field(default_factory=dict)
    calibration_summary: dict[str, Any] = field(default_factory=dict)
    confidence: str = "Limited"
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    display_flags: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_required_text("explanation_date", self.explanation_date)
        _validate_confidence(self.confidence)
        _validate_mapping("approved_macro_targets", self.approved_macro_targets)
        _validate_mapping("target_vs_actual_summary", self.target_vs_actual_summary)
        _validate_mapping(
            "approved_nutrition_guidance", self.approved_nutrition_guidance
        )
        _validate_mapping("approved_food_suggestions", self.approved_food_suggestions)
        _validate_mapping("trend_summary", self.trend_summary)
        _validate_mapping("calibration_summary", self.calibration_summary)
        _validate_display_flags(self.display_flags)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        _validate_approved_context_payloads(
            {
                "approved_macro_targets": self.approved_macro_targets,
                "target_vs_actual_summary": self.target_vs_actual_summary,
                "approved_nutrition_guidance": self.approved_nutrition_guidance,
                "approved_food_suggestions": self.approved_food_suggestions,
                "trend_summary": self.trend_summary,
                "calibration_summary": self.calibration_summary,
            }
        )

        if self.confidence in {"Limited", "Low"} and not (
            self.reason_codes or self.limitations
        ):
            raise ValueError(
                "Limited/Low nutrition explanation context requires reason_codes or limitations"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateNutritionExplanation:
    explanation_summary: str
    macro_context: str | None = None
    food_suggestion_context: str | None = None
    trend_context: str | None = None
    calibration_context: str | None = None
    limitations_context: str | None = None
    confidence: str = "Limited"
    reason_codes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_required_text("explanation_summary", self.explanation_summary)
        _validate_optional_text("macro_context", self.macro_context)
        _validate_optional_text("food_suggestion_context", self.food_suggestion_context)
        _validate_optional_text("trend_context", self.trend_context)
        _validate_optional_text("calibration_context", self.calibration_context)
        _validate_optional_text("limitations_context", self.limitations_context)
        _validate_confidence(self.confidence)
        _validate_safe_text_list("reason_codes", self.reason_codes)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ApprovedNutritionExplanation:
    user_id: int
    explanation_date: str
    explanation_summary: str
    macro_context: str | None = None
    food_suggestion_context: str | None = None
    trend_context: str | None = None
    calibration_context: str | None = None
    limitations_context: str | None = None
    confidence: str = "Limited"
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    source: str = "deterministic_fallback"

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_required_text("explanation_date", self.explanation_date)
        _validate_required_text("explanation_summary", self.explanation_summary)
        _validate_optional_text("macro_context", self.macro_context)
        _validate_optional_text("food_suggestion_context", self.food_suggestion_context)
        _validate_optional_text("trend_context", self.trend_context)
        _validate_optional_text("calibration_context", self.calibration_context)
        _validate_optional_text("limitations_context", self.limitations_context)
        _validate_confidence(self.confidence)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        _validate_source(self.source)
        _validate_no_forbidden_language(self.explanation_summary)
        for field_name in (
            "macro_context",
            "food_suggestion_context",
            "trend_context",
            "calibration_context",
            "limitations_context",
        ):
            _validate_no_forbidden_language(getattr(self, field_name))

        if self.confidence in {"Limited", "Low"} and not (
            self.reason_codes or self.limitations or self.limitations_context
        ):
            raise ValueError(
                "Limited/Low approved nutrition explanations require limitations or reason_codes"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NutritionExplanationRuntimeMetadata:
    provider: str
    fallback_used: bool
    validation_status: str
    validation_errors: list[str] = field(default_factory=list)
    raw_output_preview_truncated: str | None = None
    raw_output_length: int | None = None
    configured_provider: str | None = None
    selected_provider: str | None = None
    configured_model: str | None = None
    selected_model: str | None = None
    provider_attempted: bool = False
    fallback_reason: str | None = None
    candidate_valid: bool = False
    candidate_parse_status: str = "not_attempted"
    candidate_validation_status: str = "not_attempted"
    final_explanation_source: str = "deterministic"
    markdown_wrapper_detected: bool = False

    def __post_init__(self) -> None:
        _validate_required_text("provider", self.provider)
        _validate_required_text("validation_status", self.validation_status)
        _validate_safe_text_list("validation_errors", self.validation_errors)
        _validate_optional_non_negative_int("raw_output_length", self.raw_output_length)
        _validate_optional_text("configured_provider", self.configured_provider)
        _validate_optional_text("selected_provider", self.selected_provider)
        _validate_optional_text("configured_model", self.configured_model)
        _validate_optional_text("selected_model", self.selected_model)
        _validate_optional_text("fallback_reason", self.fallback_reason)
        _validate_required_text("candidate_parse_status", self.candidate_parse_status)
        _validate_required_text(
            "candidate_validation_status", self.candidate_validation_status
        )
        _validate_required_text(
            "final_explanation_source", self.final_explanation_source
        )
        if self.raw_output_preview_truncated is not None and not isinstance(
            self.raw_output_preview_truncated, str
        ):
            raise ValueError("raw_output_preview_truncated must be text when present")

    def to_debug_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ApprovedNutritionExplanationResult:
    approved_nutrition_explanation: ApprovedNutritionExplanation
    runtime_metadata: NutritionExplanationRuntimeMetadata

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "approved_nutrition_explanation": self.approved_nutrition_explanation.to_dict(),
            "runtime_metadata": self.runtime_metadata.to_debug_dict(),
        }


def _validate_confidence(confidence: str) -> None:
    if confidence not in AI_NUTRITION_EXPLANATION_CONFIDENCE_VALUES:
        raise ValueError(f"Invalid confidence: {confidence}")


def _validate_source(source: str) -> None:
    if source not in APPROVED_NUTRITION_EXPLANATION_SOURCES:
        raise ValueError(f"Invalid source: {source}")


def _validate_required_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_optional_text(field_name: str, value: str | None) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise ValueError(f"{field_name} must be text when present")


def _validate_positive_int(field_name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_optional_non_negative_int(field_name: str, value: int | None) -> None:
    if value is not None and (not isinstance(value, int) or value < 0):
        raise ValueError(f"{field_name} must be non-negative")


def _validate_mapping(field_name: str, value: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dictionary")


def _validate_display_flags(display_flags: dict[str, bool]) -> None:
    if not isinstance(display_flags, dict):
        raise ValueError("display_flags must be a dictionary")
    for flag_name, flag_value in display_flags.items():
        if not isinstance(flag_name, str):
            raise ValueError("display_flags keys must be strings")
        if not isinstance(flag_value, bool):
            raise ValueError(f"display_flags values must be boolean: {flag_name}")


def _validate_safe_text_list(field_name: str, values: list[str]) -> None:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list")
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must contain strings")
        _validate_no_forbidden_language(value)


def _validate_approved_context_payloads(payloads: dict[str, dict[str, Any]]) -> None:
    for field_name, payload in payloads.items():
        _validate_no_internal_keys(field_name, payload)
        _validate_payload_text_is_safe(field_name, payload)


def _validate_no_internal_keys(field_name: str, payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        if isinstance(key, str) and key.lower() in RAW_OR_INTERNAL_CONTEXT_KEYS:
            raise ValueError(f"{field_name} contains raw or internal context: {key}")
        if isinstance(value, dict):
            _validate_no_internal_keys(field_name, value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _validate_no_internal_keys(field_name, item)


def _validate_payload_text_is_safe(field_name: str, value: Any) -> None:
    if isinstance(value, str):
        try:
            _validate_no_forbidden_language(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} contains forbidden language") from exc
    elif isinstance(value, dict):
        for child_value in value.values():
            _validate_payload_text_is_safe(field_name, child_value)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_text_is_safe(field_name, item)


def _validate_no_forbidden_language(value: str | None) -> None:
    if value is None:
        return
    normalized_value = value.lower()
    for phrase in NUTRITION_EXPLANATION_FORBIDDEN_LANGUAGE:
        if phrase in normalized_value:
            raise ValueError(
                "Forbidden AI nutrition explanation language is not allowed"
            )
