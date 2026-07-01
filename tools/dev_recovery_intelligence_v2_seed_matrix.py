from __future__ import annotations

import argparse
import json
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.recovery_intelligence_v2_service import (  # noqa: E402
    build_recovery_intelligence_v2,
)

ACCEPTED_BASELINE_COMMIT = "f50a1cb"
MATRIX_VERSION = "recovery_intelligence_v2_qa_seed_matrix_validation_v1"

FORBIDDEN_OUTPUT_TERMS = (
    "overtraining",
    "injury",
    "illness",
    "diagnosis",
    "sleep disorder",
    "medical risk",
    "forced deload",
    "automatic deload",
    "must deload",
    "fat-loss",
    "fat loss",
    "fat-gain",
    "fat gain",
    "nutrition blame",
    "this caused",
)

RAW_DEBUG_TERMS = (
    "select *",
    "raw sql",
    "raw database",
    "raw row",
    "private notes",
    "provider_payload",
    "api_key",
    "authorization",
    "bearer ",
    "ollama",
    "crewai",
)


@dataclass(frozen=True)
class SeedScenario:
    label: str
    user_id: int
    purpose: str
    expected_readiness: frozenset[str] = frozenset()
    expected_pressure: frozenset[str] = frozenset()
    require_reason_or_limitation_when_limited: bool = False
    require_missing_values_explicit: bool = False
    require_duplicate_metric: bool = False
    require_body_weight_context: bool = False


SCENARIOS: tuple[SeedScenario, ...] = (
    SeedScenario(
        label="supportive_recovery",
        user_id=102,
        purpose="Adequate check-ins with supportive recovery context.",
        expected_readiness=frozenset({"supportive", "improving"}),
        expected_pressure=frozenset({"low", "moderate"}),
    ),
    SeedScenario(
        label="recovery_limited_high_pressure",
        user_id=101,
        purpose="High-pressure recovery context remains descriptive and bounded.",
        expected_readiness=frozenset({"recovery_limited", "manageable", "mixed"}),
        expected_pressure=frozenset({"high", "moderate"}),
    ),
    SeedScenario(
        label="manageable_mixed_signals",
        user_id=103,
        purpose="Mixed recovery indicators remain explainable without overclaiming.",
        expected_readiness=frozenset({"manageable", "mixed", "recovery_limited"}),
        expected_pressure=frozenset({"low", "moderate", "high"}),
    ),
    SeedScenario(
        label="improving_trend",
        user_id=104,
        purpose="Improving trend evidence can appear without overstating cause.",
        expected_readiness=frozenset(
            {"improving", "supportive", "manageable", "mixed"}
        ),
        expected_pressure=frozenset({"low", "moderate"}),
    ),
    SeedScenario(
        label="limited_data_missing_checkins",
        user_id=105,
        purpose="Limited or missing check-in coverage stays low-confidence and explicit.",
        require_reason_or_limitation_when_limited=True,
    ),
    SeedScenario(
        label="messy_duplicates_same_day",
        user_id=101,
        purpose="Duplicate same-day handling remains visible and does not crash.",
        require_duplicate_metric=True,
    ),
    SeedScenario(
        label="missing_sleep_energy_soreness",
        user_id=105,
        purpose="Missing numeric recovery indicators remain explicit None values, not zero.",
        require_missing_values_explicit=True,
        require_reason_or_limitation_when_limited=True,
    ),
    SeedScenario(
        label="body_weight_present_without_overclaiming",
        user_id=102,
        purpose="Body weight can be included as context without causation claims.",
        require_body_weight_context=True,
    ),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Developer-only Recovery Intelligence v2 QA seed matrix runner."
    )
    parser.add_argument(
        "--date",
        dest="target_date",
        type=_parse_cli_date,
        default=None,
        help="Target date in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print seed matrix results as valid formatted JSON only.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print shorter terminal-readable output.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write qa-runs/recovery_intelligence_v2_seed_matrix_<timestamp>/qa_report.md.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("qa-runs"),
        help="Directory for optional --write-report output. Defaults to qa-runs.",
    )
    args = parser.parse_args(argv)

    target_date = args.target_date or date.today().isoformat()

    with redirect_stdout(sys.stderr):
        payload = build_seed_matrix(target_date=target_date)

    if args.write_report:
        report_path = _write_report(payload, output_dir=args.output_dir)
        payload["report_path"] = str(report_path)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.compact:
        print(_render_compact_text(payload))
    else:
        print(_render_text_report(payload))
    return 0


