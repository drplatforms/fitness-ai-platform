import pytest

import database
from scripts.seed_qa_scenarios import QA_USER_IDS, seed_qa_scenarios
from services.coaching_decision_service import build_coaching_decision
from services.nutrition_target_service import build_nutrition_targets
from services.recommendation_engine_service import (
    approve_candidate_action_plan,
    build_approved_action_plan,
    build_recommendation_context,
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
    assert payload["approved_action_plan"]["daily_coaching_recommendation"]
    assert payload["rendered_recommendation"]


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
    assert payload["nutrition_targets"]["calorie_target_min"] is None
    assert payload["nutrition_targets"]["calorie_target_max"] is None


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
