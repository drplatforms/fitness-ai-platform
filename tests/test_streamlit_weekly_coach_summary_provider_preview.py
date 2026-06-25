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


def test_weekly_provider_preview_is_developer_mode_only_inside_debug_panel() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    today_source = _function_source("render_today_section")

    assert 'if not st.session_state.get("developer_mode", False):' in panel_source
    assert "Weekly Coach Summary Provider Preview" in panel_source
    assert "Generate provider candidate" in panel_source
    assert "Weekly Coach Summary Provider Preview" not in today_source
    assert "Generate provider candidate" not in today_source


def test_weekly_provider_preview_is_manual_button_only() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    assert "generate_weekly_summary_provider_preview(" in panel_source
    assert "weekly_coach_summary_generate_provider_candidate_button" in panel_source
    assert panel_source.index("Generate provider candidate") < panel_source.index(
        "generate_weekly_summary_provider_preview("
    )
    assert "Provider preview is disabled" in panel_source


def test_weekly_provider_preview_uses_backend_context_not_ui_labels() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    assert "build_weekly_summary_context_from_qa_range" in panel_source
    assert 'deterministic_summary=cached_preview["summary"]' in panel_source
    assert "split" not in panel_source
    assert "raw_provider_output" not in panel_source
    assert "raw_context" not in panel_source
    assert "scratchpad" not in panel_source


def test_weekly_provider_preview_cache_is_range_scoped() -> None:
    source = _source()
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    assert "weekly_coach_summary_provider_preview_by_range" in source
    assert "provider_preview_cache[range_key]" in panel_source
    assert "provider_preview_cache.get(range_key)" in panel_source
