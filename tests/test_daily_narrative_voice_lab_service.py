from __future__ import annotations

from services.daily_narrative_voice_lab_service import (
    build_all_daily_narrative_voice_lab_results,
    build_daily_narrative_voice_lab_result,
    daily_narrative_voice_lab_quality_hits,
    list_daily_narrative_voice_lab_scenarios,
)

REQUIRED_SCENARIOS = {
    "no_data_today",
    "nutrition_present_training_missing",
    "training_present_nutrition_missing",
    "recovery_present_training_planned",
    "high_soreness_lower_body_planned",
    "workout_completed_no_sets",
    "rich_day_multiple_domains",
    "mixed_signals_day",
    "low_data_multiple_domains",
    "chaotic_logging_week",
    "consistent_nutrition_no_training",
    "planned_workout_missed",
}


def test_voice_lab_synthetic_scenario_fixtures_load_deterministically() -> None:
    scenarios = list_daily_narrative_voice_lab_scenarios()
    scenario_ids = {scenario.scenario_id for scenario in scenarios}

    assert REQUIRED_SCENARIOS <= scenario_ids
    assert len(scenario_ids) == len(scenarios)
    assert all(scenario.reason_codes for scenario in scenarios)
    assert all(scenario.desired_coaching_angle for scenario in scenarios)


def test_voice_lab_outputs_public_safe_candidates_without_known_bad_phrases() -> None:
    results = build_all_daily_narrative_voice_lab_results()

    assert results
    for result in results:
        serialized = str(result.to_dict()).lower()
        assert "raw row" not in serialized
        assert "raw food" not in serialized
        assert "check-in notes" not in serialized
        assert "workout set rows" not in serialized
        assert "secret" not in serialized
        assert result.provider_call_required is False
        assert result.public_safe is True
        for candidate in result.candidates:
            assert candidate.banned_phrase_hits == ()
            assert candidate.awkward_phrase_hits == ()
            assert "selected date" not in candidate.body.lower()
            assert "concrete anchor" not in candidate.body.lower()
            assert "light read" not in candidate.body.lower()
            assert "useful move" not in candidate.body.lower()


def test_voice_lab_copy_families_are_adaptive_by_scenario() -> None:
    no_data = build_daily_narrative_voice_lab_result("no_data_today")
    low_data = build_daily_narrative_voice_lab_result("low_data_multiple_domains")
    rich = build_daily_narrative_voice_lab_result("rich_day_multiple_domains")
    nutrition_only = build_daily_narrative_voice_lab_result(
        "nutrition_present_training_missing"
    )

    families = {
        no_data.candidates[0].copy_family,
        low_data.candidates[0].copy_family,
        rich.candidates[0].copy_family,
        nutrition_only.candidates[0].copy_family,
    }
    bodies = {
        no_data.candidates[0].body,
        low_data.candidates[0].body,
        rich.candidates[0].body,
        nutrition_only.candidates[0].body,
    }

    assert len(families) == 4
    assert len(bodies) == 4
    assert "nutrition-based read" in nutrition_only.candidates[0].body
    assert "compare the day" in rich.candidates[0].body


def test_voice_lab_quality_hits_surface_rejected_user_language() -> None:
    hits = daily_narrative_voice_lab_quality_hits(
        "Add one concrete anchor because there is not enough signal for the selected date."
    )

    assert "concrete anchor" in hits["awkward_phrase_hits"]
    assert "selected date" in hits["awkward_phrase_hits"]
    assert "not enough signal" in hits["awkward_phrase_hits"]
