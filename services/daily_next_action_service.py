from __future__ import annotations

from datetime import date

from models.daily_next_action_models import (
    DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN,
    DAILY_NEXT_ACTION_IDS,
    DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
    DAILY_NEXT_ACTION_LOG_FOOD,
    DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS,
    DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE,
    DAILY_NEXT_ACTION_REVIEW_WORKOUT,
    DAILY_NEXT_ACTION_SEVERITIES,
    DAILY_NEXT_ACTION_WORKFLOW_TARGETS,
    DailyNextAction,
)
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    TargetVsActualNutritionSummary,
)
from models.user_state_models import UserHealthState
from services.coaching_decision_service import build_coaching_decision
from services.nutrition_target_vs_actual_service import (
    build_target_vs_actual_nutrition_summary,
)
from services.user_state_service import build_user_health_state
from services.workout_plan_service import build_approved_workout_plan

_RECOVERY_LIMITED_SCENARIOS = {"recovery_limited"}
_RECOVERY_LIMITED_READINESS = {"Poor"}
_RECOVERY_LIMITED_FATIGUE = {"High"}
_INCOMPLETE_LOGGING_STATES = {
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
}
_COMPLETE_ENOUGH_LOGGING_STATES = {
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
}
_INTERNAL_DEBUG_TERMS = {
    "raw",
    "debug",
    "provider",
    "prompt",
    "schema",
    "validation_error",
    "validation_errors",
    "traceback",
    "payload",
    "model_facing_context",
    "parser",
}


class DailyNextActionValidationError(ValueError):
    """Raised when a daily next action violates the public contract."""


def build_daily_next_action(
    user_id: int,
    *,
    target_date: str | None = None,
) -> DailyNextAction:
    """Build the deterministic primary Today-page action for one user.

    This service composes backend-owned state only. It does not call an LLM,
    mutate logs, persist action state, or use provider output to choose navigation.
    """

    action_date = target_date or date.today().isoformat()
    health_state = build_user_health_state(user_id)
    coaching_decision = build_coaching_decision(health_state)

    try:
        nutrition_summary = build_target_vs_actual_nutrition_summary(
            user_id,
            action_date,
            health_state=health_state,
        )
    except Exception:
        nutrition_summary = None

    try:
        build_approved_workout_plan(health_state)
        workout_available = True
    except Exception:
        workout_available = False

    action = build_daily_next_action_from_components(
        health_state=health_state,
        scenario=coaching_decision.scenario,
        nutrition_summary=nutrition_summary,
        workout_available=workout_available,
        report_guidance_available=_report_guidance_available(nutrition_summary),
        action_date=action_date,
    )

    violations = validate_daily_next_action(action)
    if violations:
        raise DailyNextActionValidationError("; ".join(violations))

    return action


def build_daily_next_action_from_components(
    *,
    health_state: UserHealthState,
    scenario: str | None = None,
    nutrition_summary: TargetVsActualNutritionSummary | None = None,
    workout_available: bool = False,
    report_guidance_available: bool = False,
    action_date: str | None = None,
) -> DailyNextAction:
    """Select exactly one action from approved backend-owned components."""

    action_date = action_date or date.today().isoformat()
    scenario = scenario or health_state.coordinator_focus
    evidence = _build_evidence(
        health_state=health_state,
        scenario=scenario,
        nutrition_summary=nutrition_summary,
        workout_available=workout_available,
        report_guidance_available=report_guidance_available,
        action_date=action_date,
    )

    if _recovery_is_limited(health_state, scenario) and _recovery_checkin_present(
        health_state
    ):
        return _action(
            action_id=DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
            title="Keep training conservative",
            summary="Use a controlled training stance before pushing intensity.",
            reason=(
                "Current recovery state supports keeping today's training lower-risk "
                "and controlled."
            ),
            priority=1,
            workflow_target="today_recovery_aware_workout",
            severity="warning",
            evidence=evidence,
        )

    if not _recovery_checkin_present(health_state):
        return _action(
            action_id=DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN,
            title="Complete recovery check-in",
            summary="Update sleep, energy, soreness, and body weight first.",
            reason=(
                "Today's training and coaching read are limited until recovery data "
                "is updated."
            ),
            priority=2,
            workflow_target="today_recovery_checkin",
            severity="info",
            evidence=evidence,
        )

    if _nutrition_logging_is_incomplete(nutrition_summary):
        return _action(
            action_id=DAILY_NEXT_ACTION_LOG_FOOD,
            title="Log a meal or snack",
            summary="Add today's food intake so nutrition guidance has enough data.",
            reason=(
                "Today's nutrition state is limited until more food data is logged."
            ),
            priority=3,
            workflow_target="nutrition_quick_log",
            severity="info",
            evidence=evidence,
        )

    if workout_available:
        return _action(
            action_id=DAILY_NEXT_ACTION_REVIEW_WORKOUT,
            title="Review today's workout",
            summary="Check the approved workout before starting or logging sets.",
            reason=(
                "Recovery and available workout context support reviewing the "
                "structured plan for today."
            ),
            priority=4,
            workflow_target="workout_preview",
            severity="success",
            evidence=evidence,
        )

    if report_guidance_available:
        return _action(
            action_id=DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE,
            title="Review today's report guidance",
            summary="Use validated report sections to understand today's direction.",
            reason=(
                "Logged data is complete enough to review validated report guidance."
            ),
            priority=5,
            workflow_target="reports_guidance",
            severity="success",
            evidence=evidence,
        )

    return _action(
        action_id=DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS,
        title="Review nutrition target progress",
        summary="Check what nutrition target-vs-actual can safely show today.",
        reason=(
            "Some daily evidence is still limited, so review approved progress before "
            "drawing stronger conclusions."
        ),
        priority=6,
        workflow_target="nutrition_target_vs_actual",
        severity="info",
        evidence=evidence,
    )


