from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import dev_recovery_intelligence_v2_seed_matrix as matrix


class FakeSummary:
    def __init__(self, payload: dict):
        self._payload = payload

    def to_dict(self) -> dict:
        return self._payload


def _payload(
    *,
    user_id: int = 102,
    readiness: str = "supportive",
    pressure: str = "low",
    confidence: str = "Moderate",
    data_status: str = "usable",
    data_confidence: str = "Moderate",
    missing_current: bool = False,
    duplicate_days: int = 1,
    reason_codes: list[str] | None = None,
    limitations: list[str] | None = None,
    body_weight_value: float | None = 200.5,
) -> dict:
    current_value = None if missing_current else 7.2
    return {
        "user_id": user_id,
        "target_date": "2026-06-14",
        "readiness_classification": readiness,
        "recovery_pressure": pressure,
        "fatigue_support": (
            "supportive" if readiness in {"supportive", "improving"} else "mixed"
        ),
        "confidence": confidence,
        "data_quality": {
            "expected_days": 28,
            "checkin_days": 21 if data_status != "missing" else 0,
            "checkin_rate": 0.75 if data_status != "missing" else 0.0,
            "missing_sleep_days": 1 if missing_current else 0,
            "missing_energy_days": 1 if missing_current else 0,
            "missing_soreness_days": 1 if missing_current else 0,
            "duplicate_days_collapsed": duplicate_days,
            "stale_current_day": False,
            "status": data_status,
            "confidence": data_confidence,
            "reason_codes": reason_codes or [],
            "limitations": limitations or [],
        },
        "reason_codes": reason_codes or [],
        "limitations": limitations or [],
        "coach_safe_summary": "Recent recovery indicators remain bounded and descriptive.",
        "source_facts": [
            {
                "source_table": "daily_checkins",
                "field_name": "sleep_hours",
                "observed_date": "2026-06-14",
                "value_summary": "sleep hours present for current day",
                "confidence": data_confidence,
            }
        ],
        "sleep_interpretation": _indicator("sleep", current_value=current_value),
        "energy_interpretation": _indicator("energy", current_value=current_value),
        "soreness_interpretation": _indicator("soreness", current_value=current_value),
        "body_weight_interpretation": _indicator(
            "body_weight", current_value=body_weight_value
        ),
        "checkin_consistency": _indicator("checkin_consistency", current_value=0.75),
    }


def _indicator(indicator_name: str, *, current_value: float | None) -> dict:
    return {
        "indicator_name": indicator_name,
        "status": "unknown" if current_value is None else "normal",
        "trend_direction": "unknown" if current_value is None else "stable",
        "current_value": current_value,
        "baseline_value": None if current_value is None else current_value,
        "recent_average": None if current_value is None else current_value,
        "prior_average": None if current_value is None else current_value,
        "delta_from_baseline": None,
        "delta_recent_vs_prior": None,
        "confidence": "Limited" if current_value is None else "Moderate",
        "reason_codes": ["missing_current_value"] if current_value is None else [],
        "limitations": ["Current value is missing."] if current_value is None else [],
    }


def _fake_build(user_id: int, target_date: str | None = None) -> FakeSummary:
    if user_id == 101:
        return FakeSummary(
            _payload(user_id=user_id, readiness="recovery_limited", pressure="high")
        )
    if user_id == 103:
        return FakeSummary(
            _payload(user_id=user_id, readiness="mixed", pressure="moderate")
        )
    if user_id == 104:
        return FakeSummary(
            _payload(user_id=user_id, readiness="improving", pressure="low")
        )
    if user_id == 105:
        return FakeSummary(
            _payload(
                user_id=user_id,
                readiness="unknown",
                pressure="unknown",
                confidence="Limited",
                data_status="limited",
                data_confidence="Limited",
                missing_current=True,
                reason_codes=["limited_seed_coverage"],
                limitations=["Seed data is limited for this scenario."],
            )
        )
    return FakeSummary(_payload(user_id=user_id))


def test_seed_matrix_tool_imports_successfully() -> None:
    assert (
        matrix.MATRIX_VERSION == "recovery_intelligence_v2_qa_seed_matrix_validation_v1"
    )


