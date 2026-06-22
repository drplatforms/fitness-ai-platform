from __future__ import annotations

import os
import sqlite3
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from database import initialize_database
from models.async_daily_coach_narrative_models import (
    DailyCoachNarrativeJobStatus,
    is_daily_coach_narrative_bridge_approved_model,
)
from models.daily_coach_narrative_models import (
    DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
    DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS,
    DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED,
    DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED,
)
from services.async_daily_coach_context_identity import (
    build_daily_coach_narrative_context_identity,
)
from services.daily_coach_async_persistence_service import (
    DailyCoachAsyncJobNotFoundError,
    DailyCoachAsyncPersistenceError,
    PersistedDailyCoachAsyncJob,
    create_approved_narrative,
    create_async_job,
    get_async_job,
    mark_async_job_displayable,
    record_async_job_failure_metadata,
    update_async_job_status,
)
from services.daily_coach_narrative_context_service import (
    build_daily_coach_narrative_context,
)
from services.daily_coach_narrative_provider_service import (
    build_daily_coach_narrative_prompt,
    call_ollama_generate,
)
from services.daily_coach_narrative_validation_service import (
    parse_daily_coach_narrative_candidate,
    validate_daily_coach_narrative_candidate,
)
from services.daily_next_action_service import build_daily_next_action

DAILY_COACH_ASYNC_PROVIDER_RUNTIME_ENABLED_ENV = (
    "DAILY_COACH_ASYNC_PROVIDER_RUNTIME_ENABLED"
)
DAILY_COACH_ASYNC_PROVIDER_ENV = "DAILY_COACH_ASYNC_PROVIDER"
DAILY_COACH_ASYNC_PROVIDER_MODEL_ENV = "DAILY_COACH_ASYNC_PROVIDER_MODEL"
DAILY_COACH_ASYNC_PROVIDER_TIMEOUT_ENV = "DAILY_COACH_ASYNC_PROVIDER_TIMEOUT_SECONDS"
OLLAMA_BASE_URL_ENV = "OLLAMA_BASE_URL"

DAILY_COACH_ASYNC_PROVIDER_DIRECT_OLLAMA = "direct_ollama"
DAILY_COACH_ASYNC_PROVIDER_DEFAULT_MODEL = "qwen2.5:3b"
DAILY_COACH_ASYNC_PROVIDER_DEFAULT_TIMEOUT_SECONDS = 60.0
DAILY_COACH_ASYNC_PROMPT_CONTRACT_VERSION = "daily_coach_async_provider_runtime_v1"
DAILY_COACH_ASYNC_VALIDATOR_VERSION = "daily_coach_async_provider_validator_v1"
DAILY_COACH_ASYNC_CONTEXT_VERSION = "daily_coach_async_context_v1"

PARSE_STATUS_NOT_ATTEMPTED = "not_attempted"
VALIDATION_STATUS_NOT_ATTEMPTED = "not_attempted"
FINAL_SOURCE_PROVIDER_APPROVED = "provider_approved"
FINAL_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"

FALLBACK_REASON_RUNTIME_DISABLED = "provider_runtime_disabled"
FALLBACK_REASON_PROVIDER_CONFIG_MISSING = "provider_config_missing"
FALLBACK_REASON_MODEL_CONFIG_MISSING = "model_config_missing"
FALLBACK_REASON_INVALID_PROVIDER = "invalid_provider_config"
FALLBACK_REASON_UNAPPROVED_MODEL = "unapproved_model"
FALLBACK_REASON_MISSING_JOB = "missing_job"
FALLBACK_REASON_STALE_JOB = "stale_job"
FALLBACK_REASON_EXPIRED_JOB = "expired_job"
FALLBACK_REASON_PROVIDER_TIMEOUT = "provider_timeout"
FALLBACK_REASON_PROVIDER_UNAVAILABLE = "provider_unavailable"
FALLBACK_REASON_PROVIDER_EXCEPTION = "provider_exception"
FALLBACK_REASON_PARSE_FAILURE = "candidate_parse_failure"
FALLBACK_REASON_VALIDATION_FAILURE = "candidate_validation_failure"
FALLBACK_REASON_PERSISTENCE_FAILURE = "persistence_failure"

