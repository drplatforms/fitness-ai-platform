from __future__ import annotations

from models.nutrition_provider_contract_models import (
    NUTRITION_PROVIDER_FALLBACK_REASON_PARSE_FAILED,
    NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_EXCEPTION,
    NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_TIMEOUT,
    NUTRITION_PROVIDER_FALLBACK_REASON_VALIDATION_FAILED,
    NUTRITION_PROVIDER_PARSE_STATUS_SUCCESS,
)
from services.nutrition_report_section_direct_ollama_provider import (
    CANDIDATE_NUTRITION_REPORT_SECTION_JSON_SCHEMA,
    DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_APPROVED,
    build_direct_ollama_nutrition_report_section_prompt,
    run_direct_ollama_nutrition_report_section_provider,
)
from tests.nutrition_provider_fixtures import (
    build_complete_nutrition_provider_evidence,
    valid_provider_candidate_json,
)


def test_prompt_uses_provider_safe_context_and_exact_json_contract():
    evidence = build_complete_nutrition_provider_evidence()

    prompt = build_direct_ollama_nutrition_report_section_prompt(evidence)

    assert "Return JSON only" in prompt
    assert "approved_numeric_values" in prompt
    assert "Do not calculate" in prompt
    assert "section_summary" in prompt
    assert "NutritionProvider" not in prompt
    assert "raw_output" not in prompt
    assert "traceback" not in prompt
    assert "Chicken Breast, Cooked, Skinless" in prompt


def test_direct_ollama_provider_approves_valid_fake_candidate():
    evidence = build_complete_nutrition_provider_evidence()
    calls = []

    def fake_generate(base_url, model, prompt, schema, timeout_seconds):
        calls.append((base_url, model, prompt, schema, timeout_seconds))
        assert schema == CANDIDATE_NUTRITION_REPORT_SECTION_JSON_SCHEMA
        assert model == "qwen2.5:3b"
        return valid_provider_candidate_json()

    result = run_direct_ollama_nutrition_report_section_provider(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-14",
        evidence_context=evidence,
        generate=fake_generate,
        timeout_seconds=300,
    )

    assert len(calls) == 1
    assert result.success is True
    assert result.provider_attempted is True
    assert result.fallback_used is False
    assert (
        result.final_section_source
        == DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_APPROVED
    )
    assert (
        result.approved_section.source
        == DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_APPROVED
    )
    assert result.safe_metadata["provider_enabled"] is True
    assert result.safe_metadata["provider_attempted"] is True
    assert result.safe_metadata["selected_provider"] == "direct_ollama"
    assert result.safe_metadata["selected_model"] == "qwen2.5:3b"
    assert (
        result.safe_metadata["parse_status"] == NUTRITION_PROVIDER_PARSE_STATUS_SUCCESS
    )
    assert result.safe_metadata["validation_status"] == "approved"
    assert result.safe_metadata["validation_errors_count"] == 0
    assert "raw_output" not in result.safe_metadata
    assert "prompt" not in result.safe_metadata


def test_direct_ollama_provider_parse_failure_falls_back_without_raw_output():
    evidence = build_complete_nutrition_provider_evidence()

    def fake_generate(*_args, **_kwargs):
        return '{"nutrition_report_section": {"section_summary": "wrapped"}}'

    result = run_direct_ollama_nutrition_report_section_provider(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-14",
        evidence_context=evidence,
        generate=fake_generate,
    )

    assert result.success is False
    assert result.fallback_used is True
    assert result.fallback_reason == NUTRITION_PROVIDER_FALLBACK_REASON_PARSE_FAILED
    assert result.approved_section.source.endswith("fallback")
    assert result.safe_metadata["fallback_used"] is True
    assert result.safe_metadata["validation_errors_count"] == 0
    assert "parse_errors" not in result.safe_metadata
    assert "raw_output" not in result.safe_metadata


def test_direct_ollama_provider_validation_failure_falls_back_safely():
    evidence = build_complete_nutrition_provider_evidence()

    def fake_generate(*_args, **_kwargs):
        return valid_provider_candidate_json(
            next_nutrition_action="Add 999 g of approved protein food before changing targets."
        )

    result = run_direct_ollama_nutrition_report_section_provider(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-14",
        evidence_context=evidence,
        generate=fake_generate,
    )

    assert result.success is False
    assert result.fallback_used is True
    assert (
        result.fallback_reason == NUTRITION_PROVIDER_FALLBACK_REASON_VALIDATION_FAILED
    )
    assert result.safe_metadata["validation_status"] == "rejected"
    assert result.safe_metadata["validation_errors_count"] > 0
    assert "validation_errors" not in result.safe_metadata
    assert "999 g" not in result.approved_section.next_nutrition_action.lower()


def test_direct_ollama_provider_timeout_and_exception_fall_back_safely():
    evidence = build_complete_nutrition_provider_evidence()

    def timeout_generate(*_args, **_kwargs):
        raise TimeoutError("simulated timeout")

    timeout_result = run_direct_ollama_nutrition_report_section_provider(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-14",
        evidence_context=evidence,
        generate=timeout_generate,
    )
    assert (
        timeout_result.fallback_reason
        == NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_TIMEOUT
    )
    assert "simulated timeout" not in str(timeout_result.safe_metadata)

    def exception_generate(*_args, **_kwargs):
        raise RuntimeError("secret provider payload")

    exception_result = run_direct_ollama_nutrition_report_section_provider(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-14",
        evidence_context=evidence,
        generate=exception_generate,
    )
    assert (
        exception_result.fallback_reason
        == NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_EXCEPTION
    )
    assert "secret provider payload" not in str(exception_result.safe_metadata)
