from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_coach_human_voice_prompt_preview_service import (  # noqa: E402
    run_daily_coach_human_voice_prompt_preview,
)

DEFAULT_PROMPT_FILE = (
    "docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Developer-only Daily Coach human voice prompt preview. Loads a "
            "human-editable prompt file, appends raw backend payload JSON, and "
            "prints raw provider output without persistence."
        )
    )
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt-file", default=DEFAULT_PROMPT_FILE)
    parser.add_argument("--timeout-seconds", type=float, default=300)
    parser.add_argument("--ollama-base-url", default="http://localhost:11434")
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--print-provider-input", action="store_true")
    parser.add_argument(
        "--mock-output",
        action="store_true",
        help="Use deterministic fake raw output instead of calling Ollama.",
    )
    args = parser.parse_args(argv)

    provider_callable = None
    if args.mock_output:

        def _mock_provider(provider_input: str) -> str:
            return (
                "MOCK RAW MODEL OUTPUT: Daily Coach human voice prompt preview "
                f"received {len(provider_input)} input characters."
            )

        provider_callable = _mock_provider

    result, provider_input = run_daily_coach_human_voice_prompt_preview(
        user_id=args.user_id,
        target_date=args.target_date,
        model_name=args.model,
        prompt_file=args.prompt_file,
        provider_callable=provider_callable,
        timeout_seconds=args.timeout_seconds,
        ollama_base_url=args.ollama_base_url,
        temperature=args.temperature,
    )

    _print_result(result.to_dict())
    if args.print_provider_input:
        print()
        print("=== Provider Input ===")
        print(provider_input)
    print()
    print("=== Raw Model Output ===")
    if result.raw_model_output:
        print(result.raw_model_output)
    else:
        print("<no raw model output>")
    if result.error_type or result.error_message:
        print()
        print("=== Provider Error Metadata ===")
        print(f"error_type: {result.error_type}")
        print(f"error_message: {result.error_message}")
    return 0


def _print_result(result: dict) -> None:
    print("=== Daily Coach Human Voice Prompt Preview ===")
    print(f"user_id: {result['user_id']}")
    print(f"target_date: {result['target_date']}")
    print(f"model: {result['model_name']}")
    print(f"prompt_file: {result['prompt_file']}")
    print(f"prompt_sha256: {result['prompt_sha256']}")
    print(f"payload_version: {result['payload_version']}")
    print(f"source_snapshot_version: {result['source_snapshot_version']}")
    print(f"developer_preview_only: {result['developer_preview_only']}")
    print(f"provider_call_was_opt_in: {result['provider_call_was_opt_in']}")
    print(f"persistence_allowed: {result['persistence_allowed']}")
    print(f"product_surface_allowed: {result['product_surface_allowed']}")
    print(f"normal_today_surface_allowed: {result['normal_today_surface_allowed']}")
    print(f"elapsed_seconds: {result['elapsed_seconds']}")
    print(f"latency_ms: {result['latency_ms']}")


if __name__ == "__main__":
    raise SystemExit(main())
