from __future__ import annotations

import copy

import database
from models.nutrition_target_formula_models import (
    ApprovedMacroTargets,
    MacroTargetResult,
    NutritionTargetFormulaMetadata,
)
from models.nutrition_trend_models import (
    BODYWEIGHT_TREND_DECREASING,
    BODYWEIGHT_TREND_UNAVAILABLE,
    CALIBRATION_READINESS_EARLY_SIGNAL,
    CALIBRATION_READINESS_NOT_READY,
    CALIBRATION_READINESS_STRONG,
    CALIBRATION_READINESS_USABLE,
    LOGGING_CONSISTENCY_INSUFFICIENT,
    LOGGING_CONSISTENCY_STRONG,
    LOGGING_CONSISTENCY_USABLE,
    BodyweightTrendSummary,
    NutritionCalibrationReadiness,
    NutritionIntakeTrendSummary,
    NutritionTrendWindow,
)
from services.nutrition_target_calibration_service import (
    RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT,
    RECOMMENDED_ACTION_INSUFFICIENT_DATA,
    RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS,
    RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE,
    NutritionTargetCalibrationResult,
    assess_nutrition_target_calibration,
    build_nutrition_target_calibration_result,
)


def _macro_target(target_type: str, value: float, unit: str) -> MacroTargetResult:
    return MacroTargetResult(
        target_type=target_type,
        value=value,
        min_value=value - 10,
        max_value=value + 10,
        display_value=f"{value - 10:g}-{value + 10:g} {unit}",
        unit=unit,
        confidence="Moderate",
        display_allowed=True,
        method="test_formula",
        reason_codes=[f"{target_type}_target_available"],
        limitations=["Formula targets are coaching estimates."],
    )


def _blocked_target(target_type: str, unit: str) -> MacroTargetResult:
    return MacroTargetResult(
        target_type=target_type,
        unit=unit,
        confidence="Limited",
        display_allowed=False,
        method="test_formula",
        reason_codes=[f"{target_type}_target_blocked"],
        limitations=[f"{target_type} target is blocked in this fixture."],
    )


def _approved_targets(
    *, confidence: str = "Moderate", full: bool = True
) -> ApprovedMacroTargets:
    metadata = NutritionTargetFormulaMetadata(
        formula_name="test_formula",
        formula_version="v1",
        calculation_date="2026-06-06",
        inputs_used=["test_profile_context"],
        rounding_rules=["test_rounding"],
        target_basis="Formula target fixture for calibration service tests.",
        reason_codes=[
            "formula_targets_available" if full else "formula_targets_limited"
        ],
        limitations=["Formula targets are deterministic test estimates."],
    )
    if full:
        return ApprovedMacroTargets(
            user_id=1,
            calculation_date="2026-06-06",
            calorie_target=_macro_target("calories", 2400, "kcal/day"),
            protein_target_g=_macro_target("protein_g", 170, "g/day"),
            carbohydrate_target_g=_macro_target("carbohydrate_g", 290, "g/day"),
            fat_target_g=_macro_target("fat_g", 75, "g/day"),
            confidence=confidence,
            display_flags={
                "allow_calorie_targets": True,
                "allow_protein_targets": True,
                "allow_carbohydrate_targets": True,
                "allow_fat_targets": True,
            },
            formula_metadata=metadata,
            reason_codes=["formula_targets_available"],
            limitations=["Formula targets are deterministic test estimates."],
        )

    return ApprovedMacroTargets(
        user_id=1,
        calculation_date="2026-06-06",
        calorie_target=_blocked_target("calories", "kcal/day"),
        protein_target_g=_macro_target("protein_g", 170, "g/day"),
        carbohydrate_target_g=_blocked_target("carbohydrate_g", "g/day"),
        fat_target_g=_blocked_target("fat_g", "g/day"),
        confidence="Low",
        display_flags={
            "allow_calorie_targets": False,
            "allow_protein_targets": True,
            "allow_carbohydrate_targets": False,
            "allow_fat_targets": False,
        },
        formula_metadata=metadata,
        reason_codes=["formula_targets_limited", "calorie_display_blocked"],
        limitations=["Formula targets are limited in this fixture."],
    )


