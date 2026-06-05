from __future__ import annotations

import pytest

from models.nutrition_target_formula_models import (
    MacroTargetResult,
    NutritionTargetFormulaInputs,
)
from services.nutrition_target_formula_service import (
    approve_macro_targets,
    calculate_nutrition_target_formula,
)
from services.nutrition_target_formula_validation_service import (
    approve_validated_macro_targets,
    validate_approved_macro_targets,
    validate_nutrition_target_formula_result,
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
        input_source_metadata={"source": "validation_test"},
    )


def _protein_only_inputs() -> NutritionTargetFormulaInputs:
    return NutritionTargetFormulaInputs(
        user_id=105,
        calculation_date="2026-06-05",
        body_weight_lb=190,
        height_in=None,
        age_years=None,
        sex=None,
        activity_level=None,
        primary_goal=None,
        nutrition_logging_quality="limited",
        formula_version_requested="v1_service",
        input_source_metadata={"source": "validation_test_limited"},
    )


def _missing_body_weight_inputs() -> NutritionTargetFormulaInputs:
    return NutritionTargetFormulaInputs(
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


def _result_with_missing(**overrides) -> object:
    values = {
        "body_weight_lb": 190,
        "height_in": 70,
        "age_years": 39,
        "sex": "male",
        "activity_level": "moderate",
        "primary_goal": "strength_and_recomposition",
        "nutrition_logging_quality": "complete_enough_for_guidance",
    }
    values.update(overrides)
    inputs = NutritionTargetFormulaInputs(
        user_id=10,
        calculation_date="2026-06-05",
        formula_version_requested="v1_service",
        **values,
    )
    return calculate_nutrition_target_formula(inputs)


def test_complete_formula_result_validates_successfully():
    result = calculate_nutrition_target_formula(_complete_inputs())

    validated = validate_nutrition_target_formula_result(result)

    assert validated is result
    assert validated.display_flags == {
        "allow_calorie_targets": True,
        "allow_protein_targets": True,
        "allow_carbohydrate_targets": True,
        "allow_fat_targets": True,
    }


def test_complete_approved_macro_targets_validate_successfully():
    result = calculate_nutrition_target_formula(_complete_inputs())
    approved = approve_macro_targets(result)

    validated = validate_approved_macro_targets(approved)

    assert validated is approved
    assert validated.calorie_target is not None
    assert validated.protein_target_g is not None
    assert validated.carbohydrate_target_g is not None
    assert validated.fat_target_g is not None


def test_missing_body_weight_blocks_protein_display():
    result = calculate_nutrition_target_formula(_missing_body_weight_inputs())

    assert validate_nutrition_target_formula_result(result) is result
    assert result.display_flags["allow_protein_targets"] is False

    result.protein_target.display_allowed = True  # type: ignore[union-attr]
    result.display_flags["allow_protein_targets"] = True

    with pytest.raises(ValueError, match="Protein display must be blocked"):
        validate_nutrition_target_formula_result(result)


@pytest.mark.parametrize(
    ("missing_field", "match"),
    [
        ("height_in", "Calorie display must be blocked"),
        ("age_years", "Calorie display must be blocked"),
        ("sex", "Calorie display must be blocked"),
        ("activity_level", "Calorie display must be blocked"),
        ("primary_goal", "Calorie display must be blocked"),
    ],
)
def test_missing_required_calorie_inputs_block_calorie_display(missing_field, match):
    result = _result_with_missing(**{missing_field: None})

    assert validate_nutrition_target_formula_result(result) is result
    assert result.display_flags["allow_calorie_targets"] is False

    result.calorie_target.display_allowed = True  # type: ignore[union-attr]
    result.display_flags["allow_calorie_targets"] = True

    with pytest.raises(ValueError, match=match):
        validate_nutrition_target_formula_result(result)


def test_carbohydrate_display_is_blocked_when_calories_are_blocked():
    result = calculate_nutrition_target_formula(_protein_only_inputs())

    assert validate_nutrition_target_formula_result(result) is result
    assert result.display_flags["allow_calorie_targets"] is False
    assert result.display_flags["allow_carbohydrate_targets"] is False

    result.carbohydrate_target = MacroTargetResult(
        target_type="carbohydrate_g",
        value=200,
        min_value=175,
        max_value=225,
        display_value="175-225 g/day",
        unit="g/day",
        confidence="Low",
        display_allowed=True,
        method="unsafe_test_override",
        reason_codes=["carbohydrate_formula_available"],
    )
    result.display_flags["allow_carbohydrate_targets"] = True

    with pytest.raises(ValueError, match="Carbohydrate targets cannot display"):
        validate_nutrition_target_formula_result(result)


def test_fat_display_is_blocked_without_calorie_context():
    result = calculate_nutrition_target_formula(_protein_only_inputs())

    assert result.display_flags["allow_fat_targets"] is False

    result.fat_target = MacroTargetResult(
        target_type="fat_g",
        value=65,
        min_value=55,
        max_value=75,
        display_value="55-75 g/day",
        unit="g/day",
        confidence="Low",
        display_allowed=True,
        method="unsafe_test_override",
        reason_codes=["fat_formula_available"],
    )
    result.display_flags["allow_fat_targets"] = True

    with pytest.raises(ValueError, match="Fat targets cannot display"):
        validate_nutrition_target_formula_result(result)


def test_invalid_confidence_is_rejected():
    result = calculate_nutrition_target_formula(_complete_inputs())
    result.confidence = "Certain"

    with pytest.raises(ValueError, match="Invalid confidence"):
        validate_nutrition_target_formula_result(result)


def test_negative_target_value_is_rejected():
    result = calculate_nutrition_target_formula(_complete_inputs())
    result.protein_target.value = -5  # type: ignore[union-attr]

    with pytest.raises(ValueError, match="must be non-negative"):
        validate_nutrition_target_formula_result(result)


def test_extreme_calorie_restriction_is_rejected():
    result = calculate_nutrition_target_formula(_complete_inputs())
    result.calorie_target.min_value = 1000  # type: ignore[union-attr]

    with pytest.raises(ValueError, match="extreme restriction"):
        validate_nutrition_target_formula_result(result)


def test_inconsistent_display_flag_is_rejected():
    result = calculate_nutrition_target_formula(_complete_inputs())
    result.display_flags["allow_calorie_targets"] = False

    with pytest.raises(ValueError, match="does not match target display_allowed"):
        validate_nutrition_target_formula_result(result)


def test_missing_formula_metadata_is_rejected():
    result = calculate_nutrition_target_formula(_complete_inputs())
    result.formula_metadata = None  # type: ignore[assignment]

    with pytest.raises(ValueError, match="formula_metadata is required"):
        validate_nutrition_target_formula_result(result)


def test_missing_formula_version_is_rejected():
    result = calculate_nutrition_target_formula(_complete_inputs())
    result.formula_metadata.formula_version = ""

    with pytest.raises(ValueError, match="formula_metadata.formula_version"):
        validate_nutrition_target_formula_result(result)


def test_missing_inputs_used_metadata_is_rejected():
    result = calculate_nutrition_target_formula(_complete_inputs())
    result.formula_metadata.inputs_used = []

    with pytest.raises(ValueError, match="inputs_used"):
        validate_nutrition_target_formula_result(result)


def test_missing_rounding_rules_metadata_is_rejected():
    result = calculate_nutrition_target_formula(_complete_inputs())
    result.formula_metadata.rounding_rules = []

    with pytest.raises(ValueError, match="rounding_rules"):
        validate_nutrition_target_formula_result(result)


def test_missing_limitations_rejected_when_inputs_are_missing():
    result = calculate_nutrition_target_formula(_protein_only_inputs())
    result.limitations = []
    result.formula_metadata.limitations = []
    for target in [
        result.calorie_target,
        result.protein_target,
        result.carbohydrate_target,
        result.fat_target,
    ]:
        target.limitations = []  # type: ignore[union-attr]

    with pytest.raises(ValueError, match="Limitations are required"):
        validate_nutrition_target_formula_result(result)


def test_approved_macro_targets_can_represent_protein_only_approval():
    result = calculate_nutrition_target_formula(_protein_only_inputs())
    approved = approve_validated_macro_targets(result)

    assert approved.display_flags == {
        "allow_calorie_targets": False,
        "allow_protein_targets": True,
        "allow_carbohydrate_targets": False,
        "allow_fat_targets": False,
    }
    assert approved.calorie_target is not None
    assert approved.calorie_target.display_allowed is False
    assert approved.protein_target_g is not None
    assert approved.protein_target_g.display_allowed is True
    assert approved.carbohydrate_target_g is not None
    assert approved.carbohydrate_target_g.display_allowed is False
    assert approved.fat_target_g is not None
    assert approved.fat_target_g.display_allowed is False


def test_ai_generated_numeric_target_language_is_rejected():
    result = calculate_nutrition_target_formula(_complete_inputs())
    result.formula_metadata.limitations.append("CrewAI generated this macro target.")

    with pytest.raises(ValueError, match="Forbidden nutrition target language"):
        validate_nutrition_target_formula_result(result)


def test_forbidden_restriction_language_is_rejected():
    result = calculate_nutrition_target_formula(_complete_inputs())
    result.limitations.append("You must cut calories and skip meals to reach this.")

    with pytest.raises(ValueError, match="Forbidden nutrition target language"):
        validate_nutrition_target_formula_result(result)


def test_no_forbidden_language_is_required_or_produced():
    result = calculate_nutrition_target_formula(_complete_inputs())
    approved = approve_validated_macro_targets(result)
    combined_text = " ".join(
        [
            *approved.reason_codes,
            *approved.limitations,
            approved.formula_metadata.formula_name,
            approved.formula_metadata.formula_version,
            approved.formula_metadata.target_basis,
            *approved.formula_metadata.reason_codes,
            *approved.formula_metadata.limitations,
        ]
    ).lower()

    forbidden_terms = [
        "crewai",
        "ollama",
        "ai-generated",
        "skip meals",
        "starve",
        "eating disorder",
        "guaranteed fat loss",
        "supplement recommendation",
    ]
    for term in forbidden_terms:
        assert term not in combined_text
