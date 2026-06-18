import pytest

from models.nutrition_trend_models import (
    BODYWEIGHT_TREND_STABLE,
    BODYWEIGHT_TREND_UNAVAILABLE,
    CALIBRATION_READINESS_EARLY_SIGNAL,
    CALIBRATION_READINESS_NOT_READY,
    CALIBRATION_READINESS_STRONG,
    CALIBRATION_READINESS_USABLE,
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_CONSISTENCY_INSUFFICIENT,
    LOGGING_CONSISTENCY_STRONG,
    LOGGING_CONSISTENCY_USABLE,
    BodyweightTrendSummary,
    NutritionCalibrationReadiness,
    NutritionIntakeTrendSummary,
    NutritionTrendDay,
    NutritionTrendWindow,
    NutritionTrendWindowMetadata,
)


def _unavailable_bodyweight() -> BodyweightTrendSummary:
    return BodyweightTrendSummary(
        trend_direction=BODYWEIGHT_TREND_UNAVAILABLE,
        confidence="Limited",
        reason_codes=["bodyweight_trend_unavailable"],
        limitations=["Bodyweight trend data is not available."],
    )


def _not_ready_readiness() -> NutritionCalibrationReadiness:
    return NutritionCalibrationReadiness(
        calibration_allowed=False,
        readiness_level=CALIBRATION_READINESS_NOT_READY,
        minimum_window_met=False,
        preferred_window_met=False,
        logging_quality_met=False,
        bodyweight_trend_available=False,
        goal_context_available=False,
        training_context_available=False,
        reason_codes=["calibration_not_ready"],
        limitations=["More deterministic trend data is needed."],
    )


def _limited_intake_summary() -> NutritionIntakeTrendSummary:
    return NutritionIntakeTrendSummary(
        logging_consistency_status=LOGGING_CONSISTENCY_INSUFFICIENT,
        confidence="Limited",
        reason_codes=["logging_quality_insufficient"],
        limitations=["Logging consistency is not sufficient for calibration."],
    )


def test_trend_window_can_represent_insufficient_data() -> None:
    window = NutritionTrendWindow(
        user_id=1,
        start_date="2026-06-01",
        end_date="2026-06-07",
        window_days=7,
        logged_day_count=2,
        complete_logging_day_count=0,
        partial_logging_day_count=2,
        no_log_day_count=5,
        intake_trend_summary=_limited_intake_summary(),
        bodyweight_trend_summary=_unavailable_bodyweight(),
        calibration_readiness=_not_ready_readiness(),
        confidence="Limited",
        reason_codes=["minimum_window_not_met"],
        limitations=["A longer trend window is required."],
    )

    assert window.calibration_readiness.calibration_allowed is False
    assert window.no_log_day_count == 5
    assert window.confidence == "Limited"


def test_trend_window_can_represent_14_day_early_context() -> None:
    window = NutritionTrendWindow(
        user_id=1,
        start_date="2026-06-01",
        end_date="2026-06-14",
        window_days=14,
        logged_day_count=10,
        complete_logging_day_count=7,
        partial_logging_day_count=3,
        no_log_day_count=4,
        intake_trend_summary=NutritionIntakeTrendSummary(
            average_calories=2150,
            average_protein_g=145,
            average_carbohydrate_g=220,
            average_fat_g=70,
            calorie_target_hit_rate=0.6,
            protein_target_hit_rate=0.7,
            complete_logging_rate=0.5,
            logging_consistency_status=LOGGING_CONSISTENCY_USABLE,
            confidence="Low",
        ),
        bodyweight_trend_summary=BodyweightTrendSummary(
            weigh_in_count=4,
            start_weight_lb=210,
            end_weight_lb=209,
            average_weight_lb=209.5,
            trend_direction=BODYWEIGHT_TREND_STABLE,
            weekly_rate_lb=-0.5,
            confidence="Low",
        ),
        calibration_readiness=NutritionCalibrationReadiness(
            calibration_allowed=False,
            readiness_level=CALIBRATION_READINESS_EARLY_SIGNAL,
            minimum_window_met=True,
            preferred_window_met=False,
            logging_quality_met=True,
            bodyweight_trend_available=True,
            goal_context_available=True,
            training_context_available=True,
            reason_codes=["calibration_early_signal"],
            limitations=["Four weeks are preferred before narrowing target ranges."],
        ),
        confidence="Low",
        reason_codes=["minimum_window_met"],
        limitations=["Trend evidence is early and should not mutate targets."],
    )

    assert window.window_days == 14
    assert window.calibration_readiness.minimum_window_met is True
    assert window.calibration_readiness.preferred_window_met is False


