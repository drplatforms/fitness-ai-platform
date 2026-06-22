from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from database import get_connection
from models.async_daily_coach_narrative_models import (
    DAILY_COACH_APPROVED_NARRATIVE_TABLE,
    DAILY_COACH_ASYNC_JOB_TABLE,
    DAILY_COACH_ASYNC_PERSISTENCE_FORBIDDEN_COLUMNS,
    DAILY_COACH_NARRATIVE_JOB_STATUSES,
    DailyCoachNarrativeJobStatus,
)

_ALLOWED_FAILURE_METADATA_FIELDS = {
    "fallback_reason",
    "fallback_used",
    "provider_attempted",
    "provider_name",
    "provider_model",
    "parse_status",
    "validation_status",
    "final_narrative_source",
    "sanitized_error_category",
    "raw_output_length",
    "raw_output_preview_truncated",
    "markdown_wrapper_detected",
}

_ALLOWED_BOOLEAN_FIELDS = {
    "stale",
    "expired",
    "displayable",
    "public_safe",
    "fallback_used",
    "provider_attempted",
    "raw_output_preview_truncated",
    "markdown_wrapper_detected",
}


class DailyCoachAsyncPersistenceError(Exception):
    """Base error for Daily Coach async persistence service failures."""


class DailyCoachAsyncJobNotFoundError(DailyCoachAsyncPersistenceError):
    """Raised when a Daily Coach async job cannot be found."""


class DailyCoachAsyncPersistenceValidationError(
    DailyCoachAsyncPersistenceError, ValueError
):
    """Raised when persistence input violates the approved safety contract."""


@dataclass(frozen=True)
class PersistedDailyCoachAsyncJob:
    id: int
    job_id: str
    user_id: int
    target_date: str
    workflow_target: str
    next_action_id: str
    context_hash: str
    context_version: str
    prompt_contract_version: str
    validator_version: str
    status: str
    created_at: str | None
    updated_at: str | None
    started_at: str | None
    completed_at: str | None
    expires_at: str | None
    stale_after: str | None
    stale: bool
    expired: bool
    displayable: bool
    public_safe: bool
    fallback_used: bool
    fallback_reason: str | None
    provider_attempted: bool
    provider_name: str | None
    provider_model: str | None
    parse_status: str | None
    validation_status: str | None
    final_narrative_source: str | None
    sanitized_error_category: str | None
    raw_output_length: int | None
    raw_output_preview_truncated: bool
    markdown_wrapper_detected: bool

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class PersistedDailyCoachApprovedNarrative:
    id: int
    narrative_id: str
    job_id: str
    user_id: int
    target_date: str
    context_hash: str
    context_version: str
    approved_narrative_json: str
    approved_text: str
    reason_codes_json: str | None
    action_refs_json: str | None
    validator_version: str
    prompt_contract_version: str
    created_at: str | None
    expires_at: str | None
    stale: bool
    expired: bool
    displayable: bool
    public_safe: bool
    final_narrative_source: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @property
    def approved_narrative_payload(self) -> Any:
        return _decode_json(self.approved_narrative_json, default={})

    @property
    def reason_codes(self) -> Any:
        return _decode_json(self.reason_codes_json, default=[])

    @property
    def action_refs(self) -> Any:
        return _decode_json(self.action_refs_json, default=[])


def _new_public_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _bool_to_int(value: bool) -> int:
    return 1 if bool(value) else 0


def _row_bool(row: Any, key: str) -> bool:
    return bool(row[key])


def _validate_status(status: DailyCoachNarrativeJobStatus | str) -> str:
    value = (
        status.value
        if isinstance(status, DailyCoachNarrativeJobStatus)
        else str(status)
    )
    if value not in DAILY_COACH_NARRATIVE_JOB_STATUSES:
        raise DailyCoachAsyncPersistenceValidationError(
            f"Unsupported Daily Coach async job status: {value}"
        )
    return value


def _forbidden_key_matches(key: str) -> bool:
    return key.strip().lower() in DAILY_COACH_ASYNC_PERSISTENCE_FORBIDDEN_COLUMNS


def _reject_forbidden_field_names(field_names: set[str]) -> None:
    forbidden = sorted(name for name in field_names if _forbidden_key_matches(name))
    if forbidden:
        raise DailyCoachAsyncPersistenceValidationError(
            "Forbidden Daily Coach async persistence field(s): " + ", ".join(forbidden)
        )


