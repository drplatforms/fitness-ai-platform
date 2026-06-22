from __future__ import annotations

import ast
from pathlib import Path

STREAMLIT_DAILY_COACH_NARRATIVE_NAMES = {
    "DAILY_COACH_NARRATIVE_LANES",
    "daily_coach_narrative_lane_labels",
    "daily_coach_narrative_lane_key_from_label",
    "build_daily_coach_narrative_preview_params",
    "daily_coach_narrative_request_timeout",
    "daily_coach_narrative_lane_warning",
    "daily_coach_narrative_fallback_display",
    "daily_coach_narrative_approved_display",
}


def load_daily_coach_narrative_helpers() -> dict:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    helper_nodes = []

    for node in module.body:
        if isinstance(node, ast.Assign):
            names = [
                target.id for target in node.targets if isinstance(target, ast.Name)
            ]
            if any(name in STREAMLIT_DAILY_COACH_NARRATIVE_NAMES for name in names):
                helper_nodes.append(node)
        elif (
            isinstance(node, ast.FunctionDef)
            and node.name in STREAMLIT_DAILY_COACH_NARRATIVE_NAMES
        ):
            helper_nodes.append(node)

    namespace: dict = {}
    compiled = ast.Module(body=helper_nodes, type_ignores=[])
    ast.fix_missing_locations(compiled)
    exec(compile(compiled, "ui/streamlit_app.py", "exec"), namespace)
    return namespace


def test_daily_coach_narrative_lane_selector_has_four_accepted_lanes() -> None:
    helpers = load_daily_coach_narrative_helpers()

    assert helpers["daily_coach_narrative_lane_labels"]() == [
        "Deterministic fallback",
        "Fast preview: qwen3:8b",
        "Premium preview: qwen3:32b",
        "Baseline/regression: qwen2.5:3b",
    ]


def test_daily_coach_narrative_deterministic_lane_uses_no_model() -> None:
    helpers = load_daily_coach_narrative_helpers()

    params = helpers["build_daily_coach_narrative_preview_params"]("deterministic")

    assert params == {"provider": "deterministic"}
    assert helpers["daily_coach_narrative_request_timeout"]("deterministic") == 120.0


def test_daily_coach_narrative_provider_lanes_use_expected_models() -> None:
    helpers = load_daily_coach_narrative_helpers()

    fast_params = helpers["build_daily_coach_narrative_preview_params"]("qwen3_8b_fast")
    premium_params = helpers["build_daily_coach_narrative_preview_params"](
        "qwen3_32b_premium"
    )
    baseline_params = helpers["build_daily_coach_narrative_preview_params"](
        "qwen25_3b_baseline"
    )

    assert fast_params == {
        "provider": "direct_ollama",
        "model": "qwen3:8b",
        "timeout_seconds": 180,
    }
    assert premium_params == {
        "provider": "direct_ollama",
        "model": "qwen3:32b",
        "timeout_seconds": 420,
    }
    assert baseline_params == {
        "provider": "direct_ollama",
        "model": "qwen2.5:3b",
        "timeout_seconds": 180,
    }


def test_daily_coach_narrative_premium_lane_warns_about_runtime() -> None:
    helpers = load_daily_coach_narrative_helpers()

    warning = helpers["daily_coach_narrative_lane_warning"]("qwen3_32b_premium")

    assert warning is not None
    assert "may take several minutes" in warning
    assert "deterministic fallback remains available" in warning
    assert (
        helpers["daily_coach_narrative_request_timeout"]("qwen3_32b_premium") == 450.0
    )


def test_daily_coach_narrative_preview_copy_helpers_hide_missing_narrative() -> None:
    helpers = load_daily_coach_narrative_helpers()

    assert (
        helpers["daily_coach_narrative_fallback_display"]({})
        == "Deterministic fallback narrative is not available yet."
    )
    assert (
        helpers["daily_coach_narrative_approved_display"]({"approved_narrative": None})
        == {}
    )


def test_daily_coach_async_lifecycle_developer_panel_is_present_and_manual() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")

    assert "Developer Prototype: Async Daily Coach Lifecycle" in source
    assert "Create async job shell" in source
    assert "Inspect latest async job shell" in source
    assert "Run lifecycle simulation" in source
    assert "No provider is called" in source
    assert "normal Today behavior is unchanged" in source
    assert "/async-narrative/developer/jobs" in source
