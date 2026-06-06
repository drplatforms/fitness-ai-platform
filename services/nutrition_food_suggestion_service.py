from __future__ import annotations

from datetime import date
from typing import Any

from database import get_connection
from models.nutrition_food_suggestion_models import (
    ApprovedFoodSuggestion,
    ApprovedNutritionFoodSuggestions,
    CanonicalFoodSuggestionCandidate,
    NutritionMacroGap,
)
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    TARGET_STATUS_ABOVE,
    TARGET_STATUS_BELOW,
    TARGET_STATUS_NEAR,
    NutritionTargetComparison,
    TargetVsActualNutritionSummary,
)
from services.food_normalization_service import ensure_starter_canonical_foods_seeded
from services.nutrition_target_vs_actual_service import (
    build_target_vs_actual_nutrition_summary,
)

_CONFIDENCE_RANK = {"Limited": 0, "Low": 1, "Moderate": 2, "High": 3}

_COMPARISON_TO_MACRO = {
    "calories": "calories",
    "protein": "protein_g",
    "carbs": "carbohydrate_g",
    "fat": "fat_g",
}

_MACRO_UNITS = {
    "calories": "kcal",
    "protein_g": "g",
    "carbohydrate_g": "g",
    "fat_g": "g",
}

_NUTRIENT_NAME_TO_FIELD = {
    "calorie": "calories",
    "calories": "calories",
    "energy": "calories",
    "protein": "protein_g",
    "carbohydrate": "carbohydrate_g",
    "carbohydrates": "carbohydrate_g",
    "carbs": "carbohydrate_g",
    "total carbohydrate": "carbohydrate_g",
    "fat": "fat_g",
    "total fat": "fat_g",
}

_PROTEIN_SUGGESTION_NAMES = {
    "Chicken Breast, Cooked, Skinless": (100, 200, 1),
    "Greek Yogurt, Plain Nonfat": (150, 250, 2),
    "Tuna, Canned in Water": (85, 150, 3),
    "Egg Whites": (100, 250, 4),
    "Cottage Cheese, Low Fat": (100, 250, 5),
    "Whey Protein Powder, Generic": (25, 35, 6),
    "Turkey Breast, Cooked": (100, 200, 7),
    "Shrimp, Cooked": (100, 200, 8),
    "Cod, Cooked": (100, 220, 9),
    "Pork Tenderloin, Cooked": (100, 200, 10),
}

_CARBOHYDRATE_SUGGESTION_NAMES = {
    "White Rice, Cooked": (100, 250, 1),
    "Jasmine Rice, Cooked": (100, 250, 2),
    "Basmati Rice, Cooked": (100, 250, 3),
    "Brown Rice, Cooked": (100, 250, 4),
    "Potato, Baked": (100, 300, 5),
    "Sweet Potato, Baked": (100, 300, 6),
    "Pasta, Cooked": (100, 250, 7),
    "Whole Wheat Pasta, Cooked": (100, 250, 8),
    "Banana": (100, 200, 9),
    "Oats, Dry": (30, 80, 10),
    "Black Beans, Cooked": (100, 250, 11),
    "Pinto Beans, Cooked": (100, 250, 12),
    "Lentils, Cooked": (100, 250, 13),
    "Flour Tortilla": (40, 100, 14),
    "Whole Wheat Bread": (35, 100, 15),
    "Bagel, Plain": (70, 120, 16),
    "Apple": (100, 200, 17),
}

_CALORIE_SUPPORT_SUGGESTION_NAMES = {
    "Greek Yogurt, Plain Nonfat": (150, 250, 1),
    "Cottage Cheese, Low Fat": (100, 250, 2),
    "Oats, Dry": (30, 80, 3),
    "White Rice, Cooked": (100, 250, 4),
    "Jasmine Rice, Cooked": (100, 250, 5),
    "Brown Rice, Cooked": (100, 250, 6),
    "Potato, Baked": (100, 300, 7),
    "Sweet Potato, Baked": (100, 300, 8),
    "Pasta, Cooked": (100, 250, 9),
    "Black Beans, Cooked": (100, 250, 10),
    "Pinto Beans, Cooked": (100, 250, 11),
    "Lentils, Cooked": (100, 250, 12),
    "Banana": (100, 200, 13),
    "Apple": (100, 200, 14),
    "Peanut Butter": (16, 32, 15),
    "Almonds": (15, 30, 16),
    "Walnuts": (15, 30, 17),
    "Cashews": (15, 30, 18),
    "Avocado": (50, 100, 19),
    "Whole Wheat Bread": (35, 100, 20),
    "Bagel, Plain": (70, 120, 21),
    "Flour Tortilla": (40, 100, 22),
}

_FAT_SUPPORT_SUGGESTION_NAMES = {
    "Olive Oil": (5, 15, 1),
    "Avocado Oil": (5, 15, 2),
    "Peanut Butter": (16, 32, 3),
    "Almond Butter": (16, 32, 4),
    "Almonds": (15, 30, 5),
    "Walnuts": (15, 30, 6),
    "Cashews": (15, 30, 7),
    "Avocado": (50, 100, 8),
    "Cheddar Cheese": (15, 40, 9),
    "Mozzarella Cheese": (15, 40, 10),
    "Whole Egg": (50, 100, 11),
    "Butter": (5, 15, 12),
}

_MACRO_PRIORITY = {
    "protein_g": 0,
    "carbohydrate_g": 1,
    "calories": 2,
    "fat_g": 3,
}

_FORBIDDEN_SUGGESTION_TERMS = {
    "you must eat",
    "you failed",
    "burn this off",
    "skip meals",
    "compensate tomorrow",
    "medical",
    "disease",
    "fat-loss guarantee",
    "fat loss guarantee",
    "guaranteed fat loss",
    "exact physiological certainty",
}

_SAFE_DEFAULT_LIMITATION = "Food suggestions are limited to approved canonical foods with usable nutrient data."
_UNSUPPORTED_SUGGESTION_GAP_REASON_CODES: dict[str, str] = {}
_UNSUPPORTED_SUGGESTION_GAP_LABELS: dict[str, str] = {}


def _today_iso() -> str:
    return date.today().isoformat()


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _round1(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 1)


def _round_to_nearest_5(value: float) -> float:
    return float(max(5, round(value / 5.0) * 5))


def _rank_min(*confidences: str) -> str:
    valid = [confidence for confidence in confidences if confidence in _CONFIDENCE_RANK]
    if not valid:
        return "Limited"
    return min(valid, key=lambda confidence: _CONFIDENCE_RANK[confidence])


def _text_contains_forbidden_language(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _FORBIDDEN_SUGGESTION_TERMS)


