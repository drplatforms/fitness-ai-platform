from __future__ import annotations

from datetime import date
from typing import Any

from models.daily_coach_synthesis_models import DailyCoachSynthesis
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

    synthesis = build_daily_coach_synthesis_from_components(
        health_state=health_state,
        recommendation_context=recommendation_context,
        approved_action_plan=approved_action_plan,
        approved_workout_plan=approved_workout_plan,
        approved_workout_explanation=approved_workout_explanation,
        training_execution_summary=recommendation_context.training_execution_summary,
        latest_post_workout_review=latest_review,
        latest_planned_vs_actual_summary=latest_summary,
        synthesis_date=date.today().isoformat(),
    )

    violations = validate_daily_coach_synthesis(
        synthesis,
        recommendation_context=recommendation_context,
        approved_action_plan=approved_action_plan,
        approved_workout_plan=approved_workout_plan,
        training_execution_summary=recommendation_context.training_execution_summary,
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
    synthesis_date: str | None = None,
) -> DailyCoachSynthesis:
    training_summary = training_execution_summary
    limitations = _build_limitations(
        health_state, recommendation_context, training_summary
    )
    reason_codes = _build_reason_codes(
        recommendation_context,
        approved_action_plan,
        approved_workout_plan,
        training_summary,
        latest_post_workout_review,
        latest_planned_vs_actual_summary,
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
        today_summary=_today_summary(recommendation_context, approved_action_plan),
        recovery_signal=_recovery_signal(health_state, recommendation_context),
        training_signal=_training_signal(health_state, approved_action_plan),
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
        ),
        plan_fit_note=_plan_fit_note(training_summary, latest_post_workout_review),
        recommended_focus=_recommended_focus(
            recommendation_context, approved_action_plan
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


def _today_summary(
    context: RecommendationContext,
    plan: ApprovedActionPlan,
) -> str:
    if context.scenario == "recovery_limited":
        return "Today is best treated as a controlled training day with recovery signals kept in view."
    if context.scenario == "nutrition_training_mismatch":
        return "Today should connect training demand with nutrition and logging context without making hard target changes."
    if context.scenario == "improving_after_deload":
        return "Today supports controlled training while the recent improvement trend continues to stabilize."
    if context.scenario == "data_quality_limited":
        return "Today should stay simple and focused on better logging because data quality limits stronger conclusions."
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
) -> str:
    training = health_state.training_state
    if not training.has_workout_data:
        return "Training history is limited, so today should emphasize clear logging and a manageable baseline."
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
) -> str:
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
) -> str:
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

    return list(dict.fromkeys(limitations))


def _build_reason_codes(
    context: RecommendationContext,
    plan: ApprovedActionPlan,
    workout_plan: ApprovedWorkoutPlan,
    summary: TrainingExecutionSummary | None,
    latest_review: ApprovedPostWorkoutReviewSummary | None,
    latest_planned_vs_actual_summary: WorkoutPlannedVsActualSummary | None,
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
    reason_codes.extend(limitations)
    return list(dict.fromkeys(code for code in reason_codes if code))


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
