from __future__ import annotations

from datetime import date
from typing import Any

from database import get_connection
from models.nutrition_target_formula_models import (
    ApprovedMacroTargets,
    MacroTargetResult,
)
from models.nutrition_target_models import NutritionTargets
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    TARGET_STATUS_ABOVE,
    TARGET_STATUS_BELOW,
    TARGET_STATUS_NEAR,
    TARGET_STATUS_UNAVAILABLE,
    ApprovedNutritionGuidance,
    NutritionActuals,
    NutritionLoggingSummary,
    NutritionTargetComparison,
    TargetVsActualNutritionSummary,
)
from models.user_state_models import UserHealthState
from services.nutrition_target_formula_service import (
    build_nutrition_target_formula_inputs,
    calculate_nutrition_target_formula,
)
from services.nutrition_target_formula_validation_service import (
    approve_validated_macro_targets,
)
from services.user_service import get_user_profile
from services.user_state_service import build_user_health_state

_CONFIDENCE_RANK = {"Limited": 0, "Low": 1, "Moderate": 2, "High": 3}

_FORBIDDEN_NUTRITION_GUIDANCE_TERMS = [
    "you failed",
    "failed",
    "shame",
    "bad food",
    "good food",
    "cheat meal",
    "eating disorder",
    "medical",
    "disease",
    "diagnose",
    "supplement",
    "stalled fat loss",
    "stalled weight loss",
    "nutrition is inadequate",
    "must cut calories",
    "skip meals",
    "compensate tomorrow",
    "burn this off",
    "extreme restriction",
    "caused your workout",
    "caused poor performance",
]

_NUTRIENT_ALIASES = {
    "calories": "calories",
    "calorie": "calories",
    "energy": "calories",
    "protein": "protein",
    "protein_grams": "protein",
    "carbohydrates": "carbs",
    "carbohydrate": "carbs",
    "carbs": "carbs",
    "fat": "fat",
    "total fat": "fat",
    "fats": "fat",
    "fiber": "fiber",
    "fibre": "fiber",
}


def _today_iso() -> str:
    return date.today().isoformat()


def _normalize_nutrient_name(name: str) -> str | None:
    cleaned = name.strip().lower().replace("_", " ")
    return _NUTRIENT_ALIASES.get(cleaned)


def _round_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 1)


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


_PUBLIC_FORMULA_FILTER_TERMS = {"medical", "crewai", "ollama", "ai-generated"}


def _public_safe_formula_values(values: list[str]) -> list[str]:
    safe_values: list[str] = []
    for value in values:
        lowered = value.lower()
        if any(term in lowered for term in _PUBLIC_FORMULA_FILTER_TERMS):
            continue
        safe_values.append(value)
    return _unique(safe_values)


def _rank_min(*confidences: str) -> str:
    valid = [value for value in confidences if value in _CONFIDENCE_RANK]
    if not valid:
        return "Limited"
    return min(valid, key=lambda value: _CONFIDENCE_RANK[value])


def _rows_for_date(user_id: int, target_date: str) -> list[dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            food_entries.id AS entry_id,
            food_entries.grams AS grams,
            foods.name AS food_name,
            nutrients.name AS nutrient_name,
            nutrients.unit AS nutrient_unit,
            food_nutrients.amount_per_100g AS amount_per_100g
        FROM food_entries
        JOIN foods
            ON foods.id = food_entries.food_id
        LEFT JOIN food_nutrients
            ON food_nutrients.food_id = foods.id
        LEFT JOIN nutrients
            ON nutrients.id = food_nutrients.nutrient_id
        WHERE food_entries.user_id = ?
          AND food_entries.entry_date = ?
        ORDER BY food_entries.id
        """,
        (user_id, target_date),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def _entry_count_for_date(user_id: int, target_date: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) AS entry_count
        FROM food_entries
        WHERE user_id = ?
          AND entry_date = ?
        """,
        (user_id, target_date),
    )
    row = cursor.fetchone()
    conn.close()
    return int(row["entry_count"] or 0)