def build_seed_matrix(*, target_date: str) -> dict[str, Any]:
    generated_at = datetime.now(UTC).isoformat()
    results = [
        _run_scenario(scenario, target_date=target_date) for scenario in SCENARIOS
    ]
    summary = _summarize_results(results)
    return {
        "matrix_version": MATRIX_VERSION,
        "baseline_commit": ACCEPTED_BASELINE_COMMIT,
        "target_date": target_date,
        "generated_at": generated_at,
        "scenario_count": len(SCENARIOS),
        "scenario_labels": [scenario.label for scenario in SCENARIOS],
        "summary": summary,
        "scenarios": results,
    }


def _run_scenario(scenario: SeedScenario, *, target_date: str) -> dict[str, Any]:
    warnings: list[str] = []
    failures: list[str] = []
    payload: dict[str, Any] | None = None

    try:
        summary = build_recovery_intelligence_v2(
            user_id=scenario.user_id,
            target_date=target_date,
        )
        payload = summary.to_dict()
    except Exception as exc:  # pragma: no cover - guarded by CLI behavior tests
        return {
            "label": scenario.label,
            "user_id": scenario.user_id,
            "purpose": scenario.purpose,
            "status": "fail",
            "error": f"{type(exc).__name__}: {exc}",
            "warnings": warnings,
            "failures": ["scenario_service_call_failed"],
        }

    data_quality = payload.get("data_quality") or {}
    readiness = payload.get("readiness_classification")
    pressure = payload.get("recovery_pressure")
    confidence = payload.get("confidence")
    reason_codes = payload.get("reason_codes") or []
    limitations = payload.get("limitations") or []
    source_facts = payload.get("source_facts") or []
    coach_safe_summary = payload.get("coach_safe_summary") or ""
    body_weight = payload.get("body_weight_interpretation") or {}

    _validate_payload_shape(payload, failures)
    _validate_safe_public_text(payload, failures)
    _validate_expected_labels(scenario, payload, warnings)

    if scenario.require_reason_or_limitation_when_limited and confidence in {
        "Limited",
        "Low",
    }:
        if not (reason_codes or limitations):
            failures.append("limited_confidence_without_reason_codes_or_limitations")

    if scenario.require_missing_values_explicit:
        _validate_missing_values_explicit(payload, warnings, failures)

    if scenario.require_duplicate_metric:
        if "duplicate_days_collapsed" not in data_quality:
            failures.append("duplicate_days_collapsed_missing")

    if scenario.require_body_weight_context:
        if body_weight is None:
            failures.append("body_weight_interpretation_missing")
        elif "current_value" not in body_weight:
            failures.append("body_weight_current_value_missing")

    if data_quality.get("status") == "missing":
        warnings.append("scenario_seed_data_missing_or_unavailable")
    elif data_quality.get("status") in {"limited", "partial"}:
        warnings.append("scenario_seed_data_limited_or_partial")

    status = "fail" if failures else "warn" if warnings else "pass"
    return {
        "label": scenario.label,
        "user_id": scenario.user_id,
        "purpose": scenario.purpose,
        "status": status,
        "readiness_classification": readiness,
        "recovery_pressure": pressure,
        "fatigue_support": payload.get("fatigue_support"),
        "confidence": confidence,
        "data_quality": data_quality,
        "reason_codes": reason_codes,
        "limitations": limitations,
        "coach_safe_summary": coach_safe_summary,
        "source_fact_count": len(source_facts),
        "source_facts": source_facts,
        "indicator_snapshot": {
            "sleep": _indicator_snapshot(payload.get("sleep_interpretation")),
            "energy": _indicator_snapshot(payload.get("energy_interpretation")),
            "soreness": _indicator_snapshot(payload.get("soreness_interpretation")),
            "body_weight": _indicator_snapshot(body_weight),
            "checkin_consistency": _indicator_snapshot(
                payload.get("checkin_consistency")
            ),
        },
        "warnings": _unique(warnings),
        "failures": _unique(failures),
    }


