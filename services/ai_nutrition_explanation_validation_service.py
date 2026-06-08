from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from models.ai_nutrition_explanation_models import (
    NUTRITION_EXPLANATION_FORBIDDEN_LANGUAGE,
    ApprovedNutritionExplanation,
    CandidateNutritionExplanation,
    NutritionExplanationContext,
    NutritionExplanationRuntimeMetadata,
)

_VALIDATED_REASON_CODE = "ai_nutrition_explanation_validated"
_DETERMINISTIC_FALLBACK_REASON_CODE = "deterministic_nutrition_explanation_fallback"

_NUTRITION_NUMBER_RE = re.compile(
    r"(?<![\w.])(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>kcal|calories|calorie|grams|gram|g|protein|carbs|carbohydrates|carbohydrate|fat)\b",
    re.IGNORECASE,
)

_APPROVED_CONTEXT_INTERNAL_TERMS = {
    "raw food entries",
    "raw food entry",
    "raw check-ins",
    "raw checkins",
    "raw sql",
    "sql debug",
    "debug payload",
    "provider metadata",
    "crewai",
    "ollama",
    "raw provider output",
}

_TARGET_CHANGE_PATTERNS = {
    "your targets have been changed",
    "your targets were changed",
    "your targets have changed",
    "your targets were updated",
    "targets have been changed",
    "targets were updated",
    "calibrated targets are active",
    "targets have been calibrated",
    "calibration has been applied",
    "calibration was applied",
    "new target",
    "updated target",
    "changed target",
    "adjusted target",
    "calibrated target",
}

_MEAL_PLAN_PATTERNS = {
    "meal plan",
    "breakfast:",
    "lunch:",
    "dinner:",
    "snack:",
    "eat this meal",
    "for breakfast eat",
    "for lunch eat",
    "for dinner eat",
}

_SHAME_RESTRICTION_PATTERNS = {
    "you failed",
    "you must cut calories",
    "must cut calories",
    "burn this off",
    "compensate tomorrow",
    "skip meals",
    "skip a meal",
    "make up for it",
    "you should compensate",
}

_MEDICAL_SUPPLEMENT_PATTERNS = {
    "medical diagnosis",
    "medical treatment",
    "disease treatment",
    "treat disease",
    "cure disease",
    "fat-loss guarantee",
    "fat loss guarantee",
    "guaranteed fat loss",
    "supplement will",
    "supplement guarantees",
    "take supplements to",
    "metabolism is damaged",
    "your metabolism is damaged",
}

_EXACT_CERTAINTY_PATTERNS = {
    "your true maintenance is exactly",
    "true maintenance is exactly",
    "maintenance is exactly",
    "exact physiological certainty",
    "exactly your maintenance",
}

_COMMON_CANONICAL_FOOD_TERMS = {
    "chicken",
    "chicken breast",
    "greek yogurt",
    "yogurt",
    "tuna",
    "egg whites",
    "egg",
    "eggs",
    "cottage cheese",
    "whey",
    "whey protein",
    "protein powder",
    "turkey",
    "shrimp",
    "cod",
    "pork",
    "rice",
    "white rice",
    "jasmine rice",
    "basmati rice",
    "brown rice",
    "oats",
    "oatmeal",
    "potato",
    "sweet potato",
    "pasta",
    "banana",
    "apple",
    "beans",
    "lentils",
    "tortilla",
    "bread",
    "bagel",
    "peanut butter",
    "almonds",
    "walnuts",
    "cashews",
    "avocado",
    "olive oil",
    "avocado oil",
    "butter",
    "cheese",
    "salmon",
    "beef",
    "steak",
}

_FIELD_LABELS = {
    "explanation_summary": "explanation_summary",
    "macro_context": "macro_context",
    "food_suggestion_context": "food_suggestion_context",
    "trend_context": "trend_context",
    "calibration_context": "calibration_context",
    "limitations_context": "limitations_context",
}


