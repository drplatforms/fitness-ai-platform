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


def test_developer_tab_has_safe_latency_timing_panel() -> None:
    source = _source()
    developer_source = _function_source("render_developer_section")
    timing_source = _function_source("_render_developer_mode_latency_timing")

    assert '"developer_mode_latency_timing": {}' in source
    assert "Developer Mode Timing" in timing_source
    assert "developer_tab_render_ms" in developer_source
    assert "session_state_snapshot_render_ms" in developer_source
    assert "runtime_db_source_panel_render_ms" in developer_source
    assert "weekly_coach_summary_panel_render_ms" in developer_source
    assert "Safe aggregate timing only" in timing_source


def test_runtime_diagnostics_are_not_eager_on_tab_open() -> None:
    panel_source = _function_source("render_runtime_db_source_verification")

    assert "Refresh runtime / DB diagnostics" in panel_source
    assert "opening the Developer tab alone does not run this query" in panel_source
    assert "if refresh:" in panel_source
    assert (
        'refresh or "runtime_db_diagnostics" not in st.session_state'
        not in panel_source
    )
    assert "build_runtime_db_diagnostics" in panel_source
    assert panel_source.index("if refresh:") < panel_source.index(
        "build_runtime_db_diagnostics"
    )


def test_developer_session_state_defaults_are_cheap_for_heavy_results() -> None:
    source = _source()

    assert '"runtime_db_diagnostics": None' in source
    assert '"weekly_coach_summary_preview_by_user": {}' in source
    assert '"weekly_coach_summary_persisted_by_user": {}' in source
    assert '"weekly_coach_summary_timing_by_user": {}' in source
    defaults_start = source.index("SESSION_DEFAULTS = {")
    defaults_end = source.index("for key, default_value in SESSION_DEFAULTS.items():")
    defaults_source = source[defaults_start:defaults_end]

    forbidden_eager_calls = [
        "build_runtime_db_diagnostics(",
        "verify_qa_seed_data(",
        "generate_approved_weekly_summary(",
        "get_latest_approved_weekly_summary(",
        "save_approved_weekly_summary(",
        "api_get(",
        "api_post(",
    ]
    for term in forbidden_eager_calls:
        assert term not in defaults_source


def test_developer_tab_keeps_expensive_work_button_driven() -> None:
    developer_source = _function_source("render_developer_section")
    weekly_source = _function_source("render_weekly_coach_summary_developer_inspection")
    runtime_source = _function_source("render_runtime_db_source_verification")

    assert "Developer tools are lazy-loaded" in developer_source
    assert "render_runtime_db_source_verification()" in developer_source
    assert (
        "render_weekly_coach_summary_developer_inspection(user_id)" in developer_source
    )
    assert weekly_source.index(
        "Generate deterministic weekly summary from selected QA range"
    ) < weekly_source.index("generate_approved_weekly_summary(context)")
    assert runtime_source.index(
        "Refresh runtime / DB diagnostics"
    ) < runtime_source.index("build_runtime_db_diagnostics")


def test_latency_changes_do_not_add_provider_or_raw_debug_leakage() -> None:
    combined = "\n".join(
        [
            _function_source("render_developer_section"),
            _function_source("render_runtime_db_source_verification"),
            _function_source("_render_developer_mode_latency_timing"),
        ]
    )

    forbidden = [
        "call_ollama",
        "CrewAI",
        "qwen2.5",
        "qwen3",
        "raw_provider_output",
        "rejected_provider_output",
        "full_prompt",
        "raw_context",
        "scratchpad",
        "chain_of_thought",
    ]
    for term in forbidden:
        assert term not in combined
