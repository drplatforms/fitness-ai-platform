from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Protocol

from models.async_daily_coach_narrative_models import (
    ApprovedDailyCoachNarrativePayload,
    DailyCoachNarrativeContextIdentity,
    DailyCoachNarrativeJob,
    DailyCoachNarrativeJobStatus,
)

Clock = Callable[[], datetime]
IdFactory = Callable[[], str]

DISPLAYABLE_STATUS = DailyCoachNarrativeJobStatus.APPROVED.value
NON_DISPLAYABLE_STATUSES = frozenset(
    status.value
    for status in DailyCoachNarrativeJobStatus
    if status.value != DISPLAYABLE_STATUS
)

ALLOWED_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    DailyCoachNarrativeJobStatus.NOT_REQUESTED.value: frozenset(
        {DailyCoachNarrativeJobStatus.QUEUED.value}
    ),
    DailyCoachNarrativeJobStatus.QUEUED.value: frozenset(
        {DailyCoachNarrativeJobStatus.GENERATING.value}
    ),
    DailyCoachNarrativeJobStatus.GENERATING.value: frozenset(
        {
            DailyCoachNarrativeJobStatus.PROVIDER_SUCCEEDED_PENDING_VALIDATION.value,
            DailyCoachNarrativeJobStatus.REJECTED_PARSE.value,
            DailyCoachNarrativeJobStatus.PROVIDER_TIMEOUT.value,
            DailyCoachNarrativeJobStatus.PROVIDER_ERROR.value,
        }
    ),
    DailyCoachNarrativeJobStatus.PROVIDER_SUCCEEDED_PENDING_VALIDATION.value: frozenset(
        {
            DailyCoachNarrativeJobStatus.APPROVED.value,
            DailyCoachNarrativeJobStatus.REJECTED_VALIDATION.value,
        }
    ),
    DailyCoachNarrativeJobStatus.APPROVED.value: frozenset(
        {
            DailyCoachNarrativeJobStatus.STALE.value,
            DailyCoachNarrativeJobStatus.FALLBACK_AVAILABLE.value,
        }
    ),
}


class DailyCoachNarrativeJobRepositoryProtocol(Protocol):
    """Storage boundary for service-shell tests.

    This protocol intentionally describes in-memory-style job storage only. It
    does not authorize database persistence, a queue, a worker, provider runtime,
    FastAPI routes, Streamlit display behavior, or provider cache behavior.
    """

    def save(self, job: DailyCoachNarrativeJob) -> DailyCoachNarrativeJob:
        """Persist the supplied job in the repository shell."""

    def get(self, job_id: str) -> DailyCoachNarrativeJob | None:
        """Return a job by id, or None when absent."""

    def list_jobs(self) -> list[DailyCoachNarrativeJob]:
        """Return all known jobs."""


class InMemoryDailyCoachNarrativeJobRepository:
    """Deterministic in-memory repository for async narrative service tests."""

    def __init__(self) -> None:
        self._jobs: dict[str, DailyCoachNarrativeJob] = {}

    def save(self, job: DailyCoachNarrativeJob) -> DailyCoachNarrativeJob:
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> DailyCoachNarrativeJob | None:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[DailyCoachNarrativeJob]:
        return list(self._jobs.values())


def _status_value(status: DailyCoachNarrativeJobStatus | str) -> str:
    if isinstance(status, DailyCoachNarrativeJobStatus):
        return status.value
    return str(status)


def _iso_now(clock: Clock) -> str:
    return clock().astimezone(UTC).isoformat()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _sort_timestamp(value: str | None) -> str:
    return value or ""


