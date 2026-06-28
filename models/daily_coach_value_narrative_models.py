from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

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
    "quoted_values_used",
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
class ApprovedNarrativeValueClaim:
    """Backend-approved value that a provider may quote in narrative copy."""

    key: str
    label: str
    value: str | int | float | bool
    unit: str | None = None
    aliases: list[str] = field(default_factory=list)
    claim_type: Literal[
        "recovery",
        "nutrition_actual",
        "nutrition_target",
        "nutrition_gap",
        "training",
        "workout",
        "confidence",
        "limitation",
        "recommendation",
    ] = "recommendation"
    display_allowed: bool = True
    source: str = "backend"
    confidence: str | None = None
    priority: int = 3
    section_hint: (
        Literal[
            "summary",
            "nutrition_note",
            "training_note",
            "recovery_note",
            "priority_action",
        ]
        | None
    ) = None
    coaching_use: (
        Literal[
            "explain_today",
            "prioritize_action",
            "contextualize_limit",
            "support_nutrition_action",
            "support_training_action",
            "support_recovery_action",
            "avoid_overclaiming",
        ]
        | None
    ) = None
    display_hint: str | None = None
    value_style: (
        Literal[
            "status_only",
            "exact_value_allowed",
            "range_allowed",
            "food_option",
            "limitation_only",
        ]
        | None
    ) = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachTodayStory:
    """Backend-derived, claim-key-backed story of the day for provider synthesis."""

    day_type: Literal[
        "controlled_progress",
        "recovery_first",
        "nutrition_support",
        "nutrition_supported_strength_day",
        "data_quality_check",
        "maintain_and_log",
        "managed_deload_return",
        "training_execution_focus",
    ]
    why: str
    nutrition_angle: str
    training_angle: str
    recovery_angle: str
    priority_angle: str
    avoid_overreaction_angle: str
    primary_claim_keys: list[str] = field(default_factory=list)
    optional_action_claim_keys: list[str] = field(default_factory=list)
    limitation_claim_keys: list[str] = field(default_factory=list)
    human_label: str | None = None
    main_tension: str | None = None
    training_implication: str | None = None
    nutrition_implication: str | None = None
    recovery_implication: str | None = None
    avoid_overreaction: str | None = None
    desired_coaching_move: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachApprovedContextBriefSentence:
    """Natural provider-facing context sentence backed by approved claim keys."""

    text: str
    claim_keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachClaimBackingGuide:
    """Allowed natural phrasing for a specific approved claim key."""

    claim_key: str
    allowed_phrasings: list[str] = field(default_factory=list)
    disallowed_phrasings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachVerbosityBudget:
    """Provider-facing word budget guidance for adaptive Daily Coach copy."""

    mode: Literal["limited", "normal", "rich"]
    target_words_min: int
    target_words_max: int
    guidance: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
    quoted_values_used: list[str] = field(default_factory=list)

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
    quoted_values_used: list[str] = field(default_factory=list)

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
