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


def test_runtime_diagnostics_panel_is_developer_mode_gated() -> None:
    panel_source = _function_source("render_runtime_db_source_verification")
    developer_source = _function_source("render_developer_section")

    assert "Runtime / DB Source Verification" in panel_source
    assert 'if not st.session_state.get("developer_mode", False):' in panel_source
    assert "render_runtime_db_source_verification()" in developer_source
    assert "Refresh runtime / DB diagnostics" in panel_source


def test_runtime_diagnostics_panel_not_in_normal_today_ui() -> None:
    today_source = _function_source("render_today_section")

    assert "Runtime / DB Source Verification" not in today_source
    assert "render_runtime_db_source_verification" not in today_source


def test_runtime_diagnostics_panel_uses_safe_service_only() -> None:
    panel_source = _function_source("render_runtime_db_source_verification")

    assert "build_runtime_db_diagnostics" in panel_source
    assert "api_get" not in panel_source
    assert "api_post" not in panel_source
    assert "Ollama" not in panel_source
    assert "CrewAI" not in panel_source
    assert "qwen" not in panel_source
    assert "raw_provider_output" not in panel_source
    assert "scratchpad" not in panel_source
    assert "chain_of_thought" not in panel_source


def test_runtime_diagnostics_panel_displays_required_groups() -> None:
    panel_source = _function_source("render_runtime_db_source_verification")

    for expected in [
        "Runtime Identity",
        "Database Source",
        "Streamlit / FastAPI Context",
        "QA Seed Presence",
        "git_commit_short",
        "git_branch",
        "repository_root",
        "resolved_database_path",
        "database_exists",
        "sqlite_connectable",
    ]:
        assert expected in panel_source
