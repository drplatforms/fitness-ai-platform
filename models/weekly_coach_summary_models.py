from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import date
from enum import StrEnum
from typing import Any


class WeeklyCoachSummaryModelError(ValueError):
    """Raised when a weekly coach summary contract is unsafe or invalid."""


class WeeklyCoachSummaryJobStatus(StrEnum):
    """Allowed lifecycle states for future Weekly Coach Summary async jobs."""

    NOT_CREATED = "not_created"
    CREATED = "created"
    PENDING = "pending"
    RUNNING = "running"
    APPROVED = "approved"
    REJECTED = "rejected"
    FALLBACK = "fallback"
    FAILED = "failed"
    EXPIRED = "expired"
    STALE = "stale"


class WeeklyCoachSummarySource(StrEnum):
    """Approved output sources.

    Provider-approved is future-safe vocabulary only. This module does not wire
    provider runtime and does not authorize provider execution.
    """

    DETERMINISTIC = "deterministic"
    PROVIDER_APPROVED = "provider_approved"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"


class WeeklyCoachSummaryConfidence(StrEnum):
    """Shared confidence vocabulary for weekly summary claims."""

    LIMITED = "Limited"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"


class WeeklyCoachSummaryParseStatus(StrEnum):
    """Future-safe parse status vocabulary for sanitized metadata only."""

    NOT_ATTEMPTED = "not_attempted"
    PARSED = "parsed"
    FAILED = "failed"


class WeeklyCoachSummaryValidationStatus(StrEnum):
    """Future-safe validation status vocabulary for sanitized metadata only."""

    NOT_ATTEMPTED = "not_attempted"
    APPROVED = "approved"
    REJECTED = "rejected"


WEEKLY_COACH_SUMMARY_JOB_STATUSES: tuple[str, ...] = tuple(
    status.value for status in WeeklyCoachSummaryJobStatus
)
WEEKLY_COACH_SUMMARY_SOURCES: tuple[str, ...] = tuple(
    source.value for source in WeeklyCoachSummarySource
)
WEEKLY_COACH_SUMMARY_CONFIDENCE_VALUES: tuple[str, ...] = tuple(
    confidence.value for confidence in WeeklyCoachSummaryConfidence
)

WEEKLY_COACH_SUMMARY_FORBIDDEN_APPROVED_FIELDS = frozenset(
    {
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
)

WEEKLY_COACH_SUMMARY_FORBIDDEN_LANGUAGE = (
    "you failed",
    "lack of discipline",
    "burn this off",
    "compensate tomorrow",
    "severe deficit",
    "critical deficit",
    "you must eat",
)


def _coerce_date(value: date | str, field_name: str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise WeeklyCoachSummaryModelError(
                f"{field_name} must be an ISO date string."
            ) from exc
    raise WeeklyCoachSummaryModelError(f"{field_name} must be a date or ISO string.")


def _coerce_enum(
    enum_type: type[StrEnum], value: StrEnum | str, field_name: str
) -> StrEnum:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value))
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_type)
        raise WeeklyCoachSummaryModelError(
            f"{field_name} must be one of: {allowed}."
        ) from exc


def _bounded_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise WeeklyCoachSummaryModelError(f"{field_name} must be text.")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise WeeklyCoachSummaryModelError(f"{field_name} must not be empty.")
    lowered = normalized.lower()
    for phrase in WEEKLY_COACH_SUMMARY_FORBIDDEN_LANGUAGE:
        if phrase in lowered:
            raise WeeklyCoachSummaryModelError(
                f"{field_name} contains unsafe weekly coaching language."
            )
    return normalized