def test_trend_window_can_represent_28_day_preferred_context() -> None:
    window = NutritionTrendWindow(
        user_id=1,
        start_date="2026-06-01",
        end_date="2026-06-28",
        window_days=28,
        logged_day_count=26,
        complete_logging_day_count=24,
        partial_logging_day_count=2,
        no_log_day_count=2,
        intake_trend_summary=NutritionIntakeTrendSummary(
            average_calories=2300,
            average_protein_g=170,
            average_carbohydrate_g=250,
            average_fat_g=78,
            calorie_target_hit_rate=0.75,
            protein_target_hit_rate=0.85,
            complete_logging_rate=24 / 28,
            logging_consistency_status=LOGGING_CONSISTENCY_STRONG,
            confidence="High",
        ),
        bodyweight_trend_summary=BodyweightTrendSummary(
            weigh_in_count=12,
            start_weight_lb=210,
            end_weight_lb=208,
            average_weight_lb=209,
            trend_direction="decreasing",
            weekly_rate_lb=-0.5,
            confidence="Moderate",
        ),
        calibration_readiness=NutritionCalibrationReadiness(
            calibration_allowed=True,
            readiness_level=CALIBRATION_READINESS_STRONG,
            minimum_window_met=True,
            preferred_window_met=True,
            logging_quality_met=True,
            bodyweight_trend_available=True,
            goal_context_available=True,
            training_context_available=True,
            reason_codes=["calibration_strong"],
        ),
        confidence="High",
        reason_codes=["preferred_window_met"],
        metadata=NutritionTrendWindowMetadata(
            inputs_used=["logged_intake", "bodyweight_trend", "goal_context"],
            reason_codes=["trend_window_created"],
        ),
    )

    assert window.calibration_readiness.calibration_allowed is True
    assert window.calibration_readiness.preferred_window_met is True
    assert window.metadata.model_version == "v1"


def test_no_log_days_are_counted_separately_from_partial_and_complete_days() -> None:
    day = NutritionTrendDay(
        date="2026-06-01",
        logging_completeness=LOGGING_COMPLETENESS_NO_LOGS,
        confidence="Limited",
        reason_codes=["no_logs"],
    )
    window = NutritionTrendWindow(
        user_id=1,
        start_date="2026-06-01",
        end_date="2026-06-03",
        window_days=3,
        logged_day_count=2,
        complete_logging_day_count=1,
        partial_logging_day_count=1,
        no_log_day_count=1,
        intake_trend_summary=_limited_intake_summary(),
        bodyweight_trend_summary=_unavailable_bodyweight(),
        calibration_readiness=_not_ready_readiness(),
        confidence="Limited",
        reason_codes=["minimum_window_not_met"],
        limitations=["Short trend window."],
        trend_days=[day],
    )

    assert window.logged_day_count == 2
    assert window.complete_logging_day_count == 1
    assert window.partial_logging_day_count == 1
    assert window.no_log_day_count == 1


def test_no_log_day_rejects_zero_coerced_logged_values() -> None:
    with pytest.raises(ValueError, match="No-log days"):
        NutritionTrendDay(
            date="2026-06-01",
            logged_calories=0,
            logging_completeness=LOGGING_COMPLETENESS_NO_LOGS,
            confidence="Limited",
        )


def test_missing_nutrient_values_are_not_coerced_to_zero() -> None:
    day = NutritionTrendDay(
        date="2026-06-02",
        logged_calories=1800,
        logged_protein=None,
        logged_carbohydrate=200,
        logged_fat=None,
        logging_completeness=LOGGING_COMPLETENESS_PARTIAL_DAY,
        confidence="Low",
        limitations=["Some nutrient values are missing."],
    )

    payload = day.to_dict()
    assert payload["logged_protein"] is None
    assert payload["logged_fat"] is None


