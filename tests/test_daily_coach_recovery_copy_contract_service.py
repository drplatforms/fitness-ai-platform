from __future__ import annotations

import pytest

import database
from models.daily_coach_intelligence_models import DailyCoachIntelligenceSnapshot
from models.daily_coach_recovery_copy_models import RecoveryAwareCoachCopyContract
from models.recovery_intelligence_models import (
    RecoveryIntelligenceSummary,
    RecoverySignalDay,
    RecoveryTrendComparison,
    RecoveryWindowSummary,
)
from models.recovery_intelligence_v2_models import (
    RecoveryBaseline,
    RecoveryDataQuality,
    RecoveryIndicatorInterpretation,
    RecoveryIntelligenceV2Summary,
    RecoveryRecentDelta,
    RecoverySourceFact,
    RecoveryV2IndicatorDay,
)
from services.daily_coach_recovery_copy_contract_service import (
    build_recovery_aware_coach_copy_contract,
)

_FORBIDDEN_TERMS = (
    "overtraining",
    "injury",
    "illness",
    "diagnosis",
    "sleep disorder",
    "medical risk",
    "treatment",
    "must deload",
    "forced deload",
    "automatic deload",
    "automatic progression",
    "fat gain caused by recovery",
    "fat loss caused by recovery",
    "nutrition blame caused by recovery",
    "you should not train",
    "you are unsafe to train",
)


def _v1_recovery_summary() -> RecoveryIntelligenceSummary:
    window = RecoveryWindowSummary(
        window_days=7,
        start_date="2026-06-08",
        end_date="2026-06-14",
        expected_days=7,
        checkin_days=6,
        checkin_rate=6 / 7,
        average_sleep_hours=7.0,
        average_energy_level=7.0,
        average_soreness_level=3.0,
        latest_body_weight_lb=190.0,
        body_weight_delta_lb=0.1,
        sleep_signal="adequate",
        energy_signal="strong",
        soreness_signal="moderate",
        readiness_level="high",
        fatigue_risk="low",
        confidence="Moderate",
    )
    return RecoveryIntelligenceSummary(
        user_id=102,
        target_date="2026-06-14",
        generated_at="2026-06-14T12:00:00Z",
        source_table="daily_checkins",
        model_version="recovery_intelligence_service_v1",
        current_day=RecoverySignalDay(
            date="2026-06-14",
            sleep_hours=7.2,
            energy_level=7.0,
            soreness_level=3.0,
            body_weight_lb=190.0,
            mood=None,
            notes_present=False,
        ),
        windows={"7": window},
        trend_comparison=RecoveryTrendComparison(
            recent_window_days=7,
            prior_window_days=7,
            sleep_delta=0.1,
            energy_delta=0.1,
            soreness_delta=-0.2,
            body_weight_delta=0.1,
            trend_direction="stable",
            confidence="Moderate",
        ),
        readiness_level="high",
        fatigue_risk="low",
        confidence="Moderate",
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
    *,
    confidence: str = "Moderate",
    status: str = "usable",
    checkin_days: int = 6,
) -> RecoveryDataQuality:
    return RecoveryDataQuality(
        expected_days=7,
        checkin_days=checkin_days,
        checkin_rate=checkin_days / 7,
        missing_sleep_days=7 - checkin_days,
        missing_energy_days=0,
        missing_soreness_days=0,
        duplicate_days_collapsed=0,
        stale_current_day=False,
        status=status,
        confidence=confidence,
        reason_codes=[] if confidence not in {"Limited", "Low"} else ["limited_data"],
    )


