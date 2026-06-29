from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_coach_full_user_day_free_range_service import (  # noqa: E402
    DEFAULT_FULL_USER_DAY_OUTPUT_DIR,
    list_daily_coach_full_user_day_prompt_variants,
    list_daily_coach_full_user_day_scenarios,
    run_daily_coach_full_user_day_free_range_matrix,
    run_daily_coach_full_user_day_free_range_scenario,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Developer-only Daily Coach full user-day free-range provider trial."
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
        help="Prompt variants to run. Defaults to all free-range full user-day variants.",
    )
    parser.add_argument(
        "--provider",
        default="deterministic",
        choices=["deterministic", "direct_ollama", "openai"],
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--allow-live-provider", action="store_true")
    parser.add_argument("--output-dir", default=DEFAULT_FULL_USER_DAY_OUTPUT_DIR)
    parser.add_argument("--write-provider-payload-debug", action="store_true")
    parser.add_argument("--write-model-input-manifest", action="store_true")
    parser.add_argument("--write-precision-summary", action="store_true")
    parser.add_argument("--write-food-candidate-summary", action="store_true")
    parser.add_argument("--include-voice-variants", action="store_true")
    parser.add_argument("--write-pasteback-report", action="store_true")
    parser.add_argument("--print-first-pass", action="store_true")
    parser.add_argument("--print-best-variant", action="store_true")
    parser.add_argument("--print-product-issues", action="store_true")
    parser.add_argument("--print-payload-debug", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.list_scenarios:
        for scenario in list_daily_coach_full_user_day_scenarios():
            focus = "; ".join(scenario["expected_evaluation_focus"])
            print(
                f"{scenario['scenario_id']}\tuser={scenario['user_id']}\tdate={scenario['target_date']}\t{focus}"
            )
        return 0

    if args.list_variants:
        for variant in list_daily_coach_full_user_day_prompt_variants():
            print(f"{variant['variant_id']}\t{variant['purpose']}")
        return 0

    selected_variants = args.variants or None
    output_dir = Path(args.output_dir)
    if args.run_scenario:
        result = run_daily_coach_full_user_day_free_range_scenario(
            scenario_id=args.run_scenario,
            provider=args.provider,
            model=args.model,
            variants=selected_variants,
            repeat=args.repeat,
            allow_live_provider=args.allow_live_provider,
            output_dir=output_dir,
            write_provider_payload_debug=args.write_provider_payload_debug,
            write_model_input_manifest=args.write_model_input_manifest,
            write_precision_summary=args.write_precision_summary,
            write_food_candidate_summary=args.write_food_candidate_summary,
            include_voice_variants=args.include_voice_variants,
        )
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True, default=str))
        else:
            _print_summary([result], output_dir, args.write_provider_payload_debug)
            _print_requested_sections(args, output_dir)
        return 0

    if args.run_matrix:
        results = run_daily_coach_full_user_day_free_range_matrix(
            scenarios=args.scenarios or ["rich_nutrition_training_recovery"],
            provider=args.provider,
            model=args.model,
            variants=selected_variants,
            repeat=args.repeat,
            allow_live_provider=args.allow_live_provider,
            output_dir=output_dir,
            write_provider_payload_debug=args.write_provider_payload_debug,
            write_model_input_manifest=args.write_model_input_manifest,
            write_precision_summary=args.write_precision_summary,
            write_food_candidate_summary=args.write_food_candidate_summary,
            include_voice_variants=args.include_voice_variants,
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
            _print_summary(results, output_dir, args.write_provider_payload_debug)
            _print_requested_sections(args, output_dir)
        return 0

    parser.error(
        "Use --list-scenarios, --list-variants, --run-scenario, or --run-matrix."
    )
    return 2


def _print_summary(results, output_dir: Path, debug_written: bool) -> None:
    print(f"Full User-Day Free-Range Trial runs: {len(results)}")
    print(f"Output dir: {output_dir}")
    print(f"Provider payload debug requested: {debug_written}")
    print(
        "Model input manifest / precision / food summaries are always written for this dev path when artifacts are produced."
    )
    for result in results:
        skipped = sum(1 for variant in result.variants if variant.skipped)
        print(
            f"{result.scenario_id}\t{result.provider}\tmodel={result.model}\tvariants={len(result.variants)}\tskipped={skipped}"
        )
    print(
        "Known baseline drift documented: tests/test_daily_narrative_rich_day_service.py"
    )


def _print_requested_sections(args, output_dir: Path) -> None:
    if args.write_pasteback_report:
        print(f"Pasteback report: {output_dir / 'pasteback_report.md'}")
    section_map = (
        (
            args.print_first_pass,
            "first_pass_drafts_compact.md",
            "Compact first-pass drafts",
        ),
        (args.print_best_variant, "best_variant_summary.md", "Best variant summary"),
        (
            args.print_product_issues,
            "product_language_findings.md",
            "Product language findings",
        ),
        (
            args.print_payload_debug,
            "provider_input_prompt.md",
            "Provider input prompt debug",
        ),
        (
            args.write_model_input_manifest,
            "model_input_manifest.md",
            "Model input manifest",
        ),
        (
            args.write_precision_summary,
            "precision_usage_summary.md",
            "Precision usage summary",
        ),
        (
            args.write_food_candidate_summary,
            "food_candidate_summary.md",
            "Food candidate summary",
        ),
    )
    for enabled, filename, label in section_map:
        if not enabled:
            continue
        path = output_dir / filename
        print(f"\n--- {label}: {path} ---")
        if path.exists():
            print(path.read_text(encoding="utf-8"))
        else:
            print("(artifact not found)")


if __name__ == "__main__":
    raise SystemExit(main())
