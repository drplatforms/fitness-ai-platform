from dataclasses import replace

from fastapi.testclient import TestClient

import database
from api.main import app
from models.workout_constraint_models import WorkoutConstraints
from scripts.seed_qa_scenarios import QA_USER_IDS, seed_qa_scenarios
from services.user_state_service import build_user_health_state
from services.workout_plan_service import (
    approve_candidate_workout_plan,
    build_approved_workout_plan,
    build_workout_context,
    generate_candidate_workout_plan,
    render_approved_workout_plan,
    validate_candidate_workout_plan,
)

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


def test_seeded_users_build_valid_approved_workout_plans(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    for user_id, health_state in health_states.items():
        context = build_workout_context(health_state)
        candidate = generate_candidate_workout_plan(context)
        violations = validate_candidate_workout_plan(candidate, context)
        approved = approve_candidate_workout_plan(candidate, context)
        rendered = render_approved_workout_plan(approved)

        assert context.scenario == EXPECTED_SCENARIOS[user_id]
        assert violations == []
        assert approved.scenario == EXPECTED_SCENARIOS[user_id]
        assert approved.exercises
        assert "Workout Plan Preview" in rendered
        assert "RIR" in rendered


def test_recovery_limited_workout_is_recovery_aware(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_workout_plan(health_states[101])
    rendered = render_approved_workout_plan(approved).lower()

    assert approved.scenario == "recovery_limited"
    assert "recovery" in rendered
    assert "rir 2-3" in rendered
    assert "max effort" not in rendered
    assert "to failure" not in rendered
    assert all(exercise.rir_min >= 2 for exercise in approved.exercises)
    assert all(exercise.rir_max <= 3 for exercise in approved.exercises)


def test_aligned_managed_workout_avoids_unnecessary_intervention(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_workout_plan(health_states[102])
    rendered = render_approved_workout_plan(approved).lower()

    assert approved.scenario == "aligned_managed"
    assert "gradual" in rendered or "progress" in rendered
    assert "deload" not in rendered
    assert "reduce intensity" not in rendered
    assert "cut volume" not in rendered


def test_nutrition_training_mismatch_workout_stays_controlled(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_workout_plan(health_states[103])
    rendered = render_approved_workout_plan(approved).lower()

    assert approved.scenario == "nutrition_training_mismatch"
    assert "nutrition" in rendered
    assert "controlled" in rendered
    assert "0 kcal" not in rendered


def test_improving_after_deload_workout_uses_controlled_progression(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_workout_plan(health_states[104])
    rendered = render_approved_workout_plan(approved).lower()

    assert approved.scenario == "improving_after_deload"
    assert "controlled" in rendered or "gradual" in rendered
    assert "ramping too quickly" in rendered or "jumping back" in rendered


def test_data_quality_limited_workout_uses_manageable_baseline_language(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_workout_plan(health_states[105])
    rendered = render_approved_workout_plan(approved).lower()

    assert approved.scenario == "data_quality_limited"
    assert "logging" in rendered
    assert "baseline" in rendered or "manageable" in rendered
    assert "overtraining" not in rendered
    assert "stalled progress" not in rendered
    assert "stalled fat loss" not in rendered


def test_workout_validator_rejects_invalid_and_unsafe_candidate(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_workout_context(health_states[101])
    candidate = generate_candidate_workout_plan(context)
    candidate.exercises[0].rir_min = 0
    candidate.exercises[0].rir_max = 1
    candidate.progression_guidance = "Use max effort sets to failure."

    violations = validate_candidate_workout_plan(candidate, context)

    assert violations
    assert any(
        "RIR" in violation or "max-effort" in violation for violation in violations
    )


def test_workout_context_includes_workout_constraints(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_workout_context(health_states[105])

    assert context.workout_constraints.available_equipment
    assert context.workout_constraints.recent_exercises
    assert "safe_default_equipment_assumptions" in context.reason_codes


def test_workout_generator_respects_unavailable_equipment(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_workout_context(health_states[102])
    restricted_context = replace(
        context,
        workout_constraints=WorkoutConstraints(
            available_equipment=["dumbbell", "bodyweight"],
            unavailable_equipment=["barbell", "machine", "cable"],
            confidence="Low",
            reason_codes=["test_equipment_restricted"],
        ),
    )

    candidate = generate_candidate_workout_plan(restricted_context)
    violations = validate_candidate_workout_plan(candidate, restricted_context)
    exercise_names = " ".join(exercise.name for exercise in candidate.exercises).lower()

    assert violations == []
    assert "barbell" not in exercise_names
    assert all(
        "barbell" not in exercise.equipment_required for exercise in candidate.exercises
    )


def test_workout_validator_rejects_unavailable_equipment(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_workout_context(health_states[102])
    restricted_context = replace(
        context,
        workout_constraints=WorkoutConstraints(
            available_equipment=["dumbbell", "bodyweight"],
            unavailable_equipment=["barbell"],
            confidence="Low",
            reason_codes=["test_equipment_restricted"],
        ),
    )
    candidate = generate_candidate_workout_plan(restricted_context)
    candidate.exercises[0].name = "Barbell Squat"
    candidate.exercises[0].equipment_required = ["barbell"]

    violations = validate_candidate_workout_plan(candidate, restricted_context)

    assert any("equipment" in violation.lower() for violation in violations)


def test_workout_plan_preview_endpoint_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    client = TestClient(app)
    response = client.get("/workout-plans/preview/105")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 105
    assert payload["scenario"] == "data_quality_limited"
    assert payload["confidence"] == "Low"
    assert payload["training_constraints"]["recommended_rir_min"] == 2
    assert "workout_constraints" in payload
    assert payload["workout_constraints"]["available_equipment"]
    assert payload["approved_workout_plan"]["exercises"]
    assert "Workout Plan Preview" in payload["rendered_workout_plan"]