def _recovery_v2_summary(
    *,
    confidence: str = "Moderate",
    data_quality_status: str = "usable",
    recovery_pressure: str = "moderate",
    readiness_classification: str = "manageable",
    sleep_status: str = "borderline",
    energy_status: str = "normal",
    soreness_status: str = "high",
    checkin_days: int = 6,
) -> RecoveryIntelligenceV2Summary:
    limited = confidence in {"Limited", "Low"} or data_quality_status in {
        "missing",
        "limited",
        "partial",
    }
    return RecoveryIntelligenceV2Summary(
        user_id=102,
        target_date="2026-06-14",
        generated_at="2026-06-14T12:00:00Z",
        source_table="daily_checkins",
        model_version="recovery_intelligence_v2_service_v1",
        current_day=RecoveryV2IndicatorDay(
            date="2026-06-14",
            sleep_hours=6.6,
            energy_level=7.0,
            soreness_level=7.5,
            body_weight_lb=190.0,
            notes_present=True,
            data_quality_status=data_quality_status,
        ),
        windows={"recent_7_days": {"window_days": 7}},
        baseline=RecoveryBaseline(
            baseline_window_days=28,
            start_date="2026-05-18",
            end_date="2026-06-14",
            checkin_days=24,
            average_sleep_hours=7.0,
            average_energy_level=6.8,
            average_soreness_level=3.0,
            latest_body_weight_lb=190.0,
            confidence="Moderate",
        ),
        recent_vs_baseline=RecoveryRecentDelta(
            comparison_name="recent_vs_baseline",
            recent_window_days=7,
            comparison_window_days=28,
            sleep_delta=-0.4,
            energy_delta=0.2,
            soreness_delta=2.0,
            body_weight_delta=0.1,
            trend_direction="mixed",
            confidence="Moderate",
        ),
        recent_vs_prior=RecoveryRecentDelta(
            comparison_name="recent_vs_prior",
            recent_window_days=7,
            comparison_window_days=7,
            sleep_delta=-0.3,
            energy_delta=0.1,
            soreness_delta=1.5,
            body_weight_delta=0.1,
            trend_direction="mixed",
            confidence="Moderate",
        ),
        sleep_interpretation=_indicator("sleep", status=sleep_status),
        energy_interpretation=_indicator("energy", status=energy_status),
        soreness_interpretation=_indicator("soreness", status=soreness_status),
        body_weight_interpretation=_indicator("body_weight", status="normal"),
        checkin_consistency=_indicator("checkin_consistency", status="normal"),
        readiness_classification=readiness_classification,
        recovery_pressure=recovery_pressure,
        fatigue_support="mixed",
        data_quality=_data_quality(
            confidence=confidence,
            status=data_quality_status,
            checkin_days=checkin_days,
        ),
        confidence=confidence,
        source_facts=[
            RecoverySourceFact(
                source_table="daily_checkins",
                field_name="sleep_hours",
                observed_date=None,
                value_summary="recent sleep average present",
                confidence=confidence,
            )
        ],
        coach_safe_summary="Recent recovery indicators look manageable.",
        reason_codes=["limited_data"] if limited else ["recovery_v2_available"],
        limitations=["Recovery v2 has limited check-in coverage."] if limited else [],
    )


def _snapshot(
    recovery_v2: RecoveryIntelligenceV2Summary | None,
) -> DailyCoachIntelligenceSnapshot:
    source_services = ["recovery_intelligence_service"]
    if recovery_v2 is not None:
        source_services.append("recovery_intelligence_v2_service")
    return DailyCoachIntelligenceSnapshot(
        user_id=102,
        target_date="2026-06-14",
        generated_at="2026-06-14T12:05:00Z",
        snapshot_version="daily_coach_intelligence_snapshot_v3",
        source_services=source_services,
        recovery_intelligence=_v1_recovery_summary(),
        recovery_intelligence_v2=recovery_v2,
        workout_set_intelligence=None,
        training_execution_summary=None,
        nutrition_trend_window=None,
        foundation_layer_status={"recovery_intelligence_v2": "implemented_v1"},
        data_completeness={
            "recovery_intelligence": "usable",
            "recovery_intelligence_v2": "usable" if recovery_v2 else "unavailable",
        },
        source_data_gaps=(
            [] if recovery_v2 else ["recovery_intelligence_v2: unavailable"]
        ),
        reason_codes=[] if recovery_v2 else ["recovery_intelligence_v2_unavailable"],
        limitations=[] if recovery_v2 else ["Recovery v2 intelligence unavailable."],
    )


def _joined_payload(contract: RecoveryAwareCoachCopyContract) -> str:
    payload = contract.to_dict()
    return " ".join(str(value).lower() for value in payload.values())


def test_contract_builds_when_recovery_intelligence_v2_is_present() -> None:
    contract = build_recovery_aware_coach_copy_contract(
        _snapshot(_recovery_v2_summary())
    )

    assert contract.user_id == 102
    assert contract.target_date == "2026-06-14"
    assert contract.contract_version == "recovery_aware_coach_copy_contract_v1"
    assert contract.recovery_v2_available is True
    assert contract.allowed_recovery_claims
    assert "recovery_intelligence_v2_service" in contract.source_services


