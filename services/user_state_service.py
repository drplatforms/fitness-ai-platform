from models.user_state_models import (
    UserHealthState,
    UserNutritionState,
    UserRecoveryState,
    UserTrainingState,
)
from services.nutrition_service import (
    get_nutrition_analysis,
)
from services.recovery_service import (
    get_recent_recovery_metrics,
)
from services.user_service import (
    get_user_profile,
)
from services.workout_service import (
    get_recent_workouts,
)

UNKNOWN_NUTRITION_VALUE = "Unknown"


def _get_nutrient_amount(
    nutrition_data: dict, possible_names: list[str]
) -> float | None:
    """Return a nutrient amount only when the nutrient field is present.

    Missing nutrition fields must remain unknown. They should not be converted
    to 0, because missing data is different from a logged zero intake.
    """
    for nutrient_name in possible_names:
        nutrient = nutrition_data.get(nutrient_name)

        if nutrient is not None:
            amount = nutrient.get("amount")

            if amount is None:
                return None

            return float(amount)

    return None


def _format_nutrition_value(value: float | None) -> float | str:
    if value is None:
        return UNKNOWN_NUTRITION_VALUE

    return round(value, 1)


def _classify_logged_nutrient(value: float | None) -> str:
    if value is None:
        return "Unknown"

    if value <= 0:
        return "Logged as Zero"

    return "Logged"


def _classify_calorie_status(calories: float | None) -> str:
    if calories is None:
        return "Unknown"

    if calories <= 0:
        return "Logged as Zero"

    if calories >= 2200:
        return "Logged - Higher Intake"

    if calories >= 1600:
        return "Logged - Moderate Intake"

    return "Logged - Lower Intake"


def _classify_recovery_nutrition_status(
    protein_grams: float | None,
    calories: float | None,
    carbohydrate_grams: float | None,
) -> str:
    if protein_grams is None and calories is None and carbohydrate_grams is None:
        return "Unknown"

    if calories is None:
        return "Incomplete - Calories Missing"

    if protein_grams is None:
        return "Incomplete - Protein Missing"

    if carbohydrate_grams is None:
        return "Incomplete - Carbohydrates Missing"

    if calories <= 0 or protein_grams <= 0:
        return "Limited"

    return "Logged - Review in Context"


def _interpret_rir(rir: float | int) -> str:
    """RIR means reps in reserve: lower RIR means higher effort."""
    rir_value = float(rir)

    if rir_value <= 1:
        return "low RIR / high effort / close to failure"

    if rir_value <= 3:
        return "moderate RIR / moderate effort"

    return "high RIR / lower effort / farther from failure"


def _classify_training_load(
    total_volume_load: float, avg_rir: float | str, workout_count: int
) -> str:
    if workout_count == 0:
        return "Inactive"

    if (isinstance(avg_rir, float) and avg_rir <= 1.5) or total_volume_load >= 20000:
        return "High"

    if total_volume_load >= 8000 or workout_count >= 3:
        return "Moderate"

    return "Low"


def _classify_recovery_demand(training_load: str, fatigue_risk: str) -> str:
    if training_load == "High" and fatigue_risk in ["High", "Moderate"]:
        return "Elevated"

    if training_load == "Moderate" and fatigue_risk == "High":
        return "Elevated"

    if training_load in ["High", "Moderate"]:
        return "Normal"

    return "Low"


