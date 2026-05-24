import json
import os
import re
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from models.recommendation_models import (
    ApprovedActionPlan,
    CandidateActionPlan,
    RecommendationContext,
)
from models.user_state_models import UserHealthState
from services.coaching_decision_service import build_coaching_decision
from services.nutrition_target_service import build_nutrition_targets
from services.training_constraint_service import build_training_constraints

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


def build_recommendation_context(
    health_state: UserHealthState,
) -> RecommendationContext:
    coaching_decision = build_coaching_decision(health_state)
    nutrition_targets = build_nutrition_targets(health_state)
    training_constraints = build_training_constraints(health_state, coaching_decision)

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


def build_crewai_candidate_action_plan_prompt(context: RecommendationContext) -> str:
    """Return the CrewAI task prompt for CandidateActionPlan JSON generation."""
    contract = candidate_action_plan_json_contract()
    return f"""
You are generating a candidate coaching recommendation for AI Health Coach.

Return raw JSON only. Do not return markdown, headings, bullet lists, code fences,
commentary, explanations outside JSON, or extra fields.

The backend will reject malformed JSON, unsupported fields, unsafe claims, and any
recommendation that contradicts the approved context. ApprovedActionPlan remains
the only renderable recommendation contract.

RecommendationContext JSON:
{recommendation_context_to_json(context)}

CandidateActionPlan JSON contract:
{json.dumps(contract, indent=2)}

Required output:
{{
  "daily_coaching_recommendation": "one user-facing sentence",
  "workout_recommendation": "one user-facing sentence",
  "nutrition_action": "one user-facing sentence",
  "rationale": "one user-facing sentence explaining tradeoffs",
  "confidence": "Low | Moderate | High"
}}

Rules:
- Use only the RecommendationContext JSON as source context.
- Do not change or contradict the scenario.
- Do not invent calorie, protein, carbohydrate, fat, mineral, or vitamin targets.
- Do not contradict NutritionTargets approval flags or display confidence.
- Do not contradict TrainingConstraints RIR/progression/recovery guidance.
- Treat missing nutrition fields as unknown, never zero intake.
- Do not infer supplement use or over-supplementation from unusual nutrients.
- Do not make unsupported causal claims.
- Do not include internal validation, guardrail, fallback, or debug language.
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
        "invalid_output_behavior": "deterministic_fallback",
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

    if _ZERO_NUTRITION_RE.search(text):
        violations.append("Missing nutrition must not be framed as zero intake.")

    violations.extend(_validate_numeric_calorie_claims(text, context))
    violations.extend(_validate_numeric_protein_claims(text, context))
    violations.extend(_validate_numeric_carbohydrate_claims(text, context))
    violations.extend(_validate_numeric_fat_claims(text, context))

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


def approve_candidate_json_or_fallback(
    raw_json: str,
    context: RecommendationContext,
) -> ApprovedActionPlan:
    """Approve a CandidateActionPlan JSON payload or use deterministic fallback.

    This is the backend safety boundary for CrewAI output: malformed JSON,
    markdown-wrapped JSON, schema mismatch, or validation failure never becomes
    user-facing approved recommendation content.
    """
    try:
        candidate = parse_candidate_action_plan(raw_json)
        return approve_candidate_action_plan(candidate, context)
    except ValueError:
        return build_deterministic_approved_action_plan(context)


def approve_candidate_provider_or_fallback(
    candidate_provider: CandidateActionPlanProvider,
    context: RecommendationContext,
) -> ApprovedActionPlan:
    """Run a CandidateActionPlan provider behind the backend safety boundary.

    The provider may be CrewAI or a fake provider in tests. Provider exceptions,
    non-string output, malformed JSON, schema mismatch, and validation failures
    all fall back to deterministic approved recommendations.
    """
    try:
        raw_json = candidate_provider(context)
    except Exception:
        return build_deterministic_approved_action_plan(context)

    if not isinstance(raw_json, str):
        return build_deterministic_approved_action_plan(context)

    return approve_candidate_json_or_fallback(raw_json, context)


def build_crewai_approved_action_plan(
    health_state: UserHealthState,
) -> ApprovedActionPlan:
    """Build an ApprovedActionPlan through the CrewAI CandidateActionPlan path.

    CrewAI output is never trusted directly. It must pass the same parse, schema,
    scenario, target, and safety validation as any other candidate JSON.
    """
    context = build_recommendation_context(health_state)
    return approve_candidate_provider_or_fallback(
        generate_crewai_candidate_action_plan_json,
        context,
    )


def _configured_candidate_provider() -> str:
    return (
        os.getenv(
            RECOMMENDATION_CANDIDATE_PROVIDER_ENV,
            RECOMMENDATION_PROVIDER_DETERMINISTIC,
        )
        .strip()
        .lower()
    )


def build_configured_approved_action_plan(
    health_state: UserHealthState,
) -> ApprovedActionPlan:
    """Build an ApprovedActionPlan using the configured runtime provider.

    Defaults to deterministic candidate generation. Invalid provider settings also
    fall back to deterministic behavior so local runtime, tests, and staging stay
    safe unless CrewAI is explicitly enabled.
    """
    provider = _configured_candidate_provider()

    if provider == RECOMMENDATION_PROVIDER_CREWAI:
        return build_crewai_approved_action_plan(health_state)

    return build_approved_action_plan(health_state)


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
