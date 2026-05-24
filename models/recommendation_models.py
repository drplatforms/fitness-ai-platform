from dataclasses import dataclass, field

from models.coaching_decision_models import CoachingDecision
from models.nutrition_target_models import NutritionTargets
from models.training_constraint_models import TrainingConstraints


@dataclass
class RecommendationContext:
    user_id: int
    scenario: str
    primary_goal: str
    body_weight_lb: float | None
    nutrition_targets: NutritionTargets
    training_constraints: TrainingConstraints
    coaching_decision: CoachingDecision
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    confidence: str = "Moderate"
    reason_codes: list[str] = field(default_factory=list)


@dataclass
class CandidateActionPlan:
    daily_coaching_recommendation: str
    workout_recommendation: str
    nutrition_action: str
    rationale: str
    confidence: str


@dataclass
class ApprovedActionPlan:
    daily_coaching_recommendation: str
    workout_recommendation: str
    nutrition_action: str
    rationale: str
    confidence: str
    scenario: str
    reason_codes: list[str] = field(default_factory=list)


@dataclass
class RecommendationRuntimeMetadata:
    configured_provider: str
    selected_provider: str
    crewai_attempted: bool
    fallback_used: bool
    fallback_reason: str | None
    candidate_valid: bool
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class ApprovedActionPlanResult:
    approved_action_plan: ApprovedActionPlan
    runtime_metadata: RecommendationRuntimeMetadata
