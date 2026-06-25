from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.daily_narrative_feedback_service import (
    DailyNarrativeFeedbackInput,
    build_daily_narrative_feedback_record,
    export_daily_narrative_feedback,
    feedback_record_contains_forbidden_private_data,
    list_daily_narrative_feedback,
    save_daily_narrative_feedback,
    summarize_daily_narrative_feedback,
)


def _feedback(label: str = "bad") -> DailyNarrativeFeedbackInput:
    return DailyNarrativeFeedbackInput(
        scenario_id="recovery_present_training_planned",
        scenario_label="Recovery check-in with planned workout",
        scenario_source="synthetic",
        candidate_id="primary",
        candidate_source="deterministic",
        candidate_text=(
            "Use recovery before the workout\n\nPlan the intensity around how "
            "recovered you feel today."
        ),
        feedback_label=label,
        rejected_phrase="before you treat the plan as automatic",
        preferred_rewrite=(
            "Plan the intensity of your workout around how recovered you feel today."
        ),
        user_notes="Better, less automatic-plan language.",
        reason_codes=("recovery_present_training_planned", "completion_missing"),
        data_quality="partial",
        confidence="Low",
        domains_present=("recovery", "planned_training"),
        domains_missing=("completed_training", "nutrition"),
        coaching_angle="Use recovery as a check before training, not as a verdict.",
        copy_quality_warnings=("No provider call required.",),
    )


def test_feedback_record_can_be_created_with_context() -> None:
    record = build_daily_narrative_feedback_record(_feedback())

    assert record.feedback_id
    assert record.created_at
    assert record.feedback_label == "bad"
    assert record.scenario_id == "recovery_present_training_planned"
    assert record.candidate_text
    assert record.rejected_phrase == "before you treat the plan as automatic"
    assert "Plan the intensity" in record.preferred_rewrite
    assert record.reason_codes == (
        "recovery_present_training_planned",
        "completion_missing",
    )
    assert record.raw_data_included is False


@pytest.mark.parametrize("label", ["bad", "better", "approved"])
def test_feedback_label_accepts_bad_better_approved(label: str) -> None:
    record = build_daily_narrative_feedback_record(_feedback(label=label))

    assert record.feedback_label == label


def test_feedback_save_list_filter_and_export(tmp_path: Path) -> None:
    path = tmp_path / "daily_narrative_feedback.jsonl"
    first = save_daily_narrative_feedback(_feedback(), path=path)
    other = save_daily_narrative_feedback(
        DailyNarrativeFeedbackInput(
            **{
                **_feedback(label="approved").__dict__,
                "scenario_id": "rich_day_multiple_domains",
                "scenario_label": "Rich day with all domains",
                "rejected_phrase": "adding random data",
                "preferred_rewrite": "Use what is already logged first.",
            }
        ),
        path=path,
    )

    all_records = list_daily_narrative_feedback(path=path)
    filtered = list_daily_narrative_feedback(
        path=path, scenario_id="recovery_present_training_planned"
    )
    exported = export_daily_narrative_feedback(path=path)
    summary = summarize_daily_narrative_feedback(path=path)

    assert [record.feedback_id for record in all_records] == [
        first.feedback_id,
        other.feedback_id,
    ]
    assert [record.feedback_id for record in filtered] == [first.feedback_id]
    assert len(exported) == 2
    assert summary["count"] == 2
    assert summary["by_label"]["bad"] == 1
    assert summary["by_label"]["approved"] == 1
    assert "adding random data" in summary["recent_rejected_phrases"]


def test_feedback_storage_is_jsonl_and_public_safe(tmp_path: Path) -> None:
    path = tmp_path / "daily_narrative_feedback.jsonl"
    record = save_daily_narrative_feedback(_feedback(), path=path)

    line = path.read_text(encoding="utf-8").strip()
    payload = json.loads(line)

    assert payload["feedback_id"] == record.feedback_id
    assert payload["raw_data_included"] is False
    assert not feedback_record_contains_forbidden_private_data(record)
    serialized = json.dumps(payload).lower()
    assert "raw food" not in serialized
    assert "raw set" not in serialized
    assert "secret" not in serialized
    assert "chain-of-thought" not in serialized
    assert "scratchpad" not in serialized


def test_feedback_rejects_private_or_invalid_content() -> None:
    with pytest.raises(ValueError):
        build_daily_narrative_feedback_record(
            DailyNarrativeFeedbackInput(
                **{**_feedback().__dict__, "feedback_label": "maybe"}
            )
        )

    with pytest.raises(ValueError):
        build_daily_narrative_feedback_record(
            DailyNarrativeFeedbackInput(
                **{**_feedback().__dict__, "user_notes": "secret api_key leak"}
            )
        )