def build_user_health_state(user_id: int) -> UserHealthState:
    user_profile = get_user_profile(user_id)

    if not user_profile:
        raise ValueError(f"User with id {user_id} was not found.")

    recovery_data = get_recent_recovery_metrics(user_id=user_id)
    nutrition_data = get_nutrition_analysis(user_id)
    workouts = get_recent_workouts(user_id)

    # ---------------------------------
    # Recovery State
    # ---------------------------------

    if not recovery_data:
        recovery_state = UserRecoveryState(
            avg_sleep="No data",
            avg_energy="No data",
            avg_soreness="No data",
            weight_change="No data",
            recovery_score=0,
            fatigue_risk="Unknown",
            readiness_level="Unknown",
            sleep_trend="Unknown",
            weight_trend="Unknown",
        )

    else:
        avg_sleep = recovery_data["avg_sleep"]
        avg_energy = recovery_data["avg_energy"]
        avg_soreness = recovery_data["avg_soreness"]

        # ---------------------------------
        # Recovery Score
        # ---------------------------------

        recovery_score = 100

        if avg_sleep < 5:
            recovery_score -= 30
        elif avg_sleep < 7:
            recovery_score -= 15

        if avg_energy < 4:
            recovery_score -= 25
        elif avg_energy < 7:
            recovery_score -= 10

        if avg_soreness > 7:
            recovery_score -= 25
        elif avg_soreness > 4:
            recovery_score -= 10

        recovery_score = max(recovery_score, 0)

        # ---------------------------------
        # Fatigue Risk
        # ---------------------------------

        if recovery_score < 50:
            fatigue_risk = "High"
        elif recovery_score < 75:
            fatigue_risk = "Moderate"
        else:
            fatigue_risk = "Low"

        # ---------------------------------
        # Readiness Level
        # ---------------------------------

        if recovery_score < 50:
            readiness_level = "Poor"
        elif recovery_score < 75:
            readiness_level = "Moderate"
        else:
            readiness_level = "High"

        # ---------------------------------
        # Weight Trend
        # ---------------------------------

        weight_change = recovery_data["weight_change"]

        if weight_change >= 3:
            weight_trend = "Rapid Increase"
        elif weight_change >= 1:
            weight_trend = "Increasing"
        elif weight_change <= -3:
            weight_trend = "Rapid Decrease"
        elif weight_change <= -1:
            weight_trend = "Decreasing"
        else:
            weight_trend = "Stable"

        # ---------------------------------
        # Sleep Trend
        # ---------------------------------

        if avg_sleep >= 8:
            sleep_trend = "Excellent"
        elif avg_sleep >= 7:
            sleep_trend = "Improving"
        elif avg_sleep >= 5:
            sleep_trend = "Stable"
        else:
            sleep_trend = "Declining"

        recovery_state = UserRecoveryState(
            avg_sleep=avg_sleep,
            avg_energy=avg_energy,
            avg_soreness=avg_soreness,
            weight_change=weight_change,
            recovery_score=recovery_score,
            fatigue_risk=fatigue_risk,
            readiness_level=readiness_level,
            sleep_trend=sleep_trend,
            weight_trend=weight_trend,
        )

    # ---------------------------------
    # Training Adherence
    # ---------------------------------

    workout_count = len(workouts)

    if workout_count >= 5:
        adherence_level = "High"
    elif workout_count >= 3:
        adherence_level = "Moderate"
    elif workout_count >= 1:
        adherence_level = "Low"
    else:
        adherence_level = "Inactive"

    # ---------------------------------
    # Training Trend
    # ---------------------------------

    if adherence_level == "High":
        training_trend = "Progressing"
    elif adherence_level == "Moderate":
        training_trend = "Stable"
    elif adherence_level == "Low":
        training_trend = "Inconsistent"
    else:
        training_trend = "Inactive"

    # ---------------------------------
    # Nutrition Summary
    # ---------------------------------

    if nutrition_data:
        nutrition_summary = ""

        for nutrient_name, nutrient_data in nutrition_data.items():
            nutrition_summary += (
                f"{nutrient_name}: "
                f"{nutrient_data['amount']} "
                f"{nutrient_data['unit']}\n"
            )

        nutrition_summary += (
            "\nData quality note: Missing nutrient fields are unknown, not zero. "
            "Unusually high micronutrient values may reflect database, unit, "
            "or logging issues unless confirmed by the user.\n"
        )
    else:
        nutrition_summary = "No nutrition data logged."

    calories = _get_nutrient_amount(
        nutrition_data,
        ["Energy", "Calories"],
    )
    protein_grams = _get_nutrient_amount(
        nutrition_data,
        ["Protein"],
    )
    carbohydrate_grams = _get_nutrient_amount(
        nutrition_data,
        ["Carbohydrate, by difference", "Carbohydrate", "Carbohydrates"],
    )
    fat_grams = _get_nutrient_amount(
        nutrition_data,
        ["Total lipid (fat)", "Fat", "Total fat"],
    )

    if not nutrition_data:
        protein_status = "Unknown"
        calorie_status = "Unknown"
        recovery_nutrition_status = "Unknown"
    else:
        protein_status = _classify_logged_nutrient(protein_grams)
        calorie_status = _classify_calorie_status(calories)
        recovery_nutrition_status = _classify_recovery_nutrition_status(
            protein_grams=protein_grams,
            calories=calories,
            carbohydrate_grams=carbohydrate_grams,
        )

    nutrition_state = UserNutritionState(
        nutrition_summary=nutrition_summary,
        has_nutrition_data=bool(nutrition_data),
        calories=_format_nutrition_value(calories),
        protein_grams=_format_nutrition_value(protein_grams),
        carbohydrate_grams=_format_nutrition_value(carbohydrate_grams),
        fat_grams=_format_nutrition_value(fat_grams),
        protein_status=protein_status,
        calorie_status=calorie_status,
        recovery_nutrition_status=recovery_nutrition_status,
    )

    # ---------------------------------
    # Workout Summary
    # ---------------------------------

    total_volume_load = 0.0
    rir_values = []

    if workouts:
        workout_summary = ""

        for workout in workouts:
            session = workout["session"]

            workout_summary += (
                f"\nWorkout: {session['workout_name']}\n"
                f"Date: {session['workout_date']}\n"
                f"Duration: {session['duration_minutes']} minutes\n"
            )

            for set_data in workout["sets"]:
                reps = float(set_data["reps"] or 0)
                weight = float(set_data["weight"] or 0)
                rir = set_data["rir"]

                total_volume_load += reps * weight

                if rir is not None:
                    rir_values.append(float(rir))

                workout_summary += (
                    f"- {set_data['name']} | "
                    f"{set_data['reps']} reps x "
                    f"{set_data['weight']} lbs"
                )

                if rir is not None:
                    workout_summary += f" | RIR {rir} ({_interpret_rir(rir)})"

                workout_summary += "\n"
    else:
        workout_summary = "No workout data available."

    if rir_values:
        avg_rir = round(sum(rir_values) / len(rir_values), 1)
    else:
        avg_rir = "No data"

    training_load = _classify_training_load(
        total_volume_load=total_volume_load,
        avg_rir=avg_rir,
        workout_count=workout_count,
    )
    recovery_demand = _classify_recovery_demand(
        training_load=training_load,
        fatigue_risk=recovery_state.fatigue_risk,
    )

    training_state = UserTrainingState(
        workout_summary=workout_summary,
        has_workout_data=bool(workouts),
        workout_count=workout_count,
        adherence_level=adherence_level,
        training_trend=training_trend,
        total_volume_load=round(total_volume_load, 1),
        avg_rir=avg_rir,
        training_load=training_load,
        recovery_demand=recovery_demand,
    )

    # ---------------------------------
    # System Stress Interpretation
    # ---------------------------------

    if (
        recovery_state.fatigue_risk == "High"
        and training_state.adherence_level == "High"
    ):
        system_stress_level = "Elevated"
    elif (
        recovery_state.fatigue_risk == "Moderate"
        and training_state.adherence_level in ["High", "Moderate"]
    ):
        system_stress_level = "Moderate"
    else:
        system_stress_level = "Managed"

    # ---------------------------------
    # Cross-Domain Interpretation
    # ---------------------------------

    if (
        training_state.training_load == "High"
        and nutrition_state.recovery_nutrition_status
        in [
            "Limited",
            "Incomplete - Calories Missing",
            "Incomplete - Protein Missing",
            "Incomplete - Carbohydrates Missing",
        ]
    ):
        nutrition_training_alignment = "Mismatch"
    elif training_state.training_load in [
        "Moderate",
        "High",
    ] and recovery_state.fatigue_risk in ["High", "Moderate"]:
        nutrition_training_alignment = "Needs Support"
    else:
        nutrition_training_alignment = "Aligned"

    if system_stress_level == "Elevated":
        coordinator_focus = "Prioritize recovery before increasing training stress."
    elif nutrition_training_alignment == "Mismatch":
        coordinator_focus = "Improve nutrition support for current training demand."
    elif training_state.adherence_level in ["Inactive", "Low"]:
        coordinator_focus = "Rebuild training consistency with manageable sessions."
    else:
        coordinator_focus = "Maintain current direction and progress gradually."

    # ---------------------------------
    # Unified Health State
    # ---------------------------------

    return UserHealthState(
        user_id=user_id,
        user_name=user_profile["name"],
        primary_goal=user_profile["primary_goal"],
        recovery_state=recovery_state,
        nutrition_state=nutrition_state,
        training_state=training_state,
        system_stress_level=system_stress_level,
        nutrition_training_alignment=nutrition_training_alignment,
        coordinator_focus=coordinator_focus,
    )
