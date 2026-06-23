from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.weekly_coach_summary_persistence_service import (  # noqa: E402
    get_latest_approved_weekly_summary,
    save_approved_weekly_summary,
)
from services.weekly_coach_summary_service import (  # noqa: E402
    approved_weekly_summary_to_public_sections,
    build_weekly_summary_context_from_fixture,
    generate_approved_weekly_summary,
)


def _elapsed_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 2)


def _connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def main() -> None:
    total_start = perf_counter()

    context_start = perf_counter()
    context = build_weekly_summary_context_from_fixture(
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        training_days_logged=4,
        workouts_completed=3,
        planned_workouts=4,
        recovery_notes_available=True,
        nutrition_days_logged=3,
        protein_days_logged=3,
        average_energy=7,
        average_soreness=4,
        limitations=("One nutrition day may be incomplete.",),
    )
    context_ms = _elapsed_ms(context_start)

    generate_start = perf_counter()
    summary = generate_approved_weekly_summary(context)
    generate_ms = _elapsed_ms(generate_start)

    sections_start = perf_counter()
    approved_weekly_summary_to_public_sections(summary)
    sections_ms = _elapsed_ms(sections_start)

    conn = _connection()
    save_start = perf_counter()
    save_approved_weekly_summary(
        summary=summary,
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        connection=conn,
        sanitized_metadata={
            "provider_attempted": False,
            "fallback_used": False,
            "parse_status": "not_attempted",
            "validation_status": "approved",
            "final_summary_source": "deterministic",
            "generated_by": "latency_probe",
        },
    )
    save_ms = _elapsed_ms(save_start)

    load_start = perf_counter()
    latest = get_latest_approved_weekly_summary(
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        connection=conn,
    )
    load_ms = _elapsed_ms(load_start)

    if latest is None:
        raise RuntimeError("Latency probe failed to reload the saved summary.")

    print("Weekly Coach Summary Latency Probe")
    print(f"context_build_ms: {context_ms}")
    print(f"deterministic_generation_ms: {generate_ms}")
    print(f"section_build_ms: {sections_ms}")
    print(f"sqlite_save_ms: {save_ms}")
    print(f"sqlite_load_latest_ms: {load_ms}")
    print(f"total_probe_ms: {_elapsed_ms(total_start)}")
    print("provider_runtime_called: false")


if __name__ == "__main__":
    main()
