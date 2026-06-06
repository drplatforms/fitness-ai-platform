# ruff: noqa: E402
"""Seed canonical app-facing foods."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import initialize_database
from services.food_normalization_service import seed_starter_canonical_foods


def main() -> None:
    initialize_database()
    foods = seed_starter_canonical_foods()

    print(f"Seeded canonical foods: {len(foods)}")
    for food in foods:
        print(f"- {food.display_name} | {food.food_type} | {food.default_unit}")


if __name__ == "__main__":
    main()
