from __future__ import annotations

import ast
import json
from pathlib import Path

from models.daily_coach_narrative_models import DailyCoachNarrativeContext
from services.daily_coach_narrative_preview_service import (
    DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA,
    PUBLIC_SAFE_FALLBACK_PROVIDER_PARSE_FAILED,
    PUBLIC_SAFE_FALLBACK_PROVIDER_VALIDATION_FAILED,
    build_daily_coach_narrative_preview,
)


def _context() -> DailyCoachNarrativeContext:
    return DailyCoachNarrativeContext(
        user_id=102,
        date="2026-06-20",
        next_action_id="log_food",
        next_action_title="Log a meal or snack",
        next_action_reason="Today's nutrition state is limited until more food data is logged.",
        workflow_target="nutrition_quick_log",
        priority=1,
        severity="info",
        approved_focus="Log a meal or snack",
        confidence_language="Keep this limited until more food data is logged.",
        approved_facts=[
            "Daily next action: Log a meal or snack",
            "Daily next action reason: Today's nutrition state is limited until more food data is logged.",
            "Nutrition logging completeness: likely incomplete",
        ],
        approved_limitations=[
            "Do not invent food suggestions or macro targets.",
            "Keep nutrition confidence limited until more food data is logged.",
        ],
        fallback_note="Log a meal or snack: today's nutrition state is limited until more food data is logged.",
    )


def _valid_payload(context: DailyCoachNarrativeContext) -> dict[str, object]:
    return {
        "coach_note": "Log a meal or snack so today's nutrition state has enough information to work from.",
        "key_takeaway": "Today's nutrition state is limited until more food data is logged.",
        "recommended_focus": context.approved_focus,
        "confidence_language": "Keep this limited until more food data is logged.",
        "used_approved_facts": context.approved_facts[:2],
        "avoided_claims": [
            "No food, exercise, target, recovery, or medical claim was invented."
        ],
    }


def _build_preview(monkeypatch, provider_text: str):
    import services.daily_coach_narrative_preview_service as preview_service

    context = _context()
    monkeypatch.setattr(
        preview_service,
        "build_daily_coach_narrative_context",
        lambda user_id, target_date=None: context,
    )

    return build_daily_coach_narrative_preview(
        102,
        provider=DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA,
        model_name="qwen2.5:3b",
        generate=lambda model, prompt, timeout_seconds, base_url: provider_text,
    )


def test_valid_provider_response_reaches_approved_preview(monkeypatch):
    context = _context()
    preview = _build_preview(monkeypatch, json.dumps(_valid_payload(context)))
    payload = preview.to_dict()

    assert payload["parse_success"] is True
    assert payload["validation_success"] is True
    assert payload["fallback_used"] is False
    assert payload["approved_narrative_returned"] is True
    assert payload["approved_narrative"]["recommended_focus"] == context.approved_focus


def test_markdown_fenced_json_reaches_approved_preview(monkeypatch):
    context = _context()
    provider_text = "```json\n" + json.dumps(_valid_payload(context)) + "\n```"

    preview = _build_preview(monkeypatch, provider_text)
    payload = preview.to_dict()

    assert payload["parse_success"] is True
    assert payload["validation_success"] is True
    assert payload["approved_narrative_returned"] is True
    assert "markdown_json_fence_stripped" in payload["parse_extraction_strategy"]


def test_qwen_thinking_wrapper_reaches_approved_preview(monkeypatch):
    context = _context()
    provider_text = "<think>private reasoning</think>\n" + json.dumps(
        _valid_payload(context)
    )

    preview = _build_preview(monkeypatch, provider_text)
    payload = preview.to_dict()

    assert payload["parse_success"] is True
    assert payload["validation_success"] is True
    assert payload["approved_narrative_returned"] is True
    assert "qwen_think_stripped" in payload["parse_extraction_strategy"]
    assert "private reasoning" not in str(payload)


def test_prose_around_single_json_object_reaches_approved_preview(monkeypatch):
    context = _context()
    provider_text = (
        "Here is the JSON:\n" + json.dumps(_valid_payload(context)) + "\nDone."
    )

    preview = _build_preview(monkeypatch, provider_text)
    payload = preview.to_dict()

    assert payload["parse_success"] is True
    assert payload["validation_success"] is True
    assert payload["approved_narrative_returned"] is True
    assert "single_embedded_json_object" in payload["parse_extraction_strategy"]


def test_ambiguous_multiple_json_objects_fail_safely_without_raw_leak(monkeypatch):
    context = _context()
    provider_text = (
        json.dumps(_valid_payload(context)) + "\n" + json.dumps(_valid_payload(context))
    )

    preview = _build_preview(monkeypatch, provider_text)
    payload = preview.to_dict()

    assert payload["parse_success"] is False
    assert payload["validation_success"] is False
    assert payload["fallback_used"] is True
    assert payload["fallback_reason"] == PUBLIC_SAFE_FALLBACK_PROVIDER_PARSE_FAILED
    assert payload["approved_narrative_returned"] is False
    assert "ambiguous_multiple_json_objects" in payload["parse_extraction_strategy"]
    assert "Here is" not in str(payload)
    assert "raw_output" not in str(payload).lower()
    assert "prompt" not in str(payload).lower()


def test_validation_failure_returns_sanitized_errors_without_rejected_text(monkeypatch):
    context = _context()
    payload = _valid_payload(context)
    rejected_text = (
        "Use the exact approved focus because backend-approved facts support it."
    )
    payload["coach_note"] = rejected_text

    preview = _build_preview(monkeypatch, json.dumps(payload))
    result = preview.to_dict()

    assert result["parse_success"] is True
    assert result["validation_success"] is False
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == PUBLIC_SAFE_FALLBACK_PROVIDER_VALIDATION_FAILED
    assert result["approved_narrative_returned"] is False
    assert "validation_errors" in result
    assert "meta/internal process" in str(result["validation_errors"]).lower()
    assert rejected_text not in str(result)
    assert "backend-approved" not in str(result)
    assert "raw_output" not in str(result).lower()


def test_normal_today_ui_has_no_automatic_provider_approval_controls() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    today_card_source = ""
    preview_source = ""
    for node in module.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "render_daily_coach_today_card"
        ):
            today_card_source = ast.get_source_segment(source, node) or ""
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "render_daily_coach_narrative_developer_panel"
        ):
            preview_source = ast.get_source_segment(source, node) or ""

    assert "Approve for this session" not in today_card_source
    assert "Approve for this session" in preview_source
    assert "same_session_approved_provider_preview" not in source
