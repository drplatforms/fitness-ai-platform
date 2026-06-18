from dataclasses import fields

import pytest

from models.nutrition_target_formula_models import (
    ApprovedMacroTargets,
    MacroTargetResult,
    NutritionTargetFormulaInputs,
    NutritionTargetFormulaMetadata,
    NutritionTargetFormulaResult,
)


def _display_flags(
    *, calories: bool = True, protein: bool = True, carbs: bool = True, fat: bool = True
) -> dict[str, bool]:
    return {
        "allow_calorie_targets": calories,
        "allow_protein_targets": protein,
        "allow_carbohydrate_targets": carbs,
        "allow_fat_targets": fat,
    }


def _metadata() -> NutritionTargetFormulaMetadata:
    return NutritionTargetFormulaMetadata(
        formula_name="nutrition_target_formula_engine",
        formula_version="v1_contract",
        calculation_date="2026-06-05",
        inputs_used=["body_weight_lb", "height_in", "age_years"],
        rounding_rules=["round_calories_to_nearest_50"],
        target_basis="contract_only",
        reason_codes=["formula_version_recorded", "not_medical_nutrition_advice"],
    )


def _calorie_target() -> MacroTargetResult:
    return MacroTargetResult(
        target_type="calories",
        value=2400,
        min_value=2200,
        max_value=2600,
        display_value="2,200-2,600 kcal/day",
        unit="kcal/day",
        confidence="Moderate",
        display_allowed=True,
        method="contract_placeholder",
        reason_codes=["calorie_formula_available", "calorie_display_allowed"],
    )


def _protein_target() -> MacroTargetResult:
    return MacroTargetResult(
        target_type="protein_g",
        value=165,
        min_value=145,
        max_value=185,
        display_value="145-185 g/day",
        unit="g/day",
        confidence="High",
        display_allowed=True,
        method="contract_placeholder",
        reason_codes=["protein_formula_available", "protein_display_allowed"],
    )


def _carbohydrate_target() -> MacroTargetResult:
    return MacroTargetResult(
        target_type="carbohydrate_g",
        value=250,
        min_value=200,
        max_value=300,
        display_value="200-300 g/day",
        unit="g/day",
        confidence="Moderate",
        display_allowed=True,
        method="contract_placeholder",
        reason_codes=["carbohydrate_formula_available"],
    )


def _fat_target() -> MacroTargetResult:
    return MacroTargetResult(
        target_type="fat_g",
        value=75,
        min_value=60,
        max_value=90,
        display_value="60-90 g/day",
        unit="g/day",
        confidence="Moderate",
        display_allowed=True,
        method="contract_placeholder",
        reason_codes=["fat_formula_available"],
    )


def test_model_construction_with_complete_inputs():
    inputs = NutritionTargetFormulaInputs(
        user_id=1,
        calculation_date="2026-06-05",
        body_weight_lb=190,
        height_in=70,
        age_years=39,
        sex="male",
        activity_level="moderate",
        training_frequency_per_week=4,
        training_load="moderate",
        primary_goal="strength_and_recomposition",
        goal_weight_lb=180,
        recovery_status="managed",
        nutrition_logging_quality="complete_enough_for_guidance",
        recent_weight_trend="stable",
        formula_version_requested="v1",
        input_source_metadata={"profile": "seeded_test_profile"},
    )

    assert inputs.user_id == 1
    assert inputs.body_weight_lb == 190
    assert inputs.input_source_metadata["profile"] == "seeded_test_profile"


def test_model_construction_with_limited_missing_inputs():
    inputs = NutritionTargetFormulaInputs(
        user_id=105,
        calculation_date="2026-06-05",
        body_weight_lb=None,
        height_in=None,
        age_years=None,
        activity_level=None,
        primary_goal=None,
        nutrition_logging_quality="limited",
        input_source_metadata={"profile": "missing"},
    )

    assert inputs.body_weight_lb is None
    assert inputs.height_in is None
    assert inputs.primary_goal is None
    assert inputs.nutrition_logging_quality == "limited"


