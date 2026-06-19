from __future__ import annotations

from models.daily_next_action_models import (
    DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
    DAILY_NEXT_ACTION_LOG_FOOD,
    DailyNextAction,
)
from services.daily_coach_narrative_context_service import (
    DailyCoachNarrativeContextValidationError,
    build_daily_coach_narrative_context,
    build_daily_coach_narrative_context_from_action,
    validate_daily_coach_narrative_context,
)


def _action(
    *,
    action_id: str = DAILY_NEXT_ACTION_LOG_FOOD,
    title: str = "Log a meal or snack",
    reason: str = "Today's nutrition state is limited until more food data is logged.",
    workflow_target: str = "nutrition_quick_log",
    priority: int = 3,
    severity: str = "info",
    evidence: dict[str, object] | None = None,
) -> DailyNextAction:
    return DailyNextAction(
        action_id=action_id,
        title=title,
        summary="Add today's food intake so nutrition guidance has enough data.",
        reason=reason,
        priority=priority,
        workflow_target=workflow_target,
        severity=severity,
        evidence=evidence
        or {
            "user_id": 102,
            "action_date": "2026-06-19",
            "scenario": "aligned_managed",
            "readiness_level": "High",
            "fatigue_risk": "Low",
            "recovery_checkin_present": True,
            "nutrition_logging_completeness": "likely_incomplete",
            "nutrition_confidence": "Limited",
            "workout_available": True,
            "report_guidance_available": False,
        },
    )


def test_context_preserves_daily_next_action_and_workflow_exactly():
    action = _action()

    context = build_daily_coach_narrative_context_from_action(
        user_id=102,
        action=action,
        context_date="2026-06-19",
    )

    assert context.user_id == 102
    assert context.date == "2026-06-19"
    assert context.next_action_id == action.action_id
    assert context.next_action_title == action.title
    assert context.next_action_reason == action.reason
    assert context.workflow_target == action.workflow_target
    assert context.priority == action.priority
    assert context.severity == action.severity
    assert context.approved_focus == action.title
    assert validate_daily_coach_narrative_context(context) == []


def test_context_has_explicit_approved_facts_and_limitations():
    context = build_daily_coach_narrative_context_from_action(
        user_id=105,
        action=_action(
            evidence={
                "user_id": 105,
                "action_date": "2026-06-19",
                "scenario": "data_quality_limited",
                "readiness_level": "Unknown",
                "fatigue_risk": "Unknown",
                "recovery_checkin_present": False,
                "nutrition_logging_completeness": "no_logs",
                "nutrition_confidence": "Limited",
                "workout_available": False,
                "report_guidance_available": False,
            }
        ),
        context_date="2026-06-19",
    )

    assert "Daily next action: Log a meal or snack" in context.approved_facts
    assert "Workflow target: nutrition_quick_log" in context.approved_facts
    assert "Coaching scenario: data_quality_limited" in context.approved_facts
    assert "Recovery check-in status: missing" in context.approved_facts
    assert any(
        "Recovery context is limited" in item for item in context.approved_limitations
    )
    assert any(
        "Nutrition confidence is limited" in item
        for item in context.approved_limitations
    )
    assert context.confidence_language.startswith("Confidence is limited")


def test_forbidden_claims_cover_v1_safety_boundary():
    context = build_daily_coach_narrative_context_from_action(
        user_id=101,
        action=_action(
            action_id=DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
            title="Keep training conservative",
            reason="Current recovery state supports keeping today's training lower-risk and controlled.",
            workflow_target="today_recovery_aware_workout",
            priority=1,
            severity="warning",
            evidence={
                "user_id": 101,
                "action_date": "2026-06-19",
                "scenario": "recovery_limited",
                "readiness_level": "Poor",
                "fatigue_risk": "High",
                "recovery_checkin_present": True,
                "nutrition_logging_completeness": "complete_enough",
                "nutrition_confidence": "Moderate",
                "workout_available": True,
                "report_guidance_available": True,
            },
        ),
        context_date="2026-06-19",
    )

    forbidden_claims = set(context.forbidden_claims)
    assert "changed daily next action" in forbidden_claims
    assert "changed workflow target" in forbidden_claims
    assert "invented food" in forbidden_claims
    assert "invented exercise" in forbidden_claims
    assert "unsupported fatigue claim" in forbidden_claims
    assert "unsupported progression claim" in forbidden_claims
    assert "medical diagnosis" in forbidden_claims
    assert "meal plan" in forbidden_claims
    assert context.confidence_language == (
        "Use conservative language and do not exceed the backend-approved action."
    )


