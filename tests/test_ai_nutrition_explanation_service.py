from __future__ import annotations

import copy
import json
from dataclasses import dataclass

import pytest

from models.ai_nutrition_explanation_models import (
    CandidateNutritionExplanation,
    NutritionExplanationContext,
)
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


def _safe_provider_candidate() -> CandidateNutritionExplanation:
    return CandidateNutritionExplanation(
        explanation_summary=(
            "Based on approved nutrition context, today can be reviewed cautiously."
        ),
        macro_context="Based on today’s logged meals, protein is below target.",
        food_suggestion_context=(
            "The Nutrition tab has approved food suggestions that may help close the gap."
        ),
        trend_context="Trend evidence is summarized from deterministic logged data.",
        calibration_context="Targets are still formula-derived.",
        limitations_context=(
            "Use the Nutrition tab for approved target, logging, trend, and calibration detail."
        ),
        confidence="Moderate",
        reason_codes=["provider_candidate_safe"],
    )


def test_configured_provider_defaults_to_deterministic(monkeypatch, approved_context):
    monkeypatch.delenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, raising=False)

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.configured_provider == "deterministic"
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.configured_model == "deterministic"
    assert result.runtime_metadata.selected_model == "deterministic"
    assert result.runtime_metadata.provider_attempted is False
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"
    assert result.runtime_metadata.final_explanation_source == "deterministic"


def test_invalid_configured_provider_falls_back_to_deterministic(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "not-real")

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.configured_provider == "not-real"
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "invalid_provider_config"


def test_provider_candidate_that_validates_returns_approved_explanation(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_MODEL_ENV, "ollama/qwen-test:3b")

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: _safe_provider_candidate(),
    )

    assert result.approved_nutrition_explanation.source == "ai_validated"
    assert result.runtime_metadata.configured_provider == "crewai"
    assert result.runtime_metadata.selected_provider == "crewai"
    assert result.runtime_metadata.configured_model == "ollama/qwen-test:3b"
    assert result.runtime_metadata.selected_model == "ollama/qwen-test:3b"
    assert result.runtime_metadata.provider_attempted is True
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.candidate_valid is True
    assert result.runtime_metadata.candidate_validation_status == "success"
    assert result.runtime_metadata.validation_status == "approved"
    assert result.runtime_metadata.final_explanation_source == "provider_approved"


def test_provider_json_candidate_that_validates_returns_approved_explanation(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    raw_json = _safe_provider_candidate().to_dict()

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: raw_json,
    )

    assert result.approved_nutrition_explanation.source == "ai_validated"
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.raw_output_length is not None
    assert result.runtime_metadata.raw_output_preview_truncated


def test_provider_parse_failure_metadata_includes_model_and_markdown_flag(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_MODEL_ENV, "ollama/gemma-test:4b")

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: '```json\n{"extra": "bad"}\n```',
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.configured_model == "ollama/gemma-test:4b"
    assert result.runtime_metadata.selected_model == "ollama/gemma-test:4b"
    assert result.runtime_metadata.fallback_reason == "candidate_parse_failure"
    assert result.runtime_metadata.candidate_parse_status == "failed"
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"
    assert result.runtime_metadata.markdown_wrapper_detected is True


