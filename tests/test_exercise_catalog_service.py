import database
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.exercise_catalog_service import (
    filter_exercises_for_equipment,
    find_catalog_entry_by_name,
    get_exercise_catalog,
    seed_exercise_catalog,
)
from services.user_state_service import build_user_health_state
from services.workout_plan_service import (
    _catalog_equipment_for_option,
    build_approved_workout_plan,
)

USER_HOME_GYM_EQUIPMENT = [
    "adjustable_bench",
    "barbell",
    "bike",
    "bodyweight",
    "cable",
    "dumbbell",
    "ez_bar",
    "plates",
    "pull_up_bar",
    "rack",
    "resistance_band",
    "treadmill",
]


def _plan_movement_patterns(approved):
    patterns = set()
    for exercise in approved.exercises:
        entry = find_catalog_entry_by_name(exercise.name)
        if entry is not None:
            patterns.add(entry.movement_pattern)
    return patterns


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    seed_exercise_catalog()


def test_exercise_catalog_seeds_curated_entries_with_requirements(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    entries = get_exercise_catalog()

    assert 40 <= len(entries) <= 75
    assert all(entry.name for entry in entries)
    assert all(entry.movement_pattern for entry in entries)
    assert all(entry.exercise_type for entry in entries)
    assert all(entry.primary_muscle_groups for entry in entries)
    assert all(entry.equipment_required for entry in entries)

    names = {entry.name for entry in entries}
    assert "Back Squat" in names
    assert "Dumbbell Bench Press" in names
    assert "Pull-Up" in names
    assert "Cable Row" in names
    assert "Treadmill Incline Walk" in names


def test_filtering_by_bodyweight_only_returns_bodyweight_compatible_exercises(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    entries = filter_exercises_for_equipment(
        available_equipment=["bodyweight"],
        unavailable_equipment=[
            "adjustable_bench",
            "barbell",
            "cable",
            "dumbbell",
            "machine",
            "pull_up_bar",
            "rack",
            "resistance_band",
        ],
    )

    assert entries
    for entry in entries:
        assert set(entry.equipment_required).issubset({"bodyweight"})


def test_filtering_by_dumbbell_and_bench_returns_compatible_exercises(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    entries = filter_exercises_for_equipment(
        available_equipment=["bodyweight", "dumbbell", "adjustable_bench"],
        unavailable_equipment=["barbell", "cable", "machine"],
    )

    names = {entry.name for entry in entries}
    assert "Dumbbell Bench Press" in names
    assert "Chest-Supported Dumbbell Row" in names
    assert "Goblet Squat" in names
    assert "Back Squat" not in names
    assert "Cable Row" not in names


def test_home_gym_profile_includes_available_user_equipment_and_excludes_machines(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    save_equipment_profile(
        user_id=102,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    health_state = build_user_health_state(102)
    approved = build_approved_workout_plan(health_state)

    assert approved.exercises
    exercise_names = {exercise.name for exercise in approved.exercises}
    equipment_used = {
        equipment
        for exercise in approved.exercises
        for equipment in exercise.equipment_required
    }

    assert "machine" not in equipment_used
    assert any(
        equipment in equipment_used
        for equipment in {"barbell", "dumbbell", "cable", "pull_up_bar"}
    )
    assert "Leg Press" not in exercise_names
    assert "Machine Chest Press" not in exercise_names
    assert "Machine Row" not in exercise_names


def test_machine_exercises_are_excluded_when_machine_is_unavailable(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    entries = filter_exercises_for_equipment(
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    assert entries
    assert all("machine" not in entry.equipment_required for entry in entries)


def test_workout_preview_uses_catalog_compatible_exercises(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    save_equipment_profile(
        user_id=105,
        training_environment="limited_equipment",
        available_equipment=["bodyweight", "dumbbell"],
        unavailable_equipment=[
            "adjustable_bench",
            "barbell",
            "cable",
            "machine",
            "plates",
            "pull_up_bar",
            "rack",
        ],
    )

    health_state = build_user_health_state(105)
    approved = build_approved_workout_plan(health_state)

    assert approved.exercises
    allowed = {"bodyweight", "dumbbell"}
    for exercise in approved.exercises:
        assert set(exercise.equipment_required).issubset(allowed)


def test_hyphenated_exercise_names_resolve_to_catalog_entries(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    for name in [
        "Chest-Supported Row",
        "Chest-Supported Dumbbell Row",
        "EZ-Bar Curl",
        "EZ-Bar Skull Crusher",
        "Band-Assisted Pull-Up",
    ]:
        entry = find_catalog_entry_by_name(name)
        assert entry is not None
        assert entry.name == name


def test_catalog_metadata_overrides_fallback_equipment_requirements(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    name, equipment_required = _catalog_equipment_for_option(
        "Chest-Supported Row",
        ["dumbbell"],
    )

    assert name == "Chest-Supported Row"
    assert set(equipment_required) == {"adjustable_bench", "dumbbell"}


def test_chest_supported_row_requires_adjustable_bench(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    entry = find_catalog_entry_by_name("Chest-Supported Row")

    assert entry is not None
    assert "adjustable_bench" in entry.equipment_required
    assert "dumbbell" in entry.equipment_required


def test_limited_equipment_without_bench_does_not_select_chest_supported_row(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    save_equipment_profile(
        user_id=101,
        training_environment="limited_equipment",
        available_equipment=["bodyweight", "dumbbell"],
        unavailable_equipment=[
            "adjustable_bench",
            "barbell",
            "cable",
            "machine",
            "plates",
            "pull_up_bar",
            "rack",
        ],
    )

    health_state = build_user_health_state(101)
    approved = build_approved_workout_plan(health_state)

    exercise_names = {exercise.name for exercise in approved.exercises}
    assert "Chest-Supported Row" not in exercise_names
    assert "Chest-Supported Dumbbell Row" not in exercise_names

    allowed = {"bodyweight", "dumbbell"}
    for exercise in approved.exercises:
        assert set(exercise.equipment_required).issubset(allowed)


def test_home_gym_preview_uses_varied_movement_patterns(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    save_equipment_profile(
        user_id=102,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    health_state = build_user_health_state(102)
    approved = build_approved_workout_plan(health_state)
    patterns = _plan_movement_patterns(approved)

    assert len(patterns) >= 3
    assert "hinge" in patterns or "squat" in patterns
    assert "vertical_pull" in patterns or "horizontal_pull" in patterns
    assert "machine" not in {
        equipment
        for exercise in approved.exercises
        for equipment in exercise.equipment_required
    }


def test_home_gym_preview_can_include_hinge_or_vertical_pull(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    save_equipment_profile(
        user_id=102,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    health_state = build_user_health_state(102)
    approved = build_approved_workout_plan(health_state)
    patterns = _plan_movement_patterns(approved)

    assert "hinge" in patterns or "vertical_pull" in patterns


def test_limited_equipment_without_bench_uses_non_bench_alternatives(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    save_equipment_profile(
        user_id=102,
        training_environment="limited_equipment",
        available_equipment=["bodyweight", "dumbbell"],
        unavailable_equipment=[
            "adjustable_bench",
            "barbell",
            "cable",
            "machine",
            "plates",
            "pull_up_bar",
            "rack",
        ],
    )

    health_state = build_user_health_state(102)
    approved = build_approved_workout_plan(health_state)

    assert approved.exercises
    assert all(
        "adjustable_bench" not in exercise.equipment_required
        for exercise in approved.exercises
    )
    assert all(
        set(exercise.equipment_required).issubset({"bodyweight", "dumbbell"})
        for exercise in approved.exercises
    )
