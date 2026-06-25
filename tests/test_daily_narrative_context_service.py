from __future__ import annotations

from services.daily_coach_narrative_context_service import (
    build_daily_coach_narrative_qa_preview_context,
    validate_daily_coach_narrative_context,
)


def test_daily_narrative_qa_context_includes_selected_date_provenance():
    context = build_daily_coach_narrative_qa_preview_context(
        102,
        selected_date="2026-06-06",
        lookback_days=7,
    )

    assert context.user_id == 102
    assert context.date == "2026-06-06"
    assert context.source_metadata["context_source"] == "daily_narrative_qa_preview"
    assert context.source_metadata["start_date"] == "2026-05-31"
    assert context.source_metadata["end_date"] == "2026-06-06"
    assert context.source_metadata["lookback_days"] == 7
    assert any(
        "Selected range: 2026-05-31 through 2026-06-06" in fact
        for fact in context.approved_facts
    )
    assert validate_daily_coach_narrative_context(context) == []


def test_daily_narrative_qa_context_uses_because_grounding():
    context = build_daily_coach_narrative_qa_preview_context(
        102,
        selected_date="2026-06-06",
        lookback_days=1,
    )

    assert "Because" in context.next_action_reason
    assert (
        context.fallback_note
        == f"{context.next_action_title}: {context.next_action_reason}"
    )
    assert any(
        "Grounding reason:" in fact or "Missing data reason:" in fact
        for fact in context.approved_facts
    )


def test_daily_narrative_qa_context_excludes_raw_private_details():
    context = build_daily_coach_narrative_qa_preview_context(
        105,
        selected_date="2026-06-06",
        lookback_days=7,
    )
    serialized = str(context.to_dict()).lower()

    assert "raw food" not in serialized
    assert "raw row" not in serialized
    assert "raw db" not in serialized
    assert "check-in notes" not in serialized
    assert "workout set rows" not in serialized
    assert "scratchpad" not in serialized
    assert "secret" not in serialized
    assert "qwen" not in serialized
    assert context.source_metadata["data_quality_label"] == "limited"
    assert any("limited" in item.lower() for item in context.approved_limitations)


def test_daily_narrative_qa_context_rejects_non_qa_user():
    try:
        build_daily_coach_narrative_qa_preview_context(
            1,
            selected_date="2026-06-06",
            lookback_days=1,
        )
    except ValueError as exc:
        assert "QA users 101-105" in str(exc)
    else:
        raise AssertionError("Expected QA user validation failure")


def test_internal_term_filter_does_not_flag_drawing_as_raw():
    from services.daily_coach_narrative_context_service import (
        _contains_internal_fragment,
    )

    assert not _contains_internal_fragment("before drawing stronger conclusions")
    assert not _contains_internal_fragment("Developer Mode preview")
    assert _contains_internal_fragment("raw rows")
    assert _contains_internal_fragment("provider output")
    assert _contains_internal_fragment("model metadata")
