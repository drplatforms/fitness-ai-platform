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

    assert "get_stable_workout_plan_preview(" in source
    assert "workout_plan_preview_by_user" in source
    preview_source = _function_source("display_workout_plan_preview")

    assert "Show different exercises" in preview_source
    assert "on_click=bump_workout_preview_variation_index" in preview_source
    assert "preview_variation_index" in source
    assert "workout_plan_preview_variation_index_by_user" in source


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


def test_select_success_moves_to_active_workout_without_clearing_preview_cache() -> (
    None
):
    select_source = _function_source("select_today_workout")
    success_branch = select_source.split(
        'if select_response.get("success"):', maxsplit=1
    )[1]
    success_branch = success_branch.split(
        'st.session_state.workout_plan_action_error = "Workout plan selection failed."',
        maxsplit=1,
    )[0]

    assert 'request_workout_flow_step("2. Do Workout")' in success_branch
    assert 'request_workout_flow_step("1. Plan")' not in success_branch
    assert "st.session_state.workout_plan_preview_by_user = {}" not in success_branch
    assert "Opening the active workout" in success_branch


def test_preview_refresh_control_lives_with_exercise_preview() -> None:
    preview_source = _function_source("display_workout_plan_preview")
    exercise_section = preview_source.split(
        'st.markdown("#### Exercises")', maxsplit=1
    )[1]

    assert "Show different exercises" in exercise_section
    assert "on_click=bump_workout_preview_variation_index" in exercise_section
    assert "disabled=has_selected_workout" not in preview_source
    assert "Selected and active " in preview_source
    assert "workouts stay unchanged." in preview_source


def test_selected_workout_plan_section_does_not_render_new_preview() -> None:
    plan_source = _function_source("render_workout_plan_section")
    selected_branch = plan_source.split("if has_selected_workout:", maxsplit=1)[1]
    selected_branch = selected_branch.split("else:", maxsplit=1)[0]

    assert "render_active_plan_summary(active_plan_response)" in selected_branch
    assert "get_stable_workout_plan_preview" not in selected_branch
    assert "display_workout_plan_preview" not in selected_branch
    assert "preview refreshes" in selected_branch


def test_preview_cache_key_includes_variation_index() -> None:
    cache_source = _function_source("workout_preview_cache_key")
    stable_source = _function_source("get_stable_workout_plan_preview")
    preview_source = _function_source("display_workout_plan_preview")

    assert "preview_variation_index" in cache_source
    assert ":variation:" in cache_source
    assert "bump_workout_preview_variation_index" in preview_source
    assert "preview_variation_index=" in stable_source


def test_preview_refresh_ignores_expired_prior_uncompleted_state() -> None:
    helper_source = _function_source("has_current_workout_selection")
    plan_source = _function_source("render_workout_plan_section")

    assert "expired_uncompleted_prior" in helper_source
    assert "no_workout_today" in helper_source
    assert "return False" in helper_source
    assert "has_current_workout_selection(active_plan_response)" in plan_source
    assert "if has_selected_workout:" in plan_source
    assert (
        "display_workout_plan_preview"
        not in plan_source.split("if has_selected_workout:", maxsplit=1)[1].split(
            "else:", maxsplit=1
        )[0]
    )