def _validate_payload_shape(payload: dict[str, Any], failures: list[str]) -> None:
    required = {
        "user_id",
        "target_date",
        "readiness_classification",
        "recovery_pressure",
        "confidence",
        "data_quality",
        "source_facts",
        "reason_codes",
        "limitations",
    }
    missing = sorted(required.difference(payload))
    if missing:
        failures.append("payload_missing_required_keys:" + ",".join(missing))
    data_quality = payload.get("data_quality") or {}
    for key in (
        "status",
        "confidence",
        "checkin_days",
        "missing_sleep_days",
        "missing_energy_days",
        "missing_soreness_days",
        "duplicate_days_collapsed",
    ):
        if key not in data_quality:
            failures.append(f"data_quality_missing_{key}")


def _validate_safe_public_text(payload: dict[str, Any], failures: list[str]) -> None:
    text = json.dumps(payload, sort_keys=True).lower()
    for term in FORBIDDEN_OUTPUT_TERMS:
        if term in text:
            failures.append(f"forbidden_recovery_language:{term}")
    for term in RAW_DEBUG_TERMS:
        if term in text:
            failures.append(f"raw_debug_or_provider_term:{term}")


def _validate_expected_labels(
    scenario: SeedScenario, payload: dict[str, Any], warnings: list[str]
) -> None:
    readiness = payload.get("readiness_classification")
    pressure = payload.get("recovery_pressure")
    data_quality = payload.get("data_quality") or {}
    if data_quality.get("status") == "missing":
        return
    if scenario.expected_readiness and readiness not in scenario.expected_readiness:
        warnings.append(
            "readiness_outside_expected_range:"
            f"{readiness};expected={sorted(scenario.expected_readiness)}"
        )
    if scenario.expected_pressure and pressure not in scenario.expected_pressure:
        warnings.append(
            "pressure_outside_expected_range:"
            f"{pressure};expected={sorted(scenario.expected_pressure)}"
        )


def _validate_missing_values_explicit(
    payload: dict[str, Any], warnings: list[str], failures: list[str]
) -> None:
    data_quality = payload.get("data_quality") or {}
    missing_counts = [
        data_quality.get("missing_sleep_days"),
        data_quality.get("missing_energy_days"),
        data_quality.get("missing_soreness_days"),
    ]
    if any(value is None for value in missing_counts):
        failures.append("missing_field_counts_not_populated")
    indicators = [
        payload.get("sleep_interpretation") or {},
        payload.get("energy_interpretation") or {},
        payload.get("soreness_interpretation") or {},
    ]
    if any(indicator.get("current_value") == 0 for indicator in indicators):
        failures.append("missing_numeric_value_coerced_to_zero")
    if not any(indicator.get("current_value") is None for indicator in indicators):
        warnings.append("missing_value_scenario_has_no_current_missing_numeric_values")


def _indicator_snapshot(indicator: dict[str, Any] | None) -> dict[str, Any] | None:
    if not indicator:
        return None
    return {
        "status": indicator.get("status"),
        "trend_direction": indicator.get("trend_direction"),
        "current_value": indicator.get("current_value"),
        "baseline_value": indicator.get("baseline_value"),
        "recent_average": indicator.get("recent_average"),
        "prior_average": indicator.get("prior_average"),
        "confidence": indicator.get("confidence"),
        "reason_codes": indicator.get("reason_codes") or [],
        "limitations": indicator.get("limitations") or [],
    }


