from __future__ import annotations

import sqlite3

import database
from models.async_daily_coach_narrative_models import DailyCoachNarrativeJobStatus
from models.daily_coach_narrative_models import DailyCoachNarrativeContext
from services.daily_coach_async_persistence_service import (
    create_async_job,
    get_approved_narrative_by_job_id,
    get_async_job,
)
from services.daily_coach_async_provider_runtime_service import (
    DAILY_COACH_ASYNC_PROVIDER_DEFAULT_MODEL,
    DAILY_COACH_ASYNC_PROVIDER_DIRECT_OLLAMA,
    DAILY_COACH_ASYNC_PROVIDER_ENV,
    DAILY_COACH_ASYNC_PROVIDER_MODEL_ENV,
    DAILY_COACH_ASYNC_PROVIDER_RUNTIME_ENABLED_ENV,
    FALLBACK_REASON_PARSE_FAILURE,
    FALLBACK_REASON_RUNTIME_DISABLED,
    FALLBACK_REASON_UNAPPROVED_MODEL,
    create_developer_mode_provider_runtime_job,
    resolve_daily_coach_async_provider_runtime_config,
    run_daily_coach_async_provider_runtime_prototype,
)


def _initialize_temp_database(tmp_path, monkeypatch):
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    return db_path


def _context() -> DailyCoachNarrativeContext:
    return DailyCoachNarrativeContext(
        user_id=1,
        date="2026-06-22",
        next_action_id="log_meal_or_snack",
        next_action_title="Log a meal or snack",
        next_action_reason=(
            "Today's nutrition state is limited until more food data is logged."
        ),
        workflow_target="nutrition",
        priority=2,
        severity="low",
        approved_focus="Log a meal or snack",
        confidence_language="Keep this limited until more food data is logged.",
        approved_facts=[
            "Daily next action: Log a meal or snack",
            (
                "Daily next action reason: Today's nutrition state is limited until "
                "more food data is logged."
            ),
        ],
        approved_limitations=[
            "Do not add calorie, macro, meal-plan, workout, or medical claims."
        ],
        fallback_note="Log one meal or snack first.",
    )


def _create_provider_job(job_id: str = "job-1"):
    return create_async_job(
        job_id=job_id,
        user_id=1,
        target_date="2026-06-22",
        workflow_target="nutrition",
        next_action_id="log_meal_or_snack",
        context_hash="context-hash-1",
        context_version="context-v1",
        prompt_contract_version="prompt-v1",
        validator_version="validator-v1",
    )


def _enabled_env(**overrides: str) -> dict[str, str]:
    env = {
        DAILY_COACH_ASYNC_PROVIDER_RUNTIME_ENABLED_ENV: "true",
        DAILY_COACH_ASYNC_PROVIDER_ENV: DAILY_COACH_ASYNC_PROVIDER_DIRECT_OLLAMA,
        DAILY_COACH_ASYNC_PROVIDER_MODEL_ENV: DAILY_COACH_ASYNC_PROVIDER_DEFAULT_MODEL,
    }
    env.update(overrides)
    return env


def _valid_provider_output() -> str:
    return """
{
  "coach_note": "Log a meal or snack today to make the nutrition picture less fuzzy. Today's nutrition state is limited until more food data is logged, so start with one meal or snack.",
  "key_takeaway": "More food logging gives today's guidance a clearer base.",
  "recommended_focus": "Log a meal or snack",
  "confidence_language": "Keep this limited until more food data is logged.",
  "used_approved_facts": [
    "Daily next action: Log a meal or snack",
    "Daily next action reason: Today's nutrition state is limited until more food data is logged."
  ],
  "avoided_claims": [
    "No food, exercise, target, recovery, or medical claim was invented."
  ]
}
""".strip()


def test_runtime_config_is_disabled_by_default():
    config = resolve_daily_coach_async_provider_runtime_config({})

    assert config.enabled is False
    assert config.selected_provider == DAILY_COACH_ASYNC_PROVIDER_DIRECT_OLLAMA
    assert config.selected_model == DAILY_COACH_ASYNC_PROVIDER_DEFAULT_MODEL
    assert config.to_dict()["manual_trigger_required"] is True


def test_disabled_provider_runtime_does_not_call_provider(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    called = False

    def fake_generate(*args):
        nonlocal called
        called = True
        return _valid_provider_output()

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-1",
        environ={},
        generate=fake_generate,
    )

    assert called is False
    assert result.provider_attempted is False
    assert result.fallback_used is True
    assert result.fallback_reason == FALLBACK_REASON_RUNTIME_DISABLED
    assert get_approved_narrative_by_job_id("job-1") is None


def test_runtime_rejects_unapproved_qwen3_model_before_call(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    called = False

    def fake_generate(*args):
        nonlocal called
        called = True
        return _valid_provider_output()

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-1",
        environ=_enabled_env(**{DAILY_COACH_ASYNC_PROVIDER_MODEL_ENV: "qwen3:8b"}),
        generate=fake_generate,
    )

    assert called is False
    assert result.provider_attempted is False
    assert result.fallback_used is True
    assert result.fallback_reason == FALLBACK_REASON_UNAPPROVED_MODEL
    assert (
        get_async_job("job-1").status
        == DailyCoachNarrativeJobStatus.PROVIDER_ERROR.value
    )  # type: ignore[union-attr]


