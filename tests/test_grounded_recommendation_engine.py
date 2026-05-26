import pytest

import database
import services.recommendation_engine_service as recommendation_engine_service
from scripts.seed_qa_scenarios import QA_USER_IDS, seed_qa_scenarios
from services.coaching_decision_service import build_coaching_decision
from services.nutrition_target_service import build_nutrition_targets
from services.recommendation_engine_service import (
    approve_candidate_action_plan,
    approve_candidate_json_or_fallback,
    approve_candidate_provider_or_fallback,
    build_approved_action_plan,
    build_configured_approved_action_plan,
    build_crewai_approved_action_plan,
    build_crewai_candidate_action_plan_prompt,
    build_recommendation_context,
    candidate_action_plan_json_contract,
    generate_candidate_action_plan_json,
    parse_candidate_action_plan,
    render_approved_action_plan,
    validate_candidate_action_plan,
)
from services.training_constraint_service import build_training_constraints
from services.user_state_service import build_user_health_state

EXPECTED_SCENARIOS = {
    101: "recovery_limited",
    102: "aligned_managed",
    103: "nutrition_training_mismatch",
    104: "improving_after_deload",
    105: "data_quality_limited",
}


def _seeded_health_states(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    return {user_id: build_user_health_state(user_id) for user_id in QA_USER_IDS}


def test_nutrition_targets_and_training_constraints_for_seeded_users(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    for user_id, health_state in health_states.items():
        decision = build_coaching_decision(health_state)
        targets = build_nutrition_targets(health_state)
        constraints = build_training_constraints(health_state, decision)

        assert decision.scenario == EXPECTED_SCENARIOS[user_id]
        assert targets.body_weight_lb is not None
        assert targets.protein_grams_min is not None
        assert targets.protein_grams_max is not None
        assert constraints.progression_guidance
        assert constraints.low_rir_guidance


def test_grounded_recommendation_engine_seeded_users_pass_validation(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    for user_id, health_state in health_states.items():
        context = build_recommendation_context(health_state)
        assert context.scenario == EXPECTED_SCENARIOS[user_id]

        raw_json = generate_candidate_action_plan_json(context)
        candidate = parse_candidate_action_plan(raw_json)
        violations = validate_candidate_action_plan(candidate, context)
        assert violations == []

        approved = approve_candidate_action_plan(candidate, context)
        rendered = render_approved_action_plan(approved)
        assert "Grounded Recommendation" in rendered
        assert "Daily Coaching Recommendation" in rendered
        assert "Workout Recommendation" in rendered
        assert "Nutrition Action" in rendered


def test_recommendation_context_includes_passive_training_execution_summary(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    context = build_recommendation_context(health_states[102])

    assert context.training_execution_summary is not None
    assert context.training_execution_summary.user_id == 102
    assert context.training_execution_summary.completed_execution_count == 0
    assert (
        context.training_execution_summary.execution_quality
        == "no_planned_execution_data"
    )
    assert context.training_execution_summary.confidence == "Limited"
    assert "no_completed_planned_executions" in (
        context.training_execution_summary.reason_codes
    )


def test_training_execution_summary_is_not_in_llm_context_payload(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[102])

    payload = recommendation_engine_service.json.loads(
        recommendation_engine_service.recommendation_context_to_llm_json(context)
    )

    assert context.training_execution_summary is not None
    assert "training_execution_summary" not in payload
    assert "actual_sets" not in payload
    assert "notes" not in payload


def test_aligned_managed_recommendation_avoids_unnecessary_intervention_language(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_action_plan(health_states[102])
    rendered = render_approved_action_plan(approved).lower()

    assert approved.scenario == "aligned_managed"
    assert "maintain" in rendered
    assert "deload" not in rendered
    assert "reduce intensity" not in rendered
    assert "insufficient caloric" not in rendered


def test_recovery_limited_recommendation_includes_rir_guidance_when_needed(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_action_plan(health_states[101])
    rendered = render_approved_action_plan(approved).lower()

    assert approved.scenario == "recovery_limited"
    assert "recovery" in rendered
    assert "rir 2-3" in rendered
    assert "rir 0-1" in rendered


def test_nutrition_training_mismatch_does_not_treat_missing_as_zero(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_action_plan(health_states[103])
    rendered = render_approved_action_plan(approved).lower()

    assert approved.scenario == "nutrition_training_mismatch"
    assert "nutrition" in rendered
    assert "training" in rendered
    assert "0 kcal" not in rendered
    assert "0 g protein" not in rendered


def test_data_quality_limited_uses_verification_not_supplement_assumptions(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_action_plan(health_states[105])
    rendered = render_approved_action_plan(approved).lower()

    assert approved.scenario == "data_quality_limited"
    assert "verify" in rendered or "logging" in rendered
    assert "likely from supplements" not in rendered
    assert "supplementation artifacts" not in rendered


def test_candidate_validator_rejects_known_bad_recommendations(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[101])
    raw_json = """
    {
      "daily_coaching_recommendation": "Lower RIR to 2-3 and assume 0 kcal intake.",
      "workout_recommendation": "Use high-RIR (0-1) sets.",
      "nutrition_action": "Magnesium is likely from supplements.",
      "rationale": "Bad test plan.",
      "confidence": "High"
    }
    """

    candidate = parse_candidate_action_plan(raw_json)
    violations = validate_candidate_action_plan(candidate, context)

    assert len(violations) >= 3
    with pytest.raises(ValueError):
        approve_candidate_action_plan(candidate, context)


def test_daily_approved_recommendation_endpoint_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/recommendations/daily/102")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 102
    assert payload["scenario"] == "aligned_managed"
    assert set(payload) == {
        "success",
        "user_id",
        "scenario",
        "confidence",
        "nutrition_targets",
        "training_constraints",
        "approved_action_plan",
        "rendered_recommendation",
    }

    nutrition_targets = payload["nutrition_targets"]
    assert {
        "body_weight_lb",
        "calorie_target_min",
        "calorie_target_max",
        "protein_grams_min",
        "protein_grams_max",
        "carbohydrate_grams_min",
        "carbohydrate_grams_max",
        "fat_grams_min",
        "fat_grams_max",
        "confidence",
        "allow_calorie_targets",
        "allow_protein_targets",
        "allow_carbohydrate_targets",
        "allow_fat_targets",
        "nutrition_display_message",
        "reason_codes",
    } <= set(nutrition_targets)
    assert payload["approved_action_plan"]["daily_coaching_recommendation"]
    assert payload["rendered_recommendation"]


def test_daily_endpoint_uses_crewai_candidate_provider_when_valid(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    raw_json = """
    {
      "daily_coaching_recommendation": "Use the CrewAI candidate while maintaining steady progress.",
      "workout_recommendation": "Continue manageable training progression.",
      "nutrition_action": "Keep nutrition logging consistent and review protein support.",
      "rationale": "The fake CrewAI provider returned valid bounded JSON.",
      "confidence": "High"
    }
    """

    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_json,
    )

    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/recommendations/daily/102")

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario"] == "aligned_managed"
    assert (
        payload["approved_action_plan"]["daily_coaching_recommendation"]
        == "Use the CrewAI candidate while maintaining steady progress."
    )
    assert "fake CrewAI provider" in payload["approved_action_plan"]["rationale"]


def test_limited_confidence_nutrition_does_not_expose_hard_calorie_targets(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[105])
    approved = build_approved_action_plan(health_states[105])
    rendered = render_approved_action_plan(approved).lower()

    assert context.nutrition_targets.confidence == "Limited"
    assert context.nutrition_targets.allow_calorie_targets is False
    assert "calories/day" not in rendered
    assert "kcal" not in rendered


def test_daily_endpoint_hides_limited_confidence_calorie_targets(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/recommendations/daily/105")

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario"] == "data_quality_limited"
    assert payload["nutrition_targets"]["confidence"] == "Limited"
    assert payload["nutrition_targets"]["allow_calorie_targets"] is False
    assert payload["nutrition_targets"]["allow_protein_targets"] is True
    assert payload["nutrition_targets"]["allow_carbohydrate_targets"] is False
    assert payload["nutrition_targets"]["allow_fat_targets"] is False
    assert payload["nutrition_targets"]["calorie_target_min"] is None
    assert payload["nutrition_targets"]["calorie_target_max"] is None
    assert payload["nutrition_targets"]["carbohydrate_grams_min"] is None
    assert payload["nutrition_targets"]["carbohydrate_grams_max"] is None
    assert payload["nutrition_targets"]["fat_grams_min"] is None
    assert payload["nutrition_targets"]["fat_grams_max"] is None
    assert (
        payload["nutrition_targets"]["nutrition_display_message"]
        == "Nutrition targets are limited until logging is more complete. Focus on "
        "verifying entries and improving consistency first."
    )


def test_candidate_validator_rejects_disallowed_numeric_calorie_recommendations(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[105])
    raw_json = """
    {
      "daily_coaching_recommendation": "Improve logging quality first.",
      "workout_recommendation": "Maintain manageable training.",
      "nutrition_action": "Eat 1800-2000 calories/day while logging improves.",
      "rationale": "Logging is incomplete, so verify entries.",
      "confidence": "Low"
    }
    """

    candidate = parse_candidate_action_plan(raw_json)
    violations = validate_candidate_action_plan(candidate, context)

    assert any(
        "Numeric calorie recommendations are not allowed" in v for v in violations
    )


def test_candidate_validator_rejects_numeric_protein_outside_targets(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[102])
    raw_json = """
    {
      "daily_coaching_recommendation": "Maintain current direction.",
      "workout_recommendation": "Progress gradually while recovery markers remain stable.",
      "nutrition_action": "Use protein 20-40 g/day as the target.",
      "rationale": "Recovery, training, and nutrition appear aligned.",
      "confidence": "High"
    }
    """

    candidate = parse_candidate_action_plan(raw_json)
    violations = validate_candidate_action_plan(candidate, context)

    assert any("protein recommendation is outside" in v for v in violations)


def test_missing_nutrition_fields_remain_unknown_not_zero(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    health_state = health_states[105]
    context = build_recommendation_context(health_state)
    approved = build_approved_action_plan(health_state)
    rendered = render_approved_action_plan(approved).lower()

    assert health_state.nutrition_state.calories == "Unknown"
    assert context.nutrition_targets.confidence == "Limited"
    assert "0 kcal" not in rendered
    assert "0 calories" not in rendered
    assert "0 g protein" not in rendered


def test_limited_confidence_hides_unapproved_macro_targets_in_user_payload(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    payload = client.get("/recommendations/daily/105").json()
    targets = payload["nutrition_targets"]

    assert targets["confidence"] == "Limited"
    assert targets["allow_calorie_targets"] is False
    assert targets["allow_carbohydrate_targets"] is False
    assert targets["allow_fat_targets"] is False
    assert targets["calorie_target_min"] is None
    assert targets["calorie_target_max"] is None
    assert targets["carbohydrate_grams_min"] is None
    assert targets["carbohydrate_grams_max"] is None
    assert targets["fat_grams_min"] is None
    assert targets["fat_grams_max"] is None
    assert (
        "limited until logging is more complete" in targets["nutrition_display_message"]
    )


def test_candidate_validator_rejects_disallowed_numeric_carbohydrate_and_fat_targets(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[105])
    raw_json = """
    {
      "daily_coaching_recommendation": "Improve logging quality first.",
      "workout_recommendation": "Maintain manageable training.",
      "nutrition_action": "Use carbohydrates 200-300 g/day and fat 60-80 g/day.",
      "rationale": "Logging is incomplete, so verify entries.",
      "confidence": "Low"
    }
    """

    candidate = parse_candidate_action_plan(raw_json)
    violations = validate_candidate_action_plan(candidate, context)

    assert any(
        "Numeric carbohydrate recommendations are not allowed" in violation
        for violation in violations
    )
    assert any(
        "Numeric fat recommendations are not allowed" in violation
        for violation in violations
    )


def test_candidate_action_plan_json_contract_is_explicit():
    contract = candidate_action_plan_json_contract()

    assert contract["type"] == "object"
    assert "invalid_output_behavior" not in contract
    assert contract["required_fields"] == [
        "confidence",
        "daily_coaching_recommendation",
        "nutrition_action",
        "rationale",
        "workout_recommendation",
    ]
    assert contract["allowed_fields"] == contract["required_fields"]


def test_valid_candidate_action_plan_json_parses(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[102])
    raw_json = """
    {
      "daily_coaching_recommendation": "Maintain the current direction and progress gradually.",
      "workout_recommendation": "Continue manageable training progression.",
      "nutrition_action": "Keep nutrition logging consistent and review protein support.",
      "rationale": "Recovery and training are aligned enough to favor consistency.",
      "confidence": "High"
    }
    """

    candidate = parse_candidate_action_plan(raw_json)
    approved = approve_candidate_action_plan(candidate, context)

    assert approved.scenario == "aligned_managed"
    assert approved.daily_coaching_recommendation.startswith("Maintain")


def test_malformed_candidate_json_falls_back_to_deterministic_plan(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[102])

    approved = approve_candidate_json_or_fallback("not json", context)

    assert approved.scenario == "aligned_managed"
    assert "Maintain the current direction" in approved.daily_coaching_recommendation
    assert (
        validate_candidate_action_plan(
            parse_candidate_action_plan(generate_candidate_action_plan_json(context)),
            context,
        )
        == []
    )


def test_schema_mismatch_candidate_json_falls_back_to_deterministic_plan(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[102])
    raw_json = """
    {
      "daily_coaching_recommendation": "Maintain direction.",
      "workout_recommendation": "Continue training.",
      "nutrition_action": "Keep logging.",
      "confidence": "High",
      "unexpected_field": "CrewAI extra text"
    }
    """

    approved = approve_candidate_json_or_fallback(raw_json, context)

    assert approved.scenario == "aligned_managed"
    assert approved.rationale
    assert "CrewAI extra text" not in approved.rationale


def test_unsafe_candidate_validation_failure_falls_back(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[105])
    raw_json = """
    {
      "daily_coaching_recommendation": "Use 1800-2000 calories/day to fix the caloric deficit.",
      "workout_recommendation": "Push harder once calories are fixed.",
      "nutrition_action": "Treat missing intake as 0 kcal and increase from there.",
      "rationale": "This likely caused stalled weight loss.",
      "confidence": "Low"
    }
    """

    approved = approve_candidate_json_or_fallback(raw_json, context)
    rendered = render_approved_action_plan(approved).lower()

    assert approved.scenario == "data_quality_limited"
    assert "caloric deficit" not in rendered
    assert "stalled weight loss" not in rendered
    assert "0 kcal" not in rendered
    assert "verify" in rendered or "logging" in rendered


def test_data_quality_limited_candidate_cannot_make_strong_causal_claims(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[105])
    raw_json = """
    {
      "daily_coaching_recommendation": "Verify logging, but overtraining is the problem.",
      "workout_recommendation": "Maintain manageable training.",
      "nutrition_action": "Verify food entries before changing targets.",
      "rationale": "Incomplete logging likely contribute to stalled fat loss.",
      "confidence": "Low"
    }
    """

    candidate = parse_candidate_action_plan(raw_json)
    violations = validate_candidate_action_plan(candidate, context)

    assert any("strong causal" in violation for violation in violations)


def test_aligned_managed_candidate_cannot_recommend_deload_or_reduce_intensity(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[102])
    raw_json = """
    {
      "daily_coaching_recommendation": "Deload this week despite stable recovery.",
      "workout_recommendation": "Reduce intensity across all work sets.",
      "nutrition_action": "Keep nutrition consistent.",
      "rationale": "Intervention is needed.",
      "confidence": "High"
    }
    """

    candidate = parse_candidate_action_plan(raw_json)
    violations = validate_candidate_action_plan(candidate, context)

    assert any("unnecessary intervention" in violation for violation in violations)


def test_fallback_approved_action_plan_still_renders_safely(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[105])
    approved = approve_candidate_json_or_fallback("{bad json", context)
    rendered = render_approved_action_plan(approved).lower()

    assert "Grounded Recommendation" in render_approved_action_plan(approved)
    assert "verify" in rendered or "logging" in rendered
    assert "overtraining" not in rendered
    assert "stalled weight loss" not in rendered
    assert "caloric deficit" not in rendered


def test_crewai_candidate_prompt_requires_raw_json_only(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[102])

    prompt = build_crewai_candidate_action_plan_prompt(context)

    assert "Approved context:" in prompt
    assert "Required JSON object:" in prompt
    assert "Return raw JSON only" in prompt
    assert "Do not use markdown" in prompt
    assert "invalid_output_behavior" not in prompt
    assert "daily_coaching_recommendation" in prompt
    assert "workout_recommendation" in prompt
    assert "nutrition_action" in prompt
    assert "rationale" in prompt
    assert "confidence" in prompt


def test_crewai_provider_valid_candidate_json_approves(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    raw_json = """
    {
      "daily_coaching_recommendation": "Maintain the current direction and progress gradually.",
      "workout_recommendation": "Continue manageable training progression.",
      "nutrition_action": "Keep nutrition logging consistent and review protein support.",
      "rationale": "Recovery and training are aligned enough to favor consistency.",
      "confidence": "High"
    }
    """

    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_json,
    )

    approved = build_crewai_approved_action_plan(health_states[102])

    assert approved.scenario == "aligned_managed"
    assert approved.daily_coaching_recommendation.startswith("Maintain")
    assert approved.confidence == "High"


def test_crewai_provider_exception_falls_back(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    def failing_provider(context):
        raise RuntimeError("CrewAI unavailable")

    approved = build_approved_action_plan(
        health_states[102],
        candidate_provider=failing_provider,
    )

    assert approved.scenario == "aligned_managed"
    assert "Maintain the current direction" in approved.daily_coaching_recommendation


def test_crewai_malformed_output_falls_back(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: "not valid json",
    )

    approved = build_crewai_approved_action_plan(health_states[102])

    assert approved.scenario == "aligned_managed"
    assert "Maintain the current direction" in approved.daily_coaching_recommendation


def test_crewai_markdown_wrapped_output_falls_back(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    raw_json = """
    ```json
    {
      "daily_coaching_recommendation": "Maintain direction.",
      "workout_recommendation": "Continue training.",
      "nutrition_action": "Keep logging.",
      "rationale": "CrewAI wrapped this in markdown.",
      "confidence": "High"
    }
    ```
    """

    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_json,
    )

    approved = build_crewai_approved_action_plan(health_states[102])

    assert approved.scenario == "aligned_managed"
    assert "CrewAI wrapped" not in approved.rationale
    assert "Maintain the current direction" in approved.daily_coaching_recommendation


def test_crewai_extra_fields_fall_back(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    raw_json = """
    {
      "daily_coaching_recommendation": "Maintain direction.",
      "workout_recommendation": "Continue training.",
      "nutrition_action": "Keep logging.",
      "rationale": "This includes an extra field.",
      "confidence": "High",
      "markdown_report": "Do not render me."
    }
    """

    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_json,
    )

    approved = build_crewai_approved_action_plan(health_states[102])

    assert approved.scenario == "aligned_managed"
    assert "extra field" not in approved.rationale
    assert "Do not render me" not in render_approved_action_plan(approved)


def test_crewai_unsafe_data_quality_limited_candidate_falls_back(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    raw_json = """
    {
      "daily_coaching_recommendation": "Overtraining is causing stalled fat loss.",
      "workout_recommendation": "Push harder after correcting the deficit.",
      "nutrition_action": "Use 1800-2000 calories/day to fix the caloric deficit.",
      "rationale": "Incomplete logging likely caused the issue.",
      "confidence": "Low"
    }
    """

    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_json,
    )

    approved = build_crewai_approved_action_plan(health_states[105])
    rendered = render_approved_action_plan(approved).lower()

    assert approved.scenario == "data_quality_limited"
    assert "overtraining" not in rendered
    assert "stalled fat loss" not in rendered
    assert "caloric deficit" not in rendered
    assert "verify" in rendered or "logging" in rendered


def test_crewai_aligned_managed_deload_candidate_falls_back(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    raw_json = """
    {
      "daily_coaching_recommendation": "Deload this week despite stable recovery.",
      "workout_recommendation": "Reduce intensity across all training sessions.",
      "nutrition_action": "Keep nutrition consistent.",
      "rationale": "An intervention is needed despite aligned markers.",
      "confidence": "High"
    }
    """

    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_json,
    )

    approved = build_crewai_approved_action_plan(health_states[102])
    rendered = render_approved_action_plan(approved).lower()

    assert approved.scenario == "aligned_managed"
    assert "deload" not in rendered
    assert "reduce intensity" not in rendered
    assert "maintain" in rendered


def test_candidate_provider_non_string_output_falls_back(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[102])

    approved = approve_candidate_provider_or_fallback(
        lambda received_context: {"not": "a string"},
        context,
    )

    assert approved.scenario == "aligned_managed"
    assert "Maintain the current direction" in approved.daily_coaching_recommendation


def test_configured_provider_defaults_to_deterministic(tmp_path, monkeypatch):
    monkeypatch.delenv("RECOMMENDATION_CANDIDATE_PROVIDER", raising=False)
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    def fail_if_called(health_state):
        raise AssertionError("CrewAI provider should not be called by default")

    monkeypatch.setattr(
        recommendation_engine_service,
        "build_crewai_approved_action_plan",
        fail_if_called,
    )

    approved = build_configured_approved_action_plan(health_states[102])

    assert approved.scenario == "aligned_managed"
    assert "Maintain the current direction" in approved.daily_coaching_recommendation


def test_configured_deterministic_provider_does_not_call_crewai(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "deterministic")
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    def fail_if_called(health_state):
        raise AssertionError("CrewAI provider should not be called for deterministic")

    monkeypatch.setattr(
        recommendation_engine_service,
        "build_crewai_approved_action_plan",
        fail_if_called,
    )

    approved = build_configured_approved_action_plan(health_states[105])

    assert approved.scenario == "data_quality_limited"
    assert "Verify" in approved.nutrition_action


def test_configured_crewai_provider_uses_fake_crewai_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    raw_json = """
    {
      "daily_coaching_recommendation": "Use the configured CrewAI candidate while maintaining steady progress.",
      "workout_recommendation": "Continue manageable training progression.",
      "nutrition_action": "Keep nutrition logging consistent and review protein support.",
      "rationale": "The configured fake CrewAI provider returned valid bounded JSON.",
      "confidence": "High"
    }
    """

    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_json,
    )

    approved = build_configured_approved_action_plan(health_states[102])

    assert approved.scenario == "aligned_managed"
    assert approved.daily_coaching_recommendation.startswith(
        "Use the configured CrewAI candidate"
    )


def test_configured_provider_exception_falls_back_deterministically(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    def failing_provider(context):
        raise RuntimeError("CrewAI unavailable")

    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        failing_provider,
    )

    approved = build_configured_approved_action_plan(health_states[102])

    assert approved.scenario == "aligned_managed"
    assert "Maintain the current direction" in approved.daily_coaching_recommendation


def test_invalid_configured_provider_falls_back_to_deterministic(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "invalid-provider")
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    def fail_if_called(health_state):
        raise AssertionError("Invalid provider should not call CrewAI")

    monkeypatch.setattr(
        recommendation_engine_service,
        "build_crewai_approved_action_plan",
        fail_if_called,
    )

    approved = build_configured_approved_action_plan(health_states[102])

    assert approved.scenario == "aligned_managed"
    assert "Maintain the current direction" in approved.daily_coaching_recommendation


def test_daily_endpoint_response_shape_stable_with_configured_provider(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "deterministic")
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/recommendations/daily/105")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "success",
        "user_id",
        "scenario",
        "confidence",
        "nutrition_targets",
        "training_constraints",
        "approved_action_plan",
        "rendered_recommendation",
    }
    assert payload["success"] is True
    assert payload["user_id"] == 105
    assert payload["scenario"] == "data_quality_limited"


def test_llm_context_serializer_hides_unapproved_targets_for_user_105(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[105])
    llm_json = recommendation_engine_service.recommendation_context_to_llm_json(context)
    payload = recommendation_engine_service.json.loads(llm_json)
    targets = payload["nutrition_targets"]

    assert targets["confidence"] == "Limited"
    assert targets["allow_calorie_targets"] is False
    assert targets["allow_carbohydrate_targets"] is False
    assert targets["allow_fat_targets"] is False
    assert targets["calorie_target_min"] is None
    assert targets["calorie_target_max"] is None
    assert targets["carbohydrate_grams_min"] is None
    assert targets["carbohydrate_grams_max"] is None
    assert targets["fat_grams_min"] is None
    assert targets["fat_grams_max"] is None
    assert targets["allow_protein_targets"] is True
    assert targets["protein_grams_min"] is not None
    assert (
        "limited until logging is more complete" in targets["nutrition_display_message"]
    )


def test_crewai_prompt_frames_model_as_json_copy_generator(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[102])

    prompt = build_crewai_candidate_action_plan_prompt(context)

    assert "approved context" in prompt.lower()
    assert "required JSON object" in prompt
    assert "first character must be {" in prompt
    assert "last character must be }" in prompt
    assert "Do not use markdown" in prompt
    assert "invalid_output_behavior" not in prompt
    assert "CandidateActionPlan" not in prompt


def test_candidate_validator_rejects_confidence_above_context(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[105])
    raw_json = """
    {
      "daily_coaching_recommendation": "Improve logging completeness before stronger changes.",
      "workout_recommendation": "Maintain manageable training while logging improves.",
      "nutrition_action": "Verify food entries and unusual nutrient values.",
      "rationale": "Logging quality should improve before stronger conclusions.",
      "confidence": "High"
    }
    """

    candidate = parse_candidate_action_plan(raw_json)
    violations = validate_candidate_action_plan(candidate, context)

    assert any("confidence must not exceed" in violation for violation in violations)


def test_candidate_validator_rejects_internal_debug_language(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_recommendation_context(health_states[102])
    raw_json = """
    {
      "daily_coaching_recommendation": "The backend validation fallback selected the safe option.",
      "workout_recommendation": "Continue manageable training progression.",
      "nutrition_action": "Keep nutrition logging consistent.",
      "rationale": "The schema and reason codes support this output.",
      "confidence": "High"
    }
    """

    candidate = parse_candidate_action_plan(raw_json)
    violations = validate_candidate_action_plan(candidate, context)

    assert any("internal or debug language" in violation for violation in violations)


def test_runtime_metadata_deterministic_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "deterministic")
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    result = recommendation_engine_service.build_configured_approved_action_plan_with_metadata(
        health_states[102]
    )

    assert result.approved_action_plan.scenario == "aligned_managed"
    assert result.runtime_metadata.configured_provider == "deterministic"
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.crewai_attempted is False
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.fallback_reason == "deterministic_selected"
    assert result.runtime_metadata.candidate_valid is True
    assert result.runtime_metadata.validation_errors == []
    assert result.runtime_metadata.candidate_parse_status == "not_attempted"
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"
    assert result.runtime_metadata.final_plan_source == "deterministic"


def test_runtime_metadata_invalid_provider_falls_back(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "not-real")
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    result = recommendation_engine_service.build_configured_approved_action_plan_with_metadata(
        health_states[102]
    )

    assert result.approved_action_plan.scenario == "aligned_managed"
    assert result.runtime_metadata.configured_provider == "not-real"
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.crewai_attempted is False
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "invalid_provider"
    assert result.runtime_metadata.candidate_parse_status == "not_attempted"
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"
    assert result.runtime_metadata.final_plan_source == "deterministic_fallback"


def test_runtime_metadata_crewai_success(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    raw_json = """
    {
      "daily_coaching_recommendation": "Maintain the current direction and progress gradually.",
      "workout_recommendation": "Continue manageable training progression.",
      "nutrition_action": "Keep nutrition logging consistent and review protein support.",
      "rationale": "Recovery and training are aligned enough to favor consistency.",
      "confidence": "High"
    }
    """
    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_json,
    )

    result = recommendation_engine_service.build_configured_approved_action_plan_with_metadata(
        health_states[102]
    )

    assert result.approved_action_plan.daily_coaching_recommendation.startswith(
        "Maintain"
    )
    assert result.runtime_metadata.selected_provider == "crewai"
    assert result.runtime_metadata.crewai_attempted is True
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.fallback_reason is None
    assert result.runtime_metadata.candidate_valid is True
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "success"
    assert result.runtime_metadata.final_plan_source == "crewai_approved"
    assert result.runtime_metadata.raw_output_length == len(raw_json)
    assert result.runtime_metadata.markdown_wrapper_detected is False


def test_runtime_metadata_provider_exception_falls_back(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    def failing_provider(context):
        raise RuntimeError("CrewAI unavailable")

    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        failing_provider,
    )

    result = recommendation_engine_service.build_configured_approved_action_plan_with_metadata(
        health_states[102]
    )

    assert result.approved_action_plan.scenario == "aligned_managed"
    assert result.runtime_metadata.crewai_attempted is True
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "provider_exception"


def test_runtime_metadata_malformed_json_falls_back(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: "not json",
    )

    result = recommendation_engine_service.build_configured_approved_action_plan_with_metadata(
        health_states[102]
    )

    assert result.approved_action_plan.scenario == "aligned_managed"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "malformed_json"


def test_runtime_metadata_validation_failure_falls_back(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    raw_json = """
    {
      "daily_coaching_recommendation": "Deload this week despite stable recovery.",
      "workout_recommendation": "Reduce intensity across all work sets.",
      "nutrition_action": "Keep nutrition consistent.",
      "rationale": "Intervention is needed.",
      "confidence": "High"
    }
    """
    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_json,
    )

    result = recommendation_engine_service.build_configured_approved_action_plan_with_metadata(
        health_states[102]
    )

    assert result.approved_action_plan.scenario == "aligned_managed"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "validation_failure"
    assert result.runtime_metadata.validation_errors


def test_build_configured_approved_action_plan_return_type_remains_plan(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "deterministic")
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    approved = build_configured_approved_action_plan(health_states[102])

    assert not hasattr(approved, "runtime_metadata")
    assert approved.scenario == "aligned_managed"


def test_runtime_metadata_logging_is_structured(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: "not json",
    )

    with caplog.at_level("INFO", logger="services.recommendation_engine_service"):
        recommendation_engine_service.build_configured_approved_action_plan_with_metadata(
            health_states[105]
        )

    records = [
        record
        for record in caplog.records
        if record.message == "recommendation_candidate_provider_result"
    ]
    assert records
    record = records[-1]
    assert record.user_id == 105
    assert record.scenario == "data_quality_limited"
    assert record.configured_provider == "crewai"
    assert record.selected_provider == "crewai"
    assert record.fallback_used is True
    assert record.fallback_reason == "malformed_json"
    assert record.nutrition_confidence == "Limited"
    assert isinstance(record.elapsed_ms, int)


def test_debug_endpoint_returns_runtime_metadata_deterministic(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "deterministic")
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/recommendations/daily/105/debug")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "success",
        "user_id",
        "scenario",
        "confidence",
        "approved_action_plan",
        "rendered_recommendation",
        "runtime_metadata",
        "training_execution_summary",
    }
    training_summary = payload["training_execution_summary"]
    assert training_summary["user_id"] == 105
    assert training_summary["completed_execution_count"] == 0
    assert training_summary["execution_quality"] == "no_planned_execution_data"
    assert "actual_sets" not in training_summary
    assert "notes" not in training_summary
    metadata = payload["runtime_metadata"]
    assert metadata["configured_provider"] == "deterministic"
    assert metadata["selected_provider"] == "deterministic"
    assert metadata["crewai_attempted"] is False
    assert metadata["fallback_used"] is False
    assert metadata["candidate_parse_status"] == "not_attempted"
    assert metadata["candidate_validation_status"] == "not_attempted"
    assert metadata["final_plan_source"] == "deterministic"


def test_debug_endpoint_crewai_success_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    raw_json = """
    {
      "daily_coaching_recommendation": "Maintain the current direction and progress gradually.",
      "workout_recommendation": "Continue manageable training progression.",
      "nutrition_action": "Keep nutrition logging consistent and review protein support.",
      "rationale": "Recovery and training are aligned enough to favor consistency.",
      "confidence": "High"
    }
    """
    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_json,
    )

    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/recommendations/daily/102/debug")

    assert response.status_code == 200
    metadata = response.json()["runtime_metadata"]
    assert metadata["configured_provider"] == "crewai"
    assert metadata["selected_provider"] == "crewai"
    assert metadata["crewai_attempted"] is True
    assert metadata["fallback_used"] is False
    assert metadata["fallback_reason"] is None
    assert metadata["candidate_parse_status"] == "success"
    assert metadata["candidate_validation_status"] == "success"
    assert metadata["final_plan_source"] == "crewai_approved"
    assert metadata["raw_output_length"] == len(raw_json)
    assert metadata["markdown_wrapper_detected"] is False


def test_debug_endpoint_crewai_markdown_malformed_fallback_metadata(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    raw_output = """```json
    {
      "daily_coaching_recommendation": "Maintain the current direction.",
      "workout_recommendation": "Continue manageable training progression.",
      "nutrition_action": "Keep nutrition logging consistent.",
      "rationale": "Recovery and training are aligned.",
      "confidence": "High"
    }
    ```"""
    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_output,
    )

    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/recommendations/daily/102/debug")

    assert response.status_code == 200
    metadata = response.json()["runtime_metadata"]
    assert metadata["fallback_used"] is True
    assert metadata["fallback_reason"] == "malformed_json"
    assert metadata["candidate_parse_status"] == "failed"
    assert metadata["candidate_validation_status"] == "not_attempted"
    assert metadata["final_plan_source"] == "deterministic_fallback"
    assert metadata["raw_output_length"] == len(raw_output)
    assert metadata["markdown_wrapper_detected"] is True
    assert metadata["raw_output_preview_truncated"].startswith("```json")


def test_debug_endpoint_invalid_provider_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "not-a-provider")
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/recommendations/daily/102/debug")

    assert response.status_code == 200
    metadata = response.json()["runtime_metadata"]
    assert metadata["configured_provider"] == "not-a-provider"
    assert metadata["selected_provider"] == "deterministic"
    assert metadata["crewai_attempted"] is False
    assert metadata["fallback_used"] is True
    assert metadata["fallback_reason"] == "invalid_provider"
    assert metadata["candidate_parse_status"] == "not_attempted"
    assert metadata["candidate_validation_status"] == "not_attempted"
    assert metadata["final_plan_source"] == "deterministic_fallback"


def test_debug_endpoint_exposes_training_execution_summary_only_in_debug(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "deterministic")
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    daily_payload = client.get("/recommendations/daily/102").json()
    debug_payload = client.get("/recommendations/daily/102/debug").json()

    assert "training_execution_summary" not in daily_payload
    assert "training_execution_summary" in debug_payload

    training_summary = debug_payload["training_execution_summary"]
    assert training_summary["user_id"] == 102
    assert training_summary["completed_execution_count"] == 0
    assert "actual_sets" not in training_summary
    assert "workout_execution_set_actuals" not in training_summary
    assert "notes" not in training_summary


def test_runtime_metadata_validation_failure_has_split_statuses(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    raw_json = """
    {
      "daily_coaching_recommendation": "Deload this week despite stable recovery.",
      "workout_recommendation": "Reduce intensity across all work sets.",
      "nutrition_action": "Keep nutrition consistent.",
      "rationale": "Intervention is needed.",
      "confidence": "High"
    }
    """
    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_json,
    )

    result = recommendation_engine_service.build_configured_approved_action_plan_with_metadata(
        health_states[102]
    )

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "validation_failure"
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "failed"
    assert result.runtime_metadata.final_plan_source == "deterministic_fallback"
    assert result.runtime_metadata.raw_output_length == len(raw_json)


def test_runtime_metadata_raw_output_preview_is_truncated(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    raw_output = "not json " + ("x" * 500)
    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: raw_output,
    )

    result = recommendation_engine_service.build_configured_approved_action_plan_with_metadata(
        health_states[102]
    )

    assert result.runtime_metadata.fallback_reason == "malformed_json"
    assert result.runtime_metadata.raw_output_length == len(raw_output)
    assert result.runtime_metadata.raw_output_preview_truncated.endswith("...")
    assert len(result.runtime_metadata.raw_output_preview_truncated) <= 243


def test_runtime_logging_includes_split_statuses_and_final_source(
    tmp_path, monkeypatch, caplog
):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "crewai")
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    monkeypatch.setattr(
        recommendation_engine_service,
        "generate_crewai_candidate_action_plan_json",
        lambda context: "not json",
    )

    with caplog.at_level("INFO", logger="services.recommendation_engine_service"):
        recommendation_engine_service.build_configured_approved_action_plan_with_metadata(
            health_states[105]
        )

    record = [
        record
        for record in caplog.records
        if record.message == "recommendation_candidate_provider_result"
    ][-1]
    assert record.candidate_parse_status == "failed"
    assert record.candidate_validation_status == "not_attempted"
    assert record.final_plan_source == "deterministic_fallback"
    assert record.raw_output_length == len("not json")
    assert record.markdown_wrapper_detected is False


def test_stable_daily_endpoint_does_not_expose_runtime_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "deterministic")
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/recommendations/daily/105")

    assert response.status_code == 200
    payload = response.json()
    assert "runtime_metadata" not in payload
    assert set(payload) == {
        "success",
        "user_id",
        "scenario",
        "confidence",
        "nutrition_targets",
        "training_constraints",
        "approved_action_plan",
        "rendered_recommendation",
    }
