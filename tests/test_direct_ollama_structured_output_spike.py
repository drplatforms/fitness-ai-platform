from __future__ import annotations

import pytest

from models.ai_nutrition_explanation_models import NutritionExplanationContext
from scripts.spike_direct_ollama_nutrition_explanation import (
    CANDIDATE_NUTRITION_EXPLANATION_JSON_SCHEMA,
    detect_direct_ollama_output_diagnostics,
    normalize_ollama_model_name,
    run_direct_ollama_nutrition_explanation_spike,
)


@pytest.fixture
def approved_context() -> NutritionExplanationContext:
    return NutritionExplanationContext(
        user_id=102,
        explanation_date="2026-06-06",
        target_vs_actual_summary={
            "confidence": "Moderate",
            "logging_completeness": "complete_enough_for_guidance",
            "comparisons": {
                "protein": {
                    "target_status": "below_target",
                    "comparison_available": True,
                    "confidence": "Moderate",
                }
            },
        },
        approved_food_suggestions={
            "confidence": "Moderate",
            "primary_gap": "protein_g",
            "suggestion_count": 2,
        },
        trend_summary={
            "confidence": "Moderate",
            "window_days": 28,
            "logging_consistency_status": "usable",
        },
        calibration_summary={
            "confidence": "Moderate",
            "readiness_level": "strong",
            "calibration_allowed": False,
        },
        confidence="Moderate",
        reason_codes=["approved_nutrition_explanation_context_built"],
        limitations=["Targets are coaching estimates, not medical nutrition advice."],
    )


def _valid_raw_candidate() -> str:
    return """
{
  "explanation_summary": "Approved nutrition context is available for review.",
  "macro_context": "Based on logged meals, protein is below target.",
  "food_suggestion_context": "Approved food suggestions are available in the Nutrition tab.",
  "trend_context": "Trend evidence is summarized from deterministic logged data.",
  "calibration_context": "Targets remain formula-derived until backend calibration is approved.",
  "limitations_context": "Use the Nutrition tab for approved target and trend detail.",
  "confidence": "Moderate",
  "reason_codes": ["provider_candidate_from_approved_context"]
}
""".strip()


def test_normalize_ollama_model_name_removes_crewai_prefix():
    assert normalize_ollama_model_name("ollama/qwen2.5:3b") == "qwen2.5:3b"
    assert normalize_ollama_model_name("gemma3n:e4b") == "gemma3n:e4b"


def test_json_schema_rejects_extra_properties_by_contract():
    assert CANDIDATE_NUTRITION_EXPLANATION_JSON_SCHEMA["additionalProperties"] is False
    assert set(CANDIDATE_NUTRITION_EXPLANATION_JSON_SCHEMA["required"]) == {
        "explanation_summary",
        "macro_context",
        "food_suggestion_context",
        "trend_context",
        "calibration_context",
        "limitations_context",
        "confidence",
        "reason_codes",
    }


def test_direct_ollama_spike_valid_output_parses_and_validates(approved_context):
    captured: dict[str, object] = {}

    def fake_generate(
        base_url, selected_model, prompt, response_schema, timeout_seconds
    ):
        captured["base_url"] = base_url
        captured["selected_model"] = selected_model
        captured["schema"] = response_schema
        captured["prompt"] = prompt
        captured["timeout_seconds"] = timeout_seconds
        return _valid_raw_candidate()

    result = run_direct_ollama_nutrition_explanation_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        explanation_date="2026-06-06",
        ollama_base_url="http://ollama.test:11434",
        context=approved_context,
        generate=fake_generate,
        timeout_seconds=10,
    )

    assert result.success is True
    assert result.configured_model == "ollama/qwen2.5:3b"
    assert result.selected_model == "qwen2.5:3b"
    assert result.candidate_parse_status == "success"
    assert result.candidate_validation_status == "success"
    assert result.validation_status == "approved"
    assert result.fallback_used is False
    assert result.final_explanation_source == "provider_approved"
    assert result.extra_keys_detected == []
    assert result.wrapper_object_detected is False
    assert captured["selected_model"] == "qwen2.5:3b"
    assert captured["schema"] == CANDIDATE_NUTRITION_EXPLANATION_JSON_SCHEMA
    assert "CandidateNutritionExplanation allowed output schema" in str(
        captured["prompt"]
    )


def test_direct_ollama_spike_parse_failure_captures_diagnostics(approved_context):
    def fake_generate(*_args, **_kwargs):
        return '```json\n{"explanation": {"bad": true}}\n```'

    result = run_direct_ollama_nutrition_explanation_spike(
        model="ollama/gemma3n:e4b",
        user_id=102,
        explanation_date="2026-06-06",
        context=approved_context,
        generate=fake_generate,
    )

    assert result.success is False
    assert result.candidate_parse_status == "failed"
    assert result.candidate_validation_status == "not_attempted"
    assert result.validation_status == "not_attempted"
    assert result.fallback_used is True
    assert result.fallback_reason == "candidate_parse_failure"
    assert result.markdown_wrapper_detected is True
    assert result.raw_output_length is not None
    assert result.raw_output_preview_truncated


def test_direct_ollama_spike_validation_failure_captures_rejection(approved_context):
    def fake_generate(*_args, **_kwargs):
        return """
{
  "explanation_summary": "Calibration has been applied and targets were changed.",
  "macro_context": null,
  "food_suggestion_context": null,
  "trend_context": null,
  "calibration_context": null,
  "limitations_context": null,
  "confidence": "Moderate",
  "reason_codes": ["unsafe_provider_candidate"]
}
""".strip()

    result = run_direct_ollama_nutrition_explanation_spike(
        model="ollama/hermes3:3b",
        user_id=102,
        explanation_date="2026-06-06",
        context=approved_context,
        generate=fake_generate,
    )

    assert result.success is False
    assert result.candidate_parse_status == "success"
    assert result.candidate_validation_status == "failed"
    assert result.validation_status == "rejected"
    assert result.fallback_reason == "candidate_validation_failure"
    assert result.validation_errors


def test_direct_ollama_spike_provider_exception_is_recorded(approved_context):
    def fake_generate(*_args, **_kwargs):
        raise TimeoutError("model timed out")

    result = run_direct_ollama_nutrition_explanation_spike(
        model="ollama/qwen3:8b",
        user_id=102,
        explanation_date="2026-06-06",
        context=approved_context,
        generate=fake_generate,
    )

    assert result.success is False
    assert result.candidate_parse_status == "not_attempted"
    assert result.candidate_validation_status == "not_attempted"
    assert result.fallback_used is True
    assert result.fallback_reason == "provider_exception"
    assert "TimeoutError" in result.validation_errors[0]


def test_detect_direct_ollama_output_diagnostics_detects_extra_keys_and_wrapper():
    diagnostics = detect_direct_ollama_output_diagnostics(
        '{"explanation": {"explanation_summary": "wrapped"}, "confidence": "Moderate"}'
    )

    assert diagnostics["extra_keys_detected"] == ["explanation"]
    assert diagnostics["wrapper_object_detected"] is True
