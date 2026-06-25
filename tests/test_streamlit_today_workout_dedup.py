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


def test_today_workout_panel_is_compact_and_routes_to_workout() -> None:
    today_source = _function_source("render_today_workout_panel")

    assert "Go to Workout" in today_source
    assert "Continue in Workout" in today_source
    assert 'request_main_navigation_page("Workout")' in today_source
    assert 'request_workout_flow_step("1. Plan")' in today_source
    assert "request_workout_flow_step(target_step)" in today_source


def test_today_workout_panel_no_longer_duplicates_selection_flow() -> None:
    today_source = _function_source("render_today_workout_panel")

    assert "Select This Workout" not in today_source
    assert "select_today_workout(" not in today_source
    assert "render_preview_exercise_snapshot(" not in today_source
    assert "/workout-plans/preview/" not in today_source
    assert "display_actual_set_logging(" not in today_source
    assert "display_complete_workout_control(" not in today_source


def test_top_level_navigation_supports_safe_override_from_today_buttons() -> None:
    nav_source = _function_source("render_main_navigation")

    assert "main_navigation_page_override" in nav_source
    assert "navigation_override in MAIN_NAVIGATION_PAGES" in nav_source
