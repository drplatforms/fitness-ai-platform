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


def _main_navigation_block() -> str:
    source = _source()
    start = source.index("# Main Navigation")
    end = source.index("# Portfolio visual tightening")
    return source[start:end]


def test_top_level_navigation_does_not_use_eager_streamlit_tabs() -> None:
    nav_source = _function_source("render_main_navigation")
    nav_block = _main_navigation_block()

    assert "st.radio(" in nav_source
    assert "st.tabs(" not in nav_block
    assert ") = st.tabs(" not in nav_block
    assert "with today_tab:" not in nav_block
    assert "with workout_tab:" not in nav_block
    assert "with history_tab:" not in nav_block


def test_top_level_navigation_renders_only_selected_page_branch() -> None:
    nav_source = _function_source("render_main_navigation")

    assert "selected_page = st.radio(" in nav_source
    assert 'if selected_page == "Today":' in nav_source
    assert 'elif selected_page == "Workout":' in nav_source
    assert 'elif selected_page == "Nutrition":' in nav_source
    assert 'elif selected_page == "History":' in nav_source
    assert 'elif selected_page == "Reports":' in nav_source
    assert 'elif selected_page == "Developer":' in nav_source

    assert nav_source.count("render_today_section(user_id)") == 1
    assert nav_source.count("render_workout_plan_section(user_id)") == 1
    assert nav_source.count("render_nutrition_section(user_id)") == 1
    assert nav_source.count("render_history_section(user_id)") == 1
    assert nav_source.count("render_reports_section(user_id)") == 1
    assert nav_source.count("render_developer_section(user_id)") == 1


def test_developer_page_keeps_latency_instrumentation_but_skips_other_pages() -> None:
    nav_source = _function_source("render_main_navigation")
    developer_branch = nav_source[
        nav_source.index('elif selected_page == "Developer":') :
    ]

    assert "developer_tab_container_render_start" in developer_branch
    assert "render_developer_section(user_id)" in developer_branch
    assert "developer_tab_container_render_done" in developer_branch

    assert "render_today_section(user_id)" not in developer_branch
    assert "render_workout_plan_section(user_id)" not in developer_branch
    assert "render_nutrition_section(user_id)" not in developer_branch
    assert "render_history_section(user_id)" not in developer_branch
    assert "render_reports_section(user_id)" not in developer_branch


def test_top_level_navigation_keeps_expected_pages() -> None:
    source = _source()

    assert "MAIN_NAVIGATION_PAGES" in source
    for page in ["Today", "Workout", "Nutrition", "History", "Reports", "Developer"]:
        assert f'"{page}"' in source
