from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from models.daily_coach_narrative_models import (
    DAILY_COACH_NARRATIVE_CONTEXT_STATUS_READY,
    DAILY_COACH_NARRATIVE_FORBIDDEN_CLAIMS_V1,
    DAILY_COACH_NARRATIVE_REQUIRED_OUTPUT_KEYS,
    DailyCoachNarrativeContext,
)
from models.daily_next_action_models import DailyNextAction
from services.daily_next_action_service import build_daily_next_action
from services.weekly_coach_summary_qa_data_service import (
    DEFAULT_QA_DATE_RANGE_USER_ID,
    DEFAULT_QA_LOW_DATA_USER_ID,
    QA_USER_LABELS,
    WeeklyCoachSummaryQADataError,
    inspect_weekly_summary_qa_range,
)

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


def build_daily_coach_narrative_qa_preview_context(
    user_id: int,
    *,
    selected_date: str | None = None,
    lookback_days: int = 1,
) -> DailyCoachNarrativeContext:
    """Build a Developer Mode QA Daily Narrative context for seeded dates.

    This path mirrors the Weekly Coach Summary QA date-range seam: selected
    user/date inputs are typed, backend-owned, and converted to safe aggregate
    facts. It does not call a provider and does not expose raw rows, notes, food
    logs, set rows, prompts, or provider output.
    """

    qa_user_id = int(user_id)
    if qa_user_id not in QA_USER_LABELS:
        raise DailyCoachNarrativeContextValidationError(
            "Daily Narrative QA Preview supports QA users 101-105 only."
        )

    preview_date = date.fromisoformat(selected_date or "2026-06-06")
    bounded_lookback = max(1, min(int(lookback_days or 1), 7))
    start_date = preview_date - timedelta(days=bounded_lookback - 1)

    try:
        inventory = inspect_weekly_summary_qa_range(
            user_id=qa_user_id,
            start_date=start_date.isoformat(),
            end_date=preview_date.isoformat(),
        )
    except WeeklyCoachSummaryQADataError as exc:
        raise DailyCoachNarrativeContextValidationError(str(exc)) from exc

    context = _build_daily_narrative_context_from_qa_inventory(
        user_id=qa_user_id,
        selected_date=preview_date.isoformat(),
        lookback_days=bounded_lookback,
        inventory=inventory,
    )
    violations = validate_daily_coach_narrative_context(context)
    if violations:
        raise DailyCoachNarrativeContextValidationError("; ".join(violations))
    return context


def daily_narrative_qa_default_user_id() -> int:
    return DEFAULT_QA_DATE_RANGE_USER_ID


def daily_narrative_qa_low_data_user_id() -> int:
    return DEFAULT_QA_LOW_DATA_USER_ID


def _build_daily_narrative_context_from_qa_inventory(
    *,
    user_id: int,
    selected_date: str,
    lookback_days: int,
    inventory,
) -> DailyCoachNarrativeContext:
    fact_counts = inventory.fact_counts
    nutrition_entries = int(fact_counts.get("nutrition", 0))
    recovery_rows = int(fact_counts.get("recovery", 0))
    workout_sessions = int(fact_counts.get("workout_sessions", 0))
    workout_execution_sessions = int(fact_counts.get("workout_execution_sessions", 0))
    actual_sets = int(fact_counts.get("workout_sets", 0))
    planned_exercises = int(fact_counts.get("planned_workout_exercises", 0))
    training_present = workout_sessions > 0 or workout_execution_sessions > 0
    nutrition_present = nutrition_entries > 0
    recovery_present = recovery_rows > 0
    range_label = (
        "selected date"
        if inventory.start_date == inventory.end_date
        else "selected range"
    )

    action_id, title, reason, workflow_target, priority, severity = _qa_daily_action(
        range_label=range_label,
        nutrition_present=nutrition_present,
        recovery_present=recovery_present,
        training_present=training_present,
        selected_date=selected_date,
        data_quality_label=inventory.data_quality_label,
    )

    approved_facts = [
        f"Selected QA user: {user_id} {inventory.scenario}",
        f"Selected date: {selected_date}",
        f"Selected range: {inventory.start_date} through {inventory.end_date}",
        f"Lookback days: {lookback_days}",
        f"Data quality label: {inventory.data_quality_label}",
        f"Daily next action: {title}",
        f"Daily next action reason: {reason}",
        f"Workflow target: {workflow_target}",
        f"Recovery entries in {range_label}: {recovery_rows}",
        f"Nutrition entries in {range_label}: {nutrition_entries}",
        f"Workout sessions in {range_label}: {workout_sessions}",
        f"Workout execution sessions in {range_label}: {workout_execution_sessions}",
        f"Planned workout exercises in {range_label}: {planned_exercises}",
        f"Actual set count in {range_label}: {actual_sets}",
    ]
    approved_facts.extend(
        _qa_missing_data_reason_facts(
            range_label=range_label,
            nutrition_present=nutrition_present,
            recovery_present=recovery_present,
            training_present=training_present,
            actual_sets=actual_sets,
        )
    )

    limitations = list(inventory.limitations)
    limitations.extend(
        _qa_preview_limitations(
            data_quality_label=inventory.data_quality_label,
            range_label=range_label,
            nutrition_present=nutrition_present,
            recovery_present=recovery_present,
            training_present=training_present,
        )
    )

    context = DailyCoachNarrativeContext(
        user_id=user_id,
        date=selected_date,
        next_action_id=action_id,
        next_action_title=title,
        next_action_reason=reason,
        workflow_target=workflow_target,
        priority=priority,
        severity=severity,
        approved_focus=title,
        confidence_language=_qa_confidence_language(inventory.data_quality_label),
        approved_facts=_dedupe_preserve_order(approved_facts),
        approved_limitations=_dedupe_preserve_order(limitations),
        forbidden_claims=list(DAILY_COACH_NARRATIVE_FORBIDDEN_CLAIMS_V1),
        fallback_note=f"{title}: {reason}",
        source_metadata={
            "context_source": "daily_narrative_qa_preview",
            "selected_date": selected_date,
            "start_date": inventory.start_date,
            "end_date": inventory.end_date,
            "lookback_days": lookback_days,
            "scenario": inventory.scenario,
            "data_quality_label": inventory.data_quality_label,
        },
        context_status=DAILY_COACH_NARRATIVE_CONTEXT_STATUS_READY,
    )
    return context


