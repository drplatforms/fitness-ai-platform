from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.nutrition_catalog_diagnostic_service import (  # noqa: E402
    build_nutrition_catalog_diagnostic_summary,
)


def _print_key_values(values: dict[str, Any], indent: int = 0) -> None:
    prefix = " " * indent
    for key, value in values.items():
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            _print_key_values(value, indent + 2)
        elif isinstance(value, list):
            print(f"{prefix}{key}: {value}")
        else:
            print(f"{prefix}{key}: {value}")


def _section(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def print_human_summary(summary: dict[str, Any]) -> None:
    print("=" * 80)
    print("NUTRITION CATALOG DIAGNOSTIC V1")
    print("=" * 80)

    _section("1. Catalog Summary")
    _print_key_values(summary["catalog_summary"])

    _section("2. Nutrient Completeness")
    _print_key_values(summary["nutrient_completeness"])

    _section("3. Serving Unit Readiness")
    _print_key_values(summary["serving_unit_readiness"])

    _section("4. Alias/Search Readiness")
    _print_key_values(summary["alias_search_readiness"])

    _section("5. High-Value Staple Coverage")
    totals = summary["high_value_staple_coverage"]["totals"]
    _print_key_values(totals)
    for category, category_summary in summary["high_value_staple_coverage"][
        "categories"
    ].items():
        print(f"\n{category}:")
        _print_key_values(category_summary, indent=2)

    _section("6. Duplicate/Near-Duplicate Risks")
    _print_key_values(summary["duplicate_near_duplicate_risks"])

    _section("7. Logging Assumptions")
    _print_key_values(summary["logging_assumptions"])

    _section("8. Actuals/Targets Dependencies")
    _print_key_values(summary["actuals_targets_dependencies"])

    _section("9. Food Suggestion Readiness")
    _print_key_values(summary["food_suggestion_readiness"])

    _section("10. AI/Provider Grounding Readiness")
    _print_key_values(summary["ai_provider_grounding_readiness"])

    _section("11. Recommended Next Steps")
    for step in summary["recommended_next_steps"]:
        print(f"- {step}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect current nutrition catalog/logging readiness."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the diagnostic summary as JSON.",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write the JSON summary.",
    )
    parser.add_argument(
        "--db-path",
        help="Optional SQLite database path for tests/diagnostics.",
    )
    args = parser.parse_args()

    summary = build_nutrition_catalog_diagnostic_summary(args.db_path)

    if args.output:
        Path(args.output).write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
