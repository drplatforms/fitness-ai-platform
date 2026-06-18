import pytest

from models.ai_nutrition_explanation_models import (
    ApprovedNutritionExplanation,
    CandidateNutritionExplanation,
    NutritionExplanationContext,
    NutritionExplanationRuntimeMetadata,
)


def _context() -> NutritionExplanationContext:
    return NutritionExplanationContext(
        user_id=1,
        explanation_date="2026-06-07",
        approved_macro_targets={
            "confidence": "Moderate",
            "display_flags": {"allow_protein_targets": True},
            "protein_target_g": {"display_value": "150-185 g"},
        },
        target_vs_actual_summary={
            "confidence": "Moderate",
            "comparisons": {
                "protein": {
                    "target_status": "below_target",
                    "actual_value": 128.8,
                    "unit": "g",
                }
            },
        },
        approved_nutrition_guidance={
            "summary": "Protein is below target based on logged meals."
        },
        approved_food_suggestions={
            "suggestions": [
                {
                    "display_name": "Chicken Breast, Cooked, Skinless",
                    "macro_gap_addressed": "protein_g",
                }
            ]
        },
        trend_summary={"readiness_level": "early_signal"},
        calibration_summary={
            "readiness_level": "not_ready",
            "recommended_action": "insufficient_data",
        },
        confidence="Moderate",
        reason_codes=["approved_context_available"],
        display_flags={"allow_protein_targets": True},
    )


def _approved_explanation() -> ApprovedNutritionExplanation:
    return ApprovedNutritionExplanation(
        user_id=1,
        explanation_date="2026-06-07",
        explanation_summary="Based on today’s logged meals, protein is below target.",
        macro_context="Protein is below target based on logged meals.",
        food_suggestion_context=(
            "The Nutrition tab has approved food suggestions that may help close the gap."
        ),
        trend_context="Early trend evidence is available, but more data is needed.",
        calibration_context="Targets are still formula-derived.",
        limitations_context="Calibration is not ready yet because more consistent logs are needed.",
        confidence="Moderate",
        reason_codes=["ai_nutrition_explanation_approved"],
        source="ai_validated",
    )


def test_nutrition_explanation_context_represents_approved_target_vs_actual_context():
    context = _context()

    assert context.user_id == 1
    assert (
        context.target_vs_actual_summary["comparisons"]["protein"]["target_status"]
        == "below_target"
    )
    assert (
        context.approved_macro_targets["display_flags"]["allow_protein_targets"] is True
    )


def test_nutrition_explanation_context_represents_approved_food_suggestion_context():
    context = _context()

    suggestion = context.approved_food_suggestions["suggestions"][0]
    assert suggestion["display_name"] == "Chicken Breast, Cooked, Skinless"
    assert suggestion["macro_gap_addressed"] == "protein_g"


def test_nutrition_explanation_context_represents_trend_calibration_readiness_context():
    context = _context()

    assert context.trend_summary["readiness_level"] == "early_signal"
    assert context.calibration_summary["readiness_level"] == "not_ready"


def test_context_rejects_raw_or_internal_payload_keys():
    with pytest.raises(ValueError, match="raw or internal context"):
        NutritionExplanationContext(
            user_id=1,
            explanation_date="2026-06-07",
            target_vs_actual_summary={"raw_food_entries": [{"id": 1}]},
            confidence="Moderate",
        )


def test_candidate_nutrition_explanation_represents_provider_candidate_text():
    candidate = CandidateNutritionExplanation(
        explanation_summary="Protein is below target based on logged meals.",
        macro_context="Protein is below target.",
        food_suggestion_context="Approved food suggestions are available.",
        trend_context="Trend evidence is early.",
        calibration_context="Targets are still formula-derived.",
        limitations_context="Logging limitations may apply.",
        confidence="Moderate",
        reason_codes=["candidate_generated"],
    )

    assert candidate.explanation_summary.startswith("Protein")
    assert candidate.confidence == "Moderate"


