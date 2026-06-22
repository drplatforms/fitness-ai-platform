from __future__ import annotations

import sqlite3

import pytest

import database
from models.async_daily_coach_narrative_models import DailyCoachNarrativeJobStatus
from services.daily_coach_async_persistence_service import (
    DailyCoachAsyncPersistenceValidationError,
    create_approved_narrative,
    create_async_job,
    get_approved_narrative_by_job_id,
    get_async_job,
    get_latest_displayable_approved_narrative,
    mark_async_job_displayable,
    mark_async_job_expired,
    mark_async_job_stale,
    record_async_job_failure_metadata,
    record_async_job_fallback,
    update_async_job_status,
)


def _initialize_temp_database(tmp_path, monkeypatch):
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    return db_path


def _create_job():
    return create_async_job(
        job_id="job-1",
        user_id=1,
        target_date="2026-06-22",
        workflow_target="today",
        next_action_id="review_daily_coach",
        context_hash="context-hash-1",
        context_version="context-v1",
        prompt_contract_version="prompt-v1",
        validator_version="validator-v1",
    )


def _table_columns(db_path, table_name):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    conn.close()
    return {row[1] for row in rows}


def test_create_and_read_daily_coach_async_job(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)

    job = _create_job()

    assert job.job_id == "job-1"
    assert job.status == DailyCoachNarrativeJobStatus.QUEUED.value
    assert job.user_id == 1
    assert job.displayable is False
    assert job.public_safe is False

    loaded = get_async_job("job-1")
    assert loaded is not None
    assert loaded.context_hash == "context-hash-1"


