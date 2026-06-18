import pytest

from models.nutrition_food_suggestion_models import (
    ApprovedFoodSuggestion,
    ApprovedNutritionFoodSuggestions,
    CanonicalFoodSuggestionCandidate,
    NutritionMacroGap,
)


def _protein_gap() -> NutritionMacroGap:
    return NutritionMacroGap(
        macro_name="protein_g",
        target_value=165,
        actual_value=110,
        gap_value=55,
        unit="g",
        target_status="below_target",
        display_allowed=True,
        confidence="Moderate",
        reason_codes=["protein_gap_available"],
    )


def _limited_calorie_gap() -> NutritionMacroGap:
    return NutritionMacroGap(
        macro_name="calories",
        target_value=None,
        actual_value=1800,
        gap_value=None,
        unit="kcal",
        target_status="limited",
        display_allowed=False,
        confidence="Limited",
        reason_codes=["target_not_approved"],
        limitations=["Calorie suggestions are limited until targets are approved."],
    )


def _candidate() -> CanonicalFoodSuggestionCandidate:
    return CanonicalFoodSuggestionCandidate(
        canonical_food_id=1,
        display_name="Chicken Breast, Cooked, Skinless",
        food_type="cooked",
        serving_grams=150,
        calories=247.5,
        protein_g=46.5,
        carbohydrate_g=0,
        fat_g=5.4,
        macro_gap_addressed="protein_g",
        score=95,
        confidence="Moderate",
        reason_codes=[
            "canonical_food_catalog_available",
            "canonical_food_nutrients_available",
            "practical_serving_selected",
            "protein_suggestion_available",
        ],
    )


def _approved_suggestion() -> ApprovedFoodSuggestion:
    return ApprovedFoodSuggestion(
        canonical_food_id=1,
        display_name="Chicken Breast, Cooked, Skinless",
        suggested_grams=150,
        estimated_calories=247.5,
        estimated_protein_g=46.5,
        estimated_carbohydrate_g=0,
        estimated_fat_g=5.4,
        macro_gap_addressed="protein_g",
        suggestion_summary="150g chicken breast adds about 46g protein.",
        confidence="Moderate",
        reason_codes=["practical_serving_selected", "protein_suggestion_available"],
    )


def test_nutrition_macro_gap_can_represent_approved_protein_gap():
    gap = _protein_gap()

    assert gap.macro_name == "protein_g"
    assert gap.gap_value == 55
    assert gap.display_allowed is True
    assert gap.target_status == "below_target"


def test_nutrition_macro_gap_can_represent_unavailable_limited_macro_target():
    gap = _limited_calorie_gap()

    assert gap.display_allowed is False
    assert gap.target_status == "limited"
    assert gap.reason_codes == ["target_not_approved"]
    assert gap.limitations


def test_limited_macro_gap_requires_reason_codes_or_limitations():
    with pytest.raises(ValueError, match="require reason_codes or limitations"):
        NutritionMacroGap(
            macro_name="calories",
            target_value=None,
            actual_value=None,
            gap_value=None,
            unit="kcal",
            target_status="limited",
            display_allowed=False,
            confidence="Limited",
        )


def test_canonical_food_suggestion_candidate_requires_canonical_food_id():
    with pytest.raises(ValueError, match="canonical_food_id must be positive"):
        CanonicalFoodSuggestionCandidate(
            canonical_food_id=0,
            display_name="Chicken Breast, Cooked, Skinless",
            food_type="cooked",
            serving_grams=150,
            calories=247.5,
            protein_g=46.5,
            carbohydrate_g=0,
            fat_g=5.4,
            macro_gap_addressed="protein_g",
            score=95,
            confidence="Moderate",
        )


def test_candidate_serving_grams_must_be_positive():
    with pytest.raises(ValueError, match="serving_grams must be positive"):
        CanonicalFoodSuggestionCandidate(
            canonical_food_id=1,
            display_name="Chicken Breast, Cooked, Skinless",
            food_type="cooked",
            serving_grams=0,
            calories=247.5,
            protein_g=46.5,
            carbohydrate_g=0,
            fat_g=5.4,
            macro_gap_addressed="protein_g",
            score=95,
            confidence="Moderate",
        )


def test_candidate_nutrient_estimates_must_be_non_negative():
    with pytest.raises(ValueError, match="protein_g must be non-negative"):
        CanonicalFoodSuggestionCandidate(
            canonical_food_id=1,
            display_name="Chicken Breast, Cooked, Skinless",
            food_type="cooked",
            serving_grams=150,
            calories=247.5,
            protein_g=-1,
            carbohydrate_g=0,
            fat_g=5.4,
            macro_gap_addressed="protein_g",
            score=95,
            confidence="Moderate",
        )


