from __future__ import annotations

import re
from typing import Any

from models.nutrition_provider_contract_models import (
    NUTRITION_PROVIDER_CONFIDENCE_ORDER,
    NUTRITION_PROVIDER_CONTEXT_SCHEMA_VERSION,
    NUTRITION_PROVIDER_CONTRACT_VERSION,
    NUTRITION_PROVIDER_FALLBACK_REASON_PARSE_FAILED,
    NUTRITION_PROVIDER_FALLBACK_REASON_VALIDATION_FAILED,
    NUTRITION_PROVIDER_FALLBACK_SOURCE,
    NUTRITION_PROVIDER_SECTION_ID,
    NUTRITION_PROVIDER_UNSUPPORTED_LANGUAGE,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_CONFIDENCE_CEILING,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_EMPTY_OR_PLACEHOLDER,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_EXTRA_KEY,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_FIELD_CLAIM_NOT_APPROVED,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_INVALID_ENUM,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_INVALID_JSON,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_MISSING_REQUIRED_FIELD,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_TYPE_MISMATCH,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_FOOD_SUGGESTION,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_FOOD_SUGGESTION_AVAILABILITY,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_GUARANTEE_CLAIM,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_MEAL_PLAN,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_MEDICAL_CLAIM,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_NUMERIC_VALUE,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_SERVING_SIZE,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_SHAME_LANGUAGE,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_SUPPLEMENT_CLAIM,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_VALIDATION_FAILURE,
    NUTRITION_PROVIDER_VALIDATION_CATEGORY_WRAPPER_OBJECT,
    NUTRITION_PROVIDER_VALIDATION_STATUS_APPROVED,
    NUTRITION_PROVIDER_VALIDATION_STATUS_REJECTED,
    NutritionProviderCandidateParseResult,
    NutritionProviderCandidateValidationResult,
    NutritionProviderFallbackResult,
    NutritionProviderSafeContext,
)
from models.nutrition_report_section_models import (
    CLAIM_CALORIES_ABOVE_TARGET,
    CLAIM_CALORIES_BELOW_TARGET,
    CLAIM_CALORIES_NEAR_TARGET,
    CLAIM_FOOD_SUGGESTION_AVAILABLE,
    CLAIM_PROTEIN_BELOW_TARGET,
    CLAIM_PROTEIN_NEAR_TARGET,
    CandidateNutritionReportSection,
    NutritionReportEvidenceContext,
)
from services.nutrition_report_section_service import (
    build_deterministic_nutrition_report_section,
    derive_approved_nutrition_claims,
)

_PROVIDER_DISABLED = None


def build_nutrition_provider_safe_context(
    evidence_context: NutritionReportEvidenceContext,
) -> NutritionProviderSafeContext:
    """Build a compressed provider-safe nutrition context from approved evidence.

    This function does not call a provider. It only projects backend-approved
    nutrition report evidence, approved claims, and approved canonical food
    suggestions into the contract shape designed for future provider testing.
    """

    summary = evidence_context.target_vs_actual_summary
    logging_summary = summary.get("logging_summary") or {}
    actuals = summary.get("nutrition_actuals") or {}
    comparisons = summary.get("comparisons") or {}
    guidance = evidence_context.approved_nutrition_guidance or {}
    suggestions = evidence_context.approved_food_suggestions or {}
    approved_claims = derive_approved_nutrition_claims(evidence_context)

    return NutritionProviderSafeContext(
        schema_version=NUTRITION_PROVIDER_CONTEXT_SCHEMA_VERSION,
        section_id=NUTRITION_PROVIDER_SECTION_ID,
        user_id=evidence_context.user_id,
        report_date=evidence_context.report_date,
        confidence_ceiling=_confidence_ceiling(evidence_context),
        logging={
            "logging_completeness": summary.get("logging_completeness"),
            "logged_meal_count": logging_summary.get("logged_meal_count"),
            "entry_count": actuals.get("entry_count"),
            "source_count": actuals.get("source_count"),
            "missing_nutrient_fields": list(
                logging_summary.get("missing_nutrient_fields") or []
            ),
        },
        approved_actuals={
            "calories": actuals.get("logged_calories"),
            "protein_g": actuals.get("logged_protein"),
            "carbs_g": actuals.get("logged_carbs"),
            "fat_g": actuals.get("logged_fat"),
            "fiber_g": actuals.get("logged_fiber"),
        },
        approved_comparisons={
            nutrient: _safe_comparison(comparison)
            for nutrient, comparison in comparisons.items()
            if isinstance(comparison, dict)
        },
        approved_guidance={
            "summary_message": guidance.get("summary_message"),
            "protein_guidance": guidance.get("protein_guidance"),
            "calorie_guidance": guidance.get("calorie_guidance"),
            "macro_guidance": guidance.get("macro_guidance"),
            "logging_guidance": guidance.get("logging_guidance"),
        },
        approved_claims=[claim.to_dict() for claim in approved_claims],
        approved_food_suggestions=_safe_food_suggestions(suggestions),
        approved_numeric_values=_approved_numeric_values(
            actuals=actuals,
            comparisons=comparisons,
            suggestions=suggestions,
        ),
        limitations=list(evidence_context.limitations),
        reason_codes=list(evidence_context.reason_codes),
    )