def test_seed_matrix_help_exits_successfully(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        matrix.main(["--help"])

    captured = capsys.readouterr()
    assert excinfo.value.code == 0
    assert (
        "Developer-only Recovery Intelligence v2 QA seed matrix runner" in captured.out
    )


def test_default_text_output_prints_expected_sections(monkeypatch, capsys) -> None:
    monkeypatch.setattr(matrix, "build_recovery_intelligence_v2", _fake_build)

    exit_code = matrix.main(["--date", "2026-06-14"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# Recovery Intelligence v2 Seed Matrix" in captured.out
    assert "Baseline Commit" in captured.out
    assert "Target Date: 2026-06-14" in captured.out
    assert "Scenario Count: 8" in captured.out
    assert "## Pass / Fail Summary" in captured.out
    assert "## Scenario Results" in captured.out
    assert "supportive_recovery" in captured.out
    assert "Per-Scenario" not in captured.out


def test_json_emits_valid_json_only(monkeypatch, capsys) -> None:
    def fake_build_with_banner(user_id: int, target_date: str | None = None):
        print("Using database: /tmp/fitness_ai.db")
        return _fake_build(user_id, target_date)

    monkeypatch.setattr(
        matrix, "build_recovery_intelligence_v2", fake_build_with_banner
    )

    exit_code = matrix.main(["--date", "2026-06-14", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert captured.out.lstrip().startswith("{")
    assert "Using database" not in captured.out
    assert "Using database" in captured.err
    assert payload["scenario_count"] == 8
    assert payload["target_date"] == "2026-06-14"
    assert payload["summary"]["fail_count"] == 0


def test_scenario_labels_and_required_result_fields_are_present(monkeypatch) -> None:
    monkeypatch.setattr(matrix, "build_recovery_intelligence_v2", _fake_build)

    payload = matrix.build_seed_matrix(target_date="2026-06-14")

    labels = {result["label"] for result in payload["scenarios"]}
    assert labels == {
        "supportive_recovery",
        "recovery_limited_high_pressure",
        "manageable_mixed_signals",
        "improving_trend",
        "limited_data_missing_checkins",
        "messy_duplicates_same_day",
        "missing_sleep_energy_soreness",
        "body_weight_present_without_overclaiming",
    }
    for result in payload["scenarios"]:
        assert "readiness_classification" in result
        assert "recovery_pressure" in result
        assert "confidence" in result
        assert "data_quality" in result
        assert "reason_codes" in result
        assert "limitations" in result
        assert "source_facts" in result


def test_limited_data_scenario_has_reason_codes_or_limitations(monkeypatch) -> None:
    monkeypatch.setattr(matrix, "build_recovery_intelligence_v2", _fake_build)

    payload = matrix.build_seed_matrix(target_date="2026-06-14")
    limited = _scenario(payload, "limited_data_missing_checkins")

    assert limited["confidence"] == "Limited"
    assert limited["data_quality"]["confidence"] == "Limited"
    assert limited["reason_codes"] or limited["limitations"]
    assert limited["status"] in {"pass", "warn"}


def test_missing_values_remain_none_rather_than_zero(monkeypatch) -> None:
    monkeypatch.setattr(matrix, "build_recovery_intelligence_v2", _fake_build)

    payload = matrix.build_seed_matrix(target_date="2026-06-14")
    missing = _scenario(payload, "missing_sleep_energy_soreness")

    indicators = missing["indicator_snapshot"]
    assert indicators["sleep"]["current_value"] is None
    assert indicators["energy"]["current_value"] is None
    assert indicators["soreness"]["current_value"] is None
    assert "missing_numeric_value_coerced_to_zero" not in missing["failures"]


def test_duplicate_same_day_metric_is_reported(monkeypatch) -> None:
    monkeypatch.setattr(matrix, "build_recovery_intelligence_v2", _fake_build)

    payload = matrix.build_seed_matrix(target_date="2026-06-14")
    duplicate = _scenario(payload, "messy_duplicates_same_day")

    assert "duplicate_days_collapsed" in duplicate["data_quality"]
    assert duplicate["data_quality"]["duplicate_days_collapsed"] >= 0
    assert duplicate["status"] in {"pass", "warn"}


def test_body_weight_scenario_avoids_unsupported_causation_language(
    monkeypatch,
) -> None:
    monkeypatch.setattr(matrix, "build_recovery_intelligence_v2", _fake_build)

    payload = matrix.build_seed_matrix(target_date="2026-06-14")
    body_weight = _scenario(payload, "body_weight_present_without_overclaiming")
    text = json.dumps(body_weight).lower()

    assert body_weight["indicator_snapshot"]["body_weight"] is not None
    assert "fat loss" not in text
    assert "fat gain" not in text
    assert "this caused" not in text
    assert not body_weight["failures"]


def test_tool_calls_existing_service_boundary_for_each_scenario(monkeypatch) -> None:
    calls: list[tuple[int, str | None]] = []

    def fake_build(user_id: int, target_date: str | None = None):
        calls.append((user_id, target_date))
        return _fake_build(user_id, target_date)

    monkeypatch.setattr(matrix, "build_recovery_intelligence_v2", fake_build)

    payload = matrix.build_seed_matrix(target_date="2026-06-14")

    assert len(calls) == payload["scenario_count"]
    assert all(target_date == "2026-06-14" for _, target_date in calls)


def test_no_provider_calls_or_database_mutation_in_tool_source() -> None:
    source = Path(matrix.__file__).read_text(encoding="utf-8").lower()

    assert "import ollama" not in source
    assert "import crewai" not in source
    assert "import openai" not in source
    assert "from ollama" not in source
    assert "from crewai" not in source
    assert "from openai" not in source
    assert 'execute("insert' not in source
    assert 'execute("update' not in source
    assert 'execute("delete' not in source
    assert "create table" not in source
    assert "drop table" not in source


def test_write_report_creates_markdown_report(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(matrix, "build_recovery_intelligence_v2", _fake_build)

    exit_code = matrix.main(
        [
            "--date",
            "2026-06-14",
            "--write-report",
            "--output-dir",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Report Path:" in captured.out
    reports = list(tmp_path.glob("recovery_intelligence_v2_seed_matrix_*/qa_report.md"))
    assert len(reports) == 1
    report = reports[0].read_text(encoding="utf-8")
    assert "# Recovery Intelligence v2 Seed Matrix" in report


def test_invalid_date_argument_fails_safely() -> None:
    with pytest.raises(SystemExit) as excinfo:
        matrix.main(["--date", "06/14/2026"])

    assert excinfo.value.code == 2


def _scenario(payload: dict, label: str) -> dict:
    for result in payload["scenarios"]:
        if result["label"] == label:
            return result
    raise AssertionError(f"Missing scenario: {label}")
