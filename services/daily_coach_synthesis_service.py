from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from models.daily_coach_synthesis_models import DailyCoachSynthesis
from models.nutrition_food_suggestion_models import (
    ApprovedNutritionFoodSuggestions,
)
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    TARGET_STATUS_BELOW,
    TARGET_STATUS_NEAR,
    ApprovedNutritionGuidance,
    TargetVsActualNutritionSummary,
)
from models.recommendation_models import ApprovedActionPlan, RecommendationContext
from models.training_constraint_models import TrainingConstraints
from models.training_execution_summary_models import TrainingExecutionSummary
from models.user_state_models import UserHealthState
from models.workout_plan_models import (
    ApprovedPostWorkoutReviewSummary,
    ApprovedWorkoutExplanation,
    ApprovedWorkoutPlan,
    WorkoutPlannedVsActualSummary,
)
from services.nutrition_food_suggestion_service import (
    build_approved_nutrition_food_suggestions,
)
from services.nutrition_target_calibration_service import (
    NutritionTargetCalibrationResult,
    build_nutrition_target_calibration_result,
)
from services.nutrition_target_vs_actual_service import (
    build_approved_nutrition_guidance,
    build_target_vs_actual_nutrition_summary,
    validate_target_vs_actual_nutrition_summary,
)
from services.post_workout_review_service import (
    build_deterministic_post_workout_review_summary,
    build_post_workout_review_context,
)
from services.recommendation_engine_service import (
    build_deterministic_approved_action_plan,
    build_recommendation_context,
)
from services.user_state_service import build_user_health_state
from services.workout_plan_persistence_service import get_workout_plan_history
from services.workout_plan_service import (
    build_approved_workout_plan,
    build_deterministic_workout_explanation,
    build_workout_context,
)

_DAILY_COACH_STRING_FIELDS = [
    "today_summary",
    "recovery_signal",
    "training_signal",
    "workout_guidance",
    "execution_context",
    "logging_focus",
    "plan_fit_note",
    "recommended_focus",
]

_FORBIDDEN_DAILY_COACH_TERMS = [
    "overtraining",
    "stalled progress",
    "poor adherence",
    "lack of discipline",
    "failed programming",
    "automatic deload",
    "automatic load increase",
    "automatic progression",
    "medical claim",
    "medical diagnosis",
    "injury claim",
    "injury diagnosis",
    "you failed",
    "you did not adhere",
    "your discipline",
    "this proves",
    "this means you should increase",
    "increase load next time",
    "add weight next session",
    "deload this week",
    "cut volume",
    "training is causing",
    "nutrition is inadequate",
    "you must cut calories",
    "must cut calories",
    "skip meals",
    "compensate tomorrow",
    "burn this off",
    "bad food",
    "good food",
    "eating disorder",
    "supplement",
    "stalled fat loss",
    "stalled weight loss",
    "skipped work shows discipline",
    "skipped work means discipline",
]

_ONE_WORKOUT_TREND_TERMS = [
    "trend",
    "trends",
    "pattern",
    "patterns",
    "consistently",
    "repeated",
    "repeatedly",
    "recent completed workouts",
]

_LOW_CONFIDENCE_STRONG_TERMS = [
    "clearly",
    "definitely",
    "shows that",
    "must",
    "should increase",
    "should add",
    "should deload",
    "strong trend",
]

_DATA_QUALITY_CAUSAL_TERMS = [
    "adequate nutrition",
    "nutrition is adequate",
    "nutrition is inadequate",
    "intake is inadequate",
    "stalled progress",
    "stalled weight loss",
    "stalled fat loss",
    "likely caused",
    "likely causing",
    "likely contribute",
    "likely contributes",
    "supplement",
    "supplementation",
    "overtraining",
]

_WORKOUT_STRUCTURE_CHANGE_TERMS = [
    "change the approved workout",
    "change exercises",
    "add exercises",
    "remove exercises",
    "add sets",
    "reduce sets",
    "increase reps",
    "change reps",
    "change rir",
    "increase the rir target",
    "decrease the rir target",
]

_NUTRITION_TARGET_LANGUAGE_TERMS = [
    "calorie target",
    "calorie targets",
    "kcal target",
    "macro target",
    "macro targets",
    "carb target",
    "fat target",
    "protein target",
]

_FOOD_SUGGESTION_INTERNAL_TERMS = [
    "canonical_food_id",
    "suggested_grams",
    "estimated_calories",
    "estimated_protein_g",
    "estimated_carbohydrate_g",
    "estimated_fat_g",
    "raw food suggestion",
]

_CALIBRATION_INTERNAL_TERMS = [
    "calibrated_targets",
    "true maintenance is exactly",
    "calibration has been applied",
    "calibration was applied",
    "targets have been calibrated",
    "calibrated targets are active",
    "your targets were updated",
    "your targets have changed",
    "targets have been changed",
    "metabolism is damaged",
    "exact maintenance",
    "active calibrated target",
]

_FOOD_SUGGESTION_GAP_LABELS = {
    "protein_g": "protein",
    "carbohydrate_g": "carbohydrate",
    "calories": "calorie-support",
    "fat_g": "fat-support",
}


