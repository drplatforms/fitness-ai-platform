from __future__ import annotations

from services.daily_coach_approved_brief_service import build_approved_coach_brief
from services.daily_coach_food_action_language_service import (
    food_action_language_passes,
    friendly_food_display_name,
    humanize_food_action_text,
)
from tests.test_daily_coach_approved_brief_service import FakeSynthesis, _value_context


def _brief():
    return build_approved_coach_brief(
        user_id=102,
        target_date="2026-06-05",
        scenario_id="rich_nutrition_training_recovery",
        synthesis=FakeSynthesis(),
        value_context=_value_context(),
    )


def test_food_display_language_maps_problematic_foods() -> None:
    assert friendly_food_display_name("Oats, Dry") == "oatmeal"
    assert friendly_food_display_name("Tuna, Canned in Water") == "canned tuna"


def test_food_action_language_rejects_mechanical_actions() -> None:
    brief = _brief()

    assert not food_action_language_passes(
        "Add canned tuna if protein is still short.", brief
    )
    assert not food_action_language_passes(
        "Use canned tuna if the protein gap is open.", brief
    )
    assert food_action_language_passes(
        "Eat some canned tuna if protein is still short.", brief
    )


def test_humanize_food_action_text_uses_eating_language() -> None:
    assert (
        humanize_food_action_text(
            "Add canned tuna if the protein gap is open.", _brief()
        )
        == "eat some canned tuna if protein is still short."
    )
