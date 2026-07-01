from __future__ import annotations

import argparse
import json
import sys
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.recovery_intelligence_v2_service import (  # noqa: E402
    build_recovery_intelligence_v2,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Developer-only Recovery Intelligence v2 inspection tool."
    )
    parser.add_argument("--user-id", type=int, required=True)
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
        help="Print RecoveryIntelligenceV2Summary.to_dict() as formatted JSON.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print shorter terminal text for quick checks.",
    )
    source_facts_group = parser.add_mutually_exclusive_group()
    source_facts_group.add_argument(
        "--show-source-facts",
        action="store_true",
        default=True,
        help="Include public-safe source facts in text output. Default behavior.",
    )
    source_facts_group.add_argument(
        "--hide-source-facts",
        action="store_true",
        help="Hide public-safe source facts in text output.",
    )
    args = parser.parse_args(argv)

    if args.json:
        with redirect_stdout(sys.stderr):
            summary = build_recovery_intelligence_v2(
                user_id=args.user_id,
                target_date=args.target_date,
            )
    else:
        summary = build_recovery_intelligence_v2(
            user_id=args.user_id,
            target_date=args.target_date,
        )
    payload = summary.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    show_source_facts = not args.hide_source_facts
    if args.compact:
        print(_render_compact_text(payload, show_source_facts=show_source_facts))
    else:
        print(_render_text_report(payload, show_source_facts=show_source_facts))
    return 0


def _parse_cli_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must use YYYY-MM-DD format") from exc


def _render_compact_text(
    payload: dict[str, Any], *, show_source_facts: bool = True
) -> str:
    data_quality = payload.get("data_quality") or {}
    lines = [
        "Recovery Intelligence v2 Inspection",
        f"User ID: {payload.get('user_id')}",
        f"Target Date: {payload.get('target_date')}",
        f"Readiness Classification: {payload.get('readiness_classification')}",
        f"Recovery Pressure: {payload.get('recovery_pressure')}",
        f"Fatigue Support: {payload.get('fatigue_support')}",
        f"Confidence: {payload.get('confidence')}",
        f"Data Quality: {data_quality.get('status')} / {data_quality.get('confidence')}",
        f"Coach-Safe Summary: {_clean_inline(payload.get('coach_safe_summary'))}",
    ]
    if payload.get("reason_codes"):
        lines.append("Reason Codes: " + ", ".join(payload["reason_codes"]))
    if payload.get("limitations"):
        lines.append("Limitations: " + ", ".join(payload["limitations"]))
    if show_source_facts:
        lines.append(f"Source Facts: {len(payload.get('source_facts') or [])}")
    return "\n".join(lines).rstrip() + "\n"


def _render_text_report(
    payload: dict[str, Any], *, show_source_facts: bool = True
) -> str:
    lines: list[str] = [
        "# Recovery Intelligence v2 Inspection",
        "",
        f"User ID: {payload.get('user_id')}",
        f"Target Date: {payload.get('target_date')}",
        f"Model Version: {payload.get('model_version')}",
        f"Generated At: {payload.get('generated_at')}",
        "",
        "## Current Day",
    ]
    current_day = payload.get("current_day")
    if current_day:
        lines.extend(
            [
                f"Date: {current_day.get('date')}",
                f"Sleep Hours: {_fmt_value(current_day.get('sleep_hours'))}",
                f"Energy Level: {_fmt_value(current_day.get('energy_level'))}",
                f"Soreness Level: {_fmt_value(current_day.get('soreness_level'))}",
                f"Body Weight: {_fmt_value(current_day.get('body_weight_lb'))}",
                f"Notes Present: {current_day.get('notes_present')}",
                f"Data Quality Status: {current_day.get('data_quality_status')}",
            ]
        )
    else:
        lines.append("No current-day check-in found.")

    lines.extend(["", "## Baseline Window"])
    lines.extend(_render_baseline(payload.get("baseline")))

    lines.extend(["", "## Recent vs Baseline"])
    lines.extend(_render_delta(payload.get("recent_vs_baseline")))

    lines.extend(["", "## Recent vs Prior"])
    lines.extend(_render_delta(payload.get("recent_vs_prior")))

    lines.extend(["", "## Indicators"])
    for label, key in [
        ("Sleep", "sleep_interpretation"),
        ("Energy", "energy_interpretation"),
        ("Soreness", "soreness_interpretation"),
        ("Body Weight", "body_weight_interpretation"),
        ("Check-in Consistency", "checkin_consistency"),
    ]:
        lines.extend(_render_indicator(label, payload.get(key)))

    lines.extend(
        [
            "",
            "## Classification",
            f"Readiness Classification: {payload.get('readiness_classification')}",
            f"Recovery Pressure: {payload.get('recovery_pressure')}",
            f"Fatigue Support: {payload.get('fatigue_support')}",
            f"Confidence: {payload.get('confidence')}",
        ]
    )

    lines.extend(["", "## Data Quality"])
    lines.extend(_render_data_quality(payload.get("data_quality")))

    lines.extend(["", "## Reason Codes"])
    lines.extend(_render_list(payload.get("reason_codes")))

    lines.extend(["", "## Limitations"])
    lines.extend(_render_list(payload.get("limitations")))

    lines.extend(["", "## Coach-Safe Summary"])
    lines.append(_clean_inline(payload.get("coach_safe_summary")) or "None reported.")

    if show_source_facts:
        lines.extend(["", "## Source Facts"])
        lines.extend(_render_source_facts(payload.get("source_facts")))

    return "\n".join(lines).rstrip() + "\n"


