from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_coach_intelligence_snapshot_service import (  # noqa: E402
    build_daily_coach_intelligence_snapshot,
)

DEFAULT_OUTPUT_DIR = "docs/provider_trials/daily_coach_workout_set_intelligence_v1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Developer-only Daily Coach Intelligence Snapshot + "
            "Recovery + Workout Set Intelligence v1 tool."
        )
    )
    parser.add_argument("--user-id", type=int, default=None)
    parser.add_argument("--users", default=None, help="Comma-separated user ids")
    parser.add_argument("--target-date", default=None)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--write-json", action="store_true")
    parser.add_argument("--write-markdown", action="store_true")
    parser.add_argument("--write-pasteback-report", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    args = parser.parse_args(argv)

    user_ids = _resolve_user_ids(args.user_id, args.users)
    output_dir = Path(args.output_dir)
    snapshots = [
        build_daily_coach_intelligence_snapshot(
            user_id=user_id,
            target_date=args.target_date,
        )
        for user_id in user_ids
    ]
    payloads = [snapshot.to_dict() for snapshot in snapshots]

    if args.write_json or args.write_markdown or args.write_pasteback_report:
        output_dir.mkdir(parents=True, exist_ok=True)
        if args.write_json:
            _write_json_artifacts(output_dir, payloads)
        if args.write_markdown:
            _write_markdown_artifacts(output_dir, payloads)
        if args.write_pasteback_report:
            _write_pasteback_report(output_dir, payloads)

    if args.json:
        print(
            json.dumps(
                payloads[0] if len(payloads) == 1 else payloads,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"Daily Coach Intelligence Snapshot runs: {len(payloads)}")
        print(f"Output dir: {output_dir}")
        for payload in payloads:
            recovery = payload.get("recovery_intelligence") or {}
            workout = payload.get("workout_set_intelligence") or {}
            print(
                f"user={payload['user_id']} date={payload['target_date']} "
                f"recovery={recovery.get('readiness_level')} "
                f"fatigue={recovery.get('fatigue_risk')} "
                f"workout_completion={workout.get('overall_completion_indicator')} "
                f"workout_effort={workout.get('overall_effort_indicator')} "
                f"confidence={workout.get('confidence') or recovery.get('confidence')}"
            )
        if args.write_pasteback_report:
            print(f"Pasteback report: {output_dir / 'pasteback_report.md'}")

    return 0


def _resolve_user_ids(user_id: int | None, users: str | None) -> list[int]:
    if users:
        resolved = [int(value.strip()) for value in users.split(",") if value.strip()]
        if not resolved:
            raise ValueError("--users did not contain any user ids")
        return resolved
    if user_id is not None:
        return [int(user_id)]
    raise SystemExit("Use --user-id or --users")


def _write_json_artifacts(output_dir: Path, payloads: list[dict[str, Any]]) -> None:
    content: dict[str, Any] | list[dict[str, Any]]
    content = payloads[0] if len(payloads) == 1 else {"snapshots": payloads}
    (output_dir / "daily_coach_intelligence_snapshot.json").write_text(
        json.dumps(content, indent=2, sort_keys=True), encoding="utf-8"
    )
    if len(payloads) > 1:
        for payload in payloads:
            user_path = (
                output_dir
                / f"user_{payload['user_id']}_daily_coach_intelligence_snapshot.json"
            )
            user_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
            )


def _write_markdown_artifacts(output_dir: Path, payloads: list[dict[str, Any]]) -> None:
    (output_dir / "daily_coach_intelligence_snapshot.md").write_text(
        _render_snapshot_markdown(payloads), encoding="utf-8"
    )
    (output_dir / "backend_intelligence_gap_report.md").write_text(
        _render_gap_report(payloads), encoding="utf-8"
    )
    (output_dir / "data_completeness_summary.md").write_text(
        _render_data_completeness(payloads), encoding="utf-8"
    )
    (output_dir / "workout_set_intelligence_summary.md").write_text(
        _render_workout_set_summary(payloads), encoding="utf-8"
    )


def _write_pasteback_report(output_dir: Path, payloads: list[dict[str, Any]]) -> None:
    (output_dir / "pasteback_report.md").write_text(
        _render_pasteback_report(payloads), encoding="utf-8"
    )


def _render_snapshot_markdown(payloads: list[dict[str, Any]]) -> str:
    lines = ["# Daily Coach Intelligence Snapshot", ""]
    for payload in payloads:
        recovery = payload.get("recovery_intelligence") or {}
        lines.extend(
            [
                f"## User {payload['user_id']} — {payload['target_date']}",
                "",
                f"Snapshot version: `{payload['snapshot_version']}`",
                "",
                "### Recovery Intelligence",
                "",
                f"- Readiness: `{recovery.get('readiness_level')}`",
                f"- Fatigue risk: `{recovery.get('fatigue_risk')}`",
                f"- Confidence: `{recovery.get('confidence')}`",
                f"- Coach-safe summary: {recovery.get('coach_safe_summary')}",
                "",
                "### Workout Set Intelligence",
                "",
                f"- Completion indicator: `{(payload.get('workout_set_intelligence') or {}).get('overall_completion_indicator')}`",
                f"- Effort indicator: `{(payload.get('workout_set_intelligence') or {}).get('overall_effort_indicator')}`",
                f"- Rep range indicator: `{(payload.get('workout_set_intelligence') or {}).get('overall_rep_range_indicator')}`",
                f"- Logging quality: `{(payload.get('workout_set_intelligence') or {}).get('overall_logging_quality')}`",
                f"- Confidence: `{(payload.get('workout_set_intelligence') or {}).get('confidence')}`",
                "",
                "### Foundation Layer Status",
                "",
            ]
        )
        for layer, status in payload.get("foundation_layer_status", {}).items():
            lines.append(f"- {layer}: `{status}`")
        lines.extend(["", "### Source Data Gaps", ""])
        gaps = payload.get("source_data_gaps") or [
            "No major source-data gaps reported."
        ]
        for gap in gaps:
            lines.append(f"- {gap}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_gap_report(payloads: list[dict[str, Any]]) -> str:
    lines = ["# Backend Intelligence Gap Report", ""]
    lines.append(
        "This report is read-only and does not authorize provider, UI, "
        "schema, or runtime behavior changes."
    )
    lines.append("")
    for payload in payloads:
        lines.append(f"## User {payload['user_id']}")
        for gap in payload.get("source_data_gaps") or []:
            lines.append(f"- {gap}")
        lines.append("")
    lines.extend(
        [
            "## Foundation status",
            "",
            "- Recovery Intelligence: implemented v1 in this milestone.",
            "- Workout Set Intelligence: implemented v1 as a read-only set-aware source-data layer.",
            "- Trend Engine: not implemented; existing nutrition trend only.",
            "- Six-Month Seed Data: existing QA seed data only.",
            "- Food Knowledge Expansion: pending.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _render_data_completeness(payloads: list[dict[str, Any]]) -> str:
    lines = ["# Data Completeness Summary", ""]
    for payload in payloads:
        lines.append(f"## User {payload['user_id']} — {payload['target_date']}")
        for layer, status in payload.get("data_completeness", {}).items():
            lines.append(f"- {layer}: `{status}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_workout_set_summary(payloads: list[dict[str, Any]]) -> str:
    lines = ["# Workout Set Intelligence Summary", ""]
    lines.append(
        "This report is read-only and uses indicator terminology for set-aware training source data."
    )
    lines.append("")
    for payload in payloads:
        workout = payload.get("workout_set_intelligence") or {}
        lines.extend(
            [
                f"## User {payload['user_id']} — {payload['target_date']}",
                f"- Completion indicator: `{workout.get('overall_completion_indicator')}`",
                f"- Effort indicator: `{workout.get('overall_effort_indicator')}`",
                f"- Rep range indicator: `{workout.get('overall_rep_range_indicator')}`",
                f"- Logging quality: `{workout.get('overall_logging_quality')}`",
                f"- Confidence: `{workout.get('confidence')}`",
                f"- Completed planned executions: `{workout.get('completed_execution_count')}`",
                "",
            ]
        )
        facts = workout.get("source_facts") or []
        if facts:
            lines.append("### Source facts")
            for fact in facts:
                lines.append(f"- {fact}")
            lines.append("")
        exercises = workout.get("exercise_indicators") or []
        if exercises:
            lines.append("### Exercise indicators")
            for exercise in exercises[:8]:
                lines.append(
                    f"- {exercise.get('exercise_name')}: "
                    f"completion={exercise.get('completion_indicator')}, "
                    f"effort={exercise.get('effort_indicator')}, "
                    f"rep_range={exercise.get('rep_range_indicator')}, "
                    f"load={exercise.get('load_indicator')}, "
                    f"confidence={exercise.get('confidence')}"
                )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_pasteback_report(payloads: list[dict[str, Any]]) -> str:
    lines = ["# Daily Coach Intelligence Snapshot Pasteback", ""]
    lines.append("Status: developer-only read-only backend intelligence snapshot.")
    lines.append("Provider called: false")
    lines.append("Database mutated: false")
    lines.append("Normal Today behavior changed: false")
    lines.append("")
    for payload in payloads:
        recovery = payload.get("recovery_intelligence") or {}
        workout = payload.get("workout_set_intelligence") or {}
        lines.extend(
            [
                f"## User {payload['user_id']} — {payload['target_date']}",
                f"Recovery readiness: {recovery.get('readiness_level')}",
                f"Fatigue risk: {recovery.get('fatigue_risk')}",
                f"Recovery confidence: {recovery.get('confidence')}",
                f"Workout completion indicator: {workout.get('overall_completion_indicator')}",
                f"Workout effort indicator: {workout.get('overall_effort_indicator')}",
                f"Workout rep range indicator: {workout.get('overall_rep_range_indicator')}",
                f"Workout logging quality: {workout.get('overall_logging_quality')}",
                f"Workout confidence: {workout.get('confidence')}",
                f"Source services: {', '.join(payload.get('source_services') or [])}",
                "Source data gaps:",
            ]
        )
        gaps = payload.get("source_data_gaps") or ["None reported"]
        for gap in gaps:
            lines.append(f"- {gap}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
