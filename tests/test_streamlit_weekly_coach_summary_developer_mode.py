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

    assert "Developer Mode: Weekly Coach Summary Preview" in panel_source
    assert 'if not st.session_state.get("developer_mode", False):' in panel_source
    assert (
        "render_weekly_coach_summary_developer_inspection(user_id)" in developer_source
    )
    assert "Turn on Developer Mode in the sidebar" in developer_source


def test_weekly_coach_summary_preview_is_not_in_normal_today_ui() -> None:
    today_source = _function_source("render_today_section")

    assert "Weekly Coach Summary Preview" not in today_source
    assert "render_weekly_coach_summary_developer_inspection" not in today_source


def test_weekly_coach_summary_preview_generation_is_button_driven() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    button_index = panel_source.index("Generate deterministic weekly summary preview")
    generate_index = panel_source.index("generate_approved_weekly_summary(context)")

    assert button_index < generate_index
    assert "st.button" in panel_source
    assert "build_weekly_summary_context_from_fixture(**fixture)" in panel_source
    assert "approved_weekly_summary_to_public_sections(summary)" in panel_source


def test_weekly_coach_summary_preview_has_required_scenarios() -> None:
    source = _function_source("weekly_coach_summary_developer_scenarios")

    assert "Consistent training / moderate confidence" in source
    assert "Low data / deterministic fallback" in source
    assert "Mixed signal / cautious guidance" in source
    assert "workouts_completed" in source
    assert "nutrition_days_logged" in source


def test_weekly_coach_summary_developer_preview_renders_safe_sections() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    helper_source = _function_source("_render_weekly_coach_summary_sections")
    combined_source = panel_source + helper_source

    for expected in [
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


def test_weekly_coach_summary_developer_preview_has_explicit_save_and_load() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    assert "Save approved deterministic summary" in panel_source
    assert "Load latest persisted weekly summary" in panel_source
    assert "save_approved_weekly_summary" in panel_source
    assert "get_latest_approved_weekly_summary" in panel_source
    assert "Persisted Weekly Coach Summary Metadata" in panel_source


def test_weekly_coach_summary_developer_preview_has_no_provider_or_auto_job_calls() -> (
    None
):
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")

    forbidden = [
        "api_get",
        "api_post",
        "create_developer_mode_provider_runtime_job",
        "run_daily_coach_async_provider_runtime_prototype",
        "call_ollama",
        "CrewAI",
        "qwen2.5",
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


def test_weekly_coach_summary_qa_data_range_controls_are_developer_only() -> None:
    panel_source = _function_source("render_weekly_coach_summary_developer_inspection")
    developer_source = _function_source("render_developer_section")
    qa_source = _function_source("render_weekly_coach_summary_qa_data_range_debug")
    today_source = _function_source("render_today_section")

    assert "render_weekly_coach_summary_qa_data_range_debug()" in developer_source
    assert "render_weekly_coach_summary_qa_data_range_debug()" not in panel_source
    assert "Weekly Coach Summary QA Data Range" in qa_source
    assert "Weekly Coach Summary QA user" in qa_source
    assert "Inspect QA data range" in qa_source
    assert "Generate deterministic weekly summary from selected QA range" in qa_source
    assert "Save selected-range approved summary" in qa_source
    assert "Load latest selected-range summary" in qa_source
    assert "Weekly Coach Summary QA Data Range" not in today_source


def test_weekly_coach_summary_qa_data_range_uses_safe_services_only() -> None:
    qa_source = _function_source("render_weekly_coach_summary_qa_data_range_debug")

    assert "get_weekly_summary_fact_inventory" in qa_source
    assert "build_weekly_summary_context_from_qa_range" in qa_source
    assert "save_approved_weekly_summary" in qa_source
    assert "get_latest_approved_weekly_summary" in qa_source
    assert "raw provider" in qa_source.lower()
    forbidden_calls = [
        "api_get(",
        "api_post(",
        "run_daily_coach_async_provider_runtime_prototype",
        "create_developer_mode_provider_runtime_job",
        "call_ollama",
        "CrewAI",
        "qwen2.5",
        "qwen3",
        "create_async_job",
    ]
    for term in forbidden_calls:
        assert term not in qa_source


def test_weekly_coach_summary_qa_data_range_not_in_normal_today_ui() -> None:
    today_source = _function_source("render_today_section")

    assert "Weekly Coach Summary QA user" not in today_source
    assert "Inspect QA data range" not in today_source
    assert "selected-range approved summary" not in today_source