def validate_candidate_nutrition_report_section(
    candidate: CandidateNutritionReportSection,
    *,
    safe_context: NutritionProviderSafeContext,
) -> NutritionProviderCandidateValidationResult:
    errors: list[str] = []
    text = _candidate_text(candidate)
    lowered = text.lower()
    claim_types = _approved_claim_types(safe_context)

    errors.extend(_unsupported_language_errors(lowered))
    errors.extend(_confidence_errors(candidate, safe_context))
    errors.extend(_field_level_claim_errors(lowered, claim_types))
    errors.extend(_numeric_value_errors(text, safe_context))
    errors.extend(_food_suggestion_errors(candidate.practical_food_focus, safe_context))

    unique_errors = _unique(errors)
    status = (
        NUTRITION_PROVIDER_VALIDATION_STATUS_REJECTED
        if unique_errors
        else NUTRITION_PROVIDER_VALIDATION_STATUS_APPROVED
    )
    return NutritionProviderCandidateValidationResult(
        valid=not unique_errors,
        validation_status=status,
        validation_errors=unique_errors,
        validation_error_categories=_validation_error_categories(unique_errors),
        validation_error_fields=_validation_error_fields(
            unique_errors,
            candidate=candidate,
        ),
    )


def build_nutrition_provider_safe_metadata(
    *,
    safe_context: NutritionProviderSafeContext,
    parse_result: NutritionProviderCandidateParseResult | None = None,
    validation_result: NutritionProviderCandidateValidationResult | None = None,
    provider_enabled: bool = False,
    provider_attempted: bool = False,
    selected_provider: str | None = _PROVIDER_DISABLED,
    selected_model: str | None = _PROVIDER_DISABLED,
    fallback_used: bool = False,
    fallback_reason: str | None = None,
    fallback_source: str | None = None,
    nutrition_section_source: str | None = None,
    provider_latency_ms: int | None = None,
) -> dict[str, Any]:
    """Build allowlisted metadata only; never include raw candidate/provider output."""

    validation_errors_count = (
        len(validation_result.validation_errors) if validation_result else 0
    )
    return {
        "nutrition_provider_contract_version": NUTRITION_PROVIDER_CONTRACT_VERSION,
        "nutrition_provider_context_schema_version": safe_context.schema_version,
        "nutrition_provider_execution_enabled": provider_enabled,
        "provider_enabled": provider_enabled,
        "provider_attempted": provider_attempted,
        "selected_provider": selected_provider,
        "selected_model": selected_model,
        "parse_status": parse_result.parse_status if parse_result else None,
        "candidate_valid": validation_result.valid if validation_result else None,
        "validation_status": (
            validation_result.validation_status if validation_result else None
        ),
        "validation_errors_count": validation_errors_count,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "fallback_source": fallback_source,
        "confidence_ceiling": safe_context.confidence_ceiling,
        "approved_claim_types": sorted(_approved_claim_types(safe_context)),
        "approved_food_suggestion_count": len(safe_context.approved_food_suggestions),
        "nutrition_section_source": nutrition_section_source,
        "provider_latency_ms": provider_latency_ms,
    }


