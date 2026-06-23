from __future__ import annotations

from pathlib import Path


def test_streamlit_approved_preview_bridge_is_feature_flagged_and_secondary() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")

    assert "def render_daily_coach_async_approved_preview_bridge" in source
    assert "build_daily_coach_async_approved_preview" in source
    assert "Daily Coach Narrative Preview" in source
    assert "AI-assisted coach preview" in source
    assert "Deterministic Daily Next Action remains primary" in source
    assert (
        "render_daily_next_action_panel(user_id)\n"
        "    render_daily_coach_today_card(user_id)\n"
        "    render_daily_coach_async_approved_preview_bridge(user_id)"
    ) in source


def test_streamlit_approved_preview_bridge_does_not_expose_debug_in_normal_ui() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    start = source.index("def render_daily_coach_async_approved_preview_bridge")
    end = source.index("def render_daily_coach_async_provider_runtime_panel")
    bridge_source = source[start:end]

    assert "raw provider output" in bridge_source.lower()
    assert "rejected output" in bridge_source.lower()
    assert (
        "full prompts" in bridge_source.lower()
        or "full prompt" in bridge_source.lower()
    )
    assert "stack traces" in bridge_source.lower()
    assert "provider/model diagnostics" in bridge_source.lower()
    assert "call_ollama_generate" not in bridge_source
    assert "create_developer_mode_provider_runtime_job" not in bridge_source
    assert "run_daily_coach_async_provider_runtime_prototype" not in bridge_source


def test_streamlit_approved_preview_bridge_developer_diagnostics_are_gated() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    start = source.index("def render_daily_coach_async_approved_preview_bridge")
    end = source.index("def render_daily_coach_async_provider_runtime_panel")
    bridge_source = source[start:end]

    assert 'st.session_state.get("developer_mode", False)' in bridge_source
    assert "Developer details: approved preview bridge" in bridge_source
    assert "Sanitized failure only" in bridge_source