def test_update_daily_coach_async_job_status_and_lifecycle_fields(
    tmp_path, monkeypatch
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()

    generating = update_async_job_status(
        "job-1",
        DailyCoachNarrativeJobStatus.GENERATING,
        started_at="2026-06-22T10:00:00+00:00",
    )
    assert generating.status == DailyCoachNarrativeJobStatus.GENERATING.value
    assert generating.started_at == "2026-06-22T10:00:00+00:00"

    completed = update_async_job_status(
        "job-1",
        DailyCoachNarrativeJobStatus.PROVIDER_SUCCEEDED_PENDING_VALIDATION,
        completed_at="2026-06-22T10:05:00+00:00",
    )
    assert (
        completed.status
        == DailyCoachNarrativeJobStatus.PROVIDER_SUCCEEDED_PENDING_VALIDATION.value
    )
    assert completed.completed_at == "2026-06-22T10:05:00+00:00"


def test_mark_stale_expired_and_displayable_are_explicit_backend_methods(
    tmp_path, monkeypatch
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()

    displayable = mark_async_job_displayable("job-1")
    assert displayable.status == DailyCoachNarrativeJobStatus.APPROVED.value
    assert displayable.displayable is True
    assert displayable.public_safe is True

    stale = mark_async_job_stale("job-1")
    assert stale.status == DailyCoachNarrativeJobStatus.STALE.value
    assert stale.stale is True
    assert stale.displayable is False

    expired = mark_async_job_expired("job-1")
    assert expired.status == DailyCoachNarrativeJobStatus.EXPIRED.value
    assert expired.expired is True
    assert expired.displayable is False


def test_record_sanitized_failure_and_fallback_metadata(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()

    updated = record_async_job_failure_metadata(
        "job-1",
        provider_attempted=True,
        provider_name="direct_ollama",
        provider_model="qwen2.5:3b",
        parse_status="failed",
        validation_status="not_attempted",
        sanitized_error_category="malformed_json",
        raw_output_length=123,
        raw_output_preview_truncated=True,
        markdown_wrapper_detected=True,
    )

    assert updated.provider_attempted is True
    assert updated.provider_name == "direct_ollama"
    assert updated.raw_output_length == 123
    assert updated.raw_output_preview_truncated is True
    assert updated.markdown_wrapper_detected is True

    fallback = record_async_job_fallback(
        "job-1",
        fallback_reason="provider_timeout",
    )

    assert fallback.fallback_used is True
    assert fallback.fallback_reason == "provider_timeout"
    assert fallback.final_narrative_source == "deterministic_fallback"


def test_create_and_read_approved_narrative_from_public_safe_input(
    tmp_path, monkeypatch
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    mark_async_job_displayable("job-1")

    narrative = create_approved_narrative(
        narrative_id="narrative-1",
        job_id="job-1",
        user_id=1,
        target_date="2026-06-22",
        context_hash="context-hash-1",
        context_version="context-v1",
        approved_narrative_json={
            "narrative": "Keep today simple and controlled.",
            "source": "deterministic",
        },
        approved_text="Keep today simple and controlled.",
        reason_codes_json=["daily_coach_async_safe"],
        action_refs_json=["review_daily_coach"],
        validator_version="validator-v1",
        prompt_contract_version="prompt-v1",
        final_narrative_source="deterministic",
        displayable=True,
        public_safe=True,
    )

    assert narrative.narrative_id == "narrative-1"
    assert narrative.public_safe is True
    assert narrative.displayable is True
    assert narrative.approved_narrative_payload["source"] == "deterministic"
    assert narrative.reason_codes == ["daily_coach_async_safe"]

    loaded = get_approved_narrative_by_job_id("job-1")
    assert loaded is not None
    assert loaded.approved_text == "Keep today simple and controlled."


def test_get_latest_displayable_approved_narrative_filters_by_user_and_date(
    tmp_path, monkeypatch
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    mark_async_job_displayable("job-1")

    create_approved_narrative(
        narrative_id="narrative-1",
        job_id="job-1",
        user_id=1,
        target_date="2026-06-22",
        context_hash="context-hash-1",
        context_version="context-v1",
        approved_narrative_json={"narrative": "Approved."},
        approved_text="Approved.",
        validator_version="validator-v1",
        prompt_contract_version="prompt-v1",
        final_narrative_source="deterministic",
        stale=False,
        expired=False,
        displayable=True,
        public_safe=True,
    )

    latest = get_latest_displayable_approved_narrative(
        user_id=1,
        target_date="2026-06-22",
    )

    assert latest is not None
    assert latest.narrative_id == "narrative-1"
    assert (
        get_latest_displayable_approved_narrative(
            user_id=1,
            target_date="2030-01-01",
        )
        is None
    )


def test_service_rejects_forbidden_raw_or_rejected_provider_fields(
    tmp_path, monkeypatch
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()

    with pytest.raises(DailyCoachAsyncPersistenceValidationError):
        create_async_job(
            job_id="job-raw",
            user_id=1,
            target_date="2026-06-22",
            workflow_target="today",
            next_action_id="review_daily_coach",
            context_hash="context-hash-raw",
            context_version="context-v1",
            prompt_contract_version="prompt-v1",
            validator_version="validator-v1",
            raw_provider_output="forbidden",
        )

    with pytest.raises(DailyCoachAsyncPersistenceValidationError):
        record_async_job_failure_metadata(
            "job-1",
            rejected_provider_output="forbidden",
        )

    with pytest.raises(DailyCoachAsyncPersistenceValidationError):
        create_approved_narrative(
            job_id="job-1",
            user_id=1,
            target_date="2026-06-22",
            context_hash="context-hash-1",
            context_version="context-v1",
            approved_narrative_json={
                "narrative": "Bad payload.",
                "raw_provider_output": "forbidden",
            },
            approved_text="Bad payload.",
            validator_version="validator-v1",
            prompt_contract_version="prompt-v1",
            final_narrative_source="deterministic",
        )


def test_approved_narrative_requires_public_safe_input(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()

    with pytest.raises(DailyCoachAsyncPersistenceValidationError):
        create_approved_narrative(
            job_id="job-1",
            user_id=1,
            target_date="2026-06-22",
            context_hash="context-hash-1",
            context_version="context-v1",
            approved_narrative_json={"narrative": "Unsafe."},
            approved_text="Unsafe.",
            validator_version="validator-v1",
            prompt_contract_version="prompt-v1",
            final_narrative_source="deterministic",
            public_safe=False,
        )


def test_service_shell_does_not_add_raw_provider_columns(tmp_path, monkeypatch):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)

    job_columns = _table_columns(db_path, "daily_coach_async_jobs")
    narrative_columns = _table_columns(db_path, "daily_coach_approved_narratives")
    all_columns = job_columns | narrative_columns

    forbidden_fragments = {
        "raw_provider_output",
        "provider_raw_output",
        "rejected_provider_output",
        "raw_model_output",
        "raw_llm_output",
        "full_prompt",
        "prompt_text",
        "raw_prompt",
        "raw_context",
        "raw_database_rows",
        "raw_user_notes",
        "scratchpad",
        "chain_of_thought",
        "validation_bypass",
        "secrets",
        "environment_values",
        "stack_trace",
        "traceback",
    }

    assert not any(
        fragment in column_name
        for fragment in forbidden_fragments
        for column_name in all_columns
    )
