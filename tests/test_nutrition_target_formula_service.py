from __future__ import annotations

from models.nutrition_target_formula_models import NutritionTargetFormulaInputs
from models.user_state_models import (
    UserHealthState,
    UserNutritionState,
    UserRecoveryState,
    UserTrainingState,
)
from services.nutrition_target_formula_service import (
    approve_macro_targets,
    build_nutrition_target_formula_inputs,
    calculate_nutrition_target_formula,
)


def _complete_inputs() -> NutritionTargetFormulaInputs:
    return NutritionTargetFormulaInputs(
        user_id=1,
        calculation_date="2026-06-05",
        body_weight_lb=190,
        height_in=70,
        age_years=39,
        sex="male",
        activity_level="moderate",
        training_frequency_per_week=4,
        training_load="Moderate",
        primary_goal="strength_and_recomposition",
        goal_weight_lb=180,
        recovery_status="managed",
        nutrition_logging_quality="complete_enough_for_guidance",
        recent_weight_trend="Stable",
        formula_version_requested="v1_service",
        input_source_metadata={"source": "unit_test"},
    )


def _limited_inputs() -> NutritionTargetFormulaInputs:
    return NutritionTargetFormulaInputs(
        user_id=105,
        calculation_date="2026-06-05",
        body_weight_lb=190,
        height_in=None,
        age_years=None,
        sex=None,
        activity_level=None,
        training_frequency_per_week=None,
        training_load="Unknown",
        primary_goal=None,
        goal_weight_lb=None,
        recovery_status="Unknown",
        nutrition_logging_quality="limited",
        recent_weight_trend="Unknown",
        formula_version_requested="v1_service",
        input_source_metadata={"source": "unit_test_limited"},
    )


def _health_state() -> UserHealthState:
    return UserHealthState(
        user_id=7,
        user_name="Formula User",
        primary_goal="strength_and_recomposition",
        recovery_state=UserRecoveryState(
            avg_sleep=7.2,
            avg_energy=7.0,
            avg_soreness=3.0,
            weight_change=0.0,
            recovery_score=78,
            fatigue_risk="Low",
            readiness_level="Managed",
            sleep_trend="Stable",
            weight_trend="Stable",
        ),
        nutrition_state=UserNutritionState(
            nutrition_summary="Nutrition logging is complete enough for guidance.",
            has_nutrition_data=True,
            calories=2300,
            protein_grams=170,
            carbohydrate_grams=250,
            fat_grams=75,
            protein_status="Logged",
            calorie_status="Logged - Moderate Intake",
            recovery_nutrition_status="Logged - Review in Context",
        ),
        training_state=UserTrainingState(
            workout_summary="Recent training is moderate.",
            has_workout_data=True,
            workout_count=4,
            adherence_level="Consistent",
            training_trend="Stable",
            total_volume_load=12000,
            avg_rir=2.5,
            training_load="Moderate",
            recovery_demand="Normal",
        ),
        system_stress_level="Managed",
        nutrition_training_alignment="Aligned",
        coordinator_focus="Maintain current direction and progress gradually.",
        age=39,
        height_cm=177.8,
        starting_weight=192,
        latest_body_weight=190,
        goal_weight=180,
        activity_level="moderate",
    )


def test_complete_inputs_produce_all_approved_macro_targets():
    result = calculate_nutrition_target_formula(_complete_inputs())
    approved = approve_macro_targets(result)

    assert result.display_flags == {
        "allow_calorie_targets": True,
        "allow_protein_targets": True,
        "allow_carbohydrate_targets": True,
        "allow_fat_targets": True,
    }
    assert result.confidence in {"Moderate", "High"}
    assert approved.calorie_target is not None
    assert approved.protein_target_g is not None
    assert approved.carbohydrate_target_g is not None
    assert approved.fat_target_g is not None
    assert approved.calorie_target.display_allowed is True
    assert approved.protein_target_g.display_allowed is True
    assert approved.carbohydrate_target_g.display_allowed is True
    assert approved.fat_target_g.display_allowed is True


def test_missing_body_weight_blocks_protein_target():
    inputs = NutritionTargetFormulaInputs(
        user_id=105,
        calculation_date="2026-06-05",
        body_weight_lb=None,
        height_in=70,
        age_years=39,
        sex="male",
        activity_level="moderate",
        primary_goal="strength_and_recomposition",
        nutrition_logging_quality="complete_enough_for_guidance",
    )

    result = calculate_nutrition_target_formula(inputs)

    assert result.protein_target is not None
    assert result.protein_target.display_allowed is False
    assert result.display_flags["allow_protein_targets"] is False
    assert "missing_body_weight" in result.protein_target.reason_codes


def test_body_weight_allows_protein_even_when_calories_are_blocked():
    result = calculate_nutrition_target_formula(_limited_inputs())

    assert result.protein_target is not None
    assert result.protein_target.display_allowed is True
    assert result.display_flags["allow_protein_targets"] is True
    assert result.calorie_target is not None
    assert result.calorie_target.display_allowed is False
    assert result.display_flags["allow_calorie_targets"] is False
    assert result.confidence == "Low"


