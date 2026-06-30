from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_coach_fully_free_source_data_lab_service import (  # noqa: E402
    DEFAULT_FULLY_FREE_OUTPUT_DIR,
    list_daily_coach_fully_free_prompt_variants,
    list_daily_coach_fully_free_source_data_scenarios,
    run_daily_coach_fully_free_source_data_lab_matrix,
    run_daily_coach_fully_free_source_data_lab_scenario,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Developer-only Daily Coach fully free source-data GPT-5.5 lab."
    )
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--list-variants", action="store_true")
    parser.add_argument("--run-scenario", default=None)
    parser.add_argument("--run-matrix", action="store_true")
    parser.add_argument("--scenarios", nargs="+", default=[])
    parser.add_argument("--variants", nargs="+", default=[])
    parser.add_argument(
        "--provider",
        default="deterministic",
        choices=["deterministic", "direct_ollama", "openai"],
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--allow-live-provider", action="store_true")
    parser.add_argument("--output-dir", default=DEFAULT_FULLY_FREE_OUTPUT_DIR)
    parser.add_argument("--write-provider-payload-debug", action="store_true")
    parser.add_argument("--write-source-data-packet", action="store_true")
    parser.add_argument("--write-source-data-completeness-summary", action="store_true")
    parser.add_argument("--write-model-freedom-summary", action="store_true")
    parser.add_argument(
        "--write-backend-prose-contamination-summary", action="store_true"
    )
    parser.add_argument("--write-completion-diagnostics", action="store_true")
    parser.add_argument("--write-pasteback-report", action="store_true")
    parser.add_argument("--print-best-variant", action="store_true")
    parser.add_argument("--print-product-issues", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.list_scenarios:
        for scenario in list_daily_coach_fully_free_source_data_scenarios():
            focus = "; ".join(scenario.get("expected_evaluation_focus") or [])
            print(
                f"{scenario['scenario_id']}\tuser={scenario['user_id']}\tdate={scenario['target_date']}\t{focus}"
            )
        return 0

    if args.list_variants:
        for variant in list_daily_coach_fully_free_prompt_variants():
            print(f"{variant['variant_id']}\t{variant['description']}")
        return 0

    selected_variants = args.variants or None
    output_dir = Path(args.output_dir)
    common_kwargs = {
        "provider": args.provider,
        "model": args.model,
        "variants": selected_variants,
        "repeat": args.repeat,
        "allow_live_provider": args.allow_live_provider,
        "output_dir": output_dir,
        "write_provider_payload_debug": args.write_provider_payload_debug,
        "write_source_data_packet": args.write_source_data_packet,
        "write_source_data_completeness_summary": args.write_source_data_completeness_summary,
        "write_model_freedom_summary": args.write_model_freedom_summary,
        "write_backend_prose_contamination_summary": args.write_backend_prose_contamination_summary,
        "write_completion_diagnostics": args.write_completion_diagnostics,
        "write_pasteback_report": args.write_pasteback_report,
    }

    if args.run_scenario:
        result = run_daily_coach_fully_free_source_data_lab_scenario(
            scenario_id=args.run_scenario,
            **common_kwargs,
        )
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True, default=str))
        else:
            _print_summary([result], output_dir)
            _print_requested_sections(args, output_dir)
        return 0

    if args.run_matrix:
        results = run_daily_coach_fully_free_source_data_lab_matrix(
            scenarios=args.scenarios or ["rich_nutrition_training_recovery"],
            **common_kwargs,
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
            _print_summary(results, output_dir)
            _print_requested_sections(args, output_dir)
        return 0

    parser.error(
        "Use --list-scenarios, --list-variants, --run-scenario, or --run-matrix."
    )
    return 2


def _print_summary(results, output_dir: Path) -> None:
    print(f"Fully Free Source-Data Lab runs: {len(results)}")
    print(f"Output dir: {output_dir}")
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
        (args.print_best_variant, "best_variant_summary.md", "Best variant summary"),
        (
            args.print_product_issues,
            "backend_prose_contamination_summary.md",
            "Backend prose contamination summary",
        ),
        (
            args.write_source_data_packet,
            "fully_free_source_data_packet.md",
            "Fully free source-data packet",
        ),
        (
            args.write_source_data_completeness_summary,
            "source_data_completeness_summary.md",
            "Source data completeness summary",
        ),
        (
            args.write_model_freedom_summary,
            "model_freedom_summary.md",
            "Model freedom summary",
        ),
        (
            args.write_backend_prose_contamination_summary,
            "backend_prose_contamination_summary.md",
            "Backend prose contamination summary",
        ),
        (
            args.write_completion_diagnostics,
            "completion_diagnostics.md",
            "Completion diagnostics",
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
            print("(artifact not written)")


if __name__ == "__main__":
    raise SystemExit(main())
