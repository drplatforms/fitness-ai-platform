from __future__ import annotations

from datetime import date
from typing import Any

from models.nutrition_target_formula_models import (
    ApprovedMacroTargets,
    MacroTargetResult,
    NutritionTargetFormulaInputs,
    NutritionTargetFormulaMetadata,
    NutritionTargetFormulaResult,
)
from models.user_state_models import UserHealthState

FORMULA_NAME = "nutrition_target_formula_engine"
FORMULA_VERSION = "v1_service"
CALORIE_METHOD = "mifflin_st_jeor_activity_goal_range"
PROTEIN_METHOD = "body_weight_goal_training_range"
FAT_METHOD = "approved_calorie_percent_range"
CARBOHYDRATE_METHOD = "approved_calorie_remainder_after_protein_and_fat"
COACHING_ESTIMATE_LIMITATION = (
    "Targets are coaching estimates based on available profile and training context, "
    "not medical nutrition advice."
)


def build_nutrition_target_formula_inputs(
    health_state: UserHealthState,
    *,
    calculation_date: str | None = None,
    sex: str | None = None,
    formula_version_requested: str | None = FORMULA_VERSION,
    input_source_metadata: dict[str, Any] | None = None,
) -> NutritionTargetFormulaInputs:
    """Build formula inputs from approved backend health-state context.

    UserHealthState currently carries age, height, weight, goal, activity, recovery,
    nutrition, and training context. It does not carry sex/gender, so callers may
    pass an approved value when available. Missing values remain missing; this
    function does not infer or fake formula inputs.
    """

    body_weight = _as_float(health_state.latest_body_weight) or _as_float(
        health_state.starting_weight
    )
    height_in = _cm_to_inches(_as_float(health_state.height_cm))
    training_frequency = (
        health_state.training_state.workout_count
        if health_state.training_state.workout_count > 0
        else None
    )
    metadata = {
        "source": "UserHealthState",
        "sex_source": "explicit_argument" if sex else "missing_from_health_state",
    }
    if input_source_metadata:
        metadata.update(input_source_metadata)

    return NutritionTargetFormulaInputs(
        user_id=health_state.user_id,
        calculation_date=calculation_date or date.today().isoformat(),
        body_weight_lb=body_weight,
        height_in=height_in,
        age_years=health_state.age,
        sex=_normalize_sex(sex),
        activity_level=health_state.activity_level,
        training_frequency_per_week=training_frequency,
        training_load=health_state.training_state.training_load,
        primary_goal=health_state.primary_goal,
        goal_weight_lb=_as_float(health_state.goal_weight),
        recovery_status=health_state.recovery_state.readiness_level,
        nutrition_logging_quality=_nutrition_logging_quality(health_state),
        recent_weight_trend=health_state.recovery_state.weight_trend,
        formula_version_requested=formula_version_requested,
        input_source_metadata=metadata,
    )


