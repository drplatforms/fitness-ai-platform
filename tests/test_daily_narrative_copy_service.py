from __future__ import annotations

from services.daily_narrative_copy_service import (
    banned_daily_narrative_phrases_found,
    build_daily_narrative_qa_copy_choice,
    contains_banned_daily_narrative_phrase,
)


def _choice(**overrides):
    kwargs = {
        "selected_date": "2026-06-06",
        "start_date": "2026-06-06",
        "end_date": "2026-06-06",
        "data_quality_label": "rich",
        "recovery_present": True,
        "nutrition_present": True,
        "training_present": True,
        "actual_sets_count": 4,
        "planned_exercises_count": 4,
    }
    kwargs.update(overrides)
    return build_daily_narrative_qa_copy_choice(**kwargs)


def test_rich_day_copy_does_not_default_to_generic_logging() -> None:
    choice = _choice()
    combined = f"{choice.title} {choice.reason}".lower()

    assert choice.copy_family == "rich_day_multi_domain_read"
    assert "meal or snack" not in combined
    assert "useful move" not in combined
    assert "clearer picture" not in combined
    assert "recovery, nutrition, and training" in combined


def test_limited_data_copy_is_cautious_even_with_all_domains() -> None:
    choice = _choice(data_quality_label="limited")
    combined = f"{choice.title} {choice.reason}".lower()

    assert choice.copy_family == "limited_data_light_read"
    assert choice.title == "Verify the daily picture"
    assert "light read" in combined
    assert "not a verdict" in combined
    assert "compare training, fueling, and recovery" not in combined
    assert not contains_banned_daily_narrative_phrase(combined)


def test_no_data_copy_asks_for_one_anchor_without_banned_phrases() -> None:
    choice = _choice(
        data_quality_label="insufficient",
        recovery_present=False,
        nutrition_present=False,
        training_present=False,
        actual_sets_count=0,
        planned_exercises_count=0,
    )
    combined = f"{choice.title} {choice.reason}".lower()

    assert choice.copy_family == "no_data_anchor"
    assert "concrete anchor" in combined
    assert "meal entry" in combined
    assert not contains_banned_daily_narrative_phrase(combined)


def test_reason_families_change_with_selected_facts() -> None:
    rich = _choice()
    limited = _choice(data_quality_label="limited")
    no_data = _choice(
        data_quality_label="insufficient",
        recovery_present=False,
        nutrition_present=False,
        training_present=False,
        actual_sets_count=0,
        planned_exercises_count=0,
    )

    assert len({rich.copy_family, limited.copy_family, no_data.copy_family}) == 3
    assert len({rich.reason, limited.reason, no_data.reason}) == 3


def test_banned_phrase_detector_flags_mechanical_copy() -> None:
    text = (
        "Today's useful move is to build a clearer picture without overcomplicating it."
    )

    found = banned_daily_narrative_phrases_found(text)

    assert "today's useful move" in found
    assert "useful move" in found
    assert "clearer picture" in found
    assert "without overcomplicating it" in found
