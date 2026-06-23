from __future__ import annotations

import sqlite3

import database
from models.async_daily_coach_narrative_models import DailyCoachNarrativeJobStatus
from services.daily_coach_async_persistence_service import (
    create_approved_narrative,
    create_async_job,
    mark_async_job_displayable,
    mark_async_job_expired,
    mark_async_job_stale,
)
from services.daily_coach_async_provider_runtime_service import (
    APPROVED_PREVIEW_GATE_CONTEXT_MISMATCH,
    APPROVED_PREVIEW_GATE_DISABLED,
    APPROVED_PREVIEW_GATE_ELIGIBLE,
    APPROVED_PREVIEW_GATE_EXPIRED,
    APPROVED_PREVIEW_GATE_NO_NARRATIVE,
    APPROVED_PREVIEW_GATE_NOT_DISPLAYABLE,
    APPROVED_PREVIEW_GATE_SOURCE_NOT_ALLOWED,
    APPROVED_PREVIEW_GATE_STALE,
    DAILY_COACH_ASYNC_APPROVED_PREVIEW_ENABLED_ENV,
    DAILY_COACH_ASYNC_CONTEXT_VERSION,
    DAILY_COACH_ASYNC_PROMPT_CONTRACT_VERSION,
    DAILY_COACH_ASYNC_VALIDATOR_VERSION,
    FINAL_SOURCE_PROVIDER_APPROVED,
    build_daily_coach_async_approved_preview,
    resolve_daily_coach_async_approved_preview_config,
)


def _initialize_temp_database(tmp_path, monkeypatch):
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    return db_path


def _create_job(job_id: str = "preview-job"):
    return create_async_job(
        job_id=job_id,
        user_id=1,
        target_date="2026-06-22",
        workflow_target="nutrition",
        next_action_id="log_meal_or_snack",
        context_hash="context-hash-approved-preview",
        context_version=DAILY_COACH_ASYNC_CONTEXT_VERSION,
        prompt_contract_version=DAILY_COACH_ASYNC_PROMPT_CONTRACT_VERSION,
        validator_version=DAILY_COACH_ASYNC_VALIDATOR_VERSION,
        status=DailyCoachNarrativeJobStatus.APPROVED,
    )


def _create_eligible_narrative(job_id: str = "preview-job", **overrides):
    payload = {
        "job_id": job_id,
        "user_id": 1,
        "target_date": "2026-06-22",
        "context_hash": "context-hash-approved-preview",
        "context_version": DAILY_COACH_ASYNC_CONTEXT_VERSION,
        "approved_narrative_json": {
            "coach_note": "Log one meal or snack today so the nutrition picture gets clearer."
        },
        "approved_text": "Log one meal or snack today so the nutrition picture gets clearer.",
        "reason_codes_json": ["daily_coach_async_provider_approved"],
        "action_refs_json": [
            {"next_action_id": "log_meal_or_snack", "workflow_target": "nutrition"}
        ],
        "validator_version": DAILY_COACH_ASYNC_VALIDATOR_VERSION,
        "prompt_contract_version": DAILY_COACH_ASYNC_PROMPT_CONTRACT_VERSION,
        "final_narrative_source": FINAL_SOURCE_PROVIDER_APPROVED,
        "displayable": True,
        "public_safe": True,
    }
    payload.update(overrides)
    return create_approved_narrative(**payload)


def _eligible_env() -> dict[str, str]:
    return {DAILY_COACH_ASYNC_APPROVED_PREVIEW_ENABLED_ENV: "true"}