def calculate_nutrition_target_formula(
    inputs: NutritionTargetFormulaInputs,
) -> NutritionTargetFormulaResult:
    """Calculate deterministic, display-gated macro target results."""

    reason_codes: list[str] = [
        "formula_version_recorded",
        "not_medical_nutrition_advice",
    ]
    limitations: list[str] = []
    assumptions: list[str] = []
    inputs_used = _inputs_used(inputs)

    if _formula_inputs_complete(inputs):
        reason_codes.append("formula_inputs_complete")
    else:
        reason_codes.append("formula_inputs_limited")
        limitations.append(
            "Some formula inputs are missing, so target display is limited."
        )

    protein_target = _calculate_protein_target(inputs)
    calorie_target = _calculate_calorie_target(inputs)
    fat_target = _calculate_fat_target(inputs, calorie_target)
    carbohydrate_target = _calculate_carbohydrate_target(
        inputs,
        calorie_target=calorie_target,
        protein_target=protein_target,
        fat_target=fat_target,
    )

    target_map = {
        "allow_calorie_targets": calorie_target,
        "allow_protein_targets": protein_target,
        "allow_carbohydrate_targets": carbohydrate_target,
        "allow_fat_targets": fat_target,
    }
    display_flags = {
        flag: bool(target and target.display_allowed)
        for flag, target in target_map.items()
    }

    for target in [calorie_target, protein_target, carbohydrate_target, fat_target]:
        reason_codes.extend(target.reason_codes)
        limitations.extend(target.limitations)

    confidence = _overall_confidence(display_flags, inputs)
    metadata_reason_codes = _dedupe(reason_codes)
    metadata_limitations = _dedupe(limitations)

    metadata = NutritionTargetFormulaMetadata(
        formula_name=FORMULA_NAME,
        formula_version=inputs.formula_version_requested or FORMULA_VERSION,
        calculation_date=inputs.calculation_date,
        inputs_used=inputs_used,
        assumptions=assumptions,
        rounding_rules=[
            "round_calories_to_nearest_50",
            "round_protein_to_nearest_5_g",
            "round_carbohydrate_to_nearest_5_g",
            "round_fat_to_nearest_5_g",
        ],
        target_basis=(
            "BMR/RMR estimate plus activity and goal context; protein by body "
            "weight; fat as approved calorie percentage; carbohydrate as remainder."
        ),
        reason_codes=metadata_reason_codes,
        limitations=metadata_limitations,
    )

    return NutritionTargetFormulaResult(
        user_id=inputs.user_id,
        calculation_date=inputs.calculation_date,
        calorie_target=calorie_target,
        protein_target=protein_target,
        carbohydrate_target=carbohydrate_target,
        fat_target=fat_target,
        formula_metadata=metadata,
        confidence=confidence,
        display_flags=display_flags,
        reason_codes=metadata_reason_codes,
        limitations=metadata_limitations,
    )


def approve_macro_targets(
    formula_result: NutritionTargetFormulaResult,
) -> ApprovedMacroTargets:
    """Return the approved macro target contract for downstream consumers."""

    return ApprovedMacroTargets(
        user_id=formula_result.user_id,
        calculation_date=formula_result.calculation_date,
        calorie_target=formula_result.calorie_target,
        protein_target_g=formula_result.protein_target,
        carbohydrate_target_g=formula_result.carbohydrate_target,
        fat_target_g=formula_result.fat_target,
        confidence=formula_result.confidence,
        display_flags=dict(formula_result.display_flags),
        formula_metadata=formula_result.formula_metadata,
        reason_codes=list(formula_result.reason_codes),
        limitations=list(formula_result.limitations),
    )


def _calculate_protein_target(
    inputs: NutritionTargetFormulaInputs,
) -> MacroTargetResult:
    if inputs.body_weight_lb is None:
        return _blocked_target(
            target_type="protein_g",
            unit="g/day",
            method=PROTEIN_METHOD,
            reason_codes=["missing_body_weight", "protein_display_blocked"],
            limitations=["Protein target is blocked until body weight is available."],
        )

    min_factor, max_factor, goal_reason = _protein_factors(inputs.primary_goal)
    min_value = _round_to_nearest_5(inputs.body_weight_lb * min_factor)
    max_value = _round_to_nearest_5(inputs.body_weight_lb * max_factor)
    value = _round_to_nearest_5((min_value + max_value) / 2)

    return MacroTargetResult(
        target_type="protein_g",
        value=value,
        min_value=min_value,
        max_value=max_value,
        display_value=f"{min_value}-{max_value} g/day",
        unit="g/day",
        confidence="Moderate" if inputs.primary_goal else "Low",
        display_allowed=True,
        method=PROTEIN_METHOD,
        reason_codes=[
            "body_weight_available",
            "protein_formula_available",
            "protein_display_allowed",
            goal_reason,
        ],
        limitations=[COACHING_ESTIMATE_LIMITATION],
    )


