from __future__ import annotations

import json

from models.coach_voice_bakeoff_models import (
    COACH_VOICE_DECISION_FAIL,
    COACH_VOICE_DECISION_PASS,
    COACH_VOICE_PARSE_STATUS_FAILED,
    COACH_VOICE_PARSE_STATUS_SUCCESS,
    COACH_VOICE_VALIDATION_STATUS_APPROVED,
    COACH_VOICE_VALIDATION_STATUS_REJECTED,
)
from services.coach_voice_bakeoff_service import (
    build_coach_voice_prompt,
    build_default_coach_voice_contexts,
    generate_markdown_report,
    parse_coach_voice_candidate,
    run_coach_voice_bakeoff,
    run_coach_voice_candidate,
    starter_context_ids,
    validate_coach_voice_output,
)


def _safe_candidate(context_id: str = "user_102_daily_log_food") -> str:
    context = build_default_coach_voice_contexts()[context_id]
    return json.dumps(
        {
            "coach_note": (
                f"{context.approved_focus_options[0]} is the useful move now because "
                f"{context.approved_facts[1]}."
            ),
            "key_takeaway": context.approved_facts[1],
            "recommended_focus": context.approved_focus_options[0],
            "confidence_language": "This stays limited to the approved context.",
            "used_approved_facts": context.approved_facts[:2],
            "avoided_claims": ["No invented foods, targets, or medical claims."],
        }
    )


def test_default_contexts_include_starter_users_and_contexts():
    contexts = build_default_coach_voice_contexts()

    assert set(starter_context_ids()) == {
        "user_101_recovery_limited",
        "user_102_daily_log_food",
        "user_105_data_quality_limited",
    }
    assert contexts["user_101_recovery_limited"].user_id == 101
    assert contexts["user_102_daily_log_food"].user_id == 102
    assert contexts["user_105_data_quality_limited"].user_id == 105
    assert contexts["user_102_workout_preview"].approved_facts


def test_prompt_contains_schema_approved_facts_and_exact_focus_rule():
    context = build_default_coach_voice_contexts()["user_102_daily_log_food"]

    prompt = build_coach_voice_prompt(context)

    assert "Return strict JSON only" in prompt
    assert "recommended_focus must exactly match" in prompt
    assert "Daily next action: Log a meal or snack" in prompt
    assert "used_approved_facts" in prompt


def test_parse_accepts_strict_json_candidate():
    result = parse_coach_voice_candidate(_safe_candidate())

    assert result.parse_status == COACH_VOICE_PARSE_STATUS_SUCCESS
    assert result.output is not None
    assert result.output.recommended_focus == "Log a meal or snack"


def test_parse_rejects_markdown_wrapped_json():
    result = parse_coach_voice_candidate(f"```json\n{_safe_candidate()}\n```")

    assert result.parse_status == COACH_VOICE_PARSE_STATUS_FAILED
    assert "single JSON object" in (result.error or "")


def test_parse_rejects_missing_required_field():
    payload = json.loads(_safe_candidate())
    payload.pop("avoided_claims")

    result = parse_coach_voice_candidate(json.dumps(payload))

    assert result.parse_status == COACH_VOICE_PARSE_STATUS_FAILED
    assert "missing" in (result.error or "")


def test_validation_accepts_grounded_safe_output():
    context = build_default_coach_voice_contexts()["user_102_daily_log_food"]
    parse_result = parse_coach_voice_candidate(_safe_candidate())
    assert parse_result.output is not None

    validation = validate_coach_voice_output(parse_result.output, context=context)

    assert validation.validation_status == COACH_VOICE_VALIDATION_STATUS_APPROVED
    assert validation.validation_errors == []


def test_validation_rejects_changed_backend_action():
    context = build_default_coach_voice_contexts()["user_102_daily_log_food"]
    payload = json.loads(_safe_candidate())
    payload["recommended_focus"] = "Review today's workout"
    parse_result = parse_coach_voice_candidate(json.dumps(payload))
    assert parse_result.output is not None

    validation = validate_coach_voice_output(parse_result.output, context=context)

    assert validation.validation_status == COACH_VOICE_VALIDATION_STATUS_REJECTED
    assert any("recommended_focus" in error for error in validation.validation_errors)


