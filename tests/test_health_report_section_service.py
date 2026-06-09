from __future__ import annotations

from services.health_report_section_service import (
    CANDIDATE_HEALTH_REPORT_SECTION_JSON_SCHEMA,
    FALLBACK_REASON_CANDIDATE_PARSE_FAILURE,
    FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE,
    FINAL_SECTION_SOURCE_DETERMINISTIC,
    FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
    FINAL_SECTION_SOURCE_PROVIDER_APPROVED,
    HEALTH_REPORT_SECTION_MODEL_ENV,
    HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    HEALTH_REPORT_SECTION_PROVIDER_ENV,
    build_configured_nutrition_health_report_section_with_metadata,
    build_direct_ollama_health_report_section_prompt,
    detect_direct_ollama_section_output_diagnostics,
    normalize_ollama_model_name,
    parse_candidate_health_report_section_payload,
)

APPROVED_CONTEXT = {
    "section": "nutrition",
    "report_date": "2026-06-06",
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


def test_section_schema_defines_exact_candidate_contract():
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


def test_prompt_contains_strict_json_and_source_of_truth_rules():
    prompt = build_direct_ollama_health_report_section_prompt(APPROVED_CONTEXT)

    assert "Return JSON only" in prompt
    assert "CandidateHealthReportSection allowed output schema" in prompt
    assert "Approved context JSON" in prompt
    assert "Quote numbers only when those exact values appear" in prompt
    assert "Mention foods only when they appear" in prompt
    assert "Do not invent targets" in prompt
    assert "Do not create meal plans" in prompt


def test_deterministic_provider_is_default(monkeypatch):
    monkeypatch.delenv(HEALTH_REPORT_SECTION_PROVIDER_ENV, raising=False)

    result = build_configured_nutrition_health_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
    )

    assert result.approved_section.section == "nutrition"
    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC
    assert result.runtime_metadata.configured_provider == "deterministic"
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.provider_attempted is False
    assert result.runtime_metadata.fallback_used is False