def test_candidate_can_represent_incomplete_nutrients_with_limitation():
    candidate = CanonicalFoodSuggestionCandidate(
        canonical_food_id=2,
        display_name="Greek Yogurt, Plain Nonfat",
        food_type="generic",
        serving_grams=170,
        calories=100,
        protein_g=17,
        carbohydrate_g=6,
        fat_g=None,
        macro_gap_addressed="protein_g",
        score=80,
        confidence="Low",
        limitations=["Fat estimate is unavailable for this canonical food."],
    )

    assert candidate.fat_g is None
    assert candidate.limitations


def test_approved_food_suggestion_can_represent_practical_serving_and_macros():
    suggestion = _approved_suggestion()

    assert suggestion.canonical_food_id == 1
    assert suggestion.suggested_grams == 150
    assert suggestion.estimated_protein_g == 46.5
    assert suggestion.macro_gap_addressed == "protein_g"


def test_approved_food_suggestion_rejects_negative_estimated_macros():
    with pytest.raises(ValueError, match="estimated_fat_g must be non-negative"):
        ApprovedFoodSuggestion(
            canonical_food_id=1,
            display_name="Chicken Breast, Cooked, Skinless",
            suggested_grams=150,
            estimated_calories=247.5,
            estimated_protein_g=46.5,
            estimated_carbohydrate_g=0,
            estimated_fat_g=-1,
            macro_gap_addressed="protein_g",
            suggestion_summary="150g chicken breast adds protein.",
            confidence="Moderate",
        )


def test_approved_nutrition_food_suggestions_can_represent_no_suggestions_with_limitations():
    approved = ApprovedNutritionFoodSuggestions(
        user_id=105,
        suggestion_date="2026-06-06",
        primary_gap=None,
        macro_gaps=[_limited_calorie_gap()],
        suggestions=[],
        confidence="Limited",
        reason_codes=["no_suitable_canonical_food_found"],
        limitations=["No approved macro gaps are available for food suggestions."],
    )

    assert approved.suggestions == []
    assert approved.confidence == "Limited"


def test_approved_nutrition_food_suggestions_can_represent_multiple_suggestions():
    suggestions = ApprovedNutritionFoodSuggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        primary_gap="protein_g",
        macro_gaps=[_protein_gap()],
        suggestions=[
            _approved_suggestion(),
            ApprovedFoodSuggestion(
                canonical_food_id=2,
                display_name="Greek Yogurt, Plain Nonfat",
                suggested_grams=200,
                estimated_calories=118,
                estimated_protein_g=20,
                estimated_carbohydrate_g=7,
                estimated_fat_g=0.8,
                macro_gap_addressed="protein_g",
                suggestion_summary="200g Greek yogurt is a smaller protein option.",
                confidence="Moderate",
                reason_codes=["practical_serving_selected"],
            ),
        ],
        confidence="Moderate",
        reason_codes=["protein_gap_available"],
    )

    assert len(suggestions.suggestions) == 2
    assert suggestions.primary_gap == "protein_g"
    assert suggestions.to_dict()["suggestions"][0]["canonical_food_id"] == 1


def test_blocked_targets_do_not_generate_food_suggestions():
    with pytest.raises(
        ValueError, match="Blocked targets cannot generate food suggestions"
    ):
        ApprovedNutritionFoodSuggestions(
            user_id=1,
            suggestion_date="2026-06-06",
            primary_gap="calories",
            macro_gaps=[_limited_calorie_gap()],
            suggestions=[
                ApprovedFoodSuggestion(
                    canonical_food_id=10,
                    display_name="White Rice, Cooked",
                    suggested_grams=150,
                    estimated_calories=195,
                    estimated_protein_g=4,
                    estimated_carbohydrate_g=43,
                    estimated_fat_g=0.4,
                    macro_gap_addressed="calories",
                    suggestion_summary="150g cooked rice adds calories and carbohydrates.",
                    confidence="Low",
                )
            ],
            confidence="Low",
        )


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValueError, match="Invalid confidence"):
        CanonicalFoodSuggestionCandidate(
            canonical_food_id=1,
            display_name="Chicken Breast, Cooked, Skinless",
            food_type="cooked",
            serving_grams=150,
            calories=247.5,
            protein_g=46.5,
            carbohydrate_g=0,
            fat_g=5.4,
            macro_gap_addressed="protein_g",
            score=95,
            confidence="Certain",
        )


def test_forbidden_language_is_not_allowed_but_not_required():
    suggestion = _approved_suggestion()
    assert "must" not in suggestion.suggestion_summary.lower()

    with pytest.raises(ValueError, match="Forbidden nutrition suggestion language"):
        ApprovedFoodSuggestion(
            canonical_food_id=1,
            display_name="Chicken Breast, Cooked, Skinless",
            suggested_grams=150,
            estimated_calories=247.5,
            estimated_protein_g=46.5,
            estimated_carbohydrate_g=0,
            estimated_fat_g=5.4,
            macro_gap_addressed="protein_g",
            suggestion_summary="You must eat this to compensate tomorrow.",
            confidence="Moderate",
        )
