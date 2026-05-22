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


def _get_nutrient_amount(nutrition_data: dict, possible_names: list[str]) -> float:
    for nutrient_name in possible_names:
        nutrient = nutrition_data.get(nutrient_name)

        if nutrient:
            return float(nutrient.get("amount", 0) or 0)

    return 0.0


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
        if protein_grams >= 120:
            protein_status = "Strong"
        elif protein_grams >= 80:
            protein_status = "Moderate"
        else:
            protein_status = "Low"

        if calories >= 2200:
            calorie_status = "Likely Sufficient"
        elif calories >= 1600:
            calorie_status = "Possibly Low"
        else:
            calorie_status = "Low"

        if protein_status == "Strong" and calorie_status == "Likely Sufficient":
            recovery_nutrition_status = "Supportive"
        elif protein_status == "Low" or calorie_status == "Low":
            recovery_nutrition_status = "Limited"
        else:
            recovery_nutrition_status = "Partial"

    nutrition_state = UserNutritionState(
        nutrition_summary=nutrition_summary,
        has_nutrition_data=bool(nutrition_data),
        calories=round(calories, 1),
        protein_grams=round(protein_grams, 1),
        carbohydrate_grams=round(carbohydrate_grams, 1),
        fat_grams=round(fat_grams, 1),
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
                    workout_summary += f" | RIR {rir}"

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
        and nutrition_state.recovery_nutrition_status in ["Limited", "Partial"]
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
