from dataclasses import asdict

from fastapi.testclient import TestClient

import api.routes.reports as reports_route
import api.routes.workouts as workouts_route
from api.main import app
from models.user_state_models import (
    UserHealthState,
    UserNutritionState,
    UserRecoveryState,
    UserTrainingState,
)


def _fake_health_state() -> UserHealthState:
    return UserHealthState(
        user_id=1,
        user_name="QA User",
        primary_goal="fat_loss",
        recovery_state=UserRecoveryState(
            avg_sleep="No data",
            avg_energy="No data",
            avg_soreness="No data",
            weight_change="No data",
            recovery_score=0,
            fatigue_risk="Unknown",
            readiness_level="Unknown",
            sleep_trend="Unknown",
            weight_trend="Unknown",
        ),
        nutrition_state=UserNutritionState(
            nutrition_summary="No nutrition data logged.",
            has_nutrition_data=False,
            calories="Unknown",
            protein_grams="Unknown",
            carbohydrate_grams="Unknown",
            fat_grams="Unknown",
            protein_status="Unknown",
            calorie_status="Unknown",
            recovery_nutrition_status="Unknown",
        ),
        training_state=UserTrainingState(
            workout_summary="No workout data available.",
            has_workout_data=False,
            workout_count=0,
            adherence_level="Inactive",
            training_trend="Inactive",
            total_volume_load=0.0,
            avg_rir="No data",
            training_load="Inactive",
            recovery_demand="Low",
        ),
        system_stress_level="Managed",
        nutrition_training_alignment="Aligned",
        coordinator_focus="Maintain current direction and progress gradually.",
    )


def test_health_state_smoke(monkeypatch):
    monkeypatch.setattr(
        reports_route,
        "build_user_health_state",
        lambda user_id: _fake_health_state(),
    )

    client = TestClient(app)
    response = client.get("/health-state/1")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["health_state"] == asdict(_fake_health_state())


def test_exercises_smoke(monkeypatch):
    monkeypatch.setattr(
        workouts_route,
        "get_all_exercises",
        lambda: [
            {
                "id": 1,
                "name": "Barbell Bench Press",
                "muscle_group": "Chest",
                "equipment": "Barbell",
            }
        ],
    )

    client = TestClient(app)
    response = client.get("/exercises")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["exercises"][0]["name"] == "Barbell Bench Press"


def test_recent_workouts_smoke(monkeypatch):
    monkeypatch.setattr(
        workouts_route,
        "get_recent_workouts",
        lambda user_id: [
            {
                "session": {
                    "id": 1,
                    "workout_name": "QA Workout",
                    "workout_date": "2026-05-22",
                    "duration_minutes": 30,
                },
                "sets": [],
            }
        ],
    )

    client = TestClient(app)
    response = client.get("/workouts/1")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["workouts"][0]["session"]["workout_name"] == "QA Workout"


def test_report_history_smoke(monkeypatch):
    monkeypatch.setattr(
        reports_route,
        "get_health_report_history",
        lambda user_id, limit=5: [
            {
                "id": 1,
                "user_id": user_id,
                "report_text": "Fake report history item",
                "created_at": "2026-05-22 12:00:00",
            }
        ],
    )

    client = TestClient(app)
    response = client.get("/reports/history/1")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["reports"][0]["report_text"] == "Fake report history item"
