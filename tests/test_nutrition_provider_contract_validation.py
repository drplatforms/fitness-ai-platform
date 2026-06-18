from __future__ import annotations

from models.nutrition_food_suggestion_models import (
    ApprovedFoodSuggestion,
    ApprovedNutritionFoodSuggestions,
    NutritionMacroGap,
)
from models.nutrition_provider_contract_models import (
    NUTRITION_PROVIDER_VALIDATION_STATUS_APPROVED,
    NUTRITION_PROVIDER_VALIDATION_STATUS_REJECTED,
)
from models.nutrition_report_section_models import CandidateNutritionReportSection
from models.nutrition_target_vs_actual_models import (
    ApprovedNutritionGuidance,
    NutritionActuals,
    NutritionLoggingSummary,
    NutritionTargetComparison,
    TargetVsActualNutritionSummary,
)
from services.nutrition_provider_validation_service import (
    build_nutrition_provider_safe_context,
    validate_candidate_nutrition_report_section,
)
from services.nutrition_report_section_service import NutritionReportEvidenceContext


def _candidate(**overrides) -> CandidateNutritionReportSection:
    payload = {
        "section_summary": "Nutrition logging is incomplete, so conclusions should stay limited.",
        "intake_snapshot": "One nutrition entry is logged for this report date.",
        "target_alignment": "Protein comparison is limited until approved targets and logs are available.",
        "logging_quality": "Logged intake is incomplete, so avoid bigger changes from this day alone.",
        "practical_food_focus": "No approved canonical food suggestion is available from the current evidence.",
        "next_nutrition_action": "Log a complete day before changing nutrition targets.",
        "limitations_context": "This section stays limited because nutrition logging is incomplete.",
        "confidence": "Low",
        "reason_codes": ["nutrition_provider_validation_test"],
    }
    payload.update(overrides)
    return CandidateNutritionReportSection(**payload)


def _summary_partial() -> TargetVsActualNutritionSummary:
    actuals = NutritionActuals(
        user_id=102,
        logging_date="2026-06-14",
        logging_window="daily",
        logged_calories=None,
        logged_protein=35.0,
        logged_carbs=None,
        logged_fat=None,
        logged_fiber=None,
        logged_meal_count=1,
        entry_count=1,
        source_count=1,
        reason_codes=["partial_logging"],
    )
    logging = NutritionLoggingSummary(
        user_id=102,
        logging_date="2026-06-14",
        logging_completeness="partial_day",
        confidence="Low",
        logged_meal_count=1,
        entry_count=1,
        reason_codes=["partial_day"],
        limitations=["Nutrition logging appears partial for this date."],
    )
    comparisons = {
        "protein": NutritionTargetComparison(
            nutrient="protein",
            actual=35.0,
            target_min=None,
            target_max=None,
            delta_min=None,
            delta_max=None,
            percent_of_target=None,
            target_status="unavailable",
            comparison_available=False,
            confidence="Low",
            reason_codes=["protein_target_unavailable"],
            limitations=["Protein comparison is unavailable."],
        ),
        "calories": NutritionTargetComparison(
            nutrient="calories",
            actual=None,
            target_min=None,
            target_max=None,
            delta_min=None,
            delta_max=None,
            percent_of_target=None,
            target_status="unavailable",
            comparison_available=False,
            confidence="Low",
            reason_codes=["calorie_target_unavailable"],
            limitations=["Calorie comparison is unavailable."],
        ),
    }
    return TargetVsActualNutritionSummary(
        user_id=102,
        date="2026-06-14",
        nutrition_actuals=actuals,
        logging_summary=logging,
        comparisons=comparisons,
        logging_completeness="partial_day",
        confidence="Low",
        reason_codes=["partial_nutrition_logging"],
        limitations=["Nutrition logging appears partial for this date."],
    )


