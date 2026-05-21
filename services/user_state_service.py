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


def build_user_health_state(user_id):
    user_profile = get_user_profile(user_id)
    recovery_data = get_recent_recovery_metrics()
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
            weight_change=recovery_data["weight_change"],
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

        nutrition_summary = ""

        if nutrition_data:
            for nutrient_name, nutrient_data in nutrition_data.items():
                nutrition_summary += (
                    f"{nutrient_name}: "
                    f"{nutrient_data['amount']} "
                    f"{nutrient_data['unit']}\n"
                )

        else:
            nutrition_summary = "No nutrition data logged."

        nutrition_state = UserNutritionState(
            nutrition_summary=nutrition_summary,
            has_nutrition_data=bool(nutrition_data),
        )

        # ---------------------------------
        # Workout Summary
        # ---------------------------------

        workout_summary = ""

        if workouts:
            for workout in workouts:
                session = workout["session"]

                workout_summary += (
                    f"\nWorkout: {session['workout_name']}\n"
                    f"Date: {session['workout_date']}\n"
                    f"Duration: {session['duration_minutes']} minutes\n"
                )

                for set_data in workout["sets"]:
                    workout_summary += (
                        f"- {set_data['name']} | "
                        f"{set_data['reps']} reps x "
                        f"{set_data['weight']} lbs"
                    )

                    if set_data["rir"] is not None:
                        workout_summary += f" | RIR {set_data['rir']}"

                    workout_summary += "\n"

        else:
            workout_summary = "No workout data available."

        training_state = UserTrainingState(
            workout_summary=workout_summary,
            has_workout_data=bool(workouts),
            workout_count=workout_count,
            adherence_level=adherence_level,
            training_trend=training_trend,
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
            and training_state.adherence_level
            in [
                "High",
                "Moderate",
            ]
        ):
            system_stress_level = "Moderate"

        else:
            system_stress_level = "Managed"

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
        )
