from __future__ import annotations

import sqlite3
from pathlib import Path

import database
from models.async_daily_coach_narrative_models import DailyCoachNarrativeJobStatus
from services import daily_coach_async_provider_runtime_service as bridge_service
from services.daily_coach_async_persistence_service import (
    create_approved_narrative,
    create_async_job,
    mark_async_job_displayable,
    mark_async_job_expired,
    mark_async_job_stale,
)
from services.daily_coach_async_provider_runtime_service import (
    APPROVED_PREVIEW_GATE_CONTEXT_MISMATCH,
    APPROVED_PREVIEW_GATE_CONTEXT_VERSION_MISMATCH,
    APPROVED_PREVIEW_GATE_DISABLED,
    APPROVED_PREVIEW_GATE_ELIGIBLE,
    APPROVED_PREVIEW_GATE_EMPTY_TEXT,
    APPROVED_PREVIEW_GATE_EXPIRED,
    APPROVED_PREVIEW_GATE_JOB_NOT_APPROVED,
    APPROVED_PREVIEW_GATE_MISSING_JOB,
    APPROVED_PREVIEW_GATE_NO_NARRATIVE,
    APPROVED_PREVIEW_GATE_NOT_DISPLAYABLE,
    APPROVED_PREVIEW_GATE_PERSISTENCE_UNAVAILABLE,
    APPROVED_PREVIEW_GATE_PROMPT_CONTRACT_MISMATCH,
    APPROVED_PREVIEW_GATE_SOURCE_NOT_ALLOWED,
    APPROVED_PREVIEW_GATE_STALE,
    APPROVED_PREVIEW_GATE_VALIDATOR_VERSION_MISMATCH,
    DAILY_COACH_ASYNC_APPROVED_PREVIEW_ENABLED_ENV,
    DAILY_COACH_ASYNC_CONTEXT_VERSION,
    DAILY_COACH_ASYNC_PROMPT_CONTRACT_VERSION,
    DAILY_COACH_ASYNC_VALIDATOR_VERSION,
    FINAL_SOURCE_PROVIDER_APPROVED,
    build_daily_coach_async_approved_preview,
    resolve_daily_coach_async_approved_preview_config,
)

TARGET_DATE = "2026-06-23"
CONTEXT_HASH = "context-hash-approved-preview-qa"
PREVIEW_TEXT = (
    "Take the approved coaching step, then keep the deterministic action primary."
)
FORBIDDEN_NORMAL_UI_TERMS = {
    "provider_name",
    "provider_model",
    "parse_status",
    "validation_status",
    "raw_output_length",
    "markdown_wrapper_detected",
    "sanitized_error_category",
    "context_hash",
    "prompt_contract_version",
    "validator_version",
    "raw_provider_output",
    "rejected_provider_output",
    "full_prompt",
    "raw_context",
    "scratchpad",
    "traceback",
    "stack_trace",
}


def _initialize_temp_database(tmp_path, monkeypatch) -> Path:
    db_path = tmp_path / "fitness_ai_preview_qa.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    return db_path


def _create_job(
    job_id: str = "preview-qa-job",
    *,
    status: DailyCoachNarrativeJobStatus = DailyCoachNarrativeJobStatus.APPROVED,
    context_hash: str = CONTEXT_HASH,
    context_version: str = DAILY_COACH_ASYNC_CONTEXT_VERSION,
    validator_version: str = DAILY_COACH_ASYNC_VALIDATOR_VERSION,
    prompt_contract_version: str = DAILY_COACH_ASYNC_PROMPT_CONTRACT_VERSION,
):
    return create_async_job(
        job_id=job_id,
        user_id=102,
        target_date=TARGET_DATE,
        workflow_target="nutrition",
        next_action_id="log_meal_or_snack",
        context_hash=context_hash,
        context_version=context_version,
        prompt_contract_version=prompt_contract_version,
        validator_version=validator_version,
        status=status,
    )