def _reject_unexpected_fields(extra_fields: dict[str, Any]) -> None:
    if not extra_fields:
        return
    _reject_forbidden_field_names(set(extra_fields))
    raise DailyCoachAsyncPersistenceValidationError(
        "Unexpected Daily Coach async persistence field(s): "
        + ", ".join(sorted(extra_fields))
    )


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, nested_value in value.items():
            keys.add(str(key))
            keys.update(_walk_keys(nested_value))
    elif isinstance(value, list | tuple):
        for item in value:
            keys.update(_walk_keys(item))
    return keys


def _reject_forbidden_payload_keys(value: Any) -> None:
    _reject_forbidden_field_names(_walk_keys(value))


def _encode_json(value: Any, *, default: Any) -> str:
    if value is None:
        value = default
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise DailyCoachAsyncPersistenceValidationError(
                "Approved narrative JSON fields must contain valid JSON."
            ) from exc
        _reject_forbidden_payload_keys(parsed)
        return json.dumps(parsed, sort_keys=True)
    _reject_forbidden_payload_keys(value)
    return json.dumps(value, sort_keys=True)


def _decode_json(raw_value: str | None, *, default: Any) -> Any:
    if raw_value is None:
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def _job_from_row(row: Any) -> PersistedDailyCoachAsyncJob:
    return PersistedDailyCoachAsyncJob(
        id=int(row["id"]),
        job_id=row["job_id"],
        user_id=int(row["user_id"]),
        target_date=row["target_date"],
        workflow_target=row["workflow_target"],
        next_action_id=row["next_action_id"],
        context_hash=row["context_hash"],
        context_version=row["context_version"],
        prompt_contract_version=row["prompt_contract_version"],
        validator_version=row["validator_version"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        expires_at=row["expires_at"],
        stale_after=row["stale_after"],
        stale=_row_bool(row, "stale"),
        expired=_row_bool(row, "expired"),
        displayable=_row_bool(row, "displayable"),
        public_safe=_row_bool(row, "public_safe"),
        fallback_used=_row_bool(row, "fallback_used"),
        fallback_reason=row["fallback_reason"],
        provider_attempted=_row_bool(row, "provider_attempted"),
        provider_name=row["provider_name"],
        provider_model=row["provider_model"],
        parse_status=row["parse_status"],
        validation_status=row["validation_status"],
        final_narrative_source=row["final_narrative_source"],
        sanitized_error_category=row["sanitized_error_category"],
        raw_output_length=row["raw_output_length"],
        raw_output_preview_truncated=_row_bool(row, "raw_output_preview_truncated"),
        markdown_wrapper_detected=_row_bool(row, "markdown_wrapper_detected"),
    )


def _narrative_from_row(row: Any) -> PersistedDailyCoachApprovedNarrative:
    return PersistedDailyCoachApprovedNarrative(
        id=int(row["id"]),
        narrative_id=row["narrative_id"],
        job_id=row["job_id"],
        user_id=int(row["user_id"]),
        target_date=row["target_date"],
        context_hash=row["context_hash"],
        context_version=row["context_version"],
        approved_narrative_json=row["approved_narrative_json"],
        approved_text=row["approved_text"],
        reason_codes_json=row["reason_codes_json"],
        action_refs_json=row["action_refs_json"],
        validator_version=row["validator_version"],
        prompt_contract_version=row["prompt_contract_version"],
        created_at=row["created_at"],
        expires_at=row["expires_at"],
        stale=_row_bool(row, "stale"),
        expired=_row_bool(row, "expired"),
        displayable=_row_bool(row, "displayable"),
        public_safe=_row_bool(row, "public_safe"),
        final_narrative_source=row["final_narrative_source"],
    )


def _require_job(job_id: str) -> PersistedDailyCoachAsyncJob:
    job = get_async_job(job_id)
    if job is None:
        raise DailyCoachAsyncJobNotFoundError(
            f"Daily Coach async job not found: {job_id}"
        )
    return job


def create_async_job(
    *,
    user_id: int,
    target_date: str,
    workflow_target: str,
    next_action_id: str,
    context_hash: str,
    context_version: str,
    prompt_contract_version: str,
    validator_version: str,
    status: DailyCoachNarrativeJobStatus | str = DailyCoachNarrativeJobStatus.QUEUED,
    job_id: str | None = None,
    stale_after: str | None = None,
    expires_at: str | None = None,
    **extra_fields: Any,
) -> PersistedDailyCoachAsyncJob:
    """Create a durable Daily Coach async job shell."""

    _reject_unexpected_fields(extra_fields)
    resolved_job_id = job_id or _new_public_id("daily-coach-async-job")
    status_value = _validate_status(status)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        INSERT INTO {DAILY_COACH_ASYNC_JOB_TABLE} (
            job_id, user_id, target_date, workflow_target, next_action_id,
            context_hash, context_version, prompt_contract_version,
            validator_version, status, stale_after, expires_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resolved_job_id,
            user_id,
            target_date,
            workflow_target,
            next_action_id,
            context_hash,
            context_version,
            prompt_contract_version,
            validator_version,
            status_value,
            stale_after,
            expires_at,
        ),
    )
    conn.commit()
    conn.close()
    return _require_job(resolved_job_id)


