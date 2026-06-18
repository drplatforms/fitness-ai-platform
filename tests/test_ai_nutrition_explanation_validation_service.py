from __future__ import annotations

import pytest

from models.ai_nutrition_explanation_models import (
    CandidateNutritionExplanation,
    NutritionExplanationContext,
)
from services.ai_nutrition_explanation_validation_service import (
    approve_nutrition_explanation_candidate,
    build_deterministic_fallback_nutrition_explanation,
    collect_nutrition_explanation_validation_errors,
    validate_candidate_nutrition_explanation,
)


def _context(
    *,
    confidence: str = "Moderate",
    limitations: list[str] | None = None,
) -> NutritionExplanationContext:
    return NutritionExplanationContext(
        user_id=1,
        explanation_date="2026-06-07",
        approved_macro_targets={
            "confidence": "Moderate",
            "display_flags": {
                "allow_calorie_targets": True,
                "allow_protein_targets": True,
            },
            "protein_target_g": {
                "target_min": 150,
                "target_max": 185,
                "display_value": "150-185 g",
            },
            "calorie_target": {"target_min": 2300, "target_max": 2600},
        },
        target_vs_actual_summary={
            "confidence": "Moderate",
            "logging_completeness": "reasonably_complete",
            "comparisons": {
                "protein": {
                    "target_status": "below_target",
                    "actual_value": 128.8,
                    "unit": "g",
                },
                "calories": {
                    "target_status": "near_target",
                    "actual_value": 2400,
                    "unit": "kcal",
                },
            },
        },
        approved_nutrition_guidance={
            "summary": "Protein is below target based on logged meals."
        },
        approved_food_suggestions={
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
                }
            ]
        },
        trend_summary={
            "readiness_level": "early_signal",
            "window_days": 14,
        },
        calibration_summary={
            "readiness_level": "not_ready",
            "recommended_action": "insufficient_data",
        },
        confidence=confidence,
        reason_codes=["approved_context_available"],
        limitations=limitations or [],
        display_flags={"allow_protein_targets": True},
    )


def _candidate(**overrides: object) -> CandidateNutritionExplanation:
    values = {
        "explanation_summary": "Based on today’s logged meals, protein is below target.",
        "macro_context": "Protein is below target based on logged meals.",
        "food_suggestion_context": (
            "Chicken Breast, Cooked, Skinless is an approved food option; "
            "150 g is the backend-approved serving context."
        ),
        "trend_context": "Early trend evidence is available, but more data is needed.",
        "calibration_context": "Targets are still formula-derived.",
        "limitations_context": "Calibration is not ready yet because more consistent logs or weigh-ins are needed.",
        "confidence": "Moderate",
        "reason_codes": ["candidate_generated"],
    }
    values.update(overrides)
    return CandidateNutritionExplanation(**values)  # type: ignore[arg-type]


def test_safe_target_vs_actual_explanation_passes():
    candidate = _candidate(
        explanation_summary="Based on today’s logged meals, protein is below target.",
        macro_context="Protein is below target based on logged meals.",
    )

    assert validate_candidate_nutrition_explanation(_context(), candidate) is candidate


def test_safe_food_suggestion_explanation_passes():
    candidate = _candidate(
        food_suggestion_context=(
            "Chicken Breast, Cooked, Skinless is an approved food option; "
            "150 g is the backend-approved serving context."
        )
    )

    approved = approve_nutrition_explanation_candidate(_context(), candidate)

    assert approved.source == "ai_validated"
    assert "ai_nutrition_explanation_validated" in approved.reason_codes
    assert "Chicken Breast, Cooked, Skinless" in approved.food_suggestion_context


def test_safe_food_suggestion_with_approved_food_serving_and_macro_values_passes():
    candidate = _candidate(
        food_suggestion_context=(
            "A 150 g serving of Chicken Breast, Cooked, Skinless would add "
            "about 46.5 g protein."
        )
    )

    approved = approve_nutrition_explanation_candidate(_context(), candidate)

    assert "150 g" in approved.food_suggestion_context
    assert "46.5 g protein" in approved.food_suggestion_context


def test_safe_trend_calibration_readiness_explanation_passes():
    candidate = _candidate(
        trend_context="Early trend evidence is available, but more data is needed.",
        calibration_context="Targets are still formula-derived.",
    )

    assert validate_candidate_nutrition_explanation(_context(), candidate) is candidate


