from __future__ import annotations

import sqlite3

import database
from models.async_daily_coach_narrative_models import DailyCoachNarrativeJobStatus
from models.daily_coach_narrative_models import (
    DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
    DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS,
    DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED,
    DailyCoachNarrativeContext,
    DailyCoachNarrativeValidationResult,
)
from services.daily_coach_async_persistence_service import (
    create_async_job,
    get_approved_narrative_by_job_id,
    get_async_job,
    mark_async_job_expired,
    mark_async_job_stale,
)
from services.daily_coach_async_provider_runtime_service import (
    DAILY_COACH_ASYNC_PROVIDER_DEFAULT_MODEL,
    DAILY_COACH_ASYNC_PROVIDER_DIRECT_OLLAMA,
    DAILY_COACH_ASYNC_PROVIDER_ENV,
    DAILY_COACH_ASYNC_PROVIDER_MODEL_ENV,
    DAILY_COACH_ASYNC_PROVIDER_RUNTIME_ENABLED_ENV,
    FALLBACK_REASON_EXPIRED_JOB,
    FALLBACK_REASON_MISSING_JOB,
    FALLBACK_REASON_MODEL_CONFIG_MISSING,
    FALLBACK_REASON_PARSE_FAILURE,
    FALLBACK_REASON_PERSISTENCE_FAILURE,
    FALLBACK_REASON_PROVIDER_CONFIG_MISSING,
    FALLBACK_REASON_PROVIDER_UNAVAILABLE,
    FALLBACK_REASON_STALE_JOB,
    FALLBACK_REASON_VALIDATION_FAILURE,
    run_daily_coach_async_provider_runtime_prototype,
)


def _initialize_temp_database(tmp_path, monkeypatch):
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    return db_path