def build_nutrition_actuals(
    user_id: int, target_date: str | None = None
) -> NutritionActuals:
    """Calculate actual logged nutrition from existing food log rows.

    Missing nutrient rows remain missing. They are not coerced to zero because
    missing food nutrient data is different from a verified zero intake.
    """

    target_date = target_date or _today_iso()
    rows = _rows_for_date(user_id, target_date)
    entry_count = _entry_count_for_date(user_id, target_date)

    if entry_count == 0:
        return NutritionActuals(
            user_id=user_id,
            logging_date=target_date,
            logging_window="calendar_day",
            logged_meal_count=0,
            entry_count=0,
            source_count=0,
            reason_codes=["no_nutrition_logs_today", "nutrition_actuals_unavailable"],
        )

    entry_nutrients: dict[int, set[str]] = {}
    totals: dict[str, float] = {
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
        "fiber": 0.0,
    }
    seen_nutrient_totals: set[str] = set()

    for row in rows:
        entry_id = int(row["entry_id"])
        entry_nutrients.setdefault(entry_id, set())
        nutrient_name = row.get("nutrient_name")
        if nutrient_name is None:
            continue

        normalized = _normalize_nutrient_name(str(nutrient_name))
        if normalized is None:
            continue

        grams = float(row["grams"])
        amount_per_100g = row.get("amount_per_100g")
        if amount_per_100g is None:
            continue

        entry_nutrients[entry_id].add(normalized)
        totals[normalized] += float(amount_per_100g) * grams / 100.0
        seen_nutrient_totals.add(normalized)

    missing_counts: dict[str, int] = {}
    for nutrient in ["calories", "protein", "carbs", "fat", "fiber"]:
        missing_counts[nutrient] = sum(
            1 for nutrients in entry_nutrients.values() if nutrient not in nutrients
        )

    reason_codes = ["nutrition_logs_available"]
    if missing_counts["calories"]:
        reason_codes.append("missing_calorie_values")
    if any(missing_counts[nutrient] for nutrient in ["protein", "carbs", "fat"]):
        reason_codes.append("missing_macro_values")

    return NutritionActuals(
        user_id=user_id,
        logging_date=target_date,
        logging_window="calendar_day",
        logged_calories=(
            _round_or_none(totals["calories"])
            if "calories" in seen_nutrient_totals
            else None
        ),
        logged_protein=(
            _round_or_none(totals["protein"])
            if "protein" in seen_nutrient_totals
            else None
        ),
        logged_carbs=(
            _round_or_none(totals["carbs"]) if "carbs" in seen_nutrient_totals else None
        ),
        logged_fat=(
            _round_or_none(totals["fat"]) if "fat" in seen_nutrient_totals else None
        ),
        logged_fiber=(
            _round_or_none(totals["fiber"]) if "fiber" in seen_nutrient_totals else None
        ),
        logged_meal_count=entry_count,
        entry_count=entry_count,
        source_count=entry_count,
        missing_calorie_entries=missing_counts["calories"],
        missing_protein_entries=missing_counts["protein"],
        missing_carb_entries=missing_counts["carbs"],
        missing_fat_entries=missing_counts["fat"],
        missing_fiber_entries=missing_counts["fiber"],
        reason_codes=reason_codes,
    )