def test_missing_profile_activity_or_goal_context_blocks_calorie_target():
    result = calculate_nutrition_target_formula(_limited_inputs())

    assert result.calorie_target is not None
    assert result.calorie_target.display_allowed is False
    assert result.display_flags["allow_calorie_targets"] is False
    assert "missing_height" in result.calorie_target.reason_codes
    assert "missing_age" in result.calorie_target.reason_codes
    assert "missing_sex" in result.calorie_target.reason_codes
    assert "missing_activity_level" in result.calorie_target.reason_codes
    assert "missing_primary_goal" in result.calorie_target.reason_codes


def test_carbohydrate_target_is_blocked_when_calorie_target_is_unavailable():
    result = calculate_nutrition_target_formula(_limited_inputs())

    assert result.carbohydrate_target is not None
    assert result.carbohydrate_target.display_allowed is False
    assert result.display_flags["allow_carbohydrate_targets"] is False
    assert "carbohydrate_depends_on_calorie_target" in (
        result.carbohydrate_target.reason_codes
    )


def test_fat_target_is_blocked_when_calorie_context_is_unavailable():
    result = calculate_nutrition_target_formula(_limited_inputs())

    assert result.fat_target is not None
    assert result.fat_target.display_allowed is False
    assert result.display_flags["allow_fat_targets"] is False
    assert "fat_display_blocked" in result.fat_target.reason_codes


def test_display_flags_align_with_target_availability():
    result = calculate_nutrition_target_formula(_complete_inputs())

    targets_by_flag = {
        "allow_calorie_targets": result.calorie_target,
        "allow_protein_targets": result.protein_target,
        "allow_carbohydrate_targets": result.carbohydrate_target,
        "allow_fat_targets": result.fat_target,
    }
    for flag_name, target in targets_by_flag.items():
        assert target is not None
        assert result.display_flags[flag_name] is target.display_allowed


def test_confidence_is_limited_when_required_inputs_are_missing():
    inputs = NutritionTargetFormulaInputs(
        user_id=105,
        calculation_date="2026-06-05",
        body_weight_lb=None,
        nutrition_logging_quality="limited",
    )

    result = calculate_nutrition_target_formula(inputs)

    assert result.confidence == "Limited"
    assert result.display_flags == {
        "allow_calorie_targets": False,
        "allow_protein_targets": False,
        "allow_carbohydrate_targets": False,
        "allow_fat_targets": False,
    }


def test_formula_metadata_includes_formula_name_and_version():
    result = calculate_nutrition_target_formula(_complete_inputs())

    assert result.formula_metadata.formula_name == "nutrition_target_formula_engine"
    assert result.formula_metadata.formula_version == "v1_service"
    assert "formula_version_recorded" in result.formula_metadata.reason_codes


def test_limitations_are_recorded_when_inputs_are_partial():
    result = calculate_nutrition_target_formula(_limited_inputs())

    assert result.limitations
    assert result.formula_metadata.limitations
    assert any("blocked" in limitation.lower() for limitation in result.limitations)


def test_targets_are_rounded_according_to_display_rules():
    result = calculate_nutrition_target_formula(_complete_inputs())

    assert result.calorie_target is not None
    assert result.protein_target is not None
    assert result.carbohydrate_target is not None
    assert result.fat_target is not None
    assert result.calorie_target.min_value % 50 == 0
    assert result.calorie_target.max_value % 50 == 0
    assert result.protein_target.min_value % 5 == 0
    assert result.carbohydrate_target.min_value % 5 == 0
    assert result.fat_target.min_value % 5 == 0


def test_target_values_and_ranges_are_non_negative():
    result = calculate_nutrition_target_formula(_complete_inputs())

    for target in [
        result.calorie_target,
        result.protein_target,
        result.carbohydrate_target,
        result.fat_target,
    ]:
        assert target is not None
        for value in [target.value, target.min_value, target.max_value]:
            if value is not None:
                assert value >= 0


def test_no_forbidden_language_is_required_or_produced():
    result = calculate_nutrition_target_formula(_complete_inputs())
    combined_text = " ".join(
        [
            *result.reason_codes,
            *result.limitations,
            *result.formula_metadata.reason_codes,
            *result.formula_metadata.limitations,
            result.formula_metadata.target_basis,
        ]
    ).lower()

    forbidden_terms = [
        "you need exactly",
        "must cut calories",
        "skip meals",
        "burn this off",
        "supplement",
        "stalled fat-loss",
        "medical requirement",
    ]
    for term in forbidden_terms:
        assert term not in combined_text


def test_build_inputs_from_user_health_state_uses_available_context_without_inference():
    inputs = build_nutrition_target_formula_inputs(
        _health_state(),
        calculation_date="2026-06-05",
        sex="male",
    )

    assert inputs.user_id == 7
    assert inputs.body_weight_lb == 190
    assert inputs.height_in == 70
    assert inputs.age_years == 39
    assert inputs.sex == "male"
    assert inputs.activity_level == "moderate"
    assert inputs.training_frequency_per_week == 4
    assert inputs.training_load == "Moderate"
    assert inputs.primary_goal == "strength_and_recomposition"
    assert inputs.nutrition_logging_quality == "complete_enough_for_guidance"
    assert inputs.input_source_metadata["source"] == "UserHealthState"


def test_build_inputs_does_not_infer_missing_sex_from_health_state():
    inputs = build_nutrition_target_formula_inputs(
        _health_state(),
        calculation_date="2026-06-05",
    )

    assert inputs.sex is None
    assert inputs.input_source_metadata["sex_source"] == "missing_from_health_state"
