from __future__ import annotations

from datetime import date as date_cls

from fastapi.testclient import TestClient

import api.routes.nutrition_target_formula as formula_route
from api.main import app
from models.user_state_models import (
    UserHealthState,
    UserNutritionState,
    UserRecoveryState,
    UserTrainingState,
)


def _fake_health_state(
    *,
    user_id: int = 102,
    body_weight: float | None = 190,
    height_cm: float | None = 177.8,
    age: int | None = 39,
    activity_level: str | None = "moderate",
    primary_goal: str | None = "strength_and_recomposition",
) -> UserHealthState:
    return UserHealthState(
        user_id=user_id,
        user_name="QA User",
        primary_goal=primary_goal,
        recovery_state=UserRecoveryState(
            avg_sleep=7.5,
            avg_energy=8,
            avg_soreness=3,
            weight_change=0,
            recovery_score=90,
            fatigue_risk="Low",
            readiness_level="High",
            sleep_trend="Improving",
            weight_trend="Stable",
        ),
        nutrition_state=UserNutritionState(
            nutrition_summary="Calories and macros logged.",
            has_nutrition_data=True,
            calories=2200,
            protein_grams=170,
            carbohydrate_grams=220,
            fat_grams=70,
            protein_status="Logged",
            calorie_status="Logged - Higher Intake",
            recovery_nutrition_status="Logged - Review in Context",
        ),
        training_state=UserTrainingState(
            workout_summary="Recent controlled training.",
            has_workout_data=True,
            workout_count=4,
            adherence_level="Moderate",
            training_trend="Stable",
            total_volume_load=12000,
            avg_rir=2.5,
            training_load="Moderate",
            recovery_demand="Normal",
        ),
        system_stress_level="Managed",
        nutrition_training_alignment="Aligned",
        coordinator_focus="Maintain current direction and progress gradually.",
        age=age,
        height_cm=height_cm,
        starting_weight=body_weight,
        latest_body_weight=body_weight if body_weight is not None else "Unknown",
        goal_weight=180,
        activity_level=activity_level,
    )


def _patch_profile_and_health_state(
    monkeypatch,
    *,
    health_state: UserHealthState | None = None,
    profile: dict | None = None,
) -> None:
    resolved_health_state = health_state or _fake_health_state()
    resolved_profile = profile or {
        "id": resolved_health_state.user_id,
        "gender": "Male",
    }

    monkeypatch.setattr(
        formula_route,
        "get_user_profile",
        lambda user_id: resolved_profile,
    )
    monkeypatch.setattr(
        formula_route,
        "build_user_health_state",
        lambda user_id: resolved_health_state,
    )


def test_formula_targets_endpoint_returns_approved_macro_target_contract(monkeypatch):
    _patch_profile_and_health_state(monkeypatch)

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 102
    assert payload["calculation_date"] == date_cls.today().isoformat()
    assert payload["confidence"] in {"Moderate", "High"}
    assert payload["display_flags"] == {
        "allow_calorie_targets": True,
        "allow_protein_targets": True,
        "allow_carbohydrate_targets": True,
        "allow_fat_targets": True,
    }
    assert (
        payload["approved_macro_targets"]["calorie_target"]["display_allowed"] is True
    )
    assert (
        payload["approved_macro_targets"]["protein_target_g"]["display_allowed"] is True
    )
    assert (
        payload["approved_macro_targets"]["carbohydrate_target_g"]["display_allowed"]
        is True
    )
    assert payload["approved_macro_targets"]["fat_target_g"]["display_allowed"] is True
    assert payload["formula_metadata"]["formula_name"]
    assert payload["formula_metadata"]["formula_version"]
    assert payload["formula_metadata"]["inputs_used"]
    assert payload["formula_metadata"]["rounding_rules"]


def test_formula_targets_endpoint_supports_explicit_date(monkeypatch):
    _patch_profile_and_health_state(monkeypatch)

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula?date=2026-06-01")

    assert response.status_code == 200
    assert response.json()["calculation_date"] == "2026-06-01"


def test_formula_targets_endpoint_rejects_invalid_date(monkeypatch):
    _patch_profile_and_health_state(monkeypatch)

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula?date=06-01-2026")

    assert response.status_code == 400
    assert response.json()["detail"] == "date must use YYYY-MM-DD format."


def test_formula_targets_endpoint_returns_404_for_missing_user(monkeypatch):
    monkeypatch.setattr(formula_route, "get_user_profile", lambda user_id: None)

    client = TestClient(app)
    response = client.get("/nutrition/9999/targets/formula")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_missing_body_weight_blocks_protein_display(monkeypatch):
    _patch_profile_and_health_state(
        monkeypatch,
        health_state=_fake_health_state(body_weight=None),
    )

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula")

    assert response.status_code == 200
    payload = response.json()
    assert payload["display_flags"]["allow_protein_targets"] is False
    protein_target = payload["approved_macro_targets"]["protein_target_g"]
    assert protein_target["display_allowed"] is False
    assert protein_target["value"] is None
    assert protein_target["display_value"] is None