def _intake_summary(
    *, status: str = LOGGING_CONSISTENCY_USABLE, confidence: str = "Moderate"
) -> NutritionIntakeTrendSummary:
    return NutritionIntakeTrendSummary(
        average_calories=2250.0 if status != LOGGING_CONSISTENCY_INSUFFICIENT else None,
        average_protein_g=165.0 if status != LOGGING_CONSISTENCY_INSUFFICIENT else None,
        average_carbohydrate_g=(
            275.0 if status != LOGGING_CONSISTENCY_INSUFFICIENT else None
        ),
        average_fat_g=72.0 if status != LOGGING_CONSISTENCY_INSUFFICIENT else None,
        complete_logging_rate=0.8 if status != LOGGING_CONSISTENCY_INSUFFICIENT else 0,
        logging_consistency_status=status,
        confidence=confidence,
        reason_codes=[
            (
                "logging_quality_usable"
                if status in {LOGGING_CONSISTENCY_USABLE, LOGGING_CONSISTENCY_STRONG}
                else "logging_quality_insufficient"
            )
        ],
        limitations=(
            []
            if status != LOGGING_CONSISTENCY_INSUFFICIENT
            else ["Logging is insufficient."]
        ),
    )


def _bodyweight_summary(*, available: bool = True) -> BodyweightTrendSummary:
    if not available:
        return BodyweightTrendSummary(
            trend_direction=BODYWEIGHT_TREND_UNAVAILABLE,
            confidence="Limited",
            reason_codes=["bodyweight_trend_unavailable"],
            limitations=["Bodyweight trend is unavailable."],
        )
    return BodyweightTrendSummary(
        weigh_in_count=10,
        start_weight_lb=190.0,
        end_weight_lb=188.5,
        average_weight_lb=189.2,
        trend_direction=BODYWEIGHT_TREND_DECREASING,
        weekly_rate_lb=-0.4,
        confidence="Moderate",
        reason_codes=["bodyweight_trend_available"],
    )


def _readiness(
    *, level: str = CALIBRATION_READINESS_USABLE, bodyweight_available: bool = True
) -> NutritionCalibrationReadiness:
    if level == CALIBRATION_READINESS_NOT_READY:
        return NutritionCalibrationReadiness(
            calibration_allowed=False,
            readiness_level=CALIBRATION_READINESS_NOT_READY,
            minimum_window_met=False,
            preferred_window_met=False,
            logging_quality_met=False,
            bodyweight_trend_available=bodyweight_available,
            goal_context_available=False,
            training_context_available=False,
            reason_codes=["calibration_not_ready", "minimum_window_not_met"],
            limitations=["Trend evidence is insufficient."],
        )
    if level == CALIBRATION_READINESS_EARLY_SIGNAL:
        return NutritionCalibrationReadiness(
            calibration_allowed=False,
            readiness_level=CALIBRATION_READINESS_EARLY_SIGNAL,
            minimum_window_met=True,
            preferred_window_met=False,
            logging_quality_met=True,
            bodyweight_trend_available=bodyweight_available,
            goal_context_available=True,
            training_context_available=True,
            reason_codes=["calibration_early_signal", "minimum_window_met"],
            limitations=["Trend evidence is early; 28 days are preferred."],
        )
    return NutritionCalibrationReadiness(
        calibration_allowed=True,
        readiness_level=level,
        minimum_window_met=True,
        preferred_window_met=True,
        logging_quality_met=True,
        bodyweight_trend_available=bodyweight_available,
        goal_context_available=True,
        training_context_available=True,
        reason_codes=[
            (
                "calibration_strong"
                if level == CALIBRATION_READINESS_STRONG
                else "calibration_usable"
            ),
            "preferred_window_met",
        ],
        limitations=[],
    )