DailyCoachAsyncProviderGenerateCallable = Callable[[str, str, float, str], str]


@dataclass(frozen=True)
class DailyCoachAsyncProviderRuntimeConfig:
    enabled: bool
    configured_provider: str
    selected_provider: str
    configured_model: str
    selected_model: str
    timeout_seconds: float
    ollama_base_url: str
    provider_configured: bool
    model_configured: bool

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["developer_mode_required"] = True
        payload["manual_trigger_required"] = True
        payload["normal_today_behavior_changed"] = False
        return payload


@dataclass(frozen=True)
class DailyCoachAsyncProviderRuntimeResult:
    success: bool
    developer_only: bool
    manual_trigger_only: bool
    job_id: str | None
    user_id: int | None
    target_date: str | None
    configured_provider: str
    selected_provider: str
    configured_model: str
    selected_model: str
    provider_runtime_enabled: bool
    provider_attempted: bool
    fallback_used: bool
    fallback_reason: str | None
    parse_status: str
    validation_status: str
    final_narrative_source: str
    approved_narrative_persisted: bool
    raw_output_length: int | None = None
    raw_output_preview_truncated: bool = False
    markdown_wrapper_detected: bool = False
    sanitized_error_category: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_daily_coach_async_provider_runtime_config(
    environ=None,
) -> DailyCoachAsyncProviderRuntimeConfig:
    """Resolve Developer Mode provider runtime config.

    Important test/runtime contract:
    - environ=None reads the real process environment.
    - environ={} is an explicitly empty isolated environment.
    - provider runtime is disabled by default.
    """
    env = os.environ if environ is None else environ

    def _get_env(name: str, default: str) -> str:
        value = env.get(name)
        if value is None or value == "":
            return default
        return str(value)

    def _get_bool(name: str, default: bool = False) -> bool:
        value = env.get(name)
        if value is None or value == "":
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}

    def _get_float(name: str, default: float) -> float:
        value = env.get(name)
        if value is None or value == "":
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    raw_provider = env.get(DAILY_COACH_ASYNC_PROVIDER_ENV)
    raw_model = env.get(DAILY_COACH_ASYNC_PROVIDER_MODEL_ENV)
    provider_configured = raw_provider is not None and str(raw_provider).strip() != ""
    model_configured = raw_model is not None and str(raw_model).strip() != ""
    configured_provider = _get_env(
        DAILY_COACH_ASYNC_PROVIDER_ENV,
        DAILY_COACH_ASYNC_PROVIDER_DIRECT_OLLAMA,
    )
    configured_model = _get_env(
        DAILY_COACH_ASYNC_PROVIDER_MODEL_ENV,
        DAILY_COACH_ASYNC_PROVIDER_DEFAULT_MODEL,
    )

    ollama_base_url = (
        env.get("DAILY_COACH_ASYNC_PROVIDER_OLLAMA_BASE_URL")
        or env.get("DAILY_COACH_ASYNC_OLLAMA_BASE_URL")
        or env.get("OLLAMA_BASE_URL")
        or "http://localhost:11434"
    )

    return DailyCoachAsyncProviderRuntimeConfig(
        enabled=_get_bool(DAILY_COACH_ASYNC_PROVIDER_RUNTIME_ENABLED_ENV, False),
        configured_provider=configured_provider,
        selected_provider=configured_provider,
        configured_model=configured_model,
        selected_model=configured_model,
        timeout_seconds=_get_float(DAILY_COACH_ASYNC_PROVIDER_TIMEOUT_ENV, 60.0),
        ollama_base_url=str(ollama_base_url),
        provider_configured=provider_configured,
        model_configured=model_configured,
    )