def _calculate_calorie_target(
    inputs: NutritionTargetFormulaInputs,
) -> MacroTargetResult:
    missing = _missing_calorie_inputs(inputs)
    if missing:
        return _blocked_target(
            target_type="calories",
            unit="kcal/day",
            method=CALORIE_METHOD,
            reason_codes=[
                "calorie_formula_limited",
                "calorie_display_blocked",
                *missing,
            ],
            limitations=[
                (
                    "Calorie targets are blocked until required profile, activity, "
                    "and goal inputs are available."
                )
            ],
        )

    sex = _normalize_sex(inputs.sex)
    if sex is None:
        return _blocked_target(
            target_type="calories",
            unit="kcal/day",
            method=CALORIE_METHOD,
            reason_codes=[
                "calorie_formula_limited",
                "calorie_display_blocked",
                "missing_sex",
            ],
            limitations=["Calorie targets are blocked until sex is available."],
        )

    weight_kg = inputs.body_weight_lb * 0.45359237  # type: ignore[operator]
    height_cm = inputs.height_in * 2.54  # type: ignore[operator]
    bmr = _mifflin_st_jeor_bmr(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age_years=inputs.age_years,  # type: ignore[arg-type]
        sex=sex,
    )
    activity_multiplier, activity_reason = _activity_multiplier(inputs.activity_level)
    goal_min, goal_max, goal_reason = _goal_calorie_adjustment(inputs.primary_goal)

    min_value = max(1200, _round_to_nearest_50(bmr * activity_multiplier * goal_min))
    max_value = max(
        min_value, _round_to_nearest_50(bmr * activity_multiplier * goal_max)
    )
    value = _round_to_nearest_50((min_value + max_value) / 2)

    confidence = _calorie_confidence(inputs)
    return MacroTargetResult(
        target_type="calories",
        value=value,
        min_value=min_value,
        max_value=max_value,
        display_value=f"{min_value}-{max_value} kcal/day",
        unit="kcal/day",
        confidence=confidence,
        display_allowed=True,
        method=CALORIE_METHOD,
        reason_codes=[
            "calorie_formula_available",
            "calorie_display_allowed",
            "body_weight_available",
            "activity_level_available",
            "goal_context_available",
            activity_reason,
            goal_reason,
        ],
        limitations=[COACHING_ESTIMATE_LIMITATION],
    )


def _calculate_fat_target(
    inputs: NutritionTargetFormulaInputs, calorie_target: MacroTargetResult
) -> MacroTargetResult:
    if not calorie_target.display_allowed or calorie_target.min_value is None:
        return _blocked_target(
            target_type="fat_g",
            unit="g/day",
            method=FAT_METHOD,
            reason_codes=[
                "fat_formula_limited",
                "fat_display_blocked",
                "carbohydrate_depends_on_calorie_target",
            ],
            limitations=["Fat target is blocked until calorie target is approved."],
        )

    min_value = _round_to_nearest_5((calorie_target.min_value * 0.20) / 9)
    max_value = _round_to_nearest_5((calorie_target.max_value * 0.30) / 9)  # type: ignore[operator]
    value = _round_to_nearest_5((min_value + max_value) / 2)

    return MacroTargetResult(
        target_type="fat_g",
        value=value,
        min_value=min_value,
        max_value=max_value,
        display_value=f"{min_value}-{max_value} g/day",
        unit="g/day",
        confidence=calorie_target.confidence,
        display_allowed=True,
        method=FAT_METHOD,
        reason_codes=["fat_formula_available", "fat_display_allowed"],
        limitations=[COACHING_ESTIMATE_LIMITATION],
    )