def test_preview_feature_flag_disabled_by_default_uses_isolated_empty_env(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    mark_async_job_displayable("preview-job")
    _create_eligible_narrative()

    config = resolve_daily_coach_async_approved_preview_config(environ={})
    result = build_daily_coach_async_approved_preview(
        user_id=1,
        target_date="2026-06-22",
        environ={},
    )

    assert config.enabled is False
    assert result.enabled is False
    assert result.eligible is False
    assert result.preview_text is None
    assert result.gate_status == APPROVED_PREVIEW_GATE_DISABLED


def test_enabled_preview_without_narrative_is_safe_and_does_not_call_provider(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    called = False

    def fake_provider(*args):
        nonlocal called
        called = True

    monkeypatch.setattr(
        "services.daily_coach_async_provider_runtime_service.call_ollama_generate",
        fake_provider,
    )

    result = build_daily_coach_async_approved_preview(
        user_id=1,
        target_date="2026-06-22",
        environ=_eligible_env(),
    )

    assert called is False
    assert result.enabled is True
    assert result.eligible is False
    assert result.gate_status == APPROVED_PREVIEW_GATE_NO_NARRATIVE
    assert result.preview_text is None


def test_enabled_preview_returns_eligible_persisted_narrative_without_provider_call(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    mark_async_job_displayable("preview-job")
    _create_eligible_narrative()
    called = False

    def fake_provider(*args):
        nonlocal called
        called = True

    monkeypatch.setattr(
        "services.daily_coach_async_provider_runtime_service.call_ollama_generate",
        fake_provider,
    )

    result = build_daily_coach_async_approved_preview(
        user_id=1,
        target_date="2026-06-22",
        environ=_eligible_env(),
        expected_context_hash="context-hash-approved-preview",
    )

    assert called is False
    assert result.enabled is True
    assert result.eligible is True
    assert result.gate_status == APPROVED_PREVIEW_GATE_ELIGIBLE
    assert result.preview_text == (
        "Log one meal or snack today so the nutrition picture gets clearer."
    )
    assert result.fallback_used is False
    assert result.to_normal_ui_dict() == {
        "enabled": True,
        "eligible": True,
        "preview_text": (
            "Log one meal or snack today so the nutrition picture gets clearer."
        ),
        "safe_user_message": None,
    }


def test_non_public_safe_narrative_is_hidden(tmp_path, monkeypatch):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    mark_async_job_displayable("preview-job")
    _create_eligible_narrative()
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE daily_coach_approved_narratives SET public_safe = 0")
    conn.commit()
    conn.close()

    result = build_daily_coach_async_approved_preview(
        user_id=1,
        target_date="2026-06-22",
        environ=_eligible_env(),
    )

    assert result.eligible is False
    assert result.preview_text is None
    assert result.gate_status == APPROVED_PREVIEW_GATE_NO_NARRATIVE


def test_non_displayable_job_is_hidden(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    _create_eligible_narrative()

    result = build_daily_coach_async_approved_preview(
        user_id=1,
        target_date="2026-06-22",
        environ=_eligible_env(),
    )

    assert result.eligible is False
    assert result.preview_text is None
    assert result.gate_status == APPROVED_PREVIEW_GATE_NOT_DISPLAYABLE


def test_stale_and_expired_jobs_are_hidden(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job("stale-job")
    mark_async_job_displayable("stale-job")
    _create_eligible_narrative("stale-job")
    mark_async_job_stale("stale-job")

    stale_result = build_daily_coach_async_approved_preview(
        user_id=1,
        target_date="2026-06-22",
        environ=_eligible_env(),
    )

    assert stale_result.eligible is False
    assert stale_result.gate_status == APPROVED_PREVIEW_GATE_STALE

    _create_job("expired-job")
    mark_async_job_displayable("expired-job")
    _create_eligible_narrative("expired-job")
    mark_async_job_expired("expired-job")

    expired_result = build_daily_coach_async_approved_preview(
        user_id=1,
        target_date="2026-06-22",
        environ=_eligible_env(),
    )

    assert expired_result.eligible is False
    assert expired_result.gate_status in {
        APPROVED_PREVIEW_GATE_EXPIRED,
        APPROVED_PREVIEW_GATE_STALE,
    }


def test_context_mismatch_is_hidden(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    mark_async_job_displayable("preview-job")
    _create_eligible_narrative()

    result = build_daily_coach_async_approved_preview(
        user_id=1,
        target_date="2026-06-22",
        environ=_eligible_env(),
        expected_context_hash="different-context-hash",
    )

    assert result.eligible is False
    assert result.preview_text is None
    assert result.gate_status == APPROVED_PREVIEW_GATE_CONTEXT_MISMATCH


def test_unapproved_final_source_is_hidden(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    mark_async_job_displayable("preview-job")
    _create_eligible_narrative(final_narrative_source="unapproved_source")

    result = build_daily_coach_async_approved_preview(
        user_id=1,
        target_date="2026-06-22",
        environ=_eligible_env(),
    )

    assert result.eligible is False
    assert result.preview_text is None
    assert result.gate_status == APPROVED_PREVIEW_GATE_SOURCE_NOT_ALLOWED


def test_normal_ui_result_never_contains_raw_or_rejected_fields(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    mark_async_job_displayable("preview-job")
    _create_eligible_narrative()

    result = build_daily_coach_async_approved_preview(
        user_id=1,
        target_date="2026-06-22",
        environ=_eligible_env(),
    )
    normal_payload = result.to_normal_ui_dict()
    joined_keys = " ".join(normal_payload.keys())

    assert "raw" not in joined_keys
    assert "rejected" not in joined_keys
    assert "prompt" not in joined_keys
    assert "context" not in joined_keys
    assert "scratchpad" not in joined_keys
    assert "developer_diagnostics" not in normal_payload