@dataclass(frozen=True)
class _DailyCoachFoodSuggestionContext:
    has_approved_suggestions: bool
    confidence: str
    primary_gap: str | None
    focus_text: str | None
    limitation_text: str | None
    reason_codes: list[str]
    limitations: list[str]


@dataclass(frozen=True)
class _DailyCoachNutritionCalibrationContext:
    confidence: str
    readiness_level: str
    recommended_action: str
    focus_text: str | None
    limitation_text: str | None
    reason_codes: list[str]
    limitations: list[str]


class DailyCoachSynthesisValidationError(ValueError):
    """Raised when deterministic daily coach synthesis violates the contract."""


def build_daily_coach_synthesis(user_id: int) -> DailyCoachSynthesis:
    """Build a deterministic, read-only daily coaching synthesis.

    This service composes approved backend signals into a public-safe summary. It
    does not make new programming, progression, deload, nutrition-target, or
    medical decisions.
    """

    health_state = build_user_health_state(user_id)
    recommendation_context = build_recommendation_context(health_state)
    approved_action_plan = build_deterministic_approved_action_plan(
        recommendation_context
    )
    approved_workout_plan = build_approved_workout_plan(health_state)
    workout_context = build_workout_context(health_state)
    approved_workout_explanation = build_deterministic_workout_explanation(
        approved_workout_plan,
        workout_context,
    )
    latest_review, latest_summary = _latest_completed_post_workout_context(user_id)
    nutrition_summary, approved_nutrition_guidance = _approved_nutrition_context(
        user_id
    )
    suggestion_date = date.today().isoformat()
    approved_food_suggestions = _approved_food_suggestion_context(
        user_id,
        suggestion_date=suggestion_date,
        nutrition_summary=nutrition_summary,
    )
    nutrition_calibration_result = _approved_nutrition_calibration_context(
        user_id,
        calibration_date=suggestion_date,
    )

    synthesis = build_daily_coach_synthesis_from_components(
        health_state=health_state,
        recommendation_context=recommendation_context,
        approved_action_plan=approved_action_plan,
        approved_workout_plan=approved_workout_plan,
        approved_workout_explanation=approved_workout_explanation,
        training_execution_summary=recommendation_context.training_execution_summary,
        latest_post_workout_review=latest_review,
        latest_planned_vs_actual_summary=latest_summary,
        nutrition_target_vs_actual_summary=nutrition_summary,
        approved_nutrition_guidance=approved_nutrition_guidance,
        approved_food_suggestions=approved_food_suggestions,
        nutrition_calibration_result=nutrition_calibration_result,
        synthesis_date=suggestion_date,
    )

    violations = validate_daily_coach_synthesis(
        synthesis,
        recommendation_context=recommendation_context,
        approved_action_plan=approved_action_plan,
        approved_workout_plan=approved_workout_plan,
        training_execution_summary=recommendation_context.training_execution_summary,
        nutrition_target_vs_actual_summary=nutrition_summary,
        approved_nutrition_guidance=approved_nutrition_guidance,
    )
    if violations:
        raise DailyCoachSynthesisValidationError("; ".join(violations))

    return synthesis


def build_daily_coach_synthesis_from_components(
    *,
    health_state: UserHealthState,
    recommendation_context: RecommendationContext,
    approved_action_plan: ApprovedActionPlan,
    approved_workout_plan: ApprovedWorkoutPlan,
    approved_workout_explanation: ApprovedWorkoutExplanation,
    training_execution_summary: TrainingExecutionSummary | None,
    latest_post_workout_review: ApprovedPostWorkoutReviewSummary | None = None,
    latest_planned_vs_actual_summary: WorkoutPlannedVsActualSummary | None = None,
    nutrition_target_vs_actual_summary: TargetVsActualNutritionSummary | None = None,
    approved_nutrition_guidance: ApprovedNutritionGuidance | None = None,
    approved_food_suggestions: ApprovedNutritionFoodSuggestions | None = None,
    nutrition_calibration_result: NutritionTargetCalibrationResult | None = None,
    synthesis_date: str | None = None,
) -> DailyCoachSynthesis:
    training_summary = training_execution_summary
    food_suggestion_context = _food_suggestion_context(approved_food_suggestions)
    nutrition_calibration_context = _nutrition_calibration_context(
        nutrition_calibration_result
    )
    limitations = _build_limitations(
        health_state,
        recommendation_context,
        training_summary,
        nutrition_target_vs_actual_summary,
        food_suggestion_context,
        nutrition_calibration_context,
    )
    reason_codes = _build_reason_codes(
        recommendation_context,
        approved_action_plan,
        approved_workout_plan,
        training_summary,
        latest_post_workout_review,
        latest_planned_vs_actual_summary,
        nutrition_target_vs_actual_summary,
        approved_nutrition_guidance,
        food_suggestion_context,
        nutrition_calibration_context,
        limitations,
    )

    return DailyCoachSynthesis(
        user_id=health_state.user_id,
        synthesis_date=synthesis_date or date.today().isoformat(),
        scenario=recommendation_context.scenario,
        confidence=_bounded_confidence(
            recommendation_context.confidence,
            approved_action_plan.confidence,
            approved_workout_plan.confidence,
        ),
        today_summary=_today_summary(
            recommendation_context,
            approved_action_plan,
            nutrition_target_vs_actual_summary,
            food_suggestion_context,
            nutrition_calibration_context,
        ),
        recovery_signal=_recovery_signal(health_state, recommendation_context),
        training_signal=_training_signal(
            health_state,
            approved_action_plan,
            recommendation_context,
            nutrition_target_vs_actual_summary,
            approved_nutrition_guidance,
        ),
        workout_guidance=_workout_guidance(
            approved_workout_plan,
            approved_workout_explanation,
            recommendation_context.training_constraints,
        ),
        execution_context=_execution_context(training_summary),
        logging_focus=_logging_focus(
            health_state,
            training_summary,
            latest_post_workout_review,
            nutrition_target_vs_actual_summary,
            approved_nutrition_guidance,
            food_suggestion_context,
            nutrition_calibration_context,
        ),
        plan_fit_note=_plan_fit_note(training_summary, latest_post_workout_review),
        recommended_focus=_recommended_focus(
            recommendation_context,
            approved_action_plan,
            nutrition_target_vs_actual_summary,
            approved_nutrition_guidance,
            food_suggestion_context,
            nutrition_calibration_context,
        ),
        reason_codes=reason_codes,
        limitations=limitations,
    )


