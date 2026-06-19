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
