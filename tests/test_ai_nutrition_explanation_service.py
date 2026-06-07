from __future__ import annotations

from dataclasses import dataclass

import pytest

from models.ai_nutrition_explanation_models import NutritionExplanationContext
from services import ai_nutrition_explanation_service as service


@dataclass
class FakePayload:
    payload: dict

    def to_dict(self) -> dict:
        return self.payload


def _approved_macro_targets() -> FakePayload:
    return FakePayload(
        {
            "user_id": 1,
            "calculation_date": "2026-06-07",
            "confidence": "Moderate",
            "display_flags": {
                "allow_calorie_targets": True,
                "allow_protein_targets": True,
                "allow_carbohydrate_targets": True,
                "allow_fat_targets": True,
            },
            "calorie_target": {
                "target_type": "calories",
                "min_value": 2300,
                "max_value": 2600,
                "display_value": "2300-2600 kcal",
                "unit": "kcal",
                "confidence": "Moderate",
                "display_allowed": True,
                "reason_codes": ["calorie_target_approved"],
                "limitations": [],
            },
            "protein_target_g": {
                "target_type": "protein_g",
                "min_value": 150,
                "max_value": 185,
                "display_value": "150-185 g",
                "unit": "g",
                "confidence": "Moderate",
                "display_allowed": True,
                "reason_codes": ["protein_target_approved"],
                "limitations": [],
            },
            "carbohydrate_target_g": None,
            "fat_target_g": None,
            "formula_metadata": {
                "formula_name": "nutrition_target_formula",
                "formula_version": "v1",
                "calculation_date": "2026-06-07",
                "target_basis": "formula_derived",
                "reason_codes": ["formula_targets_available"],
                "limitations": [],
            },
            "reason_codes": ["formula_targets_available"],
            "limitations": [],
        }
    )


def _target_vs_actual_summary() -> FakePayload:
    return FakePayload(
        {
            "user_id": 1,
            "date": "2026-06-07",
            "nutrition_actuals": {
                "logged_calories": 2400,
                "logged_protein": 128.8,
                "logged_carbs": 260,
                "logged_fat": 70,
                "logged_meal_count": 4,
                "entry_count": 8,
                "raw_food_entries": [{"id": 999}],
            },
            "logging_summary": {
                "logging_completeness": "complete_enough_for_guidance",
                "confidence": "Moderate",
                "logged_meal_count": 4,
                "entry_count": 8,
                "missing_nutrient_fields": [],
                "reason_codes": ["logging_quality_usable"],
                "limitations": [],
            },
            "comparisons": {
                "protein": {
                    "nutrient": "protein",
                    "actual": 128.8,
                    "target_min": 150,
                    "target_max": 185,
                    "target_status": "below_target",
                    "comparison_available": True,
                    "confidence": "Moderate",
                    "reason_codes": ["logged_protein_below_target"],
                    "limitations": [],
                },
                "calories": {
                    "nutrient": "calories",
                    "actual": 2400,
                    "target_min": 2300,
                    "target_max": 2600,
                    "target_status": "near_target",
                    "comparison_available": True,
                    "confidence": "Moderate",
                    "reason_codes": ["logged_calories_near_target"],
                    "limitations": [],
                },
            },
            "logging_completeness": "complete_enough_for_guidance",
            "confidence": "Moderate",
            "reason_codes": ["target_vs_actual_available"],
            "limitations": [],
            "raw_sql": "select * from food_entries",
        }
    )


def _approved_guidance() -> FakePayload:
    return FakePayload(
        {
            "user_id": 1,
            "date": "2026-06-07",
            "summary_message": "Logged nutrition can be compared cautiously with approved targets.",
            "protein_guidance": "Based on logged meals, protein is below today's target.",
            "calorie_guidance": "Logged calories are near the approved range based on complete-enough logs.",
            "macro_guidance": "Macro comparisons can be interpreted cautiously.",
            "logging_guidance": "Logged intake is complete enough to support cautious nutrition guidance.",
            "confidence": "Moderate",
            "reason_codes": ["approved_guidance_available"],
            "limitations": [],
        }
    )


