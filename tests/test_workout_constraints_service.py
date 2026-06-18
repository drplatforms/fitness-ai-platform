import database
from scripts.seed_qa_scenarios import QA_USER_IDS, seed_qa_scenarios
from services.user_state_service import build_user_health_state
from services.workout_constraint_service import build_workout_constraints


def test_workout_constraints_use_safe_defaults_and_recent_exercises(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    for user_id in QA_USER_IDS:
        health_state = build_user_health_state(user_id)
        constraints = build_workout_constraints(health_state)

        assert "dumbbell" in constraints.available_equipment
        assert "bodyweight" in constraints.available_equipment
        assert constraints.unavailable_equipment == []
        assert constraints.movement_restrictions == []
        assert constraints.sore_regions == []
        assert constraints.recent_exercises
        assert constraints.confidence == "Low"
        assert "safe_default_equipment_assumptions" in constraints.reason_codes
        assert "recent_exercise_history_available" in constraints.reason_codes
