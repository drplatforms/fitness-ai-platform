from __future__ import annotations

from scripts.spike_direct_ollama_training_report_section import (
    CANDIDATE_TRAINING_REPORT_SECTION_JSON_SCHEMA,
    build_approved_training_quote_context,
    build_direct_ollama_training_report_section_prompt,
    build_training_report_section_model_quote_context,
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


def _valid_raw_section() -> str:
    return """
{
  "section_summary": "Upper Body Strength has one approved completed execution for review.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Upper Body Strength has one approved Dumbbell Bench Press set for cautious review.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press effort review should stay limited to the logged 1 RIR set.",
  "suggested_focus": "Keep logging Upper Body Strength details so the next review has more than 1 completed execution.",
  "limitations_context": "Upper Body Strength review uses only Dumbbell Bench Press planned-vs-actual details.",
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
    assert "Use these exact training details first" in prompt
    assert "Required training details" in prompt
    assert "Approved context JSON" not in prompt
    assert "Quote-only model-facing context JSON" not in prompt
    assert "Allowed workout names" in prompt
    assert "Allowed exercise names" in prompt
    assert "Allowed supporting training details" in prompt
    assert "Required quote" in prompt
    assert "Do not mention user ID" in prompt
    assert "key_observations[0] must be exactly one required training detail" in prompt
    assert "approved quote facts" not in prompt
    assert "approved facts" not in prompt
    assert "bounded training summary" not in prompt
    assert "Do not calculate or infer volume load" in prompt
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
    assert result.approved_training_quote_context["approved_workout_names"] == [
        "Upper Body Strength"
    ]
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


def test_approved_training_quote_context_builder_exposes_bounded_quoteable_values():
    quote_context = build_approved_training_quote_context(
        recent_training_executions=APPROVED_CONTEXT["recent_training_executions"],
        training_execution_summary=APPROVED_CONTEXT["training_execution_summary"],
    ).to_dict()

    assert quote_context["approved_workout_names"] == ["Upper Body Strength"]
    assert quote_context["approved_exercise_names"] == ["Dumbbell Bench Press"]
    assert 50 in quote_context["approved_training_numbers"]
    assert 10 in quote_context["approved_training_numbers"]
    assert quote_context["approved_set_rep_load_rir_values"][0]["actual_load_lb"] == 50
    assert any(
        "Dumbbell Bench Press was logged at 50 lb for 10 reps" in fact
        for fact in quote_context["approved_training_summary_facts"]
    )
    assert "raw_notes" not in str(quote_context).lower()


def test_model_facing_quote_only_payload_excludes_broad_context_and_metadata():
    payload = build_training_report_section_model_quote_context(
        APPROVED_CONTEXT
    ).to_dict()

    assert payload["required_quote_name"] == "Upper Body Strength"
    assert payload["approved_workout_names"] == ["Upper Body Strength"]
    assert payload["approved_exercise_names"] == ["Dumbbell Bench Press"]
    assert (
        "Dumbbell Bench Press was logged at 50 lb for 10 reps."
        in payload["supporting_training_details"]
    )
    assert 50 in payload["approved_training_numbers"]
    assert "coaching_intent" in payload
    assert "tone_guidance" in payload

    serialized = str(payload).lower()
    assert "user_id" not in serialized
    assert "report_date" not in serialized
    assert "training_state" not in serialized
    assert "training_execution_summary" not in serialized
    assert "recent_training_executions" not in serialized
    assert "actual_sets" not in serialized
    assert "completed_at" not in serialized
    assert "provider" not in serialized
    assert "runtime" not in serialized


def test_prompt_uses_quote_only_payload_not_full_backend_context():
    captured: dict[str, object] = {}

    def fake_generate(_base_url, _selected_model, prompt, _schema, _timeout_seconds):
        captured["prompt"] = prompt
        return _valid_raw_section()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        generate=fake_generate,
    )

    assert result.success is True
    prompt = str(captured["prompt"])
    assert "Required training details" in prompt
    assert "Allowed supporting training details" in prompt
    assert "Quote-only model-facing context JSON" not in prompt
    assert "Approved context JSON" not in prompt
    assert '"training_state"' not in prompt
    assert '"training_execution_summary"' not in prompt
    assert '"recent_training_executions"' not in prompt
    assert '"user_id"' not in prompt
    assert '"report_date"' not in prompt


def test_prompt_preserves_natural_coach_language_instruction():
    prompt = build_direct_ollama_training_report_section_prompt(APPROVED_CONTEXT)

    assert "Do not merely list details in every field" in prompt
    assert "personal, practical, and specific" in prompt
    assert "prioritize, phrase, and connect exact details naturally" in prompt


def test_direct_ollama_training_section_spike_grounded_coach_like_output_approves():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a narrow but useful signal because Dumbbell Bench Press was logged at 50 lb for 10 reps.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the clearest approved performance detail, so the review should stay focused on that logged set.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press reached 1 RIR on the final logged set, so effort should be interpreted cautiously without adding recovery claims.",
  "suggested_focus": "Use Dumbbell Bench Press logging quality as the next focus before changing training direction.",
  "limitations_context": "Upper Body Strength has limited approved execution detail, so this section avoids broader claims.",
  "confidence": "Low",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        generate=fake_generate,
    )

    assert result.success is True
    assert result.fallback_used is False
    assert result.model_facing_quote_context["required_quote_name"] == (
        "Upper Body Strength"
    )


def test_direct_ollama_training_section_spike_generic_moderate_load_claim_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Training load remains moderate with consistent volume.",
  "key_observations": ["Performance is stable across recent training."],
  "performance_interpretation": "Continue gradual progression.",
  "fatigue_recovery_interpretation": "Recovery interpretation is limited.",
  "suggested_focus": "Keep training consistent.",
  "limitations_context": "Training details are available.",
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
    assert any("vague training copy" in error for error in result.validation_errors)
    assert any("must mention" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_invented_average_rir_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength was reviewed.",
  "key_observations": ["Dumbbell Bench Press was logged."],
  "performance_interpretation": "Average RIR was 3 across the workout.",
  "fatigue_recovery_interpretation": "Recovery interpretation is limited.",
  "suggested_focus": "Keep logging approved training details.",
  "limitations_context": "Approved quote context only.",
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
    assert any("average RIR" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_invented_progression_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength was reviewed.",
  "key_observations": ["Dumbbell Bench Press was logged."],
  "performance_interpretation": "Strength is improving and volume increased by 10%.",
  "fatigue_recovery_interpretation": "Recovery interpretation is limited.",
  "suggested_focus": "Keep logging approved training details.",
  "limitations_context": "Approved quote context only.",
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
    assert any("progression" in error for error in result.validation_errors)


def test_normalize_model_name_reuses_direct_ollama_helper():
    assert normalize_ollama_model_name("ollama/qwen2.5:3b") == "qwen2.5:3b"
    assert normalize_ollama_model_name("hermes3:3b") == "hermes3:3b"


def test_diagnostics_detect_wrapper_and_extra_keys():
    diagnostics = detect_direct_ollama_training_section_output_diagnostics(
        '{"response": {"section_summary": "bad"}, "extra": true}'
    )

    assert diagnostics["wrapper_object_detected"] is True
    assert diagnostics["extra_keys_detected"] == ["extra", "response"]


def test_prompt_places_required_training_details_before_supporting_details():
    prompt = build_direct_ollama_training_report_section_prompt(APPROVED_CONTEXT)

    assert prompt.index("Required training details") < prompt.index(
        "Allowed supporting training details"
    )
    assert prompt.index("Allowed workout names") < prompt.index(
        "Allowed supporting training details"
    )
    assert "Upper Body Strength" in prompt
    assert "Dumbbell Bench Press" in prompt
    assert '"training_state"' not in prompt
    assert '"training_execution_summary"' not in prompt
    assert '"recent_training_executions"' not in prompt
    assert '"user_id"' not in prompt
    assert '"report_date"' not in prompt


def test_direct_ollama_training_section_spike_user_metadata_fails_validation():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Training Execution Summary for User 102 uses Upper Body Strength.",
  "key_observations": ["Dumbbell Bench Press was logged at 50 lb for 10 reps."],
  "performance_interpretation": "Upper Body Strength has approved Dumbbell Bench Press context.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press recovery interpretation is bounded.",
  "suggested_focus": "Keep logging Upper Body Strength details.",
  "limitations_context": "Upper Body Strength context uses approved facts only.",
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
    assert any("user metadata" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_report_date_fails_validation():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength on June 6th included approved training context.",
  "key_observations": ["Dumbbell Bench Press was logged at 50 lb for 10 reps."],
  "performance_interpretation": "Upper Body Strength has approved Dumbbell Bench Press context.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press recovery interpretation is bounded.",
  "suggested_focus": "Keep logging Upper Body Strength details.",
  "limitations_context": "Upper Body Strength context uses approved facts only.",
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
    assert any("report dates" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_completion_count_fails_validation():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength had 4 out of 5 workouts completed as planned.",
  "key_observations": ["Dumbbell Bench Press was logged at 50 lb for 10 reps."],
  "performance_interpretation": "Upper Body Strength has approved Dumbbell Bench Press context.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press recovery interpretation is bounded.",
  "suggested_focus": "Keep logging Upper Body Strength details.",
  "limitations_context": "Upper Body Strength context uses approved facts only.",
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
    assert any("completion-count" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_adherence_claim_fails_validation():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength shows high adherence.",
  "key_observations": ["Dumbbell Bench Press was logged at 50 lb for 10 reps."],
  "performance_interpretation": "Upper Body Strength adherence is high with approved Dumbbell Bench Press context.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press recovery interpretation is bounded.",
  "suggested_focus": "Keep logging Upper Body Strength details.",
  "limitations_context": "Upper Body Strength context uses approved facts only.",
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
    assert any("adherence" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_skipped_claim_fails_validation():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength had one skipped exercise.",
  "key_observations": ["Dumbbell Bench Press was logged at 50 lb for 10 reps."],
  "performance_interpretation": "Upper Body Strength has approved Dumbbell Bench Press context.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press recovery interpretation is bounded.",
  "suggested_focus": "Keep logging Upper Body Strength details.",
  "limitations_context": "Upper Body Strength context uses approved facts only.",
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
    assert any("skipped-exercise" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_trend_claim_fails_validation():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength had a trend toward lower effort.",
  "key_observations": ["Dumbbell Bench Press was logged at 50 lb for 10 reps."],
  "performance_interpretation": "Upper Body Strength is trending with approved Dumbbell Bench Press context.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press recovery interpretation is bounded.",
  "suggested_focus": "Keep logging Upper Body Strength details.",
  "limitations_context": "Upper Body Strength context uses approved facts only.",
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
    assert any("trend" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_each_narrative_field_requires_name():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength has approved context.",
  "key_observations": ["Dumbbell Bench Press was logged at 50 lb for 10 reps."],
  "performance_interpretation": "This interpretation omits the exact name.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press recovery interpretation is bounded.",
  "suggested_focus": "Keep logging Upper Body Strength details.",
  "limitations_context": "Upper Body Strength context uses approved facts only.",
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
    assert any("narrative fields" in error for error in result.validation_errors)


def test_model_facing_quote_payload_includes_required_fact_anchors_and_count():
    payload = build_training_report_section_model_quote_context(
        APPROVED_CONTEXT
    ).to_dict()

    assert payload["required_quote_name"] == "Upper Body Strength"
    assert payload["required_anchor_count"] == 2
    assert payload["required_fact_anchors"][:3] == [
        "Upper Body Strength",
        "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
        "The final Dumbbell Bench Press set was logged at 1 RIR.",
    ]
    assert "forbidden_meta_terms" not in payload


def test_required_fact_anchors_prefer_concrete_facts_over_completion_fact():
    payload = build_training_report_section_model_quote_context(
        APPROVED_CONTEXT
    ).to_dict()

    assert "Upper Body Strength was completed." not in payload["required_fact_anchors"]
    assert payload["required_fact_anchors"].index(
        "Dumbbell Bench Press was logged at 50 lb for 10 reps."
    ) < payload["required_fact_anchors"].index(
        "Dumbbell Bench Press was logged in Upper Body Strength for 1 set."
    )


def test_required_anchor_count_is_zero_when_no_anchors_exist():
    payload = build_training_report_section_model_quote_context(
        {"approved_training_quote_context": {}}
    ).to_dict()

    assert payload["required_quote_name"] is None
    assert payload["required_fact_anchors"] == []
    assert payload["required_anchor_count"] == 0


def test_required_anchor_count_is_one_when_one_anchor_exists():
    payload = build_training_report_section_model_quote_context(
        {
            "approved_training_quote_context": {
                "approved_workout_names": ["Single Anchor Session"],
                "approved_exercise_names": [],
                "approved_training_numbers": [],
                "approved_set_rep_load_rir_values": [],
                "approved_training_summary_facts": [],
            }
        }
    ).to_dict()

    assert payload["required_fact_anchors"] == ["Single Anchor Session"]
    assert payload["required_anchor_count"] == 1


def test_prompt_includes_required_training_details_and_anchor_count():
    prompt = build_direct_ollama_training_report_section_prompt(APPROVED_CONTEXT)

    assert "Required training details" in prompt
    assert "at least 2 exact required training detail" in prompt
    assert "Dumbbell Bench Press was logged at 50 lb for 10 reps." in prompt
    assert "The final Dumbbell Bench Press set was logged at 1 RIR." in prompt
    assert "Forbidden meta-language" not in prompt
    assert "approved quote facts" not in prompt
    assert "approved facts" not in prompt
    assert "bounded training summary" not in prompt


def test_direct_ollama_training_section_spike_one_anchor_fails_when_two_required():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a useful but narrow signal.",
  "key_observations": ["Upper Body Strength should stay grounded in the logged detail."],
  "performance_interpretation": "Upper Body Strength is the main approved name in this section.",
  "fatigue_recovery_interpretation": "Upper Body Strength should be interpreted cautiously.",
  "suggested_focus": "Keep logging Upper Body Strength details before changing direction.",
  "limitations_context": "Upper Body Strength has limited detail for this section.",
  "confidence": "Low",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
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
    assert any(
        "exact required fact anchor" in error for error in result.validation_errors
    )


def test_direct_ollama_training_section_spike_fuzzy_anchor_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a useful Dumbbell Bench Press signal.",
  "key_observations": ["Dumbbell Bench Press used 50 lb for 10 reps."],
  "performance_interpretation": "Dumbbell Bench Press is the clearest detail from Upper Body Strength.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press effort should be reviewed cautiously.",
  "suggested_focus": "Use Upper Body Strength details before changing direction.",
  "limitations_context": "Upper Body Strength has limited Dumbbell Bench Press detail.",
  "confidence": "Low",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
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
    assert any(
        "exact required fact anchor" in error for error in result.validation_errors
    )


def test_direct_ollama_training_section_spike_meta_copy_fails_validation():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength is based on the provided facts.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press should be interpreted from approved quote facts.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press review should avoid extra claims.",
  "suggested_focus": "Use Upper Body Strength details before changing direction.",
  "limitations_context": "Upper Body Strength has a bounded training summary.",
  "confidence": "Low",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
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
    assert any("meta-copy" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_completed_as_planned_fails_with_anchors():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength was completed as planned.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the clearest approved performance detail.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press effort should stay tied to the logged 1 RIR set.",
  "suggested_focus": "Use Upper Body Strength details before changing direction.",
  "limitations_context": "Upper Body Strength has limited Dumbbell Bench Press execution detail.",
  "confidence": "Low",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
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
    assert any("completion-count" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_approved_anchors_and_coach_interpretation_passes():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a specific effort signal because Dumbbell Bench Press was logged at 50 lb for 10 reps.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the clearest performance anchor from Upper Body Strength, so the review should stay focused on that logged work.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press reached 1 RIR on the final logged set, so effort should be reviewed without adding recovery claims.",
  "suggested_focus": "Use Upper Body Strength logging quality as the next focus before changing training direction.",
  "limitations_context": "Upper Body Strength has limited Dumbbell Bench Press execution detail, so this section avoids broader claims.",
  "confidence": "Low",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        generate=fake_generate,
    )

    assert result.success is True
    assert result.candidate_validation_status == "success"


def test_direct_ollama_training_section_spike_two_anchors_not_in_required_observations_fail():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength includes Dumbbell Bench Press was logged at 50 lb for 10 reps.",
  "key_observations": [
    "Upper Body Strength should be reviewed from logged details.",
    "Dumbbell Bench Press should stay grounded in logged details."
  ],
  "performance_interpretation": "The final Dumbbell Bench Press set was logged at 1 RIR, so Upper Body Strength should be interpreted cautiously.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press effort should be discussed without adding recovery claims.",
  "suggested_focus": "Use Upper Body Strength logging detail before changing training direction.",
  "limitations_context": "Upper Body Strength has limited Dumbbell Bench Press execution detail, so broader claims are avoided.",
  "confidence": "Low",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
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
    assert any("key_observations[0]" in error for error in result.validation_errors)
    assert any("key_observations[1]" in error for error in result.validation_errors)
    assert len(result.matched_required_fact_anchors) >= 2
    assert result.missing_required_anchor_count == 0


def test_direct_ollama_training_section_spike_planned_facts_do_not_satisfy_required_anchors():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength has planned Dumbbell Bench Press detail for review.",
  "key_observations": [
    "Dumbbell Bench Press was planned in Upper Body Strength for 3 sets, 8-10 reps, RIR 2-3.",
    "Upper Body Strength"
  ],
  "performance_interpretation": "Dumbbell Bench Press planning detail should not replace logged performance detail.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press effort should be discussed without adding recovery claims.",
  "suggested_focus": "Use Upper Body Strength logging detail before changing training direction.",
  "limitations_context": "Upper Body Strength has limited Dumbbell Bench Press execution detail, so broader claims are avoided.",
  "confidence": "Low",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
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
    assert any(
        "exact required fact anchor" in error or "key_observations" in error
        for error in result.validation_errors
    )
    assert result.matched_required_fact_anchors == ["Upper Body Strength"]
    assert result.missing_required_anchor_count == 1


def test_direct_ollama_training_section_spike_exposes_matched_anchor_diagnostics_on_success():
    def fake_generate(*_args, **_kwargs):
        return _valid_raw_section()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=APPROVED_CONTEXT,
        generate=fake_generate,
    )

    assert result.success is True
    assert result.required_anchor_count == 2
    assert result.missing_required_anchor_count == 0
    assert "Dumbbell Bench Press was logged at 50 lb for 10 reps." in (
        result.matched_required_fact_anchors
    )
    assert "The final Dumbbell Bench Press set was logged at 1 RIR." in (
        result.matched_required_fact_anchors
    )