def _create_provider_job(job_id: str = "job-qa-hardening"):
    return create_async_job(
        job_id=job_id,
        user_id=1,
        target_date="2026-06-22",
        workflow_target="nutrition",
        next_action_id="log_meal_or_snack",
        context_hash="context-hash-qa-hardening",
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


def _patch_context(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.daily_coach_async_provider_runtime_service.build_daily_coach_narrative_context",
        lambda user_id, target_date=None: _context(),
    )


def test_enabled_runtime_missing_provider_config_does_not_call_provider(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    called = False

    def fake_generate(*args):
        nonlocal called
        called = True
        return _valid_provider_output()

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-qa-hardening",
        environ={
            DAILY_COACH_ASYNC_PROVIDER_RUNTIME_ENABLED_ENV: "true",
            DAILY_COACH_ASYNC_PROVIDER_MODEL_ENV: DAILY_COACH_ASYNC_PROVIDER_DEFAULT_MODEL,
        },
        generate=fake_generate,
    )

    assert called is False
    assert result.provider_attempted is False
    assert result.fallback_reason == FALLBACK_REASON_PROVIDER_CONFIG_MISSING
    assert result.sanitized_error_category == FALLBACK_REASON_PROVIDER_CONFIG_MISSING
    job = get_async_job("job-qa-hardening")
    assert job is not None
    assert job.status == DailyCoachNarrativeJobStatus.PROVIDER_ERROR.value
    assert job.sanitized_error_category == FALLBACK_REASON_PROVIDER_CONFIG_MISSING


def test_enabled_runtime_missing_model_config_does_not_call_provider(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    called = False

    def fake_generate(*args):
        nonlocal called
        called = True
        return _valid_provider_output()

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-qa-hardening",
        environ={
            DAILY_COACH_ASYNC_PROVIDER_RUNTIME_ENABLED_ENV: "true",
            DAILY_COACH_ASYNC_PROVIDER_ENV: DAILY_COACH_ASYNC_PROVIDER_DIRECT_OLLAMA,
        },
        generate=fake_generate,
    )

    assert called is False
    assert result.provider_attempted is False
    assert result.fallback_reason == FALLBACK_REASON_MODEL_CONFIG_MISSING
    assert result.sanitized_error_category == FALLBACK_REASON_MODEL_CONFIG_MISSING
    job = get_async_job("job-qa-hardening")
    assert job is not None
    assert job.provider_attempted is False
    assert job.sanitized_error_category == FALLBACK_REASON_MODEL_CONFIG_MISSING


def test_missing_job_is_sanitized_and_does_not_call_provider(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    called = False

    def fake_generate(*args):
        nonlocal called
        called = True
        return _valid_provider_output()

    result = run_daily_coach_async_provider_runtime_prototype(
        "missing-job-id",
        environ=_enabled_env(),
        generate=fake_generate,
    )

    assert called is False
    assert result.job_id is None
    assert result.provider_attempted is False
    assert result.fallback_reason == FALLBACK_REASON_MISSING_JOB
    assert result.sanitized_error_category == FALLBACK_REASON_MISSING_JOB


def test_stale_job_is_sanitized_and_does_not_call_provider(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    mark_async_job_stale("job-qa-hardening")
    called = False

    def fake_generate(*args):
        nonlocal called
        called = True
        return _valid_provider_output()

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-qa-hardening",
        environ=_enabled_env(),
        generate=fake_generate,
    )

    assert called is False
    assert result.provider_attempted is False
    assert result.fallback_reason == FALLBACK_REASON_STALE_JOB
    assert result.sanitized_error_category == FALLBACK_REASON_STALE_JOB
    assert get_approved_narrative_by_job_id("job-qa-hardening") is None


def test_expired_job_is_sanitized_and_does_not_call_provider(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    mark_async_job_expired("job-qa-hardening")
    called = False

    def fake_generate(*args):
        nonlocal called
        called = True
        return _valid_provider_output()

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-qa-hardening",
        environ=_enabled_env(),
        generate=fake_generate,
    )

    assert called is False
    assert result.provider_attempted is False
    assert result.fallback_reason == FALLBACK_REASON_EXPIRED_JOB
    assert result.sanitized_error_category == FALLBACK_REASON_EXPIRED_JOB
    assert get_approved_narrative_by_job_id("job-qa-hardening") is None


def test_provider_unavailable_result_is_sanitized(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    _patch_context(monkeypatch)

    def unavailable_generate(*args):
        raise ConnectionError("ollama refused connection with details")

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-qa-hardening",
        environ=_enabled_env(),
        generate=unavailable_generate,
    )

    assert result.provider_attempted is True
    assert result.fallback_reason == FALLBACK_REASON_PROVIDER_UNAVAILABLE
    assert result.sanitized_error_category == FALLBACK_REASON_PROVIDER_UNAVAILABLE
    assert "refused" not in str(result.to_dict()).lower()
    job = get_async_job("job-qa-hardening")
    assert job is not None
    assert job.status == DailyCoachNarrativeJobStatus.PROVIDER_ERROR.value
    assert job.sanitized_error_category == FALLBACK_REASON_PROVIDER_UNAVAILABLE
    assert get_approved_narrative_by_job_id("job-qa-hardening") is None


def test_prose_output_records_parse_failure_without_raw_text(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    _patch_context(monkeypatch)
    prose = "Here is the answer instead of JSON: eat chicken and follow a meal plan."

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-qa-hardening",
        environ=_enabled_env(),
        generate=lambda *args: prose,
    )

    assert result.provider_attempted is True
    assert result.fallback_reason == FALLBACK_REASON_PARSE_FAILURE
    assert result.parse_status == DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED
    assert result.raw_output_length == len(prose)
    job = get_async_job("job-qa-hardening")
    assert job is not None
    assert job.raw_output_length == len(prose)
    assert "meal plan" not in str(job.to_dict()).lower()
    assert get_approved_narrative_by_job_id("job-qa-hardening") is None


def test_validation_rejection_records_sanitized_metadata_only(tmp_path, monkeypatch):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    _patch_context(monkeypatch)

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-qa-hardening",
        environ=_enabled_env(),
        generate=lambda *args: _valid_provider_output().replace(
            "Log a meal or snack",
            "Follow a meal plan",
            1,
        ),
    )

    assert result.provider_attempted is True
    assert result.fallback_reason == FALLBACK_REASON_VALIDATION_FAILURE
    assert result.parse_status == DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS
    assert result.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
    job = get_async_job("job-qa-hardening")
    assert job is not None
    assert job.status == DailyCoachNarrativeJobStatus.REJECTED_VALIDATION.value
    assert job.sanitized_error_category == FALLBACK_REASON_VALIDATION_FAILURE
    assert get_approved_narrative_by_job_id("job-qa-hardening") is None
    assert "follow a meal plan" not in str(job.to_dict()).lower()


def test_persistence_failure_after_validation_returns_sanitized_result(
    tmp_path,
    monkeypatch,
):
    _initialize_temp_database(tmp_path, monkeypatch)
    _create_provider_job()
    _patch_context(monkeypatch)
    monkeypatch.setattr(
        "services.daily_coach_async_provider_runtime_service.validate_daily_coach_narrative_candidate",
        lambda candidate, context: DailyCoachNarrativeValidationResult(
            validation_status="approved",
            validation_errors=[],
            forbidden_claims_found=[],
        ),
    )
    monkeypatch.setattr(
        "services.daily_coach_async_provider_runtime_service.create_approved_narrative",
        lambda **kwargs: (_ for _ in ()).throw(sqlite3.OperationalError("boom raw db")),
    )

    result = run_daily_coach_async_provider_runtime_prototype(
        "job-qa-hardening",
        environ=_enabled_env(),
        generate=lambda *args: _valid_provider_output(),
    )

    assert result.provider_attempted is True
    assert result.approved_narrative_persisted is False
    assert result.fallback_reason == FALLBACK_REASON_PERSISTENCE_FAILURE
    assert result.sanitized_error_category == FALLBACK_REASON_PERSISTENCE_FAILURE
    assert "boom" not in str(result.to_dict()).lower()
    assert get_approved_narrative_by_job_id("job-qa-hardening") is None