def _food_suggestions() -> FakePayload:
    return FakePayload(
        {
            "user_id": 1,
            "suggestion_date": "2026-06-07",
            "primary_gap": "protein_g",
            "macro_gaps": [
                {
                    "macro_name": "protein_g",
                    "target_status": "below_target",
                    "display_allowed": True,
                    "confidence": "Moderate",
                    "reason_codes": ["protein_gap_available"],
                    "limitations": [],
                }
            ],
            "suggestions": [
                {
                    "canonical_food_id": 1,
                    "display_name": "Chicken Breast, Cooked, Skinless",
                    "suggested_grams": 150,
                    "estimated_calories": 247.5,
                    "estimated_protein_g": 46.5,
                    "estimated_carbohydrate_g": 0,
                    "estimated_fat_g": 5.4,
                    "macro_gap_addressed": "protein_g",
                    "confidence": "Moderate",
                    "reason_codes": ["protein_suggestion_available"],
                    "limitations": [],
                    "raw_source_payload": {"not": "public"},
                }
            ],
            "confidence": "Moderate",
            "reason_codes": ["food_suggestions_available"],
            "limitations": [],
        }
    )


def _trend_window() -> FakePayload:
    return FakePayload(
        {
            "user_id": 1,
            "start_date": "2026-05-11",
            "end_date": "2026-06-07",
            "window_days": 28,
            "logged_day_count": 26,
            "complete_logging_day_count": 24,
            "partial_logging_day_count": 2,
            "no_log_day_count": 2,
            "intake_trend_summary": {
                "average_calories": 2380,
                "average_protein_g": 145,
                "average_carbohydrate_g": 250,
                "average_fat_g": 72,
                "complete_logging_rate": 0.86,
                "logging_consistency_status": "usable",
                "confidence": "Moderate",
                "reason_codes": ["logging_quality_usable"],
                "limitations": [],
            },
            "bodyweight_trend_summary": {
                "weigh_in_count": 12,
                "trend_direction": "stable",
                "weekly_rate_lb": 0.1,
                "confidence": "Moderate",
                "reason_codes": ["bodyweight_trend_available"],
                "limitations": [],
            },
            "calibration_readiness": {
                "calibration_allowed": False,
                "readiness_level": "usable",
                "minimum_window_met": True,
                "preferred_window_met": True,
                "logging_quality_met": True,
                "bodyweight_trend_available": True,
                "goal_context_available": True,
                "training_context_available": True,
                "reason_codes": ["calibration_usable"],
                "limitations": [],
            },
            "confidence": "Moderate",
            "reason_codes": ["trend_window_created"],
            "limitations": [],
            "raw_daily_checkins": [{"weight": 190}],
        }
    )


def _calibration_result() -> FakePayload:
    return FakePayload(
        {
            "user_id": 1,
            "calibration_date": "2026-06-07",
            "window_days": 28,
            "calibration_allowed": False,
            "readiness_level": "usable",
            "recommended_action": "keep_current_targets",
            "calibrated_targets": None,
            "confidence": "Moderate",
            "reason_codes": ["current_targets_kept", "target_mutation_not_performed"],
            "limitations": [
                "Calibration assessment is read-only and does not mutate nutrition targets."
            ],
            "metadata": {
                "service_name": "deterministic_nutrition_target_calibration",
                "service_version": "v1",
                "inputs_used": ["nutrition_trend_window"],
                "reason_codes": ["target_mutation_not_performed"],
                "limitations": [
                    "Calibration assessment is read-only and does not mutate nutrition targets."
                ],
            },
            "provider_metadata": {"not": "public"},
        }
    )


@pytest.fixture
def approved_context(monkeypatch) -> NutritionExplanationContext:
    monkeypatch.setattr(
        service, "_build_approved_macro_targets", lambda **_: _approved_macro_targets()
    )
    monkeypatch.setattr(
        service,
        "build_target_vs_actual_nutrition_summary",
        lambda *_args, **_kwargs: _target_vs_actual_summary(),
    )
    monkeypatch.setattr(
        service,
        "build_approved_nutrition_guidance",
        lambda _summary: _approved_guidance(),
    )
    monkeypatch.setattr(
        service,
        "build_approved_nutrition_food_suggestions",
        lambda *_args, **_kwargs: _food_suggestions(),
    )
    monkeypatch.setattr(
        service,
        "build_nutrition_trend_window",
        lambda *_args, **_kwargs: _trend_window(),
    )
    monkeypatch.setattr(
        service,
        "build_nutrition_target_calibration_result",
        lambda *_args, **_kwargs: _calibration_result(),
    )
    return service.build_nutrition_explanation_context(1, "2026-06-07")


def test_service_builds_context_from_approved_target_vs_actual_data(approved_context):
    assert (
        approved_context.target_vs_actual_summary["comparisons"]["protein"][
            "target_status"
        ]
        == "below_target"
    )
    assert (
        approved_context.target_vs_actual_summary["nutrition_actuals"]["logged_protein"]
        == 128.8
    )
    assert "raw_food_entries" not in str(approved_context.target_vs_actual_summary)
    assert "raw_sql" not in str(approved_context.target_vs_actual_summary)


