from __future__ import annotations

from models.daily_next_action_models import (
    DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN,
    DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
    DAILY_NEXT_ACTION_LOG_FOOD,
    DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS,
    DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE,
    DAILY_NEXT_ACTION_REVIEW_WORKOUT,
    DailyNextAction,
)
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    TARGET_STATUS_NEAR,
    NutritionActuals,
    NutritionLoggingSummary,
    NutritionTargetComparison,
    TargetVsActualNutritionSummary,
)
from models.user_state_models import (
    UserHealthState,
    UserNutritionState,
    UserRecoveryState,
    UserTrainingState,
)
from services.daily_next_action_service import (
    build_daily_next_action_from_components,
    validate_daily_next_action,
)


def _health_state(
    *,
    user_id: int = 999,
    readiness_level: str = "High",
    fatigue_risk: str = "Low",
    recovery_score: int = 92,
    coordinator_focus: str = "aligned_managed",
) -> UserHealthState:
    return UserHealthState(
        user_id=user_id,
        user_name="QA User",
        primary_goal="strength_and_recomposition",
        recovery_state=UserRecoveryState(
            avg_sleep=7.5 if readiness_level != "Unknown" else "Unknown",
            avg_energy=8.0 if readiness_level != "Unknown" else "Unknown",
            avg_soreness=2.0 if readiness_level != "Unknown" else "Unknown",
            weight_change=0.0 if readiness_level != "Unknown" else "Unknown",
            recovery_score=recovery_score,
            fatigue_risk=fatigue_risk,
            readiness_level=readiness_level,
            sleep_trend="Stable",
            weight_trend="Stable",
        ),
        nutrition_state=UserNutritionState(
            nutrition_summary="Nutrition data is available.",
            has_nutrition_data=True,
            calories=2200.0,
            protein_grams=160.0,
            carbohydrate_grams=220.0,
            fat_grams=70.0,
            protein_status="Logged",
            calorie_status="Logged - Moderate Intake",
            recovery_nutrition_status="Logged - Review in Context",
        ),
        training_state=UserTrainingState(
            workout_summary="Workout context is available.",
            has_workout_data=True,
            workout_count=3,
            adherence_level="Moderate",
            training_trend="Stable",
            total_volume_load=12000.0,
            avg_rir=2.0,
            training_load="Moderate",
            recovery_demand="Normal",
        ),
        system_stress_level="Managed",
        nutrition_training_alignment="Aligned",
        coordinator_focus=coordinator_focus,
        latest_body_weight=190.0,
        activity_level="moderate",
    )


def _nutrition_summary(
    *,
    completeness: str = LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    confidence: str = "High",
) -> TargetVsActualNutritionSummary:
    actuals = NutritionActuals(
        user_id=999,
        logging_date="2026-06-18",
        logging_window="calendar_day",
        logged_calories=2200.0,
        logged_protein=160.0,
        logged_carbs=220.0,
        logged_fat=70.0,
        logged_meal_count=3,
        entry_count=3,
        source_count=3,
        reason_codes=["unit_test_actuals"],
    )
    logging_summary = NutritionLoggingSummary(
        user_id=999,
        logging_date="2026-06-18",
        logging_completeness=completeness,
        confidence=confidence,
        logged_meal_count=3 if completeness != LOGGING_COMPLETENESS_NO_LOGS else 0,
        entry_count=3 if completeness != LOGGING_COMPLETENESS_NO_LOGS else 0,
        reason_codes=[completeness],
    )
    comparison = NutritionTargetComparison(
        nutrient="protein",
        actual=160.0,
        target_min=140.0,
        target_max=180.0,
        delta_min=20.0,
        delta_max=-20.0,
        percent_of_target=100.0,
        target_status=TARGET_STATUS_NEAR,
        comparison_available=True,
        confidence=confidence,
        reason_codes=["unit_test_comparison"],
    )
    return TargetVsActualNutritionSummary(
        user_id=999,
        date="2026-06-18",
        nutrition_actuals=actuals,
        logging_summary=logging_summary,
        comparisons={
            "calories": comparison,
            "protein": comparison,
            "carbs": comparison,
            "fat": comparison,
        },
        logging_completeness=completeness,
        confidence=confidence,
        reason_codes=["unit_test_summary"],
    )


def _select(
    *,
    health_state: UserHealthState | None = None,
    scenario: str = "aligned_managed",
    nutrition_summary: TargetVsActualNutritionSummary | None = None,
    workout_available: bool = False,
    report_guidance_available: bool = False,
):
    return build_daily_next_action_from_components(
        health_state=health_state or _health_state(coordinator_focus=scenario),
        scenario=scenario,
        nutrition_summary=nutrition_summary,
        workout_available=workout_available,
        report_guidance_available=report_guidance_available,
        action_date="2026-06-18",
    )


