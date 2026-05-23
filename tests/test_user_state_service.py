from services import user_state_service


def _user_profile():
    return {
        "id": 1,
        "name": "QA User",
        "primary_goal": "fat_loss",
    }


def _patch_state_inputs(
    monkeypatch, recovery_data=None, nutrition_data=None, workouts=None
):
    monkeypatch.setattr(
        user_state_service, "get_user_profile", lambda user_id: _user_profile()
    )
    monkeypatch.setattr(
        user_state_service,
        "get_recent_recovery_metrics",
        lambda user_id: recovery_data,
    )
    monkeypatch.setattr(
        user_state_service,
        "get_nutrition_analysis",
        lambda user_id: nutrition_data or {},
    )
    monkeypatch.setattr(
        user_state_service,
        "get_recent_workouts",
        lambda user_id: workouts or [],
    )


def test_health_state_works_when_recovery_data_is_missing(monkeypatch):
    _patch_state_inputs(monkeypatch, recovery_data=None, nutrition_data={}, workouts=[])

    health_state = user_state_service.build_user_health_state(1)

    assert health_state.recovery_state.avg_sleep == "No data"
    assert health_state.recovery_state.fatigue_risk == "Unknown"
    assert health_state.recovery_state.readiness_level == "Unknown"


def test_missing_nutrition_fields_remain_unknown_not_zero(monkeypatch):
    nutrition_data = {
        "Protein": {"amount": 110, "unit": "g"},
    }
    _patch_state_inputs(monkeypatch, recovery_data=None, nutrition_data=nutrition_data)

    health_state = user_state_service.build_user_health_state(1)

    assert health_state.nutrition_state.calories == "Unknown"
    assert health_state.nutrition_state.calorie_status == "Unknown"
    assert health_state.nutrition_state.calories != 0


def test_explicit_zero_nutrition_value_is_distinct_from_missing(monkeypatch):
    nutrition_data = {
        "Calories": {"amount": 0, "unit": "kcal"},
        "Protein": {"amount": 0, "unit": "g"},
        "Carbohydrates": {"amount": 0, "unit": "g"},
    }
    _patch_state_inputs(monkeypatch, recovery_data=None, nutrition_data=nutrition_data)

    health_state = user_state_service.build_user_health_state(1)

    assert health_state.nutrition_state.calories == 0.0
    assert health_state.nutrition_state.calorie_status == "Logged as Zero"
    assert health_state.nutrition_state.protein_status == "Logged as Zero"


def test_rir_one_is_low_rir_high_effort_close_to_failure(monkeypatch):
    workouts = [
        {
            "session": {
                "workout_name": "QA Heavy Session",
                "workout_date": "2026-05-22",
                "duration_minutes": 45,
            },
            "sets": [
                {
                    "name": "Clean and Jerk",
                    "reps": 3,
                    "weight": 185,
                    "rir": 1,
                }
            ],
        }
    ]
    _patch_state_inputs(
        monkeypatch, recovery_data=None, nutrition_data={}, workouts=workouts
    )

    health_state = user_state_service.build_user_health_state(1)

    assert "RIR 1 (low RIR / high effort / close to failure)" in (
        health_state.training_state.workout_summary
    )
    assert "RIR 1 (high RIR" not in health_state.training_state.workout_summary


def test_high_training_with_incomplete_nutrition_creates_mismatch(monkeypatch):
    nutrition_data = {
        "Protein": {"amount": 120, "unit": "g"},
    }
    workouts = [
        {
            "session": {
                "workout_name": "QA High Load Session",
                "workout_date": "2026-05-22",
                "duration_minutes": 75,
            },
            "sets": [
                {
                    "name": "Barbell Squat",
                    "reps": 10,
                    "weight": 225,
                    "rir": 1,
                },
                {
                    "name": "Deadlift",
                    "reps": 8,
                    "weight": 315,
                    "rir": 1,
                },
                {
                    "name": "Leg Press",
                    "reps": 15,
                    "weight": 700,
                    "rir": 1,
                },
                {
                    "name": "Clean and Jerk",
                    "reps": 5,
                    "weight": 185,
                    "rir": 1,
                },
            ],
        }
    ]
    _patch_state_inputs(
        monkeypatch,
        recovery_data=None,
        nutrition_data=nutrition_data,
        workouts=workouts,
    )

    health_state = user_state_service.build_user_health_state(1)

    assert health_state.training_state.training_load == "High"
    assert health_state.nutrition_state.recovery_nutrition_status == (
        "Incomplete - Calories Missing"
    )
    assert health_state.nutrition_training_alignment == "Mismatch"
    assert health_state.coordinator_focus == (
        "Improve nutrition support for current training demand."
    )


def test_suspicious_micronutrients_include_caution_language(monkeypatch):
    nutrition_data = {
        "Vitamin D": {"amount": 9999, "unit": "mcg"},
    }
    _patch_state_inputs(monkeypatch, recovery_data=None, nutrition_data=nutrition_data)

    health_state = user_state_service.build_user_health_state(1)

    assert "Unusually high micronutrient values" in (
        health_state.nutrition_state.nutrition_summary
    )
    assert "database, unit, or logging issues" in (
        health_state.nutrition_state.nutrition_summary
    )
