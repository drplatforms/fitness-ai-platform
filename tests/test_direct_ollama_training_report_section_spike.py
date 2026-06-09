from __future__ import annotations

from scripts.spike_direct_ollama_training_report_section import (
    CANDIDATE_TRAINING_REPORT_SECTION_JSON_SCHEMA,
    build_direct_ollama_training_report_section_prompt,
    detect_direct_ollama_training_section_output_diagnostics,
    normalize_ollama_model_name,
    run_direct_ollama_training_report_section_spike,
)

APPROVED_CONTEXT = {
    "section": "training",
    "training_state": {
        "workout_summary": "2 recent workouts logged.",
        "workout_count": 2,
        "training_load": "Moderate",
        "recovery_demand": "Normal",
        "avg_rir": 2,
    },
    "recovery_constraints": {
        "recovery_score": 82,
        "fatigue_risk": "Low",
        "readiness_level": "High",
    },
    "training_execution_summary": {
        "completed_execution_count": 1,
        "average_completion_percentage": 100,
        "average_planned_rir": 2,
        "average_actual_rir": 1,
        "average_rir_deviation": -1,
        "execution_quality": "limited_execution_data",
        "execution_effort_trend": "harder_than_planned",
        "confidence": "Low",
        "reason_codes": ["single_completed_execution_limited_confidence"],
    },
    "recent_training_executions": [
        {
            "workout_title": "Upper Body Strength",
            "completed_at": "2026-06-06T12:00:00",
            "planned_exercises": [
                {
                    "exercise_name": "Dumbbell Bench Press",
                    "planned_sets": 3,
                    "planned_reps_min": 8,
                    "planned_reps_max": 10,
                    "planned_rir_min": 2,
                    "planned_rir_max": 3,
                }
            ],
            "actual_sets": [
                {
                    "exercise_name": "Dumbbell Bench Press",
                    "set_number": 1,
                    "planned_reps_min": 8,
                    "planned_reps_max": 10,
                    "planned_rir_min": 2,
                    "planned_rir_max": 3,
                    "actual_reps": 10,
                    "actual_weight": 50,
                    "actual_rir": 1,
                    "completed": True,
                    "skipped": False,
                }
            ],
        }
    ],
}


def _valid_raw_section() -> str:
    return """
{
  "section_summary": "Upper Body Strength has one approved completed execution for review.",
  "key_observations": [
    "Dumbbell Bench Press was logged with 10 reps at 50 weight on set 1.",
    "Average actual RIR was 1 compared with the approved planned RIR context."
  ],
  "performance_interpretation": "The approved data points to harder-than-planned effort in a limited training sample.",
  "fatigue_recovery_interpretation": "Low fatigue risk and High readiness support cautious continuation without adding unapproved work.",
  "suggested_focus": "Keep logging Upper Body Strength details so the next review has more than 1 completed execution.",
  "limitations_context": "This section only uses approved planned-vs-actual training context.",
  "confidence": "Low",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()


def test_json_schema_defines_exact_training_section_contract():
    assert (
        CANDIDATE_TRAINING_REPORT_SECTION_JSON_SCHEMA["additionalProperties"] is False
    )
    assert set(CANDIDATE_TRAINING_REPORT_SECTION_JSON_SCHEMA["required"]) == {
        "section_summary",
        "key_observations",
        "performance_interpretation",
        "fatigue_recovery_interpretation",
        "suggested_focus",
        "limitations_context",
        "confidence",
        "reason_codes",
    }


def test_prompt_contains_strict_json_and_training_grounding_rules():
    prompt = build_direct_ollama_training_report_section_prompt(APPROVED_CONTEXT)

    assert "Return JSON only" in prompt
    assert "CandidateTrainingReportSection allowed output schema" in prompt
    assert "Approved context JSON" in prompt
    assert "Mention workout names only when they appear" in prompt
    assert "Mention exercise names only when they appear" in prompt
    assert "Do not invent workouts" in prompt
    assert (
        "Do not invent exact workout, exercise, set, rep, load, weight, or RIR"
        in prompt
    )


def test_direct_ollama_training_section_spike_valid_output_approves():
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

    result = run_direct_ollama_training_report_section_spike(
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
    assert captured["schema"] == CANDIDATE_TRAINING_REPORT_SECTION_JSON_SCHEMA


def test_direct_ollama_training_section_spike_markdown_parse_failure_falls_back():
    def fake_generate(*_args, **_kwargs):
        return '```json\n{"section": {"bad": true}}\n```'

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/hermes3:3b",
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


def test_direct_ollama_training_section_spike_extra_keys_fall_back():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength was logged.",
  "key_observations": ["Dumbbell Bench Press is approved."],
  "performance_interpretation": "Use approved context.",
  "fatigue_recovery_interpretation": "Use approved recovery context.",
  "suggested_focus": "Review the approved training details.",
  "limitations_context": "Approved context only.",
  "confidence": "Low",
  "reason_codes": ["direct_ollama_training_report_section_candidate"],
  "extra": "not allowed"
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
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


def test_direct_ollama_training_section_spike_unapproved_numbers_fail_validation():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength needs a jump to 200 pounds next time.",
  "key_observations": ["Dumbbell Bench Press was logged."],
  "performance_interpretation": "The data supports increasing load.",
  "fatigue_recovery_interpretation": "Recovery is fine for more load.",
  "suggested_focus": "Increase the load next session.",
  "limitations_context": "No limitations.",
  "confidence": "High",
  "reason_codes": ["unsafe_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
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
    assert any("numbers not present" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_unapproved_exercise_fails_validation():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength was completed, but Barbell Deadlift should drive the next review.",
  "key_observations": ["Dumbbell Bench Press was logged."],
  "performance_interpretation": "Barbell Deadlift is the main lift signal.",
  "fatigue_recovery_interpretation": "Recovery context is bounded.",
  "suggested_focus": "Keep logging approved training details.",
  "limitations_context": "Approved context only.",
  "confidence": "Low",
  "reason_codes": ["unsafe_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        generate=fake_generate,
    )

    assert result.success is False
    assert result.candidate_validation_status == "failed"
    assert any(
        "unapproved workout or exercise" in error for error in result.validation_errors
    )


def test_direct_ollama_training_section_spike_generic_copy_fails_when_details_exist():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Training data is available for review.",
  "key_observations": ["Workout details are available."],
  "performance_interpretation": "Use the approved training data.",
  "fatigue_recovery_interpretation": "Recovery data is available.",
  "suggested_focus": "Review the approved training context.",
  "limitations_context": "Approved context only.",
  "confidence": "Low",
  "reason_codes": ["generic_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        generate=fake_generate,
    )

    assert result.success is False
    assert result.candidate_validation_status == "failed"
    assert any("vague training copy" in error for error in result.validation_errors)
    assert any("must mention" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_provider_exception_falls_back():
    def fake_generate(*_args, **_kwargs):
        raise RuntimeError("provider unavailable")

    result = run_direct_ollama_training_report_section_spike(
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
    diagnostics = detect_direct_ollama_training_section_output_diagnostics(
        '{"response": {"section_summary": "bad"}, "extra": true}'
    )

    assert diagnostics["wrapper_object_detected"] is True
    assert diagnostics["extra_keys_detected"] == ["extra", "response"]
