from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_narrative_voice_lab_service import (  # noqa: E402
    build_daily_narrative_voice_lab_result,
    list_daily_narrative_voice_lab_scenarios,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily Narrative Voice Lab")
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--scenario", help="Scenario id to render")
    parser.add_argument(
        "--dry-run", action="store_true", help="Render public-safe JSON"
    )
    args = parser.parse_args()

    if args.list_scenarios:
        for scenario in list_daily_narrative_voice_lab_scenarios():
            print(f"{scenario.scenario_id}\t{scenario.scenario_label}")
        return 0

    if not args.scenario:
        parser.error("Use --list-scenarios or --scenario <scenario_id>.")

    result = build_daily_narrative_voice_lab_result(args.scenario)
    if args.dry_run:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"Scenario: {result.scenario.scenario_id}")
        print(f"Label: {result.scenario.scenario_label}")
        print(f"Angle: {result.scenario.desired_coaching_angle}")
        for candidate in result.candidates:
            print()
            print(f"[{candidate.variant_id}] {candidate.title}")
            print(candidate.body)
            print("banned:", ", ".join(candidate.banned_phrase_hits) or "none")
            print("awkward:", ", ".join(candidate.awkward_phrase_hits) or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
