from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.food_normalization_service import ensure_starter_canonical_foods_seeded
from services.nutrition_serving_unit_service import (
    count_canonical_foods_with_active_serving_units,
    seed_canonical_food_serving_units,
    serving_unit_seed_result_to_dict,
)


def _print_summary(payload: dict) -> None:
    print("=" * 80)
    print("CANONICAL FOOD SERVING UNIT SEED V1")
    print("=" * 80)
    print(f"inserted_count: {payload['inserted_count']}")
    print(f"updated_count: {payload['updated_count']}")
    print(f"skipped_count: {payload['skipped_count']}")
    print(f"active_serving_unit_count: {payload['active_serving_unit_count']}")
    print(
        "foods_with_active_serving_units: "
        f"{payload['foods_with_active_serving_units']}"
    )
    if payload["missing_canonical_foods"]:
        print("missing_canonical_foods:")
        for food_name in payload["missing_canonical_foods"]:
            print(f"  - {food_name}")
    else:
        print("missing_canonical_foods: []")
    print("seeded_serving_units:")
    for serving_unit in payload["seeded_serving_units"]:
        print(
            "  - "
            f"food_id={serving_unit['canonical_food_id']} "
            f"display={serving_unit['display_name']} "
            f"grams={serving_unit['grams_default']} "
            f"range={serving_unit['grams_min']}..{serving_unit['grams_max']} "
            f"confidence={serving_unit['confidence']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed trusted serving-unit metadata for canonical foods."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path for the seed result.",
    )
    parser.add_argument(
        "--skip-canonical-seed",
        action="store_true",
        help="Do not seed starter canonical foods before serving units.",
    )
    args = parser.parse_args()

    if not args.skip_canonical_seed:
        ensure_starter_canonical_foods_seeded()

    result = seed_canonical_food_serving_units()
    payload = serving_unit_seed_result_to_dict(result)
    payload["foods_with_active_serving_units"] = (
        count_canonical_foods_with_active_serving_units()
    )

    _print_summary(payload)

    if args.output:
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote JSON output: {args.output}")


if __name__ == "__main__":
    main()