def build_nutrition_provider_contract_fallback_result(
    evidence_context: NutritionReportEvidenceContext,
    *,
    safe_context: NutritionProviderSafeContext | None = None,
    parse_result: NutritionProviderCandidateParseResult | None = None,
    validation_result: NutritionProviderCandidateValidationResult | None = None,
    fallback_reason: str = NUTRITION_PROVIDER_FALLBACK_REASON_VALIDATION_FAILED,
) -> NutritionProviderFallbackResult:
    context = safe_context or build_nutrition_provider_safe_context(evidence_context)
    section = build_deterministic_nutrition_report_section(evidence_context)
    fallback_source = NUTRITION_PROVIDER_FALLBACK_SOURCE
    metadata = build_nutrition_provider_safe_metadata(
        safe_context=context,
        parse_result=parse_result,
        validation_result=validation_result,
        fallback_used=True,
        fallback_reason=fallback_reason,
        fallback_source=fallback_source,
    )
    return NutritionProviderFallbackResult(
        fallback_used=True,
        fallback_reason=fallback_reason,
        fallback_source=fallback_source,
        section=section,
        safe_metadata=metadata,
    )


def build_parse_failure_fallback_result(
    evidence_context: NutritionReportEvidenceContext,
    *,
    parse_result: NutritionProviderCandidateParseResult,
) -> NutritionProviderFallbackResult:
    return build_nutrition_provider_contract_fallback_result(
        evidence_context,
        parse_result=parse_result,
        fallback_reason=NUTRITION_PROVIDER_FALLBACK_REASON_PARSE_FAILED,
    )


def _confidence_ceiling(evidence_context: NutritionReportEvidenceContext) -> str:
    confidence = evidence_context.confidence
    if confidence not in NUTRITION_PROVIDER_CONFIDENCE_ORDER:
        return "Limited"
    return confidence


def _safe_comparison(comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "comparison_available": bool(comparison.get("comparison_available")),
        "target_status": comparison.get("target_status"),
        "actual": comparison.get("actual"),
        "target_min": comparison.get("target_min"),
        "target_max": comparison.get("target_max"),
        "confidence": comparison.get("confidence"),
    }


def _safe_food_suggestions(suggestions: dict[str, Any]) -> list[dict[str, Any]]:
    safe_suggestions: list[dict[str, Any]] = []
    for suggestion in suggestions.get("suggestions") or []:
        if not isinstance(suggestion, dict):
            continue
        safe_suggestions.append(
            {
                "canonical_food_id": suggestion.get("canonical_food_id"),
                "display_name": suggestion.get("display_name"),
                "suggested_grams": suggestion.get("suggested_grams"),
                "estimated_calories": suggestion.get("estimated_calories"),
                "estimated_protein_g": suggestion.get("estimated_protein_g"),
                "macro_gap_addressed": suggestion.get("macro_gap_addressed"),
                "suggestion_summary": suggestion.get("suggestion_summary"),
                "confidence": suggestion.get("confidence"),
            }
        )
    return safe_suggestions


def _candidate_text(candidate: CandidateNutritionReportSection) -> str:
    return "\n".join(
        [
            candidate.section_summary,
            candidate.intake_snapshot,
            candidate.target_alignment,
            candidate.logging_quality,
            candidate.practical_food_focus,
            candidate.next_nutrition_action,
            candidate.limitations_context,
        ]
    )


def _approved_claim_types(safe_context: NutritionProviderSafeContext) -> set[str]:
    return {
        str(claim.get("claim_type"))
        for claim in safe_context.approved_claims
        if isinstance(claim, dict) and claim.get("claim_type")
    }


def _unsupported_language_errors(lowered_text: str) -> list[str]:
    return [
        f"unsupported_nutrition_language: {term}"
        for term in sorted(NUTRITION_PROVIDER_UNSUPPORTED_LANGUAGE)
        if term in lowered_text
    ]


