from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from models.nutrition_report_section_models import CandidateNutritionReportSection

NUTRITION_PROVIDER_CONTEXT_SCHEMA_VERSION = "nutrition_provider_context_v1"
NUTRITION_PROVIDER_CONTRACT_VERSION = "nutrition_provider_contract_v1"
NUTRITION_PROVIDER_SECTION_ID = "nutrition_report_section"

NUTRITION_PROVIDER_PARSE_STATUS_SUCCESS = "success"
NUTRITION_PROVIDER_PARSE_STATUS_EMPTY = "empty_output"
NUTRITION_PROVIDER_PARSE_STATUS_INVALID_JSON = "invalid_json"
NUTRITION_PROVIDER_PARSE_STATUS_NOT_OBJECT = "not_object"
NUTRITION_PROVIDER_PARSE_STATUS_WRAPPER_OBJECT = "wrapper_object_detected"
NUTRITION_PROVIDER_PARSE_STATUS_SCHEMA_INVALID = "schema_invalid"

NUTRITION_PROVIDER_VALIDATION_STATUS_APPROVED = "approved"
NUTRITION_PROVIDER_VALIDATION_STATUS_REJECTED = "rejected"

NUTRITION_PROVIDER_FALLBACK_REASON_PARSE_FAILED = "nutrition_provider_parse_failed"
NUTRITION_PROVIDER_FALLBACK_REASON_VALIDATION_FAILED = (
    "nutrition_provider_validation_failed"
)
NUTRITION_PROVIDER_FALLBACK_REASON_QA_FORCED_INVALID_PROVIDER_OUTPUT = (
    "qa_forced_invalid_provider_output"
)
NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_DISABLED = "nutrition_provider_disabled"
NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_EXCEPTION = "nutrition_provider_exception"
NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_TIMEOUT = "nutrition_provider_timeout"
NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT = (
    "nutrition_provider_non_string_output"
)
NUTRITION_PROVIDER_FALLBACK_REASON_INVALID_PROVIDER = (
    "nutrition_provider_invalid_provider"
)
NUTRITION_PROVIDER_FALLBACK_SOURCE = "nutrition_provider_contract_fallback"

NUTRITION_PROVIDER_CANDIDATE_REQUIRED_KEYS = {
    "section_summary",
    "intake_snapshot",
    "target_alignment",
    "logging_quality",
    "practical_food_focus",
    "next_nutrition_action",
    "limitations_context",
    "confidence",
    "reason_codes",
}

NUTRITION_PROVIDER_CANDIDATE_TEXT_FIELDS = {
    "section_summary",
    "intake_snapshot",
    "target_alignment",
    "logging_quality",
    "practical_food_focus",
    "next_nutrition_action",
    "limitations_context",
}

NUTRITION_PROVIDER_CANDIDATE_DISALLOWED_KEYS = {
    "approved_claims",
    "metadata",
    "raw_output",
    "debug",
    "prompt",
    "schema",
    "provider",
    "model",
    "user_id",
    "report_date",
    "nutrition_targets",
    "meal_plan",
    "supplements",
    "diagnosis",
}

NUTRITION_PROVIDER_WRAPPER_KEYS = {
    "candidate",
    "candidate_section",
    "nutrition_report_section",
    "result",
    "section",
    "response",
}

NUTRITION_PROVIDER_CONFIDENCE_ORDER = {
    "Limited": 0,
    "Low": 1,
    "Moderate": 2,
    "High": 3,
}

NUTRITION_PROVIDER_FORBIDDEN_CLAIMS = [
    "deficiency",
    "medical_claim",
    "supplement_recommendation",
    "severe_deficit",
    "diet_diagnosis",
    "meal_plan",
    "guaranteed_weight_loss",
    "fatigue_causation",
    "adherence_or_compliance_judgment",
    "target_change_or_calibration_claim",
]

NUTRITION_PROVIDER_UNSUPPORTED_LANGUAGE = {
    "severe deficit",
    "critical deficit",
    "deficient",
    "deficiency",
    "metabolism is damaged",
    "metabolic damage",
    "keto",
    "intermittent fasting",
    "supplement",
    "supplements",
    "explains fatigue",
    "cause fatigue",
    "caused fatigue",
    "will cause weight loss",
    "guarantees weight loss",
    "guaranteed weight loss",
    "noncompliant",
    "non-compliant",
    "compliant",
    "diet is bad",
    "bad diet",
    "you must eat",
    "you failed",
    "skip meals",
    "compensate tomorrow",
    "burn this off",
    "medical advice",
    "diagnose",
    "disease",
}

