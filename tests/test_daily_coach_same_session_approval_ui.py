from __future__ import annotations

import ast
from pathlib import Path


def _function_source(name: str) -> str:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


def test_normal_today_card_does_not_call_provider_preview_route():
    function_source = _function_source("render_daily_coach_today_card")

    assert "/daily-coach/{user_id}/today-card" in function_source
    assert "narrative-preview" not in function_source
    assert "fetch_daily_coach_narrative_preview" not in function_source
    assert "call_ollama" not in function_source.lower()


def test_same_session_approval_controls_are_developer_panel_only():
    developer_source = _function_source("render_daily_coach_narrative_developer_panel")
    approval_source = _function_source(
        "render_daily_coach_same_session_approval_controls"
    )

    assert (
        "render_daily_coach_same_session_approval_controls(preview)" in developer_source
    )
    assert "Approve for this session" in approval_source
    assert "Revert to deterministic note" in approval_source
    assert "will not be saved" in approval_source


def test_normal_today_source_does_not_expose_provider_model_labels():
    function_source = _function_source("render_daily_coach_today_card")

    forbidden_fragments = [
        "selected_provider",
        "selected_model",
        "parse_success",
        "validation_success",
        "raw_response",
        "prompt",
        "qwen",
        "ollama",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in function_source


def test_same_session_approval_uses_session_state_not_persistence():
    approval_source = _function_source(
        "render_daily_coach_same_session_approval_controls"
    )
    helper_source = _function_source("apply_daily_coach_session_approval_if_valid")

    combined = f"{approval_source}\n{helper_source}"
    assert "daily_coach_approved_preview_session" in combined
    assert "st.session_state" in combined
    assert "api_post" not in combined
    assert "api_put" not in combined
    assert "api_patch" not in combined
    assert "database" not in combined.lower()
    assert "report" not in combined.lower()


def test_rejected_preview_cannot_render_approval_controls_without_approved_narrative():
    function_source = _function_source(
        "render_daily_coach_same_session_approval_controls"
    )

    assert (
        "approved_narrative = daily_coach_narrative_approved_display(preview)"
        in function_source
    )
    assert "if not approved_narrative:" in function_source
    assert "return" in function_source
    assert "validate_preview_for_same_session_approval" in function_source


def test_preview_status_coerces_mixed_values_before_dataframe_render():
    function_source = _function_source("render_daily_coach_narrative_preview_status")

    assert "daily_coach_developer_display_value" in function_source
    assert "display_rows" in function_source
    assert "pd.DataFrame(display_rows)" in function_source