def _summary_protein_gap() -> TargetVsActualNutritionSummary:
    actuals = NutritionActuals(
        user_id=102,
        logging_date="2026-06-14",
        logging_window="daily",
        logged_calories=1850.0,
        logged_protein=80.0,
        logged_carbs=190.0,
        logged_fat=65.0,
        logged_fiber=24.0,
        logged_meal_count=3,
        entry_count=8,
        source_count=8,
        reason_codes=["complete_logging"],
    )
    logging = NutritionLoggingSummary(
        user_id=102,
        logging_date="2026-06-14",
        logging_completeness="complete_enough",
        confidence="High",
        logged_meal_count=3,
        entry_count=8,
        reason_codes=["complete_enough"],
        limitations=[],
    )
    comparisons = {
        "protein": NutritionTargetComparison(
            nutrient="protein",
            actual=80.0,
            target_min=120.0,
            target_max=150.0,
            delta_min=-40.0,
            delta_max=-70.0,
            percent_of_target=0.67,
            target_status="below_target",
            comparison_available=True,
            confidence="High",
            reason_codes=["protein_below_target"],
            limitations=[],
        ),
        "calories": NutritionTargetComparison(
            nutrient="calories",
            actual=1850.0,
            target_min=1800.0,
            target_max=2100.0,
            delta_min=50.0,
            delta_max=-250.0,
            percent_of_target=0.95,
            target_status="near_target",
            comparison_available=True,
            confidence="High",
            reason_codes=["calories_near_target"],
            limitations=[],
        ),
    }
    return TargetVsActualNutritionSummary(
        user_id=102,
        date="2026-06-14",
        nutrition_actuals=actuals,
        logging_summary=logging,
        comparisons=comparisons,
        logging_completeness="complete_enough",
        confidence="High",
        reason_codes=["complete_enough_for_guidance"],
        limitations=[],
    )


def _guidance(summary: TargetVsActualNutritionSummary) -> ApprovedNutritionGuidance:
    return ApprovedNutritionGuidance(
        user_id=summary.user_id,
        date=summary.date,
        summary_message="Nutrition evidence should stay tied to approved targets and logs.",
        protein_guidance="Protein comparison is limited until approved targets and logs are available.",
        calorie_guidance="Calorie comparison is limited until approved targets and logs are available.",
        macro_guidance="Macro conclusions should stay bounded to approved comparisons.",
        logging_guidance="Logged intake should be interpreted based on logging completeness.",
        confidence=summary.confidence,
        reason_codes=["approved_guidance"],
        limitations=list(summary.limitations),
    )


def _suggestions(with_suggestion: bool = False) -> ApprovedNutritionFoodSuggestions:
    macro_gap = NutritionMacroGap(
        macro_name="protein_g",
        target_value=120.0 if with_suggestion else None,
        actual_value=80.0 if with_suggestion else None,
        gap_value=40.0 if with_suggestion else None,
        unit="g",
        target_status="below_target" if with_suggestion else "unavailable",
        display_allowed=with_suggestion,
        confidence="High" if with_suggestion else "Low",
        reason_codes=(
            ["protein_gap_available"] if with_suggestion else ["gap_unavailable"]
        ),
        limitations=[] if with_suggestion else ["No approved suggestion is available."],
    )
    food_suggestions = []
    if with_suggestion:
        food_suggestions.append(
            ApprovedFoodSuggestion(
                canonical_food_id=11,
                display_name="Chicken Breast, Cooked, Skinless",
                suggested_grams=150.0,
                estimated_calories=248.0,
                estimated_protein_g=46.0,
                estimated_carbohydrate_g=0.0,
                estimated_fat_g=5.0,
                macro_gap_addressed="protein_g",
                suggestion_summary="Chicken Breast, Cooked, Skinless can help close the approved protein gap.",
                confidence="High",
                reason_codes=["approved_canonical_food_suggestion"],
                limitations=[],
            )
        )
    return ApprovedNutritionFoodSuggestions(
        user_id=102,
        suggestion_date="2026-06-14",
        primary_gap="protein_g" if with_suggestion else None,
        macro_gaps=[macro_gap],
        suggestions=food_suggestions,
        confidence="High" if with_suggestion else "Low",
        reason_codes=(
            ["protein_gap_available"] if with_suggestion else ["no_suggestion"]
        ),
        limitations=[] if with_suggestion else ["No approved suggestion is available."],
    )


def _evidence(
    summary: TargetVsActualNutritionSummary,
    *,
    with_suggestion: bool = False,
) -> NutritionReportEvidenceContext:
    suggestions = _suggestions(with_suggestion=with_suggestion)
    return NutritionReportEvidenceContext(
        user_id=summary.user_id,
        report_date=summary.date,
        target_vs_actual_summary=summary.to_dict(),
        approved_nutrition_guidance=_guidance(summary).to_dict(),
        approved_food_suggestions=suggestions.to_dict(),
        confidence=summary.confidence,
        reason_codes=["nutrition_provider_validation_test", *summary.reason_codes],
        limitations=[*summary.limitations, *suggestions.limitations],
    )