def validate_daily_coach_synthesis(
    synthesis: DailyCoachSynthesis,
    *,
    recommendation_context: RecommendationContext | None = None,
    approved_action_plan: ApprovedActionPlan | None = None,
    approved_workout_plan: ApprovedWorkoutPlan | None = None,
    training_execution_summary: TrainingExecutionSummary | None = None,
    nutrition_target_vs_actual_summary: TargetVsActualNutritionSummary | None = None,
    approved_nutrition_guidance: ApprovedNutritionGuidance | None = None,
) -> list[str]:
    violations: list[str] = []

    for field_name in _DAILY_COACH_STRING_FIELDS:
        value = getattr(synthesis, field_name, "")
        if not isinstance(value, str) or not value.strip():
            violations.append(f"DailyCoachSynthesis.{field_name} is required.")
        elif len(value) > 320:
            violations.append(f"DailyCoachSynthesis.{field_name} should stay concise.")

    all_text = _synthesis_text(synthesis)
    all_text_lower = all_text.lower()

    for term in _FORBIDDEN_DAILY_COACH_TERMS:
        if term in all_text_lower:
            violations.append(f"DailyCoachSynthesis must not include: {term}")

    for term in _FOOD_SUGGESTION_INTERNAL_TERMS:
        if term in all_text_lower:
            violations.append(
                f"DailyCoachSynthesis must not expose food suggestion internals: {term}"
            )

    for term in _CALIBRATION_INTERNAL_TERMS:
        if term in all_text_lower:
            violations.append(
                f"DailyCoachSynthesis must not expose calibration internals or certainty claims: {term}"
            )

    summary = training_execution_summary
    if summary is None and recommendation_context is not None:
        summary = recommendation_context.training_execution_summary

    if summary is not None and summary.completed_execution_count <= 1:
        for term in _ONE_WORKOUT_TREND_TERMS:
            if term in synthesis.execution_context.lower():
                violations.append(
                    "DailyCoachSynthesis must not make trend claims from zero or one completed planned workout."
                )
                break

    if synthesis.confidence in {"Limited", "Low"}:
        for term in _LOW_CONFIDENCE_STRONG_TERMS:
            if term in all_text_lower:
                violations.append(
                    "Low/Limited confidence DailyCoachSynthesis must remain soft and contextual."
                )
                break

    if synthesis.scenario == "data_quality_limited":
        for term in _DATA_QUALITY_CAUSAL_TERMS:
            if term in all_text_lower:
                violations.append(
                    f"Data-quality-limited synthesis must not include strong causal or adequacy claim: {term}"
                )

    workout_guidance_lower = synthesis.workout_guidance.lower()
    for term in _WORKOUT_STRUCTURE_CHANGE_TERMS:
        if term in workout_guidance_lower:
            violations.append(
                "DailyCoachSynthesis workout guidance must not alter approved workout structure."
            )
            break

    if recommendation_context is not None:
        nutrition_targets = recommendation_context.nutrition_targets
        nutrition_text = " ".join(
            [
                synthesis.today_summary,
                synthesis.logging_focus,
                synthesis.recommended_focus,
            ]
        ).lower()
        if nutrition_targets.confidence == "Limited":
            for term in _NUTRITION_TARGET_LANGUAGE_TERMS:
                if term in nutrition_text:
                    violations.append(
                        "Limited-confidence nutrition synthesis must not expose target language."
                    )
                    break

        if not nutrition_targets.allow_calorie_targets and (
            "calorie target" in nutrition_text or "kcal target" in nutrition_text
        ):
            violations.append(
                "DailyCoachSynthesis must not mention calorie targets when they are not approved."
            )

    if nutrition_target_vs_actual_summary is not None:
        nutrition_violations = _validate_nutrition_synthesis_claims(
            synthesis,
            nutrition_target_vs_actual_summary,
            approved_nutrition_guidance,
        )
        violations.extend(nutrition_violations)

    if approved_workout_plan is not None:
        workout_text = synthesis.workout_guidance.lower()
        for exercise in approved_workout_plan.exercises:
            if exercise.name.lower() in workout_text:
                continue
        if "as written" not in workout_text and "approved plan" not in workout_text:
            violations.append(
                "DailyCoachSynthesis workout guidance should anchor to the approved workout plan."
            )

    if any("raw" in code.lower() for code in synthesis.reason_codes):
        violations.append(
            "Reason codes must be backend-safe and not expose raw payloads."
        )

    return violations


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _approved_nutrition_context(
    user_id: int,
) -> tuple[TargetVsActualNutritionSummary | None, ApprovedNutritionGuidance | None]:
    try:
        summary = build_target_vs_actual_nutrition_summary(
            user_id, date.today().isoformat()
        )
        guidance = build_approved_nutrition_guidance(summary)
        violations = validate_target_vs_actual_nutrition_summary(summary, guidance)
    except Exception:
        return None, None

    if violations:
        return None, None

    return summary, guidance