def test_provider_validation_failure_metadata_includes_candidate_validation_status(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    monkeypatch.setenv(
        service.NUTRITION_EXPLANATION_MODEL_ENV, "ollama/validator-test:7b"
    )

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: CandidateNutritionExplanation(
            explanation_summary="Calibration has been applied and targets changed.",
            confidence="Moderate",
            reason_codes=["unsafe_provider_candidate"],
        ),
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.configured_model == "ollama/validator-test:7b"
    assert result.runtime_metadata.selected_model == "ollama/validator-test:7b"
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "failed"
    assert result.runtime_metadata.validation_status == "rejected"


def test_provider_candidate_with_invented_target_is_rejected_and_falls_back(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    unsafe = CandidateNutritionExplanation(
        explanation_summary="Your targets have been changed based on this trend.",
        confidence="Moderate",
        reason_codes=["unsafe_provider_candidate"],
    )

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: unsafe,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "candidate_validation_failure"
    assert result.runtime_metadata.candidate_valid is False
    assert result.runtime_metadata.validation_errors


def test_provider_candidate_with_invented_food_serving_or_macro_falls_back(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    unsafe = CandidateNutritionExplanation(
        explanation_summary="Add 999g dragonfruit for exactly 200 grams carbs.",
        confidence="Moderate",
        reason_codes=["unsafe_provider_candidate"],
    )

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: unsafe,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "candidate_validation_failure"
    assert result.runtime_metadata.final_explanation_source == "deterministic_fallback"


def test_provider_candidate_with_calibration_applied_language_falls_back(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    unsafe = CandidateNutritionExplanation(
        explanation_summary="Calibration has been applied and calibrated targets are active.",
        confidence="Moderate",
        reason_codes=["unsafe_provider_candidate"],
    )

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: unsafe,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "candidate_validation_failure"


def test_provider_unavailable_or_error_falls_back_safely(monkeypatch, approved_context):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")

    def failing_provider(_context):
        raise RuntimeError("provider unavailable")

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=failing_provider,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.provider_attempted is True
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "provider_exception"
    assert result.runtime_metadata.validation_errors == ["RuntimeError"]


def test_runtime_metadata_remains_debug_only_and_separate(
    monkeypatch,
    approved_context,
):
    monkeypatch.delenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, raising=False)
    monkeypatch.delenv(service.NUTRITION_EXPLANATION_MODEL_ENV, raising=False)

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
    )

    public_payload = result.approved_nutrition_explanation.to_dict()
    debug_payload = result.runtime_metadata.to_debug_dict()

    assert "configured_provider" not in public_payload
    assert "selected_provider" not in public_payload
    assert "configured_model" not in public_payload
    assert "selected_model" not in public_payload
    assert "raw_output_preview_truncated" not in public_payload
    assert debug_payload["configured_provider"] == "deterministic"
    assert debug_payload["configured_model"] == "deterministic"
    assert debug_payload["selected_model"] == "deterministic"
    assert "raw_output_preview_truncated" in debug_payload


def test_provider_prompt_includes_exact_schema_only_instruction(approved_context):
    prompt = service.build_crewai_nutrition_explanation_prompt(approved_context)

    assert "Return JSON only" in prompt
    assert "CandidateNutritionExplanation allowed output schema" in prompt
    assert "Include exactly these top-level keys and no others" in prompt
    for key in [
        "explanation_summary",
        "macro_context",
        "food_suggestion_context",
        "trend_context",
        "calibration_context",
        "limitations_context",
        "confidence",
        "reason_codes",
    ]:
        assert f'"{key}"' in prompt


def test_provider_prompt_forbids_extra_keys_and_display_flags(approved_context):
    prompt = service.build_crewai_nutrition_explanation_prompt(approved_context)

    assert "Do not include any keys not listed in the schema" in prompt
    assert "Do not include display flags" in prompt
    assert "Do not include display_flags" in prompt
    assert "Do not include displayFlags" in prompt
    assert "Do not include target metadata" in prompt
    assert "Do not include raw context fields" in prompt
    assert "Do not include provider fields" in prompt
    assert "Do not include runtime fields" in prompt


def test_provider_prompt_forbids_explanation_date_and_markdown(approved_context):
    prompt = service.build_crewai_nutrition_explanation_prompt(approved_context)

    assert "Do not include explanationDate" in prompt
    assert "Do not include explanation_date" in prompt
    assert "Do not include dates unless the schema explicitly requires them" in prompt
    assert "Do not include markdown" in prompt
    assert "Do not include code fences" in prompt
    assert "Do not include prose outside JSON" in prompt


def _approved_context_json_from_prompt(prompt: str) -> dict:
    context_marker = "Approved context JSON:\n"
    forbidden_marker = "\n\nForbidden language and behavior:"
    assert context_marker in prompt
    assert forbidden_marker in prompt
    context_json = prompt.split(context_marker, 1)[1].split(forbidden_marker, 1)[0]
    return json.loads(context_json)


def test_compressed_provider_context_excludes_display_flags_and_target_booleans(
    approved_context,
):
    provider_context = service._compressed_provider_context_projection(approved_context)
    provider_context_text = json.dumps(provider_context, sort_keys=True)

    forbidden_terms = [
        "display_flags",
        "displayFlags",
        "allow_calorie_targets",
        "allow_carbohydrate_targets",
        "allow_fat_targets",
        "allow_protein_targets",
        "display_allowed",
    ]
    assert not any(term in provider_context_text for term in forbidden_terms)


def test_compressed_provider_context_excludes_dates_formula_and_debug_metadata(
    approved_context,
):
    provider_context = service._compressed_provider_context_projection(approved_context)
    provider_context_text = json.dumps(provider_context, sort_keys=True)

    forbidden_terms = [
        "explanation_date",
        "explanationDate",
        "calculation_date",
        "suggestion_date",
        "start_date",
        "end_date",
        "calibration_date",
        "formula_metadata",
        "formula_name",
        "formula_version",
        "provider_metadata",
        "runtime_metadata",
        "raw_food_entries",
        "raw_daily_checkins",
        "raw_sql",
    ]
    assert not any(term in provider_context_text for term in forbidden_terms)


def test_provider_prompt_uses_compressed_context_not_full_context(approved_context):
    prompt = service.build_crewai_nutrition_explanation_prompt(approved_context)
    provider_context = _approved_context_json_from_prompt(prompt)
    provider_context_text = json.dumps(provider_context, sort_keys=True)

    assert set(provider_context) == {
        "confidence",
        "macro_context",
        "food_suggestion_context",
        "trend_context",
        "calibration_context",
        "limitations_context",
        "value_aware_context",
    }
    assert "display_flags" not in provider_context_text
    assert "formula_metadata" not in provider_context_text
    assert "reason_codes" not in provider_context_text
    assert "raw_" not in provider_context_text


def test_value_aware_provider_context_includes_approved_values(approved_context):
    provider_context = service._compressed_provider_context_projection(approved_context)
    value_context = provider_context["value_aware_context"]

    target_ranges = value_context["approved_target_ranges"]
    assert {
        "macro": "protein",
        "unit": "g",
        "target_min": 150,
        "target_max": 185,
        "display_value": "150-185 g",
        "confidence": "Moderate",
    } in target_ranges
    assert {
        "macro": "calories",
        "unit": "kcal",
        "target_min": 2300,
        "target_max": 2600,
        "display_value": "2300-2600 kcal",
        "confidence": "Moderate",
    } in target_ranges

    assert value_context["logged_actuals"]["protein"] == {"actual": 128.8, "unit": "g"}
    assert value_context["logged_actuals"]["calories"] == {
        "actual": 2400,
        "unit": "kcal",
    }

    protein_status = next(
        status
        for status in value_context["macro_statuses_and_gaps"]
        if status["macro"] == "protein"
    )
    assert protein_status["target_status"] == "below_target"
    assert protein_status["actual"] == 128.8
    assert protein_status["target_min"] == 150
    assert protein_status["target_max"] == 185
    assert protein_status["gap_to_target_min"] == 21.2

    suggestion = value_context["approved_food_suggestion_candidates"][0]
    assert suggestion["display_name"] == "Chicken Breast, Cooked, Skinless"
    assert suggestion["suggested_grams"] == 150
    assert suggestion["estimated_protein_g"] == 46.5
    assert suggestion["macro_gap_addressed"] == "protein_g"


def test_value_aware_provider_context_excludes_disallowed_target_values(
    approved_context,
):
    context_payload = copy.deepcopy(approved_context.to_dict())
    context_payload["approved_macro_targets"]["carbohydrate_target_g"] = {
        "target_type": "carbohydrate_g",
        "min_value": 250,
        "max_value": 310,
        "display_value": "250-310 g",
        "unit": "g",
        "confidence": "Moderate",
        "display_allowed": False,
        "reason_codes": ["carb_target_not_displayed"],
        "limitations": [],
    }
    context_payload["target_vs_actual_summary"]["comparisons"]["carbs"] = {
        "nutrient": "carbs",
        "actual": 200,
        "target_min": 250,
        "target_max": 310,
        "target_status": "below_target",
        "comparison_available": True,
        "confidence": "Moderate",
        "reason_codes": ["logged_carbs_below_target"],
        "limitations": [],
    }
    context_payload["target_vs_actual_summary"]["nutrition_actuals"]["logged_carbs"] = (
        200
    )
    context_payload["value_aware_summary"] = service._value_aware_summary_from_payloads(
        approved_macro_targets_payload=context_payload["approved_macro_targets"],
        target_vs_actual_payload=context_payload["target_vs_actual_summary"],
        food_suggestions_payload=context_payload["approved_food_suggestions"],
        trend_payload=context_payload["trend_summary"],
        calibration_payload=context_payload["calibration_summary"],
    )
    context = service.NutritionExplanationContext(**context_payload)

    value_context = service._compressed_provider_context_projection(context)[
        "value_aware_context"
    ]

    assert not any(
        target["macro"] == "carbs" for target in value_context["approved_target_ranges"]
    )
    carb_status = next(
        status
        for status in value_context["macro_statuses_and_gaps"]
        if status["macro"] == "carbs"
    )
    assert carb_status["actual"] == 200
    assert carb_status["target_status"] == "below_target"
    assert "target_min" not in carb_status
    assert "target_max" not in carb_status
    assert "gap_to_target_min" not in carb_status


def test_provider_prompt_allows_only_value_aware_approved_values(approved_context):
    prompt = service.build_crewai_nutrition_explanation_prompt(approved_context)
    provider_context = _approved_context_json_from_prompt(prompt)
    value_context = provider_context["value_aware_context"]

    assert "value_aware_context" in prompt
    assert (
        "You may quote numbers only when they appear in value_aware_context" in prompt
    )
    assert "You may quote foods only when they appear in value_aware_context" in prompt
    assert "Do not calculate gaps" in prompt
    assert value_context["approved_target_ranges"]
    assert value_context["macro_statuses_and_gaps"]
    assert value_context["approved_food_suggestion_candidates"]


def test_value_aware_provider_candidate_can_quote_approved_values(
    approved_context,
):
    candidate = CandidateNutritionExplanation(
        explanation_summary=(
            "Protein is below the approved 150-185 g target range after logging "
            "128.8 g today."
        ),
        macro_context=(
            "That leaves about 21.2 g to reach the approved minimum protein target."
        ),
        food_suggestion_context=(
            "Chicken breast is an approved suggestion; 150 g would add about "
            "46.5 g protein."
        ),
        trend_context="Trend evidence is summarized from deterministic logged data.",
        calibration_context="Targets are still formula-derived.",
        limitations_context=(
            "Use only approved backend values when interpreting today's nutrition."
        ),
        confidence="Moderate",
        reason_codes=["provider_candidate_value_aware"],
    )

    result = service.approve_candidate_output_or_fallback_with_metadata(
        candidate.to_dict(),
        approved_context,
        configured_provider="direct_ollama",
        selected_provider="direct_ollama",
        configured_model="ollama/qwen2.5:3b",
        selected_model="qwen2.5:3b",
        provider_attempted=True,
    )

    assert result.approved_nutrition_explanation.source == "ai_validated"
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.validation_status == "approved"


def test_provider_prompt_includes_one_compact_valid_json_example(approved_context):
    prompt = service.build_crewai_nutrition_explanation_prompt(approved_context)

    assert "One valid JSON example:" in prompt
    example_text = prompt.split("One valid JSON example:\n", 1)[1].split(
        "\n\nApproved context JSON:",
        1,
    )[0]
    example = json.loads(example_text)
    assert set(example) == {
        "explanation_summary",
        "macro_context",
        "food_suggestion_context",
        "trend_context",
        "calibration_context",
        "limitations_context",
        "confidence",
        "reason_codes",
    }
    assert example["confidence"] in {"Limited", "Low", "Moderate", "High"}


def test_provider_output_with_exact_schema_parses_successfully(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    provider_json = {
        "explanation_summary": (
            "Based on approved nutrition context, today can be reviewed cautiously."
        ),
        "macro_context": "Based on today’s logged meals, protein is below target.",
        "food_suggestion_context": (
            "The Nutrition tab has approved food suggestions that may help close the gap."
        ),
        "trend_context": "Trend evidence is summarized from deterministic logged data.",
        "calibration_context": "Targets are still formula-derived.",
        "limitations_context": (
            "Use the Nutrition tab for approved target, logging, trend, and calibration detail."
        ),
        "confidence": "Moderate",
        "reason_codes": ["provider_candidate_safe"],
    }

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: provider_json,
    )

    assert result.approved_nutrition_explanation.source == "ai_validated"
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.final_explanation_source == "provider_approved"


def test_provider_output_with_extra_display_flags_fails_parse(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    provider_json = _safe_provider_candidate().to_dict()
    provider_json["display_flags"] = {"allow_protein_targets": True}

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: provider_json,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "candidate_parse_failure"
    assert result.runtime_metadata.candidate_parse_status == "failed"
    assert result.runtime_metadata.final_explanation_source == "deterministic_fallback"


def test_provider_output_with_extra_display_flags_alias_fails_parse(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    provider_json = _safe_provider_candidate().to_dict()
    provider_json["displayFlags"] = {"allowProteinTargets": True}

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: provider_json,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.fallback_reason == "candidate_parse_failure"
    assert result.runtime_metadata.candidate_parse_status == "failed"


def test_provider_output_with_explanation_date_fails_parse(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    provider_json = _safe_provider_candidate().to_dict()
    provider_json["explanationDate"] = "2026-06-07"

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: provider_json,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.fallback_reason == "candidate_parse_failure"
    assert result.runtime_metadata.candidate_parse_status == "failed"


def test_provider_output_with_markdown_code_fence_fails_parse(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    raw_json = _safe_provider_candidate().to_dict()
    raw_output = f"```json\n{json.dumps(raw_json)}\n```"

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: raw_output,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "candidate_parse_failure"
    assert result.runtime_metadata.candidate_parse_status == "failed"


def test_parseable_provider_output_with_unsafe_language_still_fails_validation(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_PROVIDER_ENV, "crewai")
    provider_json = _safe_provider_candidate().to_dict()
    provider_json["calibration_context"] = "Calibration has been applied."

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        candidate_provider=lambda _context: provider_json,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "candidate_validation_failure"
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.validation_status == "rejected"


def test_direct_ollama_configured_provider_selects_direct_provider(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(
        service.NUTRITION_EXPLANATION_PROVIDER_ENV,
        service.NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
    )
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_MODEL_ENV, "ollama/qwen2.5:3b")
    monkeypatch.setenv(service.OLLAMA_BASE_URL_ENV, "http://ollama.test:11434")
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_DIRECT_OLLAMA_TIMEOUT_ENV, "12")
    captured: dict[str, object] = {}

    def fake_generate(
        base_url, selected_model, prompt, response_schema, timeout_seconds
    ):
        captured["base_url"] = base_url
        captured["selected_model"] = selected_model
        captured["prompt"] = prompt
        captured["response_schema"] = response_schema
        captured["timeout_seconds"] = timeout_seconds
        return json.dumps(_safe_provider_candidate().to_dict())

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        direct_ollama_generate=fake_generate,
    )

    assert result.approved_nutrition_explanation.source == "ai_validated"
    assert result.runtime_metadata.configured_provider == "direct_ollama"
    assert result.runtime_metadata.selected_provider == "direct_ollama"
    assert result.runtime_metadata.configured_model == "ollama/qwen2.5:3b"
    assert result.runtime_metadata.selected_model == "qwen2.5:3b"
    assert result.runtime_metadata.provider_attempted is True
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.fallback_reason is None
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "success"
    assert result.runtime_metadata.validation_status == "approved"
    assert result.runtime_metadata.final_explanation_source == "provider_approved"
    assert captured["base_url"] == "http://ollama.test:11434"
    assert captured["selected_model"] == "qwen2.5:3b"
    assert (
        captured["response_schema"]
        == service.CANDIDATE_NUTRITION_EXPLANATION_JSON_SCHEMA
    )
    assert captured["timeout_seconds"] == 12
    assert "CandidateNutritionExplanation allowed output schema" in str(
        captured["prompt"]
    )


@pytest.mark.parametrize(
    ("fallback_reason", "message"),
    [
        (service.FALLBACK_REASON_DIRECT_OLLAMA_TIMEOUT, "request timed out"),
        (
            service.FALLBACK_REASON_DIRECT_OLLAMA_CONNECTION_ERROR,
            "connection failed",
        ),
        (service.FALLBACK_REASON_DIRECT_OLLAMA_HTTP_ERROR, "500 server error"),
        (
            service.FALLBACK_REASON_DIRECT_OLLAMA_MALFORMED_RESPONSE,
            "malformed response",
        ),
        (
            service.FALLBACK_REASON_DIRECT_OLLAMA_MISSING_RESPONSE_TEXT,
            "missing response text",
        ),
    ],
)
def test_direct_ollama_transport_failures_fall_back_deterministically(
    monkeypatch,
    approved_context,
    fallback_reason,
    message,
):
    monkeypatch.setenv(
        service.NUTRITION_EXPLANATION_PROVIDER_ENV,
        service.NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
    )
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_MODEL_ENV, "ollama/qwen2.5:3b")

    def failing_generate(*_args, **_kwargs):
        raise service.DirectOllamaProviderError(fallback_reason, message)

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        direct_ollama_generate=failing_generate,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.configured_provider == "direct_ollama"
    assert result.runtime_metadata.selected_provider == "direct_ollama"
    assert result.runtime_metadata.provider_attempted is True
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == fallback_reason
    assert result.runtime_metadata.final_explanation_source == "deterministic_fallback"
    assert result.runtime_metadata.candidate_parse_status == "not_attempted"
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"
    assert result.runtime_metadata.validation_status == "not_attempted"
    assert result.runtime_metadata.validation_errors == [message]


def test_direct_ollama_parse_failure_falls_back_deterministically(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(
        service.NUTRITION_EXPLANATION_PROVIDER_ENV,
        service.NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
    )
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_MODEL_ENV, "ollama/gemma3n:e4b")

    def fake_generate(*_args, **_kwargs):
        return '```json\n{"explanation": {"bad": true}}\n```'

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        direct_ollama_generate=fake_generate,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "candidate_parse_failure"
    assert result.runtime_metadata.candidate_parse_status == "failed"
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"
    assert result.runtime_metadata.markdown_wrapper_detected is True
    assert result.runtime_metadata.raw_output_length is not None


def test_direct_ollama_validation_failure_falls_back_deterministically(
    monkeypatch,
    approved_context,
):
    monkeypatch.setenv(
        service.NUTRITION_EXPLANATION_PROVIDER_ENV,
        service.NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
    )
    monkeypatch.setenv(service.NUTRITION_EXPLANATION_MODEL_ENV, "ollama/hermes3:3b")
    unsafe_candidate = _safe_provider_candidate().to_dict()
    unsafe_candidate["calibration_context"] = "Calibration has been applied."

    def fake_generate(*_args, **_kwargs):
        return json.dumps(unsafe_candidate)

    result = service.build_configured_approved_nutrition_explanation_with_metadata(
        1,
        context=approved_context,
        direct_ollama_generate=fake_generate,
    )

    assert result.approved_nutrition_explanation.source == "deterministic_fallback"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "candidate_validation_failure"
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "failed"
    assert result.runtime_metadata.validation_status == "rejected"
    assert result.runtime_metadata.final_explanation_source == "deterministic_fallback"


def test_configured_direct_ollama_timeout_uses_default_for_invalid_values(monkeypatch):
    monkeypatch.delenv(
        service.NUTRITION_EXPLANATION_DIRECT_OLLAMA_TIMEOUT_ENV,
        raising=False,
    )
    assert (
        service._configured_direct_ollama_timeout_seconds()
        == service.NUTRITION_EXPLANATION_DIRECT_OLLAMA_DEFAULT_TIMEOUT_SECONDS
    )

    monkeypatch.setenv(service.NUTRITION_EXPLANATION_DIRECT_OLLAMA_TIMEOUT_ENV, "bad")
    assert (
        service._configured_direct_ollama_timeout_seconds()
        == service.NUTRITION_EXPLANATION_DIRECT_OLLAMA_DEFAULT_TIMEOUT_SECONDS
    )

    monkeypatch.setenv(service.NUTRITION_EXPLANATION_DIRECT_OLLAMA_TIMEOUT_ENV, "0")
    assert (
        service._configured_direct_ollama_timeout_seconds()
        == service.NUTRITION_EXPLANATION_DIRECT_OLLAMA_DEFAULT_TIMEOUT_SECONDS
    )
