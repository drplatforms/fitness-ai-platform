from __future__ import annotations

import json
from pathlib import Path

from models.daily_next_action_models import DailyNextAction
from services.daily_coach_narrative_context_service import (
    build_daily_coach_narrative_context_from_action,
)
from services.daily_coach_narrative_provider_service import (
    build_daily_coach_narrative_prompt,
)
from services.daily_coach_narrative_validation_service import (
    parse_daily_coach_narrative_candidate,
    validate_daily_coach_narrative_candidate,
)
from ui.daily_coach_session_approval import daily_coach_preview_approval_eligibility


def _context():
    action = DailyNextAction(
        action_id="log_food",
        title="Log a meal or snack",
        summary="Add today's food intake so nutrition guidance has enough data.",
        reason="Today's nutrition state is limited until more food data is logged.",
        priority=3,
        workflow_target="nutrition_quick_log",
        severity="info",
        evidence={
            "scenario": "data_quality_limited",
            "recovery_checkin_present": True,
            "nutrition_logging_completeness": "likely_incomplete",
            "nutrition_confidence": "Limited",
            "workout_available": False,
            "report_guidance_available": False,
        },
    )
    return build_daily_coach_narrative_context_from_action(
        user_id=102,
        action=action,
        context_date="2026-06-21",
    )


def _payload(context, **overrides):
    payload = {
        "coach_note": (
            "Nutrition is the missing anchor for this date. Add one meal entry "
            "so the coach can connect today's guidance to something concrete."
        ),
        "key_takeaway": "Today's nutrition state is limited until more food data is logged.",
        "recommended_focus": context.approved_focus,
        "confidence_language": "Keep this limited until more food data is logged.",
        "used_approved_facts": [
            f"Daily next action: {context.next_action_title}",
            f"Daily next action reason: {context.next_action_reason}",
        ],
        "avoided_claims": [
            "No food, exercise, target, recovery, or medical claim was invented."
        ],
    }
    payload.update(overrides)
    return payload


def _validate_payload(payload, context):
    parsed = parse_daily_coach_narrative_candidate(json.dumps(payload))
    assert parsed.candidate is not None
    return validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )


def test_product_voice_prompt_adds_shape_without_expanding_authority() -> None:
    context = _context()

    prompt = build_daily_coach_narrative_prompt(context)

    assert "PRODUCT_VOICE_TARGET" in prompt
    assert "human coach" in prompt
    assert "two or three short sentences" in prompt
    assert (
        "Do not add facts, targets, trends, medical claims, or a second action."
        in prompt
    )
    assert "BANNED_DAILY_NARRATIVE_PHRASES" in prompt
    assert "GOOD_STYLE_EXAMPLES" in prompt
    assert "BAD_STYLE_EXAMPLES" in prompt
    assert "useful move" in prompt
    assert "clearer picture" in prompt
    assert "backend" not in prompt.lower()
    assert "provider default" not in prompt.lower()


def test_product_voice_validator_accepts_specific_grounded_coach_copy() -> None:
    context = _context()

    validation = _validate_payload(_payload(context), context)

    assert validation.approved is True
    assert validation.validation_errors == []


def test_product_voice_validator_rejects_generic_template_and_meta_copy() -> None:
    context = _context()
    payload = _payload(
        context,
        coach_note=(
            "Based on the data provided, what matters today: Log a meal or snack. "
            "You got this."
        ),
    )

    validation = _validate_payload(payload, context)

    assert validation.approved is False
    joined = " ".join(validation.validation_errors)
    assert "Generic/template coach language" in joined
    assert "Generic filler language" in joined


def test_product_voice_validator_rejects_mechanical_daily_narrative_phrases() -> None:
    context = _context()
    payload = _payload(
        context,
        coach_note=(
            "Today's useful move is to keep logging simple so this builds a clearer picture "
            "without overcomplicating it."
        ),
    )

    validation = _validate_payload(payload, context)

    assert validation.approved is False
    joined = " ".join(validation.validation_errors)
    assert "Mechanical Daily Narrative phrase" in joined


def test_product_voice_validator_still_rejects_unsupported_claims() -> None:
    context = _context()
    payload = _payload(
        context,
        coach_note=(
            "Log a meal or snack, then eat 200g chicken breast to hit a protein target."
        ),
    )

    validation = _validate_payload(payload, context)

    assert validation.approved is False
    joined = " ".join(validation.validation_errors)
    assert "Forbidden claim" in joined
    assert "Invented numeric" in joined


def test_product_voice_does_not_widen_same_session_bridge_model_policy() -> None:
    approved_preview = {
        "user_id": 102,
        "date": "2026-06-21",
        "next_action_id": "log_food",
        "workflow_target": "nutrition_quick_log",
        "provider_enabled": True,
        "provider_attempted": True,
        "selected_provider": "direct_ollama",
        "selected_model": "qwen2.5:3b",
        "parse_success": True,
        "validation_success": True,
        "approved_narrative_returned": True,
        "fallback_used": False,
        "fallback_reason": None,
        "forbidden_debug_leaks": [],
        "approved_narrative": _payload(_context()),
    }

    assert daily_coach_preview_approval_eligibility(approved_preview).eligible is True

    qwen3_preview = {**approved_preview, "selected_model": "qwen3:8b"}
    assert daily_coach_preview_approval_eligibility(qwen3_preview).eligible is False


def test_product_voice_memory_docs_are_required() -> None:
    required = [
        "docs/project_memory/milestones/daily_coach_narrative_product_voice_polish_v1.md",
        "docs/project_memory/reviews/daily_coach_narrative_product_voice_polish_v1.md",
    ]

    for path in required:
        assert Path(path).exists(), path