def _logging_summary_from_actuals(actuals: NutritionActuals) -> NutritionLoggingSummary:
    reason_codes = list(actuals.reason_codes)
    limitations: list[str] = []
    missing_nutrient_fields: list[str] = []

    if actuals.entry_count == 0:
        return NutritionLoggingSummary(
            user_id=actuals.user_id,
            logging_date=actuals.logging_date,
            logging_completeness=LOGGING_COMPLETENESS_NO_LOGS,
            confidence="Limited",
            logged_meal_count=0,
            entry_count=0,
            reason_codes=["no_nutrition_logs_today", "nutrition_actuals_unavailable"],
            limitations=["No nutrition logs were found for this date."],
        )

    missing_field_map = {
        "calories": actuals.missing_calorie_entries,
        "protein": actuals.missing_protein_entries,
        "carbohydrates": actuals.missing_carb_entries,
        "fat": actuals.missing_fat_entries,
    }
    for nutrient, count in missing_field_map.items():
        if count:
            missing_nutrient_fields.append(nutrient)

    if actuals.entry_count <= 1:
        completeness = LOGGING_COMPLETENESS_PARTIAL_DAY
        confidence = "Low"
        reason_codes.extend(
            ["partial_nutrition_logging", "entry_count_low", "meal_count_low"]
        )
        limitations.append("Nutrition logging appears partial for this date.")
    elif missing_nutrient_fields:
        completeness = LOGGING_COMPLETENESS_LIKELY_INCOMPLETE
        confidence = "Low"
        reason_codes.extend(
            [
                "likely_incomplete_nutrition_logging",
                "macro_targets_limited_by_logging_quality",
            ]
        )
        limitations.append(
            "Some logged foods are missing calorie or macro values, so comparisons stay limited."
        )
    elif actuals.entry_count == 2:
        completeness = LOGGING_COMPLETENESS_REASONABLY_COMPLETE
        confidence = "Moderate"
        reason_codes.append("partial_nutrition_logging")
        limitations.append(
            "Logged intake may not represent a complete day, so calorie conclusions stay cautious."
        )
    else:
        completeness = LOGGING_COMPLETENESS_COMPLETE_ENOUGH
        confidence = "High"
        reason_codes.append("complete_enough_for_guidance")

    return NutritionLoggingSummary(
        user_id=actuals.user_id,
        logging_date=actuals.logging_date,
        logging_completeness=completeness,
        confidence=confidence,
        logged_meal_count=actuals.logged_meal_count,
        entry_count=actuals.entry_count,
        missing_nutrient_fields=missing_nutrient_fields,
        reason_codes=_unique(reason_codes),
        limitations=limitations,
    )


def _profile_value(user_profile: Any, key: str, default: Any = None) -> Any:
    try:
        return user_profile[key]
    except (KeyError, IndexError, TypeError):
        return default


def _target_value_if_allowed(
    target: MacroTargetResult | None,
    *,
    display_allowed: bool,
    attr_name: str,
) -> int | None:
    if target is None or not display_allowed:
        return None
    value = getattr(target, attr_name)
    return int(value) if value is not None else None


def _approved_formula_limitations(approved_targets: ApprovedMacroTargets) -> list[str]:
    limitations = [
        *approved_targets.limitations,
        *approved_targets.formula_metadata.limitations,
    ]
    for target in [
        approved_targets.calorie_target,
        approved_targets.protein_target_g,
        approved_targets.carbohydrate_target_g,
        approved_targets.fat_target_g,
    ]:
        if target is not None:
            limitations.extend(target.limitations)
    return _public_safe_formula_values(limitations)