def create_developer_mode_provider_runtime_job(
    *,
    user_id: int,
    target_date: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> PersistedDailyCoachAsyncJob:
    """Create a persisted job for manual Developer Mode provider QA only."""

    resolved_date = target_date or datetime.now(UTC).date().isoformat()
    config = resolve_daily_coach_async_provider_runtime_config(environ)
    action = build_daily_next_action(user_id, target_date=resolved_date)
    identity = build_daily_coach_narrative_context_identity(
        user_id=user_id,
        target_date=resolved_date,
        next_action_id=action.action_id,
        workflow_target=action.workflow_target,
        provider=config.selected_provider,
        model=config.selected_model,
        prompt_contract_version=DAILY_COACH_ASYNC_PROMPT_CONTRACT_VERSION,
        validator_version=DAILY_COACH_ASYNC_VALIDATOR_VERSION,
        approved_context_inputs={
            "daily_next_action": action.to_dict(),
            "developer_provider_runtime_prototype": {
                "developer_only": True,
                "manual_trigger_only": True,
                "normal_today_behavior": "unchanged",
                "public_async_narrative_display": "not_added",
            },
        },
    )

    # Developer Mode manual job creation should work against older local
    # SQLite app databases that predate the async persistence tables.
    # initialize_database() uses CREATE TABLE IF NOT EXISTS and does not
    # create provider/runtime behavior.
    initialize_database()
    return create_async_job(
        user_id=user_id,
        target_date=resolved_date,
        workflow_target=action.workflow_target,
        next_action_id=action.action_id,
        context_hash=identity.context_hash,
        context_version=DAILY_COACH_ASYNC_CONTEXT_VERSION,
        prompt_contract_version=DAILY_COACH_ASYNC_PROMPT_CONTRACT_VERSION,
        validator_version=DAILY_COACH_ASYNC_VALIDATOR_VERSION,
        status=DailyCoachNarrativeJobStatus.QUEUED,
        expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )


def run_daily_coach_async_provider_runtime_prototype(
    job_id: str,
    *,
    environ: Mapping[str, str] | None = None,
    generate: DailyCoachAsyncProviderGenerateCallable | None = None,
) -> DailyCoachAsyncProviderRuntimeResult:
    """Run one manual Developer Mode provider attempt for a persisted async job.

    The function never returns raw provider output and persists only approved public-safe
    narrative content or sanitized fallback/failure metadata.
    """

    config = resolve_daily_coach_async_provider_runtime_config(environ)
    try:
        job = get_async_job(job_id)
    except (DailyCoachAsyncPersistenceError, sqlite3.Error):
        return _result(
            config,
            job=None,
            fallback_reason=FALLBACK_REASON_PERSISTENCE_FAILURE,
            sanitized_error_category=FALLBACK_REASON_PERSISTENCE_FAILURE,
            message="Persistence lookup failed safely.",
        )
    if job is None:
        return _result(
            config,
            job=None,
            fallback_reason=FALLBACK_REASON_MISSING_JOB,
            message="No persisted Daily Coach async job found for that job_id.",
        )

    if not config.enabled:
        return _result(
            config,
            job=job,
            fallback_reason=FALLBACK_REASON_RUNTIME_DISABLED,
            message="Provider runtime is disabled by configuration.",
        )
    if not config.provider_configured:
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_PROVIDER_CONFIG_MISSING,
            status=DailyCoachNarrativeJobStatus.PROVIDER_ERROR,
            provider_attempted=False,
            parse_status=PARSE_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            fallback_reason=FALLBACK_REASON_PROVIDER_CONFIG_MISSING,
            message="Provider runtime is enabled but provider config is missing.",
        )
    if not config.model_configured:
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_MODEL_CONFIG_MISSING,
            status=DailyCoachNarrativeJobStatus.PROVIDER_ERROR,
            provider_attempted=False,
            parse_status=PARSE_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            fallback_reason=FALLBACK_REASON_MODEL_CONFIG_MISSING,
            message="Provider runtime is enabled but model config is missing.",
        )
    if config.selected_provider != DAILY_COACH_ASYNC_PROVIDER_DIRECT_OLLAMA:
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_INVALID_PROVIDER,
            status=DailyCoachNarrativeJobStatus.PROVIDER_ERROR,
            provider_attempted=False,
            parse_status=PARSE_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            fallback_reason=FALLBACK_REASON_INVALID_PROVIDER,
            message="Configured provider is not approved for this prototype.",
        )
    if not is_daily_coach_narrative_bridge_approved_model(config.selected_model):
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_UNAPPROVED_MODEL,
            status=DailyCoachNarrativeJobStatus.PROVIDER_ERROR,
            provider_attempted=False,
            parse_status=PARSE_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            fallback_reason=FALLBACK_REASON_UNAPPROVED_MODEL,
            message="Configured model is not approved for this prototype.",
        )
    if job.stale:
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_STALE_JOB,
            status=DailyCoachNarrativeJobStatus.STALE,
            provider_attempted=False,
            parse_status=PARSE_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            fallback_reason=FALLBACK_REASON_STALE_JOB,
            message="Persisted job is stale.",
        )
    if job.expired:
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_EXPIRED_JOB,
            status=DailyCoachNarrativeJobStatus.EXPIRED,
            provider_attempted=False,
            parse_status=PARSE_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            fallback_reason=FALLBACK_REASON_EXPIRED_JOB,
            message="Persisted job is expired.",
        )

    update_async_job_status(
        job.job_id,
        DailyCoachNarrativeJobStatus.GENERATING,
        started_at=datetime.now(UTC).isoformat(),
    )
    try:
        context = build_daily_coach_narrative_context(
            job.user_id,
            target_date=job.target_date,
        )
        prompt = build_daily_coach_narrative_prompt(context)
    except Exception:
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            status=DailyCoachNarrativeJobStatus.PROVIDER_ERROR,
            provider_attempted=False,
            parse_status=PARSE_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            sanitized_error_category=FALLBACK_REASON_PROVIDER_EXCEPTION,
            message="Provider input construction failed safely.",
        )
    selected_generate = generate or call_ollama_generate
    raw_output: str | None = None
    started = time.perf_counter()
    try:
        raw_output = selected_generate(
            config.selected_model,
            prompt,
            config.timeout_seconds,
            config.ollama_base_url,
        )
    except TimeoutError:
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_PROVIDER_TIMEOUT,
            status=DailyCoachNarrativeJobStatus.PROVIDER_TIMEOUT,
            provider_attempted=True,
            parse_status=PARSE_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            fallback_reason=FALLBACK_REASON_PROVIDER_TIMEOUT,
            provider_attempted=True,
            sanitized_error_category=FALLBACK_REASON_PROVIDER_TIMEOUT,
            message="Provider timed out safely.",
        )
    except (ConnectionError, OSError):
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_PROVIDER_UNAVAILABLE,
            status=DailyCoachNarrativeJobStatus.PROVIDER_ERROR,
            provider_attempted=True,
            parse_status=PARSE_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            fallback_reason=FALLBACK_REASON_PROVIDER_UNAVAILABLE,
            provider_attempted=True,
            sanitized_error_category=FALLBACK_REASON_PROVIDER_UNAVAILABLE,
            message="Provider was unavailable and failed safely.",
        )
    except Exception:
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            status=DailyCoachNarrativeJobStatus.PROVIDER_ERROR,
            provider_attempted=True,
            parse_status=PARSE_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            provider_attempted=True,
            sanitized_error_category=FALLBACK_REASON_PROVIDER_EXCEPTION,
            message="Provider failed safely.",
        )

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    raw_output_length = len(raw_output)
    markdown_wrapper_detected = _markdown_wrapper_detected(raw_output)
    raw_output_preview_truncated = raw_output_length > 500
    parse_result = parse_daily_coach_narrative_candidate(raw_output)
    if not parse_result.success or parse_result.candidate is None:
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_PARSE_FAILURE,
            status=DailyCoachNarrativeJobStatus.REJECTED_PARSE,
            provider_attempted=True,
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
            raw_output_length=raw_output_length,
            raw_output_preview_truncated=raw_output_preview_truncated,
            markdown_wrapper_detected=markdown_wrapper_detected,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            provider_attempted=True,
            fallback_reason=FALLBACK_REASON_PARSE_FAILURE,
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
            raw_output_length=raw_output_length,
            raw_output_preview_truncated=raw_output_preview_truncated,
            markdown_wrapper_detected=markdown_wrapper_detected,
            sanitized_error_category=FALLBACK_REASON_PARSE_FAILURE,
            message="Provider output failed strict JSON parsing.",
        )

    update_async_job_status(
        job.job_id,
        DailyCoachNarrativeJobStatus.PROVIDER_SUCCEEDED_PENDING_VALIDATION,
    )
    validation_result = validate_daily_coach_narrative_candidate(
        parse_result.candidate,
        context=context,
    )
    if not validation_result.approved:
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_VALIDATION_FAILURE,
            status=DailyCoachNarrativeJobStatus.REJECTED_VALIDATION,
            provider_attempted=True,
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS,
            validation_status=DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED,
            raw_output_length=raw_output_length,
            raw_output_preview_truncated=raw_output_preview_truncated,
            markdown_wrapper_detected=markdown_wrapper_detected,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            provider_attempted=True,
            fallback_reason=FALLBACK_REASON_VALIDATION_FAILURE,
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS,
            validation_status=DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED,
            raw_output_length=raw_output_length,
            raw_output_preview_truncated=raw_output_preview_truncated,
            markdown_wrapper_detected=markdown_wrapper_detected,
            sanitized_error_category=FALLBACK_REASON_VALIDATION_FAILURE,
            message="Provider output failed safety validation.",
        )

    candidate = parse_result.candidate
    approved_payload = candidate.to_dict()
    try:
        create_approved_narrative(
            job_id=job.job_id,
            user_id=job.user_id,
            target_date=job.target_date,
            context_hash=job.context_hash,
            context_version=job.context_version,
            approved_narrative_json=approved_payload,
            approved_text=candidate.coach_note,
            reason_codes_json=[
                "daily_coach_async_provider_approved",
                *candidate.used_approved_facts[:2],
            ],
            action_refs_json=[
                {
                    "next_action_id": job.next_action_id,
                    "workflow_target": job.workflow_target,
                }
            ],
            validator_version=job.validator_version,
            prompt_contract_version=job.prompt_contract_version,
            final_narrative_source=FINAL_SOURCE_PROVIDER_APPROVED,
            displayable=True,
            public_safe=True,
        )
        update_async_job_status(
            job.job_id,
            DailyCoachNarrativeJobStatus.APPROVED,
            completed_at=datetime.now(UTC).isoformat(),
        )
        mark_async_job_displayable(job.job_id)
        record_async_job_failure_metadata(
            job.job_id,
            provider_attempted=True,
            provider_name=config.selected_provider,
            provider_model=config.selected_model,
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS,
            validation_status=DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED,
            final_narrative_source=FINAL_SOURCE_PROVIDER_APPROVED,
            raw_output_length=raw_output_length,
            raw_output_preview_truncated=raw_output_preview_truncated,
            markdown_wrapper_detected=markdown_wrapper_detected,
        )
    except (DailyCoachAsyncPersistenceError, sqlite3.Error):
        _record_sanitized_failure(
            job.job_id,
            config=config,
            fallback_reason=FALLBACK_REASON_PERSISTENCE_FAILURE,
            status=DailyCoachNarrativeJobStatus.PROVIDER_ERROR,
            provider_attempted=True,
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS,
            validation_status=DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED,
            raw_output_length=raw_output_length,
            raw_output_preview_truncated=raw_output_preview_truncated,
            markdown_wrapper_detected=markdown_wrapper_detected,
        )
        return _result(
            config,
            job=get_async_job(job.job_id) or job,
            provider_attempted=True,
            fallback_reason=FALLBACK_REASON_PERSISTENCE_FAILURE,
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS,
            validation_status=DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED,
            raw_output_length=raw_output_length,
            raw_output_preview_truncated=raw_output_preview_truncated,
            markdown_wrapper_detected=markdown_wrapper_detected,
            sanitized_error_category=FALLBACK_REASON_PERSISTENCE_FAILURE,
            message="Approved provider output could not be persisted safely.",
        )
    return _result(
        config,
        job=get_async_job(job.job_id),
        provider_attempted=True,
        fallback_used=False,
        fallback_reason=None,
        parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS,
        validation_status=DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED,
        final_narrative_source=FINAL_SOURCE_PROVIDER_APPROVED,
        approved_narrative_persisted=True,
        raw_output_length=raw_output_length,
        raw_output_preview_truncated=raw_output_preview_truncated,
        markdown_wrapper_detected=markdown_wrapper_detected,
        message=f"Provider output approved and persisted in {elapsed_ms} ms.",
    )


