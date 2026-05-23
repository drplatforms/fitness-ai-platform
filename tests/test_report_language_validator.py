from models.coordinator_models import UnifiedHealthReport
from models.user_state_models import (
    UserHealthState,
    UserNutritionState,
    UserRecoveryState,
    UserTrainingState,
)
from services.coordinator_service import (
    build_final_report_from_coordinator_output,
    render_unified_health_report,
    validate_report_language,
)


def _health_state():
    return UserHealthState(
        user_id=1,
        user_name="QA User",
        primary_goal="fat_loss",
        recovery_state=UserRecoveryState(
            avg_sleep=5.3,
            avg_energy=4.0,
            avg_soreness=7.0,
            weight_change=1.5,
            recovery_score=45,
            fatigue_risk="High",
            readiness_level="Low",
            sleep_trend="Poor",
            weight_trend="Increasing",
        ),
        nutrition_state=UserNutritionState(
            nutrition_summary=(
                "Unusually high micronutrient values detected; these may reflect "
                "database, unit, or logging issues."
            ),
            has_nutrition_data=True,
            calories="Unknown",
            protein_grams=110.0,
            carbohydrate_grams="Unknown",
            fat_grams="Unknown",
            protein_status="Logged",
            calorie_status="Unknown",
            recovery_nutrition_status="Incomplete - Calories Missing",
        ),
        training_state=UserTrainingState(
            workout_summary="Clean and Jerk: RIR 1 (low RIR / high effort / close to failure)",
            has_workout_data=True,
            workout_count=1,
            adherence_level="Low",
            training_trend="Recent training logged",
            total_volume_load=9800.0,
            avg_rir=1.0,
            training_load="High",
            recovery_demand="High",
        ),
        system_stress_level="High",
        nutrition_training_alignment="Mismatch",
        coordinator_focus="Improve nutrition support for current training demand.",
    )


def test_report_language_validator_flags_known_bad_phrases():
    bad_report = """
    high-RIR (0-1) work creates risk.
    Lower RIR to 2-3.
    Sleep deprivation (5.3/10).
    Elevated magnesium likely from supplements.
    Eat 20-40g carbs.
    """

    violations = validate_report_language(bad_report)

    assert len(violations) >= 5


def test_rendered_unified_report_passes_language_validator():
    report = UnifiedHealthReport(
        overall_score=55,
        biggest_issue="Recovery is limited by approximately 5.3 hours/night.",
        likely_cause="Training demand is outpacing confirmed recovery support.",
        priority_action=(
            "Move from RIR 0-1 toward RIR 2-3 temporarily to reduce effort "
            "and leave more reps in reserve."
        ),
        recommendation=(
            "Verify nutrition logging and evaluate carbohydrate intake relative "
            "to training load, recovery, body weight, and goals."
        ),
    )

    rendered = render_unified_health_report(report, timestamp="2026-05-22 05:00:00 PM")

    assert validate_report_language(rendered) == []


def test_bad_coordinator_output_falls_back_to_deterministic_report():
    raw_text = """
    overall_score: 55
    biggest_issue: overtraining risk from high-RIR (0-1) lifts
    likely_cause: magnesium likely from supplements
    priority_action: lower RIR to 2-3
    recommendation: eat 20-40g carbs
    """

    structured_report = build_final_report_from_coordinator_output(
        raw_text=raw_text,
        health_state=_health_state(),
    )
    rendered = render_unified_health_report(structured_report)

    assert "low-RIR/high-effort work at RIR 0-1" in rendered
    assert "move from RIR 0-1 toward RIR 2-3" in rendered
    assert "approximately 5.3 hours/night" in rendered
    assert (
        "may reflect logging, database, unit, or supplementation artifacts" in rendered
    )
    assert validate_report_language(rendered) == []


def test_report_language_validator_flags_new_qa_regressions():
    bad_report = """
    Severe caloric deficit and micronutrient imbalances threaten recovery.
    Over-supplementation likely drive extreme micronutrient values.
    Prioritize 300-400 kcal/day for recovery.
    Use carbs 4-6 g/kg relative to training load.
    """

    violations = validate_report_language(bad_report)

    assert len(violations) >= 4


def test_context_aware_validator_rejects_numeric_targets_when_calories_unknown():
    bad_report = """
    The user has inadequate energy availability.
    Prioritize 300-400 kcal/day for recovery.
    Use carbohydrates 4-6 g/kg relative to training load.
    """

    violations = validate_report_language(
        bad_report,
        health_state=_health_state(),
    )

    assert any(
        "inadequate energy availability" in violation for violation in violations
    )
    assert any("numeric calorie prescriptions" in violation for violation in violations)
    assert any(
        "gram-per-kilogram macro prescriptions" in violation for violation in violations
    )
