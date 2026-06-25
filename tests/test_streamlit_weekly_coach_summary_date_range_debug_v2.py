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
    assert "weekly_coach_summary_qa_context_service" in panel_source
    assert "build_weekly_summary_context_from_qa_range" in panel_source
    assert "weekly_summary_context_to_safe_metadata" in panel_source
    assert "Generated from selected QA date-range context" in panel_source
    assert "generate_approved_weekly_summary(context)" in panel_source
    assert panel_source.index("Inspect selected QA range") < panel_source.index(
        "inspect_weekly_summary_qa_range("
    )
    assert panel_source.index(
        "Generate deterministic weekly summary from selected QA range"
    ) < panel_source.index("generate_approved_weekly_summary(context)")


def test_qa_date_range_debug_v2_uses_range_scoped_cache_and_persistence() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    assert "range_key = qa_date_range_cache_key" in panel_source
    assert "preview_cache[range_key]" in panel_source
    assert "persisted_cache[range_key]" in panel_source
    assert "Load latest selected-range summary" in panel_source


def test_qa_date_range_debug_v2_preserves_lazy_navigation() -> None:
    nav_source = _function_source("render_main_navigation")

    assert "st.radio(" in nav_source
    assert 'elif selected_page == "Developer":' in nav_source
    developer_branch = nav_source[
        nav_source.index('elif selected_page == "Developer":') :
    ]
    assert "render_developer_section(user_id)" in developer_branch
    assert "render_workout_plan_section(user_id)" not in developer_branch
    assert "render_history_section(user_id)" not in developer_branch


def test_qa_date_range_debug_v2_provider_preview_is_manual_and_safe() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    forbidden = (
        "api_post",
        "CrewAI",
        "qwen3",
        "raw_provider_output",
        "raw_context",
        "scratchpad",
        "chain_of_thought",
    )
    for term in forbidden:
        assert term not in panel_source

    assert "Generate provider candidate" in panel_source
    assert "generate_weekly_summary_provider_preview(" in panel_source
    assert panel_source.index("Generate provider candidate") < panel_source.index(
        "generate_weekly_summary_provider_preview("
    )


def test_selected_range_persistence_controls_render_before_summary_sections() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    assert "Selected-Range Persistence Controls" in panel_source
    assert "Save selected-range approved summary" in panel_source
    assert "Load latest selected-range summary" in panel_source
    assert panel_source.index(
        "Save selected-range approved summary"
    ) < panel_source.index("_render_weekly_coach_summary_sections(sections)")


def test_generated_preview_does_not_reuse_status_message_for_inventory_area() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    assert (
        "Selected QA range inventory used for this generated summary." in panel_source
    )
    assert panel_source.index(
        "cached_preview = preview_cache.get(range_key)"
    ) < panel_source.index("if cached_inventory:")
