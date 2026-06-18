from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ApprovedTrainingClaim:
    claim_id: str
    claim_type: str
    approved_meaning: str
    required_names: list[str] = field(default_factory=list)
    required_terms: list[str] = field(default_factory=list)
    allowed_terms: list[str] = field(default_factory=list)
    forbidden_scope: list[str] = field(default_factory=list)
    source_fact_refs: list[str] = field(default_factory=list)
    scope: str = "single_session"
    confidence: str = "Moderate"
    public_safe: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingEvidenceContext:
    workout_names: list[str] = field(default_factory=list)
    exercise_names: list[str] = field(default_factory=list)
    set_rep_load_rir_values: list[dict[str, Any]] = field(default_factory=list)
    training_summary_facts: list[str] = field(default_factory=list)
    required_quote_name: str | None = None
    required_fact_anchors: list[str] = field(default_factory=list)
    source: str = "approved_training_quote_context"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingClaimValidationResult:
    claim_valid: bool
    validation_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