def validate_daily_next_action(action: DailyNextAction) -> list[str]:
    violations: list[str] = []

    if action.action_id not in DAILY_NEXT_ACTION_IDS:
        violations.append("DailyNextAction.action_id is not approved for v1.")

    if action.workflow_target not in DAILY_NEXT_ACTION_WORKFLOW_TARGETS:
        violations.append("DailyNextAction.workflow_target is not approved for v1.")

    if action.severity not in DAILY_NEXT_ACTION_SEVERITIES:
        violations.append("DailyNextAction.severity is not approved for v1.")

    if not 1 <= action.priority <= 6:
        violations.append("DailyNextAction.priority must stay within the v1 order.")

    if (
        not action.title.strip()
        or not action.summary.strip()
        or not action.reason.strip()
    ):
        violations.append("DailyNextAction public text fields are required.")

    public_text = " ".join([action.title, action.summary, action.reason]).lower()
    forbidden_public_terms = [
        "raw provider",
        "prompt",
        "schema",
        "debug",
        "validation_error",
        "traceback",
        "qwen",
        "ollama",
    ]
    for term in forbidden_public_terms:
        if term in public_text:
            violations.append(
                "DailyNextAction public text exposes internal/provider terms."
            )
            break

    for key in action.evidence:
        key_lower = str(key).lower()
        if any(term in key_lower for term in _INTERNAL_DEBUG_TERMS):
            violations.append("DailyNextAction.evidence exposes internal/debug keys.")
            break

    return violations


def _action(
    *,
    action_id: str,
    title: str,
    summary: str,
    reason: str,
    priority: int,
    workflow_target: str,
    severity: str,
    evidence: dict[str, object],
) -> DailyNextAction:
    return DailyNextAction(
        action_id=action_id,
        title=title,
        summary=summary,
        reason=reason,
        priority=priority,
        workflow_target=workflow_target,
        severity=severity,
        evidence=evidence,
        is_available=True,
        blocked_reason=None,
    )


def _build_evidence(
    *,
    health_state: UserHealthState,
    scenario: str | None,
    nutrition_summary: TargetVsActualNutritionSummary | None,
    workout_available: bool,
    report_guidance_available: bool,
    action_date: str,
) -> dict[str, object]:
    return {
        "user_id": health_state.user_id,
        "action_date": action_date,
        "scenario": scenario or "Unknown",
        "readiness_level": health_state.recovery_state.readiness_level,
        "fatigue_risk": health_state.recovery_state.fatigue_risk,
        "recovery_checkin_present": _recovery_checkin_present(health_state),
        "nutrition_logging_completeness": _nutrition_logging_completeness(
            nutrition_summary
        ),
        "nutrition_confidence": _nutrition_confidence(nutrition_summary),
        "workout_available": workout_available,
        "report_guidance_available": report_guidance_available,
    }


def _recovery_checkin_present(health_state: UserHealthState) -> bool:
    recovery = health_state.recovery_state
    unknown_values = {"Unknown", "No data", None}
    return not (
        recovery.readiness_level in unknown_values
        or recovery.fatigue_risk in unknown_values
        or recovery.recovery_score <= 0
    )


def _recovery_is_limited(health_state: UserHealthState, scenario: str | None) -> bool:
    recovery = health_state.recovery_state
    return (
        scenario in _RECOVERY_LIMITED_SCENARIOS
        or recovery.readiness_level in _RECOVERY_LIMITED_READINESS
        or recovery.fatigue_risk in _RECOVERY_LIMITED_FATIGUE
    )


def _nutrition_logging_completeness(
    nutrition_summary: TargetVsActualNutritionSummary | None,
) -> str:
    if nutrition_summary is None:
        return LOGGING_COMPLETENESS_NO_LOGS
    return nutrition_summary.logging_completeness


def _nutrition_confidence(
    nutrition_summary: TargetVsActualNutritionSummary | None,
) -> str:
    if nutrition_summary is None:
        return "Limited"
    return nutrition_summary.confidence


def _nutrition_logging_is_incomplete(
    nutrition_summary: TargetVsActualNutritionSummary | None,
) -> bool:
    return (
        _nutrition_logging_completeness(nutrition_summary) in _INCOMPLETE_LOGGING_STATES
    )


def _report_guidance_available(
    nutrition_summary: TargetVsActualNutritionSummary | None,
) -> bool:
    if nutrition_summary is None:
        return False
    if nutrition_summary.confidence not in {"Moderate", "High"}:
        return False
    return nutrition_summary.logging_completeness in _COMPLETE_ENOUGH_LOGGING_STATES