def test_successful_provider_output_persists_public_safe_narrative_only(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    monkeypatch.setattr(
        "services.daily_coach_async_provider_runtime_service.build_daily_coach_narrative_context",
        lambda user_id, target_date=None: _context(),
    )

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-1",
        environ=_enabled_env(),
        generate=lambda *args: _valid_provider_output(),
    )

    assert result.provider_attempted is True
    assert result.fallback_used is False
    assert result.approved_narrative_persisted is True
    assert result.raw_output_length is not None
    job = get_async_job("job-1")
    assert job is not None
    assert job.status == DailyCoachNarrativeJobStatus.APPROVED.value
    assert job.displayable is True
    assert job.public_safe is True
    assert job.provider_name == DAILY_COACH_ASYNC_PROVIDER_DIRECT_OLLAMA
    narrative = get_approved_narrative_by_job_id("job-1")
    assert narrative is not None
    assert narrative.public_safe is True
    assert narrative.displayable is True
    assert narrative.approved_text.startswith("Log a meal or snack")
    payload = narrative.to_dict()
    assert "raw_provider_output" not in payload
    assert "rejected_provider_output" not in payload
    assert "full_prompt" not in payload


def test_malformed_provider_output_records_sanitized_failure_only(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    monkeypatch.setattr(
        "services.daily_coach_async_provider_runtime_service.build_daily_coach_narrative_context",
        lambda user_id, target_date=None: _context(),
    )

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-1",
        environ=_enabled_env(),
        generate=lambda *args: "```json\n{}\n```",
    )

    assert result.provider_attempted is True
    assert result.fallback_used is True
    assert result.fallback_reason == FALLBACK_REASON_PARSE_FAILURE
    assert result.markdown_wrapper_detected is True
    assert get_approved_narrative_by_job_id("job-1") is None
    job = get_async_job("job-1")
    assert job is not None
    assert job.status == DailyCoachNarrativeJobStatus.REJECTED_PARSE.value
    assert job.raw_output_length is not None
    assert job.markdown_wrapper_detected is True
    assert job.fallback_reason == FALLBACK_REASON_PARSE_FAILURE
    assert "```" not in str(job.to_dict())


def test_provider_timeout_records_sanitized_metadata(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    monkeypatch.setattr(
        "services.daily_coach_async_provider_runtime_service.build_daily_coach_narrative_context",
        lambda user_id, target_date=None: _context(),
    )

    def timeout_generate(*args):
        raise TimeoutError("too slow")

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-1",
        environ=_enabled_env(),
        generate=timeout_generate,
    )

    assert result.provider_attempted is True
    assert result.fallback_used is True
    assert result.fallback_reason == "provider_timeout"
    assert get_approved_narrative_by_job_id("job-1") is None
    job = get_async_job("job-1")
    assert job is not None
    assert job.status == DailyCoachNarrativeJobStatus.PROVIDER_TIMEOUT.value
    assert job.raw_output_length is None


def test_create_developer_runtime_job_uses_persisted_schema(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)

    class Action:
        action_id = "log_meal_or_snack"
        workflow_target = "nutrition"

        def to_dict(self):
            return {
                "action_id": self.action_id,
                "workflow_target": self.workflow_target,
            }

    monkeypatch.setattr(
        "services.daily_coach_async_provider_runtime_service.build_daily_next_action",
        lambda user_id, target_date=None: Action(),
    )

    job = create_developer_mode_provider_runtime_job(
        user_id=1,
        target_date="2026-06-22",
        environ={},
    )

    assert job.user_id == 1
    assert job.target_date == "2026-06-22"
    assert job.status == DailyCoachNarrativeJobStatus.QUEUED.value

    conn = sqlite3.connect(database.DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM daily_coach_async_jobs").fetchone()[0]
    conn.close()
    assert count == 1


def test_create_developer_runtime_job_initializes_missing_async_tables(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)

    class Action:
        action_id = "log_meal_or_snack"
        workflow_target = "nutrition"

        def to_dict(self):
            return {
                "action_id": self.action_id,
                "workflow_target": self.workflow_target,
            }

    monkeypatch.setattr(
        "services.daily_coach_async_provider_runtime_service.build_daily_next_action",
        lambda user_id, target_date=None: Action(),
    )

    job = create_developer_mode_provider_runtime_job(
        user_id=1,
        target_date="2026-06-22",
        environ={},
    )

    assert job.user_id == 1
    assert job.status == DailyCoachNarrativeJobStatus.QUEUED.value

    conn = sqlite3.connect(database.DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM daily_coach_async_jobs").fetchone()[0]
    approved_table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' "
        "AND name = 'daily_coach_approved_narratives'"
    ).fetchone()
    conn.close()

    assert count == 1
    assert approved_table is not None