class DailyCoachAsyncNarrativeService:
    """Service shell for future async Daily Coach narrative jobs.

    The shell owns deterministic job lifecycle behavior only. It never starts
    provider execution, never schedules background work, never creates a queue,
    never creates database schema, and never changes FastAPI or Streamlit UI
    behavior.
    """

    def __init__(
        self,
        repository: DailyCoachNarrativeJobRepositoryProtocol | None = None,
        *,
        clock: Clock | None = None,
        id_factory: IdFactory | None = None,
    ) -> None:
        self._repository = repository or InMemoryDailyCoachNarrativeJobRepository()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or self._default_id_factory
        self._counter = 0

    def _default_id_factory(self) -> str:
        self._counter += 1
        return f"daily-coach-async-job-{self._counter}"

    def create_job(
        self,
        context_identity: DailyCoachNarrativeContextIdentity,
        *,
        status: (
            DailyCoachNarrativeJobStatus | str
        ) = DailyCoachNarrativeJobStatus.QUEUED,
        expires_in: timedelta | None = None,
        expires_at: str | None = None,
        job_id: str | None = None,
    ) -> DailyCoachNarrativeJob:
        """Create a job record without starting provider work."""

        now = self._clock().astimezone(UTC)
        expiration = expires_at
        if expires_in is not None:
            expiration = (now + expires_in).isoformat()

        job = DailyCoachNarrativeJob(
            id=job_id or self._id_factory(),
            user_id=context_identity.user_id,
            target_date=context_identity.target_date,
            next_action_id=context_identity.next_action_id,
            workflow_target=context_identity.workflow_target,
            provider=context_identity.provider,
            model=context_identity.model,
            context_hash=context_identity.context_hash,
            prompt_contract_version=context_identity.prompt_contract_version,
            validator_version=context_identity.validator_version,
            status=status,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            expires_at=expiration,
        )
        return self._repository.save(job)

    def get_job(self, job_id: str) -> DailyCoachNarrativeJob | None:
        """Read a job without side effects."""

        return self._repository.get(job_id)

    def list_jobs(
        self,
        *,
        user_id: int | None = None,
        target_date: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> list[DailyCoachNarrativeJob]:
        jobs = self._repository.list_jobs()
        if user_id is not None:
            jobs = [job for job in jobs if job.user_id == user_id]
        if target_date is not None:
            jobs = [job for job in jobs if job.target_date == target_date]
        if provider is not None:
            jobs = [job for job in jobs if job.provider == provider]
        if model is not None:
            jobs = [job for job in jobs if job.model == model]
        return sorted(
            jobs,
            key=lambda job: (
                _sort_timestamp(job.updated_at),
                _sort_timestamp(job.created_at),
                job.id,
            ),
            reverse=True,
        )

    def get_latest_job(
        self,
        *,
        user_id: int,
        target_date: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> DailyCoachNarrativeJob | None:
        """Return the newest matching job by deterministic updated/created/id sort."""

        jobs = self.list_jobs(
            user_id=user_id,
            target_date=target_date,
            provider=provider,
            model=model,
        )
        return jobs[0] if jobs else None

    def get_latest_displayable_job(
        self,
        *,
        user_id: int,
        target_date: str,
        current_context: DailyCoachNarrativeContextIdentity,
    ) -> DailyCoachNarrativeJob | None:
        """Return the newest approved job that is valid for the current context."""

        for job in self.list_jobs(user_id=user_id, target_date=target_date):
            if self.is_displayable(job, current_context):
                return job
        return None

    def transition_job(
        self,
        job_id: str,
        status: DailyCoachNarrativeJobStatus | str,
        *,
        approved_narrative: ApprovedDailyCoachNarrativePayload | None = None,
        sanitized_failure_reason: str | None = None,
        latency_ms: int | None = None,
    ) -> DailyCoachNarrativeJob:
        """Move a job through an explicit status transition."""

        job = self._require_job(job_id)
        current = job.status_value
        next_status = _status_value(status)
        allowed = ALLOWED_STATUS_TRANSITIONS.get(current, frozenset())
        if next_status not in allowed and next_status != current:
            raise ValueError(
                f"Invalid Daily Coach async job transition: {current}->{next_status}"
            )

        updated = replace(
            job,
            status=status,
            approved_narrative=(
                approved_narrative
                if approved_narrative is not None
                else job.approved_narrative
            ),
            sanitized_failure_reason=sanitized_failure_reason,
            latency_ms=latency_ms if latency_ms is not None else job.latency_ms,
            updated_at=_iso_now(self._clock),
        )
        return self._repository.save(updated)

    def mark_job_stale(self, job_id: str) -> DailyCoachNarrativeJob:
        """Mark a job stale so it cannot be displayed."""

        job = self._require_job(job_id)
        updated = replace(
            job,
            status=DailyCoachNarrativeJobStatus.STALE,
            updated_at=_iso_now(self._clock),
        )
        return self._repository.save(updated)

    def expire_job(self, job_id: str) -> DailyCoachNarrativeJob:
        """Expire a job by converting it to stale service state."""

        return self.mark_job_stale(job_id)

    def is_expired(self, job: DailyCoachNarrativeJob) -> bool:
        expires_at = _parse_datetime(job.expires_at)
        if expires_at is None:
            return False
        return expires_at <= self._clock().astimezone(UTC)

    def is_context_valid(
        self,
        job: DailyCoachNarrativeJob,
        current_context: DailyCoachNarrativeContextIdentity,
        *,
        require_provider_model_match: bool = True,
    ) -> bool:
        """Return true only when a job exactly matches the current context."""

        if job.status_value == DailyCoachNarrativeJobStatus.STALE.value:
            return False
        if self.is_expired(job):
            return False

        checks = [
            job.user_id == current_context.user_id,
            job.target_date == current_context.target_date,
            job.next_action_id == current_context.next_action_id,
            job.workflow_target == current_context.workflow_target,
            job.context_hash == current_context.context_hash,
            job.prompt_contract_version == current_context.prompt_contract_version,
            job.validator_version == current_context.validator_version,
        ]
        if require_provider_model_match:
            checks.extend(
                [
                    job.provider == current_context.provider,
                    job.model == current_context.model,
                ]
            )
        return all(checks)

    def is_displayable(
        self,
        job: DailyCoachNarrativeJob,
        current_context: DailyCoachNarrativeContextIdentity,
    ) -> bool:
        """Return true only for approved, context-valid, non-expired jobs."""

        if job.status_value != DailyCoachNarrativeJobStatus.APPROVED.value:
            return False
        if job.approved_narrative is None:
            return False
        return self.is_context_valid(job, current_context)

    def classify_job_display_state(
        self,
        job: DailyCoachNarrativeJob | None,
        current_context: DailyCoachNarrativeContextIdentity,
    ) -> str:
        """Classify displayability without changing UI behavior."""

        if job is None:
            return "fallback_available"
        if self.is_displayable(job, current_context):
            return "displayable"
        if job.status_value == DailyCoachNarrativeJobStatus.STALE.value:
            return "stale"
        if self.is_expired(job):
            return "expired"
        if not self.is_context_valid(job, current_context):
            return "context_mismatch"
        if job.status_value in NON_DISPLAYABLE_STATUSES:
            return job.status_value
        return "fallback_available"

    def mark_context_mismatches_stale(
        self,
        jobs: Iterable[DailyCoachNarrativeJob],
        current_context: DailyCoachNarrativeContextIdentity,
    ) -> list[DailyCoachNarrativeJob]:
        """Mark approved jobs stale when they no longer match current context."""

        updated_jobs: list[DailyCoachNarrativeJob] = []
        for job in jobs:
            if (
                job.status_value == DailyCoachNarrativeJobStatus.APPROVED.value
                and not self.is_context_valid(job, current_context)
            ):
                updated_jobs.append(self.mark_job_stale(job.id))
        return updated_jobs

    def _require_job(self, job_id: str) -> DailyCoachNarrativeJob:
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(f"Unknown Daily Coach async narrative job: {job_id}")
        return job