def _record_sanitized_failure(
    job_id: str,
    *,
    config: DailyCoachAsyncProviderRuntimeConfig,
    fallback_reason: str,
    status: DailyCoachNarrativeJobStatus,
    provider_attempted: bool,
    parse_status: str,
    validation_status: str,
    raw_output_length: int | None = None,
    raw_output_preview_truncated: bool = False,
    markdown_wrapper_detected: bool = False,
) -> None:
    try:
        update_async_job_status(
            job_id,
            status,
            completed_at=datetime.now(UTC).isoformat(),
        )
        record_async_job_failure_metadata(
            job_id,
            fallback_reason=fallback_reason,
            fallback_used=True,
            provider_attempted=provider_attempted,
            provider_name=config.selected_provider,
            provider_model=config.selected_model,
            parse_status=parse_status,
            validation_status=validation_status,
            final_narrative_source=FINAL_SOURCE_DETERMINISTIC_FALLBACK,
            sanitized_error_category=fallback_reason,
            raw_output_length=raw_output_length,
            raw_output_preview_truncated=raw_output_preview_truncated,
            markdown_wrapper_detected=markdown_wrapper_detected,
        )
    except (
        DailyCoachAsyncJobNotFoundError,
        DailyCoachAsyncPersistenceError,
        sqlite3.Error,
    ):
        return


