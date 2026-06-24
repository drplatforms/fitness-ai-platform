from __future__ import annotations

import sqlite3
from pathlib import Path

from services.runtime_diagnostics_service import (
    build_database_source,
    build_qa_seed_diagnostics,
    build_runtime_db_diagnostics,
    build_runtime_identity,
)


def create_runtime_test_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
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
    conn.execute("INSERT INTO users (id, name) VALUES (?, ?)", (102, "QA 102"))
    conn.execute(
        "INSERT INTO daily_checkins (user_id, checkin_date, notes) VALUES (?, ?, ?)",
        (102, "2026-06-08", "private check-in note must not appear"),
    )
    conn.execute(
        """
        INSERT INTO food_entries (user_id, food_id, grams, entry_date)
        VALUES (?, ?, ?, ?)
        """,
        (102, 1, 100.0, "2026-06-09"),
    )
    conn.execute(
        "INSERT INTO workout_sessions (id, user_id, workout_date) VALUES (?, ?, ?)",
        (7, 102, "2026-06-10"),
    )
    conn.execute(
        """
        INSERT INTO workout_execution_sessions (
            id,
            workout_plan_instance_id,
            user_id,
            status,
            workout_session_id,
            started_at,
            completed_at,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            9,
            4,
            102,
            "completed",
            7,
            "2026-06-10T10:00:00",
            "2026-06-10T11:00:00",
            "2026-06-10T09:00:00",
        ),
    )
    conn.execute(
        """
        INSERT INTO workout_execution_set_actuals (
            workout_execution_session_id,
            workout_session_id,
            exercise_name,
            set_number,
            completed,
            skipped,
            notes,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            9,
            7,
            "Goblet Squat",
            1,
            1,
            0,
            "private set note must not appear",
            "2026-06-10T10:10:00",
        ),
    )
    conn.commit()
    conn.close()


def test_runtime_identity_returns_safe_fields() -> None:
    identity = build_runtime_identity()

    assert "git_commit_short" in identity
    assert "git_commit_full" in identity
    assert "git_branch" in identity
    assert "repository_root" in identity
    assert "current_working_directory" in identity
    assert "python_executable" in identity
    assert "python_version" in identity
    assert "platform" in identity


def test_runtime_identity_handles_missing_git_metadata(tmp_path: Path) -> None:
    identity = build_runtime_identity(repo_root=tmp_path)

    assert identity["git_metadata_available"] is False
    assert identity["git_commit_short"] is None
    assert identity["git_branch"] is None
    assert identity["dirty_working_tree"] is None


def test_database_source_returns_missing_db_state_safely(tmp_path: Path) -> None:
    missing_db = tmp_path / "missing.db"

    source = build_database_source(db_path=missing_db)

    assert source["database_exists"] is False
    assert source["sqlite_connectable"] is False
    assert source["error_category"] == "database_missing"
    assert str(missing_db) in source["resolved_database_path"]


def test_database_source_returns_connectable_state(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime.db"
    create_runtime_test_db(db_path)

    source = build_database_source(db_path=db_path)

    assert source["database_exists"] is True
    assert source["sqlite_connectable"] is True
    assert source["database_file_size_bytes"] > 0
    assert "users" in source["relevant_tables_found"]
    assert "daily_checkins" in source["relevant_tables_found"]


def test_qa_seed_diagnostics_return_empty_state_when_users_absent(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "empty_users.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    conn.commit()
    conn.close()

    diagnostics = build_qa_seed_diagnostics(db_path=db_path)

    assert len(diagnostics) == 5
    assert all(user["user_exists"] is False for user in diagnostics)
    assert {user["user_id"] for user in diagnostics} == {101, 102, 103, 104, 105}


def test_qa_seed_diagnostics_return_counts_and_bounds(tmp_path: Path) -> None:
    db_path = tmp_path / "qa_seed.db"
    create_runtime_test_db(db_path)

    diagnostics = build_qa_seed_diagnostics(db_path=db_path)
    user_102 = next(user for user in diagnostics if user["user_id"] == 102)

    assert user_102["user_exists"] is True
    assert user_102["scenario"] == "aligned_managed"
    assert user_102["recovery"]["row_count"] == 1
    assert user_102["recovery"]["min_date"] == "2026-06-08"
    assert user_102["nutrition"]["row_count"] == 1
    assert user_102["nutrition"]["max_date"] == "2026-06-09"
    assert user_102["workouts"]["row_count"] == 1
    assert user_102["workouts"]["min_date"] == "2026-06-10"
    assert user_102["actual_sets"]["row_count"] == 1
    assert user_102["actual_sets"]["max_date"] == "2026-06-10"


def test_runtime_diagnostics_do_not_return_raw_rows_or_private_notes(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "private_rows.db"
    create_runtime_test_db(db_path)

    diagnostics = build_runtime_db_diagnostics(
        api_base_url="http://127.0.0.1:8000",
        db_path=db_path,
        repo_root=tmp_path,
    )
    combined = repr(diagnostics)

    assert diagnostics["success"] is True
    assert "private check-in note" not in combined
    assert "private set note" not in combined
    assert "OLLAMA" not in combined
    assert "API_KEY" not in combined
    assert "SECRET" not in combined


def test_runtime_diagnostics_warn_when_qa_users_absent(tmp_path: Path) -> None:
    db_path = tmp_path / "empty_users.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    conn.commit()
    conn.close()

    diagnostics = build_runtime_db_diagnostics(db_path=db_path, repo_root=tmp_path)

    assert "QA users 101-105 were not found" in " ".join(diagnostics["warnings"])
