from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CandidateHealthReportSection:
    section_summary: str
    key_observations: list[str]
    coaching_interpretation: str
    suggested_focus: str
    limitations_context: str
    confidence: str
    reason_codes: list[str]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> CandidateHealthReportSection:
        return cls(
            section_summary=payload["section_summary"],
            key_observations=list(payload["key_observations"]),
            coaching_interpretation=payload["coaching_interpretation"],
            suggested_focus=payload["suggested_focus"],
            limitations_context=payload["limitations_context"],
            confidence=payload["confidence"],
            reason_codes=list(payload["reason_codes"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedHealthReportSection:
    section: str
    section_summary: str
    key_observations: list[str]
    coaching_interpretation: str
    suggested_focus: str
    limitations_context: str
    confidence: str
    reason_codes: list[str]
    source: str

    @classmethod
    def from_candidate(
        cls,
        candidate: CandidateHealthReportSection,
        *,
        section: str,
        source: str,
    ) -> ApprovedHealthReportSection:
        return cls(
            section=section,
            section_summary=candidate.section_summary,
            key_observations=list(candidate.key_observations),
            coaching_interpretation=candidate.coaching_interpretation,
            suggested_focus=candidate.suggested_focus,
            limitations_context=candidate.limitations_context,
            confidence=candidate.confidence,
            reason_codes=list(candidate.reason_codes),
            source=source,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HealthReportSectionRuntimeMetadata:
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

    def to_debug_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedHealthReportSectionResult:
    approved_section: ApprovedHealthReportSection
    runtime_metadata: HealthReportSectionRuntimeMetadata