def _calculate_carbohydrate_target(
    inputs: NutritionTargetFormulaInputs,
    *,
    calorie_target: MacroTargetResult,
    protein_target: MacroTargetResult,
    fat_target: MacroTargetResult,
) -> MacroTargetResult:
    if not calorie_target.display_allowed:
        return _blocked_target(
            target_type="carbohydrate_g",
            unit="g/day",
            method=CARBOHYDRATE_METHOD,
            reason_codes=[
                "carbohydrate_formula_limited",
                "carbohydrate_display_blocked",
                "carbohydrate_depends_on_calorie_target",
            ],
            limitations=[
                "Carbohydrate target is blocked until calorie target is approved."
            ],
        )

    if (
        calorie_target.min_value is None
        or calorie_target.max_value is None
        or protein_target.min_value is None
        or protein_target.max_value is None
        or fat_target.min_value is None
        or fat_target.max_value is None
    ):
        return _blocked_target(
            target_type="carbohydrate_g",
            unit="g/day",
            method=CARBOHYDRATE_METHOD,
            reason_codes=[
                "carbohydrate_formula_limited",
                "carbohydrate_display_blocked",
            ],
            limitations=[
                (
                    "Carbohydrate target is blocked until calorie, protein, and "
                    "fat targets are available."
                )
            ],
        )

    min_value = _round_to_nearest_5(
        max(
            0,
            (
                calorie_target.min_value
                - protein_target.max_value * 4
                - fat_target.max_value * 9
            )
            / 4,
        )
    )
    max_value = _round_to_nearest_5(
        max(
            0,
            (
                calorie_target.max_value
                - protein_target.min_value * 4
                - fat_target.min_value * 9
            )
            / 4,
        )
    )

    if max_value <= 0:
        return _blocked_target(
            target_type="carbohydrate_g",
            unit="g/day",
            method=CARBOHYDRATE_METHOD,
            reason_codes=[
                "carbohydrate_formula_limited",
                "carbohydrate_display_blocked",
            ],
            limitations=[
                (
                    "Carbohydrate remainder is unavailable from the approved "
                    "calorie, protein, and fat targets."
                )
            ],
        )

    if min_value > max_value:
        min_value = max_value
    value = _round_to_nearest_5((min_value + max_value) / 2)

    return MacroTargetResult(
        target_type="carbohydrate_g",
        value=value,
        min_value=min_value,
        max_value=max_value,
        display_value=f"{min_value}-{max_value} g/day",
        unit="g/day",
        confidence=calorie_target.confidence,
        display_allowed=True,
        method=CARBOHYDRATE_METHOD,
        reason_codes=[
            "carbohydrate_formula_available",
            "carbohydrate_display_allowed",
            "carbohydrate_depends_on_calorie_target",
        ],
        limitations=[COACHING_ESTIMATE_LIMITATION],
    )


def _blocked_target(
    *,
    target_type: str,
    unit: str,
    method: str,
    reason_codes: list[str],
    limitations: list[str],
) -> MacroTargetResult:
    return MacroTargetResult(
        target_type=target_type,
        value=None,
        min_value=None,
        max_value=None,
        display_value=None,
        unit=unit,
        confidence="Limited",
        display_allowed=False,
        method=method,
        reason_codes=reason_codes,
        limitations=limitations,
    )


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _cm_to_inches(height_cm: float | None) -> float | None:
    if height_cm is None:
        return None
    return round(height_cm / 2.54, 1)


def _normalize_sex(sex: str | None) -> str | None:
    if not sex:
        return None
    normalized = sex.strip().lower()
    if normalized in {"male", "m"}:
        return "male"
    if normalized in {"female", "f"}:
        return "female"
    return None


def _nutrition_logging_quality(health_state: UserHealthState) -> str:
    nutrition_state = health_state.nutrition_state
    if not nutrition_state.has_nutrition_data:
        return "missing"
    if (
        nutrition_state.calories == "Unknown"
        or nutrition_state.protein_grams == "Unknown"
        or nutrition_state.carbohydrate_grams == "Unknown"
        or nutrition_state.fat_grams == "Unknown"
        or "Incomplete" in nutrition_state.recovery_nutrition_status
    ):
        return "limited"
    return "complete_enough_for_guidance"