def test_direct_ollama_provider_valid_output_approves(monkeypatch):
    monkeypatch.setenv(
        HEALTH_REPORT_SECTION_PROVIDER_ENV,
        HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    monkeypatch.setenv(HEALTH_REPORT_SECTION_MODEL_ENV, "ollama/qwen2.5:3b")
    captured: dict[str, object] = {}

    def fake_generate(
        base_url, selected_model, prompt, response_schema, timeout_seconds
    ):
        captured["selected_model"] = selected_model
        captured["prompt"] = prompt
        captured["schema"] = response_schema
        captured["timeout_seconds"] = timeout_seconds
        return _valid_raw_section()

    result = build_configured_nutrition_health_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_PROVIDER_APPROVED
    assert result.runtime_metadata.configured_provider == "direct_ollama"
    assert result.runtime_metadata.selected_provider == "direct_ollama"
    assert result.runtime_metadata.configured_model == "ollama/qwen2.5:3b"
    assert result.runtime_metadata.selected_model == "qwen2.5:3b"
    assert result.runtime_metadata.provider_attempted is True
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "success"
    assert result.runtime_metadata.validation_status == "approved"
    assert result.runtime_metadata.final_section_source == "provider_approved"
    assert captured["selected_model"] == "qwen2.5:3b"
    assert captured["schema"] == CANDIDATE_HEALTH_REPORT_SECTION_JSON_SCHEMA


def test_malformed_json_falls_back(monkeypatch):
    monkeypatch.setenv(
        HEALTH_REPORT_SECTION_PROVIDER_ENV,
        HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    def fake_generate(*_args, **_kwargs):
        return "not json"

    result = build_configured_nutrition_health_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.fallback_used is True
    assert (
        result.runtime_metadata.fallback_reason
        == FALLBACK_REASON_CANDIDATE_PARSE_FAILURE
    )
    assert result.runtime_metadata.candidate_parse_status == "failed"
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"


def test_markdown_wrapped_output_falls_back(monkeypatch):
    monkeypatch.setenv(
        HEALTH_REPORT_SECTION_PROVIDER_ENV,
        HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    def fake_generate(*_args, **_kwargs):
        return f"```json\n{_valid_raw_section()}\n```"

    result = build_configured_nutrition_health_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.runtime_metadata.fallback_used is True
    assert (
        result.runtime_metadata.fallback_reason
        == FALLBACK_REASON_CANDIDATE_PARSE_FAILURE
    )
    assert result.runtime_metadata.markdown_wrapper_detected is True


def test_wrapper_object_output_falls_back(monkeypatch):
    monkeypatch.setenv(
        HEALTH_REPORT_SECTION_PROVIDER_ENV,
        HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    def fake_generate(*_args, **_kwargs):
        return '{"response": {"section_summary": "bad"}}'

    result = build_configured_nutrition_health_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.wrapper_object_detected is True
    assert result.runtime_metadata.extra_keys_detected == ["response"]


def test_extra_key_output_falls_back(monkeypatch):
    monkeypatch.setenv(
        HEALTH_REPORT_SECTION_PROVIDER_ENV,
        HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    def fake_generate(*_args, **_kwargs):
        return _valid_raw_section().replace(
            '"reason_codes": ["direct_ollama_report_section_candidate"]',
            '"reason_codes": ["direct_ollama_report_section_candidate"], "extra": true',
        )

    result = build_configured_nutrition_health_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.runtime_metadata.fallback_used is True
    assert (
        result.runtime_metadata.fallback_reason
        == FALLBACK_REASON_CANDIDATE_PARSE_FAILURE
    )
    assert result.runtime_metadata.extra_keys_detected == ["extra"]


def test_missing_field_output_falls_back(monkeypatch):
    monkeypatch.setenv(
        HEALTH_REPORT_SECTION_PROVIDER_ENV,
        HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    def fake_generate(*_args, **_kwargs):
        payload = parse_candidate_health_report_section_payload(_valid_raw_section())
        payload.pop("suggested_focus")
        return __import__("json").dumps(payload)

    result = build_configured_nutrition_health_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.runtime_metadata.fallback_used is True
    assert (
        result.runtime_metadata.fallback_reason
        == FALLBACK_REASON_CANDIDATE_PARSE_FAILURE
    )


def test_validation_failure_falls_back(monkeypatch):
    monkeypatch.setenv(
        HEALTH_REPORT_SECTION_PROVIDER_ENV,
        HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Targets were changed after calibration was applied.",
  "key_observations": ["The plan now requires 999 grams of protein."],
  "coaching_interpretation": "This gives medical advice.",
  "suggested_focus": "Use this treatment plan.",
  "limitations_context": "No limitations.",
  "confidence": "High",
  "reason_codes": ["unsafe_candidate"]
}
""".strip()

    result = build_configured_nutrition_health_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.runtime_metadata.fallback_used is True
    assert (
        result.runtime_metadata.fallback_reason
        == FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE
    )
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "failed"
    assert result.runtime_metadata.validation_status == "rejected"
    assert result.runtime_metadata.validation_errors


def test_invalid_provider_falls_back_to_deterministic(monkeypatch):
    monkeypatch.setenv(HEALTH_REPORT_SECTION_PROVIDER_ENV, "nonsense")

    result = build_configured_nutrition_health_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "invalid_provider"


def test_diagnostics_detect_wrapper_and_extra_keys():
    diagnostics = detect_direct_ollama_section_output_diagnostics(
        '{"response": {"section_summary": "bad"}, "extra": true}'
    )

    assert diagnostics["wrapper_object_detected"] is True
    assert diagnostics["extra_keys_detected"] == ["extra", "response"]


def test_normalize_model_name_reuses_direct_ollama_helper():
    assert normalize_ollama_model_name("ollama/qwen2.5:3b") == "qwen2.5:3b"
    assert normalize_ollama_model_name("hermes3:3b") == "hermes3:3b"
