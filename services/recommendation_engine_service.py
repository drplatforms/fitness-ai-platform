import json
import logging
import os
import re
import time
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from models.recommendation_models import (
    ApprovedActionPlan,
    ApprovedActionPlanResult,
    CandidateActionPlan,
    RecommendationContext,
    RecommendationRuntimeMetadata,
)
from models.user_state_models import UserHealthState
from services.coaching_decision_service import build_coaching_decision
from services.nutrition_target_service import (
    build_nutrition_targets,
    nutrition_targets_to_user_dict,
)
from services.training_constraint_service import build_training_constraints
from services.training_execution_summary_service import build_training_execution_summary

CANDIDATE_ACTION_PLAN_REQUIRED_FIELDS = {
    "daily_coaching_recommendation",
    "workout_recommendation",
    "nutrition_action",
    "rationale",
    "confidence",
}
CANDIDATE_ACTION_PLAN_ALLOWED_FIELDS = CANDIDATE_ACTION_PLAN_REQUIRED_FIELDS
CANDIDATE_ACTION_PLAN_CONFIDENCE_VALUES = {"Low", "Moderate", "High"}
CandidateActionPlanProvider = Callable[[RecommendationContext], str]
RECOMMENDATION_CANDIDATE_PROVIDER_ENV = "RECOMMENDATION_CANDIDATE_PROVIDER"
RECOMMENDATION_PROVIDER_DETERMINISTIC = "deterministic"
RECOMMENDATION_PROVIDER_CREWAI = "crewai"

logger = logging.getLogger(__name__)

FALLBACK_REASON_DETERMINISTIC_SELECTED = "deterministic_selected"
FALLBACK_REASON_INVALID_PROVIDER = "invalid_provider"
FALLBACK_REASON_PROVIDER_EXCEPTION = "provider_exception"
FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT = "provider_non_string_output"
FALLBACK_REASON_MALFORMED_JSON = "malformed_json"
FALLBACK_REASON_SCHEMA_MISMATCH = "schema_mismatch"
FALLBACK_REASON_INVALID_CONFIDENCE = "invalid_confidence"
FALLBACK_REASON_VALIDATION_FAILURE = "validation_failure"

CANDIDATE_PARSE_STATUS_SUCCESS = "success"
CANDIDATE_PARSE_STATUS_FAILED = "failed"
CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED = "not_attempted"
CANDIDATE_VALIDATION_STATUS_SUCCESS = "success"
CANDIDATE_VALIDATION_STATUS_FAILED = "failed"
CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED = "not_attempted"
FINAL_PLAN_SOURCE_DETERMINISTIC = "deterministic"
FINAL_PLAN_SOURCE_CREWAI_APPROVED = "crewai_approved"
FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"
RAW_OUTPUT_PREVIEW_LIMIT = 240

_CONFIDENCE_RANK = {"Low": 1, "Moderate": 2, "High": 3}

_INTERNAL_DEBUG_TERMS = [
    "guardrail",
    "guardrails",
    "validation",
    "validator",
    "fallback",
    "deterministic",
    "backend",
    "schema",
    "source of truth",
    "reason code",
    "reason codes",
    "debug",
    "internal",
    "candidateactionplan",
    "approvedactionplan",
    "recommendationcontext",
    "nutritiontargets",
    "trainingconstraints",
    "coachingdecision",
    "data_quality_limited",
    "aligned_managed",
    "recovery_limited",
    "nutrition_training_mismatch",
    "improving_after_deload",
]

_FORBIDDEN_RECOMMENDATION_PHRASES = [
    "high-rir (0-1)",
    "high rir (0-1)",
    "lower rir to 2-3",
    "sleep deprivation (5.3/10)",
    "likely from supplements",
    "over-supplementation likely",
    "supplementation artifacts",
    "0 kcal",
    "0 g protein",
    "0g protein",
    "0 g carbs",
    "0g carbs",
    "0 g fat",
    "0g fat",
]
_ZERO_NUTRITION_RE = re.compile(
    r"\b0\s*(?:kcal|calories?|g\s*(?:protein|carbs?|fat))\b"
)


_CALORIE_CLAIM_RE = re.compile(
    r"\b(\d{3,5})\s*(?:-|to)?\s*(\d{3,5})?\s*(?:kcal|calories?)\b"
)
_PROTEIN_CLAIM_RE = re.compile(
    r"\bprotein\s+(\d{1,3})\s*(?:-|to)?\s*(\d{1,3})?\s*g(?:/day)?\b"
)
_CARBOHYDRATE_CLAIM_RE = re.compile(
    r"\b(?:carbohydrates?|carbs?)\s+(\d{1,4})\s*(?:-|to)?\s*(\d{1,4})?\s*g(?:/day)?\b"
)
_FAT_CLAIM_RE = re.compile(r"\bfat\s+(\d{1,3})\s*(?:-|to)?\s*(\d{1,3})?\s*g(?:/day)?\b")

_EXECUTION_AWARE_CLAIM_TERMS = [
    "planned workout",
    "planned workouts",
    "planned session",
    "planned sessions",
    "planned-vs-actual",
    "planned vs actual",
    "execution history",
    "execution summary",
    "workout execution",
    "actual effort",
    "actual-set",
    "actual set",
    "actual sets",
    "harder than planned",
    "easier than planned",
    "skipped exercise",
    "skipped exercises",
    "substituted exercise",
    "substituted exercises",
    "substitution",
    "substitutions",
]

_EXECUTION_AWARE_STRONG_TREND_TERMS = [
    "trend",
    "trends",
    "pattern",
    "patterns",
    "consistently",
    "repeated",
    "repeatedly",
    "proves",
    "shows that",
    "demonstrates",
]

_EXECUTION_AWARE_FORBIDDEN_CLAIMS = [
    "overtraining",
    "poor adherence",
    "failed programming",
    "stalled progress",
    "automatic deload",
    "deload required",
    "required deload",
    "automatic load increase",
    "automatically increase load",
    "automatically increase weight",
    "automatic progression",
    "user failed the workout",
    "failed the workout",
    "plan is bad",
    "bad plan",
    "plan is ineffective",
    "ineffective plan",
    "lack of discipline",
    "one workout proves",
    "one workout shows",
    "one workout means",
]

