import database
from models.coordinator_models import UnifiedHealthReport
from models.user_state_models import (
    UserHealthState,
    UserNutritionState,
    UserRecoveryState,
    UserTrainingState,
)
from scripts.seed_qa_scenarios import QA_USER_IDS, seed_qa_scenarios
from services.coaching_decision_service import build_coaching_decision
from services.coordinator_service import (
    build_final_report_from_coordinator_output,
    render_unified_health_report,
    validate_report_language,
)
from services.user_state_service import build_user_health_state


def _health_state(
    *,
    fatigue_risk="Low",
    readiness_level="High",
    avg_sleep=7.8,
    avg_soreness=2.0,
    calories=2200.0,
    calorie_status="Logged - Moderate Intake",
    protein_status="Logged",
    carbs=240.0,
    fat=70.0,
    nutrition_status="Logged - Review in Context",
    nutrition_summary="Calories: 2200 kcal\nProtein: 140 g\n",
    avg_rir=2.0,
    training_load="Moderate",
    nutrition_alignment="Aligned",
    system_stress="Managed",
    coordinator_focus="Maintain current direction and progress gradually.",
):
    return UserHealthState(
        user_id=1,
        user_name="QA User",
        primary_goal="strength_progression",
        recovery_state=UserRecoveryState(
            avg_sleep=avg_sleep,
            avg_energy=8.0,
            avg_soreness=avg_soreness,
            weight_change=0.2,
            recovery_score=100 if fatigue_risk == "Low" else 45,
            fatigue_risk=fatigue_risk,
            readiness_level=readiness_level,
            sleep_trend="Improving",
            weight_trend="Stable",
        ),
        nutrition_state=UserNutritionState(
            nutrition_summary=nutrition_summary,
            has_nutrition_data=True,
            calories=calories,
            protein_grams=140.0,
            carbohydrate_grams=carbs,
            fat_grams=fat,
            protein_status=protein_status,
            calorie_status=calorie_status,
            recovery_nutrition_status=nutrition_status,
        ),
        training_state=UserTrainingState(
            workout_summary="QA workout",
            has_workout_data=True,
            workout_count=4,
            adherence_level="Moderate",
            training_trend="Progressing",
            total_volume_load=12000.0,
            avg_rir=avg_rir,
            training_load=training_load,
            recovery_demand="Normal",
        ),
        system_stress_level=system_stress,
        nutrition_training_alignment=nutrition_alignment,
        coordinator_focus=coordinator_focus,
        starting_weight=180.0,
        latest_body_weight=181.0,
        goal_weight=180.0,
        activity_level="moderate",
    )


def _render_fallback(health_state):
    decision = build_coaching_decision(health_state)
    report = build_final_report_from_coordinator_output(
        raw_text="not structured enough to parse",
        health_state=health_state,
        coaching_decision=decision,
    )
    return decision, render_unified_health_report(report, health_state=health_state)