def _confidence_errors(
    candidate: CandidateNutritionReportSection,
    safe_context: NutritionProviderSafeContext,
) -> list[str]:
    candidate_level = NUTRITION_PROVIDER_CONFIDENCE_ORDER[candidate.confidence]
    ceiling_level = NUTRITION_PROVIDER_CONFIDENCE_ORDER[safe_context.confidence_ceiling]
    if candidate_level > ceiling_level:
        return [
            "candidate_confidence_exceeds_backend_confidence_ceiling: "
            f"{candidate.confidence} > {safe_context.confidence_ceiling}"
        ]
    return []


def _field_level_claim_errors(
    lowered_text: str,
    claim_types: set[str],
) -> list[str]:
    errors: list[str] = []
    required_claim_patterns = [
        ("protein appears below", CLAIM_PROTEIN_BELOW_TARGET),
        ("protein is below", CLAIM_PROTEIN_BELOW_TARGET),
        ("protein appears near", CLAIM_PROTEIN_NEAR_TARGET),
        ("protein is near", CLAIM_PROTEIN_NEAR_TARGET),
        ("calories appear below", CLAIM_CALORIES_BELOW_TARGET),
        ("calories are below", CLAIM_CALORIES_BELOW_TARGET),
        ("calories appear near", CLAIM_CALORIES_NEAR_TARGET),
        ("calories are near", CLAIM_CALORIES_NEAR_TARGET),
        ("calories appear above", CLAIM_CALORIES_ABOVE_TARGET),
        ("calories are above", CLAIM_CALORIES_ABOVE_TARGET),
    ]
    for phrase, claim_type in required_claim_patterns:
        if phrase in lowered_text and claim_type not in claim_types:
            errors.append(
                f"field_claim_requires_approved_claim: {phrase} -> {claim_type}"
            )
    return errors


def _numeric_value_errors(
    text: str,
    safe_context: NutritionProviderSafeContext,
) -> list[str]:
    errors: list[str] = []
    allowed_numbers = _allowed_numbers(safe_context)
    for value in _extract_number_unit_values(text):
        if value not in allowed_numbers:
            errors.append(f"numeric_value_not_approved_by_evidence: {value:g}")
    return errors


def _allowed_numbers(safe_context: NutritionProviderSafeContext) -> set[float]:
    return {float(value) for value in safe_context.approved_numeric_values}


def _approved_numeric_values(
    *,
    actuals: dict[str, Any],
    comparisons: dict[str, Any],
    suggestions: dict[str, Any],
) -> list[float]:
    """Return exact numeric values a provider may repeat.

    Do not include derived deltas/gaps/percentages here. If the model infers
    a gap such as 40 g from 120 g target and 80 g actual, the validator should
    reject it until the backend explicitly approves that number.
    """

    values: set[float] = set()
    for value in actuals.values():
        _add_number(values, value)
    for comparison in comparisons.values():
        if not isinstance(comparison, dict):
            continue
        for key in ["actual", "target_min", "target_max"]:
            _add_number(values, comparison.get(key))
    for suggestion in _safe_food_suggestions(suggestions):
        for key in ["suggested_grams", "estimated_calories", "estimated_protein_g"]:
            _add_number(values, suggestion.get(key))
    return sorted(values)


def _extract_number_unit_values(text: str) -> list[float]:
    values: list[float] = []
    for match in re.finditer(
        r"\b(\d+(?:\.\d+)?)\s*(?:g|grams|calories|kcal)\b", text, re.I
    ):
        values.append(float(match.group(1)))
    return values


def _add_number(values: set[float], value: Any) -> None:
    if isinstance(value, int | float):
        values.add(float(value))