@dataclass(frozen=True)
class NutritionExplanationValidationResult:
    valid: bool
    validation_errors: list[str] = field(default_factory=list)

    def to_debug_metadata(
        self,
        *,
        provider: str = "validator",
        fallback_used: bool = False,
        raw_output_preview_truncated: str | None = None,
        raw_output_length: int | None = None,
    ) -> NutritionExplanationRuntimeMetadata:
        return NutritionExplanationRuntimeMetadata(
            provider=provider,
            fallback_used=fallback_used,
            validation_status="approved" if self.valid else "rejected",
            validation_errors=list(self.validation_errors),
            raw_output_preview_truncated=raw_output_preview_truncated,
            raw_output_length=raw_output_length,
        )


def collect_nutrition_explanation_validation_errors(
    context: NutritionExplanationContext,
    candidate: CandidateNutritionExplanation,
) -> list[str]:
    """Return debug-only validation errors for an AI nutrition explanation candidate."""

    errors: list[str] = []
    candidate_texts = _candidate_texts(candidate)
    combined_text = "\n".join(value for value in candidate_texts.values() if value)
    normalized_combined_text = _normalize(combined_text)

    _add_errors_for_required_context_boundaries(context, errors)
    _add_errors_for_forbidden_language(normalized_combined_text, errors)
    _add_errors_for_target_change_language(normalized_combined_text, errors)
    _add_errors_for_exact_maintenance_language(normalized_combined_text, errors)
    _add_errors_for_meal_plan_language(normalized_combined_text, errors)
    _add_errors_for_shame_restriction_language(normalized_combined_text, errors)
    _add_errors_for_medical_supplement_language(normalized_combined_text, errors)
    _add_errors_for_raw_or_internal_language(normalized_combined_text, errors)
    _add_errors_for_unapproved_food_mentions(context, normalized_combined_text, errors)
    _add_errors_for_unapproved_nutrition_numbers(context, combined_text, errors)

    return _unique(errors)


def validate_candidate_nutrition_explanation(
    context: NutritionExplanationContext,
    candidate: CandidateNutritionExplanation,
) -> CandidateNutritionExplanation:
    errors = collect_nutrition_explanation_validation_errors(context, candidate)
    if errors:
        raise ValueError(
            "AI nutrition explanation candidate failed validation: " + "; ".join(errors)
        )
    return candidate


def approve_nutrition_explanation_candidate(
    context: NutritionExplanationContext,
    candidate: CandidateNutritionExplanation,
) -> ApprovedNutritionExplanation:
    validate_candidate_nutrition_explanation(context, candidate)

    reason_codes = _unique(
        [
            *context.reason_codes,
            *candidate.reason_codes,
            _VALIDATED_REASON_CODE,
        ]
    )
    limitations = list(context.limitations)

    return ApprovedNutritionExplanation(
        user_id=context.user_id,
        explanation_date=context.explanation_date,
        explanation_summary=candidate.explanation_summary,
        macro_context=candidate.macro_context,
        food_suggestion_context=candidate.food_suggestion_context,
        trend_context=candidate.trend_context,
        calibration_context=candidate.calibration_context,
        limitations_context=candidate.limitations_context,
        confidence=_minimum_confidence(context.confidence, candidate.confidence),
        reason_codes=reason_codes,
        limitations=limitations,
        source="ai_validated",
    )


def build_deterministic_fallback_nutrition_explanation(
    context: NutritionExplanationContext,
) -> ApprovedNutritionExplanation:
    limitations_context = _fallback_limitations_context(context)
    summary = _fallback_summary(context)

    return ApprovedNutritionExplanation(
        user_id=context.user_id,
        explanation_date=context.explanation_date,
        explanation_summary=summary,
        macro_context=_fallback_macro_context(context),
        food_suggestion_context=_fallback_food_suggestion_context(context),
        trend_context=_fallback_trend_context(context),
        calibration_context=_fallback_calibration_context(context),
        limitations_context=limitations_context,
        confidence=context.confidence,
        reason_codes=_unique(
            [*context.reason_codes, _DETERMINISTIC_FALLBACK_REASON_CODE]
        ),
        limitations=list(context.limitations),
        source="deterministic_fallback",
    )


