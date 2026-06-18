from __future__ import annotations

from models.nutrition_food_suggestion_models import (
    ApprovedNutritionFoodSuggestions,
    NutritionMacroGap,
)
from models.nutrition_provider_contract_models import (
    NUTRITION_PROVIDER_FALLBACK_REASON_PARSE_FAILED,
    NUTRITION_PROVIDER_PARSE_STATUS_SCHEMA_INVALID,
    NUTRITION_PROVIDER_SAFE_METADATA_ALLOWLIST,
    NutritionProviderCandidateParseResult,
)
from models.nutrition_report_section_models import NutritionReportEvidenceContext
from models.nutrition_target_vs_actual_models import (
    ApprovedNutritionGuidance,
    NutritionActuals,
    NutritionLoggingSummary,
    NutritionTargetComparison,
    TargetVsActualNutritionSummary,
)
from services.full_report_section_registry_service import (
    get_provider_integrated_full_report_section_ids,
)
from services.nutrition_provider_validation_service import (
    build_nutrition_provider_contract_fallback_result,
    build_nutrition_provider_safe_context,
)


def _evidence() -> NutritionReportEvidenceContext:
    actuals = NutritionActuals(
        user_id=102,
        logging_date="2026-06-14",
        logging_window="daily",
        logged_calories=None,
        logged_protein=None,
        logged_carbs=None,
        logged_fat=None,
        logged_fiber=None,
        logged_meal_count=0,
        entry_count=0,
        source_count=0,
        reason_codes=["no_logs"],
    )
    logging = NutritionLoggingSummary(
        user_id=102,
        logging_date="2026-06-14",
        logging_completeness="no_logs",
        confidence="Limited",
        logged_meal_count=0,
        entry_count=0,
        reason_codes=["no_logs"],
        limitations=["No nutrition logs were found for this date."],
    )
    comparisons = {
        "protein": NutritionTargetComparison(
            nutrient="protein",
            actual=None,
            target_min=None,
            target_max=None,
            delta_min=None,
            delta_max=None,
            percent_of_target=None,
            target_status="unavailable",
            comparison_available=False,
            confidence="Limited",
            reason_codes=["protein_unavailable"],
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
            confidence="Limited",
            reason_codes=["calories_unavailable"],
            limitations=["Calorie comparison is unavailable."],
        ),
    }
    summary = TargetVsActualNutritionSummary(
        user_id=102,
        date="2026-06-14",
        nutrition_actuals=actuals,
        logging_summary=logging,
        comparisons=comparisons,
        logging_completeness="no_logs",
        confidence="Limited",
        reason_codes=["no_nutrition_logs"],
        limitations=["No nutrition logs were found for this date."],
    )
    guidance = ApprovedNutritionGuidance(
        user_id=102,
        date="2026-06-14",
        summary_message="Nutrition logging is unavailable, so conclusions should stay limited.",
        protein_guidance="Protein comparison is limited until approved targets and logged protein are available.",
        calorie_guidance="Calorie comparison is limited until approved targets and logged calories are available.",
        macro_guidance="Macro comparisons are limited until logging is available.",
        logging_guidance="Log a complete day before changing nutrition targets.",
        confidence="Limited",
        reason_codes=["limited_guidance"],
        limitations=["No nutrition logs were found for this date."],
    )
    suggestions = ApprovedNutritionFoodSuggestions(
        user_id=102,
        suggestion_date="2026-06-14",
        primary_gap=None,
        macro_gaps=[
            NutritionMacroGap(
                macro_name="protein_g",
                target_value=None,
                actual_value=None,
                gap_value=None,
                unit="g",
                target_status="unavailable",
                display_allowed=False,
                confidence="Limited",
                reason_codes=["target_unavailable"],
                limitations=["No approved suggestion is available."],
            )
        ],
        suggestions=[],
        confidence="Limited",
        reason_codes=["no_suggestions"],
        limitations=["No approved suggestion is available."],
    )
    return NutritionReportEvidenceContext(
        user_id=102,
        report_date="2026-06-14",
        target_vs_actual_summary=summary.to_dict(),
        approved_nutrition_guidance=guidance.to_dict(),
        approved_food_suggestions=suggestions.to_dict(),
        confidence="Limited",
        reason_codes=["nutrition_provider_fallback_test"],
        limitations=[
            "No nutrition logs were found for this date.",
            "No approved suggestion is available.",
        ],
    )


def test_fallback_result_uses_deterministic_section_and_safe_metadata_only():
    evidence = _evidence()
    safe_context = build_nutrition_provider_safe_context(evidence)
    parse_result = NutritionProviderCandidateParseResult(
        parse_status=NUTRITION_PROVIDER_PARSE_STATUS_SCHEMA_INVALID,
        parse_errors=["missing_keys: section_summary"],
    )

    result = build_nutrition_provider_contract_fallback_result(
        evidence,
        safe_context=safe_context,
        parse_result=parse_result,
        fallback_reason=NUTRITION_PROVIDER_FALLBACK_REASON_PARSE_FAILED,
    )

    assert result.fallback_used is True
    assert result.section.section_id == "nutrition_report_section"
    assert result.section.source.endswith("fallback")
    assert set(result.safe_metadata).issubset(
        NUTRITION_PROVIDER_SAFE_METADATA_ALLOWLIST
    )
    assert result.safe_metadata["nutrition_provider_execution_enabled"] is False
    assert result.safe_metadata["provider_attempted"] is False
    assert result.safe_metadata["selected_provider"] is None
    assert result.safe_metadata["fallback_used"] is True
    assert "parse_errors" not in result.safe_metadata
    assert "raw_output" not in result.safe_metadata


def test_nutrition_level_5_promotion_preserves_provider_integration_registry():
    assert get_provider_integrated_full_report_section_ids() == [
        "nutrition_report_section",
        "training",
    ]