def test_contract_preserves_recovery_v2_classification_pressure_confidence_and_quality() -> (
    None
):
    contract = build_recovery_aware_coach_copy_contract(
        _snapshot(
            _recovery_v2_summary(
                confidence="High",
                data_quality_status="strong",
                recovery_pressure="high",
                readiness_classification="recovery_limited",
            )
        )
    )

    assert contract.recovery_classification == "recovery_limited"
    assert contract.recovery_pressure == "high"
    assert contract.confidence == "High"
    assert contract.data_quality_status == "strong"


def test_contract_includes_allowed_claims_only_from_supported_v2_facts() -> None:
    contract = build_recovery_aware_coach_copy_contract(
        _snapshot(
            _recovery_v2_summary(
                sleep_status="unknown",
                energy_status="normal",
                soreness_status="high",
            )
        )
    )

    claims = " ".join(contract.allowed_recovery_claims).lower()
    assert "sleep appears" not in claims
    assert "energy appears near baseline" in claims
    assert "soreness appears elevated" in claims
    assert "recovery pressure appears" in claims
    assert "body weight is present as context only" in claims


def test_contract_includes_caveats_when_confidence_or_data_quality_is_limited() -> None:
    contract = build_recovery_aware_coach_copy_contract(
        _snapshot(
            _recovery_v2_summary(
                confidence="Limited",
                data_quality_status="partial",
                checkin_days=3,
            )
        )
    )

    caveats = " ".join(contract.required_caveats).lower()
    assert contract.confidence == "Limited"
    assert contract.data_quality_status == "partial"
    assert "confidence is limited" in caveats
    assert "check-in data is limited" in caveats
    assert "3 of 7 expected check-in days" in caveats


def test_contract_returns_valid_limited_contract_when_recovery_v2_is_none() -> None:
    contract = build_recovery_aware_coach_copy_contract(_snapshot(None))

    assert contract.recovery_v2_available is False
    assert contract.recovery_classification == "unknown"
    assert contract.recovery_pressure == "unknown"
    assert contract.confidence == "Limited"
    assert contract.data_quality_status == "missing"
    assert "recovery_intelligence_v2_unavailable" in contract.reason_codes
    assert contract.required_caveats


def test_contract_serializes_from_snapshot_dict() -> None:
    snapshot_dict = _snapshot(_recovery_v2_summary()).to_dict()

    contract = build_recovery_aware_coach_copy_contract(snapshot_dict)
    payload = contract.to_dict()

    assert payload["user_id"] == 102
    assert payload["recovery_v2_available"] is True
    assert payload["allowed_recovery_claims"]
    assert payload["forbidden_claims"]


def test_contract_does_not_include_forbidden_medical_training_or_causal_language() -> (
    None
):
    contract = build_recovery_aware_coach_copy_contract(
        _snapshot(_recovery_v2_summary())
    )
    joined = _joined_payload(contract)

    assert not [term for term in _FORBIDDEN_TERMS if term in joined]


def test_model_rejects_forbidden_copy_language() -> None:
    with pytest.raises(ValueError, match="forbidden recovery copy language"):
        RecoveryAwareCoachCopyContract(
            user_id=102,
            target_date="2026-06-14",
            recovery_v2_available=True,
            recovery_classification="manageable",
            recovery_pressure="moderate",
            confidence="Moderate",
            data_quality_status="usable",
            allowed_recovery_claims=["you are unsafe to train"],
        )


def test_contract_does_not_call_providers_or_mutate_database(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    conn = database.get_connection()
    before = conn.execute("SELECT COUNT(*) AS count FROM daily_checkins").fetchone()[
        "count"
    ]
    conn.close()

    contract = build_recovery_aware_coach_copy_contract(
        _snapshot(_recovery_v2_summary())
    )

    conn = database.get_connection()
    after = conn.execute("SELECT COUNT(*) AS count FROM daily_checkins").fetchone()[
        "count"
    ]
    conn.close()
    assert before == after
    assert "provider" not in " ".join(contract.source_services).lower()
    assert "ollama" not in _joined_payload(contract)
    assert "crewai" not in _joined_payload(contract)