def _trend_window(
    *,
    window_days: int = 28,
    readiness_level: str = CALIBRATION_READINESS_USABLE,
    logging_status: str = LOGGING_CONSISTENCY_USABLE,
    bodyweight_available: bool = True,
    confidence: str | None = None,
) -> NutritionTrendWindow:
    if readiness_level == CALIBRATION_READINESS_NOT_READY:
        logged_count = 0
        complete_count = 0
        partial_count = 0
        no_log_count = window_days
        confidence = confidence or "Limited"
    elif readiness_level == CALIBRATION_READINESS_EARLY_SIGNAL:
        logged_count = 10
        complete_count = 8
        partial_count = 2
        no_log_count = window_days - logged_count
        confidence = confidence or "Low"
    else:
        logged_count = 26 if window_days >= 28 else 12
        complete_count = 24 if window_days >= 28 else 10
        partial_count = logged_count - complete_count
        no_log_count = window_days - logged_count
        confidence = confidence or (
            "High" if readiness_level == CALIBRATION_READINESS_STRONG else "Moderate"
        )

    return NutritionTrendWindow(
        user_id=1,
        start_date="2026-05-10",
        end_date="2026-06-06",
        window_days=window_days,
        logged_day_count=logged_count,
        complete_logging_day_count=complete_count,
        partial_logging_day_count=partial_count,
        no_log_day_count=no_log_count,
        intake_trend_summary=_intake_summary(
            status=logging_status,
            confidence=(
                ("High" if logging_status == LOGGING_CONSISTENCY_STRONG else "Moderate")
                if logging_status != LOGGING_CONSISTENCY_INSUFFICIENT
                else "Limited"
            ),
        ),
        bodyweight_trend_summary=_bodyweight_summary(available=bodyweight_available),
        calibration_readiness=_readiness(
            level=readiness_level, bodyweight_available=bodyweight_available
        ),
        confidence=confidence,
        reason_codes=[
            "trend_window_created",
            (
                "bodyweight_trend_available"
                if bodyweight_available
                else "bodyweight_trend_unavailable"
            ),
        ],
        limitations=(
            []
            if confidence not in {"Limited", "Low"}
            else ["Trend evidence is limited."]
        ),
    )


def test_insufficient_trend_window_returns_calibration_not_ready() -> None:
    result = assess_nutrition_target_calibration(
        user_id=1,
        calibration_date="2026-06-06",
        trend_window=_trend_window(readiness_level=CALIBRATION_READINESS_NOT_READY),
        approved_targets=_approved_targets(),
    )

    assert result.recommended_action == RECOMMENDED_ACTION_INSUFFICIENT_DATA
    assert result.calibration_allowed is False
    assert result.confidence == "Limited"
    assert "calibration_not_ready" in result.reason_codes
    assert result.calibrated_targets is None


def test_no_log_or_poor_log_window_blocks_calibration() -> None:
    result = assess_nutrition_target_calibration(
        user_id=1,
        calibration_date="2026-06-06",
        trend_window=_trend_window(
            readiness_level=CALIBRATION_READINESS_NOT_READY,
            logging_status=LOGGING_CONSISTENCY_INSUFFICIENT,
        ),
        approved_targets=_approved_targets(),
    )

    assert result.calibration_allowed is False
    assert result.recommended_action == RECOMMENDED_ACTION_INSUFFICIENT_DATA
    assert any("Logging" in limitation for limitation in result.limitations)


def test_missing_bodyweight_trend_blocks_or_limits_calibration() -> None:
    result = assess_nutrition_target_calibration(
        user_id=1,
        calibration_date="2026-06-06",
        trend_window=_trend_window(
            readiness_level=CALIBRATION_READINESS_NOT_READY,
            bodyweight_available=False,
        ),
        approved_targets=_approved_targets(),
    )

    assert result.calibration_allowed is False
    assert "bodyweight_trend_unavailable" in result.reason_codes
    assert any("Bodyweight trend" in limitation for limitation in result.limitations)


def test_14_day_early_window_can_produce_early_signal_but_not_strong_calibration() -> (
    None
):
    result = assess_nutrition_target_calibration(
        user_id=1,
        calibration_date="2026-06-06",
        trend_window=_trend_window(
            window_days=14,
            readiness_level=CALIBRATION_READINESS_EARLY_SIGNAL,
        ),
        approved_targets=_approved_targets(),
    )

    assert result.readiness_level == CALIBRATION_READINESS_EARLY_SIGNAL
    assert result.recommended_action == RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE
    assert result.calibration_allowed is False
    assert "target_range_remains_broad" in result.reason_codes


