from dataclasses import asdict

from models.nutrition_target_models import NutritionTargets
from models.user_state_models import UserHealthState

UNKNOWN = "Unknown"
LIMITED_CONFIDENCE = "Limited"
MODERATE_CONFIDENCE = "Moderate"
HIGH_CONFIDENCE = "High"
LIMITED_NUTRITION_DISPLAY_MESSAGE = (
    "Nutrition targets are limited until logging is more complete. Focus on "
    "verifying entries and improving consistency first."
)
APPROVED_NUTRITION_DISPLAY_MESSAGE = (
    "Nutrition targets are available as approved planning ranges based on current "
    "body weight, goal, activity level, and training context."
)


def _as_float(value) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _round_to_nearest_10(value: float) -> int:
    return int(round(value / 10.0) * 10)


def _goal_key(primary_goal: str) -> str:
    return primary_goal.lower().replace("/", "_").replace(" ", "_")


def _activity_multiplier(activity_level: str | None) -> float:
    activity = (activity_level or "").lower()
    if activity in {"high", "very_active", "very active"}:
        return 16.0
    if activity in {"low", "sedentary", "light"}:
        return 12.0
    return 14.0


def _goal_calorie_adjustment(primary_goal: str) -> tuple[float, float, str]:
    goal = _goal_key(primary_goal)
    if "fat_loss" in goal or "fat loss" in goal:
        return 0.85, 0.95, "fat_loss_adjustment"
    if "performance" in goal or "strength_progression" in goal:
        return 1.0, 1.08, "performance_or_strength_adjustment"
    if "recomposition" in goal or "recomp" in goal:
        return 0.95, 1.02, "recomposition_adjustment"
    return 0.95, 1.05, "general_goal_adjustment"


def _carb_factors(training_load: str) -> tuple[float, float, str]:
    if training_load == "High":
        return 1.5, 2.25, "high_training_carb_range"
    if training_load == "Moderate":
        return 1.0, 1.75, "moderate_training_carb_range"
    if training_load == "Low":
        return 0.75, 1.25, "low_training_carb_range"
    return 0.5, 1.0, "inactive_or_unknown_training_carb_range"


def _is_unknown(value) -> bool:
    return value == UNKNOWN or value is None


def _has_incomplete_nutrition_fields(health_state: UserHealthState) -> bool:
    nutrition_state = health_state.nutrition_state
    return (
        _is_unknown(nutrition_state.calories)
        or nutrition_state.calorie_status == UNKNOWN
        or nutrition_state.protein_status == UNKNOWN
        or _is_unknown(nutrition_state.protein_grams)
        or _is_unknown(nutrition_state.carbohydrate_grams)
        or _is_unknown(nutrition_state.fat_grams)
        or "Incomplete" in nutrition_state.recovery_nutrition_status
    )


def _target_confidence(
    health_state: UserHealthState, body_weight: float
) -> tuple[str, list[str]]:
    nutrition_state = health_state.nutrition_state
    reason_codes: list[str] = []

    if _has_incomplete_nutrition_fields(health_state):
        reason_codes.append("nutrition_logging_incomplete")
        return LIMITED_CONFIDENCE, reason_codes

    if not nutrition_state.has_nutrition_data:
        reason_codes.append("nutrition_logging_missing")
        return LIMITED_CONFIDENCE, reason_codes

    if health_state.activity_level and health_state.primary_goal and body_weight:
        return HIGH_CONFIDENCE, reason_codes

    reason_codes.append("profile_context_partial")
    return MODERATE_CONFIDENCE, reason_codes


