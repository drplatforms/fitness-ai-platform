from __future__ import annotations

import pytest

from models.recovery_intelligence_v2_models import (
    DATA_QUALITY_STATUS_VALUES,
    INDICATOR_STATUS_VALUES,
    READINESS_CLASSIFICATION_VALUES,
    RECOVERY_PRESSURE_VALUES,
    TREND_DIRECTION_VALUES,
    RecoveryBaseline,
    RecoveryDataQuality,
    RecoveryIndicatorInterpretation,
    RecoveryIntelligenceV2Summary,
    RecoveryRecentDelta,
    RecoverySourceFact,
    RecoveryV2IndicatorDay,
)


def _indicator(
    indicator_name: str,
    *,
    status: str = "normal",
    trend_direction: str = "stable",
    confidence: str = "Moderate",
) -> RecoveryIndicatorInterpretation:
    return RecoveryIndicatorInterpretation(
        indicator_name=indicator_name,
        current_value=7.2,
        baseline_value=7.0,
        recent_average=7.1,
        prior_average=6.9,
        delta_from_baseline=0.1,
        delta_recent_vs_prior=0.2,
        status=status,
        trend_direction=trend_direction,
        confidence=confidence,
        reason_codes=[] if confidence not in {"Limited", "Low"} else ["limited_data"],
    )


def _data_quality(
    *, confidence: str = "Moderate", status: str = "usable"
) -> RecoveryDataQuality:
    return RecoveryDataQuality(
        expected_days=7,
        checkin_days=6,
        checkin_rate=6 / 7,
        missing_sleep_days=1,
        missing_energy_days=0,
        missing_soreness_days=0,
        duplicate_days_collapsed=1,
        stale_current_day=False,
        status=status,
        confidence=confidence,
        reason_codes=[] if confidence not in {"Limited", "Low"} else ["limited_data"],
    )


def _summary(*, confidence: str = "Moderate") -> RecoveryIntelligenceV2Summary:
    return RecoveryIntelligenceV2Summary(
        user_id=102,
        target_date="2026-06-14",
        generated_at="2026-06-14T12:00:00Z",
        source_table="daily_checkins",
        model_version="recovery_intelligence_v2_model_contract_v1",
        current_day=RecoveryV2IndicatorDay(
            date="2026-06-14",
            sleep_hours=7.4,
            energy_level=7.0,
            soreness_level=3.0,
            body_weight_lb=200.5,
            notes_present=True,
            data_quality_status="usable",
        ),
        windows={"recent_7_days": {"window_days": 7}},
        baseline=RecoveryBaseline(
            baseline_window_days=28,
            start_date="2026-05-18",
            end_date="2026-06-14",
            checkin_days=24,
            average_sleep_hours=7.0,
            average_energy_level=6.5,
            average_soreness_level=3.5,
            latest_body_weight_lb=200.5,
            confidence="Moderate",
        ),
        recent_vs_baseline=RecoveryRecentDelta(
            comparison_name="recent_vs_baseline",
            recent_window_days=7,
            comparison_window_days=28,
            sleep_delta=0.1,
            energy_delta=0.3,
            soreness_delta=-0.2,
            body_weight_delta=None,
            trend_direction="stable",
            confidence="Moderate",
        ),
        recent_vs_prior=RecoveryRecentDelta(
            comparison_name="recent_vs_prior",
            recent_window_days=7,
            comparison_window_days=7,
            sleep_delta=0.2,
            energy_delta=0.4,
            soreness_delta=-0.3,
            body_weight_delta=0.0,
            trend_direction="improving",
            confidence="Moderate",
        ),
        sleep_interpretation=_indicator("sleep"),
        energy_interpretation=_indicator("energy"),
        soreness_interpretation=_indicator("soreness"),
        body_weight_interpretation=_indicator("body_weight"),
        checkin_consistency=_indicator("checkin_consistency"),
        readiness_classification="supportive",
        recovery_pressure="low",
        fatigue_support="supportive",
        data_quality=_data_quality(),
        confidence=confidence,
        source_facts=[
            RecoverySourceFact(
                source_table="daily_checkins",
                field_name="sleep_hours",
                observed_date="2026-06-14",
                value_summary="sleep hours present for current day",
                confidence="Moderate",
            )
        ],
        coach_safe_summary="Recovery appears supportive enough for controlled progression.",
        reason_codes=[] if confidence not in {"Limited", "Low"} else ["limited_data"],
    )


def test_recovery_v2_summary_constructs_and_serializes() -> None:
    summary = _summary()

    payload = summary.to_dict()

    assert payload["user_id"] == 102
    assert payload["target_date"] == "2026-06-14"
    assert payload["readiness_classification"] == "supportive"
    assert payload["recovery_pressure"] == "low"
    assert payload["data_quality"]["status"] == "usable"
    assert payload["sleep_interpretation"]["indicator_name"] == "sleep"
    assert payload["source_facts"][0]["source_table"] == "daily_checkins"


def test_bounded_classification_values_are_documented() -> None:
    assert "recovery_limited" in READINESS_CLASSIFICATION_VALUES
    assert "supportive" in READINESS_CLASSIFICATION_VALUES
    assert RECOVERY_PRESSURE_VALUES == {"unknown", "low", "moderate", "high"}
    assert "borderline" in INDICATOR_STATUS_VALUES
    assert "worsening" in TREND_DIRECTION_VALUES
    assert DATA_QUALITY_STATUS_VALUES == {
        "missing",
        "limited",
        "partial",
        "usable",
        "strong",
    }