def test_validation_rejects_invented_food_and_meal_plan():
    context = build_default_coach_voice_contexts()["user_102_daily_log_food"]
    payload = json.loads(_safe_candidate())
    payload["coach_note"] = (
        "Log a meal or snack, then add Greek yogurt as part of a meal plan."
    )
    parse_result = parse_coach_voice_candidate(json.dumps(payload))
    assert parse_result.output is not None

    validation = validate_coach_voice_output(parse_result.output, context=context)

    assert validation.validation_status == COACH_VOICE_VALIDATION_STATUS_REJECTED
    assert "Greek yogurt" in validation.forbidden_claims_found
    assert "meal plan" in validation.forbidden_claims_found


def test_validation_rejects_invented_number():
    context = build_default_coach_voice_contexts()["user_105_data_quality_limited"]
    payload = json.loads(_safe_candidate("user_105_data_quality_limited"))
    payload["coach_note"] = (
        "Log a meal or snack before using a 500 calorie target adjustment."
    )
    parse_result = parse_coach_voice_candidate(json.dumps(payload))
    assert parse_result.output is not None

    validation = validate_coach_voice_output(parse_result.output, context=context)

    assert validation.validation_status == COACH_VOICE_VALIDATION_STATUS_REJECTED
    assert any("Invented numeric" in error for error in validation.validation_errors)


def test_run_candidate_uses_fake_generator_and_returns_pass():
    context = build_default_coach_voice_contexts()["user_102_daily_log_food"]

    def fake_generate(model_name, prompt, timeout_seconds, ollama_base_url):
        assert model_name == "qwen2.5:3b"
        assert "Daily next action: Log a meal or snack" in prompt
        assert timeout_seconds == 30
        assert ollama_base_url == "http://localhost:11434"
        return _safe_candidate()

    result = run_coach_voice_candidate(
        model_name="qwen2.5:3b",
        context=context,
        generate=fake_generate,
        timeout_seconds=30,
        ollama_base_url="http://localhost:11434",
    )

    assert result.parse_status == COACH_VOICE_PARSE_STATUS_SUCCESS
    assert result.validation_status == COACH_VOICE_VALIDATION_STATUS_APPROVED
    assert result.overall_decision == COACH_VOICE_DECISION_PASS
    assert result.representative_safe_excerpt


def test_run_candidate_returns_fail_for_parse_error():
    context = build_default_coach_voice_contexts()["user_102_daily_log_food"]

    def fake_generate(_model_name, _prompt, _timeout_seconds, _ollama_base_url):
        return "not json"

    result = run_coach_voice_candidate(
        model_name="qwen3:8b",
        context=context,
        generate=fake_generate,
    )

    assert result.parse_status == COACH_VOICE_PARSE_STATUS_FAILED
    assert result.validation_status == COACH_VOICE_VALIDATION_STATUS_REJECTED
    assert result.overall_decision == COACH_VOICE_DECISION_FAIL
    assert result.representative_rejection_reason


def test_run_bakeoff_and_markdown_report_include_model_context_and_decision():
    contexts = [build_default_coach_voice_contexts()["user_102_daily_log_food"]]

    def fake_generate(_model_name, _prompt, _timeout_seconds, _ollama_base_url):
        return _safe_candidate()

    results = run_coach_voice_bakeoff(
        model_names=["qwen2.5:3b", "qwen3:14b"],
        contexts=contexts,
        generate=fake_generate,
    )
    report = generate_markdown_report(results)

    assert len(results) == 2
    assert "qwen2.5:3b" in report
    assert "qwen3:14b" in report
    assert "user_102_daily_log_food" in report
    assert COACH_VOICE_DECISION_PASS in report
    assert "No model is promoted" in report