def _approved_food_suggestion_context(
    user_id: int,
    *,
    suggestion_date: str,
    nutrition_summary: TargetVsActualNutritionSummary | None,
) -> ApprovedNutritionFoodSuggestions | None:
    if nutrition_summary is None:
        return None
    try:
        return build_approved_nutrition_food_suggestions(
            user_id,
            suggestion_date,
            target_vs_actual_summary=nutrition_summary,
            limit=3,
        )
    except Exception:
        return None


def _approved_nutrition_calibration_context(
    user_id: int,
    *,
    calibration_date: str,
) -> NutritionTargetCalibrationResult | None:
    try:
        return build_nutrition_target_calibration_result(
            user_id,
            calibration_date=calibration_date,
            window_days=28,
        )
    except Exception:
        return None


def _latest_completed_post_workout_context(
    user_id: int,
) -> tuple[
    ApprovedPostWorkoutReviewSummary | None, WorkoutPlannedVsActualSummary | None
]:
    try:
        history_items = get_workout_plan_history(user_id)
    except Exception:
        return None, None

    for item in history_items:
        instance = item.get("workout_plan_instance")
        execution_session = item.get("execution_session")
        if instance is None or execution_session is None:
            continue
        if getattr(instance, "status", None) != "completed":
            continue
        if getattr(execution_session, "status", None) != "completed":
            continue
        try:
            review_context = build_post_workout_review_context(execution_session.id)
            return (
                build_deterministic_post_workout_review_summary(review_context),
                review_context.planned_vs_actual_summary,
            )
        except Exception:
            return None, item.get("planned_vs_actual_summary")

    return None, None


def _food_suggestion_context(
    suggestions: ApprovedNutritionFoodSuggestions | None,
) -> _DailyCoachFoodSuggestionContext | None:
    if suggestions is None:
        return None

    reason_codes = list(suggestions.reason_codes)
    limitations = list(suggestions.limitations)

    if suggestions.suggestions and suggestions.confidence in {"Moderate", "High"}:
        primary_gap = suggestions.primary_gap
        gap_label = _FOOD_SUGGESTION_GAP_LABELS.get(primary_gap or "", "macro")
        if primary_gap == "protein_g":
            focus_text = (
                "Protein is below target based on logged meals, and the Nutrition tab "
                "has approved protein-focused food options."
            )
        elif primary_gap == "carbohydrate_g":
            focus_text = (
                "Carbohydrate suggestions are available in the Nutrition tab because "
                "logged carbs are below target and calorie context allows comparison."
            )
        elif primary_gap == "calories":
            focus_text = (
                "The Nutrition tab has approved calorie-support food options based on "
                "today's logged macro gaps."
            )
        elif primary_gap == "fat_g":
            focus_text = (
                "The Nutrition tab has approved fat-support food options based on "
                "today's logged macro gaps."
            )
        else:
            focus_text = (
                "The Nutrition tab has approved food suggestions based on today's "
                "logged macro gaps."
            )
        reason_codes.extend(
            [
                "nutrition_food_suggestions_context_available",
                f"nutrition_food_suggestions_{gap_label.replace('-', '_')}_available",
            ]
        )
        return _DailyCoachFoodSuggestionContext(
            has_approved_suggestions=True,
            confidence=suggestions.confidence,
            primary_gap=primary_gap,
            focus_text=focus_text,
            limitation_text=None,
            reason_codes=_unique(reason_codes),
            limitations=_unique(limitations),
        )

    limitation_text = _food_suggestion_limitation_text(suggestions)
    if limitation_text:
        limitations.append(limitation_text)
    reason_codes.append("nutrition_food_suggestions_context_limited")
    return _DailyCoachFoodSuggestionContext(
        has_approved_suggestions=False,
        confidence=suggestions.confidence,
        primary_gap=suggestions.primary_gap,
        focus_text=None,
        limitation_text=limitation_text,
        reason_codes=_unique(reason_codes),
        limitations=_unique(limitations),
    )


def _food_suggestion_limitation_text(
    suggestions: ApprovedNutritionFoodSuggestions,
) -> str | None:
    reason_codes = set(suggestions.reason_codes)
    limitation_text = " ".join(suggestions.limitations).lower()

    if "logging_incomplete_limits_suggestions" in reason_codes or (
        "logging" in limitation_text and "incomplete" in limitation_text
    ):
        return "Food suggestions are limited because logging is incomplete."

    if "no_supported_suggestion_gap_available" in reason_codes:
        return (
            "No food suggestions are available yet because no approved supported "
            "gap is available."
        )

    if "no_macro_gap_detected" in reason_codes:
        return "No food suggestions are available yet because no approved macro gap is available."

    if "target_not_approved" in reason_codes:
        return "Food suggestions are limited because the needed nutrition target is not approved."

    if suggestions.confidence in {"Limited", "Low"}:
        return (
            "Food suggestions are limited by the available logging and target context."
        )

    return None


