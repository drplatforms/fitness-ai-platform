# ruff: noqa: E402
"""Seed the local exercise catalog."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import initialize_database
from services.exercise_catalog_service import seed_exercise_catalog


def main() -> None:
    initialize_database()
    entries = seed_exercise_catalog()

    print(f"Seeded exercise catalog entries: {len(entries)}")
    for entry in entries:
        equipment = ", ".join(entry.equipment_required)
        muscles = ", ".join(entry.primary_muscle_groups)
        print(f"- {entry.name} | {entry.movement_pattern} | {equipment} | {muscles}")


if __name__ == "__main__":
    main()