def _render_baseline(baseline: dict[str, Any] | None) -> list[str]:
    if not baseline:
        return ["No baseline window available."]
    return [
        f"Window Days: {baseline.get('baseline_window_days')}",
        f"Start Date: {baseline.get('start_date')}",
        f"End Date: {baseline.get('end_date')}",
        f"Check-in Days: {baseline.get('checkin_days')}",
        f"Average Sleep Hours: {_fmt_value(baseline.get('average_sleep_hours'))}",
        f"Average Energy Level: {_fmt_value(baseline.get('average_energy_level'))}",
        f"Average Soreness Level: {_fmt_value(baseline.get('average_soreness_level'))}",
        f"Latest Body Weight: {_fmt_value(baseline.get('latest_body_weight_lb'))}",
        f"Confidence: {baseline.get('confidence')}",
    ]


def _render_delta(delta: dict[str, Any] | None) -> list[str]:
    if not delta:
        return ["No delta available."]
    return [
        f"Comparison: {delta.get('comparison_name')}",
        f"Recent Window Days: {delta.get('recent_window_days')}",
        f"Comparison Window Days: {delta.get('comparison_window_days')}",
        f"Sleep Delta: {_fmt_value(delta.get('sleep_delta'))}",
        f"Energy Delta: {_fmt_value(delta.get('energy_delta'))}",
        f"Soreness Delta: {_fmt_value(delta.get('soreness_delta'))}",
        f"Body Weight Delta: {_fmt_value(delta.get('body_weight_delta'))}",
        f"Trend Direction: {delta.get('trend_direction')}",
        f"Confidence: {delta.get('confidence')}",
    ]


def _render_indicator(label: str, indicator: dict[str, Any] | None) -> list[str]:
    if not indicator:
        return [f"- {label}: unavailable"]
    return [
        f"- {label}:",
        f"  - Status: {indicator.get('status')}",
        f"  - Trend Direction: {indicator.get('trend_direction')}",
        f"  - Current Value: {_fmt_value(indicator.get('current_value'))}",
        f"  - Baseline Value: {_fmt_value(indicator.get('baseline_value'))}",
        f"  - Recent Average: {_fmt_value(indicator.get('recent_average'))}",
        f"  - Prior Average: {_fmt_value(indicator.get('prior_average'))}",
        f"  - Delta From Baseline: {_fmt_value(indicator.get('delta_from_baseline'))}",
        f"  - Delta Recent vs Prior: {_fmt_value(indicator.get('delta_recent_vs_prior'))}",
        f"  - Confidence: {indicator.get('confidence')}",
    ]


def _render_data_quality(data_quality: dict[str, Any] | None) -> list[str]:
    if not data_quality:
        return ["No data quality section available."]
    return [
        f"Expected Days: {data_quality.get('expected_days')}",
        f"Check-in Days: {data_quality.get('checkin_days')}",
        f"Check-in Rate: {_fmt_value(data_quality.get('checkin_rate'))}",
        f"Missing Sleep Days: {data_quality.get('missing_sleep_days')}",
        f"Missing Energy Days: {data_quality.get('missing_energy_days')}",
        f"Missing Soreness Days: {data_quality.get('missing_soreness_days')}",
        f"Duplicate Days Collapsed: {data_quality.get('duplicate_days_collapsed')}",
        f"Status: {data_quality.get('status')}",
        f"Confidence: {data_quality.get('confidence')}",
    ]


def _render_source_facts(source_facts: list[dict[str, Any]] | None) -> list[str]:
    if not source_facts:
        return ["No source facts reported."]
    lines: list[str] = []
    for fact in source_facts:
        lines.append(
            "- "
            f"{fact.get('source_table')}.{fact.get('field_name')} "
            f"({fact.get('observed_date') or 'window'}): "
            f"{_clean_inline(fact.get('value_summary'))} "
            f"[confidence: {fact.get('confidence')}]"
        )
    return lines


def _render_list(values: list[str] | None) -> list[str]:
    if not values:
        return ["None reported."]
    return [f"- {_clean_inline(value)}" for value in values]


def _fmt_value(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _clean_inline(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").strip()


if __name__ == "__main__":
    raise SystemExit(main())