_EXECUTION_AWARE_LOW_CONFIDENCE_FORBIDDEN_TERMS = [
    "trend",
    "trends",
    "pattern",
    "patterns",
    "consistently",
    "repeated",
    "repeatedly",
    "mostly completed",
    "high completion",
    "harder than planned",
    "easier than planned",
    "increase load",
    "increase weight",
    "deload",
]

_EXECUTION_AWARE_SOFT_CONTEXT_TERMS = [
    "logging",
    "context",
    "limited",
    "developing",
    "interpretation",
    "review",
    "verify",
]


def _append_sentence(existing_text: str, sentence: str | None) -> str:
    if not sentence:
        return existing_text

    cleaned = existing_text.rstrip()
    if cleaned.endswith(sentence):
        return cleaned
    return f"{cleaned} {sentence}"


def _limited_execution_context_sentence(context: RecommendationContext) -> str | None:
    summary = context.training_execution_summary
    if summary is None:
        return None

    if summary.completed_execution_count == 0:
        return None

    if summary.confidence == "Limited":
        return None

    if summary.confidence == "Low" or summary.completed_execution_count == 1:
        return (
            "Actual-set logging context is still developing, so keep logging "
            "actual reps, weight, and RIR before drawing stronger planned-vs-actual conclusions."
        )

    return None


def _execution_logging_uncertainty_sentence(
    context: RecommendationContext,
) -> str | None:
    summary = context.training_execution_summary
    if summary is None:
        return None

    if summary.confidence == "Limited":
        return None

    if (
        summary.incomplete_logging_count
        or summary.missing_actual_rir_count
        or summary.missing_actual_reps_count
    ):
        return (
            "Incomplete actual-set logging limits interpretation, so keep logging "
            "actual reps, weight, and RIR before using execution history for stronger conclusions."
        )

    return None


def _execution_quality_sentence(context: RecommendationContext) -> str | None:
    summary = context.training_execution_summary
    if summary is None:
        return None

    if summary.completed_execution_count < 2:
        return None

    if summary.confidence not in {"Moderate", "High"}:
        return None

    if (
        summary.incomplete_logging_count
        or summary.missing_actual_rir_count
        or summary.missing_actual_reps_count
    ):
        return None

    if summary.execution_quality in {"mostly_completed", "consistently_completed"}:
        return (
            "Recent completed planned workouts were mostly completed, so maintain "
            "controlled progression while monitoring recovery and actual RIR."
        )

    return None


def _execution_effort_sentence(context: RecommendationContext) -> str | None:
    summary = context.training_execution_summary
    if summary is None:
        return None

    if summary.completed_execution_count < 2:
        return None

    if summary.confidence not in {"Moderate", "High"}:
        return None

    if summary.execution_effort_trend == "harder_than_planned":
        if context.scenario == "data_quality_limited":
            return None
        return (
            "Recent actual effort was harder than planned, so keep working sets "
            "closer to the approved RIR range instead of pushing toward failure."
        )

    if summary.execution_effort_trend == "easier_than_planned":
        if context.scenario in {"data_quality_limited", "recovery_limited"}:
            return None
        return (
            "Recent actual effort was easier than planned, so monitor whether load "
            "selection still matches the intended effort target before changing progression."
        )

    return None


def _execution_plan_fit_sentence(context: RecommendationContext) -> str | None:
    summary = context.training_execution_summary
    if summary is None:
        return None

    if summary.completed_execution_count < 2:
        return None

    if summary.confidence not in {"Moderate", "High"}:
        return None

    if summary.skipped_exercise_count and summary.substituted_exercise_count:
        return (
            "Repeated skipped or substituted exercises may suggest reviewing plan fit, "
            "equipment fit, session length, recovery, or nutrition support."
        )

    if summary.substituted_exercise_count:
        return (
            "Repeated substitutions may suggest reviewing exercise fit or equipment fit "
            "before increasing training demand."
        )

    if summary.skipped_exercise_count:
        return (
            "Repeated skipped exercises may suggest reviewing plan fit, session length, "
            "recovery, or nutrition support."
        )

    return None


def _apply_execution_aware_copy(
    plan: CandidateActionPlan,
    context: RecommendationContext,
) -> CandidateActionPlan:
    """Add conservative execution-aware deterministic copy when policy allows it.

    TrainingExecutionSummary stays out of the response shape and CrewAI payload.
    This helper only adjusts deterministic CandidateActionPlan copy after the
    summary clears completed-workout, confidence, and scenario gates.
    """

    summary = context.training_execution_summary
    if summary is None:
        return plan

    if summary.completed_execution_count == 0 or summary.confidence == "Limited":
        return plan

    daily = plan.daily_coaching_recommendation
    workout = plan.workout_recommendation
    rationale = plan.rationale

    limited_sentence = _limited_execution_context_sentence(context)
    if limited_sentence:
        rationale = _append_sentence(rationale, limited_sentence)
        return CandidateActionPlan(
            daily_coaching_recommendation=daily,
            workout_recommendation=workout,
            nutrition_action=plan.nutrition_action,
            rationale=rationale,
            confidence=plan.confidence,
        )

    rationale = _append_sentence(
        rationale, _execution_logging_uncertainty_sentence(context)
    )
    daily = _append_sentence(daily, _execution_quality_sentence(context))
    workout = _append_sentence(workout, _execution_effort_sentence(context))
    rationale = _append_sentence(rationale, _execution_plan_fit_sentence(context))

    return CandidateActionPlan(
        daily_coaching_recommendation=daily,
        workout_recommendation=workout,
        nutrition_action=plan.nutrition_action,
        rationale=rationale,
        confidence=plan.confidence,
    )