def test_valid_confidence_values_are_accepted():
    for confidence in ["Limited", "Low", "Moderate", "High"]:
        target = MacroTargetResult(
            target_type="protein_g",
            value=160,
            unit="g/day",
            confidence=confidence,
            display_allowed=True,
            reason_codes=["protein_formula_available"],
        )
        assert target.confidence == confidence


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValueError, match="Invalid confidence"):
        MacroTargetResult(
            target_type="protein_g",
            value=160,
            confidence="Certain",
            display_allowed=True,
        )


def test_display_flags_are_preserved_in_formula_result():
    result = NutritionTargetFormulaResult(
        user_id=1,
        calculation_date="2026-06-05",
        calorie_target=_calorie_target(),
        protein_target=_protein_target(),
        carbohydrate_target=_carbohydrate_target(),
        fat_target=_fat_target(),
        formula_metadata=_metadata(),
        confidence="Moderate",
        display_flags=_display_flags(),
        reason_codes=["formula_inputs_complete"],
    )

    assert result.display_flags["allow_calorie_targets"] is True
    assert result.display_flags["allow_protein_targets"] is True
    assert result.to_dict()["formula_metadata"]["formula_name"] == (
        "nutrition_target_formula_engine"
    )


def test_missing_display_flag_is_rejected():
    flags = _display_flags()
    flags.pop("allow_fat_targets")

    with pytest.raises(ValueError, match="Missing display flags"):
        NutritionTargetFormulaResult(
            user_id=1,
            calculation_date="2026-06-05",
            calorie_target=_calorie_target(),
            protein_target=_protein_target(),
            carbohydrate_target=_carbohydrate_target(),
            fat_target=_fat_target(),
            formula_metadata=_metadata(),
            confidence="Moderate",
            display_flags=flags,
        )


def test_target_ranges_must_be_non_negative():
    with pytest.raises(ValueError, match="min_value must be non-negative"):
        MacroTargetResult(
            target_type="fat_g",
            min_value=-10,
            max_value=90,
            confidence="Moderate",
            display_allowed=True,
        )


def test_target_range_min_must_not_exceed_max():
    with pytest.raises(ValueError, match="min_value must be <= max_value"):
        MacroTargetResult(
            target_type="protein_g",
            min_value=200,
            max_value=150,
            confidence="Moderate",
            display_allowed=True,
        )


def test_calorie_target_must_not_imply_extreme_restriction():
    with pytest.raises(ValueError, match="extreme restriction"):
        MacroTargetResult(
            target_type="calories",
            min_value=700,
            max_value=900,
            unit="kcal/day",
            confidence="Low",
            display_allowed=True,
        )


def test_blocked_calorie_target_can_carry_reason_codes_and_limitations():
    blocked = MacroTargetResult(
        target_type="calories",
        value=None,
        min_value=None,
        max_value=None,
        display_value=None,
        unit="kcal/day",
        confidence="Limited",
        display_allowed=False,
        method="blocked_until_inputs_complete",
        reason_codes=["calorie_display_blocked", "missing_activity_level"],
        limitations=["Calorie targets are blocked until formula inputs improve."],
    )

    assert blocked.display_allowed is False
    assert "calorie_display_blocked" in blocked.reason_codes
    assert blocked.limitations


def test_blocked_target_requires_reason_codes_or_limitations():
    with pytest.raises(ValueError, match="Blocked macro targets"):
        MacroTargetResult(
            target_type="carbohydrate_g",
            confidence="Limited",
            display_allowed=False,
        )


def test_carbohydrate_target_can_be_blocked_when_calorie_target_unavailable():
    blocked_carbs = MacroTargetResult(
        target_type="carbohydrate_g",
        confidence="Limited",
        display_allowed=False,
        method="depends_on_calorie_target",
        reason_codes=[
            "carbohydrate_depends_on_calorie_target",
            "carbohydrate_formula_limited",
        ],
        limitations=[
            "Carbohydrate target is blocked until calorie target is available."
        ],
    )

    assert blocked_carbs.display_allowed is False
    assert "carbohydrate_depends_on_calorie_target" in blocked_carbs.reason_codes


