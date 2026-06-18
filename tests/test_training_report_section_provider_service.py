from __future__ import annotations

from services import training_report_section_provider_service as provider_service
from services.training_report_section_direct_ollama_provider import (
    run_direct_ollama_training_report_section_provider,
)
from services.training_report_section_provider_service import (
    FALLBACK_REASON_APPROVED_CONTEXT_MISSING_TRAINING_EVIDENCE,
    FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE,
    FALLBACK_REASON_DETERMINISTIC_SELECTED,
    FALLBACK_REASON_INVALID_PROVIDER,
    FALLBACK_REASON_PROVIDER_EXCEPTION,
    FINAL_SECTION_SOURCE_DETERMINISTIC,
    FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
    FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED,
    TRAINING_REPORT_SECTION_MODEL_ENV,
    TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    TRAINING_REPORT_SECTION_PROVIDER_ENV,
    build_configured_training_report_section,
    build_configured_training_report_section_with_metadata,
)

APPROVED_CONTEXT = {
    "section": "training",
    "approved_training_quote_context": {
        "approved_workout_names": ["Upper Body Strength"],
        "approved_exercise_names": ["Dumbbell Bench Press"],
        "approved_training_numbers": [1, 2, 3, 8, 10, 50],
        "approved_set_rep_load_rir_values": [
            {
                "workout_name": "Upper Body Strength",
                "exercise_name": "Dumbbell Bench Press",
                "planned_sets": 3,
                "planned_reps": "8-10",
                "planned_rir": "2-3",
                "actual_sets": 1,
                "actual_reps": [10],
                "actual_load_lb": 50,
                "actual_rir": [1],
            }
        ],
        "approved_training_summary_facts": [
            "Upper Body Strength was completed.",
            "Dumbbell Bench Press was planned in Upper Body Strength for 3 sets, 8-10 reps, RIR 2-3.",
            "Dumbbell Bench Press was logged in Upper Body Strength for 1 set.",
            "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
            "The final Dumbbell Bench Press set was logged at 1 RIR.",
        ],
    },
}


EMPTY_EVIDENCE_CONTEXT = {
    "section": "training",
    "approved_training_quote_context": {
        "approved_workout_names": [],
        "approved_exercise_names": [],
        "approved_training_summary_facts": [],
    },
}


