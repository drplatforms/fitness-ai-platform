from __future__ import annotations

import ast
import re
from pathlib import Path

STREAMLIT_SOURCE = Path("ui/streamlit_app.py")


def _source() -> str:
    return STREAMLIT_SOURCE.read_text(encoding="utf-8")


def _function_source(name: str) -> str:
    source = _source()
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


def test_substitution_flow_has_single_clear_target_selection() -> None:
    function_source = _function_source("display_substitution_candidates")

    assert "Need a swap?" in function_source
    assert "Pick the exercise you want to replace" in function_source
    assert "Choose an exercise to replace" in function_source
    assert "Replacing:" in function_source
    assert "Selected exercise" in function_source
    assert "for planned_exercise in planned_exercises" not in function_source


def test_substitution_candidates_use_user_safe_labels_and_actions() -> None:
    table_source = _function_source("display_substitution_candidate_table")
    apply_source = _function_source("display_apply_substitution_control")
    option_label_source = _function_source("substitution_candidate_option_label")

    assert "Suggested replacements" in table_source
    assert "Apply swap" in apply_source
    assert "Keep original" in apply_source
    assert "Compare more replacement options" in apply_source
    assert "Choose a replacement exercise" in apply_source
    assert "catalog_exercise_id} —" not in option_label_source
    assert "replacement_catalog_exercise_id" not in option_label_source


def test_substitution_empty_and_error_states_are_user_safe() -> None:
    display_source = _function_source("display_substitution_candidates")
    apply_source = _function_source("apply_substitution_candidate")
    table_source = _function_source("display_substitution_candidate_table")

    expected_empty_start = (
        "No replacement candidates are available for this exercise yet."
    )
    expected_empty_end = "Keep the original exercise or regenerate the workout."
    expected_error = "That swap could not be applied. Keep the original exercise or try another replacement."

    assert expected_empty_start in display_source
    assert expected_empty_end in display_source
    assert expected_empty_start in table_source
    assert expected_empty_end in table_source
    assert expected_error in apply_source
    assert "Substitution apply failed for" not in apply_source
    sanitized_apply_source = re.sub(
        r"st\.session_state\.substitution_apply_error_detail\s*=\s*\(?\s*"
        r"extract_api_error_message\(exc\)\s*\)?",
        "",
        apply_source,
    )
    assert "extract_api_error_message(exc)" not in sanitized_apply_source


def test_normal_substitution_ui_does_not_expose_raw_debug_or_provider_terms() -> None:
    normal_source = (
        _function_source("display_substitution_candidates")
        + _function_source("display_apply_substitution_control")
        + _function_source("display_substitution_candidate_table")
        + _function_source("display_active_substitution")
        + _function_source("substitution_candidate_option_label")
    )

    forbidden_user_visible_terms = [
        "substitution payload",
        "raw response",
        "Raw Apply Response",
        "workflow target",
        "qwen",
        "ollama",
        "provider",
        "model",
        "traceback",
        "stack trace",
    ]

    for term in forbidden_user_visible_terms:
        assert term.lower() not in normal_source.lower()

    option_label_source = _function_source("substitution_candidate_option_label")
    assert "catalog_exercise_id" not in option_label_source
    assert "planned_exercise_id" not in option_label_source


def test_substitution_ux_does_not_change_generation_or_algorithm_calls() -> None:
    source = _source()
    display_source = _function_source("display_substitution_candidates")
    apply_source = _function_source("apply_substitution_candidate")

    assert "/substitution-candidates" in display_source
    assert "/substitute" in apply_source
    assert "preview/{user_id}" in source
    assert "exercise_count" not in display_source
    assert "workout generation" not in display_source.lower()
    assert "scoring" not in display_source.lower()