def build_nutrition_targets(health_state: UserHealthState) -> NutritionTargets:
    """Calculate transparent v1 nutrition target ranges from factual health state.

    Missing nutrition fields remain unknown, never zero. Protein ranges can be
    calculated when body weight is available. Calorie targets are calculated for
    internal planning, but should only be exposed to users when confidence is
    Moderate or High.
    """
    body_weight = _as_float(health_state.latest_body_weight) or _as_float(
        health_state.starting_weight
    )
    reason_codes: list[str] = []

    if body_weight is None:
        return NutritionTargets(
            body_weight_lb=None,
            calorie_target_min=None,
            calorie_target_max=None,
            protein_grams_min=None,
            protein_grams_max=None,
            carbohydrate_grams_min=None,
            carbohydrate_grams_max=None,
            fat_grams_min=None,
            fat_grams_max=None,
            confidence=LIMITED_CONFIDENCE,
            allow_calorie_targets=False,
            allow_protein_targets=False,
            allow_carbohydrate_targets=False,
            allow_fat_targets=False,
            nutrition_display_message=LIMITED_NUTRITION_DISPLAY_MESSAGE,
            reason_codes=["missing_body_weight"],
        )

    activity_multiplier = _activity_multiplier(health_state.activity_level)
    goal_min, goal_max, goal_reason = _goal_calorie_adjustment(
        health_state.primary_goal
    )
    carb_min_factor, carb_max_factor, carb_reason = _carb_factors(
        health_state.training_state.training_load
    )

    base_calories = body_weight * activity_multiplier
    protein_min = _round_to_nearest_10(body_weight * 0.7)
    protein_max = _round_to_nearest_10(body_weight * 1.0)
    carbs_min = _round_to_nearest_10(body_weight * carb_min_factor)
    carbs_max = _round_to_nearest_10(body_weight * carb_max_factor)
    fat_min = _round_to_nearest_10(body_weight * 0.3)
    fat_max = _round_to_nearest_10(body_weight * 0.45)

    confidence, confidence_reasons = _target_confidence(health_state, body_weight)
    allow_calorie_targets = confidence in {MODERATE_CONFIDENCE, HIGH_CONFIDENCE}
    allow_macro_targets = confidence in {MODERATE_CONFIDENCE, HIGH_CONFIDENCE}
    nutrition_display_message = (
        APPROVED_NUTRITION_DISPLAY_MESSAGE
        if allow_macro_targets
        else LIMITED_NUTRITION_DISPLAY_MESSAGE
    )

    reason_codes.extend(
        [
            "body_weight_available",
            goal_reason,
            carb_reason,
            f"activity_level_{health_state.activity_level or 'unknown'}",
            *confidence_reasons,
        ]
    )

    return NutritionTargets(
        body_weight_lb=round(body_weight, 1),
        calorie_target_min=_round_to_nearest_10(base_calories * goal_min),
        calorie_target_max=_round_to_nearest_10(base_calories * goal_max),
        protein_grams_min=protein_min,
        protein_grams_max=protein_max,
        carbohydrate_grams_min=carbs_min,
        carbohydrate_grams_max=carbs_max,
        fat_grams_min=fat_min,
        fat_grams_max=fat_max,
        confidence=confidence,
        allow_calorie_targets=allow_calorie_targets,
        allow_protein_targets=True,
        allow_carbohydrate_targets=allow_macro_targets,
        allow_fat_targets=allow_macro_targets,
        nutrition_display_message=nutrition_display_message,
        reason_codes=reason_codes,
    )


def nutrition_targets_to_user_dict(targets: NutritionTargets) -> dict:
    """Return user-facing target data with confidence gates applied."""
    payload = asdict(targets)

    if not targets.allow_calorie_targets:
        payload["calorie_target_min"] = None
        payload["calorie_target_max"] = None

    if not targets.allow_protein_targets:
        payload["protein_grams_min"] = None
        payload["protein_grams_max"] = None

    if not targets.allow_carbohydrate_targets:
        payload["carbohydrate_grams_min"] = None
        payload["carbohydrate_grams_max"] = None

    if not targets.allow_fat_targets:
        payload["fat_grams_min"] = None
        payload["fat_grams_max"] = None

    return payload