def test_recovery_limited_action_wins_over_nutrition_workout_and_report():
    action = _select(
        health_state=_health_state(
            readiness_level="Poor",
            fatigue_risk="High",
            recovery_score=35,
            coordinator_focus="recovery_limited",
        ),
        scenario="recovery_limited",
        nutrition_summary=_nutrition_summary(),
        workout_available=True,
        report_guidance_available=True,
    )

    assert action.action_id == DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE
    assert action.priority == 1
    assert action.workflow_target == "today_recovery_aware_workout"
    assert validate_daily_next_action(action) == []


def test_missing_recovery_checkin_wins_when_required():
    action = _select(
        health_state=_health_state(
            readiness_level="Unknown",
            fatigue_risk="Unknown",
            recovery_score=0,
            coordinator_focus="data_quality_limited",
        ),
        scenario="data_quality_limited",
        nutrition_summary=_nutrition_summary(completeness=LOGGING_COMPLETENESS_NO_LOGS),
        workout_available=True,
        report_guidance_available=True,
    )

    assert action.action_id == DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN
    assert action.priority == 2
    assert action.workflow_target == "today_recovery_checkin"


def test_nutrition_logging_action_appears_when_intake_is_incomplete():
    for completeness in [
        LOGGING_COMPLETENESS_NO_LOGS,
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    ]:
        action = _select(
            nutrition_summary=_nutrition_summary(
                completeness=completeness,
                confidence="Low",
            ),
            workout_available=True,
            report_guidance_available=True,
        )

        assert action.action_id == DAILY_NEXT_ACTION_LOG_FOOD
        assert action.priority == 3
        assert action.workflow_target == "nutrition_quick_log"


def test_workout_action_appears_when_inputs_support_training():
    action = _select(
        nutrition_summary=_nutrition_summary(),
        workout_available=True,
        report_guidance_available=True,
    )

    assert action.action_id == DAILY_NEXT_ACTION_REVIEW_WORKOUT
    assert action.priority == 4
    assert action.workflow_target == "workout_preview"


def test_report_review_action_requires_enough_backend_data_and_no_workout():
    action = _select(
        nutrition_summary=_nutrition_summary(
            completeness=LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
            confidence="High",
        ),
        workout_available=False,
        report_guidance_available=True,
    )

    assert action.action_id == DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE
    assert action.priority == 5
    assert action.workflow_target == "reports_guidance"


def test_data_quality_limitation_returns_nutrition_progress_action():
    action = _select(
        scenario="data_quality_limited",
        nutrition_summary=_nutrition_summary(
            completeness=LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
            confidence="Low",
        ),
        workout_available=False,
        report_guidance_available=False,
    )

    assert action.action_id == DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS
    assert action.priority == 6
    assert action.workflow_target == "nutrition_target_vs_actual"


def test_service_returns_exactly_one_primary_action_object():
    action = _select(nutrition_summary=_nutrition_summary(), workout_available=True)

    assert isinstance(action.action_id, str)
    assert isinstance(action, DailyNextAction)
    assert action.is_available is True
    assert action.blocked_reason is None
    assert validate_daily_next_action(action) == []


def test_action_contract_rejects_raw_debug_provider_metadata():
    action = DailyNextAction(
        action_id=DAILY_NEXT_ACTION_LOG_FOOD,
        title="Log a meal or snack",
        summary="Add today's food intake so nutrition guidance has enough data.",
        reason="Today's nutrition state is limited until more food data is logged.",
        priority=3,
        workflow_target="nutrition_quick_log",
        severity="info",
        evidence={"raw_provider_output": "not allowed"},
    )

    assert validate_daily_next_action(action) == [
        "DailyNextAction.evidence exposes internal/debug keys."
    ]


def test_seeded_daily_next_action_api_returns_expected_action_classes(
    tmp_path, monkeypatch
):
    from fastapi.testclient import TestClient

    import database
    from api.main import app
    from scripts.seed_qa_scenarios import seed_qa_scenarios

    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    client = TestClient(app)
    expected_action_ids = {
        101: {DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE},
        102: {
            DAILY_NEXT_ACTION_REVIEW_WORKOUT,
            DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE,
            DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS,
        },
        105: {
            DAILY_NEXT_ACTION_LOG_FOOD,
            DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN,
        },
    }

    for user_id, acceptable_action_ids in expected_action_ids.items():
        response = client.get(f"/daily-coach/{user_id}/next-action")
        assert response.status_code == 200
        payload = response.json()
        action = payload["daily_next_action"]

        assert payload["success"] is True
        assert action["action_id"] in acceptable_action_ids
        assert action["title"]
        assert action["reason"]
        assert "raw_provider_output" not in action["evidence"]
        assert "validation_error_categories" not in action["evidence"]
