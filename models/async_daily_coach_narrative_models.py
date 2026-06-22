from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class DailyCoachNarrativeJobStatus(StrEnum):
    """Allowed lifecycle states for a future async Daily Coach narrative job."""

    NOT_REQUESTED = "not_requested"
    QUEUED = "queued"
    GENERATING = "generating"
    PROVIDER_SUCCEEDED_PENDING_VALIDATION = "provider_succeeded_pending_validation"
    APPROVED = "approved"
    REJECTED_VALIDATION = "rejected_validation"
    REJECTED_PARSE = "rejected_parse"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_ERROR = "provider_error"
    STALE = "stale"
    EXPIRED = "expired"
    FALLBACK_AVAILABLE = "fallback_available"


class DailyCoachNarrativeModelLane(StrEnum):
    """Model lane contract for Daily Coach narrative work."""

    DETERMINISTIC = "deterministic"
    FAST_MANUAL_BRIDGE = "fast_manual_bridge"
    PREMIUM_ASYNC_CANDIDATE = "premium_async_candidate"
    EXPERIMENTAL_PROBE = "experimental_probe"


DAILY_COACH_NARRATIVE_JOB_STATUSES: tuple[str, ...] = tuple(
    status.value for status in DailyCoachNarrativeJobStatus
)

DAILY_COACH_NARRATIVE_MODEL_LANES: tuple[str, ...] = tuple(
    lane.value for lane in DailyCoachNarrativeModelLane
)

DAILY_COACH_ASYNC_JOB_TABLE = "daily_coach_async_jobs"
DAILY_COACH_APPROVED_NARRATIVE_TABLE = "daily_coach_approved_narratives"

DAILY_COACH_ASYNC_JOB_REQUIRED_COLUMNS = (
    "id",
    "job_id",
    "user_id",
    "target_date",
    "workflow_target",
    "next_action_id",
    "context_hash",
    "context_version",
    "prompt_contract_version",
    "validator_version",
    "status",
    "created_at",
    "updated_at",
    "started_at",
    "completed_at",
    "expires_at",
    "stale_after",
    "stale",
    "expired",
    "displayable",
    "public_safe",
    "fallback_used",
    "fallback_reason",
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
)

DAILY_COACH_APPROVED_NARRATIVE_REQUIRED_COLUMNS = (
    "id",
    "narrative_id",
    "job_id",
    "user_id",
    "target_date",
    "context_hash",
    "context_version",
    "approved_narrative_json",
    "approved_text",
    "reason_codes_json",
    "action_refs_json",
    "validator_version",
    "prompt_contract_version",
    "created_at",
    "expires_at",
    "stale",
    "expired",
    "displayable",
    "public_safe",
    "final_narrative_source",
)

