from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

DAILY_COACH_NARRATIVE_REQUIRED_OUTPUT_KEYS = {
    "coach_note",
    "key_takeaway",
    "recommended_focus",
    "confidence_language",
    "used_approved_facts",
    "avoided_claims",
}

DAILY_COACH_NARRATIVE_FORBIDDEN_CLAIMS_V1 = [
    "changed daily next action",
    "changed workflow target",
    "invented food",
    "invented exercise",
    "invented calorie target",
    "invented macro target",
    "invented serving size",
    "meal plan",
    "medical diagnosis",
    "clinical nutrition claim",
    "unsupported fatigue claim",
    "unsupported recovery claim",
    "unsupported progression claim",
    "unsupported consistency claim",
    "exercise substitution",
    "unapproved internal metadata",
]

DAILY_COACH_NARRATIVE_CONTEXT_STATUS_READY = "ready_for_future_provider"


@dataclass(frozen=True)
class DailyCoachNarrativeContext:
    """Backend-approved context packet for future Daily Coach Narrative work.

    This context is deterministic and public-safe. It is not a model output and it
    does not imply provider approval. Future provider output must be parsed and
    validated against this packet before anything becomes user-facing.
    """

    user_id: int
    date: str
    next_action_id: str
    next_action_title: str
    next_action_reason: str
    workflow_target: str
    priority: int
    severity: str
    approved_focus: str
    confidence_language: str
    approved_facts: list[str]
    approved_limitations: list[str]
    forbidden_claims: list[str] = field(
        default_factory=lambda: list(DAILY_COACH_NARRATIVE_FORBIDDEN_CLAIMS_V1)
    )
    fallback_note: str = ""
    source_metadata: dict[str, Any] = field(default_factory=dict)
    context_status: str = DAILY_COACH_NARRATIVE_CONTEXT_STATUS_READY

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DAILY_COACH_TODAY_CARD_DISPLAY_SOURCE = "deterministic_today_card"


@dataclass(frozen=True)
class DailyCoachTodayCard:
    """Public-safe deterministic Today Coach Note display contract.

    Normal Today UI consumes only ``to_public_dict()`` fields. Developer metadata
    exists for Developer Mode inspection only and must not drive normal display.
    """

    user_id: int
    date: str
    next_action_id: str
    next_action_title: str
    workflow_target: str
    card_title: str
    coach_note: str
    cta_label: str
    cta_target: str
    supporting_reason: str
    display_source: str = DAILY_COACH_TODAY_CARD_DISPLAY_SOURCE
    is_provider_generated: bool = False
    is_fallback: bool = False
    user_visible: bool = True
    developer_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "card_title": self.card_title,
            "coach_note": self.coach_note,
            "next_action_title": self.next_action_title,
            "cta_label": self.cta_label,
            "cta_target": self.cta_target,
            "supporting_reason": self.supporting_reason,
        }

    def to_developer_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "date": self.date,
            "next_action_id": self.next_action_id,
            "next_action_title": self.next_action_title,
            "workflow_target": self.workflow_target,
            "display_source": self.display_source,
            "is_provider_generated": self.is_provider_generated,
            "is_fallback": self.is_fallback,
            "user_visible": self.user_visible,
            "developer_metadata": dict(self.developer_metadata),
        }


DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS = "success"
DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED = "failed"

DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED = "approved"
DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED = "rejected"

DAILY_COACH_NARRATIVE_DECISION_PASS = "pass"
DAILY_COACH_NARRATIVE_DECISION_FAIL = "fail"


@dataclass(frozen=True)
class CandidateDailyCoachNarrative:
    """Strict provider candidate output for offline narrative QA.

    This is not user-facing until a validator approves it. Normal Today UI does
    not consume this object in v1.
    """

    coach_note: str
    key_takeaway: str
    recommended_focus: str
    confidence_language: str
    used_approved_facts: list[str]
    avoided_claims: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachNarrativeParseResult:
    parse_status: str
    candidate: CandidateDailyCoachNarrative | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.parse_status == DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["candidate"] = self.candidate.to_dict() if self.candidate else None
        return payload


@dataclass(frozen=True)
class DailyCoachNarrativeValidationResult:
    validation_status: str
    validation_errors: list[str]
    forbidden_claims_found: list[str]

    @property
    def approved(self) -> bool:
        return (
            self.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachNarrativePreviewResult:
    """Public-safe developer preview payload for Daily Coach Narrative.

    This object may contain approved provider narrative only after validation
    succeeds. Rejected model output, raw prompts, raw provider payloads, raw
    validation internals, and stack traces are intentionally excluded.
    """

    user_id: int
    date: str
    next_action_id: str
    next_action_title: str
    workflow_target: str
    provider_enabled: bool
    provider_attempted: bool
    selected_provider: str
    selected_model: str | None
    parse_success: bool
    validation_success: bool
    fallback_used: bool
    fallback_reason: str | None
    approved_narrative: dict[str, Any] | None
    deterministic_fallback_note: str
    approved_focus: str
    context_summary: dict[str, Any]
    latency_ms: int | None = None
    developer_diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachNarrativeScores:
    grounding: int
    claim_safety: int
    coach_voice: int
    specificity: int
    brevity: int
    actionability: int
    validator_compatibility: int
    runtime_practicality: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachNarrativeOfflineQAResult:
    model_name: str
    user_id: int
    date: str
    next_action_id: str
    next_action_title: str
    workflow_target: str
    parse_status: str
    validation_status: str
    overall_decision: str
    elapsed_seconds: float
    latency_ms: int
    scores: DailyCoachNarrativeScores
    validation_errors: list[str]
    forbidden_claims_found: list[str]
    representative_safe_excerpt: str | None = None
    representative_rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["scores"] = self.scores.to_dict()
        return payload