def get_async_job(job_id: str) -> PersistedDailyCoachAsyncJob | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM {DAILY_COACH_ASYNC_JOB_TABLE} WHERE job_id = ?",
        (job_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _job_from_row(row) if row is not None else None


def update_async_job_status(
    job_id: str,
    status: DailyCoachNarrativeJobStatus | str,
    *,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> PersistedDailyCoachAsyncJob:
    _require_job(job_id)
    assignments = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
    values: list[Any] = [_validate_status(status)]
    if started_at is not None:
        assignments.append("started_at = ?")
        values.append(started_at)
    if completed_at is not None:
        assignments.append("completed_at = ?")
        values.append(completed_at)
    values.append(job_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE {DAILY_COACH_ASYNC_JOB_TABLE} SET {', '.join(assignments)} WHERE job_id = ?",
        tuple(values),
    )
    conn.commit()
    conn.close()
    return _require_job(job_id)


def _update_async_job_flags(
    job_id: str,
    *,
    stale: bool | None = None,
    expired: bool | None = None,
    displayable: bool | None = None,
    public_safe: bool | None = None,
    status: DailyCoachNarrativeJobStatus | str | None = None,
) -> PersistedDailyCoachAsyncJob:
    _require_job(job_id)
    assignments = ["updated_at = CURRENT_TIMESTAMP"]
    values: list[Any] = []
    for name, value in (
        ("stale", stale),
        ("expired", expired),
        ("displayable", displayable),
        ("public_safe", public_safe),
    ):
        if value is not None:
            assignments.append(f"{name} = ?")
            values.append(_bool_to_int(value))
    if status is not None:
        assignments.append("status = ?")
        values.append(_validate_status(status))
    values.append(job_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE {DAILY_COACH_ASYNC_JOB_TABLE} SET {', '.join(assignments)} WHERE job_id = ?",
        tuple(values),
    )
    conn.commit()
    conn.close()
    return _require_job(job_id)


def mark_async_job_stale(job_id: str) -> PersistedDailyCoachAsyncJob:
    return _update_async_job_flags(
        job_id,
        stale=True,
        displayable=False,
        status=DailyCoachNarrativeJobStatus.STALE,
    )


def mark_async_job_expired(job_id: str) -> PersistedDailyCoachAsyncJob:
    return _update_async_job_flags(
        job_id,
        expired=True,
        displayable=False,
        status=DailyCoachNarrativeJobStatus.EXPIRED,
    )


def mark_async_job_displayable(
    job_id: str,
    *,
    public_safe: bool = True,
) -> PersistedDailyCoachAsyncJob:
    if not public_safe:
        raise DailyCoachAsyncPersistenceValidationError(
            "Displayable Daily Coach async jobs must be public_safe."
        )
    return _update_async_job_flags(
        job_id,
        displayable=True,
        public_safe=True,
        status=DailyCoachNarrativeJobStatus.APPROVED,
    )


def record_async_job_failure_metadata(
    job_id: str,
    **metadata: Any,
) -> PersistedDailyCoachAsyncJob:
    """Record allowlisted sanitized metadata only."""

    _require_job(job_id)
    _reject_forbidden_field_names(set(metadata))
    unexpected = sorted(set(metadata) - _ALLOWED_FAILURE_METADATA_FIELDS)
    if unexpected:
        raise DailyCoachAsyncPersistenceValidationError(
            "Unexpected Daily Coach async failure metadata field(s): "
            + ", ".join(unexpected)
        )
    assignments = ["updated_at = CURRENT_TIMESTAMP"]
    values: list[Any] = []
    for field_name in sorted(metadata):
        assignments.append(f"{field_name} = ?")
        value = metadata[field_name]
        values.append(
            _bool_to_int(value) if field_name in _ALLOWED_BOOLEAN_FIELDS else value
        )
    values.append(job_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE {DAILY_COACH_ASYNC_JOB_TABLE} SET {', '.join(assignments)} WHERE job_id = ?",
        tuple(values),
    )
    conn.commit()
    conn.close()
    return _require_job(job_id)


def record_async_job_fallback(
    job_id: str,
    *,
    fallback_reason: str,
    final_narrative_source: str = "deterministic_fallback",
) -> PersistedDailyCoachAsyncJob:
    return record_async_job_failure_metadata(
        job_id,
        fallback_reason=fallback_reason,
        fallback_used=True,
        final_narrative_source=final_narrative_source,
    )


def create_approved_narrative(
    *,
    job_id: str,
    user_id: int,
    target_date: str,
    context_hash: str,
    context_version: str,
    approved_narrative_json: Any,
    approved_text: str,
    validator_version: str,
    prompt_contract_version: str,
    final_narrative_source: str,
    narrative_id: str | None = None,
    reason_codes_json: Any | None = None,
    action_refs_json: Any | None = None,
    expires_at: str | None = None,
    stale: bool = False,
    expired: bool = False,
    displayable: bool = True,
    public_safe: bool = True,
    **extra_fields: Any,
) -> PersistedDailyCoachApprovedNarrative:
    """Persist an approved, public-safe narrative payload only."""

    _reject_unexpected_fields(extra_fields)
    _require_job(job_id)
    if not public_safe:
        raise DailyCoachAsyncPersistenceValidationError(
            "Approved Daily Coach narratives must be public_safe."
        )
    if not approved_text.strip():
        raise DailyCoachAsyncPersistenceValidationError(
            "Approved Daily Coach narratives require approved_text."
        )
    if not final_narrative_source.strip():
        raise DailyCoachAsyncPersistenceValidationError(
            "Approved Daily Coach narratives require final_narrative_source."
        )
    resolved_narrative_id = narrative_id or _new_public_id(
        "daily-coach-approved-narrative"
    )
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        INSERT INTO {DAILY_COACH_APPROVED_NARRATIVE_TABLE} (
            narrative_id, job_id, user_id, target_date, context_hash, context_version,
            approved_narrative_json, approved_text, reason_codes_json,
            action_refs_json, validator_version, prompt_contract_version, expires_at,
            stale, expired, displayable, public_safe, final_narrative_source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resolved_narrative_id,
            job_id,
            user_id,
            target_date,
            context_hash,
            context_version,
            _encode_json(approved_narrative_json, default={}),
            approved_text,
            _encode_json(reason_codes_json, default=[]),
            _encode_json(action_refs_json, default=[]),
            validator_version,
            prompt_contract_version,
            expires_at,
            _bool_to_int(stale),
            _bool_to_int(expired),
            _bool_to_int(displayable),
            _bool_to_int(public_safe),
            final_narrative_source,
        ),
    )
    conn.commit()
    conn.close()
    narrative = get_approved_narrative_by_job_id(job_id)
    if narrative is None:
        raise DailyCoachAsyncPersistenceError(
            "Approved Daily Coach narrative was not persisted."
        )
    return narrative


def get_approved_narrative_by_job_id(
    job_id: str,
) -> PersistedDailyCoachApprovedNarrative | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT *
        FROM {DAILY_COACH_APPROVED_NARRATIVE_TABLE}
        WHERE job_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (job_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _narrative_from_row(row) if row is not None else None


def get_latest_displayable_approved_narrative(
    *,
    user_id: int,
    target_date: str | None = None,
) -> PersistedDailyCoachApprovedNarrative | None:
    values: list[Any] = [user_id]
    where = [
        "user_id = ?",
        "displayable = 1",
        "public_safe = 1",
        "stale = 0",
        "expired = 0",
    ]
    if target_date is not None:
        where.append("target_date = ?")
        values.append(target_date)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT *
        FROM {DAILY_COACH_APPROVED_NARRATIVE_TABLE}
        WHERE {" AND ".join(where)}
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        tuple(values),
    )
    row = cursor.fetchone()
    conn.close()
    return _narrative_from_row(row) if row is not None else None
