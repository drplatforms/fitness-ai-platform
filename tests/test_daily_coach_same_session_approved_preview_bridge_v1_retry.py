from __future__ import annotations

import ast
from pathlib import Path

from ui.daily_coach_session_approval import (
    DAILY_COACH_SESSION_APPROVAL_MODEL,
    DAILY_COACH_SESSION_APPROVAL_PROVIDER,
    DAILY_COACH_SESSION_APPROVAL_STATE_KEY,
    build_daily_coach_session_approval_key_from_context,
    build_daily_coach_session_approval_key_from_preview,
    daily_coach_preview_approval_eligibility,
    get_daily_coach_session_approved_narrative,
    store_daily_coach_session_approved_narrative,
)


def _approved_preview(**overrides: object) -> dict[str, object]:
    preview: dict[str, object] = {
        "user_id": 102,
        "date": "2026-06-20",
        "next_action_id": "log_food",
        "next_action_title": "Log a meal or snack",
        "workflow_target": "nutrition_quick_log",
        "provider_enabled": True,
        "provider_attempted": True,
        "selected_provider": DAILY_COACH_SESSION_APPROVAL_PROVIDER,
        "selected_model": DAILY_COACH_SESSION_APPROVAL_MODEL,
        "parse_success": True,
        "validation_success": True,
        "approved_narrative_returned": True,
        "fallback_used": False,
        "fallback_reason": None,
        "forbidden_debug_leaks": [],
        "approved_narrative": {
            "coach_note": "Log a meal or snack so today's nutrition read has a better base.",
            "key_takeaway": "The useful move is to close the logging gap first.",
            "recommended_focus": "Log a meal or snack",
            "confidence_language": "Keep this limited until more food data is logged.",
        },
    }
    preview.update(overrides)
    return preview


def _function_source(name: str) -> str:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


def test_approval_eligibility_requires_full_provider_success() -> None:
    eligibility = daily_coach_preview_approval_eligibility(_approved_preview())

    assert eligibility.eligible is True
    assert eligibility.reasons == []


def test_approval_eligibility_rejects_parse_validation_and_fallback_failures() -> None:
    cases = [
        ("parse_success", False, "Parse must succeed"),
        ("validation_success", False, "Validation must succeed"),
        ("approved_narrative_returned", False, "approved narrative"),
        ("fallback_used", True, "Fallback output"),
        ("fallback_reason", "provider_timeout", "Fallback reason"),
    ]

    for key, value, expected_reason in cases:
        eligibility = daily_coach_preview_approval_eligibility(
            _approved_preview(**{key: value})
        )
        assert eligibility.eligible is False
        assert expected_reason in " ".join(eligibility.reasons)


def test_approval_eligibility_rejects_forbidden_debug_leaks() -> None:
    eligibility = daily_coach_preview_approval_eligibility(
        _approved_preview(forbidden_debug_leaks=["raw_output"])
    )

    assert eligibility.eligible is False
    assert "Forbidden/debug leaks" in " ".join(eligibility.reasons)


def test_approval_eligibility_rejects_non_bridge_models_and_providers() -> None:
    non_bridge_model = daily_coach_preview_approval_eligibility(
        _approved_preview(selected_model="qwen3:8b")
    )
    non_bridge_provider = daily_coach_preview_approval_eligibility(
        _approved_preview(selected_provider="deterministic")
    )

    assert non_bridge_model.eligible is False
    assert "qwen2.5:3b" in " ".join(non_bridge_model.reasons)
    assert non_bridge_provider.eligible is False
    assert "direct_ollama" in " ".join(non_bridge_provider.reasons)


def test_session_approval_key_includes_context_provider_and_model() -> None:
    preview = _approved_preview()
    key = build_daily_coach_session_approval_key_from_preview(preview)

    assert "102" in key
    assert "2026-06-20" in key
    assert "log_food" in key
    assert "nutrition_quick_log" in key
    assert DAILY_COACH_SESSION_APPROVAL_PROVIDER in key
    assert DAILY_COACH_SESSION_APPROVAL_MODEL in key


def test_session_approval_retrieves_only_matching_context() -> None:
    preview = _approved_preview()
    session_state: dict[str, object] = {}
    record = store_daily_coach_session_approved_narrative(session_state, preview)

    matching_context = {
        "user_id": 102,
        "date": "2026-06-20",
        "next_action_id": "log_food",
        "workflow_target": "nutrition_quick_log",
    }
    changed_user = {**matching_context, "user_id": 105}
    changed_date = {**matching_context, "date": "2026-06-21"}
    changed_action = {**matching_context, "next_action_id": "review_workout"}
    changed_target = {**matching_context, "workflow_target": "workout_preview"}

    assert record[
        "approval_key"
    ] == build_daily_coach_session_approval_key_from_context(matching_context)
    assert session_state[DAILY_COACH_SESSION_APPROVAL_STATE_KEY]
    assert get_daily_coach_session_approved_narrative(session_state, matching_context)
    assert (
        get_daily_coach_session_approved_narrative(session_state, changed_user) is None
    )
    assert (
        get_daily_coach_session_approved_narrative(session_state, changed_date) is None
    )
    assert (
        get_daily_coach_session_approved_narrative(session_state, changed_action)
        is None
    )
    assert (
        get_daily_coach_session_approved_narrative(session_state, changed_target)
        is None
    )


def test_normal_today_card_does_not_call_provider_preview_or_show_debug_terms() -> None:
    function_source = _function_source("render_daily_coach_today_card")

    context_source = _function_source("build_daily_coach_session_approval_context")

    assert "/daily-coach/{user_id}/today-card" in function_source
    assert "/daily-coach/{user_id}/next-action" in context_source
    assert "narrative-preview" not in function_source
    assert "narrative-preview" not in context_source
    assert "direct_ollama" not in function_source
    assert "qwen2.5:3b" not in function_source
    assert "parse_success" not in function_source
    assert "validation_success" not in function_source
    assert "Approve for this session" not in function_source


def test_developer_panel_contains_manual_approval_controls_only() -> None:
    function_source = _function_source("render_daily_coach_narrative_developer_panel")

    assert "Run selected narrative preview" in function_source
    assert "Approve for this session" in function_source
    assert "daily_coach_preview_approval_eligibility" in function_source
    assert "store_daily_coach_session_approved_narrative" in function_source
    assert "Clear session-approved coach note" in function_source


def test_no_provider_narrative_persistence_or_database_write_added() -> None:
    helper_source = Path("ui/daily_coach_session_approval.py").read_text(
        encoding="utf-8"
    )
    streamlit_source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")

    assert "sqlite" not in helper_source.lower()
    assert "database" not in helper_source.lower()
    assert "report" not in helper_source.lower()
    assert "api_post" not in _function_source(
        "render_daily_coach_narrative_developer_panel"
    )
    assert "Approve for this session" in streamlit_source