def _is_logging_incomplete(summary: TargetVsActualNutritionSummary) -> bool:
    return summary.logging_completeness in {
        LOGGING_COMPLETENESS_NO_LOGS,
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
        LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    }


def _gap_status_for_unavailable_comparison(
    comparison: NutritionTargetComparison,
) -> str:
    text = " ".join([*comparison.reason_codes, *comparison.limitations]).lower()
    if "limited" in text or "incomplete" in text or "partial" in text:
        return "limited"
    return "unavailable"


def _gap_from_comparison(
    comparison: NutritionTargetComparison,
    macro_name: str,
) -> NutritionMacroGap:
    if not comparison.comparison_available:
        status = _gap_status_for_unavailable_comparison(comparison)
        reason_codes = list(comparison.reason_codes)
        limitations = list(comparison.limitations)
        if not reason_codes and not limitations:
            reason_codes = ["target_not_approved"]
        return NutritionMacroGap(
            macro_name=macro_name,
            target_value=_round1(comparison.target_min),
            actual_value=_round1(comparison.actual),
            gap_value=None,
            unit=_MACRO_UNITS[macro_name],
            target_status=status,
            display_allowed=False,
            confidence=comparison.confidence,
            reason_codes=_unique(reason_codes),
            limitations=_unique(limitations),
        )

    target_value = comparison.target_min
    actual_value = comparison.actual
    gap_value = None
    if (
        comparison.target_status == TARGET_STATUS_BELOW
        and target_value is not None
        and actual_value is not None
    ):
        gap_value = max(float(target_value) - float(actual_value), 0.0)

    reason_codes = list(comparison.reason_codes)
    if macro_name == "protein_g" and comparison.target_status == TARGET_STATUS_BELOW:
        reason_codes.append("protein_gap_available")
    elif macro_name == "calories" and comparison.target_status == TARGET_STATUS_BELOW:
        reason_codes.append("calorie_gap_available")
    elif (
        macro_name == "carbohydrate_g"
        and comparison.target_status == TARGET_STATUS_BELOW
    ):
        reason_codes.append("carbohydrate_gap_available")
    elif macro_name == "fat_g" and comparison.target_status == TARGET_STATUS_BELOW:
        reason_codes.append("fat_gap_available")
    elif comparison.target_status in {TARGET_STATUS_NEAR, TARGET_STATUS_ABOVE}:
        reason_codes.append("no_macro_gap_detected")

    return NutritionMacroGap(
        macro_name=macro_name,
        target_value=_round1(target_value),
        actual_value=_round1(actual_value),
        gap_value=_round1(gap_value),
        unit=_MACRO_UNITS[macro_name],
        target_status=comparison.target_status,
        display_allowed=True,
        confidence=comparison.confidence,
        reason_codes=_unique(reason_codes),
        limitations=list(comparison.limitations),
    )


def build_nutrition_macro_gaps(
    target_vs_actual_summary: TargetVsActualNutritionSummary,
) -> list[NutritionMacroGap]:
    """Build approved macro-gap model objects from target-vs-actual comparisons.

    This function only reads already-approved target-vs-actual output. It does not
    calculate targets, infer actuals, mutate logs, or use AI.
    """

    gaps: list[NutritionMacroGap] = []
    for comparison_name, macro_name in _COMPARISON_TO_MACRO.items():
        comparison = target_vs_actual_summary.comparisons.get(comparison_name)
        if comparison is None:
            gaps.append(
                NutritionMacroGap(
                    macro_name=macro_name,
                    target_value=None,
                    actual_value=None,
                    gap_value=None,
                    unit=_MACRO_UNITS[macro_name],
                    target_status="unavailable",
                    display_allowed=False,
                    confidence="Limited",
                    reason_codes=["target_not_approved"],
                    limitations=[
                        f"{comparison_name.title()} comparison is unavailable."
                    ],
                )
            )
            continue
        gaps.append(_gap_from_comparison(comparison, macro_name))
    return gaps


def _macro_gap_by_name(
    macro_gaps: list[NutritionMacroGap], macro_name: str
) -> NutritionMacroGap | None:
    for gap in macro_gaps:
        if gap.macro_name == macro_name:
            return gap
    return None


def _normalized_nutrient_key(nutrient_name: str) -> str | None:
    normalized = " ".join(nutrient_name.strip().lower().replace("_", " ").split())
    return _NUTRIENT_NAME_TO_FIELD.get(normalized)