def build_recommendation_context(
    health_state: UserHealthState,
) -> RecommendationContext:
    coaching_decision = build_coaching_decision(health_state)
    nutrition_targets = build_nutrition_targets(health_state)
    training_constraints = build_training_constraints(health_state, coaching_decision)
    training_execution_summary = build_training_execution_summary(health_state.user_id)

    allowed_actions = [
        coaching_decision.training_action,
        coaching_decision.nutrition_action,
        coaching_decision.sleep_action,
        coaching_decision.monitoring_action,
        training_constraints.progression_guidance,
    ]
    forbidden_claims = [
        "Do not treat missing nutrition fields as zero intake.",
        "Do not assume supplements explain unusual micronutrient values.",
        "Do not describe RIR 0-1 as high RIR.",
        "Do not prescribe calorie targets unless NutritionTargets allows calories.",
        "Do not prescribe protein targets unless body weight is available.",
        "Do not prescribe targets outside NutritionTargets v1 ranges.",
    ]

    return RecommendationContext(
        user_id=health_state.user_id,
        scenario=coaching_decision.scenario,
        primary_goal=health_state.primary_goal,
        body_weight_lb=nutrition_targets.body_weight_lb,
        nutrition_targets=nutrition_targets,
        training_constraints=training_constraints,
        coaching_decision=coaching_decision,
        training_execution_summary=training_execution_summary,
        allowed_actions=allowed_actions,
        forbidden_claims=forbidden_claims,
        confidence=coaching_decision.confidence,
        reason_codes=list(
            dict.fromkeys(
                coaching_decision.reason_codes
                + nutrition_targets.reason_codes
                + training_constraints.reason_codes
            )
        ),
    )


def recommendation_context_to_json(context: RecommendationContext) -> str:
    return json.dumps(asdict(context), indent=2)


def recommendation_context_to_llm_json(context: RecommendationContext) -> str:
    """Serialize only LLM-safe RecommendationContext fields for CrewAI prompts.

    This intentionally uses the user-facing NutritionTargets display contract so
    disallowed target values are not exposed to the model. For example, a
    Limited-confidence user can see the nutrition_display_message and approved
    protein range, but not hidden calorie/carbohydrate/fat ranges.

    TrainingExecutionSummary is intentionally not included in this LLM payload
    in the passive integration milestone. That keeps execution history available
    to backend/debug context without changing CrewAI recommendation behavior.
    """

    safe_payload = {
        "user_id": context.user_id,
        "scenario": context.scenario,
        "primary_goal": context.primary_goal,
        "body_weight_lb": context.body_weight_lb,
        "confidence": context.confidence,
        "nutrition_targets": nutrition_targets_to_user_dict(context.nutrition_targets),
        "training_constraints": asdict(context.training_constraints),
        "approved_strategy": {
            "primary_focus": context.coaching_decision.primary_focus,
            "training_action": context.coaching_decision.training_action,
            "nutrition_action": context.coaching_decision.nutrition_action,
            "sleep_action": context.coaching_decision.sleep_action,
            "monitoring_action": context.coaching_decision.monitoring_action,
            "confidence": context.coaching_decision.confidence,
        },
        "allowed_actions": context.allowed_actions,
        "forbidden_claims": context.forbidden_claims,
    }
    return json.dumps(safe_payload, indent=2)


def build_crewai_candidate_action_plan_prompt(context: RecommendationContext) -> str:
    """Return the CrewAI task prompt for candidate recommendation JSON."""
    return f"""
You write concise coaching copy inside a required JSON object.

The approved context below already contains the user's scenario, target-display
permissions, training constraints, and safety boundaries. Follow that context.
Do not choose a different strategy.

Approved context:
{recommendation_context_to_llm_json(context)}

Return raw JSON only.
- The first character must be {{.
- The last character must be }}.
- Do not use markdown, code fences, headings, bullets, commentary, or extra fields.
- Use exactly these fields:
  - daily_coaching_recommendation
  - workout_recommendation
  - nutrition_action
  - rationale
  - confidence

Required JSON object:
{{
  "daily_coaching_recommendation": "one user-facing sentence",
  "workout_recommendation": "one user-facing sentence",
  "nutrition_action": "one user-facing sentence",
  "rationale": "one user-facing sentence explaining the tradeoff",
  "confidence": "Low | Moderate | High"
}}

Rules:
- Use only the approved context.
- Do not invent calorie, protein, carbohydrate, fat, mineral, or vitamin targets.
- Do not mention hidden target ranges.
- Mention protein ranges only when protein targets are approved.
- If nutrition target confidence is Limited, emphasize logging and verification.
- Follow the RIR, progression, and recovery guidance from the approved context.
- Treat missing nutrition as unknown, never zero.
- Do not infer supplement use from unusual nutrients.
- Do not make unsupported causal claims.
- Do not include internal system, validation, fallback, debug, model, or data-label terms.
- Confidence must not exceed the approved context confidence.
""".strip()


def _crew_result_to_raw_json(result: Any) -> str:
    raw = getattr(result, "raw", None)
    if raw is not None:
        return str(raw)
    return str(result)