def test_fallback_note_is_deterministic_daily_next_action_wording():
    action = _action()

    context = build_daily_coach_narrative_context_from_action(
        user_id=102,
        action=action,
        context_date="2026-06-19",
    )

    assert context.fallback_note == f"{action.title}: {action.reason}"


def test_internal_evidence_keys_are_not_exposed():
    context = build_daily_coach_narrative_context_from_action(
        user_id=102,
        action=_action(
            evidence={
                "user_id": 102,
                "scenario": "aligned_managed",
                "nutrition_confidence": "Limited",
                "raw_provider_payload": "do not expose",
                "debug_traceback": "do not expose",
                "validation_errors": ["do not expose"],
            }
        ),
        context_date="2026-06-19",
    )

    serialized = str(context.to_dict()).lower()
    assert "raw_provider_payload" not in serialized
    assert "debug_traceback" not in serialized
    assert "validation_errors" not in serialized
    assert validate_daily_coach_narrative_context(context) == []


def test_validation_rejects_changed_approved_focus():
    action = _action()
    context = build_daily_coach_narrative_context_from_action(
        user_id=102,
        action=action,
        context_date="2026-06-19",
    )
    mutated = context.__class__(
        **{
            **context.to_dict(),
            "approved_focus": "Review today's workout",
        }
    )

    violations = validate_daily_coach_narrative_context(mutated)

    assert "DailyCoachNarrativeContext.approved_focus changed the action." in violations


def test_validation_rejects_non_deterministic_fallback_note():
    action = _action()
    context = build_daily_coach_narrative_context_from_action(
        user_id=102,
        action=action,
        context_date="2026-06-19",
    )
    mutated = context.__class__(
        **{
            **context.to_dict(),
            "fallback_note": "A model-written fallback note",
        }
    )

    violations = validate_daily_coach_narrative_context(mutated)

    assert (
        "DailyCoachNarrativeContext.fallback_note is not deterministic." in violations
    )


def test_top_level_builder_uses_daily_next_action_without_model_call(monkeypatch):
    calls = {"next_action": 0}
    expected_action = _action()

    def fake_build_daily_next_action(user_id: int, *, target_date: str | None = None):
        calls["next_action"] += 1
        assert user_id == 102
        assert target_date == "2026-06-19"
        return expected_action

    monkeypatch.setattr(
        "services.daily_coach_narrative_context_service.build_daily_next_action",
        fake_build_daily_next_action,
    )

    context = build_daily_coach_narrative_context(
        102,
        target_date="2026-06-19",
    )

    assert calls == {"next_action": 1}
    assert context.next_action_id == expected_action.action_id
    assert context.approved_focus == expected_action.title


def test_invalid_context_from_top_level_builder_raises(monkeypatch):
    def fake_build_daily_next_action(user_id: int, *, target_date: str | None = None):
        return _action(title="", reason="")

    monkeypatch.setattr(
        "services.daily_coach_narrative_context_service.build_daily_next_action",
        fake_build_daily_next_action,
    )

    try:
        build_daily_coach_narrative_context(102, target_date="2026-06-19")
    except DailyCoachNarrativeContextValidationError as exc:
        assert "required text fields" in str(exc)
    else:
        raise AssertionError("Expected DailyCoachNarrativeContextValidationError")