def test_body_weight_allows_protein_only_approval_when_calories_are_blocked(
    monkeypatch,
):
    _patch_profile_and_health_state(
        monkeypatch,
        health_state=_fake_health_state(
            body_weight=190,
            height_cm=None,
            age=None,
            activity_level=None,
            primary_goal=None,
        ),
        profile={"id": 102, "gender": None},
    )

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula")

    assert response.status_code == 200
    payload = response.json()
    assert payload["confidence"] in {"Limited", "Low"}
    assert payload["display_flags"] == {
        "allow_calorie_targets": False,
        "allow_protein_targets": True,
        "allow_carbohydrate_targets": False,
        "allow_fat_targets": False,
    }
    assert (
        payload["approved_macro_targets"]["protein_target_g"]["display_allowed"] is True
    )
    assert (
        payload["approved_macro_targets"]["calorie_target"]["display_allowed"] is False
    )
    assert payload["approved_macro_targets"]["calorie_target"]["value"] is None
    assert (
        payload["approved_macro_targets"]["carbohydrate_target_g"]["display_allowed"]
        is False
    )
    assert payload["approved_macro_targets"]["fat_target_g"]["display_allowed"] is False
    assert payload["limitations"]


def test_missing_height_blocks_calories_and_carbs(monkeypatch):
    _patch_profile_and_health_state(
        monkeypatch,
        health_state=_fake_health_state(height_cm=None),
    )

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula")

    assert response.status_code == 200
    payload = response.json()
    assert payload["display_flags"]["allow_calorie_targets"] is False
    assert payload["display_flags"]["allow_carbohydrate_targets"] is False
    assert payload["approved_macro_targets"]["calorie_target"]["value"] is None
    assert payload["approved_macro_targets"]["carbohydrate_target_g"]["value"] is None
    assert "missing_height" in payload["reason_codes"]


def test_missing_age_blocks_calories(monkeypatch):
    _patch_profile_and_health_state(
        monkeypatch,
        health_state=_fake_health_state(age=None),
    )

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula")

    assert response.status_code == 200
    payload = response.json()
    assert payload["display_flags"]["allow_calorie_targets"] is False
    assert "missing_age" in payload["reason_codes"]


def test_missing_sex_blocks_calories(monkeypatch):
    _patch_profile_and_health_state(
        monkeypatch,
        profile={"id": 102, "gender": None},
    )

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula")

    assert response.status_code == 200
    payload = response.json()
    assert payload["display_flags"]["allow_calorie_targets"] is False
    assert "missing_sex" in payload["reason_codes"]


def test_missing_activity_level_blocks_calories(monkeypatch):
    _patch_profile_and_health_state(
        monkeypatch,
        health_state=_fake_health_state(activity_level=None),
    )

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula")

    assert response.status_code == 200
    payload = response.json()
    assert payload["display_flags"]["allow_calorie_targets"] is False
    assert "missing_activity_level" in payload["reason_codes"]


def test_missing_goal_context_blocks_calories(monkeypatch):
    _patch_profile_and_health_state(
        monkeypatch,
        health_state=_fake_health_state(primary_goal=None),
    )

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula")

    assert response.status_code == 200
    payload = response.json()
    assert payload["display_flags"]["allow_calorie_targets"] is False
    assert "missing_primary_goal" in payload["reason_codes"]


def test_formula_targets_public_response_does_not_expose_internals(monkeypatch):
    _patch_profile_and_health_state(monkeypatch)

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula")

    assert response.status_code == 200
    payload_text = str(response.json()).lower()
    forbidden_public_terms = [
        "validation_errors",
        "validator",
        "traceback",
        "sql",
        "database row",
        "crewai",
        "ollama",
        "provider metadata",
        "raw_output",
    ]
    for term in forbidden_public_terms:
        assert term not in payload_text


def test_validation_failure_returns_safe_400_without_internals(monkeypatch):
    _patch_profile_and_health_state(monkeypatch)

    def broken_approval(formula_result):
        raise ValueError("validator internal detail: impossible target")

    monkeypatch.setattr(
        formula_route,
        "approve_validated_macro_targets",
        broken_approval,
    )

    client = TestClient(app)
    response = client.get("/nutrition/102/targets/formula")

    assert response.status_code == 400
    assert response.json() == {"detail": "Nutrition target formula validation failed."}