NUTRITION_PROVIDER_PLACEHOLDER_LANGUAGE = {
    "placeholder",
    "todo",
    "tbd",
    "lorem ipsum",
    "insert",
    "n/a",
    "none",
    "null",
}

NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_NUMERIC_VALUE = (
    "unsupported_numeric_value"
)
NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_FOOD_SUGGESTION = (
    "unsupported_food_suggestion"
)
NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_FOOD_SUGGESTION_AVAILABILITY = (
    "unsupported_food_suggestion_availability_claim"
)
NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_SERVING_SIZE = (
    "unsupported_serving_size"
)
NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_MEAL_PLAN = "unsupported_meal_plan"
NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_MEDICAL_CLAIM = (
    "unsupported_medical_claim"
)
NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_SUPPLEMENT_CLAIM = (
    "unsupported_supplement_claim"
)
NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_GUARANTEE_CLAIM = (
    "unsupported_guarantee_claim"
)
NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_SHAME_LANGUAGE = (
    "unsupported_compliance_or_shame_language"
)
NUTRITION_PROVIDER_VALIDATION_CATEGORY_FIELD_CLAIM_NOT_APPROVED = (
    "field_claim_not_approved"
)
NUTRITION_PROVIDER_VALIDATION_CATEGORY_CONFIDENCE_CEILING = (
    "confidence_ceiling_violation"
)
NUTRITION_PROVIDER_VALIDATION_CATEGORY_MISSING_REQUIRED_FIELD = "missing_required_field"
NUTRITION_PROVIDER_VALIDATION_CATEGORY_EXTRA_KEY = "extra_key_detected"
NUTRITION_PROVIDER_VALIDATION_CATEGORY_INVALID_ENUM = "invalid_enum_value"
NUTRITION_PROVIDER_VALIDATION_CATEGORY_EMPTY_OR_PLACEHOLDER = (
    "empty_or_placeholder_text"
)
NUTRITION_PROVIDER_VALIDATION_CATEGORY_WRAPPER_OBJECT = "wrapper_object_detected"
NUTRITION_PROVIDER_VALIDATION_CATEGORY_INVALID_JSON = "invalid_json"
NUTRITION_PROVIDER_VALIDATION_CATEGORY_TYPE_MISMATCH = "type_mismatch"
NUTRITION_PROVIDER_VALIDATION_CATEGORY_VALIDATION_FAILURE = "validation_failure"

NUTRITION_PROVIDER_SAFE_METADATA_ALLOWLIST = {
    "nutrition_provider_contract_version",
    "nutrition_provider_context_schema_version",
    "nutrition_provider_execution_enabled",
    "provider_enabled",
    "provider_attempted",
    "selected_provider",
    "selected_model",
    "parse_status",
    "candidate_valid",
    "validation_status",
    "validation_errors_count",
    "fallback_used",
    "fallback_reason",
    "fallback_source",
    "confidence_ceiling",
    "approved_claim_types",
    "approved_food_suggestion_count",
    "nutrition_section_source",
    "provider_latency_ms",
}


@dataclass(frozen=True)
class NutritionProviderSafeContext:
    schema_version: str
    section_id: str
    user_id: int
    report_date: str
    confidence_ceiling: str
    logging: dict[str, Any]
    approved_actuals: dict[str, Any]
    approved_comparisons: dict[str, Any]
    approved_guidance: dict[str, Any]
    approved_claims: list[dict[str, Any]]
    approved_food_suggestions: list[dict[str, Any]] = field(default_factory=list)
    approved_practical_food_focus_options: list[str] = field(default_factory=list)
    approved_practical_food_focus_unavailable_options: list[str] = field(
        default_factory=list
    )
    approved_numeric_values: list[float] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(
        default_factory=lambda: list(NUTRITION_PROVIDER_FORBIDDEN_CLAIMS)
    )

    def __post_init__(self) -> None:
        if self.schema_version != NUTRITION_PROVIDER_CONTEXT_SCHEMA_VERSION:
            raise ValueError("Invalid nutrition provider context schema_version")
        if self.section_id != NUTRITION_PROVIDER_SECTION_ID:
            raise ValueError("Nutrition provider context section_id is invalid")
        _validate_positive_int("user_id", self.user_id)
        _validate_required_text("report_date", self.report_date)
        _validate_confidence("confidence_ceiling", self.confidence_ceiling)
        _validate_dict("logging", self.logging)
        _validate_dict("approved_actuals", self.approved_actuals)
        _validate_dict("approved_comparisons", self.approved_comparisons)
        _validate_dict("approved_guidance", self.approved_guidance)
        _validate_list_of_dicts("approved_claims", self.approved_claims)
        _validate_list_of_dicts(
            "approved_food_suggestions", self.approved_food_suggestions
        )
        _validate_text_list(
            "approved_practical_food_focus_options",
            self.approved_practical_food_focus_options,
        )
        _validate_text_list(
            "approved_practical_food_focus_unavailable_options",
            self.approved_practical_food_focus_unavailable_options,
        )
        _validate_number_list("approved_numeric_values", self.approved_numeric_values)
        _validate_text_list("limitations", self.limitations)
        _validate_text_list("reason_codes", self.reason_codes)
        _validate_text_list("forbidden_claims", self.forbidden_claims)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NutritionProviderCandidateParseResult:
    parse_status: str
    candidate: CandidateNutritionReportSection | None = None
    parse_errors: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return self.parse_status == NUTRITION_PROVIDER_PARSE_STATUS_SUCCESS

    def __post_init__(self) -> None:
        _validate_required_text("parse_status", self.parse_status)
        _validate_text_list("parse_errors", self.parse_errors)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "parse_status": self.parse_status,
            "parse_errors": list(self.parse_errors),
            "candidate": self.candidate.to_dict() if self.candidate else None,
        }