def _result(
    config: DailyCoachAsyncProviderRuntimeConfig,
    *,
    job: PersistedDailyCoachAsyncJob | None,
    fallback_reason: str | None,
    provider_attempted: bool = False,
    fallback_used: bool = True,
    parse_status: str = PARSE_STATUS_NOT_ATTEMPTED,
    validation_status: str = VALIDATION_STATUS_NOT_ATTEMPTED,
    final_narrative_source: str = FINAL_SOURCE_DETERMINISTIC_FALLBACK,
    approved_narrative_persisted: bool = False,
    raw_output_length: int | None = None,
    raw_output_preview_truncated: bool = False,
    markdown_wrapper_detected: bool = False,
    sanitized_error_category: str | None = None,
    message: str | None = None,
) -> DailyCoachAsyncProviderRuntimeResult:
    return DailyCoachAsyncProviderRuntimeResult(
        success=fallback_reason is None or approved_narrative_persisted,
        developer_only=True,
        manual_trigger_only=True,
        job_id=job.job_id if job else None,
        user_id=job.user_id if job else None,
        target_date=job.target_date if job else None,
        configured_provider=config.configured_provider,
        selected_provider=config.selected_provider,
        configured_model=config.configured_model,
        selected_model=config.selected_model,
        provider_runtime_enabled=config.enabled,
        provider_attempted=provider_attempted,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        parse_status=parse_status,
        validation_status=validation_status,
        final_narrative_source=final_narrative_source,
        approved_narrative_persisted=approved_narrative_persisted,
        raw_output_length=raw_output_length,
        raw_output_preview_truncated=raw_output_preview_truncated,
        markdown_wrapper_detected=markdown_wrapper_detected,
        sanitized_error_category=sanitized_error_category or fallback_reason,
        message=message,
    )


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _safe_timeout_seconds(raw_value: str | None) -> float:
    if not raw_value:
        return DAILY_COACH_ASYNC_PROVIDER_DEFAULT_TIMEOUT_SECONDS
    try:
        parsed = float(raw_value)
    except ValueError:
        return DAILY_COACH_ASYNC_PROVIDER_DEFAULT_TIMEOUT_SECONDS
    return max(1.0, min(parsed, 180.0))


def _markdown_wrapper_detected(raw_output: str) -> bool:
    stripped = raw_output.strip().lower()
    return stripped.startswith("```") or "```json" in stripped or "```" in stripped