def test_validator_rejects_unsupported_protein_calorie_claims_and_numbers():
    context = build_nutrition_provider_safe_context(_evidence(_summary_partial()))
    candidate = _candidate(
        target_alignment="Protein appears below target at 35 g and calories appear below the approved range.",
    )

    result = validate_candidate_nutrition_report_section(
        candidate, safe_context=context
    )

    assert result.validation_status == NUTRITION_PROVIDER_VALIDATION_STATUS_REJECTED
    assert any("protein appears below" in error for error in result.validation_errors)
    assert any("calories appear below" in error for error in result.validation_errors)


def test_validator_rejects_confidence_above_backend_ceiling():
    context = build_nutrition_provider_safe_context(_evidence(_summary_partial()))
    candidate = _candidate(confidence="High")

    result = validate_candidate_nutrition_report_section(
        candidate, safe_context=context
    )

    assert result.validation_status == NUTRITION_PROVIDER_VALIDATION_STATUS_REJECTED
    assert any("confidence" in error for error in result.validation_errors)


def test_validator_rejects_unapproved_food_and_serving_claims():
    context = build_nutrition_provider_safe_context(_evidence(_summary_protein_gap()))
    candidate = _candidate(
        confidence="High",
        practical_food_focus="A 200 g salmon serving can help close the approved protein gap.",
    )

    result = validate_candidate_nutrition_report_section(
        candidate, safe_context=context
    )

    assert result.validation_status == NUTRITION_PROVIDER_VALIDATION_STATUS_REJECTED
    assert any("food_suggestion" in error for error in result.validation_errors)
    assert any(
        "numeric_value_not_approved" in error for error in result.validation_errors
    )


def test_validator_accepts_candidate_tied_to_approved_claims_and_food_suggestion():
    context = build_nutrition_provider_safe_context(
        _evidence(_summary_protein_gap(), with_suggestion=True)
    )
    candidate = _candidate(
        section_summary="Nutrition logging is complete enough for cautious target comparison.",
        intake_snapshot="Logged intake includes 1850 calories and 80 g protein.",
        target_alignment="Protein appears below the approved target based on logged entries.",
        logging_quality="Nutrition logging is complete enough for cautious target comparison.",
        practical_food_focus="Chicken Breast, Cooked, Skinless at 150 g can help close the approved protein gap.",
        next_nutrition_action="Use the approved food suggestion or keep logging complete meals.",
        limitations_context="This section stays tied to approved comparisons and canonical food suggestions.",
        confidence="High",
    )

    result = validate_candidate_nutrition_report_section(
        candidate, safe_context=context
    )

    assert result.validation_status == NUTRITION_PROVIDER_VALIDATION_STATUS_APPROVED
    assert result.valid is True


def test_provider_safe_context_lists_only_exact_approved_numeric_values():
    context = build_nutrition_provider_safe_context(
        _evidence(_summary_protein_gap(), with_suggestion=True)
    )

    assert 80.0 in context.approved_numeric_values
    assert 120.0 in context.approved_numeric_values
    assert 150.0 in context.approved_numeric_values
    assert 1850.0 in context.approved_numeric_values
    assert 40.0 not in context.approved_numeric_values


def test_validator_rejects_model_inferred_numeric_gap_not_explicitly_approved():
    context = build_nutrition_provider_safe_context(
        _evidence(_summary_protein_gap(), with_suggestion=True)
    )
    candidate = _candidate(
        section_summary="Nutrition logging is complete enough for cautious target comparison.",
        intake_snapshot="Logged intake includes 1850 calories and 80 g protein.",
        target_alignment="Protein appears below the approved target with a 40 g gap.",
        logging_quality="Nutrition logging is complete enough for cautious guidance.",
        practical_food_focus="Chicken Breast, Cooked, Skinless at 150 g can help close the approved protein gap.",
        next_nutrition_action="Use the approved food suggestion or keep logging complete meals.",
        limitations_context="This section stays tied to approved comparisons and canonical food suggestions.",
        confidence="High",
    )

    result = validate_candidate_nutrition_report_section(
        candidate, safe_context=context
    )

    assert result.validation_status == NUTRITION_PROVIDER_VALIDATION_STATUS_REJECTED
    assert result.valid is False
    assert any(
        "numeric_value_not_approved_by_evidence: 40" in error
        for error in result.validation_errors
    )
