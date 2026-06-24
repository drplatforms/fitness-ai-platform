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


def test_qa_date_range_debug_v2_is_developer_mode_only() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    today_source = _function_source("render_today_section")
    assert "Developer Mode: Weekly Coach Summary QA Date Range Debug" in panel_source
    assert 'if not st.session_state.get("developer_mode", False):' in panel_source
    assert "Weekly Coach Summary QA Date Range Debug" not in today_source
    assert "Inspect selected QA range" not in today_source


def test_qa_date_range_debug_v2_uses_stable_typed_selection() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    assert "options=user_ids" in panel_source
    assert "format_func=lambda option: user_options[int(option)]" in panel_source
    assert "split" not in panel_source


def test_qa_date_range_debug_v2_has_manual_inspect_and_generate_buttons() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    assert "Inspect selected QA range" in panel_source
    assert (
        "Generate deterministic weekly summary from selected QA range" in panel_source
    )
    assert "inspect_weekly_summary_qa_range" in panel_source
    assert "build_weekly_summary_context_from_qa_range" in panel_source
    assert "generate_approved_weekly_summary(context)" in panel_source


def test_qa_date_range_debug_v2_uses_range_scoped_cache_and_persistence() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    assert "range_key = qa_date_range_cache_key" in panel_source
    assert "preview_cache[range_key]" in panel_source
    assert "persisted_cache[range_key]" in panel_source
    assert "Load latest selected-range summary" in panel_source


def test_qa_date_range_debug_v2_has_no_provider_calls() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    for forbidden in (
        "api_post",
        "CrewAI",
        "qwen2.5",
        "qwen3",
        "raw_provider_output",
        "raw_context",
        "scratchpad",
        "chain_of_thought",
    ):
        assert forbidden not in panel_source