@dataclass(frozen=True)
class NutritionProviderCandidateValidationResult:
    valid: bool
    validation_status: str
    validation_errors: list[str] = field(default_factory=list)
    validation_error_categories: list[str] = field(default_factory=list)
    validation_error_fields: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        expected_status = (
            NUTRITION_PROVIDER_VALIDATION_STATUS_APPROVED
            if self.valid
            else NUTRITION_PROVIDER_VALIDATION_STATUS_REJECTED
        )
        if self.validation_status != expected_status:
            raise ValueError("validation_status does not match valid flag")
        _validate_text_list("validation_errors", self.validation_errors)
        _validate_text_list(
            "validation_error_categories", self.validation_error_categories
        )
        _validate_text_list("validation_error_fields", self.validation_error_fields)

    @property
    def validation_error_count(self) -> int:
        return len(self.validation_errors)

    @property
    def first_validation_error_category(self) -> str | None:
        return (
            self.validation_error_categories[0]
            if self.validation_error_categories
            else None
        )

    @property
    def first_validation_error_field(self) -> str | None:
        return self.validation_error_fields[0] if self.validation_error_fields else None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NutritionProviderFallbackResult:
    fallback_used: bool
    fallback_reason: str
    fallback_source: str
    section: Any
    safe_metadata: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.fallback_used:
            raise ValueError(
                "Nutrition provider fallback result must mark fallback_used"
            )
        _validate_required_text("fallback_reason", self.fallback_reason)
        _validate_required_text("fallback_source", self.fallback_source)
        _validate_safe_metadata(self.safe_metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "fallback_source": self.fallback_source,
            "section": (
                self.section.to_dict()
                if hasattr(self.section, "to_dict")
                else self.section
            ),
            "safe_metadata": dict(self.safe_metadata),
        }


def _validate_positive_int(field_name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")


def _validate_required_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _validate_confidence(field_name: str, value: str) -> None:
    if value not in NUTRITION_PROVIDER_CONFIDENCE_ORDER:
        raise ValueError(f"{field_name} must be a valid confidence value")


def _validate_dict(field_name: str, value: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dictionary")


def _validate_list_of_dicts(field_name: str, values: list[dict[str, Any]]) -> None:
    if not isinstance(values, list) or not all(
        isinstance(value, dict) for value in values
    ):
        raise ValueError(f"{field_name} must be a list of dictionaries")


def _validate_number_list(field_name: str, values: list[float]) -> None:
    if not isinstance(values, list) or not all(
        isinstance(value, int | float) for value in values
    ):
        raise ValueError(f"{field_name} must contain numeric values")


def _validate_text_list(field_name: str, values: list[str]) -> None:
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value.strip() for value in values
    ):
        raise ValueError(f"{field_name} must contain non-empty strings")


def _validate_safe_metadata(metadata: dict[str, Any]) -> None:
    _validate_dict("safe_metadata", metadata)
    extra_keys = set(metadata) - NUTRITION_PROVIDER_SAFE_METADATA_ALLOWLIST
    if extra_keys:
        raise ValueError(
            "Nutrition provider safe metadata contains non-allowlisted keys: "
            + ", ".join(sorted(extra_keys))
        )
