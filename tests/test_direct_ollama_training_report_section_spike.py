from __future__ import annotations

from copy import deepcopy

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
  "section_summary": "Dumbbell Bench Press is the lift worth paying attention to from Upper Body Strength.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a reference point and keep the next session measured.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
  "confidence": "Low",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()


def _bounded_claims_context() -> dict:
    context = deepcopy(APPROVED_CONTEXT)
    actual_sets = []
    for set_number, rir in [(1, 2), (2, 1), (3, 0)]:
        actual_sets.append(
            {
                "exercise_name": "Dumbbell Bench Press",
                "set_number": set_number,
                "planned_reps_min": 8,
                "planned_reps_max": 10,
                "planned_rir_min": 2,
                "planned_rir_max": 3,
                "actual_reps": 10,
                "actual_weight": 50,
                "actual_rir": rir,
                "completed": True,
                "skipped": False,
            }
        )
    context["recent_training_executions"][0]["actual_sets"] = actual_sets
    context["approved_training_quote_context"] = build_approved_training_quote_context(
        recent_training_executions=context["recent_training_executions"],
        training_execution_summary=context["training_execution_summary"],
    ).to_dict()
    return context


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
  "section_summary": "Upper Body Strength gives a narrow but useful signal through Dumbbell Bench Press.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the clearest approved performance detail, so the review should stay focused on that logged set.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press reached 1 RIR on the final logged set, so effort should be interpreted cautiously without adding recovery claims.",
  "suggested_focus": "Use Dumbbell Bench Press logging quality as the next focus before changing training direction.",
  "limitations_context": "Upper Body Strength has limited Dumbbell Bench Press detail, so broader recovery claims are avoided.",
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
    assert any("planned-work alignment" in error for error in result.validation_errors)


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
    assert any("planned-work alignment" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_approved_anchors_and_coach_interpretation_passes():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a specific effort signal through Dumbbell Bench Press.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the clearest performance anchor from Upper Body Strength, so the review should stay focused on that logged work.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press reached 1 RIR on the final logged set, so effort should be reviewed without adding recovery claims.",
  "suggested_focus": "Use Dumbbell Bench Press as the next reference point before changing training direction.",
  "limitations_context": "Upper Body Strength has limited Dumbbell Bench Press detail, so broader recovery claims are avoided.",
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


def test_model_facing_payload_includes_backend_approved_interpretation_claims():
    payload = build_training_report_section_model_quote_context(
        APPROVED_CONTEXT
    ).to_dict()

    assert "approved_interpretation_claims" in payload
    assert any(
        "clearest training signal" in claim
        for claim in payload["approved_interpretation_claims"]
    )
    assert any(
        "No conclusion about form quality" in claim
        for claim in payload["approved_interpretation_claims"]
    )
    assert any(
        "planned-work alignment" in claim
        for claim in payload["approved_interpretation_claims"]
    )


def test_prompt_separates_required_details_from_allowed_interpretation_claims():
    prompt = build_direct_ollama_training_report_section_prompt(APPROVED_CONTEXT)

    assert "Required training details" in prompt
    assert "Allowed interpretation claims" in prompt
    assert "Approved semantic coaching moves" in prompt
    assert "Interpretation fields may only express" in prompt
    assert "Do not create new conclusions" in prompt
    assert prompt.index("Required training details") < prompt.index(
        "Allowed interpretation claims"
    )
    assert prompt.index("Allowed interpretation claims") < prompt.index(
        "Approved semantic coaching moves"
    )
    assert prompt.index("Approved semantic coaching moves") < prompt.index(
        "Allowed supporting training details"
    )


def test_direct_ollama_training_section_spike_approved_interpretation_claim_passes():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Dumbbell Bench Press is the lift worth paying attention to from Upper Body Strength.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Upper Body Strength has its clearest training signal in lifts with recorded loads and reps.",
  "fatigue_recovery_interpretation": "Upper Body Strength note: This is enough to guide the next training choice, but not enough to make broad claims about recovery or progression.",
  "suggested_focus": "Dumbbell Bench Press next focus: keep the next training choice measured rather than adding more intensity immediately.",
  "limitations_context": "Dumbbell Bench Press limitation: one workout is not enough for a full form, recovery, or trend picture.",
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
    assert result.matched_approved_interpretation_claims


def test_direct_ollama_training_section_spike_consistent_effort_claim_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a specific Dumbbell Bench Press signal.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press showed consistent effort in Upper Body Strength.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press recovery interpretation is limited.",
  "suggested_focus": "Use Upper Body Strength detail before changing direction.",
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
    assert any("effort or consistency" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_progression_claim_fails_with_anchors():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a specific Dumbbell Bench Press signal.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press showed moderate weight progression in Upper Body Strength.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press recovery interpretation is limited.",
  "suggested_focus": "Use Upper Body Strength detail before changing direction.",
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
    assert any("progression" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_form_control_claim_fails_with_anchors():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a specific Dumbbell Bench Press signal.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press showed strong control and form in Upper Body Strength.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press recovery interpretation is limited.",
  "suggested_focus": "Use Upper Body Strength detail before changing direction.",
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
    assert any("form or control" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_fatigue_recovery_claim_fails_with_anchors():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a specific Dumbbell Bench Press signal.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the main Upper Body Strength detail.",
  "fatigue_recovery_interpretation": "There is no indication of fatigue or recovery issues for Dumbbell Bench Press.",
  "suggested_focus": "Use Upper Body Strength detail before changing direction.",
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
    assert any("fatigue or recovery" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_planned_alignment_claim_fails_with_anchors():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a specific Dumbbell Bench Press signal.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press aligned with planned work in Upper Body Strength.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press recovery interpretation is limited.",
  "suggested_focus": "Use Upper Body Strength detail before changing direction.",
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
    assert any("planned-work alignment" in error for error in result.validation_errors)


def test_model_facing_payload_includes_approved_coaching_moves():
    payload = build_training_report_section_model_quote_context(
        APPROVED_CONTEXT
    ).to_dict()

    assert "approved_coaching_moves" in payload
    assert "primary_signal" in payload["approved_coaching_moves"]
    assert "next_focus" in payload["approved_coaching_moves"]
    assert "allowed_meaning" in payload["approved_coaching_moves"]["primary_signal"]
    assert payload["approved_coaching_frames"] == []


def test_prompt_includes_semantic_coaching_moves_and_user_facing_focus_rule():
    prompt = build_direct_ollama_training_report_section_prompt(APPROVED_CONTEXT)

    assert "Approved semantic coaching moves" in prompt
    assert "suggested_focus must give the user a practical next step" in prompt
    assert "Sound like a coach speaking directly to the user" in prompt


def test_direct_ollama_training_section_spike_controlled_execution_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a concrete Dumbbell Bench Press checkpoint.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press showed controlled execution in Upper Body Strength.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a reference point and keep the next session measured.",
  "limitations_context": "Upper Body Strength supports a narrow training review, not broad recovery claims.",
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
    assert any("form or control" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_debug_style_copy_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength execution data for review is available.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the main Upper Body Strength detail.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a reference point and keep the next session measured.",
  "limitations_context": "Upper Body Strength supports a narrow training review, not broad recovery claims.",
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
    assert any("debug-style" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_exact_detail_internal_copy_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a concrete Dumbbell Bench Press checkpoint.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press should be interpreted from the exact logged training details.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a reference point and keep the next session measured.",
  "limitations_context": "Upper Body Strength supports a narrow training review, not broad recovery claims.",
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
    assert any("debug-style" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_weak_suggested_focus_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a concrete Dumbbell Bench Press checkpoint.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the main Upper Body Strength detail.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Review the execution data for Dumbbell Bench Press.",
  "limitations_context": "Upper Body Strength supports a narrow training review, not broad recovery claims.",
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
    assert any("suggested_focus" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_style_safe_coach_copy_passes():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Dumbbell Bench Press is the lift worth paying attention to from Upper Body Strength.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength gives enough signal for the next training choice, but not broad recovery claims.",
  "suggested_focus": "Keep Dumbbell Bench Press as the reference point and continue logging load, reps, and RIR.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
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
    assert result.validation_errors == []


def test_direct_ollama_training_section_spike_coaching_frame_does_not_bypass_control_claim():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives you a concrete checkpoint from Dumbbell Bench Press.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press gives the clearest training signal with controlled execution.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a reference point and keep the next session measured.",
  "limitations_context": "Upper Body Strength supports a narrow training review, not broad recovery claims.",
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
    assert any("form or control" in error for error in result.validation_errors)


def test_model_facing_payload_uses_semantic_coaching_moves_not_finished_frames():
    payload = build_training_report_section_model_quote_context(
        APPROVED_CONTEXT
    ).to_dict()
    moves = payload["approved_coaching_moves"]

    assert "primary_signal" in moves
    assert "next_focus" in moves
    assert "allowed_meaning" in moves["primary_signal"]
    assert moves["primary_signal"]["required_names"] == ["Dumbbell Bench Press"]
    assert payload["approved_coaching_frames"] == []


def test_prompt_discourages_stiff_product_copy():
    prompt = build_direct_ollama_training_report_section_prompt(APPROVED_CONTEXT)

    assert "Product voice" not in prompt
    assert "Prefer practical coaching language" in prompt
    assert "concrete checkpoint" in prompt
    assert "logged session" in prompt
    assert "centered on the logged lifts" in prompt


def test_direct_ollama_training_section_spike_stiff_checkpoint_copy_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives you a concrete checkpoint from the logged session.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength gives enough signal for the next training choice, but not broad recovery claims.",
  "suggested_focus": "Keep Dumbbell Bench Press as the reference point and continue logging load, reps, and RIR.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
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
    assert any("product-weak" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_product_voice_copy_passes():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Dumbbell Bench Press is the lift worth paying attention to from Upper Body Strength.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength gives enough signal for the next training choice, but not broad recovery claims.",
  "suggested_focus": "Keep Dumbbell Bench Press as the reference point and continue logging load, reps, and RIR.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
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
    assert result.validation_errors == []


def test_direct_ollama_training_section_spike_finished_coaching_frame_copy_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Dumbbell Bench Press give Upper Body Strength its clearest training signal.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Use Dumbbell Bench Press as reference lifts before increasing intensity.",
  "fatigue_recovery_interpretation": "Upper Body Strength gives enough signal to guide the next training choice, but not enough for broad recovery or progression conclusions.",
  "suggested_focus": "Keep Dumbbell Bench Press as the reference point and continue logging load, reps, and RIR.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
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
        "copies backend coaching guidance" in error
        for error in result.validation_errors
    )


def test_prompt_requires_summary_synthesis_and_recovery_scope_name():
    prompt = build_direct_ollama_training_report_section_prompt(APPROVED_CONTEXT)

    assert "section_summary should synthesize the main training signal" in prompt
    assert "Save exact numbers for key_observations" in prompt
    assert "fatigue_recovery_interpretation must name the required quote" in prompt
    assert "does not prove a recovery or fatigue pattern" in prompt
    assert "strong execution" in prompt


def test_direct_ollama_training_section_spike_section_summary_data_recap_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Key observations from Upper Body Strength include Dumbbell Bench Press at 50 lb for 10 reps.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a reference point and keep the next session measured.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
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
        "section_summary should synthesize" in error
        for error in result.validation_errors
    )


def test_direct_ollama_training_section_spike_unsupported_execution_quality_fails():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength included strong execution on Dumbbell Bench Press.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a reference point and keep the next session measured.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
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
        "form or control" in error or "quality" in error
        for error in result.validation_errors
    )


def test_model_facing_payload_includes_backend_derived_bounded_claims():
    payload = build_training_report_section_model_quote_context(
        _bounded_claims_context()
    ).to_dict()

    claims = payload["approved_bounded_training_claims"]
    claim_types = {claim["claim_type"] for claim in claims}

    assert "single_session_rep_pattern" in claim_types
    assert "single_session_effort" in claim_types
    assert "complete_reference_lift" in claim_types
    assert "scope_limit" in claim_types
    assert any("same rep count" in claim["approved_meaning"] for claim in claims)
    assert any("0 RIR" in claim["approved_meaning"] for claim in claims)


def test_prompt_exposes_bounded_training_claims_without_making_them_broad_trends():
    prompt = build_direct_ollama_training_report_section_prompt(
        _bounded_claims_context()
    )

    assert "Approved bounded training claims" in prompt
    assert "approved single-session observations" in prompt
    assert "do not turn them into trends" in prompt
    assert "same rep count" in prompt
    assert "effort was high within this logged session" in prompt
    assert "limitations_context must mention" in prompt
    assert "Do not translate same-rep language into consistent effort" in prompt
    assert "Do not translate RIR into execution quality" in prompt


def test_direct_ollama_training_section_spike_bounded_single_session_claims_pass():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a narrow Dumbbell Bench Press signal.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press held the same rep count across the logged sets and finished close to failure based on the 0 RIR log.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session, but it does not prove a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a single-session reference point and keep logging load, reps, and RIR before making a bigger adjustment.",
  "limitations_context": "Upper Body Strength is one workout, not enough to call it a trend.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen3:8b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is True
    assert result.validation_errors == []


def test_direct_ollama_training_section_spike_qwen3_style_consistent_effort_still_fails_with_bounded_claims():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength focused on consistent effort across multiple lifts, with notable attention to Dumbbell Bench Press.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press held the same rep count across the logged sets and finished close to failure based on the 0 RIR log.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session, but it does not prove a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a single-session reference point and keep logging load, reps, and RIR before making a bigger adjustment.",
  "limitations_context": "Upper Body Strength is one workout, not enough to call it a trend.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen3:8b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is False
    assert any(
        "effort or consistency" in error or "trend or consistency" in error
        for error in result.validation_errors
    )


def test_prompt_prioritizes_exact_anchor_copy_before_bounded_claims() -> None:
    prompt = build_direct_ollama_training_report_section_prompt(
        _bounded_claims_context()
    )

    assert "Exact key_observation copy gate" in prompt
    assert "Satisfy key_observations before using any bounded claims" in prompt
    assert "Do not use planned-only details in key_observations" in prompt
    assert "Do not say progression, progression in load and reps" in prompt
    assert prompt.index("Required training details") < prompt.index(
        "Exact key_observation copy gate"
    )
    assert prompt.index("Exact key_observation copy gate") < prompt.index(
        "Approved bounded training claims"
    )
    assert prompt.index("Approved bounded training claims") < prompt.index(
        "Approved semantic coaching moves"
    )


def test_direct_ollama_training_section_spike_progression_in_load_and_reps_fails() -> (
    None
):
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength shows progression in load and reps for Dumbbell Bench Press.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press shows progression in load and reps from this workout.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session, but it does not prove a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a single-session reference point and keep logging load, reps, and RIR before making a bigger adjustment.",
  "limitations_context": "Upper Body Strength is one workout, not enough to call it a trend.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is False
    assert any("progression" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_paraphrased_key_observations_fail() -> (
    None
):
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength has useful Dumbbell Bench Press signal.",
  "key_observations": [
    "Dumbbell Bench Press was planned for 3 sets, 8-10 reps with RIR 2-3.",
    "Dumbbell Bench Press was logged for three sets at 50 lb for 10 reps."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session, but it does not prove a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a single-session reference point and keep logging load, reps, and RIR before making a bigger adjustment.",
  "limitations_context": "Upper Body Strength is one workout, not enough to call it a trend.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is False
    assert any("key_observations[0]" in error for error in result.validation_errors)
    assert any("key_observations[1]" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_allows_logged_training_details_copy() -> (
    None
):
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength included Dumbbell Bench Press with clear load and rep details.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the strongest reference lift in this session because it has complete logged training details.",
  "fatigue_recovery_interpretation": "Upper Body Strength shows high-effort work from logged RIR, but it does not prove a broader fatigue or recovery pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a reference point and keep logging load, reps, and RIR.",
  "limitations_context": "Upper Body Strength is useful signal from one workout, not a full trend picture.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen3:8b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is True
    assert result.validation_errors == []


def test_direct_ollama_training_section_spike_still_rejects_exact_training_detail_placeholder() -> (
    None
):
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Training Detail is available for Upper Body Strength.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session, but it does not prove a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a reference point and keep logging load, reps, and RIR.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen3:8b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is False
    assert any(
        "placeholder training context" in error for error in result.validation_errors
    )


def test_direct_ollama_training_section_spike_broad_consistency_still_fails_with_bounded_claims():
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a narrow Dumbbell Bench Press signal.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press shows consistent performance over time.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session, but it does not prove a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a single-session reference point and keep logging load, reps, and RIR before making a bigger adjustment.",
  "limitations_context": "Upper Body Strength is one workout, not enough to call it a trend.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen3:8b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is False
    assert any(
        "trend or consistency" in error or "effort or consistency" in error
        for error in result.validation_errors
    )


def test_prompt_includes_scope_limit_product_voice_examples() -> None:
    prompt = build_direct_ollama_training_report_section_prompt(
        _bounded_claims_context()
    )

    assert "Example fatigue/recovery shape" in prompt
    assert "does not prove a broader fatigue or recovery pattern" in prompt
    assert "Example limitation shape" in prompt
    assert "one workout should not be read as a trend" in prompt


def test_direct_ollama_training_section_spike_qwen3_scope_limited_product_voice_passes() -> (
    None
):
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a useful Dumbbell Bench Press signal without turning one workout into a trend.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press held the same rep count across the logged sets and finished close to failure based on the 0 RIR log.",
  "fatigue_recovery_interpretation": "Upper Body Strength shows high-effort work from logged RIR, but it does not prove a broader fatigue or recovery pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as the next training reference and keep logging load, reps, and RIR before making a bigger adjustment.",
  "limitations_context": "Upper Body Strength can guide the next training choice, but one workout should not be read as a trend.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen3:8b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is True
    assert result.validation_errors == []


def test_direct_ollama_training_section_spike_rejects_angle_bracket_template_artifacts() -> (
    None
):
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a useful Dumbbell Bench Press signal without turning one workout into a trend.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press held the same rep count across the logged sets and finished close to failure based on the 0 RIR log.",
  "fatigue_recovery_interpretation": "<Upper Body Strength> shows high-effort work from logged RIR, but it does not prove a broader fatigue or recovery pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as the next training reference and keep logging load, reps, and RIR before making a bigger adjustment.",
  "limitations_context": "<Upper Body Strength> can guide the next training choice, but one workout should not be read as a trend.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is False
    assert result.fallback_used is True
    assert any(
        "angle-bracket template artifacts" in error
        for error in result.validation_errors
    )


def test_direct_ollama_training_section_spike_allows_treated_as_trend_scope_language() -> (
    None
):
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a useful Dumbbell Bench Press signal without turning one workout into a trend.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Use Dumbbell Bench Press as the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength is a single-session observation and should not be treated as a trend for recovery or fatigue patterns.",
  "suggested_focus": "Keep Dumbbell Bench Press as a reference point and keep logging load, reps, and RIR.",
  "limitations_context": "Upper Body Strength provides useful signal but does not prove broader recovery or fatigue trends.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:7b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is True
    assert result.validation_errors == []


def test_direct_ollama_training_section_spike_still_rejects_medical_treatment_claims() -> (
    None
):
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a useful Dumbbell Bench Press signal without turning one workout into a trend.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Use Dumbbell Bench Press as the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session, but it does not prove a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press for medical treatment decisions.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:7b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is False
    assert any("medical claims" in error for error in result.validation_errors)


def test_direct_ollama_training_section_spike_rejects_unapproved_prompt_example_workout_name() -> (
    None
):
    context = _bounded_claims_context()
    context["recent_training_executions"][0]["workout_title"] = (
        "Gradual Progression Strength Session"
    )
    context["approved_training_quote_context"] = build_approved_training_quote_context(
        recent_training_executions=context["recent_training_executions"],
        training_execution_summary=context["training_execution_summary"],
    ).to_dict()

    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Gradual Progression Strength Session gives a useful Dumbbell Bench Press signal, but Upper Body Strength should not appear here.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Use Dumbbell Bench Press as the reference point for the next Gradual Progression Strength Session choice.",
  "fatigue_recovery_interpretation": "Gradual Progression Strength Session can guide the next session, but it does not prove a recovery or fatigue pattern.",
  "suggested_focus": "Keep Dumbbell Bench Press as a reference point and keep logging load, reps, and RIR.",
  "limitations_context": "Gradual Progression Strength Session is one workout, not a full trend or recovery picture.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=context,
        generate=fake_generate,
    )

    assert result.success is False
    assert any(
        "unapproved training name" in error for error in result.validation_errors
    )


def test_direct_ollama_training_section_spike_qwen3_broad_recovery_trend_still_fails() -> (
    None
):
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "Upper Body Strength gives a useful Dumbbell Bench Press signal without turning one workout into a trend.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10, 10, 10 reps.",
    "The final Dumbbell Bench Press set was logged at 0 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press held the same rep count across the logged sets and finished close to failure based on the 0 RIR log.",
  "fatigue_recovery_interpretation": "Upper Body Strength shows recovery is trending well after this workout.",
  "suggested_focus": "Use Dumbbell Bench Press as the next training reference and keep logging load, reps, and RIR before making a bigger adjustment.",
  "limitations_context": "Upper Body Strength suggests a broader recovery trend from this training signal.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen3:8b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=_bounded_claims_context(),
        generate=fake_generate,
    )

    assert result.success is False
    assert any(
        "recovery" in error or "fatigue" in error or "trend" in error
        for error in result.validation_errors
    )


def test_direct_ollama_training_section_spike_empty_evidence_falls_back_before_provider() -> (
    None
):
    provider_called = False
    empty_context = {
        "section": "training",
        "approved_training_quote_context": {
            "approved_workout_names": [],
            "approved_exercise_names": [],
            "approved_training_numbers": [0],
            "approved_set_rep_load_rir_values": [],
            "approved_training_summary_facts": [],
        },
    }

    def fake_generate(*_args, **_kwargs):
        nonlocal provider_called
        provider_called = True
        raise AssertionError("provider should not be called with empty evidence")

    result = run_direct_ollama_training_report_section_spike(
        model="ollama/qwen2.5:3b",
        user_id=102,
        report_date="2026-06-06",
        approved_context=empty_context,
        generate=fake_generate,
    )

    assert provider_called is False
    assert result.success is False
    assert result.provider_attempted is False
    assert result.fallback_used is True
    assert result.fallback_reason == "approved_context_missing_training_evidence"
    assert result.validation_status == "rejected"
    assert result.candidate_validation_status == "failed"
    assert any("approved quote name" in error for error in result.validation_errors)
    assert any(
        "exact required fact anchors" in error for error in result.validation_errors
    )


def test_direct_ollama_training_section_spike_placeholder_text_falls_back() -> None:
    def fake_generate(*_args, **_kwargs):
        return """
{
  "section_summary": "None available can guide the next training choice.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Use Dumbbell Bench Press from Upper Body Strength as the next reference point.",
  "fatigue_recovery_interpretation": "Dumbbell Bench Press can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Use Dumbbell Bench Press as a reference point and keep the next session measured.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
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
    assert result.provider_attempted is True
    assert result.fallback_used is True
    assert result.fallback_reason == "candidate_validation_failure"
    assert result.candidate_parse_status == "success"
    assert result.candidate_validation_status == "failed"
    assert any(
        "placeholder training context" in error for error in result.validation_errors
    )
