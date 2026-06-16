from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ApprovedTrainingReportSection:
    section: str
    section_summary: str
    key_observations: list[str]
    performance_interpretation: str
    fatigue_recovery_interpretation: str
    suggested_focus: str
    limitations_context: str
    confidence: str
    reason_codes: list[str]
    source: str

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        source: str,
    ) -> ApprovedTrainingReportSection:
        return cls(
            section="training",
            section_summary=payload["section_summary"],
            key_observations=list(payload["key_observations"]),
            performance_interpretation=payload["performance_interpretation"],
            fatigue_recovery_interpretation=payload["fatigue_recovery_interpretation"],
            suggested_focus=payload["suggested_focus"],
            limitations_context=payload["limitations_context"],
            confidence=payload["confidence"],
            reason_codes=list(payload["reason_codes"]),
            source=source,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingReportSectionRuntimeMetadata:
    configured_provider: str
    selected_provider: str
    configured_model: str
    selected_model: str
    provider_attempted: bool
    fallback_used: bool
    fallback_reason: str | None
    candidate_valid: bool
    validation_errors: list[str]
    candidate_parse_status: str
    candidate_validation_status: str
    validation_status: str
    final_section_source: str
    raw_output_length: int | None = None
    raw_output_preview_truncated: str | None = None
    markdown_wrapper_detected: bool = False
    extra_keys_detected: list[str] = field(default_factory=list)
    wrapper_object_detected: bool = False
    elapsed_seconds: float | None = None
    provider_latency_ms: int | None = None
    required_anchor_count: int = 0
    matched_required_fact_anchors: list[str] = field(default_factory=list)
    missing_required_anchor_count: int = 0
    matched_approved_interpretation_claims: list[str] = field(default_factory=list)
    model_facing_quote_context: dict[str, Any] = field(default_factory=dict)
    approved_training_quote_context: dict[str, Any] = field(default_factory=dict)

    def to_debug_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedTrainingReportSectionResult:
    approved_section: ApprovedTrainingReportSection
    runtime_metadata: TrainingReportSectionRuntimeMetadata