def test_bodyweight_trend_unavailable_is_distinct_from_stable_trend() -> None:
    unavailable = _unavailable_bodyweight()
    stable = BodyweightTrendSummary(
        weigh_in_count=6,
        start_weight_lb=200,
        end_weight_lb=200.2,
        average_weight_lb=200.1,
        trend_direction=BODYWEIGHT_TREND_STABLE,
        weekly_rate_lb=0.05,
        confidence="Moderate",
    )

    assert unavailable.trend_direction == BODYWEIGHT_TREND_UNAVAILABLE
    assert stable.trend_direction == BODYWEIGHT_TREND_STABLE
    assert stable.weigh_in_count > 0


def test_calibration_readiness_can_be_not_ready() -> None:
    readiness = _not_ready_readiness()

    assert readiness.readiness_level == CALIBRATION_READINESS_NOT_READY
    assert readiness.calibration_allowed is False


def test_calibration_readiness_can_be_early_signal() -> None:
    readiness = NutritionCalibrationReadiness(
        calibration_allowed=False,
        readiness_level=CALIBRATION_READINESS_EARLY_SIGNAL,
        minimum_window_met=True,
        preferred_window_met=False,
        logging_quality_met=True,
        bodyweight_trend_available=True,
        goal_context_available=True,
        training_context_available=True,
        reason_codes=["calibration_early_signal"],
        limitations=["Preferred observation window has not been met."],
    )

    assert readiness.minimum_window_met is True
    assert readiness.preferred_window_met is False


def test_calibration_readiness_can_be_usable_or_strong_when_inputs_support_it() -> None:
    usable = NutritionCalibrationReadiness(
        calibration_allowed=True,
        readiness_level=CALIBRATION_READINESS_USABLE,
        minimum_window_met=True,
        preferred_window_met=False,
        logging_quality_met=True,
        bodyweight_trend_available=True,
        goal_context_available=True,
        training_context_available=True,
        reason_codes=["calibration_usable"],
    )
    strong = NutritionCalibrationReadiness(
        calibration_allowed=True,
        readiness_level=CALIBRATION_READINESS_STRONG,
        minimum_window_met=True,
        preferred_window_met=True,
        logging_quality_met=True,
        bodyweight_trend_available=True,
        goal_context_available=True,
        training_context_available=True,
        reason_codes=["calibration_strong"],
    )

    assert usable.calibration_allowed is True
    assert strong.preferred_window_met is True


def test_confidence_values_are_constrained() -> None:
    with pytest.raises(ValueError, match="Invalid confidence"):
        NutritionTrendDay(
            date="2026-06-01",
            logging_completeness=LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
            confidence="Certain",
        )


def test_model_does_not_require_target_mutation_fields() -> None:
    window = NutritionTrendWindow(
        user_id=1,
        start_date="2026-06-01",
        end_date="2026-06-07",
        window_days=7,
        logged_day_count=0,
        complete_logging_day_count=0,
        partial_logging_day_count=0,
        no_log_day_count=7,
        intake_trend_summary=_limited_intake_summary(),
        bodyweight_trend_summary=_unavailable_bodyweight(),
        calibration_readiness=_not_ready_readiness(),
        confidence="Limited",
        reason_codes=["minimum_window_not_met"],
        limitations=["Trend window is not ready for calibration."],
    )

    payload = window.to_dict()
    forbidden_fields = {
        "new_calorie_target",
        "mutated_targets",
        "target_adjustment",
        "ai_target_change",
    }
    assert forbidden_fields.isdisjoint(payload)


def test_forbidden_language_is_not_required_or_allowed_by_contracts() -> None:
    with pytest.raises(ValueError, match="Forbidden nutrition trend language"):
        NutritionTrendWindowMetadata(
            limitations=["Your true maintenance is exactly 2200 calories."],
        )


def test_trend_window_rejects_inconsistent_day_counts() -> None:
    with pytest.raises(ValueError, match="logged_day_count"):
        NutritionTrendWindow(
            user_id=1,
            start_date="2026-06-01",
            end_date="2026-06-07",
            window_days=7,
            logged_day_count=3,
            complete_logging_day_count=1,
            partial_logging_day_count=1,
            no_log_day_count=4,
            intake_trend_summary=_limited_intake_summary(),
            bodyweight_trend_summary=_unavailable_bodyweight(),
            calibration_readiness=_not_ready_readiness(),
            confidence="Limited",
            reason_codes=["minimum_window_not_met"],
            limitations=["Invalid day counts should be rejected."],
        )
