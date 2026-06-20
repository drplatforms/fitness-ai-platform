from __future__ import annotations

import json

from models.daily_next_action_models import (
    DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
    DAILY_NEXT_ACTION_LOG_FOOD,
    DailyNextAction,
)
from services.daily_coach_narrative_context_service import (
    build_daily_coach_narrative_context_from_action,
)
from services.daily_coach_narrative_preview_service import (
    DAILY_COACH_NARRATIVE_PREVIEW_DEFAULT_MODEL,
    DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DETERMINISTIC,
    DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA,
    PUBLIC_SAFE_FALLBACK_PROVIDER_DISABLED,
    PUBLIC_SAFE_FALLBACK_PROVIDER_PARSE_FAILED,
    PUBLIC_SAFE_FALLBACK_PROVIDER_VALIDATION_FAILED,
    build_daily_coach_narrative_preview,
)


def _action(
    *,
    action_id: str = DAILY_NEXT_ACTION_LOG_FOOD,
    title: str = "Log a meal or snack",
    reason: str = "Today's nutrition state is limited until more food data is logged.",
    workflow_target: str = "nutrition_quick_log",
    priority: int = 3,
    severity: str = "info",
) -> DailyNextAction:
    return DailyNextAction(
        action_id=action_id,
        title=title,
        summary="Add today's food intake so nutrition guidance has enough data.",
        reason=reason,
        priority=priority,
        workflow_target=workflow_target,
        severity=severity,
        evidence={
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


def _context():
    return build_daily_coach_narrative_context_from_action(
        user_id=102,
        action=_action(),
        context_date="2026-06-19",
    )


def _approved_output(context):
    return json.dumps(
        {
            "coach_note": "Log a meal or snack to improve today's nutrition picture.",
            "key_takeaway": "More food logging gives today's guidance a clearer base.",
            "recommended_focus": context.approved_focus,
            "confidence_language": "Keep this limited until more food data is logged.",
            "used_approved_facts": context.approved_facts[:2],
            "avoided_claims": [
                "No food, exercise, target, recovery, or medical claim was invented."
            ],
        }
    )


def test_preview_defaults_to_deterministic_fallback_without_provider_call(monkeypatch):
    context = _context()
    calls = {"provider": 0}

    def fake_build_context(user_id: int, *, target_date: str | None = None):
        assert user_id == 102
        assert target_date == "2026-06-19"
        return context

    def fake_generate(*args, **kwargs):
        calls["provider"] += 1
        raise AssertionError("Provider should not be called by default.")

    monkeypatch.setattr(
        "services.daily_coach_narrative_preview_service.build_daily_coach_narrative_context",
        fake_build_context,
    )

    preview = build_daily_coach_narrative_preview(
        102,
        target_date="2026-06-19",
        provider=DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DETERMINISTIC,
        generate=fake_generate,
    )

    assert calls == {"provider": 0}
    assert preview.provider_enabled is False
    assert preview.provider_attempted is False
    assert preview.fallback_used is True
    assert preview.fallback_reason == PUBLIC_SAFE_FALLBACK_PROVIDER_DISABLED
    assert preview.approved_narrative is None
    assert preview.deterministic_fallback_note == context.fallback_note
    assert preview.context_summary["approved_facts_count"] == len(
        context.approved_facts
    )


def test_preview_returns_approved_narrative_after_parse_and_validation(monkeypatch):
    context = _context()
    calls = {"provider": 0}

    def fake_build_context(user_id: int, *, target_date: str | None = None):
        return context

    def fake_generate(
        model_name: str, prompt: str, timeout_seconds: float, base_url: str
    ):
        calls["provider"] += 1
        assert model_name == DAILY_COACH_NARRATIVE_PREVIEW_DEFAULT_MODEL
        assert "FOCUS_TO_COPY_EXACTLY" in prompt
        return _approved_output(context)

    monkeypatch.setattr(
        "services.daily_coach_narrative_preview_service.build_daily_coach_narrative_context",
        fake_build_context,
    )

    preview = build_daily_coach_narrative_preview(
        102,
        provider=DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA,
        generate=fake_generate,
    )

    assert calls == {"provider": 1}
    assert preview.provider_enabled is True
    assert preview.provider_attempted is True
    assert (
        preview.selected_provider
        == DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA
    )
    assert preview.selected_model == DAILY_COACH_NARRATIVE_PREVIEW_DEFAULT_MODEL
    assert preview.parse_success is True
    assert preview.validation_success is True
    assert preview.fallback_used is False
    assert preview.fallback_reason is None
    assert preview.approved_narrative is not None
    assert preview.approved_narrative["recommended_focus"] == context.approved_focus


def test_preview_falls_back_without_exposing_rejected_provider_text(monkeypatch):
    context = _context()
    rejected_phrase = (
        "Use the exact approved focus because backend-approved facts support it."
    )

    def fake_build_context(user_id: int, *, target_date: str | None = None):
        return context

    def fake_generate(
        model_name: str, prompt: str, timeout_seconds: float, base_url: str
    ):
        return json.dumps(
            {
                "coach_note": rejected_phrase,
                "key_takeaway": "More food logging gives today's guidance a clearer base.",
                "recommended_focus": context.approved_focus,
                "confidence_language": "Keep this limited until more food data is logged.",
                "used_approved_facts": context.approved_facts[:2],
                "avoided_claims": ["No invented claim."],
            }
        )

    monkeypatch.setattr(
        "services.daily_coach_narrative_preview_service.build_daily_coach_narrative_context",
        fake_build_context,
    )

    preview = build_daily_coach_narrative_preview(
        102,
        provider=DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA,
        generate=fake_generate,
    )
    payload = str(preview.to_dict())

    assert preview.parse_success is True
    assert preview.validation_success is False
    assert preview.fallback_used is True
    assert preview.fallback_reason == PUBLIC_SAFE_FALLBACK_PROVIDER_VALIDATION_FAILED
    assert preview.approved_narrative is None
    assert rejected_phrase not in payload
    assert "backend-approved" not in payload
    assert "Meta/internal process language is not allowed" in payload
    assert "raw_output" not in payload
    assert "prompt" not in payload


def test_preview_parse_failure_falls_back_without_raw_output(monkeypatch):
    context = _context()

    def fake_build_context(user_id: int, *, target_date: str | None = None):
        return context

    def fake_generate(
        model_name: str, prompt: str, timeout_seconds: float, base_url: str
    ):
        return "not json from provider"

    monkeypatch.setattr(
        "services.daily_coach_narrative_preview_service.build_daily_coach_narrative_context",
        fake_build_context,
    )

    preview = build_daily_coach_narrative_preview(
        102,
        provider=DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA,
        generate=fake_generate,
    )
    payload = str(preview.to_dict()).lower()

    assert preview.parse_success is False
    assert preview.validation_success is False
    assert preview.fallback_used is True
    assert preview.fallback_reason == PUBLIC_SAFE_FALLBACK_PROVIDER_PARSE_FAILED
    assert preview.approved_narrative is None
    assert "not json from provider" not in payload


def test_preview_keeps_training_action_from_drifting_to_nutrition(monkeypatch):
    context = build_daily_coach_narrative_context_from_action(
        user_id=101,
        action=_action(
            action_id=DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
            title="Keep training conservative",
            reason=(
                "Current recovery state supports keeping today's training "
                "lower-risk and controlled."
            ),
            workflow_target="today_recovery_aware_workout",
            priority=1,
            severity="warning",
        ),
        context_date="2026-06-19",
    )

    def fake_build_context(user_id: int, *, target_date: str | None = None):
        return context

    def fake_generate(
        model_name: str, prompt: str, timeout_seconds: float, base_url: str
    ):
        assert "without switching to nutrition logging" in prompt
        return json.dumps(
            {
                "coach_note": "Log a meal or snack to improve today's nutrition picture.",
                "key_takeaway": "Food logging gives today's guidance a clearer base.",
                "recommended_focus": "Log a meal or snack",
                "confidence_language": "Keep this limited until more food data is logged.",
                "used_approved_facts": context.approved_facts[:2],
                "avoided_claims": ["No invented claim."],
            }
        )

    monkeypatch.setattr(
        "services.daily_coach_narrative_preview_service.build_daily_coach_narrative_context",
        fake_build_context,
    )

    preview = build_daily_coach_narrative_preview(
        101,
        provider=DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA,
        generate=fake_generate,
    )

    assert preview.validation_success is False
    assert preview.fallback_used is True
    assert preview.fallback_reason == PUBLIC_SAFE_FALLBACK_PROVIDER_VALIDATION_FAILED
    assert preview.approved_narrative is None
