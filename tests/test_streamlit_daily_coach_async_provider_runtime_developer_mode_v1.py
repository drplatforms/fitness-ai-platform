from __future__ import annotations

from pathlib import Path


def test_streamlit_provider_runtime_panel_is_developer_mode_only() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")

    assert "Developer Prototype: Daily Coach Async Provider Runtime" in source
    assert "def render_daily_coach_async_provider_runtime_panel" in source
    assert 'if not st.session_state.get("developer_mode", False):' in source
    assert "Run manual provider attempt" in source
    assert "Create persisted provider job" in source
    assert "Provider runtime is disabled" in source
    assert "never runs on page load" in source
    assert "no normal Today provider call" in source


def test_streamlit_provider_runtime_panel_is_visible_before_persistence_inspection() -> (
    None
):
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    expected = (
        "render_daily_coach_narrative_developer_panel(user_id)\n"
        "        render_daily_coach_async_provider_runtime_panel(user_id)\n"
        "        render_daily_coach_async_persistence_inspection_panel(user_id)"
    )

    assert expected in source


def test_streamlit_provider_runtime_does_not_expose_raw_or_rejected_output() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    panel_start = source.index("def render_daily_coach_async_provider_runtime_panel")
    panel_end = source.index(
        "def render_daily_coach_async_persistence_inspection_panel"
    )
    panel_source = source[panel_start:panel_end]

    assert "raw provider output" in panel_source.lower()
    assert "rejected_provider_output" not in panel_source
    assert "raw_provider_output" not in panel_source
    assert "full_prompt" not in panel_source
    assert "chain_of_thought" not in panel_source
