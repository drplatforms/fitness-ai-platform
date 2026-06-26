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
    "exercise_ball",
    "ez_bar",
    "plates",
    "pull_up_bar",
    "rack",
    "resistance_band",
    "rope_cable_attachment",
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

    assert 225 <= len(entries) <= 260
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
    assert "Rope Triceps Pressdown" in names
    assert "Stability Ball Rollout" in names
    assert "Dumbbell Bulgarian Split Squat" in names
    assert "Barbell Rollout" in names


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


def test_home_gym_preview_adds_accessory_slot_when_equipment_allows(
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
    accessory = approved.exercises[3]
    accessory_entry = find_catalog_entry_by_name(accessory.name)

    assert len(approved.exercises) == 5
    assert accessory_entry is not None
    assert accessory_entry.movement_pattern in {
        "arms_biceps",
        "arms_triceps",
        "carry",
        "conditioning",
        "core_anti_extension",
        "core_anti_rotation",
        "horizontal_pull",
        "vertical_push",
    }
    assert set(accessory.equipment_required).issubset(set(USER_HOME_GYM_EQUIPMENT))


def test_bodyweight_only_fourth_slot_remains_bodyweight_compatible(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    save_equipment_profile(
        user_id=105,
        training_environment="bodyweight_only",
        available_equipment=["bodyweight"],
        unavailable_equipment=[
            "adjustable_bench",
            "barbell",
            "bike",
            "cable",
            "dumbbell",
            "ez_bar",
            "machine",
            "plates",
            "pull_up_bar",
            "rack",
            "resistance_band",
            "treadmill",
        ],
    )

    health_state = build_user_health_state(105)
    approved = build_approved_workout_plan(health_state)

    assert len(approved.exercises) == 5
    assert all(
        set(exercise.equipment_required).issubset({"bodyweight"})
        for exercise in approved.exercises
    )


def test_limited_equipment_accessory_avoids_unavailable_equipment(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    unavailable = [
        "adjustable_bench",
        "barbell",
        "bike",
        "cable",
        "ez_bar",
        "machine",
        "plates",
        "pull_up_bar",
        "rack",
        "resistance_band",
        "treadmill",
    ]
    save_equipment_profile(
        user_id=102,
        training_environment="limited_equipment",
        available_equipment=["bodyweight", "dumbbell"],
        unavailable_equipment=unavailable,
    )

    health_state = build_user_health_state(102)
    approved = build_approved_workout_plan(health_state)

    assert len(approved.exercises) == 5
    for exercise in approved.exercises:
        assert set(exercise.equipment_required).isdisjoint(set(unavailable))
        assert set(exercise.equipment_required).issubset({"bodyweight", "dumbbell"})


def test_recovery_limited_accessory_slot_avoids_aggressive_finisher_language(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    save_equipment_profile(
        user_id=101,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    health_state = build_user_health_state(101)
    approved = build_approved_workout_plan(health_state)
    rendered = " ".join(
        [approved.progression_guidance]
        + [exercise.notes for exercise in approved.exercises]
    ).lower()

    assert 4 <= len(approved.exercises) <= 5
    assert all(exercise.rir_min >= 2 for exercise in approved.exercises)
    assert "max effort" not in rendered
    assert "to failure" not in rendered
    assert "hard finisher" not in rendered


def test_data_quality_limited_fourth_slot_stays_simple_and_manageable(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    save_equipment_profile(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    health_state = build_user_health_state(105)
    approved = build_approved_workout_plan(health_state)
    fourth_exercise = approved.exercises[3]
    rendered = " ".join(
        [approved.session_focus, approved.rationale, fourth_exercise.notes]
    ).lower()

    assert len(approved.exercises) == 5
    assert fourth_exercise.name in {
        "Dead Bug",
        "Treadmill Walk",
        "Bike Steady State",
        "Band Pull-Apart",
    }
    assert "manageable" in rendered or "simple" in rendered
    assert "overtraining" not in rendered
    assert "stalled progress" not in rendered


def test_expanded_home_gym_catalog_contains_user_specific_equipment(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    entries = get_exercise_catalog()
    names = {entry.name for entry in entries}
    equipment = {item for entry in entries for item in entry.equipment_required}

    assert "exercise_ball" in equipment
    assert "rope_cable_attachment" in equipment
    assert "Stability Ball Hamstring Curl" in names
    assert "Rope Face Pull" in names
    assert "Cable Pull-Through" in names
    assert "Dumbbell Single-Leg RDL" in names
    assert "Band Pallof Press" in names


def test_home_gym_filter_includes_exercise_ball_and_rope_attachment_options(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    entries = filter_exercises_for_equipment(
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    names = {entry.name for entry in entries}

    assert "Rope Triceps Pressdown" in names
    assert "Rope Face Pull" in names
    assert "Cable Crunch" in names
    assert "Stability Ball Rollout" in names
    assert "Stability Ball Wall Squat" in names
    assert all("machine" not in entry.equipment_required for entry in entries)


def test_limited_equipment_without_new_home_tools_excludes_rope_and_ball(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    entries = filter_exercises_for_equipment(
        available_equipment=["bodyweight", "dumbbell"],
        unavailable_equipment=[
            "adjustable_bench",
            "barbell",
            "bike",
            "cable",
            "exercise_ball",
            "ez_bar",
            "machine",
            "plates",
            "pull_up_bar",
            "rack",
            "resistance_band",
            "rope_cable_attachment",
            "treadmill",
        ],
    )

    assert entries
    assert all(
        "exercise_ball" not in entry.equipment_required
        and "rope_cable_attachment" not in entry.equipment_required
        for entry in entries
    )


def test_expanded_catalog_keeps_machine_exercises_excludable(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    entries = filter_exercises_for_equipment(
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    assert len(entries) >= 100
    assert all("machine" not in entry.equipment_required for entry in entries)


def test_exercise_catalog_expansion_v1_adds_curated_reviewable_entries(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    entries = get_exercise_catalog()
    names = {entry.name for entry in entries}

    assert len(entries) == 240
    for expected_name in {
        "Wall Push-Up",
        "Scapular Push-Up",
        "Dumbbell Squeeze Press",
        "Dumbbell Suitcase Deadlift",
        "Barbell Shrug",
        "Rack Pull",
        "Band Chest Press",
        "Band Romanian Deadlift",
        "Cable Chest Press",
        "Cable Romanian Deadlift",
        "Treadmill Recovery Walk",
        "Bike Easy Spin",
        "Cat-Cow",
        "Half-Kneeling Hip Flexor Stretch",
    }:
        assert expected_name in names


def test_exercise_catalog_expansion_v1_has_no_duplicate_names(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    names = [entry.name.strip().lower() for entry in get_exercise_catalog()]

    assert len(names) == len(set(names))


def test_exercise_catalog_expansion_v1_required_tags_are_valid(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    allowed_types = {"strength", "core", "conditioning", "mobility"}
    allowed_patterns = {
        "arms_biceps",
        "arms_triceps",
        "carry",
        "conditioning",
        "core_anti_extension",
        "core_anti_rotation",
        "hinge",
        "horizontal_pull",
        "horizontal_push",
        "lunge",
        "mobility",
        "squat",
        "vertical_pull",
        "vertical_push",
    }
    allowed_difficulties = {"beginner", "intermediate", "advanced"}
    allowed_equipment = set(USER_HOME_GYM_EQUIPMENT) | {"bodyweight", "machine"}

    for entry in get_exercise_catalog():
        assert entry.exercise_type in allowed_types
        assert entry.movement_pattern in allowed_patterns
        assert entry.difficulty in allowed_difficulties
        assert entry.name.strip()
        assert entry.primary_muscle_groups
        assert entry.equipment_required
        assert set(entry.equipment_required).issubset(allowed_equipment)


def test_exercise_catalog_expansion_v1_improves_mobility_and_recovery_depth(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    entries = get_exercise_catalog()
    mobility_names = {
        entry.name for entry in entries if entry.exercise_type == "mobility"
    }

    assert len(mobility_names) >= 12
    assert "Cat-Cow" in mobility_names
    assert "Quadruped T-Spine Rotation" in mobility_names
    assert "Half-Kneeling Hip Flexor Stretch" in mobility_names
    assert "Child's Pose Lat Stretch" in mobility_names
    assert "Pull-Up Bar Dead Hang" in mobility_names


def test_home_gym_filter_includes_expanded_v1_equipment_aware_options(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    entries = filter_exercises_for_equipment(
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    names = {entry.name for entry in entries}

    assert "Dumbbell Squeeze Press" in names
    assert "Rack Pull" in names
    assert "Band Chest Press" in names
    assert "Cable Chest Press" in names
    assert "Treadmill Recovery Walk" in names
    assert "Bike Easy Spin" in names
    assert all("machine" not in entry.equipment_required for entry in entries)


def test_limited_equipment_filter_keeps_expanded_v1_options_compatible(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    entries = filter_exercises_for_equipment(
        available_equipment=["bodyweight", "dumbbell"],
        unavailable_equipment=[
            "adjustable_bench",
            "barbell",
            "bike",
            "cable",
            "exercise_ball",
            "ez_bar",
            "machine",
            "plates",
            "pull_up_bar",
            "rack",
            "resistance_band",
            "rope_cable_attachment",
            "treadmill",
        ],
    )
    names = {entry.name for entry in entries}

    assert "Wall Push-Up" in names
    assert "Scapular Push-Up" in names
    assert "Dumbbell Suitcase Deadlift" in names
    assert "Dumbbell Farmer March" in names
    assert "Dumbbell Squeeze Press" not in names
    assert all(
        set(entry.equipment_required).issubset({"bodyweight", "dumbbell"})
        for entry in entries
    )
