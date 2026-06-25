from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_coach_narrative_preview_service import (  # noqa: E402
    DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DETERMINISTIC,
    DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA,
    build_daily_coach_narrative_preview,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Developer-only Daily Narrative QA seeded-date preview."
    )
    parser.add_argument("--user-id", type=int, default=102)
    parser.add_argument("--date", default="2026-06-06")
    parser.add_argument("--lookback-days", type=int, default=1, choices=[1, 3, 7])
    parser.add_argument("--model", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Deterministic only; no provider call."
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="Call configured direct Ollama provider manually.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provider = (
        DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA
        if args.live
        else DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DETERMINISTIC
    )
    preview = build_daily_coach_narrative_preview(
        args.user_id,
        target_date=args.date,
        provider=provider,
        model_name=args.model,
        timeout_seconds=args.timeout_seconds,
        qa_preview=True,
        lookback_days=args.lookback_days,
    )
    print(json.dumps(preview.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
