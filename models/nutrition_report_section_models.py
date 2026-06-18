from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

NUTRITION_REPORT_SECTION_CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

CLAIM_TARGET_AVAILABLE = "target_available"
CLAIM_ACTUALS_LOGGED = "actuals_logged"
CLAIM_LOGGING_COMPLETE_ENOUGH = "logging_complete_enough"
CLAIM_LOGGING_INCOMPLETE = "logging_incomplete"
CLAIM_PROTEIN_BELOW_TARGET = "protein_below_target"
CLAIM_PROTEIN_NEAR_TARGET = "protein_near_target"
CLAIM_CALORIES_BELOW_TARGET = "calories_below_target"
CLAIM_CALORIES_NEAR_TARGET = "calories_near_target"
CLAIM_CALORIES_ABOVE_TARGET = "calories_above_target"
CLAIM_FOOD_SUGGESTION_AVAILABLE = "food_suggestion_available"
CLAIM_CONFIDENCE_LIMITED_BY_MISSING_LOGS = "confidence_limited_by_missing_logs"

APPROVED_NUTRITION_CLAIM_TYPES = {
    CLAIM_TARGET_AVAILABLE,
    CLAIM_ACTUALS_LOGGED,
    CLAIM_LOGGING_COMPLETE_ENOUGH,
    CLAIM_LOGGING_INCOMPLETE,
    CLAIM_PROTEIN_BELOW_TARGET,
    CLAIM_PROTEIN_NEAR_TARGET,
    CLAIM_CALORIES_BELOW_TARGET,
    CLAIM_CALORIES_NEAR_TARGET,
    CLAIM_CALORIES_ABOVE_TARGET,
    CLAIM_FOOD_SUGGESTION_AVAILABLE,
    CLAIM_CONFIDENCE_LIMITED_BY_MISSING_LOGS,
}

NUTRITION_REPORT_SECTION_SOURCE_DETERMINISTIC = "deterministic_nutrition_report_section"
NUTRITION_REPORT_SECTION_SOURCE_DETERMINISTIC_FALLBACK = (
    "deterministic_nutrition_report_section_fallback"
)

