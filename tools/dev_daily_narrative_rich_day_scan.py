from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_narrative_rich_day_service import (  # noqa: E402
    scan_daily_narrative_rich_days,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan seeded QA dates for Daily Narrative rich-day candidates."
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--user-id", type=int, help="QA user id to scan, usually 101-105."
    )
    scope.add_argument(
        "--all-qa-users",
        action="store_true",
        help="Scan all seeded QA users 101-105.",
    )
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of a compact table.",
    )
    return parser.parse_args()


def _render_table(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "No Daily Narrative candidate days found."
    columns = [
        "user_id",
        "date",
        "richness_score",
        "recovery_checkins_count",
        "nutrition_entries_count",
        "workout_sessions_count",
        "planned_workouts_count",
        "planned_exercises_count",
        "actual_sets_count",
        "data_quality_label",
        "recommended_test_label",
    ]
    widths = {
        column: max(len(column), *(len(str(row.get(column, ""))) for row in rows))
        for column in columns
    }
    header = " | ".join(column.ljust(widths[column]) for column in columns)
    divider = "-+-".join("-" * widths[column] for column in columns)
    lines = [header, divider]
    for row in rows:
        lines.append(
            " | ".join(
                str(row.get(column, "")).ljust(widths[column]) for column in columns
            )
        )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    result = scan_daily_narrative_rich_days(
        user_id=None if args.all_qa_users else args.user_id,
        start_date=args.start_date,
        end_date=args.end_date,
        top=args.top,
    )
    payload = result.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    rows = payload["top_candidates"]
    print("Daily Narrative Rich-Day Scan")
    print(f"Selected range: {payload['start_date']} through {payload['end_date']}")
    print(_render_table(rows))
    print("\nTop reason codes:")
    for row in rows[: min(len(rows), 5)]:
        codes = ", ".join(row.get("reason_codes") or [])
        print(f"- user {row['user_id']} {row['date']}: {codes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
