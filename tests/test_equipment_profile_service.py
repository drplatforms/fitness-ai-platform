from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import (
    get_effective_equipment_profile,
    get_equipment_profile,
    save_equipment_profile,
)
from services.user_state_service import build_user_health_state
from services.workout_constraint_service import build_workout_constraints
from services.workout_plan_service import build_approved_workout_plan


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()


def test_missing_equipment_profile_uses_safe_defaults(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    profile = get_effective_equipment_profile(105)
    stored_profile = get_equipment_profile(105)

    assert stored_profile is None
    assert profile.training_environment == "unknown"
    assert "dumbbell" in profile.available_equipment
    assert "bodyweight" in profile.available_equipment
    assert profile.unavailable_equipment == []
    assert profile.confidence == "Low"
    assert "safe_default_equipment_assumptions" in profile.reason_codes


def test_explicit_equipment_profile_overrides_defaults(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    profile = save_equipment_profile(
        user_id=105,
        training_environment="limited_equipment",
        available_equipment=["Bodyweight", "Dumbbell"],
        unavailable_equipment=["Barbell", "Machine", "Cable"],
    )
    health_state = build_user_health_state(105)
    constraints = build_workout_constraints(health_state)

    assert profile.training_environment == "limited_equipment"
    assert profile.available_equipment == ["bodyweight", "dumbbell"]
    assert "barbell" in profile.unavailable_equipment
    assert constraints.available_equipment == ["bodyweight", "dumbbell"]
    assert "barbell" in constraints.unavailable_equipment
    assert constraints.confidence == "High"
    assert "explicit_equipment_profile" in constraints.reason_codes


def test_bodyweight_only_profile_avoids_equipment_requiring_exercises(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    save_equipment_profile(
        user_id=102,
        training_environment="bodyweight_only",
        available_equipment=[],
        unavailable_equipment=[],
    )
    health_state = build_user_health_state(102)
    approved = build_approved_workout_plan(health_state)

    assert approved.exercises
    for exercise in approved.exercises:
        assert exercise.equipment_required == ["bodyweight"]


def test_dumbbell_bodyweight_profile_avoids_barbell_machine_and_cable(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    save_equipment_profile(
        user_id=102,
        training_environment="limited_equipment",
        available_equipment=["dumbbell", "bodyweight"],
        unavailable_equipment=["barbell", "machine", "cable"],
    )
    health_state = build_user_health_state(102)
    approved = build_approved_workout_plan(health_state)

    forbidden = {"barbell", "machine", "cable"}
    for exercise in approved.exercises:
        assert not (set(exercise.equipment_required) & forbidden)


def test_equipment_profile_api_get_and_put(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    default_response = client.get("/users/105/equipment-profile")
    assert default_response.status_code == 200
    default_payload = default_response.json()
    assert default_payload["success"] is True
    assert default_payload["source"] == "default"
    assert "dumbbell" in default_payload["equipment_profile"]["available_equipment"]

    put_response = client.put(
        "/users/105/equipment-profile",
        json={
            "training_environment": "bodyweight_only",
            "available_equipment": [],
            "unavailable_equipment": [],
        },
    )
    assert put_response.status_code == 200
    put_payload = put_response.json()
    assert put_payload["success"] is True
    assert put_payload["source"] == "explicit"
    assert put_payload["equipment_profile"]["available_equipment"] == ["bodyweight"]
    assert "barbell" in put_payload["equipment_profile"]["unavailable_equipment"]

    get_response = client.get("/users/105/equipment-profile")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["source"] == "explicit"
    assert get_payload["equipment_profile"]["training_environment"] == "bodyweight_only"


def test_workout_plan_preview_respects_explicit_equipment_profile(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    save_equipment_profile(
        user_id=105,
        training_environment="bodyweight_only",
        available_equipment=[],
        unavailable_equipment=[],
    )

    client = TestClient(app)
    response = client.get("/workout-plans/preview/105")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["scenario"] == "data_quality_limited"
    assert payload["workout_constraints"]["available_equipment"] == ["bodyweight"]
    assert (
        "explicit_equipment_profile" in payload["workout_constraints"]["reason_codes"]
    )

    exercises = payload["approved_workout_plan"]["exercises"]
    assert exercises
    for exercise in exercises:
        assert exercise["equipment_required"] == ["bodyweight"]