def generate_crewai_candidate_action_plan_json(context: RecommendationContext) -> str:
    """Run the CrewAI CandidateActionPlan task and return its raw JSON output.

    The returned string is intentionally not trusted. Callers must pass it through
    parse_candidate_action_plan(), validate_candidate_action_plan(), and approval
    before it can become user-facing content.
    """
    from crewai import LLM, Agent, Crew, Task

    llm = LLM(
        model=os.getenv("CREWAI_RECOMMENDATION_MODEL", "ollama/qwen3:8b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )

    recommendation_agent = Agent(
        role="Grounded Recommendation Generator",
        goal="Generate safe CandidateActionPlan JSON from approved context only.",
        backstory=(
            "You create candidate coaching actions from structured health, "
            "nutrition, training, and scenario constraints."
        ),
        llm=llm,
        verbose=False,
    )

    recommendation_task = Task(
        description=build_crewai_candidate_action_plan_prompt(context),
        expected_output="Raw CandidateActionPlan JSON object only. No markdown.",
        agent=recommendation_agent,
    )

    crew = Crew(
        agents=[recommendation_agent],
        tasks=[recommendation_task],
        verbose=False,
    )

    result = crew.kickoff()
    return _crew_result_to_raw_json(result)


def _protein_target_phrase(context: RecommendationContext) -> str:
    targets = context.nutrition_targets
    if (
        targets.allow_protein_targets
        and targets.protein_grams_min is not None
        and targets.protein_grams_max is not None
    ):
        return f"protein {targets.protein_grams_min}-{targets.protein_grams_max} g/day"
    return "protein support against training demand"


def _carbohydrate_target_phrase(context: RecommendationContext) -> str:
    targets = context.nutrition_targets
    if (
        targets.allow_carbohydrate_targets
        and targets.carbohydrate_grams_min is not None
        and targets.carbohydrate_grams_max is not None
    ):
        return (
            f"carbohydrates {targets.carbohydrate_grams_min}-"
            f"{targets.carbohydrate_grams_max} g/day"
        )
    return "carbohydrate support against training demand"


def _nutrition_check_in_phrase(context: RecommendationContext) -> str:
    targets = context.nutrition_targets
    if targets.confidence == "Limited":
        return (
            f"Keep nutrition logging consistent and use {_protein_target_phrase(context)} "
            "as a body-weight-based check-in point. Avoid hard calorie targets until "
            "logging confidence improves."
        )

    if (
        targets.allow_calorie_targets
        and targets.calorie_target_min
        and targets.calorie_target_max
    ):
        return (
            "Keep nutrition logging consistent and use the current target ranges as "
            f"check-in points: {targets.calorie_target_min}-{targets.calorie_target_max} "
            f"calories/day and {_protein_target_phrase(context)}."
        )

    return (
        f"Keep nutrition logging consistent and compare {_protein_target_phrase(context)} "
        f"and {_carbohydrate_target_phrase(context)} against training demand."
    )


def generate_candidate_action_plan_json(context: RecommendationContext) -> str:
    """Return structured JSON for the v1 recommendation vertical slice.

    This deterministic implementation is the local stand-in for the CrewAI JSON task.
    The schema and validator are the contract the future CrewAI task must satisfy.
    """
    decision = context.coaching_decision
    constraints = context.training_constraints

    if context.scenario == "aligned_managed":
        plan = CandidateActionPlan(
            daily_coaching_recommendation=(
                "Maintain the current direction and progress gradually while recovery markers stay stable."
            ),
            workout_recommendation=constraints.progression_guidance,
            nutrition_action=_nutrition_check_in_phrase(context),
            rationale=(
                "Recovery, training load, and nutrition appear aligned enough to favor consistency over intervention."
            ),
            confidence=context.confidence,
        )
    elif context.scenario == "recovery_limited":
        plan = CandidateActionPlan(
            daily_coaching_recommendation=decision.primary_focus,
            workout_recommendation=constraints.low_rir_guidance,
            nutrition_action=(
                "Review protein and carbohydrate support against training demand without assuming missing intake is zero."
            ),
            rationale=(
                "Sleep, soreness, energy, and training effort suggest recovery should lead the next recommendation."
            ),
            confidence=context.confidence,
        )
    elif context.scenario == "nutrition_training_mismatch":
        plan = CandidateActionPlan(
            daily_coaching_recommendation=decision.primary_focus,
            workout_recommendation=constraints.progression_guidance,
            nutrition_action=(
                f"Improve nutrition logging and compare {_protein_target_phrase(context)} "
                "and carbohydrate support against training demand."
            ),
            rationale=(
                "Training demand appears higher than confirmed nutrition support, but missing fields are unknown rather than zero."
            ),
            confidence=context.confidence,
        )
    elif context.scenario == "improving_after_deload":
        plan = CandidateActionPlan(
            daily_coaching_recommendation=(
                "Continue controlled progression while the recovery trend stabilizes."
            ),
            workout_recommendation=constraints.low_rir_guidance,
            nutrition_action=(
                "Keep nutrition logging consistent on training days and review support against training demand."
            ),
            rationale=(
                "The recent lower-stress period appears to be helping, so the next step is gradual progression."
            ),
            confidence=context.confidence,
        )
    else:
        plan = CandidateActionPlan(
            daily_coaching_recommendation=(
                "Improve logging completeness before making stronger nutrition or training changes."
            ),
            workout_recommendation=constraints.progression_guidance,
            nutrition_action=(
                "Verify food entries and unusual nutrient values; treat missing fields as unknown."
            ),
            rationale=(
                "Data quality limits confidence, so verification should come before stronger conclusions."
            ),
            confidence=context.confidence,
        )

    plan = _apply_execution_aware_copy(plan, context)
    return json.dumps(asdict(plan))


def candidate_action_plan_json_contract() -> dict[str, Any]:
    """Return the JSON contract the future CrewAI task must satisfy.

    CrewAI may reason internally, but the backend only accepts this exact
    structured CandidateActionPlan object. Invalid output falls back to the
    deterministic candidate generator.
    """
    return {
        "type": "object",
        "required_fields": sorted(CANDIDATE_ACTION_PLAN_REQUIRED_FIELDS),
        "allowed_fields": sorted(CANDIDATE_ACTION_PLAN_ALLOWED_FIELDS),
        "field_types": {
            "daily_coaching_recommendation": "string",
            "workout_recommendation": "string",
            "nutrition_action": "string",
            "rationale": "string",
            "confidence": "Low | Moderate | High",
        },
    }


def parse_candidate_action_plan(raw_json: str) -> CandidateActionPlan:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError("CandidateActionPlan must be valid JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("CandidateActionPlan JSON must be an object.")

    payload_fields = set(payload)
    missing = CANDIDATE_ACTION_PLAN_REQUIRED_FIELDS - payload_fields
    if missing:
        raise ValueError(f"CandidateActionPlan missing fields: {sorted(missing)}")

    extra = payload_fields - CANDIDATE_ACTION_PLAN_ALLOWED_FIELDS
    if extra:
        raise ValueError(f"CandidateActionPlan has unsupported fields: {sorted(extra)}")

    for field in CANDIDATE_ACTION_PLAN_REQUIRED_FIELDS:
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise ValueError(
                f"CandidateActionPlan field must be a non-empty string: {field}"
            )

    if payload["confidence"] not in CANDIDATE_ACTION_PLAN_CONFIDENCE_VALUES:
        raise ValueError(
            "CandidateActionPlan confidence must be one of: "
            f"{sorted(CANDIDATE_ACTION_PLAN_CONFIDENCE_VALUES)}"
        )

    return CandidateActionPlan(
        daily_coaching_recommendation=payload["daily_coaching_recommendation"],
        workout_recommendation=payload["workout_recommendation"],
        nutrition_action=payload["nutrition_action"],
        rationale=payload["rationale"],
        confidence=payload["confidence"],
    )


def _all_range_values_within(
    claimed_values: tuple[int, ...], minimum: int, maximum: int
) -> bool:
    return all(minimum <= value <= maximum for value in claimed_values)


def _validate_numeric_calorie_claims(
    text: str, context: RecommendationContext
) -> list[str]:
    targets = context.nutrition_targets
    violations: list[str] = []

    for match in _CALORIE_CLAIM_RE.finditer(text):
        values = tuple(int(value) for value in match.groups() if value is not None)
        if not targets.allow_calorie_targets:
            violations.append(
                "Numeric calorie recommendations are not allowed at current target confidence."
            )
            continue

        if targets.calorie_target_min is None or targets.calorie_target_max is None:
            violations.append(
                "Numeric calorie recommendation has no approved calorie range."
            )
            continue

        if not _all_range_values_within(
            values, targets.calorie_target_min, targets.calorie_target_max
        ):
            violations.append(
                "Numeric calorie recommendation is outside NutritionTargets range."
            )

    return violations


def _validate_numeric_protein_claims(
    text: str, context: RecommendationContext
) -> list[str]:
    targets = context.nutrition_targets
    violations: list[str] = []

    for match in _PROTEIN_CLAIM_RE.finditer(text):
        values = tuple(int(value) for value in match.groups() if value is not None)
        if not targets.allow_protein_targets:
            violations.append(
                "Numeric protein recommendations are not allowed without body weight."
            )
            continue

        if targets.protein_grams_min is None or targets.protein_grams_max is None:
            violations.append(
                "Numeric protein recommendation has no approved protein range."
            )
            continue

        if not _all_range_values_within(
            values, targets.protein_grams_min, targets.protein_grams_max
        ):
            violations.append(
                "Numeric protein recommendation is outside NutritionTargets range."
            )

    return violations


def _validate_numeric_carbohydrate_claims(
    text: str, context: RecommendationContext
) -> list[str]:
    targets = context.nutrition_targets
    violations: list[str] = []

    for match in _CARBOHYDRATE_CLAIM_RE.finditer(text):
        values = tuple(int(value) for value in match.groups() if value is not None)
        if not targets.allow_carbohydrate_targets:
            violations.append(
                "Numeric carbohydrate recommendations are not allowed at current target confidence."
            )
            continue

        if (
            targets.carbohydrate_grams_min is None
            or targets.carbohydrate_grams_max is None
        ):
            violations.append(
                "Numeric carbohydrate recommendation has no approved carbohydrate range."
            )
            continue

        if not _all_range_values_within(
            values, targets.carbohydrate_grams_min, targets.carbohydrate_grams_max
        ):
            violations.append(
                "Numeric carbohydrate recommendation is outside NutritionTargets range."
            )

    return violations


def _validate_numeric_fat_claims(
    text: str, context: RecommendationContext
) -> list[str]:
    targets = context.nutrition_targets
    violations: list[str] = []

    for match in _FAT_CLAIM_RE.finditer(text):
        values = tuple(int(value) for value in match.groups() if value is not None)
        if not targets.allow_fat_targets:
            violations.append(
                "Numeric fat recommendations are not allowed at current target confidence."
            )
            continue

        if targets.fat_grams_min is None or targets.fat_grams_max is None:
            violations.append("Numeric fat recommendation has no approved fat range.")
            continue

        if not _all_range_values_within(
            values, targets.fat_grams_min, targets.fat_grams_max
        ):
            violations.append(
                "Numeric fat recommendation is outside NutritionTargets range."
            )

    return violations


def _validate_execution_aware_claims(
    text: str,
    context: RecommendationContext,
) -> list[str]:
    summary = context.training_execution_summary
    if summary is None:
        return []

    violations: list[str] = []
    has_execution_claim = any(term in text for term in _EXECUTION_AWARE_CLAIM_TERMS)
    has_strong_trend_claim = has_execution_claim and any(
        term in text for term in _EXECUTION_AWARE_STRONG_TREND_TERMS
    )

    for claim in _EXECUTION_AWARE_FORBIDDEN_CLAIMS:
        if claim in text:
            violations.append(
                "Execution-aware recommendations must not make forbidden claims: "
                f"{claim}"
            )

    if summary.completed_execution_count == 0 and has_execution_claim:
        violations.append(
            "Execution-aware recommendation claims are not allowed without completed planned workouts."
        )

    if summary.completed_execution_count < 2 and has_strong_trend_claim:
        violations.append(
            "Execution-aware trend claims require at least two completed planned workouts."
        )

    if summary.confidence == "Limited" and has_execution_claim:
        violations.append(
            "Limited-confidence TrainingExecutionSummary must not produce user-facing execution-aware claims."
        )

    if summary.confidence == "Low" and has_execution_claim:
        has_soft_context = any(
            term in text for term in _EXECUTION_AWARE_SOFT_CONTEXT_TERMS
        )
        has_low_confidence_forbidden_term = any(
            term in text for term in _EXECUTION_AWARE_LOW_CONFIDENCE_FORBIDDEN_TERMS
        )
        if has_low_confidence_forbidden_term or not has_soft_context:
            violations.append(
                "Low-confidence TrainingExecutionSummary may only support soft logging or context language."
            )

    if "skipped" in text and any(
        term in text
        for term in [
            "poor adherence",
            "lack of discipline",
            "failed the workout",
            "user failed",
            "noncompliance",
        ]
    ):
        violations.append(
            "Skipped exercise language must use plan-fit or review framing, not adherence or failure framing."
        )

    if any(term in text for term in ["substitution", "substitutions", "substituted"]):
        if any(
            term in text
            for term in [
                "failure",
                "failed",
                "noncompliance",
                "poor adherence",
                "lack of discipline",
            ]
        ):
            violations.append(
                "Substitution language must use plan-fit or equipment-fit framing, not failure or noncompliance framing."
            )

    if summary.execution_effort_trend == "harder_than_planned":
        if has_execution_claim and any(
            term in text
            for term in ["overtraining", "deload", "reduce intensity required"]
        ):
            violations.append(
                "Harder-than-planned effort must not be framed as overtraining or an automatic deload requirement."
            )

    if summary.execution_effort_trend == "easier_than_planned":
        if has_execution_claim and any(
            term in text
            for term in [
                "automatic progression",
                "automatic load increase",
                "automatically increase load",
                "increase load",
                "increase weight",
            ]
        ):
            violations.append(
                "Easier-than-planned effort must not trigger automatic progression or load-increase claims."
            )

    if summary.incomplete_logging_count:
        strong_execution_quality_terms = [
            "mostly completed",
            "consistently completed",
            "high completion",
            "strong execution trend",
            "reliable execution trend",
        ]
        if has_execution_claim and any(
            term in text for term in strong_execution_quality_terms
        ):
            violations.append(
                "Incomplete actual-set logging must not support strong execution-quality claims."
            )

    return violations


def validate_candidate_action_plan(
    candidate: CandidateActionPlan,
    context: RecommendationContext,
) -> list[str]:
    text = " ".join(
        [
            candidate.daily_coaching_recommendation,
            candidate.workout_recommendation,
            candidate.nutrition_action,
            candidate.rationale,
        ]
    ).lower()
    violations: list[str] = []

    for phrase in _FORBIDDEN_RECOMMENDATION_PHRASES:
        if phrase in text:
            violations.append(f"Forbidden recommendation phrase: {phrase}")

    for term in _INTERNAL_DEBUG_TERMS:
        if term in text:
            violations.append(
                "CandidateActionPlan user-facing fields must not include internal "
                f"or debug language: {term}"
            )

    if _CONFIDENCE_RANK[candidate.confidence] > _CONFIDENCE_RANK[context.confidence]:
        violations.append(
            "CandidateActionPlan confidence must not exceed RecommendationContext confidence."
        )

    if _ZERO_NUTRITION_RE.search(text):
        violations.append("Missing nutrition must not be framed as zero intake.")

    violations.extend(_validate_numeric_calorie_claims(text, context))
    violations.extend(_validate_numeric_protein_claims(text, context))
    violations.extend(_validate_numeric_carbohydrate_claims(text, context))
    violations.extend(_validate_numeric_fat_claims(text, context))
    violations.extend(_validate_execution_aware_claims(text, context))

    if context.scenario == "recovery_limited":
        if "low_rir_high_effort_training" in context.reason_codes:
            if "rir 2-3" not in text or "rir 0-1" not in text:
                violations.append(
                    "Recovery-limited low-RIR recommendations must include RIR 2-3 guidance."
                )

    if context.scenario == "aligned_managed":
        intervention_terms = ["deload", "reduce intensity", "caloric deficit"]
        if any(term in text for term in intervention_terms):
            violations.append(
                "Aligned/managed recommendations should not use unnecessary intervention framing."
            )

    if context.scenario == "nutrition_training_mismatch":
        zero_intake_phrases = [
            "missing intake is zero",
            "missing fields are zero",
            "missing nutrition is zero",
        ]
        if any(phrase in text for phrase in zero_intake_phrases):
            violations.append("Missing nutrition must not be framed as zero intake.")

    if context.scenario == "data_quality_limited":
        if "verify" not in text and "logging" not in text:
            violations.append(
                "Data-quality-limited recommendations must emphasize verification or logging."
            )

        strong_claims = [
            "overtraining",
            "stalled weight loss",
            "stalled fat loss",
            "compromise recovery",
            "compromise fat-loss progress",
            "likely contribute",
            "likely caused",
            "likely causing",
            "insufficient caloric intake",
            "inadequate caloric intake",
            "severe deficit",
            "caloric deficit",
        ]
        if any(claim in text for claim in strong_claims):
            violations.append(
                "Data-quality-limited recommendations must not make strong causal, progress, or intake-adequacy claims."
            )

    return violations


def approve_candidate_action_plan(
    candidate: CandidateActionPlan,
    context: RecommendationContext,
) -> ApprovedActionPlan:
    violations = validate_candidate_action_plan(candidate, context)
    if violations:
        raise ValueError("CandidateActionPlan rejected: " + "; ".join(violations))

    return ApprovedActionPlan(
        daily_coaching_recommendation=candidate.daily_coaching_recommendation,
        workout_recommendation=candidate.workout_recommendation,
        nutrition_action=candidate.nutrition_action,
        rationale=candidate.rationale,
        confidence=candidate.confidence,
        scenario=context.scenario,
        reason_codes=context.reason_codes,
    )


def render_approved_action_plan(plan: ApprovedActionPlan) -> str:
    return (
        "**Grounded Recommendation**\n\n"
        f"**Daily Coaching Recommendation:** {plan.daily_coaching_recommendation}\n\n"
        f"**Workout Recommendation:** {plan.workout_recommendation}\n\n"
        f"**Nutrition Action:** {plan.nutrition_action}\n\n"
        f"**Why:** {plan.rationale}\n\n"
        f"**Confidence:** {plan.confidence}"
    )


def build_deterministic_approved_action_plan(
    context: RecommendationContext,
) -> ApprovedActionPlan:
    raw_json = generate_candidate_action_plan_json(context)
    candidate = parse_candidate_action_plan(raw_json)
    return approve_candidate_action_plan(candidate, context)


def _fallback_reason_for_parse_error(error: ValueError) -> str:
    message = str(error).lower()
    if "valid json" in message:
        return FALLBACK_REASON_MALFORMED_JSON
    if "confidence" in message:
        return FALLBACK_REASON_INVALID_CONFIDENCE
    return FALLBACK_REASON_SCHEMA_MISMATCH


def _markdown_wrapper_detected(raw_output: str) -> bool:
    stripped = raw_output.strip().lower()
    return stripped.startswith("```") or "```json" in stripped or "```" in stripped


def _truncate_raw_output_preview(raw_output: str) -> str:
    compact = " ".join(raw_output.split())
    if len(compact) <= RAW_OUTPUT_PREVIEW_LIMIT:
        return compact
    return compact[:RAW_OUTPUT_PREVIEW_LIMIT] + "..."


def _raw_output_diagnostics(raw_output: str | None) -> dict[str, Any]:
    if raw_output is None:
        return {
            "raw_output_length": None,
            "raw_output_preview_truncated": None,
            "markdown_wrapper_detected": False,
        }

    return {
        "raw_output_length": len(raw_output),
        "raw_output_preview_truncated": _truncate_raw_output_preview(raw_output),
        "markdown_wrapper_detected": _markdown_wrapper_detected(raw_output),
    }


def _deterministic_result(
    context: RecommendationContext,
    metadata: RecommendationRuntimeMetadata,
) -> ApprovedActionPlanResult:
    return ApprovedActionPlanResult(
        approved_action_plan=build_deterministic_approved_action_plan(context),
        runtime_metadata=metadata,
    )


def _log_recommendation_runtime(
    context: RecommendationContext,
    metadata: RecommendationRuntimeMetadata,
    elapsed_ms: int,
) -> None:
    logger.info(
        "recommendation_candidate_provider_result",
        extra={
            "user_id": context.user_id,
            "scenario": context.scenario,
            "configured_provider": metadata.configured_provider,
            "selected_provider": metadata.selected_provider,
            "model": os.getenv("CREWAI_RECOMMENDATION_MODEL", "ollama/qwen3:8b"),
            "context_confidence": context.confidence,
            "nutrition_confidence": context.nutrition_targets.confidence,
            "crewai_attempted": metadata.crewai_attempted,
            "candidate_parse_status": metadata.candidate_parse_status,
            "candidate_validation_status": metadata.candidate_validation_status,
            "final_plan_source": metadata.final_plan_source,
            "fallback_used": metadata.fallback_used,
            "fallback_reason": metadata.fallback_reason,
            "validation_violations": metadata.validation_errors,
            "raw_output_length": metadata.raw_output_length,
            "raw_output_preview_truncated": metadata.raw_output_preview_truncated,
            "markdown_wrapper_detected": metadata.markdown_wrapper_detected,
            "elapsed_ms": elapsed_ms,
        },
    )


def approve_candidate_json_or_fallback_with_metadata(
    raw_json: str,
    context: RecommendationContext,
    *,
    configured_provider: str = RECOMMENDATION_PROVIDER_DETERMINISTIC,
    selected_provider: str = RECOMMENDATION_PROVIDER_DETERMINISTIC,
    crewai_attempted: bool = False,
) -> ApprovedActionPlanResult:
    """Approve a CandidateActionPlan JSON payload or use deterministic fallback.

    The metadata wrapper is internal/runtime-only. The returned ApprovedActionPlan
    remains the renderable user-facing recommendation contract.
    """
    start_time = time.perf_counter()
    raw_diagnostics = _raw_output_diagnostics(raw_json)
    try:
        candidate = parse_candidate_action_plan(raw_json)
        violations = validate_candidate_action_plan(candidate, context)
        if violations:
            metadata = RecommendationRuntimeMetadata(
                configured_provider=configured_provider,
                selected_provider=selected_provider,
                crewai_attempted=crewai_attempted,
                fallback_used=True,
                fallback_reason=FALLBACK_REASON_VALIDATION_FAILURE,
                candidate_valid=False,
                validation_errors=violations,
                candidate_parse_status=CANDIDATE_PARSE_STATUS_SUCCESS,
                candidate_validation_status=CANDIDATE_VALIDATION_STATUS_FAILED,
                final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK,
                **raw_diagnostics,
            )
            result = _deterministic_result(context, metadata)
        else:
            metadata = RecommendationRuntimeMetadata(
                configured_provider=configured_provider,
                selected_provider=selected_provider,
                crewai_attempted=crewai_attempted,
                fallback_used=False,
                fallback_reason=None,
                candidate_valid=True,
                validation_errors=[],
                candidate_parse_status=CANDIDATE_PARSE_STATUS_SUCCESS,
                candidate_validation_status=CANDIDATE_VALIDATION_STATUS_SUCCESS,
                final_plan_source=(
                    FINAL_PLAN_SOURCE_CREWAI_APPROVED
                    if crewai_attempted
                    else FINAL_PLAN_SOURCE_DETERMINISTIC
                ),
                **raw_diagnostics,
            )
            result = ApprovedActionPlanResult(
                approved_action_plan=approve_candidate_action_plan(candidate, context),
                runtime_metadata=metadata,
            )
    except ValueError as exc:
        metadata = RecommendationRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=crewai_attempted,
            fallback_used=True,
            fallback_reason=_fallback_reason_for_parse_error(exc),
            candidate_valid=False,
            validation_errors=[str(exc)],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_FAILED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK,
            **raw_diagnostics,
        )
        result = _deterministic_result(context, metadata)

    _log_recommendation_runtime(
        context,
        result.runtime_metadata,
        elapsed_ms=round((time.perf_counter() - start_time) * 1000),
    )
    return result


def approve_candidate_json_or_fallback(
    raw_json: str,
    context: RecommendationContext,
) -> ApprovedActionPlan:
    """Approve a CandidateActionPlan JSON payload or use deterministic fallback."""
    return approve_candidate_json_or_fallback_with_metadata(
        raw_json,
        context,
    ).approved_action_plan


def approve_candidate_provider_or_fallback_with_metadata(
    candidate_provider: CandidateActionPlanProvider,
    context: RecommendationContext,
    *,
    configured_provider: str = RECOMMENDATION_PROVIDER_CREWAI,
    selected_provider: str = RECOMMENDATION_PROVIDER_CREWAI,
) -> ApprovedActionPlanResult:
    """Run a CandidateActionPlan provider behind the backend safety boundary."""
    start_time = time.perf_counter()
    try:
        raw_json = candidate_provider(context)
    except Exception as exc:
        metadata = RecommendationRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            candidate_valid=False,
            validation_errors=[type(exc).__name__],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK,
        )
        result = _deterministic_result(context, metadata)
        _log_recommendation_runtime(
            context,
            result.runtime_metadata,
            elapsed_ms=round((time.perf_counter() - start_time) * 1000),
        )
        return result

    if not isinstance(raw_json, str):
        metadata = RecommendationRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT,
            candidate_valid=False,
            validation_errors=[
                "CandidateActionPlan provider returned non-string output."
            ],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK,
        )
        result = _deterministic_result(context, metadata)
        _log_recommendation_runtime(
            context,
            result.runtime_metadata,
            elapsed_ms=round((time.perf_counter() - start_time) * 1000),
        )
        return result

    return approve_candidate_json_or_fallback_with_metadata(
        raw_json,
        context,
        configured_provider=configured_provider,
        selected_provider=selected_provider,
        crewai_attempted=True,
    )


