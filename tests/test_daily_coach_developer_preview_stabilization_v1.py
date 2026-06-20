from __future__ import annotations

import ast
from pathlib import Path

from models.daily_coach_narrative_models import DailyCoachNarrativeContext
from services.daily_coach_narrative_preview_service import (
    PUBLIC_SAFE_FALLBACK_PROVIDER_PARSE_FAILED,
    build_daily_coach_narrative_preview,
)


def _function_source(name: str) -> str:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


def test_developer_preview_status_table_coerces_mixed_values_to_strings() -> None:
    function_source = _function_source("render_daily_coach_narrative_preview_status")

    assert "daily_coach_preview_table_value" in function_source
    assert 'status_df["Value"]' in function_source
    assert "Sanitized preview diagnostics" in function_source
    assert 'pd.DataFrame(status_rows), width="stretch"' not in function_source


def test_diagnostic_value_formatter_handles_bool_string_none_and_lists() -> None:
    namespace: dict[str, object] = {}
    source = _function_source("daily_coach_preview_table_value")
    exec(source, namespace)
    formatter = namespace["daily_coach_preview_table_value"]

    assert formatter(True) == "true"
    assert formatter(False) == "false"
    assert formatter(None) == ""
    assert formatter("direct_ollama") == "direct_ollama"
    assert formatter(["a", "b"]) == "a, b"


def test_today_section_preserves_coach_synthesis_before_grounded_recommendation() -> (
    None
):
    function_source = _function_source("render_today_section")

    synthesis_index = function_source.index(
        "render_daily_coach_synthesis_card(user_id)"
    )
    recommendation_index = function_source.index(
        "render_daily_recommendation_snapshot(user_id)"
    )
    preview_index = function_source.index(
        "render_daily_coach_narrative_developer_panel(user_id)"
    )

    assert synthesis_index < recommendation_index < preview_index


def test_coachs_read_card_is_visible_and_separate_from_developer_preview() -> None:
    synthesis_source = _function_source("render_daily_coach_synthesis_card")
    preview_source = _function_source("render_daily_coach_narrative_developer_panel")

    assert "Coach’s Read for Today" in synthesis_source
    assert "Daily Coach Synthesis" in synthesis_source
    assert "portfolio_card_html" in synthesis_source
    assert "Developer Preview: Daily Coach Narrative" not in synthesis_source
    assert "Approve for this session" not in synthesis_source
    assert "Developer Preview: Daily Coach Narrative" in preview_source


def test_normal_today_card_source_does_not_call_provider_preview() -> None:
    function_source = _function_source("render_daily_coach_today_card")

    assert "/daily-coach/{user_id}/today-card" in function_source
    assert "narrative-preview" not in function_source
    assert "provider" not in function_source.lower()
    assert "Approve for this session" not in Path("ui/streamlit_app.py").read_text(
        encoding="utf-8"
    )


def test_preview_parse_failure_returns_sanitized_developer_diagnostics(
    monkeypatch,
) -> None:
    import services.daily_coach_narrative_preview_service as preview_service

    context = DailyCoachNarrativeContext(
        user_id=102,
        date="2026-06-20",
        next_action_id="log_food",
        next_action_title="Log a meal or snack",
        next_action_reason="Nutrition state is limited until more food data is logged.",
        workflow_target="nutrition_quick_log",
        priority=1,
        severity="info",
        approved_focus="Log a meal or snack",
        confidence_language="Limited until more food data is logged.",
        approved_facts=[
            "Daily next action: Log a meal or snack",
            "Daily next action reason: Nutrition state is limited until more food data is logged.",
        ],
        approved_limitations=["Nutrition confidence is limited."],
        fallback_note="Log a meal or snack: nutrition context is limited until more food data is logged.",
    )

    monkeypatch.setattr(
        preview_service,
        "build_daily_coach_narrative_context",
        lambda user_id, target_date=None: context,
    )

    preview = build_daily_coach_narrative_preview(
        102,
        provider="direct_ollama",
        model_name="qwen2.5:3b",
        generate=lambda model, prompt, timeout_seconds, base_url: "not json",
    )

    payload = preview.to_dict()
    diagnostics = payload["developer_diagnostics"]

    assert payload["parse_success"] is False
    assert payload["validation_success"] is False
    assert payload["fallback_used"] is True
    assert payload["approved_narrative"] is None
    assert diagnostics["provider_attempted"] is True
    assert diagnostics["selected_provider"] == "direct_ollama"
    assert diagnostics["selected_model"] == "qwen2.5:3b"
    assert diagnostics["fallback_reason"] == PUBLIC_SAFE_FALLBACK_PROVIDER_PARSE_FAILED
    assert "parse_error" in diagnostics
    assert "not json" not in str(diagnostics).lower()
    assert "prompt" not in str(diagnostics).lower()
    assert "raw_output" not in str(diagnostics).lower()