def _food_suggestion_errors(
    practical_food_focus: str,
    safe_context: NutritionProviderSafeContext,
) -> list[str]:
    lowered = practical_food_focus.lower()
    approved_food_names = {
        str(suggestion.get("display_name", "")).lower()
        for suggestion in safe_context.approved_food_suggestions
        if suggestion.get("display_name")
    }
    claim_types = _approved_claim_types(safe_context)

    if _is_safe_food_suggestion_unavailable_language(lowered):
        return []

    food_language_present = any(
        phrase in lowered
        for phrase in [
            "can help close",
            "suggestion",
            "serving",
            "grams",
            " g",
        ]
    )

    if not food_language_present:
        return []

    if CLAIM_FOOD_SUGGESTION_AVAILABLE not in claim_types:
        return ["food_suggestion_language_requires_approved_food_suggestion_claim"]

    if not approved_food_names:
        return ["food_suggestion_language_requires_approved_canonical_food"]

    if not any(food_name in lowered for food_name in approved_food_names):
        return ["food_suggestion_mentions_no_approved_canonical_food"]

    return []


def _is_safe_food_suggestion_unavailable_language(lowered_text: str) -> bool:
    """Allow negative food-suggestion limitation language without an approved suggestion.

    The provider may safely say that no approved food suggestion is available.
    It may not turn that into a serving recommendation or invented food.
    """

    unavailable_patterns = [
        "no approved canonical food suggestion",
        "no approved food suggestion",
        "no approved suggestion",
        "no food suggestion is available",
        "no canonical food suggestion is available",
        "approved food suggestion is not available",
        "canonical food suggestion is not available",
    ]
    recommendation_patterns = [
        "can help close",
        "add ",
        "eat ",
        "use ",
        "try ",
        "serving",
        "grams",
        " g",
    ]
    return any(pattern in lowered_text for pattern in unavailable_patterns) and not any(
        pattern in lowered_text for pattern in recommendation_patterns
    )


def validation_error_categories_from_errors(errors: list[str]) -> list[str]:
    """Return safe category names for raw validation or parse error strings.

    This is intended for explicit debug/QA surfaces only. Public/persisted report
    metadata should keep using validation_errors_count and status fields instead
    of these more detailed diagnostics.
    """

    return _validation_error_categories(errors)


def validation_error_fields_from_errors(
    errors: list[str],
    *,
    candidate: CandidateNutritionReportSection | None = None,
) -> list[str]:
    return _validation_error_fields(errors, candidate=candidate)


def _validation_error_categories(errors: list[str]) -> list[str]:
    return _unique([_category_for_error(error) for error in errors])


def _category_for_error(error: str) -> str:
    lowered = error.lower()
    if lowered.startswith("numeric_value_not_approved_by_evidence"):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_NUMERIC_VALUE
    if "serving" in lowered or "grams" in lowered or " g" in lowered:
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_SERVING_SIZE
    if lowered.startswith(
        "food_suggestion_language_requires_approved_food_suggestion_claim"
    ):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_FOOD_SUGGESTION_AVAILABILITY
    if "food_suggestion" in lowered:
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_FOOD_SUGGESTION
    if lowered.startswith("field_claim_requires_approved_claim"):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_FIELD_CLAIM_NOT_APPROVED
    if lowered.startswith("candidate_confidence_exceeds_backend_confidence_ceiling"):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_CONFIDENCE_CEILING
    if lowered.startswith("missing_keys"):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_MISSING_REQUIRED_FIELD
    if lowered.startswith("extra_keys_detected") or lowered.startswith(
        "disallowed_keys_detected"
    ):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_EXTRA_KEY
    if lowered.startswith("invalid_enum_value"):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_INVALID_ENUM
    if lowered.startswith("empty_content") or lowered.startswith("placeholder_content"):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_EMPTY_OR_PLACEHOLDER
    if lowered.startswith("type_mismatch"):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_TYPE_MISMATCH
    if lowered.startswith("wrapper_object_detected"):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_WRAPPER_OBJECT
    if (
        lowered.startswith("invalid_json")
        or "must be exactly one json object" in lowered
        or "must be a json object" in lowered
        or "candidate output is empty" in lowered
    ):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_INVALID_JSON
    if lowered.startswith("unsupported_nutrition_language"):
        return _unsupported_language_category(lowered)
    return NUTRITION_PROVIDER_VALIDATION_CATEGORY_VALIDATION_FAILURE