def _nutrition_calibration_context(
    result: NutritionTargetCalibrationResult | None,
) -> _DailyCoachNutritionCalibrationContext | None:
    if result is None:
        return None

    reason_codes = _unique(
        list(result.reason_codes)
        + [
            "nutrition_calibration_context_available",
            f"nutrition_calibration_readiness_{result.readiness_level}",
            f"nutrition_calibration_action_{result.recommended_action}",
        ]
    )
    limitations = list(result.limitations)
    focus_text, limitation_text = _nutrition_calibration_context_text(result)

    if limitation_text:
        limitations.append(limitation_text)
        reason_codes.append("nutrition_calibration_context_limited")
    else:
        reason_codes.append("nutrition_calibration_context_summarized")

    return _DailyCoachNutritionCalibrationContext(
        confidence=result.confidence,
        readiness_level=result.readiness_level,
        recommended_action=result.recommended_action,
        focus_text=focus_text,
        limitation_text=limitation_text,
        reason_codes=_unique(reason_codes),
        limitations=_unique(limitations),
    )


def _nutrition_calibration_context_text(
    result: NutritionTargetCalibrationResult,
) -> tuple[str | None, str | None]:
    readiness = result.readiness_level
    action = result.recommended_action

    if action == "insufficient_data" or readiness == "not_ready":
        return (
            None,
            "Calibration is not ready yet because more consistent logs or weigh-ins are needed.",
        )

    if readiness == "early_signal":
        return (
            None,
            "Early trend evidence is available, but more data is needed before target calibration can be trusted.",
        )

    if action == "keep_current_targets":
        return (
            "Current evidence supports keeping formula-derived targets unchanged.",
            None,
        )

    if action == "maintain_broad_range":
        return (
            None,
            "Formula-derived targets remain broad because uncertainty still exists.",
        )

    if action == "eligible_for_future_refinement":
        return (
            "This trend window may support future target refinement, but targets are still formula-derived for now.",
            None,
        )

    if readiness in {"usable", "strong"}:
        return (
            "Nutrition trend evidence is improving, but targets are still formula-derived for now.",
            None,
        )

    if result.confidence in {"Limited", "Low"}:
        return (
            None,
            "Nutrition calibration context is limited by the available trend evidence.",
        )

    return None, None


def _today_summary(
    context: RecommendationContext,
    plan: ApprovedActionPlan,
    nutrition_summary: TargetVsActualNutritionSummary | None,
    food_suggestion_context: _DailyCoachFoodSuggestionContext | None,
    nutrition_calibration_context: _DailyCoachNutritionCalibrationContext | None,
) -> str:
    if context.scenario == "recovery_limited":
        return "Today is best treated as a controlled training day with recovery signals kept in view."
    if context.scenario == "nutrition_training_mismatch":
        if _nutrition_logging_is_limited(nutrition_summary):
            return "Today should connect training demand with nutrition logging context while keeping conclusions limited."
        return "Today should connect training demand with approved nutrition context without making hard target changes."
    if context.scenario == "improving_after_deload":
        return "Today supports controlled training while the recent improvement trend continues to stabilize."
    if context.scenario == "data_quality_limited":
        return "Today should stay simple and focused on better logging because data quality limits stronger conclusions."
    if (
        nutrition_calibration_context is not None
        and nutrition_calibration_context.focus_text
        and nutrition_calibration_context.readiness_level in {"usable", "strong"}
    ):
        return "Nutrition trend evidence is improving, while today's coaching still uses formula-derived targets."
    return plan.daily_coaching_recommendation


def _recovery_signal(
    health_state: UserHealthState,
    context: RecommendationContext,
) -> str:
    recovery = health_state.recovery_state
    if not _has_recovery_checkin_data(health_state):
        return "Recovery check-in data is limited today, so the synthesis should stay cautious until sleep, energy, and soreness are updated."

    readiness = str(recovery.readiness_level).replace("_", " ").lower()
    fatigue = str(recovery.fatigue_risk).replace("_", " ").lower()
    if context.scenario == "recovery_limited":
        return (
            "Recovery signals point toward controlled effort and careful RIR use today."
        )
    return f"Recovery readiness is {readiness}, with fatigue risk currently {fatigue}."


def _training_signal(
    health_state: UserHealthState,
    plan: ApprovedActionPlan,
    context: RecommendationContext,
    nutrition_summary: TargetVsActualNutritionSummary | None,
    nutrition_guidance: ApprovedNutritionGuidance | None,
) -> str:
    training = health_state.training_state
    if not training.has_workout_data:
        return "Training history is limited, so today should emphasize clear logging and a manageable baseline."

    if context.scenario == "nutrition_training_mismatch":
        nutrition_text = _nutrition_training_signal(
            nutrition_summary, nutrition_guidance
        )
        if nutrition_text:
            return nutrition_text

    return plan.workout_recommendation