def _valid_raw_section() -> str:
    return """
{
  "section_summary": "Dumbbell Bench Press is the lift worth paying attention to from Upper Body Strength.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Keep Dumbbell Bench Press as the reference point and continue logging load, reps, and RIR.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()


def test_training_report_section_provider_defaults_to_deterministic(monkeypatch):
    monkeypatch.delenv(TRAINING_REPORT_SECTION_PROVIDER_ENV, raising=False)

    result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
    )

    assert result.approved_section.section == "training"
    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC
    assert result.runtime_metadata.user_id == 102
    assert result.runtime_metadata.report_date == "2026-06-06"
    assert result.runtime_metadata.configured_provider == "deterministic"
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.provider_attempted is False
    assert result.runtime_metadata.fallback_used is False
    assert (
        result.runtime_metadata.fallback_reason
        == FALLBACK_REASON_DETERMINISTIC_SELECTED
    )


def test_training_report_section_public_builder_returns_section(monkeypatch):
    monkeypatch.delenv(TRAINING_REPORT_SECTION_PROVIDER_ENV, raising=False)
    monkeypatch.setattr(
        "services.training_report_section_provider_service.build_training_report_section_context",
        lambda **_kwargs: APPROVED_CONTEXT,
    )

    section = build_configured_training_report_section(
        user_id=102,
        report_date="2026-06-06",
    )

    assert section.section == "training"
    assert section.source == FINAL_SECTION_SOURCE_DETERMINISTIC


def test_training_report_section_invalid_provider_falls_back(monkeypatch):
    monkeypatch.setenv(TRAINING_REPORT_SECTION_PROVIDER_ENV, "bad_provider")

    result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.user_id == 102
    assert result.runtime_metadata.report_date == "2026-06-06"
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == FALLBACK_REASON_INVALID_PROVIDER
    assert "Unsupported provider" in result.runtime_metadata.validation_errors[0]


def test_training_report_section_direct_ollama_valid_output_approves(monkeypatch):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    monkeypatch.setenv(TRAINING_REPORT_SECTION_MODEL_ENV, "ollama/qwen2.5:3b")
    captured: dict[str, object] = {}

    def fake_generate(
        base_url, selected_model, prompt, response_schema, timeout_seconds
    ):
        captured["selected_model"] = selected_model
        captured["prompt"] = prompt
        captured["response_schema"] = response_schema
        captured["timeout_seconds"] = timeout_seconds
        return _valid_raw_section()

    result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED
    assert "Upper Body Strength" in result.approved_section.section_summary
    assert result.runtime_metadata.user_id == 102
    assert result.runtime_metadata.report_date == "2026-06-06"
    assert result.runtime_metadata.configured_provider == "direct_ollama"
    assert result.runtime_metadata.selected_provider == "direct_ollama"
    assert result.runtime_metadata.configured_model == "ollama/qwen2.5:3b"
    assert result.runtime_metadata.selected_model == "qwen2.5:3b"
    assert result.runtime_metadata.provider_attempted is True
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "success"
    assert result.runtime_metadata.validation_status == "approved"
    assert result.runtime_metadata.final_section_source == "direct_ollama_approved"
    assert result.runtime_metadata.required_anchor_count == 2
    assert result.runtime_metadata.missing_required_anchor_count == 0
    assert "Dumbbell Bench Press was logged at 50 lb for 10 reps." in (
        result.runtime_metadata.matched_required_fact_anchors
    )
    assert (
        result.runtime_metadata.model_facing_quote_context["required_anchor_count"] == 2
    )
    assert captured["selected_model"] == "qwen2.5:3b"


def test_training_report_section_direct_ollama_validation_failure_falls_back(
    monkeypatch,
):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a checkpoint.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Upper Body Strength showed controlled execution.",
  "fatigue_recovery_interpretation": "Upper Body Strength recovery status looks fine.",
  "suggested_focus": "Review the execution data.",
  "limitations_context": "Upper Body Strength remains limited.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.fallback_used is True
    assert (
        result.runtime_metadata.fallback_reason
        == FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE
    )
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "failed"
    assert result.runtime_metadata.validation_status == "rejected"
    assert any(
        "form or control" in error
        for error in result.runtime_metadata.validation_errors
    )
    assert any(
        "fatigue or recovery" in error
        for error in result.runtime_metadata.validation_errors
    )


def test_training_report_section_direct_ollama_exception_falls_back(monkeypatch):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    def fake_generate(*_args, **_kwargs):
        raise RuntimeError("ollama unavailable")

    result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == FALLBACK_REASON_PROVIDER_EXCEPTION
    assert result.runtime_metadata.user_id == 102
    assert result.runtime_metadata.report_date == "2026-06-06"
    assert result.runtime_metadata.provider_attempted is True
    assert result.runtime_metadata.candidate_valid is False


def test_training_report_section_provider_name_is_case_insensitive(monkeypatch):
    monkeypatch.setenv(TRAINING_REPORT_SECTION_PROVIDER_ENV, "DIRECT_OLLAMA")

    result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=lambda *_args, **_kwargs: _valid_raw_section(),
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED
    assert result.runtime_metadata.configured_provider == "direct_ollama"


def test_training_report_section_direct_ollama_empty_evidence_does_not_call_provider(
    monkeypatch,
):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    provider_calls = {"count": 0}

    def fake_generate(*_args, **_kwargs):
        provider_calls["count"] += 1
        raise AssertionError("provider should not be called without approved evidence")

    result = build_configured_training_report_section_with_metadata(
        user_id=105,
        report_date="2026-06-06",
        approved_context=EMPTY_EVIDENCE_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert provider_calls["count"] == 0
    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.provider_attempted is False
    assert result.runtime_metadata.user_id == 105
    assert result.runtime_metadata.report_date == "2026-06-06"
    assert result.runtime_metadata.fallback_used is True
    assert (
        result.runtime_metadata.fallback_reason
        == FALLBACK_REASON_APPROVED_CONTEXT_MISSING_TRAINING_EVIDENCE
    )
    assert result.runtime_metadata.candidate_parse_status == "not_attempted"
    assert result.runtime_metadata.candidate_validation_status == "failed"
    assert result.runtime_metadata.validation_status == "rejected"


def test_training_report_section_direct_ollama_parse_failure_falls_back(monkeypatch):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=lambda *_args, **_kwargs: "not json",
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.provider_attempted is True
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "candidate_parse_failure"
    assert result.runtime_metadata.candidate_parse_status == "failed"
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"
    assert result.runtime_metadata.raw_output_length == len("not json")


def test_training_report_section_direct_ollama_placeholder_output_falls_back(
    monkeypatch,
):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Training Detail is available for Upper Body Strength.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Keep Dumbbell Bench Press as the reference point and continue logging load, reps, and RIR.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.fallback_used is True
    assert (
        result.runtime_metadata.fallback_reason
        == FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE
    )
    assert any(
        "placeholder training context" in error
        for error in result.runtime_metadata.validation_errors
    )


def test_training_report_section_direct_ollama_angle_bracket_output_falls_back(
    monkeypatch,
):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Dumbbell Bench Press is the lift worth paying attention to from <Upper Body Strength>.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Keep Dumbbell Bench Press as the reference point and continue logging load, reps, and RIR.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.fallback_used is True
    assert (
        result.runtime_metadata.fallback_reason
        == FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE
    )
    assert any(
        "angle-bracket template artifacts" in error
        for error in result.runtime_metadata.validation_errors
    )


def test_training_report_section_public_section_does_not_include_raw_output(
    monkeypatch,
):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=lambda *_args, **_kwargs: _valid_raw_section(),
    )

    public_payload = result.approved_section.to_dict()

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED
    assert "raw_output_length" not in public_payload
    assert "raw_output_preview_truncated" not in public_payload
    assert "model_facing_quote_context" not in public_payload
    assert result.runtime_metadata.raw_output_length is not None
    assert result.runtime_metadata.provider_latency_ms is not None


def test_training_report_section_service_uses_formal_direct_ollama_provider_module():
    assert (
        provider_service.run_direct_ollama_training_report_section_provider
        is run_direct_ollama_training_report_section_provider
    )
    assert (
        provider_service.run_direct_ollama_training_report_section_provider.__module__
        == "services.training_report_section_direct_ollama_provider"
    )


def test_training_report_section_runtime_metadata_is_self_contained_on_approved_provider(
    monkeypatch,
):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=lambda *_args, **_kwargs: _valid_raw_section(),
    )

    payload = result.runtime_metadata.to_debug_dict()

    assert payload["user_id"] == 102
    assert payload["report_date"] == "2026-06-06"
    assert payload["provider_attempted"] is True
    assert payload["fallback_used"] is False
    assert payload["final_section_source"] == "direct_ollama_approved"


def test_training_report_section_runtime_metadata_is_self_contained_on_fallback(
    monkeypatch,
):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    result = build_configured_training_report_section_with_metadata(
        user_id=105,
        report_date="2026-06-06",
        approved_context=EMPTY_EVIDENCE_CONTEXT,
        direct_ollama_generate=lambda *_args, **_kwargs: _valid_raw_section(),
    )

    payload = result.runtime_metadata.to_debug_dict()

    assert payload["user_id"] == 105
    assert payload["report_date"] == "2026-06-06"
    assert payload["provider_attempted"] is False
    assert payload["fallback_used"] is True
    assert payload["final_section_source"] == "deterministic_fallback"