def test_approved_nutrition_explanation_represents_validated_public_safe_text():
    explanation = _approved_explanation()

    assert explanation.user_id == 1
    assert explanation.source == "ai_validated"
    assert "formula-derived" in explanation.calibration_context


def test_approved_explanation_supports_deterministic_fallback_style_output():
    explanation = ApprovedNutritionExplanation(
        user_id=1,
        explanation_date="2026-06-07",
        explanation_summary=(
            "Nutrition guidance is limited because logging appears incomplete for this date."
        ),
        limitations_context="Use the Nutrition tab for approved target and logging detail.",
        confidence="Limited",
        limitations=["Logging appears incomplete."],
        source="deterministic_fallback",
    )

    assert explanation.source == "deterministic_fallback"
    assert explanation.confidence == "Limited"


@pytest.mark.parametrize("confidence", ["Limited", "Low", "Moderate", "High"])
def test_confidence_values_are_preserved_and_validated(confidence):
    limitations = (
        ["Explanation confidence is limited."]
        if confidence in {"Limited", "Low"}
        else []
    )
    explanation = ApprovedNutritionExplanation(
        user_id=1,
        explanation_date="2026-06-07",
        explanation_summary="Targets are still formula-derived.",
        confidence=confidence,
        limitations=limitations,
    )

    assert explanation.confidence == confidence


def test_invalid_confidence_value_is_rejected():
    with pytest.raises(ValueError, match="Invalid confidence"):
        ApprovedNutritionExplanation(
            user_id=1,
            explanation_date="2026-06-07",
            explanation_summary="Targets are still formula-derived.",
            confidence="Certain",
        )


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "Your true maintenance is exactly 2400 calories.",
        "Your targets have been changed.",
        "Calibration has been applied.",
        "You failed your target.",
        "You must cut calories.",
        "Burn this off tomorrow.",
        "Compensate tomorrow.",
        "Here is a meal plan: eat these foods.",
    ],
)
def test_forbidden_nutrition_medical_calibration_language_is_rejected_from_public_fields(
    unsafe_text,
):
    with pytest.raises(ValueError, match="Forbidden AI nutrition explanation language"):
        ApprovedNutritionExplanation(
            user_id=1,
            explanation_date="2026-06-07",
            explanation_summary=unsafe_text,
            confidence="Moderate",
        )


def test_context_rejects_forbidden_public_context_language():
    with pytest.raises(ValueError, match="forbidden language"):
        NutritionExplanationContext(
            user_id=1,
            explanation_date="2026-06-07",
            calibration_summary={"summary": "Calibration has been applied."},
            confidence="Moderate",
        )


def test_runtime_metadata_is_debug_only_and_separate_from_approved_output():
    metadata = NutritionExplanationRuntimeMetadata(
        provider="deterministic",
        fallback_used=True,
        validation_status="fallback_used",
        validation_errors=[],
        raw_output_preview_truncated=None,
        raw_output_length=0,
        configured_model="deterministic",
        selected_model="deterministic",
        candidate_validation_status="not_attempted",
        markdown_wrapper_detected=False,
    )
    approved = _approved_explanation()
    approved_payload = approved.to_dict()

    debug_payload = metadata.to_debug_dict()
    assert debug_payload["provider"] == "deterministic"
    assert debug_payload["configured_model"] == "deterministic"
    assert debug_payload["selected_model"] == "deterministic"
    assert debug_payload["candidate_validation_status"] == "not_attempted"
    assert debug_payload["markdown_wrapper_detected"] is False
    assert "provider" not in approved_payload
    assert "raw_output_preview_truncated" not in approved_payload


def test_low_limited_approved_explanation_requires_limitation_context_or_reason():
    with pytest.raises(ValueError, match="Limited/Low approved"):
        ApprovedNutritionExplanation(
            user_id=1,
            explanation_date="2026-06-07",
            explanation_summary="Nutrition explanation is limited.",
            confidence="Low",
        )
