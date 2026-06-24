from __future__ import annotations

import sqlite3
from pathlib import Path

from models.weekly_coach_summary_models import WeeklyCoachSummaryConfidence
from services.weekly_coach_summary_qa_data_service import (
    DEFAULT_QA_DATE_RANGE_PRESET_KEY,
    DEFAULT_QA_DATE_RANGE_USER_ID,
    DEFAULT_QA_LOW_DATA_USER_ID,
    QA_DATE_RANGE_PRESETS,
    QA_USER_LABELS,
    build_weekly_summary_context_from_qa_range,
    inspect_weekly_summary_qa_range,
    qa_date_range_cache_key,
    qa_range_preset_dates,
)


def create_qa_range_fixture_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE daily_checkins (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            checkin_date TEXT NOT NULL,
            notes TEXT
        );
        CREATE TABLE food_entries (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            food_id INTEGER NOT NULL,
            grams REAL NOT NULL,
            entry_date TEXT NOT NULL
        );
        CREATE TABLE workout_sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            workout_date TEXT NOT NULL
        );
        CREATE TABLE workout_plan_instances (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            scenario TEXT NOT NULL,
            confidence TEXT NOT NULL,
            title TEXT NOT NULL,
            approved_workout_plan_json TEXT NOT NULL,
            selected_at TEXT,
            created_at TEXT
        );
        CREATE TABLE planned_workout_exercises (
            id INTEGER PRIMARY KEY,
            workout_plan_instance_id INTEGER NOT NULL,
            exercise_order INTEGER NOT NULL,
            name TEXT NOT NULL,
            sets INTEGER NOT NULL,
            reps_min INTEGER NOT NULL,
            reps_max INTEGER NOT NULL,
            rir_min INTEGER NOT NULL,
            rir_max INTEGER NOT NULL,
            notes TEXT NOT NULL,
            equipment_required_json TEXT NOT NULL
        );
        CREATE TABLE workout_execution_sessions (
            id INTEGER PRIMARY KEY,
            workout_plan_instance_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            workout_session_id INTEGER,
            started_at TEXT,
            completed_at TEXT,
            created_at TEXT
        );
        CREATE TABLE workout_execution_set_actuals (
            id INTEGER PRIMARY KEY,
            workout_execution_session_id INTEGER NOT NULL,
            workout_session_id INTEGER,
            exercise_name TEXT NOT NULL,
            set_number INTEGER NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            skipped INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT
        );
        """)
    connection.executemany(
        "INSERT INTO users (id, name) VALUES (?, ?)",
        [(102, "QA 102"), (105, "QA 105")],
    )
    for day in range(8, 15):
        checkin_date = f"2026-06-{day:02d}"
        connection.execute(
            """
            INSERT INTO daily_checkins (user_id, checkin_date, notes)
            VALUES (?, ?, ?)
            """,
            (102, checkin_date, "private check-in note must not leak"),
        )
        connection.execute(
            """
            INSERT INTO food_entries (user_id, food_id, grams, entry_date)
            VALUES (?, ?, ?, ?)
            """,
            (102, 1, 100.0, checkin_date),
        )
    for session_id, day in enumerate((8, 10, 12), start=1):
        workout_date = f"2026-06-{day:02d}"
        connection.execute(
            "INSERT INTO workout_sessions (id, user_id, workout_date) VALUES (?, ?, ?)",
            (session_id, 102, workout_date),
        )
        connection.execute(
            """
            INSERT INTO workout_plan_instances (
                id, user_id, status, scenario, confidence, title,
                approved_workout_plan_json, selected_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                102,
                "completed",
                "aligned_managed",
                "High",
                "Fixture Plan",
                "{}",
                workout_date,
                workout_date,
            ),
        )
        connection.execute(
            """
            INSERT INTO planned_workout_exercises (
                workout_plan_instance_id, exercise_order, name, sets, reps_min,
                reps_max, rir_min, rir_max, notes, equipment_required_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, 1, "Goblet Squat", 3, 8, 12, 2, 3, "private", "[]"),
        )
        connection.execute(
            """
            INSERT INTO workout_execution_sessions (
                id, workout_plan_instance_id, user_id, status,
                workout_session_id, started_at, completed_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                session_id,
                102,
                "completed",
                session_id,
                f"{workout_date}T10:00:00",
                f"{workout_date}T11:00:00",
                f"{workout_date}T09:00:00",
            ),
        )
        for set_number in (1, 2):
            connection.execute(
                """
                INSERT INTO workout_execution_set_actuals (
                    workout_execution_session_id, workout_session_id,
                    exercise_name, set_number, completed, skipped, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    session_id,
                    "Goblet Squat",
                    set_number,
                    1,
                    0,
                    "private set note must not leak",
                    f"{workout_date}T10:10:00",
                ),
            )
    connection.execute(
        "INSERT INTO daily_checkins (user_id, checkin_date, notes) VALUES (?, ?, ?)",
        (105, "2026-06-09", "private sparse note must not leak"),
    )
    connection.commit()
    connection.close()


def test_qa_range_defaults_are_stable() -> None:
    assert DEFAULT_QA_DATE_RANGE_USER_ID == 102
    assert DEFAULT_QA_LOW_DATA_USER_ID == 105
    assert DEFAULT_QA_DATE_RANGE_PRESET_KEY == "latest_seeded_week"
    assert QA_DATE_RANGE_PRESETS["latest_seeded_week"] == (
        "2026-06-08",
        "2026-06-14",
    )
    assert QA_USER_LABELS[102] == "102 aligned_managed"


def test_qa_range_preset_and_cache_key_are_typed() -> None:
    start, end = qa_range_preset_dates("latest_seeded_week")
    assert start.isoformat() == "2026-06-08"
    assert end.isoformat() == "2026-06-14"
    assert qa_date_range_cache_key(102, start, end) == (
        "user:102|start:2026-06-08|end:2026-06-14"
    )


def test_inspect_weekly_summary_qa_range_returns_safe_inventory(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "qa.db"
    create_qa_range_fixture_db(db_path)
    inventory = inspect_weekly_summary_qa_range(
        user_id=102,
        start_date="2026-06-08",
        end_date="2026-06-14",
        db_path=db_path,
    )
    payload_text = str(inventory.to_dict()).lower()
    assert inventory.user_id == 102
    assert inventory.scenario == "aligned_managed"
    assert inventory.data_quality_label == "strong"
    assert inventory.fact_counts["recovery"] == 7
    assert inventory.distinct_logged_days["nutrition"] == 7
    assert inventory.fact_counts["actual_sets"] == 6
    assert inventory.public_safe is True
    assert inventory.deterministic_provider_free is True
    assert "private" not in payload_text
    assert "raw_provider_output" not in payload_text


def test_low_data_user_inventory_is_limited_but_safe(tmp_path: Path) -> None:
    db_path = tmp_path / "qa.db"
    create_qa_range_fixture_db(db_path)
    inventory = inspect_weekly_summary_qa_range(
        user_id=105,
        start_date="2026-06-08",
        end_date="2026-06-14",
        db_path=db_path,
    )
    assert inventory.user_id == 105
    assert inventory.scenario == "data_quality_limited"
    assert inventory.data_quality_label in {"limited", "insufficient"}
    assert inventory.public_safe is True


def test_out_of_range_inventory_warns_with_available_bounds(tmp_path: Path) -> None:
    db_path = tmp_path / "qa.db"
    create_qa_range_fixture_db(db_path)
    inventory = inspect_weekly_summary_qa_range(
        user_id=102,
        start_date="2030-01-01",
        end_date="2030-01-07",
        db_path=db_path,
    )
    assert inventory.selected_range_has_data is False
    assert inventory.available_start_date == "2026-06-08"
    assert inventory.available_end_date == "2026-06-14"
    assert "selected_range_out_of_bounds" in inventory.diagnosis_codes


def test_build_context_from_qa_range_uses_selected_user_and_dates(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "qa.db"
    create_qa_range_fixture_db(db_path)
    context = build_weekly_summary_context_from_qa_range(
        user_id=102,
        start_date="2026-06-08",
        end_date="2026-06-14",
        db_path=db_path,
    )
    assert context.user_id == 102
    assert context.period.week_start.isoformat() == "2026-06-08"
    assert context.period.week_end.isoformat() == "2026-06-14"
    assert context.fact_boundary.training_facts_available is True
    assert context.fact_boundary.nutrition_facts_available is True
    assert context.confidence in {
        WeeklyCoachSummaryConfidence.MODERATE,
        WeeklyCoachSummaryConfidence.HIGH,
    }
    assert "approved_backend_facts_only" in context.reason_codes
