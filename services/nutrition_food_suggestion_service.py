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
_UNSUPPORTED_SUGGESTION_GAP_REASON_CODES = {
    "calories": "calorie_gap_suggestions_not_enabled_v1",
    "carbohydrate_g": "carbohydrate_gap_suggestions_not_enabled_v1",
    "fat_g": "fat_gap_suggestions_not_enabled_v1",
}
_UNSUPPORTED_SUGGESTION_GAP_LABELS = {
    "calories": "calorie",
    "carbohydrate_g": "carbohydrate",
    "fat_g": "fat",
}


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


def _serving_bounds_for_food(display_name: str) -> tuple[float, float, int] | None:
    if display_name in _PROTEIN_SUGGESTION_NAMES:
        min_grams, max_grams, preference_rank = _PROTEIN_SUGGESTION_NAMES[display_name]
        return float(min_grams), float(max_grams), int(preference_rank)
    return None


def _serving_grams_for_gap(
    *,
    protein_gap_g: float,
    protein_per_100g: float,
    min_grams: float,
    max_grams: float,
) -> tuple[float, bool]:
    if protein_per_100g <= 0:
        return min_grams, True
    desired_grams = protein_gap_g * 100.0 / protein_per_100g
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


def _candidate_score(
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


def get_canonical_food_suggestion_candidates(
    macro_gaps: list[NutritionMacroGap],
    *,
    logging_incomplete: bool = False,
) -> list[CanonicalFoodSuggestionCandidate]:
    """Build deterministic suggestion candidates from canonical foods only."""

    protein_gap = _macro_gap_by_name(macro_gaps, "protein_g")
    if (
        protein_gap is None
        or not protein_gap.display_allowed
        or protein_gap.target_status != TARGET_STATUS_BELOW
        or protein_gap.gap_value is None
        or protein_gap.gap_value <= 0
    ):
        return []

    candidates: list[CanonicalFoodSuggestionCandidate] = []
    for food in _canonical_food_nutrient_maps():
        bounds = _serving_bounds_for_food(food["display_name"])
        if bounds is None:
            continue
        nutrients = food["nutrients"]
        required_keys = {"calories", "protein_g", "carbohydrate_g", "fat_g"}
        if not required_keys.issubset(nutrients):
            continue
        if nutrients["protein_g"] <= 0:
            continue

        min_grams, max_grams, preference_rank = bounds
        serving_grams, was_bounded = _serving_grams_for_gap(
            protein_gap_g=float(protein_gap.gap_value),
            protein_per_100g=nutrients["protein_g"],
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
                score=_candidate_score(
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


def rank_food_suggestion_candidates(
    candidates: list[CanonicalFoodSuggestionCandidate],
    *,
    limit: int = 3,
) -> list[CanonicalFoodSuggestionCandidate]:
    return sorted(
        candidates,
        key=lambda candidate: (
            -candidate.score,
            candidate.serving_grams,
            candidate.display_name,
            candidate.canonical_food_id,
        ),
    )[: max(0, int(limit))]


def _summary_for_candidate(candidate: CanonicalFoodSuggestionCandidate) -> str:
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

    if protein_gap is None or not protein_gap.display_allowed:
        reason_codes.append("target_not_approved")
        limitations.append(
            "Protein food suggestions require an approved protein target."
        )
    elif protein_gap.target_status != TARGET_STATUS_BELOW:
        unsupported_gaps = _unsupported_v1_macro_gaps(macro_gaps)
        if unsupported_gaps:
            reason_codes.extend(
                ["no_supported_suggestion_gap_available", "no_protein_gap_available"]
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
    elif not approved_suggestions:
        reason_codes.append("no_suitable_canonical_food_found")
        limitations.append(_SAFE_DEFAULT_LIMITATION)
    else:
        reason_codes.extend(["protein_gap_available", "protein_suggestion_available"])

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
        primary_gap="protein_g" if approved_suggestions else None,
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