def _inputs_used(inputs: NutritionTargetFormulaInputs) -> list[str]:
    used: list[str] = []
    for field_name in [
        "body_weight_lb",
        "height_in",
        "age_years",
        "sex",
        "activity_level",
        "training_frequency_per_week",
        "training_load",
        "primary_goal",
        "goal_weight_lb",
        "recovery_status",
        "nutrition_logging_quality",
        "recent_weight_trend",
    ]:
        if getattr(inputs, field_name) is not None:
            used.append(field_name)
    return used


def _formula_inputs_complete(inputs: NutritionTargetFormulaInputs) -> bool:
    return not _missing_calorie_inputs(inputs)


def _missing_calorie_inputs(inputs: NutritionTargetFormulaInputs) -> list[str]:
    missing: list[str] = []
    if inputs.body_weight_lb is None:
        missing.append("missing_body_weight")
    if inputs.height_in is None:
        missing.append("missing_height")
    if inputs.age_years is None:
        missing.append("missing_age")
    if _normalize_sex(inputs.sex) is None:
        missing.append("missing_sex")
    if inputs.activity_level is None:
        missing.append("missing_activity_level")
    if inputs.primary_goal is None:
        missing.append("missing_primary_goal")
    return missing


def _mifflin_st_jeor_bmr(
    *, weight_kg: float, height_cm: float, age_years: int, sex: str
) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age_years
    if sex == "male":
        return base + 5
    return base - 161


def _activity_multiplier(activity_level: str | None) -> tuple[float, str]:
    activity = (activity_level or "").strip().lower().replace(" ", "_")
    if activity in {"sedentary", "very_low"}:
        return 1.2, "activity_level_available"
    if activity in {"low", "light", "lightly_active"}:
        return 1.35, "activity_level_available"
    if activity in {"moderate", "moderately_active"}:
        return 1.5, "activity_level_available"
    if activity in {"high", "active", "very_active"}:
        return 1.65, "activity_level_available"
    return 1.4, "formula_assumption_used"


def _goal_key(primary_goal: str | None) -> str:
    return (primary_goal or "").strip().lower().replace("/", "_").replace(" ", "_")


def _goal_calorie_adjustment(primary_goal: str | None) -> tuple[float, float, str]:
    goal = _goal_key(primary_goal)
    if "fat_loss" in goal or "fat-loss" in goal:
        return 0.90, 0.95, "goal_context_available"
    if "recomposition" in goal or "recomp" in goal:
        return 0.95, 1.02, "goal_context_available"
    if "muscle_gain" in goal or "hypertrophy" in goal:
        return 1.02, 1.08, "goal_context_available"
    if "strength" in goal or "performance" in goal:
        return 1.00, 1.08, "goal_context_available"
    if "maintain" in goal or "maintenance" in goal:
        return 0.97, 1.03, "goal_context_available"
    return 0.95, 1.05, "formula_assumption_used"


def _protein_factors(primary_goal: str | None) -> tuple[float, float, str]:
    goal = _goal_key(primary_goal)
    if "fat_loss" in goal or "recomposition" in goal or "recomp" in goal:
        return 0.8, 1.0, "goal_context_available"
    if "strength" in goal or "muscle_gain" in goal or "performance" in goal:
        return 0.75, 1.0, "training_context_available"
    return 0.7, 0.9, "formula_assumption_used"


def _calorie_confidence(inputs: NutritionTargetFormulaInputs) -> str:
    if inputs.nutrition_logging_quality in {"limited", "missing"}:
        return "Moderate"
    if inputs.training_load and inputs.recovery_status:
        return "High"
    return "Moderate"


def _overall_confidence(
    display_flags: dict[str, bool], inputs: NutritionTargetFormulaInputs
) -> str:
    if display_flags["allow_calorie_targets"] and all(display_flags.values()):
        if inputs.nutrition_logging_quality in {"limited", "missing"}:
            return "Moderate"
        return "High"
    if display_flags["allow_protein_targets"]:
        return "Low"
    return "Limited"


def _round_to_nearest_50(value: float) -> int:
    return int(round(value / 50.0) * 50)


def _round_to_nearest_5(value: float) -> int:
    return int(round(value / 5.0) * 5)


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return deduped
