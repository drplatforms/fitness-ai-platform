from __future__ import annotations

import sqlite3
from pathlib import Path

from models.weekly_coach_summary_models import WeeklyCoachSummaryConfidence
from services.weekly_coach_summary_qa_context_service import (
    build_weekly_summary_context_from_qa_range,
    build_weekly_summary_qa_context_signals,
    weekly_summary_context_to_safe_metadata,
)
from services.weekly_coach_summary_qa_data_service import (
    inspect_weekly_summary_qa_range,
)
from services.weekly_coach_summary_service import generate_approved_weekly_summary


def create_context_fixture_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE daily_checkins (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            checkin_date TEXT NOT NULL,
            sleep_hours REAL,
            energy_level INTEGER,
            soreness_level INTEGER,
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
        CREATE TABLE workout_sets (
            id INTEGER PRIMARY KEY,
            workout_session_id INTEGER NOT NULL,
            set_number INTEGER NOT NULL,
            reps INTEGER NOT NULL,
            weight REAL,
            rir INTEGER
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
    fixture_dates = [
        "2026-05-31",
        "2026-06-01",
        "2026-06-02",
        "2026-06-03",
        "2026-06-04",
        "2026-06-05",
        "2026-06-06",
    ]
    for index, checkin_date in enumerate(fixture_dates):
        connection.execute(
            """
            INSERT INTO daily_checkins (
                user_id, checkin_date, sleep_hours, energy_level, soreness_level, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                102,
                checkin_date,
                7.6 + (index % 3) * 0.2,
                8,
                2,
                "private check-in note must not leak",
            ),
        )
        connection.execute(
            """
            INSERT INTO food_entries (user_id, food_id, grams, entry_date)
            VALUES (?, ?, ?, ?)
            """,
            (102, 1, 100.0, checkin_date),
        )
    for session_id, workout_date in enumerate(
        ("2026-06-01", "2026-06-03", "2026-06-05"),
        start=1,
    ):
        connection.execute(
            "INSERT INTO workout_sessions (id, user_id, workout_date) VALUES (?, ?, ?)",
            (session_id, 102, workout_date),
        )
        for set_number in (1, 2):
            connection.execute(
                """
                INSERT INTO workout_sets (
                    workout_session_id, set_number, reps, weight, rir
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, set_number, 8, 100.0, 3),
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
        """
        INSERT INTO daily_checkins (
            user_id, checkin_date, sleep_hours, energy_level, soreness_level, notes
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (105, "2026-06-02", 6.2, 5, 6, "private sparse note must not leak"),
    )
    connection.commit()
    connection.close()


def test_context_service_builds_richer_selected_range_context(tmp_path: Path) -> None:
    db_path = tmp_path / "qa.db"
    create_context_fixture_db(db_path)

    context = build_weekly_summary_context_from_qa_range(
        user_id=102,
        start_date="2026-05-31",
        end_date="2026-06-06",
        db_path=db_path,
    )
    payload_text = str(context.to_dict()).lower()

    assert context.user_id == 102
    assert context.period.week_start.isoformat() == "2026-05-31"
    assert context.period.week_end.isoformat() == "2026-06-06"
    assert context.scenario == "aligned_managed"
    assert context.confidence == WeeklyCoachSummaryConfidence.HIGH
    assert context.fact_boundary.recovery_facts_available is True
    assert context.fact_boundary.nutrition_facts_available is True
    assert context.fact_boundary.training_facts_available is True
    assert context.fact_boundary.workout_execution_facts_available is True
    assert "qa_date_range_context_built" in context.reason_codes
    assert "qa_date_range_debug_source" in context.reason_codes
    assert "Average sleep was about" in context.recovery_summary
    assert "Nutrition coverage includes 7 entries" in context.nutrition_summary
    assert "Training coverage includes 3 sessions" in context.training_summary
    assert "private" not in payload_text
    assert "raw_database_rows" not in payload_text
    assert "raw_provider_output" not in payload_text


def test_context_signals_are_safe_aggregate_only(tmp_path: Path) -> None:
    db_path = tmp_path / "qa.db"
    create_context_fixture_db(db_path)
    inventory = inspect_weekly_summary_qa_range(
        user_id=102,
        start_date="2026-05-31",
        end_date="2026-06-06",
        db_path=db_path,
    )

    signals = build_weekly_summary_qa_context_signals(inventory, db_path=db_path)
    payload_text = str(signals.to_dict()).lower()

    assert signals.user_id == 102
    assert signals.source == "qa_date_range_debug"
    assert signals.recovery_checkins_count == 7
    assert signals.nutrition_logged_days == 7
    assert signals.average_energy_level == 8.0
    assert signals.average_training_rir == 3.0
    assert "private" not in payload_text
    assert "scratchpad" not in payload_text


def test_low_data_context_remains_limited_and_safe(tmp_path: Path) -> None:
    db_path = tmp_path / "qa.db"
    create_context_fixture_db(db_path)

    context = build_weekly_summary_context_from_qa_range(
        user_id=105,
        start_date="2026-05-31",
        end_date="2026-06-06",
        db_path=db_path,
    )
    approved = generate_approved_weekly_summary(context)

    assert context.user_id == 105
    assert context.scenario == "data_quality_limited"
    assert context.confidence == WeeklyCoachSummaryConfidence.LIMITED
    assert context.fact_boundary.data_quality_limited is True
    assert approved.public_safe is True
    assert approved.displayable is True
    assert "deterministic_fallback_used" in approved.reason_codes


def test_out_of_range_context_has_safe_insufficient_data_limitation(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "qa.db"
    create_context_fixture_db(db_path)

    context = build_weekly_summary_context_from_qa_range(
        user_id=102,
        start_date="2030-01-01",
        end_date="2030-01-07",
        db_path=db_path,
    )
    limitation_text = " ".join(context.limitations)

    assert context.confidence == WeeklyCoachSummaryConfidence.LIMITED
    assert context.fact_boundary.data_quality_limited is True
    assert "Selected range has no data for this user" in limitation_text
    assert "2026-05-31 to 2026-06-06" in limitation_text


def test_context_metadata_is_sanitized_for_developer_display(tmp_path: Path) -> None:
    db_path = tmp_path / "qa.db"
    create_context_fixture_db(db_path)
    context = build_weekly_summary_context_from_qa_range(
        user_id=102,
        start_date="2026-05-31",
        end_date="2026-06-06",
        db_path=db_path,
    )

    metadata = weekly_summary_context_to_safe_metadata(context)
    metadata_text = str(metadata).lower()

    assert metadata["user_id"] == 102
    assert metadata["source"] == "qa_date_range_debug"
    assert metadata["provider_attempted"] is False
    assert metadata["deterministic_provider_free"] is True
    assert "raw_provider_output" not in metadata_text
    assert "private" not in metadata_text
    assert "scratchpad" not in metadata_text
