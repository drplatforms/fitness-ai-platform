from __future__ import annotations

import json

import pytest

from models.recovery_intelligence_v2_models import (
    RecoveryBaseline,
    RecoveryDataQuality,
    RecoveryIndicatorInterpretation,
    RecoveryIntelligenceV2Summary,
    RecoveryRecentDelta,
    RecoverySourceFact,
    RecoveryV2IndicatorDay,
)
from tools import dev_recovery_intelligence_v2 as tool


def _indicator(indicator_name: str) -> RecoveryIndicatorInterpretation:
    return RecoveryIndicatorInterpretation(
        indicator_name=indicator_name,
        current_value=7.2,
        baseline_value=7.0,
        recent_average=7.1,
        prior_average=6.8,
        delta_from_baseline=0.1,
        delta_recent_vs_prior=0.3,
        status="normal",
        trend_direction="stable",
        confidence="Moderate",
    )


def _summary() -> RecoveryIntelligenceV2Summary:
    return RecoveryIntelligenceV2Summary(
        user_id=102,
        target_date="2026-06-14",
        generated_at="2026-06-14T12:00:00+00:00",
        source_table="daily_checkins",
        model_version="recovery_intelligence_v2_service_v1",
        current_day=RecoveryV2IndicatorDay(
            date="2026-06-14",
            sleep_hours=7.4,
            energy_level=7.0,
            soreness_level=3.0,
            body_weight_lb=200.5,
            notes_present=True,
            data_quality_status="usable",
        ),
        windows={
            "recent_7_days": {"window_days": 7, "checkin_days": 7},
            "prior_7_days": {"window_days": 7, "checkin_days": 7},
            "baseline_28_days": {"window_days": 28, "checkin_days": 21},
        },
        baseline=RecoveryBaseline(
            baseline_window_days=28,
            start_date="2026-05-18",
            end_date="2026-06-14",
            checkin_days=21,
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
            sleep_delta=0.3,
            energy_delta=0.4,
            soreness_delta=-0.5,
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
        data_quality=RecoveryDataQuality(
            expected_days=28,
            checkin_days=21,
            checkin_rate=0.75,
            missing_sleep_days=0,
            missing_energy_days=0,
            missing_soreness_days=0,
            duplicate_days_collapsed=1,
            stale_current_day=False,
            status="usable",
            confidence="Moderate",
        ),
        confidence="Moderate",
        source_facts=[
            RecoverySourceFact(
                source_table="daily_checkins",
                field_name="sleep_hours",
                observed_date="2026-06-14",
                value_summary="sleep hours present for current day",
                confidence="Moderate",
            )
        ],
        coach_safe_summary="Recent recovery indicators look supportive enough for a controlled day.",
        reason_codes=[],
        limitations=[],
    )


def test_tool_help_exits_successfully(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        tool.main(["--help"])

    captured = capsys.readouterr()
    assert excinfo.value.code == 0
    assert "Developer-only Recovery Intelligence v2 inspection tool" in captured.out


def test_text_mode_prints_expected_top_level_sections(monkeypatch, capsys) -> None:
    calls = []

    def fake_build(user_id: int, target_date: str | None = None):
        calls.append((user_id, target_date))
        return _summary()

    monkeypatch.setattr(tool, "build_recovery_intelligence_v2", fake_build)

    exit_code = tool.main(["--user-id", "102", "--date", "2026-06-14"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls == [(102, "2026-06-14")]
    assert "# Recovery Intelligence v2 Inspection" in captured.out
    assert "## Current Day" in captured.out
    assert "## Baseline Window" in captured.out
    assert "## Recent vs Baseline" in captured.out
    assert "## Recent vs Prior" in captured.out
    assert "## Indicators" in captured.out
    assert "## Classification" in captured.out
    assert "## Data Quality" in captured.out
    assert "## Coach-Safe Summary" in captured.out
    assert "## Source Facts" in captured.out
    assert "Sleep" in captured.out
    assert "Energy" in captured.out
    assert "Soreness" in captured.out
    assert "Body Weight" in captured.out
    assert "Check-in Consistency" in captured.out


def test_json_mode_prints_valid_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        tool,
        "build_recovery_intelligence_v2",
        lambda user_id, target_date=None: _summary(),
    )

    exit_code = tool.main(["--user-id", "102", "--date", "2026-06-14", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["user_id"] == 102
    assert payload["target_date"] == "2026-06-14"
    assert payload["data_quality"]["status"] == "usable"
    assert payload["confidence"] == "Moderate"
    assert payload["source_facts"]
    assert not captured.err


def test_json_mode_redirects_service_stdout_to_stderr(monkeypatch, capsys) -> None:
    def fake_build(user_id: int, target_date: str | None = None):
        print("Using database: /tmp/fitness_ai.db")
        return _summary()

    monkeypatch.setattr(tool, "build_recovery_intelligence_v2", fake_build)

    exit_code = tool.main(["--user-id", "102", "--date", "2026-06-14", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["user_id"] == 102
    assert "Using database:" not in captured.out
    assert "Using database:" in captured.err


def test_compact_mode_prints_shorter_summary(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        tool,
        "build_recovery_intelligence_v2",
        lambda user_id, target_date=None: _summary(),
    )

    exit_code = tool.main(["--user-id", "102", "--compact", "--hide-source-facts"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Readiness Classification: supportive" in captured.out
    assert "Recovery Pressure: low" in captured.out
    assert "Source Facts:" not in captured.out


def test_invalid_user_id_argument_fails_safely() -> None:
    with pytest.raises(SystemExit) as excinfo:
        tool.main(["--user-id", "abc", "--date", "2026-06-14"])

    assert excinfo.value.code == 2


def test_invalid_date_argument_fails_safely() -> None:
    with pytest.raises(SystemExit) as excinfo:
        tool.main(["--user-id", "102", "--date", "06/14/2026"])

    assert excinfo.value.code == 2


def test_no_raw_sql_debug_rows_or_private_payloads_in_text(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        tool,
        "build_recovery_intelligence_v2",
        lambda user_id, target_date=None: _summary(),
    )

    tool.main(["--user-id", "102", "--date", "2026-06-14"])

    output = capsys.readouterr().out.lower()
    assert "select *" not in output
    assert "raw" not in output
    assert "api_key" not in output
    assert "authorization" not in output
    assert "provider_payload" not in output
    assert "ollama" not in output
    assert "crewai" not in output


def test_tool_uses_service_function_not_duplicate_calculation(
    monkeypatch, capsys
) -> None:
    calls = {"count": 0}

    def fake_build(user_id: int, target_date: str | None = None):
        calls["count"] += 1
        return _summary()

    monkeypatch.setattr(tool, "build_recovery_intelligence_v2", fake_build)

    exit_code = tool.main(["--user-id", "102", "--date", "2026-06-14"])

    assert exit_code == 0
    assert calls["count"] == 1
    assert "Recovery Intelligence v2 Inspection" in capsys.readouterr().out