def _approved_macro_targets_to_nutrition_targets(
    approved_targets: ApprovedMacroTargets,
    health_state: UserHealthState,
) -> NutritionTargets:
    display_flags = approved_targets.display_flags
    body_weight = _as_float(health_state.latest_body_weight) or _as_float(
        health_state.starting_weight
    )
    reason_codes = [
        "formula_derived_targets",
        *approved_targets.reason_codes,
        *approved_targets.formula_metadata.reason_codes,
    ]

    for target in [
        approved_targets.calorie_target,
        approved_targets.protein_target_g,
        approved_targets.carbohydrate_target_g,
        approved_targets.fat_target_g,
    ]:
        if target is not None:
            reason_codes.extend(target.reason_codes)

    return NutritionTargets(
        body_weight_lb=round(body_weight, 1) if body_weight is not None else None,
        calorie_target_min=_target_value_if_allowed(
            approved_targets.calorie_target,
            display_allowed=display_flags["allow_calorie_targets"],
            attr_name="min_value",
        ),
        calorie_target_max=_target_value_if_allowed(
            approved_targets.calorie_target,
            display_allowed=display_flags["allow_calorie_targets"],
            attr_name="max_value",
        ),
        protein_grams_min=_target_value_if_allowed(
            approved_targets.protein_target_g,
            display_allowed=display_flags["allow_protein_targets"],
            attr_name="min_value",
        ),
        protein_grams_max=_target_value_if_allowed(
            approved_targets.protein_target_g,
            display_allowed=display_flags["allow_protein_targets"],
            attr_name="max_value",
        ),
        carbohydrate_grams_min=_target_value_if_allowed(
            approved_targets.carbohydrate_target_g,
            display_allowed=display_flags["allow_carbohydrate_targets"],
            attr_name="min_value",
        ),
        carbohydrate_grams_max=_target_value_if_allowed(
            approved_targets.carbohydrate_target_g,
            display_allowed=display_flags["allow_carbohydrate_targets"],
            attr_name="max_value",
        ),
        fat_grams_min=_target_value_if_allowed(
            approved_targets.fat_target_g,
            display_allowed=display_flags["allow_fat_targets"],
            attr_name="min_value",
        ),
        fat_grams_max=_target_value_if_allowed(
            approved_targets.fat_target_g,
            display_allowed=display_flags["allow_fat_targets"],
            attr_name="max_value",
        ),
        confidence=approved_targets.confidence,
        allow_calorie_targets=display_flags["allow_calorie_targets"],
        allow_protein_targets=display_flags["allow_protein_targets"],
        allow_carbohydrate_targets=display_flags["allow_carbohydrate_targets"],
        allow_fat_targets=display_flags["allow_fat_targets"],
        nutrition_display_message=(
            "Formula-derived nutrition targets are available for approved comparisons."
            if any(display_flags.values())
            else (
                "Nutrition target comparisons are limited until formula inputs improve."
            )
        ),
        reason_codes=_public_safe_formula_values(reason_codes),
    )


def build_formula_derived_nutrition_targets(
    health_state: UserHealthState,
    *,
    calculation_date: str | None = None,
) -> tuple[NutritionTargets, ApprovedMacroTargets]:
    """Build validated formula-derived targets for target-vs-actual comparisons.

    This composes the formula service directly instead of calling the HTTP API.
    Missing inputs stay missing; no AI, estimation, persistence, or food-log mutation
    occurs here.
    """

    user_profile = get_user_profile(health_state.user_id)
    sex = _profile_value(user_profile, "gender") if user_profile else None
    formula_inputs = build_nutrition_target_formula_inputs(
        health_state,
        calculation_date=calculation_date,
        sex=sex,
        input_source_metadata={"consumer": "nutrition_target_vs_actual"},
    )
    formula_result = calculate_nutrition_target_formula(formula_inputs)
    approved_targets = approve_validated_macro_targets(formula_result)
    return (
        _approved_macro_targets_to_nutrition_targets(approved_targets, health_state),
        approved_targets,
    )


def _target_range_for_nutrient(
    targets: NutritionTargets, nutrient: str
) -> tuple[float | None, float | None, bool, str]:
    if nutrient == "calories":
        return (
            targets.calorie_target_min,
            targets.calorie_target_max,
            targets.allow_calorie_targets,
            "calorie_target",
        )
    if nutrient == "protein":
        return (
            targets.protein_grams_min,
            targets.protein_grams_max,
            targets.allow_protein_targets,
            "protein_target",
        )
    if nutrient == "carbs":
        return (
            targets.carbohydrate_grams_min,
            targets.carbohydrate_grams_max,
            targets.allow_carbohydrate_targets,
            "carbohydrate_target",
        )
    if nutrient == "fat":
        return (
            targets.fat_grams_min,
            targets.fat_grams_max,
            targets.allow_fat_targets,
            "fat_target",
        )
    return None, None, False, f"{nutrient}_target"


