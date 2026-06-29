from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_coach_wide_context_ceiling_trial_service import (  # noqa: E402
    DEFAULT_WIDE_CONTEXT_OUTPUT_DIR,
    list_daily_coach_wide_context_prompt_variants,
    list_daily_coach_wide_context_scenarios,
    run_daily_coach_wide_context_ceiling_trial_matrix,
    run_daily_coach_wide_context_ceiling_trial_scenario,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Developer-only Daily Coach Wide Context Uncaged Ceiling Trial."
    )
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--list-variants", action="store_true")
    parser.add_argument("--run-scenario", default=None)
    parser.add_argument("--run-matrix", action="store_true")
    parser.add_argument("--scenarios", nargs="+", default=[])
    parser.add_argument(
        "--variants",
        nargs="+",
        default=[],
        help="Prompt variants to run. Defaults to current_narrow_path plus three wide-context variants.",
    )
    parser.add_argument(
        "--provider",
        default="deterministic",
        choices=["deterministic", "direct_ollama", "openai"],
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--allow-live-provider", action="store_true")
    parser.add_argument("--output-dir", default=DEFAULT_WIDE_CONTEXT_OUTPUT_DIR)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.list_scenarios:
        for scenario in list_daily_coach_wide_context_scenarios():
            focus = "; ".join(scenario["expected_evaluation_focus"])
            print(
                f"{scenario['scenario_id']}\tuser={scenario['user_id']}\tdate={scenario['target_date']}\t{focus}"
            )
        return 0

    if args.list_variants:
        for variant in list_daily_coach_wide_context_prompt_variants():
            print(
                f"{variant['variant_id']}\twide_context={variant['uses_wide_context']}\t{variant['purpose']}"
            )
        return 0

    selected_variants = args.variants or None
    if args.run_scenario:
        result = run_daily_coach_wide_context_ceiling_trial_scenario(
            scenario_id=args.run_scenario,
            provider=args.provider,
            model=args.model,
            variants=selected_variants,
            allow_live_provider=args.allow_live_provider,
            output_dir=Path(args.output_dir),
        )
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True, default=str))
        else:
            _print_summary([result], Path(args.output_dir))
        return 0

    if args.run_matrix:
        scenarios = args.scenarios or ["rich_nutrition_training_recovery"]
        results = run_daily_coach_wide_context_ceiling_trial_matrix(
            scenarios=scenarios,
            provider=args.provider,
            model=args.model,
            variants=selected_variants,
            allow_live_provider=args.allow_live_provider,
            output_dir=Path(args.output_dir),
        )
        if args.json:
            print(
                json.dumps(
                    [result.to_dict() for result in results],
                    indent=2,
                    sort_keys=True,
                    default=str,
                )
            )
        else:
            _print_summary(results, Path(args.output_dir))
        return 0

    parser.error(
        "Use --list-scenarios, --list-variants, --run-scenario, or --run-matrix."
    )
    return 2


def _print_summary(results, output_dir: Path) -> None:
    print(f"Wide Context Ceiling Trial runs: {len(results)}")
    print(f"Output dir: {output_dir}")
    for result in results:
        skipped = sum(1 for variant in result.variants if variant.skipped)
        print(
            f"{result.scenario_id}\t{result.provider}\tmodel={result.model}\tvariants={len(result.variants)}\tskipped={skipped}"
        )
    print(
        "Known baseline drift documented: tests/test_daily_narrative_rich_day_service.py"
    )


if __name__ == "__main__":
    raise SystemExit(main())
