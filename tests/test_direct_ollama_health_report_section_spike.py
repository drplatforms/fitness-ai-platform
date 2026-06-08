from __future__ import annotations

from scripts.spike_direct_ollama_health_report_sections import (
    CANDIDATE_HEALTH_REPORT_SECTION_JSON_SCHEMA,
    build_direct_ollama_health_report_section_prompt,
    detect_direct_ollama_section_output_diagnostics,
    normalize_ollama_model_name,
    run_direct_ollama_health_report_section_spike,
)

APPROVED_CONTEXT = {
    "section": "nutrition",
    "coaching_decision": {
        "scenario": "aligned_managed",
        "primary_focus": "maintain consistent progress",
        "nutrition_action": "use approved nutrition gaps",
        "confidence": "High",
    },
    "approved_nutrition_context": {
        "confidence": "High",
        "value_aware_context": {
            "approved_target_ranges": [
                {
                    "macro": "protein",
                    "unit": "g",
                    "target_min": 150,
                    "target_max": 180,
                    "confidence": "High",
                }
            ],
            "logged_actuals": {"protein": {"actual": 120, "unit": "g"}},
            "macro_statuses_and_gaps": [
                {
                    "macro": "protein",
                    "target_status": "below_target",
                    "gap_to_target_min": 30,
                    "unit": "g",
                    "confidence": "High",
                }
            ],
            "approved_food_suggestion_candidates": [
                {
                    "display_name": "Greek Yogurt, Plain",
                    "suggested_grams": 200,
                    "macro_gap_addressed": "protein_g",
                    "suggestion_summary": "200 g Greek yogurt can support the protein gap.",
                    "confidence": "High",
                }
            ],
        },
    },
}


def _valid_raw_section() -> str:
    return """
{
  "section_summary": "Protein is the main approved nutrition focus today.",
  "key_observations": [
    "Logged protein is below the approved target range.",
    "Greek Yogurt, Plain is an approved food option for the current protein gap."
  ],
  "coaching_interpretation": "This looks like a simple nutrition support opportunity rather than a major change.",
  "suggested_focus": "Use the Nutrition tab and consider Greek Yogurt, Plain as a practical snack option.",
  "limitations_context": "This section only uses approved backend nutrition context.",
  "confidence": "High",
  "reason_codes": ["direct_ollama_report_section_candidate"]
}
""".strip()


def test_json_schema_defines_exact_section_contract():
    assert CANDIDATE_HEALTH_REPORT_SECTION_JSON_SCHEMA["additionalProperties"] is False
    assert set(CANDIDATE_HEALTH_REPORT_SECTION_JSON_SCHEMA["required"]) == {
        "section_summary",
        "key_observations",
        "coaching_interpretation",
        "suggested_focus",
        "limitations_context",
        "confidence",
        "reason_codes",
    }


def test_prompt_contains_strict_json_and_approved_context_rules():
    prompt = build_direct_ollama_health_report_section_prompt(APPROVED_CONTEXT)

    assert "Return JSON only" in prompt
    assert "CandidateHealthReportSection allowed output schema" in prompt
    assert "Approved context JSON" in prompt
    assert "Quote numbers only when those exact values appear" in prompt
    assert "Do not invent targets" in prompt
    assert "Do not create meal plans" in prompt


def test_direct_ollama_report_section_spike_valid_output_approves():
    captured: dict[str, object] = {}

    def fake_generate(
        base_url,
        selected_model,
        prompt,
        response_schema,
        timeout_seconds,
    ):
        captured["base_url"] = base_url
        captured["selected_model"] = selected_model
        captured["prompt"] = prompt
        captured["schema"] = response_schema
        captured["timeout_seconds"] = timeout_seconds
        return _valid_raw_section()

    result = run_direct_ollama_health_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        ollama_base_url="http://ollama.test:11434",
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
    assert result.final_section_source == "provider_approved"
    assert result.extra_keys_detected == []
    assert result.wrapper_object_detected is False
    assert captured["selected_model"] == "qwen2.5:3b"
    assert captured["schema"] == CANDIDATE_HEALTH_REPORT_SECTION_JSON_SCHEMA


def test_direct_ollama_report_section_spike_parse_failure_falls_back():
    def fake_generate(*_args, **_kwargs):
        return '```json\n{"section": {"bad": true}}\n```'

    result = run_direct_ollama_health_report_section_spike(
        model="ollama/gemma3n:e4b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
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


def test_direct_ollama_report_section_spike_extra_keys_fall_back():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Protein is below target.",
  "key_observations": ["Greek Yogurt, Plain is approved."],
  "coaching_interpretation": "Use approved context.",
  "suggested_focus": "Review the Nutrition tab.",
  "limitations_context": "Approved context only.",
  "confidence": "High",
  "reason_codes": ["direct_ollama_report_section_candidate"],
  "extra": "not allowed"
}
""".strip()

    result = run_direct_ollama_health_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        generate=fake_generate,
    )

    assert result.success is False
    assert result.candidate_parse_status == "failed"
    assert result.fallback_reason == "candidate_parse_failure"
    assert result.extra_keys_detected == ["extra"]


def test_direct_ollama_report_section_spike_validation_failure_falls_back():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Targets were changed after calibration was applied.",
  "key_observations": ["The plan now requires 999 grams of protein."],
  "coaching_interpretation": "This treats the backend as mutable.",
  "suggested_focus": "Use this medical advice to fix the issue.",
  "limitations_context": "No limitations.",
  "confidence": "High",
  "reason_codes": ["unsafe_candidate"]
}
""".strip()

    result = run_direct_ollama_health_report_section_spike(
        model="ollama/hermes3:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        generate=fake_generate,
    )

    assert result.success is False
    assert result.candidate_parse_status == "success"
    assert result.candidate_validation_status == "failed"
    assert result.validation_status == "rejected"
    assert result.fallback_reason == "candidate_validation_failure"
    assert result.validation_errors


def test_direct_ollama_report_section_spike_provider_exception_falls_back():
    def fake_generate(*_args, **_kwargs):
        raise RuntimeError("provider unavailable")

    result = run_direct_ollama_health_report_section_spike(
        model="ollama/qwen3:8b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        generate=fake_generate,
    )

    assert result.success is False
    assert result.candidate_parse_status == "not_attempted"
    assert result.fallback_reason == "provider_exception"
    assert result.validation_errors == ["RuntimeError: provider unavailable"]


def test_normalize_model_name_reuses_direct_ollama_helper():
    assert normalize_ollama_model_name("ollama/qwen2.5:3b") == "qwen2.5:3b"
    assert normalize_ollama_model_name("hermes3:3b") == "hermes3:3b"


def test_diagnostics_detect_wrapper_and_extra_keys():
    diagnostics = detect_direct_ollama_section_output_diagnostics(
        '{"response": {"section_summary": "bad"}, "extra": true}'
    )

    assert diagnostics["wrapper_object_detected"] is True
    assert diagnostics["extra_keys_detected"] == ["extra", "response"]