def _actual_for_nutrient(actuals: NutritionActuals, nutrient: str) -> float | None:
    if nutrient == "calories":
        return actuals.logged_calories
    if nutrient == "protein":
        return actuals.logged_protein
    if nutrient == "carbs":
        return actuals.logged_carbs
    if nutrient == "fat":
        return actuals.logged_fat
    return None


def _comparison_confidence(
    targets: NutritionTargets,
    logging_summary: NutritionLoggingSummary,
) -> str:
    return _rank_min(targets.confidence, logging_summary.confidence)


def _comparison_available(
    nutrient: str,
    actual: float | None,
    target_min: float | None,
    target_max: float | None,
    target_allowed: bool,
    targets: NutritionTargets,
    logging_summary: NutritionLoggingSummary,
) -> tuple[bool, list[str], list[str]]:
    reason_codes: list[str] = []
    limitations: list[str] = []

    if not target_allowed or target_min is None or target_max is None:
        reason_codes.append(
            "calorie_target_unavailable"
            if nutrient == "calories"
            else f"{nutrient}_target_unavailable"
        )
        limitations.append(f"{nutrient.title()} target comparison is unavailable.")
        return False, reason_codes, limitations

    if targets.confidence == "Limited":
        reason_codes.append("target_confidence_limited")
        limitations.append(
            "Target confidence is limited, so comparison stays unavailable."
        )
        return False, reason_codes, limitations

    if actual is None:
        reason_codes.append(
            "calorie_delta_not_available"
            if nutrient == "calories"
            else f"{nutrient}_delta_not_available"
        )
        limitations.append(f"Logged {nutrient} is unavailable for this date.")
        return False, reason_codes, limitations

    if logging_summary.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS:
        reason_codes.append("no_nutrition_logs_today")
        limitations.append("No logged intake is available for comparison.")
        return False, reason_codes, limitations

    if nutrient == "calories":
        if targets.confidence not in {"Moderate", "High"}:
            reason_codes.append("calorie_target_limited")
            limitations.append("Calorie targets are limited.")
            return False, reason_codes, limitations
        if logging_summary.logging_completeness != LOGGING_COMPLETENESS_COMPLETE_ENOUGH:
            reason_codes.extend(
                ["calorie_delta_not_available", "comparison_limited_by_partial_day"]
            )
            limitations.append(
                "Calories are not compared because logging is not complete enough."
            )
            return False, reason_codes, limitations

    if nutrient in {"carbs", "fat"} and logging_summary.confidence == "Low":
        reason_codes.append("macro_targets_limited_by_logging_quality")
        limitations.append(
            "Macro comparisons are limited until nutrition logging is more complete."
        )
        return False, reason_codes, limitations

    reason_codes.append(
        "calorie_target_available"
        if nutrient == "calories"
        else f"{nutrient}_target_available"
    )
    return True, reason_codes, limitations


def _status_for_actual(actual: float, target_min: float, target_max: float) -> str:
    if actual < target_min:
        return TARGET_STATUS_BELOW
    if actual > target_max:
        return TARGET_STATUS_ABOVE
    return TARGET_STATUS_NEAR


def _build_comparison(
    nutrient: str,
    actuals: NutritionActuals,
    targets: NutritionTargets,
    logging_summary: NutritionLoggingSummary,
) -> NutritionTargetComparison:
    actual = _actual_for_nutrient(actuals, nutrient)
    target_min, target_max, target_allowed, _label = _target_range_for_nutrient(
        targets, nutrient
    )
    available, reason_codes, limitations = _comparison_available(
        nutrient,
        actual,
        target_min,
        target_max,
        target_allowed,
        targets,
        logging_summary,
    )
    confidence = _comparison_confidence(targets, logging_summary)

    if not available or actual is None or target_min is None or target_max is None:
        return NutritionTargetComparison(
            nutrient=nutrient,
            actual=actual,
            target_min=target_min,
            target_max=target_max,
            delta_min=None,
            delta_max=None,
            percent_of_target=None,
            target_status=TARGET_STATUS_UNAVAILABLE,
            comparison_available=False,
            confidence=confidence,
            reason_codes=_unique(reason_codes),
            limitations=limitations,
        )

    target_midpoint = (target_min + target_max) / 2.0
    status = _status_for_actual(actual, target_min, target_max)
    reason_codes.append(f"logged_{nutrient}_{status}")

    if nutrient == "protein" and status == TARGET_STATUS_NEAR:
        reason_codes.append("logged_intake_near_protein_target")
    if nutrient == "protein" and status == TARGET_STATUS_BELOW:
        reason_codes.append("logged_protein_below_target")

    return NutritionTargetComparison(
        nutrient=nutrient,
        actual=round(actual, 1),
        target_min=target_min,
        target_max=target_max,
        delta_min=round(actual - target_min, 1),
        delta_max=round(actual - target_max, 1),
        percent_of_target=(
            round((actual / target_midpoint) * 100, 1) if target_midpoint else None
        ),
        target_status=status,
        comparison_available=True,
        confidence=confidence,
        reason_codes=_unique(reason_codes),
        limitations=limitations,
    )


