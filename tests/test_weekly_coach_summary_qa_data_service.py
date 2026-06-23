from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from services.weekly_coach_summary_persistence_service import (
    get_latest_approved_weekly_summary,
    save_approved_weekly_summary,
)
from services.weekly_coach_summary_qa_data_service import (
    WeeklyCoachSummaryQADataError,
    build_weekly_summary_context_from_qa_range,
    get_qa_user_options,
    get_user_data_date_bounds,
    get_weekly_summary_fact_inventory,
)
from services.weekly_coach_summary_service import generate_approved_weekly_summary


def _connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE daily_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            checkin_date TEXT NOT NULL,
            sleep_hours REAL,
            energy_level INTEGER,
            soreness_level INTEGER,
            notes TEXT
        );
        CREATE TABLE food_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_id INTEGER NOT NULL,
            grams REAL NOT NULL,
            entry_date TEXT NOT NULL
        );
        CREATE TABLE workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            workout_date TEXT NOT NULL,
            workout_name TEXT
        );
        CREATE TABLE workout_plan_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            selected_at TEXT,
            created_at TEXT
        );
        CREATE TABLE workout_execution_set_actuals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_session_id INTEGER NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            skipped INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        );
        """)
    return conn


def _seed_user_102(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT INTO users (id, name) VALUES (102, 'QA 102')")
    for offset, day in enumerate(range(8, 15), start=1):
        conn.execute(
            """
            INSERT INTO daily_checkins (
                user_id, checkin_date, sleep_hours, energy_level, soreness_level, notes
            )
            VALUES (102, ?, ?, ?, ?, 'safe note not returned')
            """,
            (f"2026-06-{day:02d}", 7.0, 7, 4),
        )
        conn.execute(
            "INSERT INTO food_entries (user_id, food_id, grams, entry_date) VALUES (102, 1, 100, ?)",
            (f"2026-06-{day:02d}",),
        )
        if offset % 2 == 0:
            conn.execute(
                "INSERT INTO food_entries (user_id, food_id, grams, entry_date) VALUES (102, 2, 150, ?)",
                (f"2026-06-{day:02d}",),
            )
    for _workout_index, day in enumerate((8, 10, 12, 14), start=1):
        cursor = conn.execute(
            "INSERT INTO workout_sessions (user_id, workout_date, workout_name) VALUES (102, ?, 'safe workout name')",
            (f"2026-06-{day:02d}",),
        )
        session_id = int(cursor.lastrowid)
        conn.execute(
            "INSERT INTO workout_plan_instances (user_id, status, selected_at, created_at) VALUES (102, 'completed', ?, ?)",
            (f"2026-06-{day:02d} 08:00:00", f"2026-06-{day:02d} 08:00:00"),
        )
        for _ in range(3):
            conn.execute(
                "INSERT INTO workout_execution_set_actuals (workout_session_id, completed, skipped, notes) VALUES (?, 1, 0, 'hidden raw set note')",
                (session_id,),
            )
    conn.commit()


def test_qa_user_options_return_known_users_and_presence() -> None:
    conn = _connection()
    _seed_user_102(conn)

    options = get_qa_user_options(conn)

    by_id = {option.user_id: option for option in options}
    assert by_id[102].present is True
    assert by_id[102].scenario == "aligned_managed"
    assert by_id[105].present is False
    assert by_id[101].label == "101 - recovery_limited"


def test_date_bounds_for_seeded_user_are_safe_aggregates() -> None:
    conn = _connection()
    _seed_user_102(conn)

    bounds = get_user_data_date_bounds(102, conn)

    assert bounds.earliest_recovery_date == "2026-06-08"
    assert bounds.latest_recovery_date == "2026-06-14"
    assert bounds.earliest_nutrition_date == "2026-06-08"
    assert bounds.latest_workout_date == "2026-06-14"
    assert bounds.overall_earliest_date == "2026-06-08"
    assert "notes" not in bounds.to_dict()


def test_fact_inventory_returns_counts_not_raw_rows() -> None:
    conn = _connection()
    _seed_user_102(conn)

    inventory = get_weekly_summary_fact_inventory(
        user_id=102,
        start_date="2026-06-08",
        end_date="2026-06-14",
        connection=conn,
    )

    assert inventory.recovery_checkins_count == 7
    assert inventory.nutrition_logged_days_count == 7
    assert inventory.nutrition_entries_count == 10
    assert inventory.completed_workouts_count == 4
    assert inventory.actual_sets_count == 12
    assert inventory.planned_workouts_count == 4
    assert inventory.data_quality_label == "strong"
    inventory_payload = inventory.to_dict()
    assert "raw" not in " ".join(inventory_payload)
    assert "safe note not returned" not in str(inventory_payload)
    assert "hidden raw set note" not in str(inventory_payload)


def test_invalid_date_range_is_rejected_safely() -> None:
    conn = _connection()

    with pytest.raises(WeeklyCoachSummaryQADataError):
        get_weekly_summary_fact_inventory(
            user_id=102,
            start_date="2026-06-15",
            end_date="2026-06-08",
            connection=conn,
        )


def test_future_or_no_data_range_returns_insufficient_safely() -> None:
    conn = _connection()

    inventory = get_weekly_summary_fact_inventory(
        user_id=999,
        start_date="2030-01-01",
        end_date="2030-01-07",
        connection=conn,
    )

    assert inventory.data_quality_label == "insufficient"
    assert inventory.recovery_checkins_count == 0
    assert "insufficient_weekly_data" in inventory.reason_codes


def test_context_from_qa_range_generates_deterministic_approved_summary() -> None:
    conn = _connection()
    _seed_user_102(conn)

    context = build_weekly_summary_context_from_qa_range(
        user_id=102,
        start_date="2026-06-08",
        end_date="2026-06-14",
        connection=conn,
    )
    summary = generate_approved_weekly_summary(context)

    assert context.user_id == 102
    assert context.period.week_start.isoformat() == "2026-06-08"
    assert summary.public_safe is True
    assert summary.displayable is True
    assert summary.source == "deterministic"
    assert "weekly_training_consistency_detected" in summary.reason_codes


def test_low_data_qa_range_produces_limited_or_fallback_summary() -> None:
    conn = _connection()
    conn.execute("INSERT INTO users (id, name) VALUES (105, 'QA 105')")
    conn.execute(
        "INSERT INTO daily_checkins (user_id, checkin_date, sleep_hours, energy_level, soreness_level, notes) VALUES (105, '2026-06-08', 6.5, 5, 5, 'hidden')"
    )
    conn.commit()

    context = build_weekly_summary_context_from_qa_range(
        user_id=105,
        start_date="2026-06-08",
        end_date="2026-06-14",
        connection=conn,
    )
    summary = generate_approved_weekly_summary(context)

    assert summary.public_safe is True
    assert summary.displayable is True
    assert summary.source == "deterministic_fallback"
    assert summary.confidence == "Limited"
    assert "deterministic_fallback_used" in summary.reason_codes


def test_selected_range_save_load_isolated_by_user_and_range() -> None:
    conn = _connection()
    _seed_user_102(conn)
    context = build_weekly_summary_context_from_qa_range(
        user_id=102,
        start_date="2026-06-08",
        end_date="2026-06-14",
        connection=conn,
    )
    summary = generate_approved_weekly_summary(context)

    saved = save_approved_weekly_summary(
        summary=summary,
        user_id=102,
        week_start="2026-06-08",
        week_end="2026-06-14",
        connection=conn,
    )

    matching = get_latest_approved_weekly_summary(
        user_id=102,
        week_start="2026-06-08",
        week_end="2026-06-14",
        connection=conn,
    )
    wrong_user = get_latest_approved_weekly_summary(
        user_id=103,
        week_start="2026-06-08",
        week_end="2026-06-14",
        connection=conn,
    )
    wrong_range = get_latest_approved_weekly_summary(
        user_id=102,
        week_start="2026-06-01",
        week_end="2026-06-07",
        connection=conn,
    )

    assert matching is not None
    assert matching.record_id == saved.record_id
    assert wrong_user is None
    assert wrong_range is None


def test_qa_data_service_has_no_provider_runtime_or_ui_dependency_text() -> None:
    source = Path("services/weekly_coach_summary_qa_data_service.py").read_text(
        encoding="utf-8"
    )

    forbidden = (
        "ollama",
        "crewai",
        "qwen2.5",
        "qwen3",
        "streamlit",
        "raw_provider_output",
        "rejected_provider_output",
        "full_prompt",
        "scratchpad",
        "chain_of_thought",
    )
    lower_source = source.lower()
    assert all(term not in lower_source for term in forbidden)