def _workout_guidance(
    plan: ApprovedWorkoutPlan,
    explanation: ApprovedWorkoutExplanation,
    constraints: TrainingConstraints,
) -> str:
    rir_text = _rir_target_text(constraints)
    return (
        f"Use the approved plan as written: {plan.title}. {rir_text} "
        f"{explanation.focus_cue}"
    )


def _execution_context(summary: TrainingExecutionSummary | None) -> str:
    if summary is None or summary.completed_execution_count == 0:
        return "No completed planned workouts are available yet, so execution history will not drive today's coaching."

    if summary.completed_execution_count == 1:
        return "One completed planned workout is available, so treat it as context only rather than a broader signal."

    if summary.incomplete_logging_count:
        return "Incomplete actual-set logging limits how much the system should infer from recent workouts."

    if summary.confidence in {"Limited", "Low"}:
        return "Recent planned-workout context is available, but logging limits how much the system should infer."

    if summary.execution_effort_trend == "harder_than_planned":
        return "Recent completed workouts show effort has been a little harder than planned, so use the RIR target as today's anchor."

    if summary.execution_effort_trend == "easier_than_planned":
        return "Recent completed workouts have been a little easier than planned; keep logging effort before making stronger changes."

    if summary.execution_quality in {"mostly_completed", "consistently_completed"}:
        return "Recent completed workouts were generally close to the plan."

    return "Recent completed workout data is useful context, but it should stay descriptive for now."


def _logging_focus(
    health_state: UserHealthState,
    summary: TrainingExecutionSummary | None,
    latest_review: ApprovedPostWorkoutReviewSummary | None,
    nutrition_summary: TargetVsActualNutritionSummary | None,
    nutrition_guidance: ApprovedNutritionGuidance | None,
    food_suggestion_context: _DailyCoachFoodSuggestionContext | None,
    nutrition_calibration_context: _DailyCoachNutritionCalibrationContext | None,
) -> str:
    if _nutrition_no_logs(nutrition_summary):
        return "No nutrition logs are available for today yet, so logging meals will make nutrition guidance more useful."

    if _nutrition_logging_is_limited(nutrition_summary):
        return _nutrition_logging_focus(nutrition_summary, nutrition_guidance)

    if (
        food_suggestion_context is not None
        and food_suggestion_context.limitation_text
        and food_suggestion_context.confidence in {"Limited", "Low"}
    ):
        return food_suggestion_context.limitation_text

    if (
        nutrition_calibration_context is not None
        and nutrition_calibration_context.limitation_text
        and nutrition_calibration_context.confidence in {"Limited", "Low"}
    ):
        return nutrition_calibration_context.limitation_text

    if not _has_recovery_checkin_data(health_state):
        return "Complete today's recovery check-in so sleep, energy, and soreness can improve the recommendation."

    if summary is not None and (
        summary.incomplete_logging_count
        or summary.missing_actual_reps_count
        or summary.missing_actual_rir_count
    ):
        return "Keep reps, weight, and RIR logging complete so planned-vs-actual reviews stay useful."

    if latest_review is not None:
        return latest_review.logging_quality_note

    return "Keep recovery, nutrition, and set-level workout logging consistent today."


def _plan_fit_note(
    summary: TrainingExecutionSummary | None,
    latest_review: ApprovedPostWorkoutReviewSummary | None,
) -> str:
    if summary is not None and (
        summary.skipped_exercise_count or summary.substituted_exercise_count
    ):
        return "Recent substitutions or skipped items are useful context for reviewing plan fit or equipment fit."

    if latest_review is not None:
        return latest_review.substitutions_or_skips_context

    return (
        "No recent plan-fit concerns are strong enough to change today's approved plan."
    )


def _recommended_focus(
    context: RecommendationContext,
    plan: ApprovedActionPlan,
    nutrition_summary: TargetVsActualNutritionSummary | None,
    nutrition_guidance: ApprovedNutritionGuidance | None,
    food_suggestion_context: _DailyCoachFoodSuggestionContext | None,
    nutrition_calibration_context: _DailyCoachNutritionCalibrationContext | None,
) -> str:
    if food_suggestion_context is not None:
        if food_suggestion_context.focus_text:
            return food_suggestion_context.focus_text
        if food_suggestion_context.limitation_text:
            return food_suggestion_context.limitation_text

    if nutrition_calibration_context is not None:
        if nutrition_calibration_context.focus_text:
            return nutrition_calibration_context.focus_text
        if nutrition_calibration_context.limitation_text:
            return nutrition_calibration_context.limitation_text

    nutrition_focus = _nutrition_recommended_focus(
        nutrition_summary, nutrition_guidance
    )
    if nutrition_focus:
        return nutrition_focus

    if context.scenario == "recovery_limited":
        return "Anchor today on controlled effort, recovery check-in quality, and staying within the approved RIR range."
    if context.scenario == "nutrition_training_mismatch":
        return "Train within the approved plan and keep nutrition logging complete enough to compare support with demand."
    if context.scenario == "improving_after_deload":
        return "Use controlled training and clear logging while recovery continues to stabilize."
    if context.scenario == "data_quality_limited":
        return "Prioritize logging completeness and a manageable workout before drawing stronger nutrition or training conclusions."
    return plan.rationale


