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


def test_workout_plan_step_uses_stable_preview_cache() -> None:
    source = _source()
    plan_source = _function_source("render_workout_plan_section")

    assert "get_stable_workout_plan_preview(" in source
    assert "workout_plan_preview_by_user" in source
    assert "Refresh workout preview" in plan_source
    assert "force_preview_refresh" in plan_source


def test_select_this_workout_uses_visible_approved_preview_payload() -> None:
    select_source = _function_source("select_today_workout")
    plan_source = _function_source("render_workout_plan_section")

    assert '"approved_workout_plan": approved_workout_plan' in select_source
    assert 'f"/workout-plans/{user_id}/select-preview"' in select_source
    assert "approved_workout_plan=approved_workout_plan" in plan_source


def test_select_button_does_not_force_preview_generation_endpoint() -> None:
    select_source = _function_source("select_today_workout")
    preview_branch = select_source.split("if approved_workout_plan:", maxsplit=1)[1]
    exact_preview_branch = preview_branch.split("else:", maxsplit=1)[0]

    assert "/select-preview" in exact_preview_branch
    assert "/workout-plans/preview" not in exact_preview_branch
