from models.coaching_decision_models import CoachingDecision
from models.user_state_models import UserHealthState


def _has_incomplete_nutrition(health_state: UserHealthState) -> bool:
    nutrition_state = health_state.nutrition_state
    nutrition_summary = nutrition_state.nutrition_summary.lower()
    recovery_nutrition_status = nutrition_state.recovery_nutrition_status.lower()

    return (
        nutrition_state.calories == "Unknown"
        or nutrition_state.calorie_status == "Unknown"
        or nutrition_state.protein_status == "Unknown"
        or nutrition_state.carbohydrate_grams == "Unknown"
        or nutrition_state.fat_grams == "Unknown"
        or "incomplete" in recovery_nutrition_status
        or "missing" in recovery_nutrition_status
        or "unknown" in nutrition_summary
        or "unavailable" in nutrition_summary
    )


def _has_unusual_micronutrients(health_state: UserHealthState) -> bool:
    nutrition_summary = health_state.nutrition_state.nutrition_summary.lower()

    if "unusually high micronutrient values detected" in nutrition_summary:
        return True

    suspicious_markers = ["25000", "9000", "9999", "450"]
    return any(marker in nutrition_summary for marker in suspicious_markers)


def _has_low_rir_training(health_state: UserHealthState) -> bool:
    avg_rir = health_state.training_state.avg_rir
    return isinstance(avg_rir, int | float) and avg_rir <= 1.5


def _recent_notes_text(health_state: UserHealthState) -> str:
    recovery_summary = " ".join(
        str(value)
        for value in [
            health_state.recovery_state.sleep_trend,
            health_state.recovery_state.weight_trend,
            health_state.coordinator_focus,
        ]
    )
    return recovery_summary.lower()


def build_coaching_decision(health_state: UserHealthState) -> CoachingDecision:
    """Turn interpreted health state into an approved coaching strategy.

    UserState stays factual. This layer decides the coaching scenario and gives
    the report generator a deterministic strategy contract to follow.
    """
    reason_codes: list[str] = []

    incomplete_nutrition = _has_incomplete_nutrition(health_state)
    unusual_micronutrients = _has_unusual_micronutrients(health_state)
    low_rir_training = _has_low_rir_training(health_state)
    high_training_load = health_state.training_state.training_load == "High"
    recovery_limited = (
        health_state.recovery_state.fatigue_risk == "High"
        or health_state.recovery_state.readiness_level == "Poor"
    )
    nutrition_mismatch = health_state.nutrition_training_alignment == "Mismatch"

    if incomplete_nutrition:
        reason_codes.append("incomplete_nutrition")
    if recovery_limited:
        reason_codes.append("recovery_limited")
    if recovery_limited:
        rir_action = (
            "For 1-2 weeks, keep most working sets around RIR 2-3 instead of RIR 0-1."
            if low_rir_training or high_training_load
            else "Avoid increasing training stress until recovery markers improve."
        )
        return CoachingDecision(
            scenario="recovery_limited",
            primary_focus="Prioritize recovery before adding more training stress.",
            training_action=rir_action,
            nutrition_action=(
                "Evaluate nutrition support against training demand and recovery status "
                "without assuming missing intake is zero."
            ),
            sleep_action="Increase sleep duration by about 1-2 hours/night if possible.",
            monitoring_action=(
                "Monitor sleep duration, energy, soreness, training effort, and body-weight trend."
            ),
            confidence="High",
            reason_codes=reason_codes,
        )

    if unusual_micronutrients:
        reason_codes.append("unusual_micronutrients")
    if low_rir_training:
        reason_codes.append("low_rir_high_effort_training")
    if high_training_load:
        reason_codes.append("high_training_load")
    if nutrition_mismatch:
        reason_codes.append("nutrition_training_mismatch")

    if unusual_micronutrients:
        return CoachingDecision(
            scenario="data_quality_limited",
            primary_focus=(
                "Improve logging completeness and verify unusual nutrition entries "
                "before making stronger coaching conclusions."
            ),
            training_action=(
                "Avoid major training changes from this report alone unless recovery "
                "or performance markers worsen."
            ),
            nutrition_action=(
                "Verify food entries and nutrient data quality; treat missing fields "
                "as unknown rather than zero intake."
            ),
            sleep_action=(
                "Keep sleep logging consistent so recovery trend confidence improves."
            ),
            monitoring_action=(
                "Monitor data completeness, unusual nutrient values, recovery check-ins, "
                "and workout logging quality."
            ),
            confidence="Low",
            reason_codes=reason_codes,
        )

    if nutrition_mismatch:
        return CoachingDecision(
            scenario="nutrition_training_mismatch",
            primary_focus="Improve nutrition support for current training demand.",
            training_action=(
                "Keep training progression controlled while nutrition support is clarified."
            ),
            nutrition_action=(
                "Improve logging consistency and evaluate protein and carbohydrate support "
                "relative to body weight, goal, activity level, training load, and recovery status."
            ),
            sleep_action="Maintain sleep consistency while nutrition support is reviewed.",
            monitoring_action=(
                "Monitor workout performance, soreness, energy, and nutrition logging completeness."
            ),
            confidence="Moderate",
            reason_codes=reason_codes,
        )

    notes_text = _recent_notes_text(health_state)
    workout_text = health_state.training_state.workout_summary.lower()
    if "deload" in notes_text or "deload" in workout_text:
        return CoachingDecision(
            scenario="improving_after_deload",
            primary_focus="Continue controlled progression while preserving the improving recovery trend.",
            training_action="Progress gradually and avoid quickly returning to frequent RIR 0-1 work.",
            nutrition_action="Keep nutrition logging consistent and review support against training demand.",
            sleep_action="Maintain the improved sleep pattern.",
            monitoring_action="Monitor whether energy, soreness, sleep, and performance continue improving.",
            confidence="Moderate",
            reason_codes=reason_codes + ["improving_recovery_trend"],
        )

    return CoachingDecision(
        scenario="aligned_managed",
        primary_focus="Maintain consistency and progress gradually.",
        training_action="Continue gradual progression without unnecessary restriction language.",
        nutrition_action="Keep nutrition logging consistent and review support against training demand.",
        sleep_action="Maintain current sleep consistency.",
        monitoring_action="Monitor sleep, energy, soreness, body weight trend, and training performance.",
        confidence="High",
        reason_codes=reason_codes + ["aligned_managed"],
    )
