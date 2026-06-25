from __future__ import annotations

import ast
from pathlib import Path


def _source() -> str:
    return Path("ui/streamlit_app.py").read_text(encoding="utf-8")


def _function_source(name: str) -> str:
    source = _source()
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


def test_daily_narrative_qa_preview_is_developer_mode_only() -> None:
    panel_source = _function_source("render_daily_coach_narrative_developer_panel")
    today_source = _function_source("render_today_section")

    assert 'if not st.session_state.get("developer_mode", False):' in panel_source
    assert "Daily Narrative QA Date Range Preview" in panel_source
    assert "Use seeded QA date context" in panel_source
    assert "Daily Narrative QA Date Range Preview" not in today_source
    assert "Use seeded QA date context" not in today_source


def test_daily_narrative_qa_preview_uses_typed_inputs_not_label_parsing() -> None:
    panel_source = _function_source("render_daily_coach_narrative_developer_panel")
    fetch_source = _function_source("fetch_daily_coach_narrative_preview")

    assert "qa_user_id = st.selectbox" in panel_source
    assert "format_func=lambda value" in panel_source
    assert "preview_user_id = int(qa_user_id)" in panel_source
    assert "qa_selected_date.isoformat()" in panel_source
    assert "qa_preview" in fetch_source
    assert "lookback_days" in fetch_source
    assert ".split(" not in panel_source


def test_daily_narrative_provider_preview_remains_manual_button_only() -> None:
    panel_source = _function_source("render_daily_coach_narrative_developer_panel")

    assert "Run selected narrative preview" in panel_source
    assert "fetch_daily_coach_narrative_preview(" in panel_source
    assert panel_source.index("Run selected narrative preview") < panel_source.rindex(
        "fetch_daily_coach_narrative_preview("
    )
    assert "Provider output is" in panel_source
