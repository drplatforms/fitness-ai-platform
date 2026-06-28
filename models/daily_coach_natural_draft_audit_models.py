from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

DailyCoachNaturalDraftProvider = Literal["deterministic", "direct_ollama", "openai"]
ClaimAuditSeverity = Literal["info", "warn", "fail", "block"]
ClaimAuditDecision = Literal["approve", "repair_required", "fallback_required"]
ProductVoiceAuditMode = Literal["exploration", "audit", "repair", "approval"]
ProductVoiceAuditDecision = Literal["approve", "repair_required", "fallback_required"]
ReviewerConclusion = Literal[
    "model_failure",
    "brief_failure",
    "audit_failure",
    "repair_failure",
    "fallback_failure",
    "product_voice_failure",
    "minor_voice_warning",
    "repaired_success",
    "fallback_success",
    "success",
]
FinalCopySource = Literal[
    "draft_approved",
    "repair_approved",
    "deterministic_fallback",
    "no_approved_copy",
    "skipped",
]


@dataclass(frozen=True)
class AddressingPolicy:
    allow_name: bool = False
    preferred_name: str | None = None
    default_reference: str = "the user"
    visible_name_usage: str = "forbidden_unless_explicitly_approved"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedCoachFact:
    claim_key: str
    claim_type: str
    value: str | int | float | bool | None
    display_value: str
    friendly_display_value: str | None = None
    user_facing_allowed: bool = True
    source: str = "backend"
    confidence: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedFoodAction:
    food_claim_key: str
    canonical_name: str | None
    friendly_name: str | None
    macro_reason: str | None
    allowed_conditions: tuple[str, ...] = field(default_factory=tuple)
    serving_display: str | None = None
    serving_allowed: bool = False
    blocked_user_facing_names: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedTrainingAction:
    claim_keys: tuple[str, ...]
    instruction: str
    allowed_phrasings: tuple[str, ...] = field(default_factory=tuple)
    blocked_phrasings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedRecoveryInterpretation:
    claim_keys: tuple[str, ...]
    interpretation: str
    allowed_phrasings: tuple[str, ...] = field(default_factory=tuple)
    blocked_phrasings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedCoachBrief:
    brief_id: str
    user_id: int
    date: str
    scenario: str
    today_intent: str
    addressing_policy: AddressingPolicy = field(default_factory=AddressingPolicy)
    approved_facts: tuple[ApprovedCoachFact, ...] = field(default_factory=tuple)
    approved_interpretations: tuple[str, ...] = field(default_factory=tuple)
    approved_food_actions: tuple[ApprovedFoodAction, ...] = field(default_factory=tuple)
    approved_training_actions: tuple[ApprovedTrainingAction, ...] = field(
        default_factory=tuple
    )
    approved_recovery_interpretations: tuple[ApprovedRecoveryInterpretation, ...] = (
        field(default_factory=tuple)
    )
    blocked_topics: tuple[str, ...] = field(default_factory=tuple)
    blocked_phrases: tuple[str, ...] = field(default_factory=tuple)
    claim_registry: dict[str, dict[str, Any]] = field(default_factory=dict)
    display_policy: dict[str, Any] = field(default_factory=dict)
    verbosity_policy: dict[str, Any] = field(default_factory=dict)
    repair_policy: dict[str, Any] = field(default_factory=dict)
    fallback_policy: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["addressing_policy"] = self.addressing_policy.to_dict()
        payload["approved_facts"] = [fact.to_dict() for fact in self.approved_facts]
        payload["approved_food_actions"] = [
            action.to_dict() for action in self.approved_food_actions
        ]
        payload["approved_training_actions"] = [
            action.to_dict() for action in self.approved_training_actions
        ]
        payload["approved_recovery_interpretations"] = [
            item.to_dict() for item in self.approved_recovery_interpretations
        ]
        return payload


