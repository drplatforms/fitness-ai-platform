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


def test_weekly_coach_summary_developer_panel_is_gated() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    developer_source = _function_source("render_developer_section")

    assert "Developer Mode: Weekly Coach Summary QA Date Range Debug" in panel_source
    assert 'if not st.session_state.get("developer_mode", False):' in panel_source
    assert (
        "render_weekly_coach_summary_developer_inspection(user_id)" in developer_source
    )
    assert "Turn on Developer Mode in the sidebar" in developer_source


def test_weekly_coach_summary_debug_is_not_in_normal_today_ui() -> None:
    today_source = _function_source("render_today_section")

    assert "Weekly Coach Summary QA Date Range Debug" not in today_source
    assert "render_weekly_coach_summary_developer_inspection" not in today_source


def test_weekly_coach_summary_selected_range_generation_is_button_driven() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    button_index = panel_source.index(
        "Generate deterministic weekly summary from selected QA range"
    )
    generate_index = panel_source.index("generate_approved_weekly_summary(context)")

    assert button_index < generate_index
    assert "st.button" in panel_source
    assert "build_weekly_summary_context_from_qa_range" in panel_source
    assert "approved_weekly_summary_to_public_sections(summary)" in panel_source


def test_weekly_coach_summary_debug_renders_safe_sections() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    inventory_source = _function_source("_render_weekly_coach_summary_qa_inventory")
    helper_source = _function_source("_render_weekly_coach_summary_sections")
    combined_source = panel_source + inventory_source + helper_source

    for expected in [
        "Selected QA Range Inventory",
        "Source",
        "Confidence",
        "Public Safe",
        "Displayable",
        "Headline",
        "Weekly Overview",
        "Recovery Observation",
        "Nutrition Observation",
        "Training Observation",
        "Primary Pattern",
        "Recommended Focus",
        "Next Week Guidance",
        "Reason Codes",
        "Limitations",
    ]:
        assert expected in combined_source


def test_weekly_coach_summary_debug_has_selected_range_save_and_load() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    assert "Save selected-range approved summary" in panel_source
    assert "Load latest selected-range summary" in panel_source
    assert "save_approved_weekly_summary" in panel_source
    assert "get_latest_approved_weekly_summary" in panel_source
    assert "range_key" in panel_source


def test_weekly_coach_summary_debug_provider_preview_has_no_auto_job_calls() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    forbidden = [
        "api_get",
        "api_post",
        "create_developer_mode_provider_runtime_job",
        "run_daily_coach_async_provider_runtime_prototype",
        "call_ollama",
        "CrewAI",
        "qwen3",
        "create_async_job",
        "raw_provider_output",
        "rejected_provider_output",
        "full_prompt",
        "raw_context",
        "scratchpad",
        "chain_of_thought",
    ]
    for term in forbidden:
        assert term not in panel_source

    assert "Generate provider candidate" in panel_source
    assert panel_source.index("Generate provider candidate") < panel_source.index(
        "generate_weekly_summary_provider_preview("
    )


def test_weekly_coach_summary_developer_preview_uses_fragment_and_timing() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    timing_source = _function_source("_render_weekly_coach_summary_timing")

    assert "def weekly_coach_summary_streamlit_fragment" in source
    assert "@weekly_coach_summary_streamlit_fragment" in source
    assert "perf_counter" in panel_source
    assert "Weekly Coach Summary Timing" in timing_source
    assert "panel_render_ms" in panel_source
    assert "deterministic_generation_ms" in panel_source
    assert "save_ms" in panel_source
    assert "load_latest_ms" in panel_source


def test_weekly_coach_summary_timing_is_not_in_normal_today_ui() -> None:
    today_source = _function_source("render_today_section")

    assert "Weekly Coach Summary Timing" not in today_source
    assert "weekly_coach_summary_timing_by_user" not in today_source