DAILY_COACH_ASYNC_PERSISTENCE_FORBIDDEN_COLUMNS = frozenset(
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

DAILY_COACH_NARRATIVE_BRIDGE_BASELINE_MODEL = "qwen2.5:3b"
DAILY_COACH_NARRATIVE_PREMIUM_ASYNC_CANDIDATE_MODELS = frozenset({"qwen3:32b"})
DAILY_COACH_NARRATIVE_EXPERIMENTAL_PROBE_MODELS = frozenset(
    {
        "qwen2.5:7b",
        "qwen3:8b",
        "qwen3:14b",
        "qwen3:30b-a3b",
    }
)

DAILY_COACH_NARRATIVE_MODELS_NOT_BRIDGE_APPROVED = frozenset(
    {
        "qwen2.5:7b",
        "qwen3:8b",
        "qwen3:14b",
        "qwen3:30b-a3b",
        "qwen3:32b",
    }
)

DAILY_COACH_NARRATIVE_FORBIDDEN_DIAGNOSTIC_KEYS = frozenset(
    {
        "raw_prompt",
        "raw_output",
        "raw_rejected_output",
        "rejected_output",
        "provider_raw_output",
        "prompt",
        "stack_trace",
        "traceback",
        "secret",
    }
)


def normalize_daily_coach_narrative_model_name(model: str | None) -> str:
    """Return the canonical comparison form for a model name."""

    return (model or "").strip().lower()


def get_daily_coach_narrative_model_lane(
    model: str | None,
) -> DailyCoachNarrativeModelLane:
    """Classify a model without promoting it.

    The lane is descriptive policy metadata only. It does not authorize runtime
    execution, product display, bridge approval, or persistence.
    """

    normalized = normalize_daily_coach_narrative_model_name(model)
    if normalized in {"", "deterministic"}:
        return DailyCoachNarrativeModelLane.DETERMINISTIC
    if normalized == DAILY_COACH_NARRATIVE_BRIDGE_BASELINE_MODEL:
        return DailyCoachNarrativeModelLane.FAST_MANUAL_BRIDGE
    if normalized in DAILY_COACH_NARRATIVE_PREMIUM_ASYNC_CANDIDATE_MODELS:
        return DailyCoachNarrativeModelLane.PREMIUM_ASYNC_CANDIDATE
    return DailyCoachNarrativeModelLane.EXPERIMENTAL_PROBE


def is_daily_coach_narrative_bridge_approved_model(model: str | None) -> bool:
    """Return true only for the existing fast manual bridge baseline."""

    return (
        normalize_daily_coach_narrative_model_name(model)
        == DAILY_COACH_NARRATIVE_BRIDGE_BASELINE_MODEL
    )


def is_daily_coach_narrative_premium_async_candidate(model: str | None) -> bool:
    """Return true for future premium async candidates without promoting them."""

    return (
        normalize_daily_coach_narrative_model_name(model)
        in DAILY_COACH_NARRATIVE_PREMIUM_ASYNC_CANDIDATE_MODELS
    )


@dataclass(frozen=True)
class DailyCoachNarrativeContextIdentity:
    """Stable identity for future async narrative generation and staleness checks."""

    user_id: int
    target_date: str
    next_action_id: str
    workflow_target: str
    provider: str
    model: str
    prompt_contract_version: str
    validator_version: str
    context_hash: str

    @property
    def model_lane(self) -> DailyCoachNarrativeModelLane:
        return get_daily_coach_narrative_model_lane(self.model)

    @property
    def bridge_approved(self) -> bool:
        return is_daily_coach_narrative_bridge_approved_model(self.model)

    @property
    def premium_async_candidate(self) -> bool:
        return is_daily_coach_narrative_premium_async_candidate(self.model)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["model_lane"] = self.model_lane.value
        payload["bridge_approved"] = self.bridge_approved
        payload["premium_async_candidate"] = self.premium_async_candidate
        return payload


@dataclass(frozen=True)
class ApprovedDailyCoachNarrativePayload:
    """Approved/sanitized narrative payload only.

    This model intentionally has no raw prompt, raw output, rejected output, stack
    trace, or secret fields. It represents text that has already passed the
    parser, schema, validation, model eligibility, and context gates.
    """

    narrative: str
    key_takeaway: str
    recommended_focus: str
    source: str
    provider: str
    model: str
    validation_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SanitizedDailyCoachNarrativeDiagnostics:
    """Safe diagnostics for Developer Mode and future job metadata.

    Raw prompts, raw rejected output, stack traces, and secrets are explicitly out
    of contract and are not represented as fields here.
    """

    provider_attempted: bool
    selected_provider: str
    selected_model: str
    parse_success: bool
    validation_success: bool
    fallback_used: bool
    fallback_reason: str | None
    failure_classification: str | None
    latency_ms: int | None
    model_lane: DailyCoachNarrativeModelLane | str
    approval_eligible: bool

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        lane = payload["model_lane"]
        if isinstance(lane, DailyCoachNarrativeModelLane):
            payload["model_lane"] = lane.value
        return payload


@dataclass(frozen=True)
class DailyCoachNarrativeJob:
    """In-memory/contract model for future async Daily Coach narrative jobs.

    This is not a database model and does not create persistence. It exists so
    later service/runtime milestones can share one typed job contract.
    """

    id: str
    user_id: int
    target_date: str
    next_action_id: str
    workflow_target: str
    provider: str
    model: str
    context_hash: str
    prompt_contract_version: str
    validator_version: str
    status: DailyCoachNarrativeJobStatus | str
    approved_narrative: ApprovedDailyCoachNarrativePayload | None = None
    sanitized_failure_reason: str | None = None
    latency_ms: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    expires_at: str | None = None

    @property
    def status_value(self) -> str:
        if isinstance(self.status, DailyCoachNarrativeJobStatus):
            return self.status.value
        return str(self.status)

    @property
    def model_lane(self) -> DailyCoachNarrativeModelLane:
        return get_daily_coach_narrative_model_lane(self.model)

    @property
    def bridge_approved(self) -> bool:
        return is_daily_coach_narrative_bridge_approved_model(self.model)

    @property
    def approval_eligible(self) -> bool:
        return self.status_value == DailyCoachNarrativeJobStatus.APPROVED.value

    def context_identity(self) -> DailyCoachNarrativeContextIdentity:
        return DailyCoachNarrativeContextIdentity(
            user_id=self.user_id,
            target_date=self.target_date,
            next_action_id=self.next_action_id,
            workflow_target=self.workflow_target,
            provider=self.provider,
            model=self.model,
            prompt_contract_version=self.prompt_contract_version,
            validator_version=self.validator_version,
            context_hash=self.context_hash,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status_value
        payload["model_lane"] = self.model_lane.value
        payload["bridge_approved"] = self.bridge_approved
        payload["approval_eligible"] = self.approval_eligible
        payload["approved_narrative"] = (
            self.approved_narrative.to_dict() if self.approved_narrative else None
        )
        return payload
