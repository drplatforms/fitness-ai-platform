from __future__ import annotations

from typing import Any

from models.nutrition_food_suggestion_models import ApprovedNutritionFoodSuggestions
from models.nutrition_report_section_models import (
    CLAIM_ACTUALS_LOGGED,
    CLAIM_CALORIES_ABOVE_TARGET,
    CLAIM_CALORIES_BELOW_TARGET,
    CLAIM_CALORIES_NEAR_TARGET,
    CLAIM_CONFIDENCE_LIMITED_BY_MISSING_LOGS,
    CLAIM_FOOD_SUGGESTION_AVAILABLE,
    CLAIM_LOGGING_COMPLETE_ENOUGH,
    CLAIM_LOGGING_INCOMPLETE,
    CLAIM_PROTEIN_BELOW_TARGET,
    CLAIM_PROTEIN_NEAR_TARGET,
    CLAIM_TARGET_AVAILABLE,
    NUTRITION_REPORT_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
    ApprovedNutritionClaim,
    ApprovedNutritionReportSection,
    CandidateNutritionReportSection,
    NutritionReportEvidenceContext,
    NutritionReportSectionValidationResult,
)
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    TARGET_STATUS_ABOVE,
    TARGET_STATUS_BELOW,
    TARGET_STATUS_NEAR,
    ApprovedNutritionGuidance,
    TargetVsActualNutritionSummary,
)
from services.nutrition_food_suggestion_service import (
    build_approved_nutrition_food_suggestions,
)
from services.nutrition_target_vs_actual_service import (
    build_approved_nutrition_guidance,
    build_target_vs_actual_nutrition_summary,
    validate_target_vs_actual_nutrition_summary,
)

NUTRITION_REPORT_SECTION_ID = "nutrition_report_section"