def validate_approved_nutrition_explanation(
    explanation: ApprovedNutritionExplanation,
) -> ApprovedNutritionExplanation:
    # ApprovedNutritionExplanation performs model-level public safety validation at
    # construction time. This function is a named validator boundary for downstream
    # callers that want a service-level approval step.
    return explanation


def _candidate_texts(candidate: CandidateNutritionExplanation) -> dict[str, str]:
    return {
        field_name: value or ""
        for field_name, value in {
            "explanation_summary": candidate.explanation_summary,
            "macro_context": candidate.macro_context,
            "food_suggestion_context": candidate.food_suggestion_context,
            "trend_context": candidate.trend_context,
            "calibration_context": candidate.calibration_context,
            "limitations_context": candidate.limitations_context,
        }.items()
    }


def _add_errors_for_required_context_boundaries(
    context: NutritionExplanationContext,
    errors: list[str],
) -> None:
    if not any(
        [
            context.approved_macro_targets,
            context.target_vs_actual_summary,
            context.approved_nutrition_guidance,
            context.approved_food_suggestions,
            context.trend_summary,
            context.calibration_summary,
        ]
    ):
        errors.append("approved_context_required")


def _add_errors_for_forbidden_language(text: str, errors: list[str]) -> None:
    for phrase in NUTRITION_EXPLANATION_FORBIDDEN_LANGUAGE:
        if phrase in text:
            errors.append("forbidden_language_detected")
            return


def _add_errors_for_target_change_language(text: str, errors: list[str]) -> None:
    if any(phrase in text for phrase in _TARGET_CHANGE_PATTERNS):
        errors.append("target_change_language_detected")

    if re.search(r"\b(target|targets)\s+(?:is|are|should be|will be)\s+\d", text):
        errors.append("invented_macro_target_detected")


def _add_errors_for_exact_maintenance_language(text: str, errors: list[str]) -> None:
    if any(phrase in text for phrase in _EXACT_CERTAINTY_PATTERNS):
        errors.append("exact_maintenance_claim_detected")

    if re.search(r"\bmaintenance\s+(?:calories\s+)?(?:is|are)\s+\d", text):
        errors.append("exact_maintenance_claim_detected")


def _add_errors_for_meal_plan_language(text: str, errors: list[str]) -> None:
    if any(phrase in text for phrase in _MEAL_PLAN_PATTERNS):
        errors.append("meal_plan_language_detected")


def _add_errors_for_shame_restriction_language(text: str, errors: list[str]) -> None:
    if any(phrase in text for phrase in _SHAME_RESTRICTION_PATTERNS):
        errors.append("shame_or_restriction_language_detected")


def _add_errors_for_medical_supplement_language(text: str, errors: list[str]) -> None:
    if any(phrase in text for phrase in _MEDICAL_SUPPLEMENT_PATTERNS):
        errors.append("medical_supplement_or_fat_loss_claim_detected")


def _add_errors_for_raw_or_internal_language(text: str, errors: list[str]) -> None:
    if any(phrase in text for phrase in _APPROVED_CONTEXT_INTERNAL_TERMS):
        errors.append("raw_or_internal_details_detected")


def _add_errors_for_unapproved_food_mentions(
    context: NutritionExplanationContext,
    text: str,
    errors: list[str],
) -> None:
    approved_terms = _approved_food_terms(context)
    for food_term in sorted(_COMMON_CANONICAL_FOOD_TERMS, key=len, reverse=True):
        if not re.search(rf"\b{re.escape(food_term)}\b", text):
            continue
        if food_term not in approved_terms:
            errors.append("unapproved_food_mention_detected")
            return


