from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.daily_coach_narrative_provider_service import (  # noqa: E402
    build_daily_coach_narrative_contexts_for_users,
    generate_markdown_report,
    run_daily_coach_narrative_offline_qa,
)

DEFAULT_MODELS = ["qwen3:8b", "qwen2.5:3b", "qwen3:32b"]
DEFAULT_USER_IDS = [101, 102, 105]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run offline/debug-only Daily Coach Narrative provider QA."
    )
    parser.add_argument("--model", action="append", dest="models")
    parser.add_argument("--user-id", action="append", type=int, dest="user_ids")
    parser.add_argument("--date", default=None, help="Context date in YYYY-MM-DD form.")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--ollama-base-url", default=None)
    parser.add_argument(
        "--output-dir",
        default="artifacts/daily_coach_narrative_offline_qa_v1",
        help="Local-only output directory for JSON and markdown results.",
    )
    args = parser.parse_args()

    user_ids = args.user_ids or DEFAULT_USER_IDS
    models = args.models or DEFAULT_MODELS
    contexts = build_daily_coach_narrative_contexts_for_users(
        user_ids,
        target_date=args.date,
    )

    results = run_daily_coach_narrative_offline_qa(
        model_names=models,
        contexts=contexts,
        timeout_seconds=args.timeout,
        ollama_base_url=args.ollama_base_url,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.json"
    report_path = output_dir / "report.md"
    context_path = output_dir / "contexts.json"

    context_path.write_text(
        json.dumps(
            [context.to_dict() for context in contexts], indent=2, sort_keys=True
        ),
        encoding="utf-8",
    )
    results_path.write_text(
        json.dumps([result.to_dict() for result in results], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report_path.write_text(
        generate_markdown_report(results, contexts=contexts),
        encoding="utf-8",
    )

    print(f"Wrote {context_path}")
    print(f"Wrote {results_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