def test_invalid_enum_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="readiness_classification"):
        RecoveryIntelligenceV2Summary(
            **{
                **_summary().to_dict(),
                "readiness_classification": "great",
                "current_day": _summary().current_day,
                "baseline": _summary().baseline,
                "recent_vs_baseline": _summary().recent_vs_baseline,
                "recent_vs_prior": _summary().recent_vs_prior,
                "sleep_interpretation": _summary().sleep_interpretation,
                "energy_interpretation": _summary().energy_interpretation,
                "soreness_interpretation": _summary().soreness_interpretation,
                "body_weight_interpretation": _summary().body_weight_interpretation,
                "checkin_consistency": _summary().checkin_consistency,
                "data_quality": _summary().data_quality,
                "source_facts": _summary().source_facts,
            }
        )


def test_limited_and_low_confidence_require_reason_codes_or_limitations() -> None:
    with pytest.raises(ValueError, match="Recovery baselines"):
        RecoveryBaseline(
            baseline_window_days=28,
            start_date="2026-05-18",
            end_date="2026-06-14",
            checkin_days=2,
            average_sleep_hours=None,
            average_energy_level=None,
            average_soreness_level=None,
            latest_body_weight_lb=None,
            confidence="Limited",
        )

    with pytest.raises(ValueError, match="Recovery v2 summaries"):
        RecoveryIntelligenceV2Summary(
            **{
                **_summary().to_dict(),
                "confidence": "Low",
                "reason_codes": [],
                "limitations": [],
                "current_day": _summary().current_day,
                "baseline": _summary().baseline,
                "recent_vs_baseline": _summary().recent_vs_baseline,
                "recent_vs_prior": _summary().recent_vs_prior,
                "sleep_interpretation": _summary().sleep_interpretation,
                "energy_interpretation": _summary().energy_interpretation,
                "soreness_interpretation": _summary().soreness_interpretation,
                "body_weight_interpretation": _summary().body_weight_interpretation,
                "checkin_consistency": _summary().checkin_consistency,
                "data_quality": _summary().data_quality,
                "source_facts": _summary().source_facts,
            }
        )


def test_missing_values_remain_explicit_none_not_zero() -> None:
    interpretation = RecoveryIndicatorInterpretation(
        indicator_name="sleep",
        current_value=None,
        baseline_value=None,
        recent_average=None,
        prior_average=None,
        delta_from_baseline=None,
        delta_recent_vs_prior=None,
        status="unknown",
        trend_direction="unknown",
        confidence="Limited",
        limitations=["missing_sleep_data"],
    )

    payload = interpretation.to_dict()

    assert payload["current_value"] is None
    assert payload["baseline_value"] is None
    assert payload["recent_average"] is None
    assert payload["delta_from_baseline"] is None


def test_data_quality_model_requires_explicit_missing_counts() -> None:
    quality = RecoveryDataQuality(
        expected_days=7,
        checkin_days=0,
        checkin_rate=0.0,
        missing_sleep_days=7,
        missing_energy_days=7,
        missing_soreness_days=7,
        duplicate_days_collapsed=0,
        stale_current_day=True,
        status="missing",
        confidence="Limited",
        limitations=["no_checkins_in_window"],
    )

    payload = quality.to_dict()

    assert payload["missing_sleep_days"] == 7
    assert payload["missing_energy_days"] == 7
    assert payload["missing_soreness_days"] == 7
    assert payload["stale_current_day"] is True


def test_forbidden_recovery_language_is_rejected() -> None:
    with pytest.raises(ValueError, match="forbidden recovery language"):
        RecoveryIndicatorInterpretation(
            indicator_name="soreness",
            current_value=9.0,
            baseline_value=4.0,
            recent_average=8.0,
            prior_average=4.0,
            delta_from_baseline=4.0,
            delta_recent_vs_prior=4.0,
            status="high",
            trend_direction="worsening",
            confidence="Moderate",
            limitations=["injury risk is high"],
        )

    with pytest.raises(ValueError, match="forbidden recovery language"):
        RecoveryIntelligenceV2Summary(
            **{
                **_summary().to_dict(),
                "coach_safe_summary": "You must deload because you are not recovering.",
                "current_day": _summary().current_day,
                "baseline": _summary().baseline,
                "recent_vs_baseline": _summary().recent_vs_baseline,
                "recent_vs_prior": _summary().recent_vs_prior,
                "sleep_interpretation": _summary().sleep_interpretation,
                "energy_interpretation": _summary().energy_interpretation,
                "soreness_interpretation": _summary().soreness_interpretation,
                "body_weight_interpretation": _summary().body_weight_interpretation,
                "checkin_consistency": _summary().checkin_consistency,
                "data_quality": _summary().data_quality,
                "source_facts": _summary().source_facts,
            }
        )


def test_source_fact_validates_provenance_shape() -> None:
    fact = RecoverySourceFact(
        source_table="daily_checkins",
        field_name="energy_level",
        observed_date=None,
        value_summary="recent energy average present",
        confidence="Moderate",
    )

    assert fact.to_dict()["observed_date"] is None

    with pytest.raises(ValueError, match="confidence"):
        RecoverySourceFact(
            source_table="daily_checkins",
            field_name="energy_level",
            observed_date="2026-06-14",
            value_summary="recent energy average present",
            confidence="Certain",
        )


def test_model_contract_does_not_require_service_or_snapshot_integration() -> None:
    summary = _summary()

    assert summary.model_version == "recovery_intelligence_v2_model_contract_v1"
    assert summary.source_table == "daily_checkins"
    assert summary.recent_vs_baseline is not None
    assert summary.recent_vs_prior is not None