def _summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    pass_count = sum(1 for result in results if result.get("status") == "pass")
    warn_count = sum(1 for result in results if result.get("status") == "warn")
    fail_count = sum(1 for result in results if result.get("status") == "fail")
    return {
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "overall_status": "fail" if fail_count else "warn" if warn_count else "pass",
    }


def _parse_cli_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must use YYYY-MM-DD format") from exc


def _render_text_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Recovery Intelligence v2 Seed Matrix",
        "",
        f"Baseline Commit: {payload['baseline_commit']}",
        f"Target Date: {payload['target_date']}",
        f"Generated At: {payload['generated_at']}",
        f"Scenario Count: {payload['scenario_count']}",
        "",
        "## Pass / Fail Summary",
        f"Overall Status: {summary['overall_status']}",
        f"Pass: {summary['pass_count']}",
        f"Warn: {summary['warn_count']}",
        f"Fail: {summary['fail_count']}",
        "",
        "## Scenario Results",
    ]
    for result in payload["scenarios"]:
        lines.extend(_render_scenario(result, compact=False))
    if payload.get("report_path"):
        lines.extend(["", f"Report Path: {payload['report_path']}"])
    return "\n".join(lines).rstrip() + "\n"


def _render_compact_text(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "Recovery Intelligence v2 Seed Matrix",
        f"Baseline Commit: {payload['baseline_commit']}",
        f"Target Date: {payload['target_date']}",
        f"Scenario Count: {payload['scenario_count']}",
        (
            "Pass / Warn / Fail: "
            f"{summary['pass_count']} / {summary['warn_count']} / {summary['fail_count']}"
        ),
    ]
    for result in payload["scenarios"]:
        lines.extend(_render_scenario(result, compact=True))
    if payload.get("report_path"):
        lines.append(f"Report Path: {payload['report_path']}")
    return "\n".join(lines).rstrip() + "\n"


def _render_scenario(result: dict[str, Any], *, compact: bool) -> list[str]:
    data_quality = result.get("data_quality") or {}
    lines = [
        "",
        f"### {result['label']}" if not compact else f"- {result['label']}",
        f"Status: {result['status']}",
        f"User ID: {result['user_id']}",
        f"Readiness Classification: {result.get('readiness_classification')}",
        f"Recovery Pressure: {result.get('recovery_pressure')}",
        f"Confidence: {result.get('confidence')}",
        f"Data Quality: {data_quality.get('status')} / {data_quality.get('confidence')}",
    ]
    if compact:
        return lines
    lines.extend(
        [
            f"Purpose: {result['purpose']}",
            f"Reason Codes: {_join_or_none(result.get('reason_codes'))}",
            f"Limitations: {_join_or_none(result.get('limitations'))}",
            f"Warnings: {_join_or_none(result.get('warnings'))}",
            f"Failures: {_join_or_none(result.get('failures'))}",
            f"Source Facts: {result.get('source_fact_count')}",
            f"Coach-Safe Summary: {result.get('coach_safe_summary') or 'None reported.'}",
        ]
    )
    return lines


def _write_report(payload: dict[str, Any], *, output_dir: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_dir = output_dir / f"recovery_intelligence_v2_seed_matrix_{timestamp}"
    report_dir.mkdir(parents=True, exist_ok=False)
    report_path = report_dir / "qa_report.md"
    report_payload = dict(payload)
    report_payload["report_path"] = str(report_path)
    report_path.write_text(_render_text_report(report_payload), encoding="utf-8")
    return report_path


def _join_or_none(values: list[str] | None) -> str:
    if not values:
        return "None"
    return ", ".join(values)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