def _add_errors_for_unapproved_nutrition_numbers(
    context: NutritionExplanationContext,
    candidate_text: str,
    errors: list[str],
) -> None:
    approved_numbers = _approved_context_numbers(context)
    for match in _NUTRITION_NUMBER_RE.finditer(candidate_text):
        number = float(match.group("number"))
        if not _number_is_approved(number, approved_numbers):
            errors.append("unapproved_nutrition_number_detected")
            return


def _approved_food_terms(context: NutritionExplanationContext) -> set[str]:
    terms: set[str] = set()
    for value in _walk_values(context.approved_food_suggestions):
        if isinstance(value, str):
            lowered = _normalize(value)
            for food_term in _COMMON_CANONICAL_FOOD_TERMS:
                if re.search(rf"\b{re.escape(food_term)}\b", lowered):
                    terms.add(food_term)
    return terms


def _approved_context_numbers(context: NutritionExplanationContext) -> list[float]:
    numbers: list[float] = []
    for payload in (
        context.approved_macro_targets,
        context.target_vs_actual_summary,
        context.approved_nutrition_guidance,
        context.approved_food_suggestions,
        context.trend_summary,
        context.calibration_summary,
        context.value_aware_summary,
    ):
        numbers.extend(_numbers_from_payload(payload))
    return numbers


def _numbers_from_payload(value: Any) -> list[float]:
    numbers: list[float] = []
    if isinstance(value, bool):
        return numbers
    if isinstance(value, int | float):
        numbers.append(float(value))
    elif isinstance(value, str):
        for match in re.finditer(r"(?<![\w.])\d+(?:\.\d+)?", value):
            numbers.append(float(match.group(0)))
    elif isinstance(value, dict):
        for child in value.values():
            numbers.extend(_numbers_from_payload(child))
    elif isinstance(value, list):
        for child in value:
            numbers.extend(_numbers_from_payload(child))
    return numbers


def _walk_values(value: Any) -> list[Any]:
    values: list[Any] = []
    if isinstance(value, dict):
        for child in value.values():
            values.extend(_walk_values(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(_walk_values(child))
    else:
        values.append(value)
    return values


def _number_is_approved(number: float, approved_numbers: list[float]) -> bool:
    return any(
        abs(number - approved_number) <= 0.6 for approved_number in approved_numbers
    )


def _minimum_confidence(first: str, second: str) -> str:
    rank = {"Limited": 0, "Low": 1, "Moderate": 2, "High": 3}
    valid = [value for value in [first, second] if value in rank]
    if not valid:
        return "Limited"
    return min(valid, key=lambda value: rank[value])


def _fallback_summary(context: NutritionExplanationContext) -> str:
    if context.confidence in {"High", "Moderate"}:
        return "Approved nutrition context is available for this date."
    return "Nutrition explanation is limited because the approved context is limited for this date."


def _fallback_macro_context(context: NutritionExplanationContext) -> str | None:
    if context.target_vs_actual_summary:
        return "Target-vs-Actual details are based on approved backend calculations."
    if context.approved_macro_targets:
        return "Targets are still formula-derived."
    return None


def _fallback_food_suggestion_context(
    context: NutritionExplanationContext,
) -> str | None:
    suggestions = context.approved_food_suggestions.get("suggestions")
    if isinstance(suggestions, list) and suggestions:
        return "The Nutrition tab has approved food suggestions based on logged macro gaps."
    return None


def _fallback_trend_context(context: NutritionExplanationContext) -> str | None:
    if context.trend_summary:
        return "Trend evidence is summarized from deterministic logged data."
    return None


def _fallback_calibration_context(context: NutritionExplanationContext) -> str | None:
    if context.calibration_summary:
        return (
            "Targets are still formula-derived; calibration readiness is context only."
        )
    return None


def _fallback_limitations_context(context: NutritionExplanationContext) -> str | None:
    if context.limitations:
        return "Some nutrition explanation details are limited by approved context limitations."
    if context.confidence in {"Limited", "Low"}:
        return "Use the Nutrition tab for approved target, logging, trend, and calibration detail."
    return None


def _normalize(value: str) -> str:
    return value.lower().replace("’", "'").strip()


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