def approve_candidate_provider_or_fallback(
    candidate_provider: CandidateActionPlanProvider,
    context: RecommendationContext,
) -> ApprovedActionPlan:
    """Run a CandidateActionPlan provider and return only the approved plan."""
    return approve_candidate_provider_or_fallback_with_metadata(
        candidate_provider,
        context,
    ).approved_action_plan


def build_crewai_approved_action_plan_with_metadata(
    health_state: UserHealthState,
) -> ApprovedActionPlanResult:
    """Build an ApprovedActionPlan through the CrewAI CandidateActionPlan path."""
    context = build_recommendation_context(health_state)
    return approve_candidate_provider_or_fallback_with_metadata(
        generate_crewai_candidate_action_plan_json,
        context,
        configured_provider=RECOMMENDATION_PROVIDER_CREWAI,
        selected_provider=RECOMMENDATION_PROVIDER_CREWAI,
    )


def build_crewai_approved_action_plan(
    health_state: UserHealthState,
) -> ApprovedActionPlan:
    """Build an ApprovedActionPlan through the CrewAI CandidateActionPlan path."""
    return build_crewai_approved_action_plan_with_metadata(
        health_state
    ).approved_action_plan


def _configured_candidate_provider() -> str:
    return (
        os.getenv(
            RECOMMENDATION_CANDIDATE_PROVIDER_ENV,
            RECOMMENDATION_PROVIDER_DETERMINISTIC,
        )
        .strip()
        .lower()
    )


