from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.weekly_coach_summary_service import (  # noqa: E402
    approved_weekly_summary_to_public_sections,
    build_weekly_summary_context_from_fixture,
    generate_approved_weekly_summary,
)


def main() -> None:
    context = build_weekly_summary_context_from_fixture(
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        training_days_logged=4,
        workouts_completed=3,
        planned_workouts=4,
        recovery_notes_available=True,
        nutrition_days_logged=3,
        protein_days_logged=3,
        average_energy=7,
        average_soreness=4,
        limitations=("One nutrition day may be incomplete.",),
    )
    summary = generate_approved_weekly_summary(context)
    sections = approved_weekly_summary_to_public_sections(summary)

    print("Weekly Coach Summary Preview")
    print(
        f"Period: {context.period.week_start.isoformat()} "
        f"to {context.period.week_end.isoformat()}"
    )
    print(f"Source: {sections['source']}")
    print(f"Confidence: {sections['confidence']}")
    print(f"Public safe: {str(sections['public_safe']).lower()}")
    print(f"Displayable: {str(sections['displayable']).lower()}")
    print()
    print("Headline:")
    print(sections["headline"])
    print()
    print("Weekly Overview:")
    print(sections["weekly_overview"])
    print()
    print("Recovery Observation:")
    print(sections["recovery_observation"])
    print()
    print("Nutrition Observation:")
    print(sections["nutrition_observation"])
    print()
    print("Training Observation:")
    print(sections["training_observation"])
    print()
    print("Primary Pattern:")
    print(sections["primary_pattern"])
    print()
    print("Recommended Focus:")
    print(sections["recommended_focus"])
    print()
    print("Next Week Guidance:")
    print(sections["next_week_guidance"])
    print()
    print("Reason Codes:")
    print(", ".join(sections["reason_codes"]))


if __name__ == "__main__":
    main()
