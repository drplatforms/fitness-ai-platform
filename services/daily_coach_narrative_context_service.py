from __future__ import annotations

from datetime import date
from typing import Any

from models.daily_coach_narrative_models import (
    DAILY_COACH_NARRATIVE_CONTEXT_STATUS_READY,
    DAILY_COACH_NARRATIVE_FORBIDDEN_CLAIMS_V1,
    DAILY_COACH_NARRATIVE_REQUIRED_OUTPUT_KEYS,
    DailyCoachNarrativeContext,
)
from models.daily_next_action_models import DailyNextAction
from services.daily_next_action_service import build_daily_next_action

_INTERNAL_METADATA_TERMS = {
    "raw",
    "debug",
    "provider",
    "prompt",
    "schema",
    "validation_error",
    "validation_errors",
    "traceback",
    "payload",
    "model",
    "ollama",
    "qwen",
    "crewai",
    "parser",
}

_LIMITED_CONFIDENCE_VALUES = {"Limited", "Low", "Unknown", None}


class DailyCoachNarrativeContextValidationError(ValueError):
    """Raised when a DailyCoachNarrativeContext violates the v1 contract."""


def build_daily_coach_narrative_context(
    user_id: int,
    *,
    target_date: str | None = None,
) -> DailyCoachNarrativeContext:
    """Build a backend-approved Daily Coach Narrative context packet.

    This function intentionally calls only deterministic backend services. It does
    not call qwen, Ollama, CrewAI, direct_ollama, or any provider path.
    """

    context_date = target_date or date.today().isoformat()
    action = build_daily_next_action(user_id, target_date=context_date)
    context = build_daily_coach_narrative_context_from_action(
        user_id=user_id,
        action=action,
        context_date=context_date,
    )

    violations = validate_daily_coach_narrative_context(context)
    if violations:
        raise DailyCoachNarrativeContextValidationError("; ".join(violations))

    return context


def build_daily_coach_narrative_context_from_action(
    *,
    user_id: int,
    action: DailyNextAction,
    context_date: str | None = None,
) -> DailyCoachNarrativeContext:
    """Build narrative context from an already-approved DailyNextAction.

    This helper exists so tests and future debug endpoints can verify that the
    context builder preserves the selected action and workflow target exactly.
    """

    context_date = context_date or date.today().isoformat()
    evidence = _public_safe_evidence(action.evidence)
    approved_facts = _build_approved_facts(action=action, evidence=evidence)
    approved_limitations = _build_approved_limitations(evidence=evidence)
    confidence_language = _build_confidence_language(
        action=action,
        evidence=evidence,
        approved_limitations=approved_limitations,
    )

    context = DailyCoachNarrativeContext(
        user_id=user_id,
        date=context_date,
        next_action_id=action.action_id,
        next_action_title=action.title,
        next_action_reason=action.reason,
        workflow_target=action.workflow_target,
        priority=action.priority,
        severity=action.severity,
        approved_focus=action.title,
        confidence_language=confidence_language,
        approved_facts=approved_facts,
        approved_limitations=approved_limitations,
        forbidden_claims=list(DAILY_COACH_NARRATIVE_FORBIDDEN_CLAIMS_V1),
        fallback_note=_build_fallback_note(action),
        source_metadata={
            "context_source": "daily_next_action_service",
            "output_contract_keys": sorted(DAILY_COACH_NARRATIVE_REQUIRED_OUTPUT_KEYS),
        },
        context_status=DAILY_COACH_NARRATIVE_CONTEXT_STATUS_READY,
    )

    violations = validate_daily_coach_narrative_context(context)
    if violations:
        raise DailyCoachNarrativeContextValidationError("; ".join(violations))

    return context


def validate_daily_coach_narrative_context(
    context: DailyCoachNarrativeContext,
) -> list[str]:
    """Validate the public-safe v1 narrative context contract."""

    violations: list[str] = []

    if context.user_id <= 0:
        violations.append("DailyCoachNarrativeContext.user_id must be positive.")

    required_text_fields = [
        context.date,
        context.next_action_id,
        context.next_action_title,
        context.next_action_reason,
        context.workflow_target,
        context.severity,
        context.approved_focus,
        context.confidence_language,
        context.fallback_note,
        context.context_status,
    ]
    if any(not str(value).strip() for value in required_text_fields):
        violations.append("DailyCoachNarrativeContext required text fields must exist.")

    if context.approved_focus != context.next_action_title:
        violations.append(
            "DailyCoachNarrativeContext.approved_focus changed the action."
        )

    if context.priority < 1:
        violations.append("DailyCoachNarrativeContext.priority must be positive.")

    if len(context.approved_facts) < 3:
        violations.append("DailyCoachNarrativeContext.approved_facts is too sparse.")

    if not context.forbidden_claims:
        violations.append("DailyCoachNarrativeContext.forbidden_claims is required.")

    if context.fallback_note != _expected_fallback_note(context):
        violations.append(
            "DailyCoachNarrativeContext.fallback_note is not deterministic."
        )

    public_safe_payload = {
        "next_action_title": context.next_action_title,
        "next_action_reason": context.next_action_reason,
        "approved_facts": context.approved_facts,
        "approved_limitations": context.approved_limitations,
        "fallback_note": context.fallback_note,
        "source_metadata": context.source_metadata,
    }
    if _contains_internal_terms(public_safe_payload):
        violations.append(
            "DailyCoachNarrativeContext exposes raw/debug/provider/model metadata."
        )

    return violations