def test_28_day_preferred_window_with_usable_evidence_keeps_current_targets() -> None:
    result = assess_nutrition_target_calibration(
        user_id=1,
        calibration_date="2026-06-06",
        trend_window=_trend_window(readiness_level=CALIBRATION_READINESS_USABLE),
        approved_targets=_approved_targets(confidence="Moderate"),
    )

    assert result.readiness_level == CALIBRATION_READINESS_USABLE
    assert result.recommended_action == RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS
    assert result.calibration_allowed is True
    assert "current_targets_kept" in result.reason_codes
    assert any("keeping formula-derived targets" in item for item in result.limitations)


def test_28_day_preferred_window_with_strong_evidence_can_be_future_refinement_candidate() -> (
    None
):
    result = assess_nutrition_target_calibration(
        user_id=1,
        calibration_date="2026-06-06",
        trend_window=_trend_window(
            readiness_level=CALIBRATION_READINESS_STRONG,
            logging_status=LOGGING_CONSISTENCY_STRONG,
            confidence="High",
        ),
        approved_targets=_approved_targets(confidence="High"),
    )

    assert result.readiness_level == CALIBRATION_READINESS_STRONG
    assert (
        result.recommended_action == RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT
    )
    assert result.calibration_allowed is True
    assert result.confidence == "High"
    assert "future_refinement_candidate" in result.reason_codes


def test_limited_formula_targets_maintain_broad_ranges() -> None:
    result = assess_nutrition_target_calibration(
        user_id=1,
        calibration_date="2026-06-06",
        trend_window=_trend_window(readiness_level=CALIBRATION_READINESS_STRONG),
        approved_targets=_approved_targets(full=False),
    )

    assert result.recommended_action == RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE
    assert result.calibration_allowed is False
    assert "formula_targets_limited" in result.reason_codes
    assert any(
        "target ranges should remain broad" in item for item in result.limitations
    )


def test_service_does_not_mutate_formula_targets() -> None:
    targets = _approved_targets(confidence="High")
    before = copy.deepcopy(targets.to_dict())

    assess_nutrition_target_calibration(
        user_id=1,
        calibration_date="2026-06-06",
        trend_window=_trend_window(
            readiness_level=CALIBRATION_READINESS_STRONG,
            logging_status=LOGGING_CONSISTENCY_STRONG,
            confidence="High",
        ),
        approved_targets=targets,
    )

    assert targets.to_dict() == before


def test_service_does_not_mutate_user_profile_activity_or_goal_fields(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()

    before = _user_profile_snapshot(1)
    result = build_nutrition_target_calibration_result(
        1,
        calibration_date="2026-06-06",
        window_days=14,
    )
    after = _user_profile_snapshot(1)

    assert isinstance(result, NutritionTargetCalibrationResult)
    assert before == after
    assert result.calibrated_targets is None
    assert "target_mutation_not_performed" in result.reason_codes


def test_service_does_not_create_exact_maintenance_calorie_claims() -> None:
    result = assess_nutrition_target_calibration(
        user_id=1,
        calibration_date="2026-06-06",
        trend_window=_trend_window(readiness_level=CALIBRATION_READINESS_USABLE),
        approved_targets=_approved_targets(),
    )

    flattened = str(result.to_dict()).lower()
    assert "true maintenance is exactly" not in flattened
    assert "metabolism is damaged" not in flattened
    assert "must cut calories" not in flattened
    assert "no_exact_maintenance_claim" in result.reason_codes


def test_forbidden_calibration_language_is_rejected() -> None:
    try:
        NutritionTargetCalibrationResult(
            user_id=1,
            calibration_date="2026-06-06",
            window_days=28,
            calibration_allowed=False,
            readiness_level=CALIBRATION_READINESS_NOT_READY,
            recommended_action=RECOMMENDED_ACTION_INSUFFICIENT_DATA,
            confidence="Limited",
            reason_codes=["target_mutation_not_performed"],
            limitations=["Your true maintenance is exactly 2200 calories."],
        )
    except ValueError as exc:
        assert "Forbidden nutrition calibration language" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Forbidden calibration language should be rejected")


def _user_profile_snapshot(user_id: int) -> tuple:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT primary_goal, activity_level, goal_weight, starting_weight
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return tuple(row) if row else ()
