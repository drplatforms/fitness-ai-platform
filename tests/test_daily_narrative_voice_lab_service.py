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
            assert "adding random data" not in candidate.body.lower()
            assert "random data" not in candidate.body.lower()
            assert "optimal results" not in candidate.body.lower()
            assert "compare training load" not in candidate.body.lower()
            assert "easiest missing piece" not in candidate.body.lower()
            assert "pretending" not in candidate.body.lower()
            assert "does not support expended energy" not in candidate.body.lower()
            assert "let how you move decide" not in candidate.body.lower()
            assert "session stays heavy" not in candidate.body.lower()
            assert (
                "before you treat the plan as automatic" not in candidate.body.lower()
            )


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
    assert "full-day view" in rich.candidates[0].body
    assert "consider training load" in rich.candidates[0].body.lower()


def test_voice_lab_quality_hits_surface_rejected_user_language() -> None:
    hits = daily_narrative_voice_lab_quality_hits(
        "Add one concrete anchor because there is not enough signal for the selected date."
    )

    assert "concrete anchor" in hits["awkward_phrase_hits"]
    assert "selected date" in hits["awkward_phrase_hits"]
    assert "not enough signal" in hits["awkward_phrase_hits"]

    revised_hits = daily_narrative_voice_lab_quality_hits(
        "Use the easiest missing piece while pretending it covers the whole plan. "
        "Do not compare training load when the copy should consider the full day."
    )
    assert "easiest missing piece" in revised_hits["awkward_phrase_hits"]
    assert "pretend" in revised_hits["awkward_phrase_hits"]
    assert "compare training load" in revised_hits["awkward_phrase_hits"]


def test_voice_lab_rich_day_uses_full_day_view_without_optimal_results() -> None:
    rich = build_daily_narrative_voice_lab_result("rich_day_multiple_domains")
    primary = rich.candidates[0]

    assert "full-day view" in primary.body
    assert "consider training load, food intake, and recovery together" in primary.body
    assert "stay consistent or needs a small adjustment" in primary.body
    assert "compare" not in primary.body.lower()
    assert "adding random data" not in primary.body.lower()
    assert "random data" not in primary.body.lower()
    assert "optimal results" not in primary.body.lower()


def test_voice_lab_recovery_planned_uses_preferred_rewrite_direction() -> None:
    recovery = build_daily_narrative_voice_lab_result(
        "recovery_present_training_planned"
    )
    primary = recovery.candidates[0]

    assert "Plan the intensity" in primary.body
    assert "before you treat the plan as automatic" not in primary.body


def test_voice_lab_high_soreness_lower_body_uses_body_reaction_language() -> None:
    result = build_daily_narrative_voice_lab_result("high_soreness_lower_body_planned")
    primary = result.candidates[0]

    assert "Keep the first sets conservative" in primary.body
    assert "let how your body reacts decide how the session progresses" in primary.body
    assert "let how you move decide" not in primary.body.lower()
    assert "session stays heavy" not in primary.body.lower()


def test_voice_lab_mixed_signals_uses_readiness_without_overclaiming() -> None:
    result = build_daily_narrative_voice_lab_result("mixed_signals_day")
    primary = result.candidates[0]

    assert "recovery is the weaker point today" in primary.body
    assert "Let readiness guide" in primary.body
    assert "recovery is the limiting factor" not in primary.body.lower()
    assert "does not support expended energy" not in primary.body.lower()
    assert "overtrained" not in primary.body.lower()


def test_voice_lab_no_data_mentions_data_for_recommendations() -> None:
    result = build_daily_narrative_voice_lab_result("no_data_today")
    primary = result.candidates[0]
    body = primary.body.lower()

    assert "recovery check-in" in body
    assert "meal/snack" in body
    assert "completed workout" in body
    assert "data" in body
    assert "recommendations" in body


def test_voice_lab_training_logged_food_missing_mentions_today_entries() -> None:
    result = build_daily_narrative_voice_lab_result(
        "training_present_nutrition_missing"
    )
    primary = result.candidates[0]
    body = primary.body.lower()

    assert "training session" in body
    assert "food entries" in body
    assert "meals or snacks" in body
    assert "today" in body


def test_voice_lab_workout_completed_no_sets_mentions_sets_reps_effort() -> None:
    result = build_daily_narrative_voice_lab_result("workout_completed_no_sets")
    primary = result.candidates[0]
    body = primary.body.lower()

    assert "sets" in body
    assert "reps" in body
    assert "effort" in body
    assert "rir" in body
    assert "progression" in body


def test_voice_lab_low_data_lists_practical_options() -> None:
    result = build_daily_narrative_voice_lab_result("low_data_multiple_domains")
    primary = result.candidates[0]
    body = primary.body.lower()

    assert "handful of entries" in body
    assert "recovery check-in" in body
    assert "meal/snack" in body
    assert "completed workout" in body
    assert "easiest missing piece" not in body


def test_voice_lab_consistent_nutrition_removes_internal_instruction_tone() -> None:
    result = build_daily_narrative_voice_lab_result("consistent_nutrition_no_training")
    primary = result.candidates[0]
    body = primary.body.lower()

    assert "food logs are present" in body
    assert "nutrition context" in body
    assert "training details" in body
    assert "pretending" not in body
    assert "debug" not in body


def test_voice_lab_scenario_specific_quality_notes_include_feedback_guidance() -> None:
    rich = build_daily_narrative_voice_lab_result("rich_day_multiple_domains")
    soreness = build_daily_narrative_voice_lab_result(
        "high_soreness_lower_body_planned"
    )
    mixed = build_daily_narrative_voice_lab_result("mixed_signals_day")

    assert any("full-day view" in note for note in rich.candidates[0].quality_notes)
    assert any(
        "body's response" in note for note in soreness.candidates[0].quality_notes
    )
    assert any(
        "physiology claims" in note for note in mixed.candidates[0].quality_notes
    )
