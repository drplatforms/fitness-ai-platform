from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.coach_voice_bakeoff_service import (  # noqa: E402
    all_context_ids,
    build_default_coach_voice_contexts,
    generate_markdown_report,
    run_coach_voice_bakeoff,
    starter_context_ids,
)

DEFAULT_MODELS = ["qwen2.5:3b", "qwen3:8b", "qwen3:14b"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the offline bounded coach voice bakeoff."
    )
    parser.add_argument("--model", action="append", dest="models")
    parser.add_argument(
        "--context",
        action="append",
        dest="contexts",
        help="Context id to run. May be passed more than once.",
    )
    parser.add_argument(
        "--all-contexts",
        action="store_true",
        help="Run all built-in context packs instead of the starter subset.",
    )
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--ollama-base-url", default=None)
    parser.add_argument(
        "--output-dir",
        default="artifacts/coach_voice_bakeoff_v1",
        help="Local-only output directory for JSON and markdown results.",
    )
    args = parser.parse_args()

    contexts_by_id = build_default_coach_voice_contexts()
    selected_context_ids = _selected_context_ids(args, contexts_by_id)
    selected_contexts = [
        contexts_by_id[context_id] for context_id in selected_context_ids
    ]
    models = args.models or DEFAULT_MODELS

    results = run_coach_voice_bakeoff(
        model_names=models,
        contexts=selected_contexts,
        timeout_seconds=args.timeout,
        ollama_base_url=args.ollama_base_url,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.json"
    report_path = output_dir / "report.md"

    results_path.write_text(
        json.dumps([result.to_dict() for result in results], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report_path.write_text(generate_markdown_report(results), encoding="utf-8")

    print(f"Wrote {results_path}")
    print(f"Wrote {report_path}")
    return 0


def _selected_context_ids(args, contexts_by_id: dict) -> list[str]:
    if args.all_contexts:
        return all_context_ids()
    if args.contexts:
        missing = [
            context_id
            for context_id in args.contexts
            if context_id not in contexts_by_id
        ]
        if missing:
            raise SystemExit(f"Unknown context id(s): {', '.join(missing)}")
        return args.contexts
    return starter_context_ids()


if __name__ == "__main__":
    raise SystemExit(main())
