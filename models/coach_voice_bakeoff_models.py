from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

COACH_VOICE_CONTEXT_DAILY_NEXT_ACTION = "daily_next_action"
COACH_VOICE_CONTEXT_NUTRITION_TARGET_VS_ACTUAL = "nutrition_target_vs_actual"
COACH_VOICE_CONTEXT_WORKOUT_PREVIEW = "workout_preview"
COACH_VOICE_CONTEXT_RECOVERY_LIMITED = "recovery_limited"
COACH_VOICE_CONTEXT_DATA_QUALITY_LIMITED = "data_quality_limited"

COACH_VOICE_CONTEXT_TYPES = {
    COACH_VOICE_CONTEXT_DAILY_NEXT_ACTION,
    COACH_VOICE_CONTEXT_NUTRITION_TARGET_VS_ACTUAL,
    COACH_VOICE_CONTEXT_WORKOUT_PREVIEW,
    COACH_VOICE_CONTEXT_RECOVERY_LIMITED,
    COACH_VOICE_CONTEXT_DATA_QUALITY_LIMITED,
}

COACH_VOICE_OUTPUT_REQUIRED_FIELDS = {
    "coach_note",
    "key_takeaway",
    "recommended_focus",
    "confidence_language",
    "used_approved_facts",
    "avoided_claims",
}

COACH_VOICE_DECISION_PASS = "pass"
COACH_VOICE_DECISION_FAIL = "fail"

COACH_VOICE_PARSE_STATUS_SUCCESS = "success"
COACH_VOICE_PARSE_STATUS_FAILED = "failed"

COACH_VOICE_VALIDATION_STATUS_APPROVED = "approved"
COACH_VOICE_VALIDATION_STATUS_REJECTED = "rejected"


@dataclass(frozen=True)
class CoachVoiceContext:
    context_id: str
    context_type: str
    user_id: int
    title: str
    approved_facts: list[str]
    approved_focus_options: list[str]
    forbidden_claims: list[str] = field(default_factory=list)
    workflow_target: str | None = None
    severity: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CoachVoiceCandidateOutput:
    coach_note: str
    key_takeaway: str
    recommended_focus: str
    confidence_language: str
    used_approved_facts: list[str]
    avoided_claims: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CoachVoiceParseResult:
    parse_status: str
    output: CoachVoiceCandidateOutput | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["output"] = self.output.to_dict() if self.output else None
        return payload


@dataclass(frozen=True)
class CoachVoiceValidationResult:
    validation_status: str
    validation_errors: list[str]
    forbidden_claims_found: list[str]

    @property
    def approved(self) -> bool:
        return self.validation_status == COACH_VOICE_VALIDATION_STATUS_APPROVED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CoachVoiceScores:
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
class CoachVoiceBakeoffResult:
    model_name: str
    context_id: str
    context_type: str
    parse_status: str
    validation_status: str
    overall_decision: str
    elapsed_seconds: float
    latency_ms: int
    scores: CoachVoiceScores
    validation_errors: list[str]
    forbidden_claims_found: list[str]
    representative_safe_excerpt: str | None = None
    representative_rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["scores"] = self.scores.to_dict()
        return payload
