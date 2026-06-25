from __future__ import annotations

from services.daily_narrative_copy_service import (
    awkward_daily_narrative_phrases_found,
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


def _combined(choice) -> str:
    return f"{choice.title} {choice.reason}".lower()


def test_rich_day_copy_does_not_default_to_generic_logging() -> None:
    choice = _choice()
    combined = _combined(choice)

    assert choice.copy_family == "rich_day_interpretation"
    assert "meal or snack" not in combined
    assert "useful move" not in combined
    assert "clearer picture" not in combined
    assert "training load, food intake, and recovery" in combined


def test_limited_data_copy_is_practical_without_weird_debug_language() -> None:
    choice = _choice(data_quality_label="limited")
    combined = _combined(choice)

    assert choice.copy_family == "low_data_practical_next_step"
    assert choice.title == "Let's get on the same page"
    assert "not enough detail" in combined
    assert "selected date" not in combined
    assert "signal" not in combined
    assert "concrete anchor" not in combined
    assert "light read" not in combined
    assert not contains_banned_daily_narrative_phrase(combined)
    assert awkward_daily_narrative_phrases_found(combined) == []


def test_no_data_copy_asks_for_practical_update_without_banned_phrases() -> None:
    choice = _choice(
        data_quality_label="insufficient",
        recovery_present=False,
        nutrition_present=False,
        training_present=False,
        actual_sets_count=0,
        planned_exercises_count=0,
    )
    combined = _combined(choice)

    assert choice.copy_family == "no_data_start_point"
    assert choice.title == "Today's advice is limited"
    assert "recovery check-in" in combined
    assert "meal or snack" in combined
    assert "workout you completed" in combined
    assert "selected date" not in combined
    assert "signal" not in combined
    assert "concrete anchor" not in combined
    assert not contains_banned_daily_narrative_phrase(combined)


def test_nutrition_present_training_missing_uses_user_preferred_direction() -> None:
    choice = _choice(
        recovery_present=False,
        nutrition_present=True,
        training_present=False,
        actual_sets_count=0,
        planned_exercises_count=0,
    )
    combined = _combined(choice)

    assert choice.copy_family == "nutrition_only_read"
    assert "food logged today" in combined
    assert "no workout" in combined
    assert "nutrition-based read" in combined
    assert "nutrition note" not in combined
    assert "food-context note" not in combined
    assert "because" not in combined


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


def test_banned_and_awkward_phrase_detectors_flag_mechanical_copy() -> None:
    banned_text = (
        "Today's useful move is to build a clearer picture without overcomplicating it."
    )
    awkward_text = "Add one concrete anchor because there is not enough signal for the selected date."

    found = banned_daily_narrative_phrases_found(banned_text)
    awkward = awkward_daily_narrative_phrases_found(awkward_text)

    assert "today's useful move" in found
    assert "useful move" in found
    assert "clearer picture" in found
    assert "without overcomplicating it" in found
    assert "concrete anchor" in awkward
    assert "selected date" in awkward
    assert "not enough signal" in awkward


def test_random_data_and_automatic_plan_phrases_are_rejected() -> None:
    found = banned_daily_narrative_phrases_found(
        "You have enough logged to compare the day instead of adding random data. "
        "Use recovery before you treat the plan as automatic."
    )

    assert "adding random data" in found
    assert "random data" in found
    assert "before you treat the plan as automatic" in found


def test_new_user_rejected_phrases_are_flagged() -> None:
    found = banned_daily_narrative_phrases_found(
        "Let how you move decide whether the session stays heavy. "
        "Recovery does not support expended energy, but the plan is optimal results."
    )

    assert "let how you move decide" in found
    assert "session stays heavy" in found
    assert "does not support expended energy" in found
    assert "optimal results" in found


def test_rich_day_copy_uses_full_day_view_without_overclaiming() -> None:
    choice = _choice()
    combined = _combined(choice)

    assert "full-day view" in combined
    assert "training load, food intake, and recovery" in combined
    assert "stay consistent or needs a small adjustment" in combined
    assert "adding random data" not in combined
    assert "random data" not in combined
    assert "optimal results" not in combined
