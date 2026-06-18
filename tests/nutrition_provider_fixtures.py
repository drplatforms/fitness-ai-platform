from __future__ import annotations

import json

from models.nutrition_food_suggestion_models import (
    ApprovedFoodSuggestion,
    ApprovedNutritionFoodSuggestions,
    NutritionMacroGap,
)
from models.nutrition_report_section_models import NutritionReportEvidenceContext
from models.nutrition_target_vs_actual_models import (
    ApprovedNutritionGuidance,
    NutritionActuals,
    NutritionLoggingSummary,
    NutritionTargetComparison,
    TargetVsActualNutritionSummary,
)


def build_complete_nutrition_provider_evidence() -> NutritionReportEvidenceContext:
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
    summary = TargetVsActualNutritionSummary(
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
    guidance = ApprovedNutritionGuidance(
        user_id=102,
        date="2026-06-14",
        summary_message="Nutrition evidence should stay tied to approved targets and logs.",
        protein_guidance="Protein appears below the approved target based on logged entries.",
        calorie_guidance="Calories appear near the approved range based on complete-enough logs.",
        macro_guidance="Macro conclusions should stay bounded to approved comparisons.",
        logging_guidance="Logged intake is complete enough for cautious guidance.",
        confidence="High",
        reason_codes=["approved_guidance"],
        limitations=[],
    )
    macro_gap = NutritionMacroGap(
        macro_name="protein_g",
        target_value=120.0,
        actual_value=80.0,
        gap_value=40.0,
        unit="g",
        target_status="below_target",
        display_allowed=True,
        confidence="High",
        reason_codes=["protein_gap_available"],
        limitations=[],
    )
    suggestions = ApprovedNutritionFoodSuggestions(
        user_id=102,
        suggestion_date="2026-06-14",
        primary_gap="protein_g",
        macro_gaps=[macro_gap],
        suggestions=[
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
        ],
        confidence="High",
        reason_codes=["approved_food_suggestion_available"],
        limitations=[],
    )
    return NutritionReportEvidenceContext(
        user_id=102,
        report_date="2026-06-14",
        target_vs_actual_summary=summary.to_dict(),
        approved_nutrition_guidance=guidance.to_dict(),
        approved_food_suggestions=suggestions.to_dict(),
        confidence="High",
        reason_codes=["nutrition_provider_test_fixture", *summary.reason_codes],
        limitations=[],
    )


def valid_provider_candidate_json(**overrides) -> str:
    payload = {
        "section_summary": "Nutrition logging is complete enough for cautious target comparison.",
        "intake_snapshot": "Logged intake includes 80 g protein and 1850 calories for this report date.",
        "target_alignment": "Protein appears below the approved target, while calories appear near the approved range.",
        "logging_quality": "Logging is complete enough for cautious nutrition guidance.",
        "practical_food_focus": "Approved food suggestion Chicken Breast, Cooked, Skinless can help close the approved protein gap with 150 g.",
        "next_nutrition_action": "Use the approved food suggestion or log another complete day before changing targets.",
        "limitations_context": "This section is limited to approved logged intake, approved targets, and approved food suggestions.",
        "confidence": "High",
        "reason_codes": ["valid_fake_nutrition_provider_candidate"],
    }
    payload.update(overrides)
    return json.dumps(payload)