def _build_limitations(
    health_state: UserHealthState,
    context: RecommendationContext,
    summary: TrainingExecutionSummary | None,
    nutrition_summary: TargetVsActualNutritionSummary | None,
    food_suggestion_context: _DailyCoachFoodSuggestionContext | None,
    nutrition_calibration_context: _DailyCoachNutritionCalibrationContext | None,
) -> list[str]:
    limitations: list[str] = []

    if not _has_recovery_checkin_data(health_state):
        limitations.append("recovery_checkin_missing_or_limited")
    if summary is None or summary.completed_execution_count == 0:
        limitations.append("no_completed_planned_workout_execution_data")
    elif summary.completed_execution_count == 1:
        limitations.append("single_completed_planned_workout_no_trend_claims")
    if summary is not None and summary.incomplete_logging_count:
        limitations.append("incomplete_actual_set_logging_limits_inference")
    if context.confidence in {"Limited", "Low"}:
        limitations.append("low_confidence_context_requires_soft_language")
    if context.nutrition_targets.confidence == "Limited":
        limitations.append("nutrition_targets_limited_by_logging_quality")

    limitations.extend(_nutrition_limitations(nutrition_summary))
    if food_suggestion_context is not None:
        limitations.extend(food_suggestion_context.limitations)
    if nutrition_calibration_context is not None:
        limitations.extend(nutrition_calibration_context.limitations)

    return list(dict.fromkeys(limitations))


def _build_reason_codes(
    context: RecommendationContext,
    plan: ApprovedActionPlan,
    workout_plan: ApprovedWorkoutPlan,
    summary: TrainingExecutionSummary | None,
    latest_review: ApprovedPostWorkoutReviewSummary | None,
    latest_planned_vs_actual_summary: WorkoutPlannedVsActualSummary | None,
    nutrition_summary: TargetVsActualNutritionSummary | None,
    nutrition_guidance: ApprovedNutritionGuidance | None,
    food_suggestion_context: _DailyCoachFoodSuggestionContext | None,
    nutrition_calibration_context: _DailyCoachNutritionCalibrationContext | None,
    limitations: list[str],
) -> list[str]:
    reason_codes = [
        "daily_coach_synthesis_deterministic_v1",
        "approved_action_plan_used",
        "approved_workout_plan_used",
    ]
    reason_codes.extend(context.reason_codes)
    reason_codes.extend(plan.reason_codes)
    reason_codes.extend(workout_plan.reason_codes)
    if summary is not None:
        reason_codes.extend(summary.reason_codes)
        reason_codes.append("training_execution_summary_used")
    if latest_review is not None:
        reason_codes.append("latest_post_workout_review_used")
    if latest_planned_vs_actual_summary is not None:
        reason_codes.append("latest_planned_vs_actual_summary_available")
    reason_codes.extend(_nutrition_reason_codes(nutrition_summary, nutrition_guidance))
    if food_suggestion_context is not None:
        reason_codes.extend(food_suggestion_context.reason_codes)
    if nutrition_calibration_context is not None:
        reason_codes.extend(nutrition_calibration_context.reason_codes)
    reason_codes.extend(limitations)
    return list(dict.fromkeys(code for code in reason_codes if code))


def _nutrition_no_logs(summary: TargetVsActualNutritionSummary | None) -> bool:
    return bool(
        summary and summary.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS
    )


def _nutrition_logging_is_limited(
    summary: TargetVsActualNutritionSummary | None,
) -> bool:
    return bool(
        summary
        and summary.logging_completeness
        in {
            LOGGING_COMPLETENESS_NO_LOGS,
            LOGGING_COMPLETENESS_PARTIAL_DAY,
            LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
        }
    )


def _protein_comparison(summary: TargetVsActualNutritionSummary | None):
    if summary is None:
        return None
    return summary.comparisons.get("protein")


def _calorie_comparison(summary: TargetVsActualNutritionSummary | None):
    if summary is None:
        return None
    return summary.comparisons.get("calories")


def _macro_comparisons_are_available(
    summary: TargetVsActualNutritionSummary | None,
) -> bool:
    if summary is None:
        return False
    carb = summary.comparisons.get("carbs")
    fat = summary.comparisons.get("fat")
    return bool(carb and fat and carb.comparison_available and fat.comparison_available)


def _nutrition_training_signal(
    summary: TargetVsActualNutritionSummary | None,
    guidance: ApprovedNutritionGuidance | None,
) -> str | None:
    if summary is None or guidance is None:
        return None
    if _nutrition_logging_is_limited(summary):
        return "Nutrition logging is incomplete today, so nutrition conclusions should stay limited while training stays controlled."

    protein = _protein_comparison(summary)
    if protein and protein.comparison_available:
        if protein.target_status == TARGET_STATUS_BELOW:
            return "Based on logged meals, protein is below today's target; keep training controlled and consider a protein-centered meal."
        if protein.target_status == TARGET_STATUS_NEAR:
            return "Protein is close to target based on current logs, which gives useful support context for today's training."

    return None


