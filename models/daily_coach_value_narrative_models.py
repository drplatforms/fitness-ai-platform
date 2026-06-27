from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

DAILY_COACH_VALUE_NARRATIVE_PROVIDERS = {
    "deterministic",
    "direct_ollama",
    "openai",
}

DAILY_COACH_VALUE_NARRATIVE_CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

DAILY_COACH_VALUE_NARRATIVE_CANDIDATE_KEYS = {
    "headline",
    "summary",
    "nutrition_note",
    "training_note",
    "recovery_note",
    "priority_action",
    "confidence",
    "reason_codes",
}

DAILY_COACH_VALUE_NARRATIVE_PARSE_SUCCESS = "success"
DAILY_COACH_VALUE_NARRATIVE_PARSE_FAILED = "failed"
DAILY_COACH_VALUE_NARRATIVE_PARSE_NOT_ATTEMPTED = "not_attempted"

DAILY_COACH_VALUE_NARRATIVE_VALIDATION_SUCCESS = "success"
DAILY_COACH_VALUE_NARRATIVE_VALIDATION_FAILED = "failed"
DAILY_COACH_VALUE_NARRATIVE_VALIDATION_NOT_ATTEMPTED = "not_attempted"

DAILY_COACH_VALUE_NARRATIVE_STATUS_APPROVED = "approved"
DAILY_COACH_VALUE_NARRATIVE_STATUS_REJECTED = "rejected"
DAILY_COACH_VALUE_NARRATIVE_STATUS_NOT_ATTEMPTED = "not_attempted"

DAILY_COACH_VALUE_NARRATIVE_SOURCE_DETERMINISTIC = "deterministic"
DAILY_COACH_VALUE_NARRATIVE_SOURCE_DIRECT_OLLAMA_APPROVED = "direct_ollama_approved"
DAILY_COACH_VALUE_NARRATIVE_SOURCE_OPENAI_APPROVED = "openai_approved"
DAILY_COACH_VALUE_NARRATIVE_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"


@dataclass(frozen=True)
class CandidateDailyCoachValueNarrative:
    """Strict provider candidate for value-aware Daily Coach narrative copy.

    Provider output is not user-facing until parsed, validated, and converted to
    ApprovedDailyCoachValueNarrative. Providers may quote only backend-approved
    values present in the value-aware provider context.
    """

    headline: str
    summary: str
    nutrition_note: str
    training_note: str
    recovery_note: str
    priority_action: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedDailyCoachValueNarrative:
    """Backend-approved user-facing Daily Coach narrative contract."""

    headline: str
    summary: str
    nutrition_note: str
    training_note: str
    recovery_note: str
    priority_action: str
    confidence: str
    source: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachValueNarrativeRuntimeMetadata:
    configured_provider: str
    selected_provider: str
    configured_model: str | None
    selected_model: str | None
    provider_attempted: bool
    fallback_used: bool
    fallback_reason: str | None
    candidate_parse_status: str
    candidate_validation_status: str
    validation_status: str
    final_narrative_source: str
    raw_output_length: int | None = None
    raw_output_preview_truncated: bool | None = None
    markdown_wrapper_detected: bool = False
    validation_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachValueNarrativeResult:
    user_id: int
    narrative_date: str
    approved_daily_coach_narrative: ApprovedDailyCoachValueNarrative
    rendered_narrative: str
    runtime_metadata: DailyCoachValueNarrativeRuntimeMetadata
    provider_context_summary: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "success": True,
            "user_id": self.user_id,
            "narrative_date": self.narrative_date,
            "approved_daily_coach_narrative": (
                self.approved_daily_coach_narrative.to_dict()
            ),
            "rendered_narrative": self.rendered_narrative,
        }

    def to_debug_dict(self) -> dict[str, Any]:
        payload = self.to_public_dict()
        payload["runtime_metadata"] = self.runtime_metadata.to_dict()
        payload["provider_context_summary"] = dict(self.provider_context_summary)
        return payload