def _summary_confidence(
    targets: NutritionTargets, logging_summary: NutritionLoggingSummary
) -> str:
    return _rank_min(targets.confidence, logging_summary.confidence)


def build_target_vs_actual_nutrition_summary(
    user_id: int,
    target_date: str | None = None,
    *,
    health_state: UserHealthState | None = None,
    nutrition_targets: NutritionTargets | None = None,
    training_day_context_available: bool = False,
) -> TargetVsActualNutritionSummary:
    """Build deterministic nutrition target-vs-actual summary.

    This service reads existing food logs and approved NutritionTargets. It does
    not use AI, infer missing food values, mutate targets, or call external food
    databases.
    """

    target_date = target_date or _today_iso()
    health_state = health_state or build_user_health_state(user_id)
    formula_limitations: list[str] = []
    if nutrition_targets is None:
        (
            nutrition_targets,
            approved_formula_targets,
        ) = build_formula_derived_nutrition_targets(
            health_state,
            calculation_date=target_date,
        )
        formula_limitations = _approved_formula_limitations(approved_formula_targets)

    actuals = build_nutrition_actuals(user_id, target_date)
    logging_summary = _logging_summary_from_actuals(actuals)
    comparisons = {
        nutrient: _build_comparison(
            nutrient,
            actuals,
            nutrition_targets,
            logging_summary,
        )
        for nutrient in ["calories", "protein", "carbs", "fat"]
    }

    reason_codes = [*nutrition_targets.reason_codes, *logging_summary.reason_codes]
    limitations = [*formula_limitations, *logging_summary.limitations]

    if training_day_context_available:
        reason_codes.append("training_day_context_available")

    for nutrient, comparison in comparisons.items():
        reason_codes.extend(comparison.reason_codes)
        limitations.extend(comparison.limitations)
        if nutrient == "calories" and not comparison.comparison_available:
            reason_codes.append("calorie_delta_not_available")
        if nutrient == "protein" and not comparison.comparison_available:
            reason_codes.append("protein_delta_not_available")

    return TargetVsActualNutritionSummary(
        user_id=user_id,
        date=target_date,
        nutrition_actuals=actuals,
        logging_summary=logging_summary,
        comparisons=comparisons,
        logging_completeness=logging_summary.logging_completeness,
        confidence=_summary_confidence(nutrition_targets, logging_summary),
        reason_codes=_unique(reason_codes),
        limitations=_unique(limitations),
    )


def _protein_guidance(comparison: NutritionTargetComparison) -> str:
    if not comparison.comparison_available:
        return "Protein comparison is limited until approved protein targets and logged protein are available."
    if comparison.target_status == TARGET_STATUS_BELOW:
        return "Based on logged meals, protein is below today's target."
    if comparison.target_status == TARGET_STATUS_ABOVE:
        return "Based on logged meals, protein is above today's target range; treat this as context rather than a required change."
    return "Protein is close to target based on current logs."


