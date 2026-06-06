from __future__ import annotations

import database
from scripts.seed_user_profiles import SEED_PROFILES, seed_user_profiles
from services.equipment_profile_service import get_equipment_profile
from services.nutrition_target_formula_service import (
    build_nutrition_target_formula_inputs,
    calculate_nutrition_target_formula,
)
from services.nutrition_target_formula_validation_service import (
    approve_validated_macro_targets,
)
from services.user_service import get_user_profile
from services.user_state_service import build_user_health_state
from services.workout_plan_service import build_approved_workout_plan


def _profile_sex(user_id: int) -> str | None:
    profile = get_user_profile(user_id)
    return profile["gender"] if profile else None


def _formula_result_for_user(user_id: int):
    health_state = build_user_health_state(user_id)
    inputs = build_nutrition_target_formula_inputs(
        health_state,
        calculation_date="2026-06-06",
        sex=_profile_sex(user_id),
        input_source_metadata={"consumer": "seed_user_profiles_test"},
    )
    return calculate_nutrition_target_formula(inputs)


def test_seed_user_profiles_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")

    first_run = seed_user_profiles()
    second_run = seed_user_profiles()

    assert [profile.user_id for profile in first_run] == [
        profile.user_id for profile in SEED_PROFILES
    ]
    assert [profile.user_id for profile in second_run] == [
        profile.user_id for profile in SEED_PROFILES
    ]

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM users
        WHERE id IN (1, 102, 103, 104, 105)
        """)
    assert cursor.fetchone()["count"] == 5

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM user_equipment_profiles
        WHERE user_id IN (1, 102, 103, 104, 105)
        """)
    assert cursor.fetchone()["count"] == 5

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM daily_checkins
        WHERE notes LIKE 'seed_user_profiles_v1:%'
          AND user_id = 102
        """)
    assert cursor.fetchone()["count"] == 4
    conn.close()


def test_complete_profile_user_produces_approved_formula_targets(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_user_profiles()

    result = _formula_result_for_user(102)
    approved = approve_validated_macro_targets(result)

    assert approved.display_flags["allow_calorie_targets"] is True
    assert approved.display_flags["allow_protein_targets"] is True
    assert approved.display_flags["allow_carbohydrate_targets"] is True
    assert approved.display_flags["allow_fat_targets"] is True
    assert approved.confidence in {"Moderate", "High"}


def test_partial_profile_user_remains_protein_only(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_user_profiles()

    result = _formula_result_for_user(103)
    approved = approve_validated_macro_targets(result)

    assert approved.display_flags["allow_protein_targets"] is True
    assert approved.display_flags["allow_calorie_targets"] is False
    assert approved.display_flags["allow_carbohydrate_targets"] is False
    assert approved.display_flags["allow_fat_targets"] is False
    assert "missing_height" in approved.reason_codes
    assert "missing_age" in approved.reason_codes
    assert "missing_sex" in approved.reason_codes
    assert "missing_activity_level" in approved.reason_codes
    assert "missing_primary_goal" in approved.reason_codes


def test_missing_body_weight_user_blocks_protein_target(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_user_profiles()

    health_state = build_user_health_state(104)
    result = _formula_result_for_user(104)
    approved = approve_validated_macro_targets(result)

    assert health_state.latest_body_weight is None
    assert health_state.starting_weight is None
    assert approved.display_flags["allow_protein_targets"] is False
    assert "missing_body_weight" in approved.reason_codes


def test_seeded_equipment_profile_supports_home_gym_workout_preview(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_user_profiles()

    equipment_profile = get_equipment_profile(102)
    assert equipment_profile is not None
    assert equipment_profile.training_environment == "home_gym"
    assert "barbell" in equipment_profile.available_equipment
    assert "machine" in equipment_profile.unavailable_equipment

    preview = build_approved_workout_plan(build_user_health_state(102))
    assert preview.exercises
    for exercise in preview.exercises:
        assert "machine" not in exercise.equipment_required