def _optional_bounded_text(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _bounded_text(value, field_name)


def _safe_tuple(
    values: tuple[str, ...] | list[str] | None, field_name: str
) -> tuple[str, ...]:
    if values is None:
        return ()
    if not isinstance(values, tuple | list):
        raise WeeklyCoachSummaryModelError(
            f"{field_name} must be a list/tuple of text."
        )
    return tuple(_bounded_text(str(value), field_name) for value in values)


@dataclass(frozen=True)
class WeeklyCoachSummaryPeriod:
    """Bounded weekly summary period."""

    user_id: int
    week_start: date | str
    week_end: date | str
    timezone: str = "local"
    generated_for_date: date | str | None = None

    def __post_init__(self) -> None:
        if int(self.user_id) <= 0:
            raise WeeklyCoachSummaryModelError("user_id must be positive.")
        start = _coerce_date(self.week_start, "week_start")
        end = _coerce_date(self.week_end, "week_end")
        if start > end:
            raise WeeklyCoachSummaryModelError(
                "week_start must be on or before week_end."
            )
        if (end - start).days > 6:
            raise WeeklyCoachSummaryModelError(
                "Weekly summary period must be 7 days or fewer."
            )
        object.__setattr__(self, "week_start", start)
        object.__setattr__(self, "week_end", end)
        object.__setattr__(self, "timezone", _bounded_text(self.timezone, "timezone"))
        if self.generated_for_date is not None:
            object.__setattr__(
                self,
                "generated_for_date",
                _coerce_date(self.generated_for_date, "generated_for_date"),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "week_start": self.week_start.isoformat(),
            "week_end": self.week_end.isoformat(),
            "timezone": self.timezone,
            "generated_for_date": (
                self.generated_for_date.isoformat() if self.generated_for_date else None
            ),
        }


@dataclass(frozen=True)
class WeeklyCoachSummaryFactBoundary:
    """Fact availability contract, not a raw fact or raw database row container."""

    recovery_facts_available: bool = False
    nutrition_facts_available: bool = False
    training_facts_available: bool = False
    workout_execution_facts_available: bool = False
    daily_recommendation_facts_available: bool = False
    profile_context_available: bool = False
    data_quality_limited: bool = False
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "limitations", _safe_tuple(self.limitations, "limitations")
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WeeklyCoachSummaryContext:
    """Future deterministic context contract built only from approved facts."""

    user_id: int
    period: WeeklyCoachSummaryPeriod
    fact_boundary: WeeklyCoachSummaryFactBoundary
    confidence: WeeklyCoachSummaryConfidence | str
    scenario: str | None = None
    recovery_summary: str | None = None
    nutrition_summary: str | None = None
    training_summary: str | None = None
    workout_execution_summary: str | None = None
    recommendation_summary: str | None = None
    limitations: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.user_id != self.period.user_id:
            raise WeeklyCoachSummaryModelError(
                "context user_id must match period user_id."
            )
        object.__setattr__(
            self,
            "confidence",
            _coerce_enum(WeeklyCoachSummaryConfidence, self.confidence, "confidence"),
        )
        object.__setattr__(
            self, "scenario", _optional_bounded_text(self.scenario, "scenario")
        )
        for field_name in (
            "recovery_summary",
            "nutrition_summary",
            "training_summary",
            "workout_execution_summary",
            "recommendation_summary",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_bounded_text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self, "limitations", _safe_tuple(self.limitations, "limitations")
        )
        object.__setattr__(
            self, "reason_codes", _safe_tuple(self.reason_codes, "reason_codes")
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["period"] = self.period.to_dict()
        payload["fact_boundary"] = self.fact_boundary.to_dict()
        payload["confidence"] = self.confidence.value
        return payload


@dataclass(frozen=True)
class CandidateWeeklyCoachSummary:
    """Candidate weekly summary before approval.

    A candidate is not automatically approved. It may be deterministic now, while
    provider-generated candidates remain future/deferred.
    """

    headline: str
    weekly_overview: str
    recovery_observation: str
    nutrition_observation: str
    training_observation: str
    primary_pattern: str
    recommended_focus: str
    next_week_guidance: str
    confidence: WeeklyCoachSummaryConfidence | str
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for field_name in (
            "headline",
            "weekly_overview",
            "recovery_observation",
            "nutrition_observation",
            "training_observation",
            "primary_pattern",
            "recommended_focus",
            "next_week_guidance",
        ):
            object.__setattr__(
                self, field_name, _bounded_text(getattr(self, field_name), field_name)
            )
        object.__setattr__(
            self,
            "confidence",
            _coerce_enum(WeeklyCoachSummaryConfidence, self.confidence, "confidence"),
        )
        object.__setattr__(
            self, "reason_codes", _safe_tuple(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self, "limitations", _safe_tuple(self.limitations, "limitations")
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = self.confidence.value
        return payload


@dataclass(frozen=True)
class ApprovedWeeklyCoachSummary:
    """Approved/public-safe weekly summary shape for future persistence/display."""

    headline: str
    weekly_overview: str
    recovery_observation: str
    nutrition_observation: str
    training_observation: str
    primary_pattern: str
    recommended_focus: str
    next_week_guidance: str
    confidence: WeeklyCoachSummaryConfidence | str
    source: WeeklyCoachSummarySource | str
    public_safe: bool
    displayable: bool
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.displayable and not self.public_safe:
            raise WeeklyCoachSummaryModelError(
                "displayable weekly summaries must also be public_safe."
            )
        for field_name in (
            "headline",
            "weekly_overview",
            "recovery_observation",
            "nutrition_observation",
            "training_observation",
            "primary_pattern",
            "recommended_focus",
            "next_week_guidance",
        ):
            object.__setattr__(
                self, field_name, _bounded_text(getattr(self, field_name), field_name)
            )
        object.__setattr__(
            self,
            "confidence",
            _coerce_enum(WeeklyCoachSummaryConfidence, self.confidence, "confidence"),
        )
        object.__setattr__(
            self,
            "source",
            _coerce_enum(WeeklyCoachSummarySource, self.source, "source"),
        )
        object.__setattr__(
            self, "reason_codes", _safe_tuple(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self, "limitations", _safe_tuple(self.limitations, "limitations")
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = self.confidence.value
        payload["source"] = self.source.value
        return payload

    @classmethod
    def approved_field_names(cls) -> frozenset[str]:
        return frozenset(field.name for field in fields(cls))


@dataclass(frozen=True)
class WeeklyCoachSummaryRuntimeMetadata:
    """Sanitized future runtime metadata.

    Raw provider output, rejected output, prompts, raw context, stack traces, and
    secrets are intentionally not represented.
    """

    provider_attempted: bool = False
    fallback_used: bool = False
    fallback_reason: str | None = None
    parse_status: WeeklyCoachSummaryParseStatus | str = (
        WeeklyCoachSummaryParseStatus.NOT_ATTEMPTED
    )
    validation_status: WeeklyCoachSummaryValidationStatus | str = (
        WeeklyCoachSummaryValidationStatus.NOT_ATTEMPTED
    )
    final_summary_source: WeeklyCoachSummarySource | str = (
        WeeklyCoachSummarySource.DETERMINISTIC
    )
    validation_errors: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fallback_reason",
            _optional_bounded_text(self.fallback_reason, "fallback_reason"),
        )
        object.__setattr__(
            self,
            "parse_status",
            _coerce_enum(
                WeeklyCoachSummaryParseStatus, self.parse_status, "parse_status"
            ),
        )
        object.__setattr__(
            self,
            "validation_status",
            _coerce_enum(
                WeeklyCoachSummaryValidationStatus,
                self.validation_status,
                "validation_status",
            ),
        )
        object.__setattr__(
            self,
            "final_summary_source",
            _coerce_enum(
                WeeklyCoachSummarySource,
                self.final_summary_source,
                "final_summary_source",
            ),
        )
        object.__setattr__(
            self,
            "validation_errors",
            _safe_tuple(self.validation_errors, "validation_errors"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_attempted": self.provider_attempted,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "parse_status": self.parse_status.value,
            "validation_status": self.validation_status.value,
            "final_summary_source": self.final_summary_source.value,
            "validation_errors": self.validation_errors,
        }


@dataclass(frozen=True)
class WeeklyCoachSummaryJobRecord:
    """Contract-only job record; not a DB schema or persistence implementation."""

    job_id: str
    user_id: int
    period: WeeklyCoachSummaryPeriod
    status: WeeklyCoachSummaryJobStatus | str
    created_at: str
    updated_at: str
    started_at: str | None = None
    completed_at: str | None = None
    expires_at: str | None = None
    stale: bool = False
    expired: bool = False
    approved_summary: ApprovedWeeklyCoachSummary | None = None
    runtime_metadata: WeeklyCoachSummaryRuntimeMetadata = field(
        default_factory=WeeklyCoachSummaryRuntimeMetadata
    )

    def __post_init__(self) -> None:
        if self.user_id != self.period.user_id:
            raise WeeklyCoachSummaryModelError("job user_id must match period user_id.")
        object.__setattr__(self, "job_id", _bounded_text(self.job_id, "job_id"))
        object.__setattr__(
            self,
            "status",
            _coerce_enum(WeeklyCoachSummaryJobStatus, self.status, "status"),
        )
        object.__setattr__(
            self, "created_at", _bounded_text(self.created_at, "created_at")
        )
        object.__setattr__(
            self, "updated_at", _bounded_text(self.updated_at, "updated_at")
        )
        for field_name in ("started_at", "completed_at", "expires_at"):
            object.__setattr__(
                self,
                field_name,
                _optional_bounded_text(getattr(self, field_name), field_name),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "period": self.period.to_dict(),
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "expires_at": self.expires_at,
            "stale": self.stale,
            "expired": self.expired,
            "approved_summary": (
                self.approved_summary.to_dict() if self.approved_summary else None
            ),
            "runtime_metadata": self.runtime_metadata.to_dict(),
        }