def _build_approved_facts(
    *,
    action: DailyNextAction,
    evidence: dict[str, object],
) -> list[str]:
    facts = [
        f"Daily next action: {action.title}",
        f"Daily next action reason: {action.reason}",
        f"Workflow target: {action.workflow_target}",
        f"Priority: {action.priority}",
        f"Severity: {action.severity}",
    ]

    scenario = _string_or_none(evidence.get("scenario"))
    if scenario:
        facts.append(f"Coaching scenario: {scenario}")

    readiness = _string_or_none(evidence.get("readiness_level"))
    if readiness:
        facts.append(f"Recovery readiness level: {readiness}")

    fatigue_risk = _string_or_none(evidence.get("fatigue_risk"))
    if fatigue_risk:
        facts.append(f"Fatigue risk label: {fatigue_risk}")

    completeness = _string_or_none(evidence.get("nutrition_logging_completeness"))
    if completeness:
        facts.append(f"Nutrition logging completeness: {completeness}")

    nutrition_confidence = _string_or_none(evidence.get("nutrition_confidence"))
    if nutrition_confidence:
        facts.append(f"Nutrition confidence: {nutrition_confidence}")

    recovery_present = evidence.get("recovery_checkin_present")
    if isinstance(recovery_present, bool):
        status = "present" if recovery_present else "missing"
        facts.append(f"Recovery check-in status: {status}")

    workout_available = evidence.get("workout_available")
    if isinstance(workout_available, bool):
        status = "available" if workout_available else "not available"
        facts.append(f"Workout preview status: {status}")

    report_guidance_available = evidence.get("report_guidance_available")
    if isinstance(report_guidance_available, bool):
        status = "available" if report_guidance_available else "not available"
        facts.append(f"Report guidance status: {status}")

    return _dedupe_preserve_order(facts)


def _build_approved_limitations(evidence: dict[str, object]) -> list[str]:
    limitations: list[str] = []

    if evidence.get("recovery_checkin_present") is False:
        limitations.append(
            "Recovery context is limited until today's recovery check-in is updated."
        )

    nutrition_confidence = evidence.get("nutrition_confidence")
    if nutrition_confidence in _LIMITED_CONFIDENCE_VALUES:
        limitations.append(
            "Nutrition confidence is limited to the logged evidence available today."
        )

    completeness = evidence.get("nutrition_logging_completeness")
    if completeness in {"no_logs", "partial_day", "likely_incomplete"}:
        limitations.append(
            "Nutrition guidance should stay focused on logging completeness."
        )

    if evidence.get("workout_available") is False:
        limitations.append(
            "Workout-specific explanation is limited unless an approved workout preview is available."
        )

    if not limitations:
        limitations.append(
            "Narrative wording must stay limited to the approved daily action and facts."
        )

    return limitations


def _build_confidence_language(
    *,
    action: DailyNextAction,
    evidence: dict[str, object],
    approved_limitations: list[str],
) -> str:
    if evidence.get("recovery_checkin_present") is False:
        return "Confidence is limited until today's recovery check-in is updated."

    nutrition_confidence = evidence.get("nutrition_confidence")
    if nutrition_confidence in _LIMITED_CONFIDENCE_VALUES:
        return "Confidence is limited to backend-approved facts and current logging completeness."

    if action.severity == "warning":
        return (
            "Use conservative language and do not exceed the backend-approved action."
        )

    if approved_limitations:
        return (
            "Use only the backend-approved daily action, reason, and supporting facts."
        )

    return "Use only backend-approved facts."


def _build_fallback_note(action: DailyNextAction) -> str:
    return f"{action.title}: {action.reason}"


def _expected_fallback_note(context: DailyCoachNarrativeContext) -> str:
    return f"{context.next_action_title}: {context.next_action_reason}"


def _public_safe_evidence(evidence: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in evidence.items():
        key_text = str(key)
        if _contains_internal_fragment(key_text):
            continue
        if isinstance(value, str | int | float | bool) or value is None:
            safe[key_text] = value
    return safe


def _contains_internal_terms(payload: Any) -> bool:
    if isinstance(payload, dict):
        return any(
            _contains_internal_terms(key) or _contains_internal_terms(value)
            for key, value in payload.items()
        )
    if isinstance(payload, list | tuple | set):
        return any(_contains_internal_terms(item) for item in payload)
    if isinstance(payload, str):
        return _contains_internal_fragment(payload)
    return False


def _contains_internal_fragment(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in _INTERNAL_METADATA_TERMS)


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            deduped.append(value)
            seen.add(value)
    return deduped
