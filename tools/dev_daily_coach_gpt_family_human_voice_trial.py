from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.daily_coach_human_voice_prompt_preview_models import (  # noqa: E402
    DailyCoachHumanVoicePromptPreviewResult,
)
from services.openai_human_voice_prompt_preview_service import (  # noqa: E402
    DEFAULT_OPENAI_BASE_URL,
    run_openai_daily_coach_human_voice_prompt_preview,
)

DEFAULT_PROMPT_FILE = (
    "docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md"
)
DEFAULT_OUTPUT_DIR = "qa-runs/daily_coach_gpt_family_human_voice_trial_v1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Developer-only Daily Coach GPT-family human voice trial. Runs "
            "multiple OpenAI model IDs against the same human prompt and raw "
            "backend payload, then prints raw output without persistence."
        )
    )
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--models", required=True)
    parser.add_argument("--prompt-file", default=DEFAULT_PROMPT_FILE)
    parser.add_argument("--openai-base-url", default=DEFAULT_OPENAI_BASE_URL)
    parser.add_argument("--timeout-seconds", type=float, default=300)
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Optional developer-only artifact directory. Defaults to no file "
            "writes unless this flag is passed."
        ),
    )
    parser.add_argument(
        "--mock-output",
        action="store_true",
        help="Use deterministic fake raw output instead of calling OpenAI.",
    )
    args = parser.parse_args(argv)

    models = parse_model_ids(args.models)
    results, provider_input = run_trial(
        user_id=args.user_id,
        target_date=args.target_date,
        model_ids=models,
        prompt_file=args.prompt_file,
        openai_base_url=args.openai_base_url,
        timeout_seconds=args.timeout_seconds,
        mock_output=args.mock_output,
    )

    print_trial(
        results=results,
        user_id=args.user_id,
        target_date=args.target_date,
        prompt_file=args.prompt_file,
        models=models,
    )

    if args.output_dir:
        write_trial_artifacts(
            output_dir=Path(args.output_dir),
            results=results,
            provider_input=provider_input,
            user_id=args.user_id,
            target_date=args.target_date,
            prompt_file=args.prompt_file,
            models=models,
            openai_base_url=args.openai_base_url,
            timeout_seconds=args.timeout_seconds,
        )
    return 0


def parse_model_ids(models: str) -> list[str]:
    model_ids = [model.strip() for model in models.split(",") if model.strip()]
    if not model_ids:
        raise ValueError("--models must include at least one model id")
    return model_ids


def run_trial(
    *,
    user_id: int,
    target_date: str,
    model_ids: list[str],
    prompt_file: str,
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL,
    timeout_seconds: float = 300,
    mock_output: bool = False,
) -> tuple[list[DailyCoachHumanVoicePromptPreviewResult], str]:
    results: list[DailyCoachHumanVoicePromptPreviewResult] = []
    provider_input = ""

    for model_id in model_ids:
        provider_callable = None
        if mock_output:

            def _mock_provider(
                current_provider_input: str,
                *,
                current_model_id: str = model_id,
            ) -> str:
                return (
                    "MOCK RAW MODEL OUTPUT: Daily Coach GPT-family trial "
                    f"model={current_model_id} received "
                    f"{len(current_provider_input)} input characters."
                )

            provider_callable = _mock_provider

        result, current_provider_input = (
            run_openai_daily_coach_human_voice_prompt_preview(
                user_id=user_id,
                target_date=target_date,
                model_name=model_id,
                prompt_file=prompt_file,
                provider_callable=provider_callable,
                timeout_seconds=timeout_seconds,
                openai_base_url=openai_base_url,
            )
        )
        if not provider_input:
            provider_input = current_provider_input
        results.append(result)

    return results, provider_input


def print_trial(
    *,
    results: list[DailyCoachHumanVoicePromptPreviewResult],
    user_id: int,
    target_date: str,
    prompt_file: str,
    models: list[str],
) -> None:
    prompt_sha256 = results[0].prompt_sha256 if results else "unknown"
    payload_version = results[0].payload_version if results else "unknown"
    source_snapshot_version = (
        results[0].source_snapshot_version if results else "unknown"
    )

    print("=== Daily Coach GPT Family Human Voice Trial ===")
    print(f"user_id: {user_id}")
    print(f"target_date: {target_date}")
    print(f"prompt_file: {prompt_file}")
    print(f"prompt_sha256: {prompt_sha256}")
    print(f"payload_version: {payload_version}")
    print(f"source_snapshot_version: {source_snapshot_version}")
    print(f"models: {', '.join(models)}")

    for result in results:
        status = "success" if not result.error_type else "failed"
        print()
        print(f"=== Model: {result.model_name} ===")
        print(f"status: {status}")
        print(f"provider: {result.provider_name}")
        print(f"elapsed_seconds: {result.elapsed_seconds}")
        print(f"error_type: {result.error_type}")
        print(f"error_message: {result.error_message}")
        print()
        print("Raw Model Output:")
        if result.raw_model_output:
            print(result.raw_model_output)
        else:
            print("<no raw model output>")

    print()
    print("=== Trial Summary ===")
    print("model | status | elapsed_seconds | output_length | error_type")
    for result in results:
        status = "success" if not result.error_type else "failed"
        print(
            f"{result.model_name} | {status} | {result.elapsed_seconds} | "
            f"{len(result.raw_model_output)} | {result.error_type}"
        )


def write_trial_artifacts(
    *,
    output_dir: Path,
    results: list[DailyCoachHumanVoicePromptPreviewResult],
    provider_input: str,
    user_id: int,
    target_date: str,
    prompt_file: str,
    models: list[str],
    openai_base_url: str,
    timeout_seconds: float,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    run_config = {
        "developer_preview_only": True,
        "provider_call_was_opt_in": True,
        "persistence_allowed": False,
        "product_surface_allowed": False,
        "normal_today_surface_allowed": False,
        "user_id": user_id,
        "target_date": target_date,
        "prompt_file": prompt_file,
        "prompt_sha256": results[0].prompt_sha256 if results else "unknown",
        "payload_version": results[0].payload_version if results else "unknown",
        "source_snapshot_version": (
            results[0].source_snapshot_version if results else "unknown"
        ),
        "models": models,
        "openai_base_url": openai_base_url,
        "timeout_seconds": timeout_seconds,
    }
    _write_json(output_dir / "run_config.json", run_config)
    (output_dir / f"provider_input_{user_id}_{target_date}.txt").write_text(
        provider_input,
        encoding="utf-8",
    )

    for result in results:
        raw_output_path = (
            output_dir / f"raw_output_{_safe_filename(result.model_name)}.txt"
        )
        raw_output_path.write_text(result.raw_model_output, encoding="utf-8")

    summary_rows = [result.to_dict() for result in results]
    _write_json(output_dir / "trial_summary.json", {"results": summary_rows})
    (output_dir / "trial_summary.md").write_text(
        build_trial_summary_markdown(results),
        encoding="utf-8",
    )


def build_trial_summary_markdown(
    results: list[DailyCoachHumanVoicePromptPreviewResult],
) -> str:
    lines = [
        "# Daily Coach GPT Family Human Voice Trial Summary",
        "",
        "| Model | Status | Elapsed seconds | Output length | Error type |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for result in results:
        status = "success" if not result.error_type else "failed"
        lines.append(
            f"| {result.model_name} | {status} | {result.elapsed_seconds} | "
            f"{len(result.raw_model_output)} | {result.error_type or ''} |"
        )
    lines.append("")
    return "\n".join(lines)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _safe_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return safe or "model"


if __name__ == "__main__":
    raise SystemExit(main())