def build_configured_approved_action_plan_with_metadata(
    health_state: UserHealthState,
) -> ApprovedActionPlanResult:
    """Build an ApprovedActionPlan and runtime metadata for observability."""
    context = build_recommendation_context(health_state)
    provider = _configured_candidate_provider()

    if provider == RECOMMENDATION_PROVIDER_DETERMINISTIC:
        metadata = RecommendationRuntimeMetadata(
            configured_provider=provider,
            selected_provider=RECOMMENDATION_PROVIDER_DETERMINISTIC,
            crewai_attempted=False,
            fallback_used=False,
            fallback_reason=FALLBACK_REASON_DETERMINISTIC_SELECTED,
            candidate_valid=True,
            validation_errors=[],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC,
        )
        result = _deterministic_result(context, metadata)
        _log_recommendation_runtime(context, result.runtime_metadata, elapsed_ms=0)
        return result

    if provider == RECOMMENDATION_PROVIDER_CREWAI:
        return approve_candidate_provider_or_fallback_with_metadata(
            generate_crewai_candidate_action_plan_json,
            context,
            configured_provider=provider,
            selected_provider=RECOMMENDATION_PROVIDER_CREWAI,
        )

    metadata = RecommendationRuntimeMetadata(
        configured_provider=provider,
        selected_provider=RECOMMENDATION_PROVIDER_DETERMINISTIC,
        crewai_attempted=False,
        fallback_used=True,
        fallback_reason=FALLBACK_REASON_INVALID_PROVIDER,
        candidate_valid=True,
        validation_errors=[f"Unsupported provider: {provider}"],
        candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
        candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
        final_plan_source=FINAL_PLAN_SOURCE_DETERMINISTIC_FALLBACK,
    )
    result = _deterministic_result(context, metadata)
    _log_recommendation_runtime(context, result.runtime_metadata, elapsed_ms=0)
    return result


def build_configured_approved_action_plan(
    health_state: UserHealthState,
) -> ApprovedActionPlan:
    """Build an ApprovedActionPlan using the configured runtime provider.

    Defaults to deterministic candidate generation. Invalid provider settings also
    fall back to deterministic behavior so local runtime, tests, and staging stay
    safe unless CrewAI is explicitly enabled.
    """
    return build_configured_approved_action_plan_with_metadata(
        health_state
    ).approved_action_plan


def build_approved_action_plan(
    health_state: UserHealthState,
    candidate_json: str | None = None,
    candidate_provider: CandidateActionPlanProvider | None = None,
) -> ApprovedActionPlan:
    context = build_recommendation_context(health_state)

    if candidate_json is not None:
        return approve_candidate_json_or_fallback(candidate_json, context)

    if candidate_provider is not None:
        return approve_candidate_provider_or_fallback(candidate_provider, context)

    return build_deterministic_approved_action_plan(context)