def test_seeded_users_classify_into_expected_scenarios(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    expected = {
        101: "recovery_limited",
        102: "aligned_managed",
        103: "nutrition_training_mismatch",
        104: "improving_after_deload",
        105: "data_quality_limited",
    }

    assert set(expected) == set(QA_USER_IDS)
    for user_id, scenario in expected.items():
        health_state = build_user_health_state(user_id)
        decision = build_coaching_decision(health_state)
        assert decision.scenario == scenario


def test_aligned_managed_report_avoids_unnecessary_intervention_language():
    health_state = _health_state()
    decision, rendered = _render_fallback(health_state)

    assert decision.scenario == "aligned_managed"
    assert "Maintain consistency" in rendered or "maintaining consistency" in rendered
    assert "deload" not in rendered.lower()
    assert "recovery mismatch" not in rendered.lower()
    assert "insufficient calor" not in rendered.lower()
    assert validate_report_language(rendered, health_state, decision) == []


def test_recovery_limited_report_includes_recovery_priority_and_rir_guidance():
    health_state = _health_state(
        fatigue_risk="High",
        readiness_level="Poor",
        avg_sleep=5.3,
        avg_soreness=7.0,
        avg_rir=1.0,
        training_load="High",
        nutrition_alignment="Needs Support",
        system_stress="Elevated",
    )
    decision, rendered = _render_fallback(health_state)

    assert decision.scenario == "recovery_limited"
    assert "recovery" in rendered.lower()
    assert "RIR 2-3" in rendered
    assert "RIR 0-1" in rendered
    assert validate_report_language(rendered, health_state, decision) == []


def test_nutrition_training_mismatch_does_not_treat_missing_nutrition_as_zero():
    health_state = _health_state(
        calories="Unknown",
        calorie_status="Unknown",
        carbs="Unknown",
        fat="Unknown",
        nutrition_status="Incomplete - Calories Missing",
        nutrition_alignment="Mismatch",
        training_load="High",
        avg_rir=2.0,
    )
    decision, rendered = _render_fallback(health_state)

    assert decision.scenario == "nutrition_training_mismatch"
    assert "Nutrition logging is incomplete" in rendered
    assert "0 kcal" not in rendered
    assert "0 g protein" not in rendered
    assert validate_report_language(rendered, health_state, decision) == []


def test_data_quality_limited_uses_logging_verification_without_supplement_assumptions():
    health_state = _health_state(
        calories="Unknown",
        calorie_status="Unknown",
        carbs="Unknown",
        fat="Unknown",
        nutrition_status="Incomplete - Calories Missing",
        nutrition_summary=(
            "Unusually high micronutrient values detected; these may reflect "
            "database, unit, or logging issues."
        ),
        nutrition_alignment="Aligned",
    )
    decision, rendered = _render_fallback(health_state)

    assert decision.scenario == "data_quality_limited"
    assert "Data quality limits confidence" in rendered
    assert "verify" in rendered.lower()
    assert "supplementation artifacts" not in rendered
    assert "likely from supplements" not in rendered
    assert validate_report_language(rendered, health_state, decision) == []


def test_validate_report_language_rejects_aligned_managed_over_intervention():
    decision = build_coaching_decision(_health_state())
    report = render_unified_health_report(
        UnifiedHealthReport(
            overall_score=85,
            biggest_issue="The user needs a deload due to recovery mismatch.",
            likely_cause="Training is outpacing confirmed recovery support.",
            priority_action="Reduce intensity.",
            recommendation="Address insufficient caloric intake.",
        )
    )

    violations = validate_report_language(report, coaching_decision=decision)
    assert any("Aligned/managed" in violation for violation in violations)


def _data_quality_limited_health_state():
    return _health_state(
        calories="Unknown",
        calorie_status="Unknown",
        carbs="Unknown",
        fat="Unknown",
        nutrition_status="Incomplete - Calories Missing",
        nutrition_summary=(
            "Unusually high micronutrient values detected; these may reflect "
            "database, unit, or logging issues."
        ),
        nutrition_alignment="Aligned",
        fatigue_risk="Low",
        readiness_level="High",
        avg_sleep=6.5,
        avg_soreness=3.0,
        avg_rir=2.5,
        training_load="Moderate",
    )


def test_data_quality_limited_validator_rejects_overconfident_causal_claims():
    health_state = _data_quality_limited_health_state()
    decision = build_coaching_decision(health_state)
    bad_report = render_unified_health_report(
        UnifiedHealthReport(
            overall_score=60,
            biggest_issue=(
                "Incomplete nutrition data and unusually high micronutrient values "
                "compromise recovery and fat-loss progress."
            ),
            likely_cause=(
                "Suboptimal sleep and inconsistent RIR management likely contribute "
                "to overtraining and stalled weight loss."
            ),
            priority_action="Address insufficient caloric intake.",
            recommendation="Resolve the caloric deficit before training hard again.",
        ),
        health_state=health_state,
        coaching_decision=decision,
    )

    violations = validate_report_language(
        bad_report,
        health_state=health_state,
        coaching_decision=decision,
    )

    assert decision.scenario == "data_quality_limited"
    assert any("overtraining" in violation for violation in violations)
    assert any("stalled" in violation for violation in violations)
    assert any(
        "compromised" in violation or "compromise" in violation
        for violation in violations
    )
    assert any("intake adequacy" in violation for violation in violations)
    assert any("caloric deficit" in violation for violation in violations)


def test_bad_data_quality_limited_coordinator_output_falls_back_to_deterministic_report():
    health_state = _data_quality_limited_health_state()
    decision = build_coaching_decision(health_state)
    raw_text = """
    overall_score: 60
    biggest_issue: Incomplete nutrition data and unusually high micronutrient values compromise recovery and fat-loss progress.
    likely_cause: Suboptimal sleep and inconsistent RIR management likely contribute to overtraining and stalled weight loss.
    priority_action: Address insufficient caloric intake.
    recommendation: Fix the caloric deficit before training hard again.
    """

    structured_report = build_final_report_from_coordinator_output(
        raw_text=raw_text,
        health_state=health_state,
        coaching_decision=decision,
    )
    rendered = render_unified_health_report(
        structured_report,
        health_state=health_state,
        coaching_decision=decision,
    )
    rendered_lower = rendered.lower()

    assert decision.scenario == "data_quality_limited"
    assert "Data quality limits confidence" in rendered
    assert "Nutrition Target Display" in rendered
    assert "Nutrition targets are limited until logging is more complete" in rendered
    assert "overtraining" not in rendered_lower
    assert "stalled weight loss" not in rendered_lower
    assert "stalled fat loss" not in rendered_lower
    assert "compromise recovery" not in rendered_lower
    assert "caloric deficit" not in rendered_lower
    assert validate_report_language(rendered, health_state, decision) == []


def test_seeded_user_105_final_report_uses_limited_confidence_language(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    health_state = build_user_health_state(105)
    decision = build_coaching_decision(health_state)

    report = build_final_report_from_coordinator_output(
        raw_text="not structured enough to parse",
        health_state=health_state,
        coaching_decision=decision,
    )
    rendered = render_unified_health_report(
        report,
        health_state=health_state,
        coaching_decision=decision,
    )
    rendered_lower = rendered.lower()

    assert decision.scenario == "data_quality_limited"
    assert "Grounded Recommendation" in rendered
    assert "Nutrition Target Display" in rendered
    assert "Nutrition targets are limited until logging is more complete" in rendered
    assert "overtraining" not in rendered_lower
    assert "stalled weight loss" not in rendered_lower
    assert "stalled fat loss" not in rendered_lower
    assert "likely contribute" not in rendered_lower
    assert "hard calorie" not in rendered_lower
    assert validate_report_language(rendered, health_state, decision) == []


def test_seeded_full_reports_include_grounded_recommendation_section(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    for user_id in QA_USER_IDS:
        health_state = build_user_health_state(user_id)
        decision = build_coaching_decision(health_state)
        report = build_final_report_from_coordinator_output(
            raw_text="not structured enough to parse",
            health_state=health_state,
            coaching_decision=decision,
        )
        rendered = render_unified_health_report(
            report,
            health_state=health_state,
            coaching_decision=decision,
        )

        assert "Grounded Recommendation" in rendered
        assert "Daily Coaching Recommendation" in rendered
        assert "Workout Recommendation" in rendered
        assert "Nutrition Action" in rendered
        assert "Nutrition Target Display" in rendered
        assert validate_report_language(rendered, health_state, decision) == []
