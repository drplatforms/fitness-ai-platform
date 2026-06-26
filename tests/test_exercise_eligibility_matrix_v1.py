from __future__ import annotations

from services.exercise_eligibility_matrix_service import (
    build_exercise_eligibility_matrix,
    build_exercise_eligibility_summary,
    build_generator_slot_options,
)

HOME_GYM_AVAILABLE_EQUIPMENT = [
    "bodyweight",
    "dumbbell",
    "adjustable_bench",
    "barbell",
    "rack",
    "plates",
    "ez_bar",
    "pull_up_bar",
    "resistance_band",
    "cable",
    "rope_cable_attachment",
    "treadmill",
    "bike",
    "exercise_ball",
]
HOME_GYM_UNAVAILABLE_EQUIPMENT = ["machine"]


def _home_gym_matrix():
    return build_exercise_eligibility_matrix(
        available_equipment=HOME_GYM_AVAILABLE_EQUIPMENT,
        unavailable_equipment=HOME_GYM_UNAVAILABLE_EQUIPMENT,
    )


def _by_name(matrix):
    return {row.exercise_name: row for row in matrix}


def test_eligibility_matrix_classifies_primary_movements():
    rows = _by_name(_home_gym_matrix())

    assert rows["Dumbbell RDL"].is_generator_eligible is True
    assert "eligible_primary" in rows["Dumbbell RDL"].eligibility_roles
    assert "primary:hinge" in rows["Dumbbell RDL"].slot_families

    assert rows["Dumbbell Bench Press"].is_generator_eligible is True
    assert "eligible_primary" in rows["Dumbbell Bench Press"].eligibility_roles
    assert "primary:horizontal_push" in rows["Dumbbell Bench Press"].slot_families

    assert rows["Cable Row"].is_generator_eligible is True
    assert "eligible_primary" in rows["Cable Row"].eligibility_roles
    assert "primary:horizontal_pull" in rows["Cable Row"].slot_families


def test_eligibility_matrix_classifies_specialized_accessory_and_core_movements():
    rows = _by_name(_home_gym_matrix())

    assert rows["Band Face Pull"].is_generator_eligible is True
    assert "specialized_or_accessory" in rows["Band Face Pull"].eligibility_roles
    assert "accessory:upper_back" in rows["Band Face Pull"].slot_families

    assert rows["Cable Face Pull"].is_generator_eligible is True
    assert "specialized_or_accessory" in rows["Cable Face Pull"].eligibility_roles
    assert "accessory:upper_back" in rows["Cable Face Pull"].slot_families

    assert rows["Farmer Carry"].is_generator_eligible is True
    assert "eligible_conditioning" in rows["Farmer Carry"].eligibility_roles
    assert "conditioning:carry" in rows["Farmer Carry"].slot_families

    assert rows["Suitcase Carry"].is_generator_eligible is True
    assert "eligible_conditioning" in rows["Suitcase Carry"].eligibility_roles
    assert "conditioning:carry" in rows["Suitcase Carry"].slot_families

    assert rows["Dead Bug"].is_generator_eligible is True
    assert "eligible_core" in rows["Dead Bug"].eligibility_roles
    assert "core:anti_extension" in rows["Dead Bug"].slot_families

    assert rows["Bird Dog"].is_generator_eligible is True
    assert "eligible_core" in rows["Bird Dog"].eligibility_roles
    assert "core:anti_rotation" in rows["Bird Dog"].slot_families

    assert rows["Side Plank"].is_generator_eligible is True
    assert "eligible_core" in rows["Side Plank"].eligibility_roles
    assert "core:anti_rotation" in rows["Side Plank"].slot_families


def test_eligibility_matrix_respects_equipment_constraints_and_metadata_gaps():
    rows = _by_name(_home_gym_matrix())

    assert rows["Leg Press"].is_equipment_compatible is False
    assert rows["Leg Press"].is_generator_eligible is False
    assert "equipment_excluded" in rows["Leg Press"].reachability_status
    assert any(
        reason.startswith("blocked_unavailable_equipment:machine")
        for reason in rows["Leg Press"].exclusion_reasons
    )

    assert rows["Machine Chest Press"].is_equipment_compatible is False
    assert rows["Machine Chest Press"].is_generator_eligible is False
    assert "equipment_excluded" in rows["Machine Chest Press"].reachability_status

    assert rows["Cat-Cow"].is_equipment_compatible is True
    assert rows["Cat-Cow"].is_generator_eligible is False
    assert any(
        reason.startswith("movement_pattern_unmapped:mobility")
        for reason in rows["Cat-Cow"].exclusion_reasons
    )


def test_eligibility_summary_exposes_reachability_and_exclusion_reasons():
    matrix = _home_gym_matrix()
    summary = build_exercise_eligibility_summary(matrix)

    assert summary["total_active_exercises"] >= 200
    assert summary["total_equipment_compatible_exercises"] >= 200
    assert summary["total_generator_eligible"] >= 200
    assert summary["total_reachable_in_deterministic_sweep"] >= 50
    assert summary["total_not_reachable_in_deterministic_sweep"] >= 100

    exclusion_reason_counts = summary["exclusion_reason_counts"]
    assert (
        "not_supported_by_current_generator_candidate_pools" in exclusion_reason_counts
    )
    assert "movement_pattern_unmapped:mobility" in exclusion_reason_counts
    assert "blocked_unavailable_equipment:machine" in exclusion_reason_counts

    weak_families = set(summary["weak_movement_families"])
    assert "arms_biceps" in weak_families
    assert "arms_triceps" in weak_families
    assert "mobility" in weak_families


def test_generator_slot_options_are_consumable_by_workout_candidate_pools():
    matrix = _home_gym_matrix()

    lunge_options = build_generator_slot_options(matrix, "primary:lunge")
    lunge_names = {name for name, _equipment in lunge_options}
    assert {"Reverse Lunge", "Split Squat", "Dumbbell Split Squat"} <= lunge_names

    upper_back_options = build_generator_slot_options(matrix, "accessory:upper_back")
    upper_back_names = {name for name, _equipment in upper_back_options}
    assert {
        "Band Face Pull",
        "Cable Face Pull",
        "Dumbbell Rear Delt Fly",
    } <= upper_back_names

    core_options = build_generator_slot_options(matrix, "core:anti_rotation")
    core_names = {name for name, _equipment in core_options}
    assert {"Side Plank", "Bird Dog", "Cable Woodchop"} <= core_names

    carry_options = build_generator_slot_options(matrix, "conditioning:carry")
    carry_names = {name for name, _equipment in carry_options}
    assert {"Farmer Carry", "Suitcase Carry"} <= carry_names

    assert all(isinstance(name, str) and name for name, _equipment in lunge_options)
    assert all(isinstance(equipment, list) for _name, equipment in lunge_options)