FORBIDDEN_NUTRITION_REPORT_SECTION_TERMS = {
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
    "noncompliant",
    "non-compliant",
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


@dataclass(frozen=True)
class NutritionReportEvidenceContext:
    user_id: int
    report_date: str
    target_vs_actual_summary: dict[str, Any]
    approved_nutrition_guidance: dict[str, Any]
    approved_food_suggestions: dict[str, Any] | None = None
    confidence: str = "Limited"
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_required_text("report_date", self.report_date)
        _validate_confidence(self.confidence)
        _validate_dict("target_vs_actual_summary", self.target_vs_actual_summary)
        _validate_dict("approved_nutrition_guidance", self.approved_nutrition_guidance)
        if self.approved_food_suggestions is not None:
            _validate_dict("approved_food_suggestions", self.approved_food_suggestions)
        _validate_text_list("reason_codes", self.reason_codes)
        _validate_text_list("limitations", self.limitations)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedNutritionClaim:
    claim_type: str
    claim_text: str
    evidence_fields: list[str]
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.claim_type not in APPROVED_NUTRITION_CLAIM_TYPES:
            raise ValueError(f"Invalid nutrition claim_type: {self.claim_type}")
        _validate_required_text("claim_text", self.claim_text)
        _validate_confidence(self.confidence)
        _validate_text_list("evidence_fields", self.evidence_fields)
        _validate_text_list("reason_codes", self.reason_codes)
        _validate_text_list("limitations", self.limitations)
        _validate_safe_public_text(self.claim_text)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CandidateNutritionReportSection:
    section_summary: str
    intake_snapshot: str
    target_alignment: str
    logging_quality: str
    practical_food_focus: str
    next_nutrition_action: str
    limitations_context: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> CandidateNutritionReportSection:
        return cls(
            section_summary=payload["section_summary"],
            intake_snapshot=payload["intake_snapshot"],
            target_alignment=payload["target_alignment"],
            logging_quality=payload["logging_quality"],
            practical_food_focus=payload["practical_food_focus"],
            next_nutrition_action=payload["next_nutrition_action"],
            limitations_context=payload["limitations_context"],
            confidence=payload["confidence"],
            reason_codes=list(payload.get("reason_codes", [])),
        )

    def __post_init__(self) -> None:
        _validate_section_text_fields(self)
        _validate_confidence(self.confidence)
        _validate_text_list("reason_codes", self.reason_codes)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedNutritionReportSection:
    section_id: str
    section_summary: str
    intake_snapshot: str
    target_alignment: str
    logging_quality: str
    practical_food_focus: str
    next_nutrition_action: str
    limitations_context: str
    confidence: str
    approved_claims: list[ApprovedNutritionClaim]
    reason_codes: list[str]
    source: str

    @classmethod
    def from_candidate(
        cls,
        candidate: CandidateNutritionReportSection,
        *,
        approved_claims: list[ApprovedNutritionClaim],
        source: str,
    ) -> ApprovedNutritionReportSection:
        return cls(
            section_id="nutrition_report_section",
            section_summary=candidate.section_summary,
            intake_snapshot=candidate.intake_snapshot,
            target_alignment=candidate.target_alignment,
            logging_quality=candidate.logging_quality,
            practical_food_focus=candidate.practical_food_focus,
            next_nutrition_action=candidate.next_nutrition_action,
            limitations_context=candidate.limitations_context,
            confidence=candidate.confidence,
            approved_claims=list(approved_claims),
            reason_codes=list(candidate.reason_codes),
            source=source,
        )

    def __post_init__(self) -> None:
        _validate_required_text("section_id", self.section_id)
        if self.section_id != "nutrition_report_section":
            raise ValueError(
                "Nutrition report section_id must be nutrition_report_section"
            )
        _validate_section_text_fields(self)
        _validate_confidence(self.confidence)
        _validate_text_list("reason_codes", self.reason_codes)
        _validate_required_text("source", self.source)
        if not isinstance(self.approved_claims, list) or not all(
            isinstance(claim, ApprovedNutritionClaim) for claim in self.approved_claims
        ):
            raise ValueError(
                "approved_claims must contain ApprovedNutritionClaim items"
            )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approved_claims"] = [claim.to_dict() for claim in self.approved_claims]
        return payload


@dataclass(frozen=True)
class NutritionReportSectionValidationResult:
    valid: bool
    validation_errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_text_list("validation_errors", self.validation_errors)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_positive_int(field_name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")


def _validate_required_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _validate_safe_public_text(value)


def _validate_dict(field_name: str, value: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dictionary")


def _validate_confidence(confidence: str) -> None:
    if confidence not in NUTRITION_REPORT_SECTION_CONFIDENCE_VALUES:
        raise ValueError(f"Invalid nutrition report confidence: {confidence}")


def _validate_text_list(field_name: str, values: list[str]) -> None:
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value.strip() for value in values
    ):
        raise ValueError(f"{field_name} must contain non-empty strings")
    for value in values:
        _validate_safe_public_text(value)


def _validate_section_text_fields(section: Any) -> None:
    for field_name in [
        "section_summary",
        "intake_snapshot",
        "target_alignment",
        "logging_quality",
        "practical_food_focus",
        "next_nutrition_action",
        "limitations_context",
    ]:
        _validate_required_text(field_name, getattr(section, field_name))


def _validate_safe_public_text(value: str) -> None:
    lowered = value.lower()
    for term in FORBIDDEN_NUTRITION_REPORT_SECTION_TERMS:
        if term in lowered:
            raise ValueError(
                f"Nutrition report section contains forbidden term: {term}"
            )