@dataclass(frozen=True)
class NaturalCoachDraft:
    headline: str
    body: str
    provider: DailyCoachNaturalDraftProvider = "deterministic"
    model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExtractedDraftClaim:
    claim_type: str
    text_span: str
    normalized_claim: str
    claim_keys_matched: tuple[str, ...] = field(default_factory=tuple)
    extraction_source: str = "deterministic_regex"
    confidence: str = "medium"
    needs_audit: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClaimAuditFinding:
    finding_type: str
    severity: ClaimAuditSeverity
    text_span: str
    extracted_claim: str
    reason: str
    required_support: str
    available_support: tuple[str, ...] = field(default_factory=tuple)
    repair_instruction: str | None = None
    repairable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClaimAuditResult:
    passed: bool
    findings: tuple[ClaimAuditFinding, ...] = field(default_factory=tuple)
    repairable: bool = False
    final_decision: ClaimAuditDecision = "approve"
    unsupported_claim_count: int = 0
    food_claim_count: int = 0
    causal_claim_count: int = 0
    addressing_violation_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["findings"] = [finding.to_dict() for finding in self.findings]
        return payload


@dataclass(frozen=True)
class ProductVoiceAuditScore:
    dimension: str
    score: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProductVoiceAuditFinding:
    finding_type: str
    severity: ClaimAuditSeverity
    text_span: str
    reason: str
    repair_instruction: str | None = None
    repairable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProductVoiceAuditResult:
    passed: bool
    mode: ProductVoiceAuditMode
    decision: ProductVoiceAuditDecision
    scores: tuple[ProductVoiceAuditScore, ...] = field(default_factory=tuple)
    findings: tuple[ProductVoiceAuditFinding, ...] = field(default_factory=tuple)
    mechanical_food_action_count: int = 0
    backend_phrase_count: int = 0
    stale_skeleton_count: int = 0
    product_readiness_score: int = 1

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["scores"] = [score.to_dict() for score in self.scores]
        payload["findings"] = [finding.to_dict() for finding in self.findings]
        return payload


@dataclass(frozen=True)
class RepairAttemptResult:
    attempted: bool
    provider: DailyCoachNaturalDraftProvider
    model: str | None
    passed: bool = False
    findings_after_repair: tuple[ClaimAuditFinding, ...] = field(default_factory=tuple)
    final_copy: NaturalCoachDraft | None = None
    fallback_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["findings_after_repair"] = [
            finding.to_dict() for finding in self.findings_after_repair
        ]
        payload["final_copy"] = self.final_copy.to_dict() if self.final_copy else None
        return payload


@dataclass(frozen=True)
class NaturalDraftAuditRunResult:
    scenario_id: str
    user_id: int
    date: str
    provider: DailyCoachNaturalDraftProvider
    model: str | None
    draft: NaturalCoachDraft | None
    extracted_claims: tuple[ExtractedDraftClaim, ...]
    audit_result: ClaimAuditResult
    repair_result: RepairAttemptResult
    final_copy: NaturalCoachDraft | None
    final_source: FinalCopySource
    deterministic_fallback: NaturalCoachDraft | None = None
    product_voice_audit_result: ProductVoiceAuditResult | None = None
    repaired_product_voice_audit_result: ProductVoiceAuditResult | None = None
    fallback_product_voice_audit_result: ProductVoiceAuditResult | None = None
    reviewer_conclusion: ReviewerConclusion = "success"
    runtime_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["draft"] = self.draft.to_dict() if self.draft else None
        payload["extracted_claims"] = [
            claim.to_dict() for claim in self.extracted_claims
        ]
        payload["audit_result"] = self.audit_result.to_dict()
        payload["repair_result"] = self.repair_result.to_dict()
        payload["final_copy"] = self.final_copy.to_dict() if self.final_copy else None
        payload["deterministic_fallback"] = (
            self.deterministic_fallback.to_dict()
            if self.deterministic_fallback
            else None
        )
        payload["product_voice_audit_result"] = (
            self.product_voice_audit_result.to_dict()
            if self.product_voice_audit_result
            else None
        )
        payload["repaired_product_voice_audit_result"] = (
            self.repaired_product_voice_audit_result.to_dict()
            if self.repaired_product_voice_audit_result
            else None
        )
        payload["fallback_product_voice_audit_result"] = (
            self.fallback_product_voice_audit_result.to_dict()
            if self.fallback_product_voice_audit_result
            else None
        )
        return payload