def _unsupported_language_category(lowered_error: str) -> str:
    if "supplement" in lowered_error:
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_SUPPLEMENT_CLAIM
    if any(
        term in lowered_error
        for term in [
            "deficiency",
            "deficient",
            "medical advice",
            "diagnose",
            "disease",
            "fatigue",
            "metabolism",
        ]
    ):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_MEDICAL_CLAIM
    if any(term in lowered_error for term in ["guaranteed", "will cause weight loss"]):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_GUARANTEE_CLAIM
    if any(
        term in lowered_error
        for term in [
            "noncompliant",
            "non-compliant",
            "compliant",
            "you failed",
            "diet is bad",
            "bad diet",
        ]
    ):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_SHAME_LANGUAGE
    if any(
        term in lowered_error
        for term in [
            "meal",
            "keto",
            "intermittent fasting",
            "skip meals",
            "compensate tomorrow",
            "burn this off",
            "you must eat",
        ]
    ):
        return NUTRITION_PROVIDER_VALIDATION_CATEGORY_UNSUPPORTED_MEAL_PLAN
    return NUTRITION_PROVIDER_VALIDATION_CATEGORY_VALIDATION_FAILURE


def _validation_error_fields(
    errors: list[str],
    *,
    candidate: CandidateNutritionReportSection | None = None,
) -> list[str]:
    fields: list[str] = []
    for error in errors:
        fields.extend(_fields_for_error(error, candidate=candidate))
    return _unique(fields)


def _fields_for_error(
    error: str,
    *,
    candidate: CandidateNutritionReportSection | None,
) -> list[str]:
    lowered = error.lower()
    if lowered.startswith("candidate_confidence_exceeds"):
        return ["confidence"]
    if "food_suggestion" in lowered:
        return ["practical_food_focus"]
    if lowered.startswith("field_claim_requires_approved_claim"):
        phrase = lowered.split(":", 1)[-1].split("->", 1)[0].strip()
        return _candidate_fields_containing(candidate, phrase) or ["target_alignment"]
    if lowered.startswith("numeric_value_not_approved_by_evidence"):
        number = lowered.split(":", 1)[-1].strip() if ":" in lowered else ""
        return _candidate_fields_containing(candidate, number) or ["candidate_text"]
    if lowered.startswith("unsupported_nutrition_language"):
        term = lowered.split(":", 1)[-1].strip() if ":" in lowered else ""
        return _candidate_fields_containing(candidate, term) or ["candidate_text"]
    if any(
        lowered.startswith(prefix)
        for prefix in [
            "missing_keys",
            "extra_keys_detected",
            "disallowed_keys_detected",
        ]
    ):
        return ["candidate_schema"]
    if lowered.startswith("invalid_enum_value"):
        return ["confidence"]
    if lowered.startswith("empty_content") or lowered.startswith("placeholder_content"):
        return [lowered.split(":", 1)[-1].strip()]
    if lowered.startswith("type_mismatch"):
        return [lowered.split(":", 1)[-1].split("must", 1)[0].strip()]
    if lowered.startswith("wrapper_object_detected"):
        return ["candidate_wrapper"]
    return ["candidate_text"]


def _candidate_fields_containing(
    candidate: CandidateNutritionReportSection | None,
    term: str,
) -> list[str]:
    if candidate is None or not term:
        return []
    fields = []
    for field_name, value in _candidate_field_text(candidate).items():
        if term in value.lower():
            fields.append(field_name)
    return fields


def _candidate_field_text(candidate: CandidateNutritionReportSection) -> dict[str, str]:
    return {
        "section_summary": candidate.section_summary,
        "intake_snapshot": candidate.intake_snapshot,
        "target_alignment": candidate.target_alignment,
        "logging_quality": candidate.logging_quality,
        "practical_food_focus": candidate.practical_food_focus,
        "next_nutrition_action": candidate.next_nutrition_action,
        "limitations_context": candidate.limitations_context,
    }


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values