def _calorie_guidance(
    comparison: NutritionTargetComparison,
    summary: TargetVsActualNutritionSummary,
) -> str:
    if not comparison.comparison_available:
        if summary.logging_completeness in {
            LOGGING_COMPLETENESS_PARTIAL_DAY,
            LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
            LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
        }:
            return "Nutrition logging is incomplete, so calorie conclusions should stay limited."
        return (
            "Calories are not compared because calorie targets are currently limited."
        )
    if comparison.target_status == TARGET_STATUS_BELOW:
        return "Logged calories are below the approved range based on complete-enough logs."
    if comparison.target_status == TARGET_STATUS_ABOVE:
        return "Logged calories are above the approved range based on complete-enough logs."
    return "Logged calories are near the approved range based on complete-enough logs."


def _macro_guidance(summary: TargetVsActualNutritionSummary) -> str:
    carb = summary.comparisons["carbs"]
    fat = summary.comparisons["fat"]
    if not carb.comparison_available or not fat.comparison_available:
        return "Macro comparisons are limited until logging is more complete."
    return (
        "Carbohydrate and fat logs can be compared cautiously against approved ranges."
    )


def _logging_guidance(summary: TargetVsActualNutritionSummary) -> str:
    if summary.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS:
        return "No nutrition logs were found for this date, so guidance should stay limited."
    if summary.logging_completeness in {
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    }:
        return "Logged intake is incomplete, so avoid making bigger nutrition changes from this day alone."
    return "Logged intake is complete enough to support cautious nutrition guidance."


def build_approved_nutrition_guidance(
    summary: TargetVsActualNutritionSummary,
) -> ApprovedNutritionGuidance:
    protein = summary.comparisons["protein"]
    calories = summary.comparisons["calories"]

    if summary.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS:
        summary_message = "No nutrition logs were found for this date."
    elif summary.logging_completeness in {
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    }:
        summary_message = (
            "Nutrition logging is incomplete, so conclusions should stay limited."
        )
    else:
        summary_message = (
            "Logged nutrition can be compared cautiously with approved targets."
        )

    return ApprovedNutritionGuidance(
        user_id=summary.user_id,
        date=summary.date,
        summary_message=summary_message,
        protein_guidance=_protein_guidance(protein),
        calorie_guidance=_calorie_guidance(calories, summary),
        macro_guidance=_macro_guidance(summary),
        logging_guidance=_logging_guidance(summary),
        confidence=summary.confidence,
        reason_codes=list(summary.reason_codes),
        limitations=list(summary.limitations),
    )


def _text_blob_from_guidance(guidance: ApprovedNutritionGuidance) -> str:
    return " ".join(
        [
            guidance.summary_message,
            guidance.protein_guidance,
            guidance.calorie_guidance,
            guidance.macro_guidance,
            guidance.logging_guidance,
        ]
    ).lower()


def validate_target_vs_actual_nutrition_summary(
    summary: TargetVsActualNutritionSummary,
    guidance: ApprovedNutritionGuidance | None = None,
) -> list[str]:
    violations: list[str] = []
    guidance = guidance or build_approved_nutrition_guidance(summary)
    text = _text_blob_from_guidance(guidance)

    for term in _FORBIDDEN_NUTRITION_GUIDANCE_TERMS:
        if term in text:
            violations.append("Nutrition guidance contains forbidden language.")
            break

    if (
        summary.logging_completeness
        in {
            LOGGING_COMPLETENESS_NO_LOGS,
            LOGGING_COMPLETENESS_PARTIAL_DAY,
            LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
        }
        and summary.comparisons["calories"].comparison_available
    ):
        violations.append(
            "Calorie comparison must stay unavailable when logging is incomplete."
        )

    if summary.confidence in {"Limited", "Low"}:
        hard_terms = ["must", "exactly", "definitely", "guarantees"]
        if any(term in text for term in hard_terms):
            violations.append("Low-confidence nutrition guidance must stay soft.")

    if "calorie" in guidance.protein_guidance.lower():
        violations.append("Protein guidance should not make calorie claims.")

    return violations