def test_formula_metadata_includes_formula_name_and_version():
    metadata = _metadata()

    assert metadata.formula_name == "nutrition_target_formula_engine"
    assert metadata.formula_version == "v1_contract"
    assert "formula_version_recorded" in metadata.reason_codes


def test_metadata_requires_limitations_when_assumptions_are_used():
    with pytest.raises(ValueError, match="limitations are required"):
        NutritionTargetFormulaMetadata(
            formula_name="nutrition_target_formula_engine",
            formula_version="v1_contract",
            calculation_date="2026-06-05",
            assumptions=["used_default_activity_level"],
        )


def test_approved_macro_targets_can_represent_only_protein_allowed():
    blocked_calories = MacroTargetResult(
        target_type="calories",
        confidence="Limited",
        display_allowed=False,
        unit="kcal/day",
        method="blocked_until_inputs_complete",
        reason_codes=["calorie_display_blocked", "calorie_formula_limited"],
        limitations=["Calories are blocked until formula inputs are complete."],
    )
    blocked_carbs = MacroTargetResult(
        target_type="carbohydrate_g",
        confidence="Limited",
        display_allowed=False,
        unit="g/day",
        method="depends_on_calorie_target",
        reason_codes=[
            "carbohydrate_display_blocked",
            "carbohydrate_depends_on_calorie_target",
        ],
        limitations=["Carbohydrates depend on approved calorie target availability."],
    )
    blocked_fat = MacroTargetResult(
        target_type="fat_g",
        confidence="Limited",
        display_allowed=False,
        unit="g/day",
        method="blocked_until_inputs_complete",
        reason_codes=["fat_display_blocked", "fat_formula_limited"],
        limitations=["Fat target is blocked until formula inputs are complete."],
    )

    approved = ApprovedMacroTargets(
        user_id=105,
        calculation_date="2026-06-05",
        calorie_target=blocked_calories,
        protein_target_g=_protein_target(),
        carbohydrate_target_g=blocked_carbs,
        fat_target_g=blocked_fat,
        confidence="Limited",
        display_flags=_display_flags(
            calories=False, protein=True, carbs=False, fat=False
        ),
        formula_metadata=_metadata(),
        reason_codes=["protein_display_allowed", "macro_display_limited_by_confidence"],
        limitations=["Only protein is approved for display in this limited context."],
    )

    assert approved.display_flags == {
        "allow_calorie_targets": False,
        "allow_protein_targets": True,
        "allow_carbohydrate_targets": False,
        "allow_fat_targets": False,
    }
    assert approved.protein_target_g is not None
    assert approved.protein_target_g.display_allowed is True
    assert approved.calorie_target is not None
    assert approved.calorie_target.display_allowed is False


def test_approved_macro_targets_reject_enabled_flag_for_blocked_target():
    blocked_calories = MacroTargetResult(
        target_type="calories",
        confidence="Limited",
        display_allowed=False,
        reason_codes=["calorie_display_blocked"],
    )

    with pytest.raises(ValueError, match="target display is blocked"):
        ApprovedMacroTargets(
            user_id=1,
            calculation_date="2026-06-05",
            calorie_target=blocked_calories,
            protein_target_g=_protein_target(),
            carbohydrate_target_g=_carbohydrate_target(),
            fat_target_g=_fat_target(),
            confidence="Limited",
            display_flags=_display_flags(calories=True),
            formula_metadata=_metadata(),
        )


def test_no_forbidden_language_fields_are_required_in_model_outputs():
    model_field_names = {
        field.name
        for model in [
            NutritionTargetFormulaInputs,
            MacroTargetResult,
            NutritionTargetFormulaMetadata,
            NutritionTargetFormulaResult,
            ApprovedMacroTargets,
        ]
        for field in fields(model)
    }

    assert "medical_nutrition_advice" not in model_field_names
    assert "supplement_recommendations" not in model_field_names
    assert "ai_explanation" not in model_field_names