def _qa_daily_action(
    *,
    range_label: str,
    nutrition_present: bool,
    recovery_present: bool,
    training_present: bool,
    selected_date: str,
    data_quality_label: str,
) -> tuple[str, str, str, str, int, str]:
    if training_present and not nutrition_present:
        return (
            "daily_narrative_qa_log_nutrition_for_training_day",
            "Log a meal or snack",
            (
                f"Because training is present but nutrition is missing for the {range_label}, "
                "one meal entry gives the coach something real to compare against the training day."
            ),
            "nutrition_quick_log",
            3,
            "info",
        )
    if not nutrition_present:
        return (
            "daily_narrative_qa_log_missing_nutrition",
            "Log a meal or snack",
            (
                f"Because there are no nutrition entries for the {range_label} ending {selected_date}, "
                "one simple meal or snack log gives the coach something real to work from."
            ),
            "nutrition_quick_log",
            3,
            "info",
        )
    if not recovery_present:
        return (
            "daily_narrative_qa_complete_recovery_checkin",
            "Complete recovery check-in",
            (
                f"Because recovery detail is missing for the {range_label}, a quick check-in "
                "keeps the day from being interpreted from nutrition or training alone."
            ),
            "today_recovery_checkin",
            2,
            "info",
        )
    if data_quality_label == "limited":
        return (
            "daily_narrative_qa_keep_logging_simple",
            "Keep logging simple",
            (
                f"Because the {range_label} has limited data quality, the useful move is "
                "to keep logging simple before drawing stronger conclusions."
            ),
            "daily_logging_review",
            4,
            "info",
        )
    return (
        "daily_narrative_qa_compare_training_and_fueling",
        "Compare training and fueling",
        (
            f"Because the {range_label} has recovery, nutrition, and training context, "
            "the useful move is to compare effort with fueling instead of adding random detail."
        ),
        "daily_grounded_review",
        4,
        "success",
    )


def _qa_missing_data_reason_facts(
    *,
    range_label: str,
    nutrition_present: bool,
    recovery_present: bool,
    training_present: bool,
    actual_sets: int,
) -> list[str]:
    facts: list[str] = []
    if not nutrition_present:
        facts.append(
            f"Missing data reason: no nutrition entries for the {range_label}."
        )
    if not recovery_present:
        facts.append(
            f"Missing data reason: no recovery check-in for the {range_label}."
        )
    if training_present and actual_sets == 0:
        facts.append(
            f"Missing data reason: training is present but actual set detail is absent for the {range_label}."
        )
    if not nutrition_present and training_present:
        facts.append(
            f"Grounding reason: training is present but nutrition is missing for the {range_label}."
        )
    if not facts:
        facts.append(
            f"Grounding reason: selected {range_label} has enough safe aggregate facts for a more specific narrative."
        )
    return facts


def _qa_preview_limitations(
    *,
    data_quality_label: str,
    range_label: str,
    nutrition_present: bool,
    recovery_present: bool,
    training_present: bool,
) -> list[str]:
    limitations = [
        "Daily Narrative QA Preview uses safe aggregate facts only.",
        "Normal Today Daily Narrative behavior is unchanged by this Developer Mode preview.",
    ]
    if data_quality_label == "limited":
        limitations.append(
            "Keep conclusions cautious because this QA user has limited data quality."
        )
    if not nutrition_present:
        limitations.append(
            f"Nutrition interpretation is limited because the {range_label} has no nutrition entries."
        )
    if not recovery_present:
        limitations.append(
            f"Recovery interpretation is limited because the {range_label} has no recovery check-in."
        )
    if not training_present:
        limitations.append(
            f"Training interpretation is limited because the {range_label} has no workout session."
        )
    return limitations


def _qa_confidence_language(data_quality_label: str) -> str:
    if data_quality_label == "limited":
        return "Confidence is limited because the selected QA context is intentionally sparse."
    return "Confidence is based on the selected QA date range and safe aggregate facts."


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
            "Workout-specific explanation is limited unless today's workout preview is available."
        )

    if not limitations:
        limitations.append(
            "Keep the note focused on today's selected action and available facts."
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
        return "Confidence is limited until more nutrition logging is available today."

    if action.severity == "warning":
        return "Confidence stays conservative because today's action is safety-focused."

    if approved_limitations:
        return "Confidence is based on today's selected action and available facts."

    return "Confidence is based on today's selected action and available facts."


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
    tokens = set(
        "".join(
            character if character.isalnum() else " " for character in lowered
        ).split()
    )
    if tokens.intersection(_INTERNAL_METADATA_TERMS):
        return True
    normalized = " ".join(tokens)
    return "validation error" in normalized or "validation errors" in normalized


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