def _nutrition_logging_focus(
    summary: TargetVsActualNutritionSummary | None,
    guidance: ApprovedNutritionGuidance | None,
) -> str:
    if summary is None or guidance is None:
        return "Keep nutrition logging complete so nutrition guidance stays useful."
    if summary.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS:
        return "No nutrition logs are available for today yet, so logging meals will make nutrition guidance more useful."
    if summary.logging_completeness in {
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    }:
        return "Nutrition logging is incomplete today, so calorie conclusions and macro conclusions should stay limited."
    return guidance.logging_guidance


def _nutrition_recommended_focus(
    summary: TargetVsActualNutritionSummary | None,
    guidance: ApprovedNutritionGuidance | None,
) -> str | None:
    if summary is None or guidance is None:
        return None

    protein = _protein_comparison(summary)
    if protein and protein.comparison_available:
        if protein.target_status == TARGET_STATUS_BELOW:
            return "A protein-centered meal may help support today's training while keeping conclusions based on logged meals."
        if protein.target_status == TARGET_STATUS_NEAR:
            return "Protein is close to target based on current logs; keep meals and training well logged today."

    if _macro_comparisons_are_available(summary):
        return guidance.macro_guidance

    return None


def _nutrition_limitations(
    summary: TargetVsActualNutritionSummary | None,
) -> list[str]:
    if summary is None:
        return ["Nutrition target-vs-actual context is unavailable today."]
    if summary.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS:
        return ["No nutrition logs are available for today yet."]
    limitations: list[str] = []
    if summary.logging_completeness in {
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    }:
        limitations.append(
            "Nutrition logging is incomplete, so calorie conclusions are limited."
        )
    if not _macro_comparisons_are_available(summary):
        limitations.append("Macro comparisons are limited until more meals are logged.")
    return limitations


def _nutrition_reason_codes(
    summary: TargetVsActualNutritionSummary | None,
    guidance: ApprovedNutritionGuidance | None,
) -> list[str]:
    if summary is None or guidance is None:
        return ["nutrition_target_vs_actual_unavailable"]

    reason_codes = ["nutrition_target_vs_actual_available"]
    if summary.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS:
        reason_codes.append("nutrition_no_logs_today")
    if summary.logging_completeness in {
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    }:
        reason_codes.extend(
            [
                "nutrition_logging_incomplete",
                "nutrition_guidance_limited_by_logging_quality",
            ]
        )

    protein = _protein_comparison(summary)
    if protein and protein.comparison_available:
        if protein.target_status == TARGET_STATUS_BELOW:
            reason_codes.append("protein_below_target_based_on_logs")
        if protein.target_status == TARGET_STATUS_NEAR:
            reason_codes.append("protein_near_target_based_on_logs")

    calories = _calorie_comparison(summary)
    if calories is None or not calories.comparison_available:
        reason_codes.append("calorie_comparison_limited")

    if not _macro_comparisons_are_available(summary):
        reason_codes.append("macro_comparison_limited")

    return reason_codes


def _validate_nutrition_synthesis_claims(
    synthesis: DailyCoachSynthesis,
    summary: TargetVsActualNutritionSummary,
    guidance: ApprovedNutritionGuidance | None,
) -> list[str]:
    violations: list[str] = []
    text = _synthesis_text(synthesis).lower()

    calories = _calorie_comparison(summary)
    if calories is not None and not calories.comparison_available:
        hard_calorie_claims = [
            "calories are below",
            "calories are above",
            "calories are near",
            "calorie intake is below",
            "calorie intake is above",
            "calorie intake is near",
        ]
        if any(term in text for term in hard_calorie_claims):
            violations.append(
                "DailyCoachSynthesis must not make hard calorie claims when calorie comparison is unavailable."
            )

    if _nutrition_logging_is_limited(summary):
        hard_macro_claims = [
            "carbs are below",
            "carbs are above",
            "fat is below",
            "fat is above",
            "macros are on target",
        ]
        if any(term in text for term in hard_macro_claims):
            violations.append(
                "DailyCoachSynthesis must not make exact macro claims when nutrition logging is incomplete."
            )

    if summary.confidence in {"Limited", "Low"}:
        for term in _LOW_CONFIDENCE_STRONG_TERMS:
            if term in text:
                violations.append(
                    "Low/Limited nutrition confidence must keep synthesis language soft."
                )
                break

    return violations


def _has_recovery_checkin_data(health_state: UserHealthState) -> bool:
    recovery = health_state.recovery_state
    return any(
        _is_number(value)
        for value in [
            recovery.avg_sleep,
            recovery.avg_energy,
            recovery.avg_soreness,
        ]
    )


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _rir_target_text(constraints: TrainingConstraints) -> str:
    if (
        constraints.recommended_rir_min is None
        or constraints.recommended_rir_max is None
    ):
        return "Use the approved RIR target as the anchor today."
    return (
        f"Use RIR {constraints.recommended_rir_min}-{constraints.recommended_rir_max} "
        "as the anchor today."
    )


def _bounded_confidence(*values: str | None) -> str:
    rank = {"Limited": 0, "Low": 1, "Moderate": 2, "High": 3}
    valid_values = [value for value in values if value in rank]
    if not valid_values:
        return "Low"
    return min(valid_values, key=lambda value: rank[value])


def _synthesis_text(synthesis: DailyCoachSynthesis) -> str:
    return " ".join(
        str(getattr(synthesis, field_name)) for field_name in _DAILY_COACH_STRING_FIELDS
    )
