from __future__ import annotations

import sqlite3
from pathlib import Path

import database
from models.async_daily_coach_narrative_models import (
    DAILY_COACH_APPROVED_NARRATIVE_REQUIRED_COLUMNS,
    DAILY_COACH_APPROVED_NARRATIVE_TABLE,
    DAILY_COACH_ASYNC_JOB_REQUIRED_COLUMNS,
    DAILY_COACH_ASYNC_JOB_TABLE,
    DAILY_COACH_ASYNC_PERSISTENCE_FORBIDDEN_COLUMNS,
    DAILY_COACH_NARRATIVE_JOB_STATUSES,
)


def _initialize_temp_database(tmp_path, monkeypatch):
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    return db_path


def _table_columns(db_path, table_name):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    conn.close()
    return {row[1] for row in rows}


def _table_sql(db_path, table_name):
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    conn.close()
    assert row is not None
    return row[0]


def _table_names(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    conn.close()
    return {row[0] for row in rows}


def test_daily_coach_async_persistence_tables_are_created(tmp_path, monkeypatch):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)

    tables = _table_names(db_path)

    assert DAILY_COACH_ASYNC_JOB_TABLE in tables
    assert DAILY_COACH_APPROVED_NARRATIVE_TABLE in tables
    assert "daily_coach_job_events" not in tables


def test_daily_coach_async_jobs_required_columns_exist(tmp_path, monkeypatch):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)

    columns = _table_columns(db_path, DAILY_COACH_ASYNC_JOB_TABLE)

    assert set(DAILY_COACH_ASYNC_JOB_REQUIRED_COLUMNS).issubset(columns)


def test_daily_coach_approved_narratives_required_columns_exist(tmp_path, monkeypatch):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)

    columns = _table_columns(db_path, DAILY_COACH_APPROVED_NARRATIVE_TABLE)

    assert set(DAILY_COACH_APPROVED_NARRATIVE_REQUIRED_COLUMNS).issubset(columns)


def test_daily_coach_async_persistence_forbidden_columns_absent(tmp_path, monkeypatch):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)

    job_columns = _table_columns(db_path, DAILY_COACH_ASYNC_JOB_TABLE)
    narrative_columns = _table_columns(db_path, DAILY_COACH_APPROVED_NARRATIVE_TABLE)
    all_columns = job_columns | narrative_columns

    assert all_columns.isdisjoint(DAILY_COACH_ASYNC_PERSISTENCE_FORBIDDEN_COLUMNS)

    forbidden_fragments = {
        "raw_provider_output",
        "rejected_provider_output",
        "raw_model_output",
        "raw_llm_output",
        "full_prompt",
        "raw_context",
        "scratchpad",
        "chain_of_thought",
    }
    assert not any(
        fragment in column_name
        for fragment in forbidden_fragments
        for column_name in all_columns
    )


def test_daily_coach_async_job_status_check_constraint_matches_contract(
    tmp_path, monkeypatch
):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)

    create_sql = _table_sql(db_path, DAILY_COACH_ASYNC_JOB_TABLE)

    for status in DAILY_COACH_NARRATIVE_JOB_STATUSES:
        assert f"'{status}'" in create_sql
    assert "'expired'" in create_sql


def test_daily_coach_async_persistence_public_safety_flags_exist(tmp_path, monkeypatch):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)

    required_flags = {"stale", "expired", "displayable", "public_safe"}
    job_columns = _table_columns(db_path, DAILY_COACH_ASYNC_JOB_TABLE)
    narrative_columns = _table_columns(db_path, DAILY_COACH_APPROVED_NARRATIVE_TABLE)

    assert required_flags.issubset(job_columns)
    assert required_flags.issubset(narrative_columns)


def test_daily_coach_async_persistence_context_identity_fields_exist(
    tmp_path, monkeypatch
):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)

    required_fields = {
        "user_id",
        "target_date",
        "context_hash",
        "context_version",
        "validator_version",
        "prompt_contract_version",
    }
    job_columns = _table_columns(db_path, DAILY_COACH_ASYNC_JOB_TABLE)
    narrative_columns = _table_columns(db_path, DAILY_COACH_APPROVED_NARRATIVE_TABLE)

    assert required_fields.issubset(job_columns)
    assert required_fields.issubset(narrative_columns)


def test_daily_coach_async_persistence_is_schema_only_not_runtime():
    database_text = Path("database.py").read_text(encoding="utf-8")
    models_text = Path("models/async_daily_coach_narrative_models.py").read_text(
        encoding="utf-8"
    )
    combined = "\n".join([database_text, models_text])

    assert "direct_ollama(" not in combined
    assert "requests." not in combined
    assert "httpx" not in combined
    assert "subprocess" not in combined
    assert "BackgroundTasks" not in combined
    assert "asyncio.create_task" not in combined
    assert "threading.Thread" not in combined
    assert "streamlit" not in combined
    assert "uvicorn" not in combined