def _create_narrative(job_id: str = "preview-qa-job", **overrides):
    payload = {
        "job_id": job_id,
        "user_id": 102,
        "target_date": TARGET_DATE,
        "context_hash": CONTEXT_HASH,
        "context_version": DAILY_COACH_ASYNC_CONTEXT_VERSION,
        "approved_narrative_json": {"coach_note": PREVIEW_TEXT},
        "approved_text": PREVIEW_TEXT,
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


def _enabled_env() -> dict[str, str]:
    return {DAILY_COACH_ASYNC_APPROVED_PREVIEW_ENABLED_ENV: "true"}


def _assert_bridge_does_not_call_provider_or_create_jobs(monkeypatch) -> None:
    def forbidden_provider_call(*args, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("Today approved preview bridge must not call provider")

    def forbidden_job_creation(*args, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("Today approved preview bridge must not create async jobs")

    monkeypatch.setattr(bridge_service, "call_ollama_generate", forbidden_provider_call)
    monkeypatch.setattr(bridge_service, "create_async_job", forbidden_job_creation)


def _enabled_preview(**kwargs):
    return build_daily_coach_async_approved_preview(
        user_id=102,
        target_date=TARGET_DATE,
        environ=_enabled_env(),
        expected_context_hash=CONTEXT_HASH,
        **kwargs,
    )


def test_qa_feature_flag_default_is_disabled_and_isolated_from_process_env(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    mark_async_job_displayable("preview-qa-job")
    _create_narrative()
    _assert_bridge_does_not_call_provider_or_create_jobs(monkeypatch)
    monkeypatch.setenv(DAILY_COACH_ASYNC_APPROVED_PREVIEW_ENABLED_ENV, "true")

    config = resolve_daily_coach_async_approved_preview_config(environ={})
    result = build_daily_coach_async_approved_preview(
        user_id=102,
        target_date=TARGET_DATE,
        environ={},
        expected_context_hash=CONTEXT_HASH,
    )

    assert config.enabled is False
    assert result.enabled is False
    assert result.eligible is False
    assert result.preview_text is None
    assert result.gate_status == APPROVED_PREVIEW_GATE_DISABLED


def test_qa_enabled_without_approved_narrative_is_safe_and_read_only(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _assert_bridge_does_not_call_provider_or_create_jobs(monkeypatch)

    result = _enabled_preview()

    assert result.enabled is True
    assert result.eligible is False
    assert result.preview_text is None
    assert result.gate_status == APPROVED_PREVIEW_GATE_NO_NARRATIVE
    assert result.safe_user_message is None


def test_qa_enabled_eligible_preview_is_read_only_secondary_and_normal_payload_safe(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    mark_async_job_displayable("preview-qa-job")
    _create_narrative()
    _assert_bridge_does_not_call_provider_or_create_jobs(monkeypatch)

    result = _enabled_preview()
    normal_payload = result.to_normal_ui_dict()

    assert result.enabled is True
    assert result.eligible is True
    assert result.gate_status == APPROVED_PREVIEW_GATE_ELIGIBLE
    assert result.preview_text == PREVIEW_TEXT
    assert result.fallback_used is False
    assert normal_payload == {
        "enabled": True,
        "eligible": True,
        "preview_text": PREVIEW_TEXT,
        "safe_user_message": None,
    }
    assert FORBIDDEN_NORMAL_UI_TERMS.isdisjoint(normal_payload.keys())


def test_qa_job_status_missing_stale_and_expired_jobs_are_hidden(
    tmp_path,
    monkeypatch,
):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)
    _create_job("queued-job", status=DailyCoachNarrativeJobStatus.QUEUED)
    _create_narrative("queued-job")
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE daily_coach_async_jobs SET displayable = 1, public_safe = 1 "
        "WHERE job_id = ?",
        ("queued-job",),
    )
    conn.commit()
    conn.close()
    _assert_bridge_does_not_call_provider_or_create_jobs(monkeypatch)

    queued = _enabled_preview()
    assert queued.eligible is False
    assert queued.preview_text is None
    assert queued.gate_status == APPROVED_PREVIEW_GATE_JOB_NOT_APPROVED

    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM daily_coach_async_jobs WHERE job_id = ?", ("queued-job",))
    conn.commit()
    conn.close()

    missing = _enabled_preview()
    assert missing.eligible is False
    assert missing.gate_status == APPROVED_PREVIEW_GATE_MISSING_JOB

    _create_job("stale-job")
    mark_async_job_displayable("stale-job")
    _create_narrative("stale-job")
    mark_async_job_stale("stale-job")
    stale = _enabled_preview()
    assert stale.eligible is False
    assert stale.preview_text is None
    assert stale.gate_status == APPROVED_PREVIEW_GATE_STALE

    _create_job("expired-job")
    mark_async_job_displayable("expired-job")
    _create_narrative("expired-job")
    mark_async_job_expired("expired-job")
    expired = _enabled_preview()
    assert expired.eligible is False
    assert expired.preview_text is None
    assert expired.gate_status in {
        APPROVED_PREVIEW_GATE_EXPIRED,
        APPROVED_PREVIEW_GATE_STALE,
    }


def test_qa_visibility_public_safety_and_empty_text_gates_hide_preview(
    tmp_path,
    monkeypatch,
):
    db_path = _initialize_temp_database(tmp_path, monkeypatch)
    _assert_bridge_does_not_call_provider_or_create_jobs(monkeypatch)

    _create_job("non-displayable-job")
    _create_narrative("non-displayable-job")
    non_displayable = _enabled_preview()
    assert non_displayable.eligible is False
    assert non_displayable.preview_text is None
    assert non_displayable.gate_status == APPROVED_PREVIEW_GATE_NOT_DISPLAYABLE

    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE daily_coach_async_jobs SET displayable = 1, public_safe = 1")
    conn.execute("UPDATE daily_coach_approved_narratives SET public_safe = 0")
    conn.commit()
    conn.close()

    non_public_safe = _enabled_preview()
    assert non_public_safe.eligible is False
    assert non_public_safe.preview_text is None
    assert non_public_safe.gate_status == APPROVED_PREVIEW_GATE_NO_NARRATIVE

    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE daily_coach_approved_narratives SET public_safe = 1")
    conn.execute("UPDATE daily_coach_approved_narratives SET approved_text = ''")
    conn.commit()
    conn.close()

    empty_text = _enabled_preview()
    assert empty_text.eligible is False
    assert empty_text.preview_text is None
    assert empty_text.gate_status == APPROVED_PREVIEW_GATE_EMPTY_TEXT


def test_qa_context_version_validator_prompt_and_source_gates_hide_preview(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _assert_bridge_does_not_call_provider_or_create_jobs(monkeypatch)

    _create_job("context-mismatch-job")
    mark_async_job_displayable("context-mismatch-job")
    _create_narrative("context-mismatch-job")
    context_mismatch = build_daily_coach_async_approved_preview(
        user_id=102,
        target_date=TARGET_DATE,
        environ=_enabled_env(),
        expected_context_hash="different-context-hash",
    )
    assert context_mismatch.gate_status == APPROVED_PREVIEW_GATE_CONTEXT_MISMATCH
    assert context_mismatch.preview_text is None

    _create_job("context-version-job")
    mark_async_job_displayable("context-version-job")
    _create_narrative(
        "context-version-job",
        context_version="old_context_version",
    )
    context_version = _enabled_preview()
    assert context_version.gate_status == APPROVED_PREVIEW_GATE_CONTEXT_VERSION_MISMATCH
    assert context_version.preview_text is None

    _create_job("validator-version-job")
    mark_async_job_displayable("validator-version-job")
    _create_narrative(
        "validator-version-job",
        validator_version="old_validator_version",
    )
    validator_version = _enabled_preview()
    assert (
        validator_version.gate_status
        == APPROVED_PREVIEW_GATE_VALIDATOR_VERSION_MISMATCH
    )
    assert validator_version.preview_text is None

    _create_job("prompt-contract-job")
    mark_async_job_displayable("prompt-contract-job")
    _create_narrative(
        "prompt-contract-job",
        prompt_contract_version="old_prompt_contract_version",
    )
    prompt_contract = _enabled_preview()
    assert prompt_contract.gate_status == APPROVED_PREVIEW_GATE_PROMPT_CONTRACT_MISMATCH
    assert prompt_contract.preview_text is None

    _create_job("source-job")
    mark_async_job_displayable("source-job")
    _create_narrative("source-job", final_narrative_source="unapproved_source")
    source = _enabled_preview()
    assert source.gate_status == APPROVED_PREVIEW_GATE_SOURCE_NOT_ALLOWED
    assert source.preview_text is None


def test_qa_persistence_unavailable_result_is_sanitized(monkeypatch):
    _assert_bridge_does_not_call_provider_or_create_jobs(monkeypatch)

    def unavailable_lookup(*args, **kwargs):
        raise sqlite3.OperationalError("no such table: daily_coach_approved_narratives")

    monkeypatch.setattr(
        bridge_service,
        "get_latest_displayable_approved_narrative",
        unavailable_lookup,
    )

    result = _enabled_preview()

    assert result.enabled is True
    assert result.eligible is False
    assert result.preview_text is None
    assert result.gate_status == APPROVED_PREVIEW_GATE_PERSISTENCE_UNAVAILABLE
    assert result.developer_diagnostics == {"feature_flag_enabled": True}
    assert result.to_normal_ui_dict() == {
        "enabled": True,
        "eligible": False,
        "preview_text": None,
        "safe_user_message": None,
    }


def test_qa_developer_diagnostics_are_sanitized_and_not_normal_payload(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_job()
    mark_async_job_displayable("preview-qa-job")
    _create_narrative()
    _assert_bridge_does_not_call_provider_or_create_jobs(monkeypatch)

    result = _enabled_preview()
    diagnostics = result.developer_diagnostics or {}
    normal_payload = result.to_normal_ui_dict()

    assert diagnostics["feature_flag_enabled"] is True
    assert diagnostics["approved_narrative_found"] is True
    assert diagnostics["context_hash_match"] is True
    assert "developer_diagnostics" not in normal_payload
    assert FORBIDDEN_NORMAL_UI_TERMS.isdisjoint(normal_payload.keys())
    assert "raw_provider_output" not in str(diagnostics)
    assert "rejected_provider_output" not in str(diagnostics)
    assert "full_prompt" not in str(diagnostics)
    assert "raw_context" not in str(diagnostics)
    assert "scratchpad" not in str(diagnostics)


def test_streamlit_qa_bridge_uses_normal_ui_payload_for_normal_rendering() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    start = source.index("def render_daily_coach_async_approved_preview_bridge")
    end = source.index("def render_daily_coach_async_provider_runtime_panel")
    bridge_source = source[start:end]
    normal_start = bridge_source.index("normal_preview = preview.to_normal_ui_dict()")
    developer_start = bridge_source.index(
        'if st.session_state.get("developer_mode", False)', normal_start
    )
    normal_source = bridge_source[normal_start:developer_start]

    assert "normal_preview = preview.to_normal_ui_dict()" in normal_source
    assert 'normal_preview.get("preview_text")' in normal_source
    assert "developer_diagnostics" not in normal_source
    assert "render_daily_coach_async_persistence_table" not in normal_source


def test_streamlit_qa_bridge_never_calls_provider_or_creates_jobs() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    start = source.index("def render_daily_coach_async_approved_preview_bridge")
    end = source.index("def render_daily_coach_async_provider_runtime_panel")
    bridge_source = source[start:end]

    forbidden_calls = [
        "call_ollama_generate",
        "create_developer_mode_provider_runtime_job",
        "run_daily_coach_async_provider_runtime_prototype",
        "create_async_job",
    ]
    for forbidden in forbidden_calls:
        assert forbidden not in bridge_source


def test_streamlit_qa_normal_bridge_source_excludes_provider_debug_metadata() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    start = source.index("def render_daily_coach_async_approved_preview_bridge")
    end = source.index("def render_daily_coach_async_provider_runtime_panel")
    bridge_source = source[start:end]
    normal_start = bridge_source.index("normal_preview = preview.to_normal_ui_dict()")
    developer_start = bridge_source.index(
        'if st.session_state.get("developer_mode", False)', normal_start
    )
    normal_source = bridge_source[normal_start:developer_start]

    forbidden_normal_source_terms = [
        "provider_model",
        "provider_name",
        "parse_status",
        "validation_status",
        "raw_output_length",
        "markdown_wrapper_detected",
        "sanitized_error_category",
        "context_hash",
        "prompt_contract_version",
        "validator_version",
        "raw provider output",
        "rejected output",
        "full prompt",
        "raw context",
        "scratchpad",
        "stack traces",
    ]
    lowered = normal_source.lower()
    for forbidden in forbidden_normal_source_terms:
        assert forbidden.lower() not in lowered
