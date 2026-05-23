from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import QA_USER_IDS, seed_qa_scenarios
from services.user_state_service import build_user_health_state


def test_seed_qa_scenarios_runs_and_health_state_aligns(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")

    seeded_users = seed_qa_scenarios()

    assert [user.user_id for user in seeded_users] == list(QA_USER_IDS)

    under_recovered = build_user_health_state(101)
    assert under_recovered.recovery_state.fatigue_risk == "High"
    assert under_recovered.training_state.training_load == "High"
    assert under_recovered.nutrition_training_alignment in {"Mismatch", "Needs Support"}

    mismatch = build_user_health_state(103)
    assert mismatch.nutrition_training_alignment == "Mismatch"

    well_recovered = build_user_health_state(102)
    assert well_recovered.recovery_state.readiness_level == "High"
    assert well_recovered.training_state.avg_rir == 2.0
    assert well_recovered.nutrition_state.calorie_status != "Unknown"

    messy_logging = build_user_health_state(105)
    assert messy_logging.nutrition_state.calorie_status == "Unknown"
    assert "Unusually high micronutrient values" in (
        messy_logging.nutrition_state.nutrition_summary
    )


def test_seeded_qa_users_return_health_state_success(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    client = TestClient(app)

    for user_id in QA_USER_IDS:
        response = client.get(f"/health-state/{user_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
