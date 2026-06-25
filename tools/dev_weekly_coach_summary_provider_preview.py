from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.weekly_coach_summary_provider_service import (  # noqa: E402
    generate_weekly_summary_provider_preview,
    resolve_weekly_summary_provider_preview_config,
)
from services.weekly_coach_summary_qa_context_service import (  # noqa: E402
    build_weekly_summary_context_from_qa_range,
)
from services.weekly_coach_summary_service import (  # noqa: E402
    generate_approved_weekly_summary,
)


def _fake_provider_response(context: Any) -> dict[str, Any]:
    return {
        "title": "Developer provider dry run",
        "summary": "Because the selected range has approved backend facts, this dry run can test parser and validator behavior without live Ollama.",
        "recovery_note": "Because recovery facts are bounded, recovery wording stays cautious and factual.",
        "nutrition_note": "Because nutrition facts are bounded, nutrition wording avoids raw food details.",
        "training_note": "There are workout sessions but no actual set details, so progression comments stay conservative.",
        "next_action": "Log one workout note and one meal detail so next week's summary has more specific context.",
        "confidence_label": (
            "Limited" if context.fact_boundary.data_quality_limited else "Moderate"
        ),
        "data_limitations": list(context.limitations)
        or ["Actual set details are not available for this range."],
        "facts_used": [
            "selected QA date-range context",
            "safe aggregate recovery/nutrition/training facts",
            "deterministic baseline summary",
        ],
        "safety_flags": [
            "developer_mode_provider_preview_only",
            "dry_run_fake_transport",
        ],
        "provider_model": "qwen2.5:3b",
        "source_context_metadata": {
            "user_id": context.user_id,
            "start_date": context.period.week_start.isoformat(),
            "end_date": context.period.week_end.isoformat(),
            "source": "qa_date_range_debug",
        },
        "generated_at": "dry-run",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Developer-only Weekly Coach Summary provider preview smoke helper."
    )
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--model", default="qwen2.5:3b")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--live", action="store_true")
    args = parser.parse_args()

    context = build_weekly_summary_context_from_qa_range(
        user_id=args.user_id,
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
    )
    deterministic = generate_approved_weekly_summary(context)
    config = resolve_weekly_summary_provider_preview_config(
        environ={
            "FITNESS_AI_WEEKLY_SUMMARY_PROVIDER_PREVIEW_ENABLED": "true",
            "FITNESS_AI_WEEKLY_SUMMARY_PROVIDER_MODEL": args.model,
            "FITNESS_AI_OLLAMA_KEEP_ALIVE": "0",
            "FITNESS_AI_OLLAMA_UNLOAD_AFTER_REQUEST": "true",
        }
    )

    if args.dry_run:

        def fake_post(
            url: str, payload: dict[str, Any], timeout: float
        ) -> dict[str, Any]:
            return {"response": json.dumps(_fake_provider_response(context))}

        result = generate_weekly_summary_provider_preview(
            context=context,
            deterministic_summary=deterministic,
            config=config,
            http_post=fake_post,
        )
    else:
        result = generate_weekly_summary_provider_preview(
            context=context,
            deterministic_summary=deterministic,
            config=config,
        )

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.validation_status == "approved" or result.fallback_used else 1


if __name__ == "__main__":
    raise SystemExit(main())