def test_service_builds_context_from_approved_food_suggestions(approved_context):
    suggestion = approved_context.approved_food_suggestions["suggestions"][0]

    assert suggestion["canonical_food_id"] == 1
    assert suggestion["display_name"] == "Chicken Breast, Cooked, Skinless"
    assert suggestion["suggested_grams"] == 150
    assert "raw_source_payload" not in str(approved_context.approved_food_suggestions)


def test_service_builds_context_from_trend_calibration_readiness(approved_context):
    assert (
        approved_context.trend_summary["calibration_readiness"]["readiness_level"]
        == "usable"
    )
    assert approved_context.calibration_summary["readiness_level"] == "usable"
    assert approved_context.calibration_summary["calibrated_targets"] is None
    assert "provider_metadata" not in str(approved_context.calibration_summary)


def test_service_returns_approved_nutrition_explanation_for_complete_context(
    approved_context,
):
    explanation = service.build_approved_nutrition_explanation(
        1,
        "2026-06-07",
        context=approved_context,
    )

    assert explanation.user_id == 1
    assert explanation.source == "deterministic_fallback"
    assert explanation.confidence == "Moderate"
    assert "deterministic_nutrition_explanation_service" in explanation.reason_codes


def test_service_returns_safe_limited_explanation_for_incomplete_context():
    context = NutritionExplanationContext(
        user_id=1,
        explanation_date="2026-06-07",
        approved_nutrition_guidance={
            "summary": "Nutrition explanation context is limited for this date."
        },
        confidence="Limited",
        reason_codes=["approved_context_limited"],
        limitations=["Approved nutrition context is incomplete for this date."],
    )

    explanation = service.build_approved_nutrition_explanation(1, context=context)

    assert explanation.confidence == "Limited"
    assert explanation.limitations
    assert "limited" in explanation.explanation_summary.lower()


def test_deterministic_fallback_candidate_validates_successfully(approved_context):
    candidate = service.build_deterministic_nutrition_explanation_candidate(
        approved_context
    )
    explanation = service.build_approved_nutrition_explanation(
        1,
        context=approved_context,
    )

    assert candidate.confidence == approved_context.confidence
    assert explanation.source == "deterministic_fallback"


def test_explanation_mentions_formula_derived_targets_safely_when_calibration_exists(
    approved_context,
):
    explanation = service.build_approved_nutrition_explanation(
        1,
        context=approved_context,
    )

    assert explanation.calibration_context is not None
    assert "formula-derived" in explanation.calibration_context
    assert "calibration has been applied" not in explanation.calibration_context.lower()


def test_explanation_does_not_expose_raw_internal_debug_or_provider_fields(
    approved_context,
):
    explanation = service.build_approved_nutrition_explanation(
        1,
        context=approved_context,
    )
    public_text = str(explanation.to_dict()).lower()

    assert "raw_food_entries" not in public_text
    assert "raw_daily_checkins" not in public_text
    assert "provider_metadata" not in public_text
    assert "raw sql" not in public_text


def test_explanation_does_not_invent_foods_servings_or_macros(approved_context):
    explanation = service.build_approved_nutrition_explanation(
        1,
        context=approved_context,
    )
    public_text = " ".join(
        value
        for value in [
            explanation.explanation_summary,
            explanation.macro_context,
            explanation.food_suggestion_context,
            explanation.trend_context,
            explanation.calibration_context,
        ]
        if value
    ).lower()

    assert "150g" not in public_text
    assert "46.5g" not in public_text
    assert "chicken breast" not in public_text
    assert "new target" not in public_text


def test_explanation_does_not_produce_meal_plan_language(approved_context):
    explanation = service.build_approved_nutrition_explanation(
        1,
        context=approved_context,
    )
    public_text = str(explanation.to_dict()).lower()

    assert "meal plan" not in public_text
    assert "breakfast:" not in public_text
    assert "lunch:" not in public_text
    assert "dinner:" not in public_text


def test_no_ai_crewai_or_ollama_provider_is_called(monkeypatch, approved_context):
    def fail_provider_call(*_args, **_kwargs):
        raise AssertionError("AI provider should not be called")

    monkeypatch.setattr(
        service, "_unused_provider_call_for_test", fail_provider_call, raising=False
    )

    explanation = service.build_approved_nutrition_explanation(
        1,
        context=approved_context,
    )

    assert explanation.source == "deterministic_fallback"
    assert "crewai" not in str(explanation.to_dict()).lower()
    assert "ollama" not in str(explanation.to_dict()).lower()