FORBIDDEN_NUTRITION_REPORT_TEXT_TERMS = {
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


def build_nutrition_report_evidence_context(
    *,
    user_id: int,
    report_date: str,
    target_vs_actual_summary: TargetVsActualNutritionSummary | None = None,
    approved_food_suggestions: ApprovedNutritionFoodSuggestions | None = None,
) -> NutritionReportEvidenceContext:
    """Build the backend-owned nutrition section evidence context.

    This service reads already-approved nutrition target/actual/completeness and
    canonical food-suggestion services. It does not call AI, infer missing values,
    mutate targets, create meal plans, or unlock blocked nutrition targets.
    """

    summary = target_vs_actual_summary or build_target_vs_actual_nutrition_summary(
        user_id,
        report_date,
    )
    guidance = build_approved_nutrition_guidance(summary)
    suggestions = (
        approved_food_suggestions
        or build_approved_nutrition_food_suggestions(
            user_id,
            report_date,
            target_vs_actual_summary=summary,
        )
    )

    return NutritionReportEvidenceContext(
        user_id=user_id,
        report_date=report_date,
        target_vs_actual_summary=summary.to_dict(),
        approved_nutrition_guidance=guidance.to_dict(),
        approved_food_suggestions=suggestions.to_dict(),
        confidence=summary.confidence,
        reason_codes=_unique(
            [
                "nutrition_report_section_evidence_context",
                *summary.reason_codes,
                *guidance.reason_codes,
                *suggestions.reason_codes,
            ]
        ),
        limitations=_unique(
            [
                *summary.limitations,
                *guidance.limitations,
                *suggestions.limitations,
            ]
        ),
    )


def derive_approved_nutrition_claims(
    evidence_context: NutritionReportEvidenceContext,
) -> list[ApprovedNutritionClaim]:
    """Derive bounded nutrition claims from backend-approved evidence only."""

    summary = evidence_context.target_vs_actual_summary
    suggestions = evidence_context.approved_food_suggestions or {}
    comparisons = summary.get("comparisons") or {}
    logging_summary = summary.get("logging_summary") or {}
    actuals = summary.get("nutrition_actuals") or {}

    confidence = str(summary.get("confidence") or evidence_context.confidence)
    claims: list[ApprovedNutritionClaim] = []

    if int(actuals.get("entry_count") or 0) > 0:
        claims.append(
            _claim(
                CLAIM_ACTUALS_LOGGED,
                "Nutrition entries are logged for this date.",
                ["nutrition_actuals.entry_count"],
                confidence,
                ["nutrition_entries_logged"],
            )
        )

    logging_completeness = str(summary.get("logging_completeness") or "")
    if logging_completeness == LOGGING_COMPLETENESS_COMPLETE_ENOUGH:
        claims.append(
            _claim(
                CLAIM_LOGGING_COMPLETE_ENOUGH,
                "Nutrition logging is complete enough for cautious target comparison.",
                ["logging_summary.logging_completeness"],
                confidence,
                ["logging_complete_enough"],
            )
        )
    elif logging_completeness in {
        LOGGING_COMPLETENESS_NO_LOGS,
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
        LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    }:
        claims.append(
            _claim(
                CLAIM_LOGGING_INCOMPLETE,
                "Nutrition logging is incomplete, so conclusions should stay limited.",
                ["logging_summary.logging_completeness"],
                _limited_or_low(confidence),
                ["nutrition_logging_incomplete"],
                list(logging_summary.get("limitations") or []),
            )
        )

    for nutrient, comparison in comparisons.items():
        if not isinstance(comparison, dict):
            continue
        if comparison.get("comparison_available"):
            claims.append(
                _claim(
                    CLAIM_TARGET_AVAILABLE,
                    f"{_nutrient_label(nutrient)} target comparison is available.",
                    [f"comparisons.{nutrient}.comparison_available"],
                    str(comparison.get("confidence") or confidence),
                    [f"{nutrient}_target_available"],
                )
            )

    protein = comparisons.get("protein") or {}
    if protein.get("comparison_available"):
        if protein.get("target_status") == TARGET_STATUS_BELOW:
            claims.append(
                _claim(
                    CLAIM_PROTEIN_BELOW_TARGET,
                    "Protein appears below the approved target based on logged entries.",
                    ["comparisons.protein.target_status"],
                    str(protein.get("confidence") or confidence),
                    ["protein_below_approved_target"],
                )
            )
        elif protein.get("target_status") == TARGET_STATUS_NEAR:
            claims.append(
                _claim(
                    CLAIM_PROTEIN_NEAR_TARGET,
                    "Protein appears near the approved target based on logged entries.",
                    ["comparisons.protein.target_status"],
                    str(protein.get("confidence") or confidence),
                    ["protein_near_approved_target"],
                )
            )

    calories = comparisons.get("calories") or {}
    if calories.get("comparison_available"):
        calorie_status = calories.get("target_status")
        if calorie_status == TARGET_STATUS_BELOW:
            claims.append(
                _claim(
                    CLAIM_CALORIES_BELOW_TARGET,
                    "Calories appear below the approved range based on complete-enough logs.",
                    ["comparisons.calories.target_status"],
                    str(calories.get("confidence") or confidence),
                    ["calories_below_approved_target"],
                )
            )
        elif calorie_status == TARGET_STATUS_NEAR:
            claims.append(
                _claim(
                    CLAIM_CALORIES_NEAR_TARGET,
                    "Calories appear near the approved range based on complete-enough logs.",
                    ["comparisons.calories.target_status"],
                    str(calories.get("confidence") or confidence),
                    ["calories_near_approved_target"],
                )
            )
        elif calorie_status == TARGET_STATUS_ABOVE:
            claims.append(
                _claim(
                    CLAIM_CALORIES_ABOVE_TARGET,
                    "Calories appear above the approved range based on complete-enough logs.",
                    ["comparisons.calories.target_status"],
                    str(calories.get("confidence") or confidence),
                    ["calories_above_approved_target"],
                )
            )

    approved_suggestions = suggestions.get("suggestions") or []
    if approved_suggestions:
        claims.append(
            _claim(
                CLAIM_FOOD_SUGGESTION_AVAILABLE,
                "A canonical food suggestion is available for an approved nutrition gap.",
                ["approved_food_suggestions.suggestions"],
                str(suggestions.get("confidence") or confidence),
                ["approved_food_suggestion_available"],
            )
        )

    if confidence in {"Limited", "Low"} or logging_completeness in {
        LOGGING_COMPLETENESS_NO_LOGS,
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
        LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    }:
        claims.append(
            _claim(
                CLAIM_CONFIDENCE_LIMITED_BY_MISSING_LOGS,
                "Nutrition confidence is limited by logging completeness or missing values.",
                ["confidence", "logging_summary.logging_completeness"],
                _limited_or_low(confidence),
                ["nutrition_confidence_limited_by_logging"],
                list(evidence_context.limitations),
            )
        )

    if not claims:
        claims.append(
            _claim(
                CLAIM_LOGGING_INCOMPLETE,
                "Nutrition evidence is limited, so the section should stay conservative.",
                ["target_vs_actual_summary"],
                "Limited",
                ["nutrition_evidence_limited"],
                list(evidence_context.limitations),
            )
        )

    return _unique_claims(claims)


def build_deterministic_nutrition_report_section(
    evidence_context: NutritionReportEvidenceContext,
    *,
    source: str = NUTRITION_REPORT_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
) -> ApprovedNutritionReportSection:
    claims = derive_approved_nutrition_claims(evidence_context)
    summary = evidence_context.target_vs_actual_summary
    guidance = evidence_context.approved_nutrition_guidance or {}
    suggestions = evidence_context.approved_food_suggestions or {}

    candidate = CandidateNutritionReportSection(
        section_summary=_section_summary(guidance, summary),
        intake_snapshot=_intake_snapshot(summary),
        target_alignment=_target_alignment(guidance, claims),
        logging_quality=_logging_quality(guidance, summary),
        practical_food_focus=_practical_food_focus(suggestions),
        next_nutrition_action=_next_nutrition_action(guidance, claims),
        limitations_context=_limitations_context(evidence_context),
        confidence=evidence_context.confidence,
        reason_codes=_unique(
            [
                "deterministic_nutrition_report_section",
                *evidence_context.reason_codes,
            ]
        ),
    )
    approved = ApprovedNutritionReportSection.from_candidate(
        candidate,
        approved_claims=claims,
        source=source,
    )
    validation = validate_nutrition_report_section(
        approved,
        evidence_context=evidence_context,
    )
    if not validation.valid:
        return _safe_limited_section(evidence_context, validation.validation_errors)
    return approved


def validate_nutrition_report_section(
    section: ApprovedNutritionReportSection,
    *,
    evidence_context: NutritionReportEvidenceContext,
) -> NutritionReportSectionValidationResult:
    errors: list[str] = []
    text = _section_text(section)
    lowered = text.lower()

    for term in FORBIDDEN_NUTRITION_REPORT_TEXT_TERMS:
        if term in lowered:
            errors.append(f"Nutrition report section contains forbidden term: {term}")
            break

    summary = evidence_context.target_vs_actual_summary
    comparisons = summary.get("comparisons") or {}
    protein = comparisons.get("protein") or {}
    calories = comparisons.get("calories") or {}

    if not protein.get("comparison_available"):
        unsupported_protein_terms = [
            "protein appears below",
            "protein is below",
            "protein appears near",
            "protein is near",
        ]
        if any(term in lowered for term in unsupported_protein_terms):
            errors.append(
                "Protein target-alignment claims require an available protein comparison."
            )

    if not calories.get("comparison_available"):
        unsupported_calorie_terms = [
            "calories appear below",
            "calories are below",
            "calories appear near",
            "calories are near",
            "calories appear above",
            "calories are above",
            "calorie target comparison is available",
        ]
        if any(term in lowered for term in unsupported_calorie_terms):
            errors.append(
                "Calorie target-alignment claims require an available calorie comparison."
            )

    guidance_errors = validate_target_vs_actual_nutrition_summary(
        _summary_from_context(evidence_context),
        _guidance_from_context(evidence_context),
    )
    errors.extend(guidance_errors)

    return NutritionReportSectionValidationResult(
        valid=not errors,
        validation_errors=_unique(errors),
    )


def _claim(
    claim_type: str,
    claim_text: str,
    evidence_fields: list[str],
    confidence: str,
    reason_codes: list[str],
    limitations: list[str] | None = None,
) -> ApprovedNutritionClaim:
    return ApprovedNutritionClaim(
        claim_type=claim_type,
        claim_text=claim_text,
        evidence_fields=evidence_fields,
        confidence=(
            confidence
            if confidence in {"Limited", "Low", "Moderate", "High"}
            else "Limited"
        ),
        reason_codes=reason_codes,
        limitations=limitations or [],
    )


def _limited_or_low(confidence: str) -> str:
    return "Limited" if confidence == "Limited" else "Low"


def _nutrient_label(nutrient: str) -> str:
    labels = {
        "calories": "Calorie",
        "protein": "Protein",
        "carbs": "Carbohydrate",
        "fat": "Fat",
    }
    return labels.get(nutrient, nutrient.title())


def _section_summary(guidance: dict[str, Any], summary: dict[str, Any]) -> str:
    if guidance.get("summary_message"):
        return str(guidance["summary_message"])
    if summary.get("logging_completeness") == LOGGING_COMPLETENESS_NO_LOGS:
        return "No nutrition logs were found for this date."
    return "Nutrition should be reviewed using approved logged data and target context."


def _intake_snapshot(summary: dict[str, Any]) -> str:
    actuals = summary.get("nutrition_actuals") or {}
    entry_count = int(actuals.get("entry_count") or 0)
    if entry_count == 0:
        return "No logged nutrition entries are available for this report date."

    values = []
    if actuals.get("logged_calories") is not None:
        values.append(f"{actuals['logged_calories']:g} calories")
    if actuals.get("logged_protein") is not None:
        values.append(f"{actuals['logged_protein']:g} g protein")
    if actuals.get("logged_carbs") is not None:
        values.append(f"{actuals['logged_carbs']:g} g carbohydrates")
    if actuals.get("logged_fat") is not None:
        values.append(f"{actuals['logged_fat']:g} g fat")

    if values:
        return (
            f"Logged intake includes {', '.join(values)} across {entry_count} entries."
        )
    return f"{entry_count} nutrition entries are logged, but usable calorie or macro values are limited."


def _target_alignment(
    guidance: dict[str, Any], claims: list[ApprovedNutritionClaim]
) -> str:
    claim_types = {claim.claim_type for claim in claims}
    if CLAIM_PROTEIN_BELOW_TARGET in claim_types:
        return "Protein appears below the approved target based on logged entries."
    if CLAIM_PROTEIN_NEAR_TARGET in claim_types:
        return "Protein appears near the approved target based on logged entries."
    if CLAIM_CALORIES_BELOW_TARGET in claim_types:
        return "Calories appear below the approved range based on complete-enough logs."
    if CLAIM_CALORIES_NEAR_TARGET in claim_types:
        return "Calories appear near the approved range based on complete-enough logs."
    if CLAIM_CALORIES_ABOVE_TARGET in claim_types:
        return "Calories appear above the approved range based on complete-enough logs."
    if guidance.get("protein_guidance"):
        return str(guidance["protein_guidance"])
    return "Target alignment is limited until approved targets and logged actuals are available."


def _logging_quality(guidance: dict[str, Any], summary: dict[str, Any]) -> str:
    if guidance.get("logging_guidance"):
        return str(guidance["logging_guidance"])
    completeness = summary.get("logging_completeness")
    if completeness == LOGGING_COMPLETENESS_COMPLETE_ENOUGH:
        return (
            "Logged intake is complete enough to support cautious nutrition guidance."
        )
    return "Logging completeness limits nutrition confidence for this report."


def _practical_food_focus(suggestions: dict[str, Any]) -> str:
    approved_suggestions = suggestions.get("suggestions") or []
    if not approved_suggestions:
        return "No approved canonical food suggestion is available from the current evidence."
    first = approved_suggestions[0]
    display_name = first.get("display_name") or "an approved canonical food"
    macro_gap = str(first.get("macro_gap_addressed") or "nutrition gap").replace(
        "_g", ""
    )
    grams = first.get("suggested_grams")
    if grams is not None:
        return f"{display_name} at about {grams:g} g is an approved option for the {macro_gap} gap."
    return f"{display_name} is an approved option for the {macro_gap} gap."


def _next_nutrition_action(
    guidance: dict[str, Any], claims: list[ApprovedNutritionClaim]
) -> str:
    claim_types = {claim.claim_type for claim in claims}
    if CLAIM_LOGGING_INCOMPLETE in claim_types:
        return "Log a complete day before making stronger nutrition changes."
    if CLAIM_FOOD_SUGGESTION_AVAILABLE in claim_types:
        return "Use an approved canonical food suggestion if it fits the current meal plan."
    if guidance.get("macro_guidance"):
        return str(guidance["macro_guidance"])
    return "Keep logging consistently so nutrition guidance can become more specific."


def _limitations_context(evidence_context: NutritionReportEvidenceContext) -> str:
    if evidence_context.limitations:
        return " ".join(evidence_context.limitations[:2])
    if evidence_context.confidence in {"Limited", "Low"}:
        return "Nutrition confidence is limited, so this section stays conservative."
    return "Nutrition guidance is bounded to backend-approved targets, actuals, and suggestions."


def _safe_limited_section(
    evidence_context: NutritionReportEvidenceContext,
    validation_errors: list[str],
) -> ApprovedNutritionReportSection:
    fallback_claim = _claim(
        CLAIM_CONFIDENCE_LIMITED_BY_MISSING_LOGS,
        "Nutrition confidence is limited, so this section should stay conservative.",
        ["confidence", "validation"],
        "Limited",
        ["nutrition_report_section_validation_fallback"],
        validation_errors,
    )
    candidate = CandidateNutritionReportSection(
        section_summary="Nutrition evidence is limited for this report date.",
        intake_snapshot="Usable logged nutrition details are limited for this report date.",
        target_alignment="Target alignment should stay limited until approved comparisons are available.",
        logging_quality="Improve logging completeness before making stronger nutrition changes.",
        practical_food_focus="No approved food suggestion should be treated as required.",
        next_nutrition_action="Keep logging complete meals and review approved Nutrition tab guidance.",
        limitations_context="This section is conservative because validation found unsupported nutrition language.",
        confidence="Limited",
        reason_codes=[
            "deterministic_nutrition_report_section_validation_fallback",
            *evidence_context.reason_codes,
        ],
    )
    return ApprovedNutritionReportSection.from_candidate(
        candidate,
        approved_claims=[fallback_claim],
        source=NUTRITION_REPORT_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
    )


def _summary_from_context(
    evidence_context: NutritionReportEvidenceContext,
) -> TargetVsActualNutritionSummary:
    return _summary_from_dict(evidence_context.target_vs_actual_summary)


def _guidance_from_context(
    evidence_context: NutritionReportEvidenceContext,
) -> ApprovedNutritionGuidance:
    return ApprovedNutritionGuidance(**evidence_context.approved_nutrition_guidance)


def _summary_from_dict(payload: dict[str, Any]) -> TargetVsActualNutritionSummary:
    from models.nutrition_target_vs_actual_models import (
        NutritionActuals,
        NutritionLoggingSummary,
        NutritionTargetComparison,
    )

    actuals = NutritionActuals(**payload["nutrition_actuals"])
    logging_summary = NutritionLoggingSummary(**payload["logging_summary"])
    comparisons = {
        nutrient: NutritionTargetComparison(**comparison)
        for nutrient, comparison in payload["comparisons"].items()
    }
    return TargetVsActualNutritionSummary(
        user_id=payload["user_id"],
        date=payload["date"],
        nutrition_actuals=actuals,
        logging_summary=logging_summary,
        comparisons=comparisons,
        logging_completeness=payload["logging_completeness"],
        confidence=payload["confidence"],
        reason_codes=list(payload.get("reason_codes", [])),
        limitations=list(payload.get("limitations", [])),
    )


def _section_text(section: ApprovedNutritionReportSection) -> str:
    return "\n".join(
        [
            section.section_summary,
            section.intake_snapshot,
            section.target_alignment,
            section.logging_quality,
            section.practical_food_focus,
            section.next_nutrition_action,
            section.limitations_context,
            *[claim.claim_text for claim in section.approved_claims],
        ]
    )


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _unique_claims(
    claims: list[ApprovedNutritionClaim],
) -> list[ApprovedNutritionClaim]:
    seen: set[str] = set()
    unique_claims: list[ApprovedNutritionClaim] = []
    for claim in claims:
        key = f"{claim.claim_type}:{claim.claim_text}"
        if key in seen:
            continue
        seen.add(key)
        unique_claims.append(claim)
    return unique_claims