def test_deterministic_fallback_style_explanation_passes():
    context = _context(
        confidence="Limited",
        limitations=["Approved context is limited for this date."],
    )

    fallback = build_deterministic_fallback_nutrition_explanation(context)

    assert fallback.source == "deterministic_fallback"
    assert fallback.confidence == "Limited"
    assert "deterministic_nutrition_explanation_fallback" in fallback.reason_codes


@pytest.mark.parametrize(
    ("unsafe_summary", "expected_error"),
    [
        ("Your protein target is 200g now.", "invented_macro_target_detected"),
        ("You logged 999g protein today.", "unapproved_nutrition_number_detected"),
        (
            "Try 200g chicken breast to hit the gap.",
            "unapproved_nutrition_number_detected",
        ),
        (
            "Salmon would be a better option for this gap.",
            "unapproved_food_mention_detected",
        ),
        (
            "Your true maintenance is exactly 2400 calories.",
            "exact_maintenance_claim_detected",
        ),
        ("Your targets have been changed.", "target_change_language_detected"),
        ("Calibration has been applied.", "target_change_language_detected"),
        ("Calibrated targets are active.", "target_change_language_detected"),
        (
            "Here is a meal plan: chicken for breakfast and rice for dinner.",
            "meal_plan_language_detected",
        ),
        (
            "You failed, so you must cut calories tomorrow.",
            "shame_or_restriction_language_detected",
        ),
        ("Burn this off tomorrow.", "shame_or_restriction_language_detected"),
        (
            "This supplement guarantees fat loss.",
            "medical_supplement_or_fat_loss_claim_detected",
        ),
    ],
)
def test_unsafe_candidates_are_rejected(unsafe_summary, expected_error):
    candidate = _candidate(explanation_summary=unsafe_summary)

    errors = collect_nutrition_explanation_validation_errors(_context(), candidate)

    assert expected_error in errors
    with pytest.raises(ValueError, match="failed validation"):
        validate_candidate_nutrition_explanation(_context(), candidate)


def test_candidate_with_raw_or_internal_payload_language_is_rejected():
    candidate = _candidate(
        explanation_summary="Raw food entries show protein is below target."
    )

    errors = collect_nutrition_explanation_validation_errors(_context(), candidate)

    assert "raw_or_internal_details_detected" in errors


def test_candidate_requires_approved_context():
    context = NutritionExplanationContext(
        user_id=1,
        explanation_date="2026-06-07",
        confidence="Limited",
        limitations=["No approved nutrition explanation context is available."],
    )
    candidate = _candidate()

    errors = collect_nutrition_explanation_validation_errors(context, candidate)

    assert "approved_context_required" in errors


def test_validation_errors_remain_debug_only_and_not_public_explanation_text():
    candidate = _candidate(explanation_summary="Your targets have been changed.")
    errors = collect_nutrition_explanation_validation_errors(_context(), candidate)

    assert errors
    assert all("Your targets" not in error for error in errors)


def test_runtime_metadata_from_validation_result_is_debug_only():
    candidate = _candidate(explanation_summary="Your targets have been changed.")
    errors = collect_nutrition_explanation_validation_errors(_context(), candidate)

    from services.ai_nutrition_explanation_validation_service import (  # noqa: PLC0415
        NutritionExplanationValidationResult,
    )

    result = NutritionExplanationValidationResult(valid=False, validation_errors=errors)
    metadata = result.to_debug_metadata(provider="fake_provider")

    assert metadata.to_debug_dict()["provider"] == "fake_provider"
    assert metadata.to_debug_dict()["validation_status"] == "rejected"


def test_approved_output_does_not_include_runtime_metadata():
    approved = approve_nutrition_explanation_candidate(_context(), _candidate())
    payload = approved.to_dict()

    assert "provider" not in payload
    assert "raw_output_preview_truncated" not in payload
    assert payload["source"] == "ai_validated"


def test_low_confidence_candidate_preserves_limitation_compatibility():
    context = _context(
        confidence="Low",
        limitations=["Logging context is incomplete for this date."],
    )
    candidate = _candidate(confidence="Low")

    approved = approve_nutrition_explanation_candidate(context, candidate)

    assert approved.confidence == "Low"
    assert approved.limitations == ["Logging context is incomplete for this date."]


def test_validation_deduplicates_repeated_errors():
    candidate = _candidate(
        explanation_summary="Your targets have been changed. Your targets have been changed."
    )

    errors = collect_nutrition_explanation_validation_errors(_context(), candidate)

    assert errors.count("target_change_language_detected") == 1