def _canonical_food_rows() -> list[dict[str, Any]]:
    ensure_starter_canonical_foods_seeded()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            canonical_foods.id AS canonical_food_id,
            canonical_foods.display_name,
            canonical_foods.food_type,
            canonical_foods.search_priority,
            canonical_food_nutrients.nutrient_name,
            canonical_food_nutrients.amount_per_100g
        FROM canonical_foods
        LEFT JOIN canonical_food_nutrients
            ON canonical_food_nutrients.canonical_food_id = canonical_foods.id
        WHERE canonical_foods.active = 1
        ORDER BY canonical_foods.search_priority, canonical_foods.display_name
        """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def _canonical_food_nutrient_maps() -> list[dict[str, Any]]:
    grouped: dict[int, dict[str, Any]] = {}
    for row in _canonical_food_rows():
        canonical_food_id = int(row["canonical_food_id"])
        food = grouped.setdefault(
            canonical_food_id,
            {
                "canonical_food_id": canonical_food_id,
                "display_name": row["display_name"],
                "food_type": row["food_type"],
                "search_priority": int(row["search_priority"] or 100),
                "nutrients": {},
            },
        )
        nutrient_name = row.get("nutrient_name")
        if nutrient_name is None:
            continue
        nutrient_key = _normalized_nutrient_key(str(nutrient_name))
        if nutrient_key is not None:
            food["nutrients"][nutrient_key] = float(row["amount_per_100g"])
    return list(grouped.values())


def _serving_bounds_for_food(
    display_name: str,
    macro_gap_addressed: str,
) -> tuple[float, float, int] | None:
    sources = {
        "protein_g": _PROTEIN_SUGGESTION_NAMES,
        "carbohydrate_g": _CARBOHYDRATE_SUGGESTION_NAMES,
        "calories": _CALORIE_SUPPORT_SUGGESTION_NAMES,
        "fat_g": _FAT_SUPPORT_SUGGESTION_NAMES,
    }
    source = sources.get(macro_gap_addressed, {})
    if display_name in source:
        min_grams, max_grams, preference_rank = source[display_name]
        return float(min_grams), float(max_grams), int(preference_rank)
    return None


def _serving_grams_for_gap(
    *,
    gap_value: float,
    nutrient_per_100g: float,
    min_grams: float,
    max_grams: float,
) -> tuple[float, bool]:
    if nutrient_per_100g <= 0:
        return min_grams, True
    desired_grams = gap_value * 100.0 / nutrient_per_100g
    bounded_grams = min(max(desired_grams, min_grams), max_grams)
    rounded_grams = _round_to_nearest_5(bounded_grams)
    bounded_again = min(max(rounded_grams, min_grams), max_grams)
    was_bounded = desired_grams < min_grams or desired_grams > max_grams
    return float(bounded_again), was_bounded


def _nutrient_at_serving(
    nutrients: dict[str, float], nutrient_key: str, serving_grams: float
) -> float | None:
    value = nutrients.get(nutrient_key)
    if value is None:
        return None
    return round(value * serving_grams / 100.0, 1)


def _protein_candidate_score(
    *,
    nutrients: dict[str, float],
    serving_grams: float,
    search_priority: int,
    preference_rank: int,
) -> float:
    protein = nutrients["protein_g"]
    calories = max(nutrients.get("calories", 0.0), 1.0)
    fat = nutrients.get("fat_g", 0.0)
    protein_density = protein / calories * 100.0
    serving_practicality = max(0.0, 100.0 - abs(serving_grams - 150.0) / 2.0)
    priority_bonus = max(0.0, 100.0 - float(search_priority)) / 10.0
    preference_bonus = max(0.0, 12.0 - float(preference_rank)) * 6.0
    fat_penalty = max(0.0, fat - 8.0) * 1.5
    score = (
        protein_density * 5.0
        + serving_practicality
        + priority_bonus
        + preference_bonus
        - fat_penalty
    )
    return round(max(score, 0.0), 2)


def _carbohydrate_candidate_score(
    *,
    nutrients: dict[str, float],
    serving_grams: float,
    search_priority: int,
    preference_rank: int,
    calorie_gap: float | None,
) -> float:
    carbohydrate = nutrients["carbohydrate_g"]
    calories = max(nutrients.get("calories", 0.0), 1.0)
    fat = nutrients.get("fat_g", 0.0)
    protein = nutrients.get("protein_g", 0.0)
    carbohydrate_density = carbohydrate / calories * 100.0
    serving_practicality = max(0.0, 100.0 - abs(serving_grams - 150.0) / 2.0)
    priority_bonus = max(0.0, 100.0 - float(search_priority)) / 10.0
    preference_bonus = max(0.0, 18.0 - float(preference_rank)) * 4.0
    fat_penalty = max(0.0, fat - 5.0) * 3.0
    protein_bonus = min(protein, 12.0) * 0.75
    calorie_penalty = 0.0
    serving_calories = nutrients.get("calories", 0.0) * serving_grams / 100.0
    if calorie_gap is not None and serving_calories > calorie_gap * 1.15:
        calorie_penalty = (serving_calories - calorie_gap) * 0.1
    score = (
        carbohydrate_density * 4.0
        + serving_practicality
        + priority_bonus
        + preference_bonus
        + protein_bonus
        - fat_penalty
        - calorie_penalty
    )
    return round(max(score, 0.0), 2)


def _calorie_support_candidate_score(
    *,
    nutrients: dict[str, float],
    serving_grams: float,
    search_priority: int,
    preference_rank: int,
    protein_above_target: bool,
    carbohydrate_above_target: bool,
    fat_above_target: bool,
) -> float:
    calories = nutrients["calories"]
    protein = nutrients.get("protein_g", 0.0)
    carbohydrate = nutrients.get("carbohydrate_g", 0.0)
    fat = nutrients.get("fat_g", 0.0)
    serving_practicality = max(0.0, 100.0 - abs(serving_grams - 150.0) / 2.0)
    priority_bonus = max(0.0, 100.0 - float(search_priority)) / 10.0
    preference_bonus = max(0.0, 24.0 - float(preference_rank)) * 3.5
    energy_support = min(calories, 500.0) / 6.0
    protein_bonus = min(protein, 20.0) * 0.6
    carbohydrate_bonus = min(carbohydrate, 35.0) * 0.35
    fat_bonus = min(fat, 15.0) * 0.25
    conflict_penalty = 0.0
    if protein_above_target:
        conflict_penalty += max(0.0, protein - 12.0) * 2.0
    if carbohydrate_above_target:
        conflict_penalty += max(0.0, carbohydrate - 20.0) * 2.5
    if fat_above_target:
        conflict_penalty += max(0.0, fat - 7.0) * 4.0
    score = (
        energy_support
        + serving_practicality
        + priority_bonus
        + preference_bonus
        + protein_bonus
        + carbohydrate_bonus
        + fat_bonus
        - conflict_penalty
    )
    return round(max(score, 0.0), 2)


def _fat_support_candidate_score(
    *,
    nutrients: dict[str, float],
    serving_grams: float,
    search_priority: int,
    preference_rank: int,
    protein_above_target: bool,
    carbohydrate_above_target: bool,
) -> float:
    calories = max(nutrients.get("calories", 0.0), 1.0)
    fat = nutrients["fat_g"]
    protein = nutrients.get("protein_g", 0.0)
    carbohydrate = nutrients.get("carbohydrate_g", 0.0)
    serving_practicality = max(0.0, 100.0 - abs(serving_grams - 25.0) * 2.0)
    priority_bonus = max(0.0, 100.0 - float(search_priority)) / 10.0
    preference_bonus = max(0.0, 14.0 - float(preference_rank)) * 4.0
    fat_density = fat / calories * 100.0
    calorie_penalty = max(0.0, calories - 220.0) * 0.18
    conflict_penalty = 0.0
    if protein_above_target:
        conflict_penalty += max(0.0, protein - 10.0) * 2.0
    if carbohydrate_above_target:
        conflict_penalty += max(0.0, carbohydrate - 12.0) * 2.5
    score = (
        fat_density * 5.0
        + serving_practicality
        + priority_bonus
        + preference_bonus
        - calorie_penalty
        - conflict_penalty
    )
    return round(max(score, 0.0), 2)


def _displayable_gap_status(
    macro_gaps: list[NutritionMacroGap], macro_name: str, status: str
) -> bool:
    gap = _macro_gap_by_name(macro_gaps, macro_name)
    return bool(gap and gap.display_allowed and gap.target_status == status)


def _calorie_support_conflicts_with_above_macros(
    *,
    macro_gaps: list[NutritionMacroGap],
    nutrients: dict[str, float],
    serving_grams: float,
) -> bool:
    serving_protein = _nutrient_at_serving(nutrients, "protein_g", serving_grams) or 0.0
    serving_carbohydrate = (
        _nutrient_at_serving(nutrients, "carbohydrate_g", serving_grams) or 0.0
    )
    serving_fat = _nutrient_at_serving(nutrients, "fat_g", serving_grams) or 0.0
    if _displayable_gap_status(macro_gaps, "protein_g", TARGET_STATUS_ABOVE):
        if serving_protein > 30.0:
            return True
    if _displayable_gap_status(macro_gaps, "carbohydrate_g", TARGET_STATUS_ABOVE):
        if serving_carbohydrate > 30.0:
            return True
    if _displayable_gap_status(macro_gaps, "fat_g", TARGET_STATUS_ABOVE):
        if serving_fat > 9.0:
            return True
    return False


def _fat_support_conflicts_with_above_macros(
    *,
    macro_gaps: list[NutritionMacroGap],
    nutrients: dict[str, float],
    serving_grams: float,
) -> bool:
    serving_calories = _nutrient_at_serving(nutrients, "calories", serving_grams) or 0.0
    serving_protein = _nutrient_at_serving(nutrients, "protein_g", serving_grams) or 0.0
    serving_carbohydrate = (
        _nutrient_at_serving(nutrients, "carbohydrate_g", serving_grams) or 0.0
    )
    if _displayable_gap_status(macro_gaps, "calories", TARGET_STATUS_ABOVE):
        return True
    if serving_calories > 260.0:
        return True
    if _displayable_gap_status(macro_gaps, "protein_g", TARGET_STATUS_ABOVE):
        if serving_protein > 18.0:
            return True
    if _displayable_gap_status(macro_gaps, "carbohydrate_g", TARGET_STATUS_ABOVE):
        if serving_carbohydrate > 18.0:
            return True
    return False


def _calorie_support_block_limitations(
    macro_gaps: list[NutritionMacroGap],
    *,
    logging_incomplete: bool,
) -> tuple[list[str], list[str]]:
    reason_codes: list[str] = ["calorie_support_suggestion_limited"]
    limitations: list[str] = []
    calorie_gap = _macro_gap_by_name(macro_gaps, "calories")

    if calorie_gap is None or not calorie_gap.display_allowed:
        reason_codes.append("target_not_approved")
        limitations.append(
            "Calorie-support food suggestions require an approved calorie target."
        )
    elif calorie_gap.target_status != TARGET_STATUS_BELOW:
        reason_codes.append("no_calorie_gap_available")
        limitations.append(
            "Calorie-support food suggestions are limited because calories are not below target."
        )
    if logging_incomplete:
        reason_codes.append("logging_incomplete_limits_suggestions")
        limitations.append(
            "Calorie-support suggestions are limited because logging appears incomplete."
        )
    if _displayable_gap_status(macro_gaps, "protein_g", TARGET_STATUS_ABOVE):
        reason_codes.append("protein_conflict_limits_calorie_suggestions")
    if _displayable_gap_status(macro_gaps, "carbohydrate_g", TARGET_STATUS_ABOVE):
        reason_codes.append("carbohydrate_conflict_limits_calorie_suggestions")
        limitations.append(
            "Calorie-support suggestions avoid high-carbohydrate options because carbohydrates are already above target."
        )
    if _displayable_gap_status(macro_gaps, "fat_g", TARGET_STATUS_ABOVE):
        reason_codes.append("fat_conflict_limits_calorie_suggestions")
        limitations.append(
            "Calorie-support suggestions avoid high-fat options because fat is already above target."
        )
    return _unique(reason_codes), _unique(limitations)


def _fat_support_block_limitations(
    macro_gaps: list[NutritionMacroGap],
    *,
    logging_incomplete: bool,
) -> tuple[list[str], list[str]]:
    reason_codes: list[str] = ["fat_support_suggestion_limited"]
    limitations: list[str] = []
    fat_gap = _macro_gap_by_name(macro_gaps, "fat_g")
    calorie_gap = _macro_gap_by_name(macro_gaps, "calories")

    if fat_gap is None or not fat_gap.display_allowed:
        reason_codes.append("target_not_approved")
        limitations.append(
            "Fat-support food suggestions require an approved fat target."
        )
    elif fat_gap.target_status != TARGET_STATUS_BELOW:
        reason_codes.append("no_fat_gap_available")
        limitations.append(
            "Fat-support food suggestions are limited because fat is not below target."
        )
    if calorie_gap is None or not calorie_gap.display_allowed:
        reason_codes.append("target_not_approved")
        limitations.append(
            "Fat-support food suggestions require an approved calorie target."
        )
    elif calorie_gap.target_status == TARGET_STATUS_ABOVE:
        reason_codes.append("calorie_conflict_limits_fat_suggestions")
        limitations.append(
            "Fat-support suggestions are limited because calories are already above target."
        )
    if logging_incomplete:
        reason_codes.append("logging_incomplete_limits_suggestions")
        limitations.append(
            "Fat-support suggestions are limited because logging appears incomplete."
        )
    if _displayable_gap_status(macro_gaps, "protein_g", TARGET_STATUS_ABOVE):
        reason_codes.append("protein_conflict_limits_fat_suggestions")
    if _displayable_gap_status(macro_gaps, "carbohydrate_g", TARGET_STATUS_ABOVE):
        reason_codes.append("carbohydrate_conflict_limits_fat_suggestions")
        limitations.append(
            "Fat-support suggestions avoid high-carbohydrate options because carbohydrates are already above target."
        )
    return _unique(reason_codes), _unique(limitations)


def _calorie_context_allows_carbohydrate_suggestions(
    macro_gaps: list[NutritionMacroGap],
) -> bool:
    calorie_gap = _macro_gap_by_name(macro_gaps, "calories")
    if calorie_gap is None or not calorie_gap.display_allowed:
        return False
    return calorie_gap.target_status in {TARGET_STATUS_BELOW, TARGET_STATUS_NEAR}


def _carbohydrate_block_limitations(
    macro_gaps: list[NutritionMacroGap],
    *,
    logging_incomplete: bool,
) -> tuple[list[str], list[str]]:
    reason_codes: list[str] = ["carb_suggestion_limited"]
    limitations: list[str] = []
    carbohydrate_gap = _macro_gap_by_name(macro_gaps, "carbohydrate_g")
    calorie_gap = _macro_gap_by_name(macro_gaps, "calories")

    if carbohydrate_gap is None or not carbohydrate_gap.display_allowed:
        reason_codes.append("target_not_approved")
        limitations.append(
            "Carbohydrate food suggestions require an approved carbohydrate target."
        )
    if calorie_gap is None or not calorie_gap.display_allowed:
        reason_codes.append("target_not_approved")
        limitations.append(
            "Carbohydrate food suggestions require an approved calorie target."
        )
    elif calorie_gap.target_status == TARGET_STATUS_ABOVE:
        reason_codes.append("calorie_conflict_limits_carb_suggestions")
        limitations.append(
            "Carbohydrate food suggestions are limited because calories are already above target."
        )
    if logging_incomplete:
        reason_codes.append("logging_incomplete_limits_suggestions")
        limitations.append(
            "Carbohydrate suggestions are limited because logging appears incomplete."
        )
    return _unique(reason_codes), _unique(limitations)


def _required_macro_nutrients_available(nutrients: dict[str, float]) -> bool:
    required_keys = {"calories", "protein_g", "carbohydrate_g", "fat_g"}
    return required_keys.issubset(nutrients)


def _protein_suggestion_candidates(
    macro_gaps: list[NutritionMacroGap],
    *,
    logging_incomplete: bool,
) -> list[CanonicalFoodSuggestionCandidate]:
    protein_gap = _macro_gap_by_name(macro_gaps, "protein_g")
    if protein_gap is None or not _is_displayable_macro_gap(protein_gap):
        return []

    candidates: list[CanonicalFoodSuggestionCandidate] = []
    for food in _canonical_food_nutrient_maps():
        bounds = _serving_bounds_for_food(food["display_name"], "protein_g")
        if bounds is None:
            continue
        nutrients = food["nutrients"]
        if not _required_macro_nutrients_available(nutrients):
            continue
        if nutrients["protein_g"] <= 0:
            continue

        min_grams, max_grams, preference_rank = bounds
        serving_grams, was_bounded = _serving_grams_for_gap(
            gap_value=float(protein_gap.gap_value),
            nutrient_per_100g=nutrients["protein_g"],
            min_grams=min_grams,
            max_grams=max_grams,
        )
        reason_codes = [
            "canonical_food_catalog_available",
            "canonical_food_nutrients_available",
            "practical_serving_selected",
            "protein_suggestion_available",
        ]
        limitations: list[str] = []
        if was_bounded:
            reason_codes.append("serving_limited_by_practical_bounds")
        if logging_incomplete:
            limitations.append(
                "Suggestions are limited because logging appears incomplete."
            )

        candidates.append(
            CanonicalFoodSuggestionCandidate(
                canonical_food_id=food["canonical_food_id"],
                display_name=food["display_name"],
                food_type=food["food_type"],
                serving_grams=serving_grams,
                calories=_nutrient_at_serving(nutrients, "calories", serving_grams),
                protein_g=_nutrient_at_serving(nutrients, "protein_g", serving_grams),
                carbohydrate_g=_nutrient_at_serving(
                    nutrients, "carbohydrate_g", serving_grams
                ),
                fat_g=_nutrient_at_serving(nutrients, "fat_g", serving_grams),
                macro_gap_addressed="protein_g",
                score=_protein_candidate_score(
                    nutrients=nutrients,
                    serving_grams=serving_grams,
                    search_priority=food["search_priority"],
                    preference_rank=preference_rank,
                ),
                confidence=protein_gap.confidence,
                reason_codes=_unique(reason_codes),
                limitations=limitations,
            )
        )
    return candidates


def _carbohydrate_suggestion_candidates(
    macro_gaps: list[NutritionMacroGap],
    *,
    logging_incomplete: bool,
) -> list[CanonicalFoodSuggestionCandidate]:
    carbohydrate_gap = _macro_gap_by_name(macro_gaps, "carbohydrate_g")
    calorie_gap = _macro_gap_by_name(macro_gaps, "calories")
    if carbohydrate_gap is None or not _is_displayable_macro_gap(carbohydrate_gap):
        return []
    if logging_incomplete:
        return []
    if not _calorie_context_allows_carbohydrate_suggestions(macro_gaps):
        return []

    calorie_room = (
        calorie_gap.gap_value if calorie_gap and calorie_gap.gap_value else None
    )
    candidates: list[CanonicalFoodSuggestionCandidate] = []
    for food in _canonical_food_nutrient_maps():
        bounds = _serving_bounds_for_food(food["display_name"], "carbohydrate_g")
        if bounds is None:
            continue
        nutrients = food["nutrients"]
        if not _required_macro_nutrients_available(nutrients):
            continue
        if nutrients["carbohydrate_g"] <= 0:
            continue
        if nutrients.get("fat_g", 0.0) > 18.0:
            continue

        min_grams, max_grams, preference_rank = bounds
        serving_grams, was_bounded = _serving_grams_for_gap(
            gap_value=float(carbohydrate_gap.gap_value),
            nutrient_per_100g=nutrients["carbohydrate_g"],
            min_grams=min_grams,
            max_grams=max_grams,
        )
        serving_calories = _nutrient_at_serving(nutrients, "calories", serving_grams)
        if calorie_room is not None and serving_calories is not None:
            if serving_calories > max(calorie_room * 1.25, calorie_room + 150.0):
                continue

        reason_codes = [
            "canonical_food_catalog_available",
            "canonical_food_nutrients_available",
            "practical_serving_selected",
            "carbohydrate_suggestion_available",
        ]
        limitations: list[str] = []
        if was_bounded:
            reason_codes.append("serving_limited_by_practical_bounds")

        candidates.append(
            CanonicalFoodSuggestionCandidate(
                canonical_food_id=food["canonical_food_id"],
                display_name=food["display_name"],
                food_type=food["food_type"],
                serving_grams=serving_grams,
                calories=serving_calories,
                protein_g=_nutrient_at_serving(nutrients, "protein_g", serving_grams),
                carbohydrate_g=_nutrient_at_serving(
                    nutrients, "carbohydrate_g", serving_grams
                ),
                fat_g=_nutrient_at_serving(nutrients, "fat_g", serving_grams),
                macro_gap_addressed="carbohydrate_g",
                score=_carbohydrate_candidate_score(
                    nutrients=nutrients,
                    serving_grams=serving_grams,
                    search_priority=food["search_priority"],
                    preference_rank=preference_rank,
                    calorie_gap=calorie_room,
                ),
                confidence=carbohydrate_gap.confidence,
                reason_codes=_unique(reason_codes),
                limitations=limitations,
            )
        )
    return candidates


def _calorie_support_suggestion_candidates(
    macro_gaps: list[NutritionMacroGap],
    *,
    logging_incomplete: bool,
) -> list[CanonicalFoodSuggestionCandidate]:
    calorie_gap = _macro_gap_by_name(macro_gaps, "calories")
    if calorie_gap is None or not _is_displayable_macro_gap(calorie_gap):
        return []
    if logging_incomplete:
        return []

    candidates: list[CanonicalFoodSuggestionCandidate] = []
    protein_above_target = _displayable_gap_status(
        macro_gaps, "protein_g", TARGET_STATUS_ABOVE
    )
    carbohydrate_above_target = _displayable_gap_status(
        macro_gaps, "carbohydrate_g", TARGET_STATUS_ABOVE
    )
    fat_above_target = _displayable_gap_status(macro_gaps, "fat_g", TARGET_STATUS_ABOVE)

    for food in _canonical_food_nutrient_maps():
        bounds = _serving_bounds_for_food(food["display_name"], "calories")
        if bounds is None:
            continue
        nutrients = food["nutrients"]
        if not _required_macro_nutrients_available(nutrients):
            continue
        if nutrients["calories"] <= 0:
            continue

        min_grams, max_grams, preference_rank = bounds
        serving_grams, was_bounded = _serving_grams_for_gap(
            gap_value=float(calorie_gap.gap_value),
            nutrient_per_100g=nutrients["calories"],
            min_grams=min_grams,
            max_grams=max_grams,
        )
        if _calorie_support_conflicts_with_above_macros(
            macro_gaps=macro_gaps,
            nutrients=nutrients,
            serving_grams=serving_grams,
        ):
            continue

        reason_codes = [
            "canonical_food_catalog_available",
            "canonical_food_nutrients_available",
            "practical_serving_selected",
            "calorie_support_suggestion_available",
        ]
        limitations: list[str] = []
        if was_bounded:
            reason_codes.append("serving_limited_by_practical_bounds")
        if protein_above_target or carbohydrate_above_target or fat_above_target:
            reason_codes.append("macro_conflict_checked")

        candidates.append(
            CanonicalFoodSuggestionCandidate(
                canonical_food_id=food["canonical_food_id"],
                display_name=food["display_name"],
                food_type=food["food_type"],
                serving_grams=serving_grams,
                calories=_nutrient_at_serving(nutrients, "calories", serving_grams),
                protein_g=_nutrient_at_serving(nutrients, "protein_g", serving_grams),
                carbohydrate_g=_nutrient_at_serving(
                    nutrients, "carbohydrate_g", serving_grams
                ),
                fat_g=_nutrient_at_serving(nutrients, "fat_g", serving_grams),
                macro_gap_addressed="calories",
                score=_calorie_support_candidate_score(
                    nutrients=nutrients,
                    serving_grams=serving_grams,
                    search_priority=food["search_priority"],
                    preference_rank=preference_rank,
                    protein_above_target=protein_above_target,
                    carbohydrate_above_target=carbohydrate_above_target,
                    fat_above_target=fat_above_target,
                ),
                confidence=calorie_gap.confidence,
                reason_codes=_unique(reason_codes),
                limitations=limitations,
            )
        )
    return candidates


def _fat_support_suggestion_candidates(
    macro_gaps: list[NutritionMacroGap],
    *,
    logging_incomplete: bool,
) -> list[CanonicalFoodSuggestionCandidate]:
    fat_gap = _macro_gap_by_name(macro_gaps, "fat_g")
    calorie_gap = _macro_gap_by_name(macro_gaps, "calories")
    if fat_gap is None or not _is_displayable_macro_gap(fat_gap):
        return []
    if calorie_gap is None or not calorie_gap.display_allowed:
        return []
    if calorie_gap.target_status == TARGET_STATUS_ABOVE:
        return []
    if logging_incomplete:
        return []

    candidates: list[CanonicalFoodSuggestionCandidate] = []
    protein_above_target = _displayable_gap_status(
        macro_gaps, "protein_g", TARGET_STATUS_ABOVE
    )
    carbohydrate_above_target = _displayable_gap_status(
        macro_gaps, "carbohydrate_g", TARGET_STATUS_ABOVE
    )

    for food in _canonical_food_nutrient_maps():
        bounds = _serving_bounds_for_food(food["display_name"], "fat_g")
        if bounds is None:
            continue
        nutrients = food["nutrients"]
        if not _required_macro_nutrients_available(nutrients):
            continue
        if nutrients["fat_g"] <= 0:
            continue

        min_grams, max_grams, preference_rank = bounds
        serving_grams, was_bounded = _serving_grams_for_gap(
            gap_value=float(fat_gap.gap_value),
            nutrient_per_100g=nutrients["fat_g"],
            min_grams=min_grams,
            max_grams=max_grams,
        )
        if _fat_support_conflicts_with_above_macros(
            macro_gaps=macro_gaps,
            nutrients=nutrients,
            serving_grams=serving_grams,
        ):
            continue

        reason_codes = [
            "canonical_food_catalog_available",
            "canonical_food_nutrients_available",
            "practical_serving_selected",
            "fat_support_suggestion_available",
        ]
        limitations: list[str] = []
        if was_bounded:
            reason_codes.append("serving_limited_by_practical_bounds")
        if protein_above_target or carbohydrate_above_target:
            reason_codes.append("macro_conflict_checked")

        candidates.append(
            CanonicalFoodSuggestionCandidate(
                canonical_food_id=food["canonical_food_id"],
                display_name=food["display_name"],
                food_type=food["food_type"],
                serving_grams=serving_grams,
                calories=_nutrient_at_serving(nutrients, "calories", serving_grams),
                protein_g=_nutrient_at_serving(nutrients, "protein_g", serving_grams),
                carbohydrate_g=_nutrient_at_serving(
                    nutrients, "carbohydrate_g", serving_grams
                ),
                fat_g=_nutrient_at_serving(nutrients, "fat_g", serving_grams),
                macro_gap_addressed="fat_g",
                score=_fat_support_candidate_score(
                    nutrients=nutrients,
                    serving_grams=serving_grams,
                    search_priority=food["search_priority"],
                    preference_rank=preference_rank,
                    protein_above_target=protein_above_target,
                    carbohydrate_above_target=carbohydrate_above_target,
                ),
                confidence=fat_gap.confidence,
                reason_codes=_unique(reason_codes),
                limitations=limitations,
            )
        )
    return candidates


def get_canonical_food_suggestion_candidates(
    macro_gaps: list[NutritionMacroGap],
    *,
    logging_incomplete: bool = False,
) -> list[CanonicalFoodSuggestionCandidate]:
    """Build deterministic suggestion candidates from canonical foods only."""

    return [
        *_protein_suggestion_candidates(
            macro_gaps,
            logging_incomplete=logging_incomplete,
        ),
        *_carbohydrate_suggestion_candidates(
            macro_gaps,
            logging_incomplete=logging_incomplete,
        ),
        *_calorie_support_suggestion_candidates(
            macro_gaps,
            logging_incomplete=logging_incomplete,
        ),
        *_fat_support_suggestion_candidates(
            macro_gaps,
            logging_incomplete=logging_incomplete,
        ),
    ]


def rank_food_suggestion_candidates(
    candidates: list[CanonicalFoodSuggestionCandidate],
    *,
    limit: int = 3,
) -> list[CanonicalFoodSuggestionCandidate]:
    return sorted(
        candidates,
        key=lambda candidate: (
            _MACRO_PRIORITY.get(candidate.macro_gap_addressed, 99),
            -candidate.score,
            candidate.serving_grams,
            candidate.display_name,
            candidate.canonical_food_id,
        ),
    )[: max(0, int(limit))]


def _summary_for_candidate(candidate: CanonicalFoodSuggestionCandidate) -> str:
    if candidate.macro_gap_addressed == "carbohydrate_g":
        carbohydrate = candidate.carbohydrate_g or 0.0
        return (
            f"{candidate.serving_grams:g}g {candidate.display_name} adds about "
            f"{carbohydrate:g}g carbohydrate."
        )
    if candidate.macro_gap_addressed == "calories":
        calories = candidate.calories or 0.0
        return (
            f"{candidate.serving_grams:g}g {candidate.display_name} adds about "
            f"{calories:g} kcal for optional energy support."
        )
    if candidate.macro_gap_addressed == "fat_g":
        fat = candidate.fat_g or 0.0
        return (
            f"{candidate.serving_grams:g}g {candidate.display_name} adds about "
            f"{fat:g}g fat as a small optional fat-support option."
        )

    protein = candidate.protein_g or 0.0
    if "yogurt" in candidate.display_name.lower():
        return (
            f"{candidate.serving_grams:g}g {candidate.display_name} is a smaller protein option "
            f"and adds about {protein:g}g protein."
        )
    return (
        f"{candidate.serving_grams:g}g {candidate.display_name} adds about "
        f"{protein:g}g protein."
    )


def _approved_suggestion_from_candidate(
    candidate: CanonicalFoodSuggestionCandidate,
) -> ApprovedFoodSuggestion:
    summary = _summary_for_candidate(candidate)
    if _text_contains_forbidden_language(summary):
        raise ValueError("Forbidden food suggestion summary generated.")
    return ApprovedFoodSuggestion(
        canonical_food_id=candidate.canonical_food_id,
        display_name=candidate.display_name,
        suggested_grams=candidate.serving_grams,
        estimated_calories=candidate.calories,
        estimated_protein_g=candidate.protein_g,
        estimated_carbohydrate_g=candidate.carbohydrate_g,
        estimated_fat_g=candidate.fat_g,
        macro_gap_addressed=candidate.macro_gap_addressed,
        suggestion_summary=summary,
        confidence=candidate.confidence,
        reason_codes=list(candidate.reason_codes),
        limitations=list(candidate.limitations),
    )


def _is_displayable_macro_gap(gap: NutritionMacroGap) -> bool:
    return (
        gap.display_allowed
        and gap.target_status == TARGET_STATUS_BELOW
        and gap.gap_value is not None
        and gap.gap_value > 0
    )


def _unsupported_v1_macro_gaps(
    macro_gaps: list[NutritionMacroGap],
) -> list[NutritionMacroGap]:
    return [
        gap
        for gap in macro_gaps
        if gap.macro_name in _UNSUPPORTED_SUGGESTION_GAP_REASON_CODES
        and _is_displayable_macro_gap(gap)
    ]


def _unsupported_v1_limitation(
    unsupported_gaps: list[NutritionMacroGap],
) -> str:
    labels = [
        _UNSUPPORTED_SUGGESTION_GAP_LABELS[gap.macro_name] for gap in unsupported_gaps
    ]
    if not labels:
        return "Only protein food suggestions are enabled in this version."
    if len(labels) == 1:
        gap_text = f"{labels[0]} food suggestions are"
    elif len(labels) == 2:
        gap_text = f"{labels[0]} and {labels[1]} food suggestions are"
    else:
        gap_text = f"{', '.join(labels[:-1])}, and {labels[-1]} food suggestions are"
    return f"Protein is not below target for this date. {gap_text.capitalize()} not enabled in this version."


def _approved_suggestion_macros(
    approved_suggestions: list[ApprovedFoodSuggestion],
) -> set[str]:
    return {suggestion.macro_gap_addressed for suggestion in approved_suggestions}


def _primary_gap_for_suggestions(
    approved_suggestions: list[ApprovedFoodSuggestion],
) -> str | None:
    if not approved_suggestions:
        return None
    return min(
        (suggestion.macro_gap_addressed for suggestion in approved_suggestions),
        key=lambda macro_name: _MACRO_PRIORITY.get(macro_name, 99),
    )


def _has_displayable_carbohydrate_gap(macro_gaps: list[NutritionMacroGap]) -> bool:
    carbohydrate_gap = _macro_gap_by_name(macro_gaps, "carbohydrate_g")
    return bool(carbohydrate_gap and _is_displayable_macro_gap(carbohydrate_gap))


def _has_displayable_calorie_gap(macro_gaps: list[NutritionMacroGap]) -> bool:
    calorie_gap = _macro_gap_by_name(macro_gaps, "calories")
    return bool(calorie_gap and _is_displayable_macro_gap(calorie_gap))


def _has_displayable_fat_gap(macro_gaps: list[NutritionMacroGap]) -> bool:
    fat_gap = _macro_gap_by_name(macro_gaps, "fat_g")
    return bool(fat_gap and _is_displayable_macro_gap(fat_gap))


def _has_blocked_fat_target(macro_gaps: list[NutritionMacroGap]) -> bool:
    fat_gap = _macro_gap_by_name(macro_gaps, "fat_g")
    calorie_gap = _macro_gap_by_name(macro_gaps, "calories")
    return bool(
        fat_gap
        and not fat_gap.display_allowed
        and calorie_gap
        and calorie_gap.display_allowed
    )


def approve_food_suggestions(
    *,
    user_id: int,
    suggestion_date: str,
    macro_gaps: list[NutritionMacroGap],
    candidates: list[CanonicalFoodSuggestionCandidate],
    summary_confidence: str = "Limited",
    logging_incomplete: bool = False,
    limit: int = 3,
) -> ApprovedNutritionFoodSuggestions:
    ranked_candidates = rank_food_suggestion_candidates(candidates, limit=limit)
    approved_suggestions = [
        _approved_suggestion_from_candidate(candidate)
        for candidate in ranked_candidates
    ]

    protein_gap = _macro_gap_by_name(macro_gaps, "protein_g")
    reason_codes: list[str] = []
    limitations: list[str] = []

    if approved_suggestions:
        suggestion_macros = _approved_suggestion_macros(approved_suggestions)
        if "protein_g" in suggestion_macros:
            reason_codes.extend(
                ["protein_gap_available", "protein_suggestion_available"]
            )
        if "carbohydrate_g" in suggestion_macros:
            reason_codes.extend(
                ["carbohydrate_gap_available", "carbohydrate_suggestion_available"]
            )
        if "calories" in suggestion_macros:
            reason_codes.extend(
                ["calorie_gap_available", "calorie_support_suggestion_available"]
            )
        if "fat_g" in suggestion_macros:
            reason_codes.extend(
                ["fat_gap_available", "fat_support_suggestion_available"]
            )
    elif protein_gap is None or not protein_gap.display_allowed:
        reason_codes.append("target_not_approved")
        limitations.append(
            "Protein food suggestions require an approved protein target."
        )
    elif protein_gap.target_status != TARGET_STATUS_BELOW:
        if _has_displayable_carbohydrate_gap(macro_gaps):
            carb_reason_codes, carb_limitations = _carbohydrate_block_limitations(
                macro_gaps,
                logging_incomplete=logging_incomplete,
            )
            reason_codes.extend(carb_reason_codes)
            limitations.extend(carb_limitations)
            if "carb_suggestion_limited" not in reason_codes:
                reason_codes.append("no_suitable_canonical_food_found")
                limitations.append(_SAFE_DEFAULT_LIMITATION)
        elif _has_displayable_calorie_gap(macro_gaps):
            calorie_reason_codes, calorie_limitations = (
                _calorie_support_block_limitations(
                    macro_gaps,
                    logging_incomplete=logging_incomplete,
                )
            )
            if calorie_limitations:
                reason_codes.extend(calorie_reason_codes)
                limitations.extend(calorie_limitations)
            else:
                reason_codes.append("no_suitable_canonical_food_found")
                limitations.append(_SAFE_DEFAULT_LIMITATION)
        elif _has_displayable_fat_gap(macro_gaps) or _has_blocked_fat_target(
            macro_gaps
        ):
            fat_reason_codes, fat_limitations = _fat_support_block_limitations(
                macro_gaps,
                logging_incomplete=logging_incomplete,
            )
            if fat_limitations:
                reason_codes.extend(fat_reason_codes)
                limitations.extend(fat_limitations)
            else:
                reason_codes.append("no_suitable_canonical_food_found")
                limitations.append(_SAFE_DEFAULT_LIMITATION)
        else:
            unsupported_gaps = _unsupported_v1_macro_gaps(macro_gaps)
            if unsupported_gaps:
                reason_codes.extend(
                    [
                        "no_supported_suggestion_gap_available",
                        "no_protein_gap_available",
                    ]
                )
                reason_codes.extend(
                    _UNSUPPORTED_SUGGESTION_GAP_REASON_CODES[gap.macro_name]
                    for gap in unsupported_gaps
                )
                limitations.append(_unsupported_v1_limitation(unsupported_gaps))
            else:
                reason_codes.append("no_macro_gap_detected")
                limitations.append(
                    "No approved macro gap is available for food suggestions."
                )
    elif _has_displayable_carbohydrate_gap(macro_gaps):
        carb_reason_codes, carb_limitations = _carbohydrate_block_limitations(
            macro_gaps,
            logging_incomplete=logging_incomplete,
        )
        if carb_limitations and not candidates:
            reason_codes.extend(carb_reason_codes)
            limitations.extend(carb_limitations)
        else:
            reason_codes.append("no_suitable_canonical_food_found")
            limitations.append(_SAFE_DEFAULT_LIMITATION)
    elif _has_displayable_calorie_gap(macro_gaps):
        calorie_reason_codes, calorie_limitations = _calorie_support_block_limitations(
            macro_gaps,
            logging_incomplete=logging_incomplete,
        )
        if calorie_limitations and not candidates:
            reason_codes.extend(calorie_reason_codes)
            limitations.extend(calorie_limitations)
        else:
            reason_codes.append("no_suitable_canonical_food_found")
            limitations.append(_SAFE_DEFAULT_LIMITATION)
    elif _has_displayable_fat_gap(macro_gaps) or _has_blocked_fat_target(macro_gaps):
        fat_reason_codes, fat_limitations = _fat_support_block_limitations(
            macro_gaps,
            logging_incomplete=logging_incomplete,
        )
        if fat_limitations and not candidates:
            reason_codes.extend(fat_reason_codes)
            limitations.extend(fat_limitations)
        else:
            reason_codes.append("no_suitable_canonical_food_found")
            limitations.append(_SAFE_DEFAULT_LIMITATION)
    elif not approved_suggestions:
        reason_codes.append("no_suitable_canonical_food_found")
        limitations.append(_SAFE_DEFAULT_LIMITATION)

    if logging_incomplete:
        reason_codes.append("logging_incomplete_limits_suggestions")
        limitations.append(
            "Suggestions are limited because logging appears incomplete."
        )

    suggestion_confidences = [
        suggestion.confidence for suggestion in approved_suggestions
    ]
    confidence = _rank_min(summary_confidence, *(suggestion_confidences or ["Limited"]))
    if approved_suggestions and summary_confidence in {"Moderate", "High"}:
        confidence = _rank_min(
            summary_confidence, *(suggestion_confidences or [summary_confidence])
        )

    return ApprovedNutritionFoodSuggestions(
        user_id=user_id,
        suggestion_date=suggestion_date,
        primary_gap=_primary_gap_for_suggestions(approved_suggestions),
        macro_gaps=macro_gaps,
        suggestions=approved_suggestions,
        confidence=confidence,
        reason_codes=_unique(reason_codes),
        limitations=_unique(limitations),
    )


def build_approved_nutrition_food_suggestions(
    user_id: int,
    suggestion_date: str | None = None,
    *,
    target_vs_actual_summary: TargetVsActualNutritionSummary | None = None,
    limit: int = 3,
) -> ApprovedNutritionFoodSuggestions:
    """Build approved deterministic food suggestions from approved macro gaps.

    The service composes existing target-vs-actual output and canonical nutrient
    data. It does not call AI, infer foods, invent serving sizes outside fixed
    practical bounds, mutate logged actuals, or create meal plans.
    """

    suggestion_date = suggestion_date or _today_iso()
    summary = target_vs_actual_summary or build_target_vs_actual_nutrition_summary(
        user_id,
        suggestion_date,
    )
    macro_gaps = build_nutrition_macro_gaps(summary)
    logging_incomplete = _is_logging_incomplete(summary)
    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=logging_incomplete,
    )
    return approve_food_suggestions(
        user_id=user_id,
        suggestion_date=suggestion_date,
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence=summary.confidence,
        logging_incomplete=logging_incomplete,
        limit=limit,
    )
