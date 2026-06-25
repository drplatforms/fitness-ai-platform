from __future__ import annotations

from services.daily_narrative_rich_day_service import (
    DAILY_NARRATIVE_LABEL_NO_DATA,
    DAILY_NARRATIVE_LABEL_RICH_DAY,
    DAILY_NARRATIVE_LABEL_TRAINING_PRESENT_NUTRITION_MISSING,
    select_daily_narrative_qa_next_action,
    summarize_daily_narrative_inventory,
)
from services.weekly_coach_summary_qa_data_service import WeeklyCoachSummaryQAInventory


def _inventory(
    *,
    user_id: int = 102,
    scenario: str = "aligned_managed",
    selected_date: str = "2026-06-06",
    recovery: int = 0,
    nutrition: int = 0,
    workout_sessions: int = 0,
    workout_execution_sessions: int = 0,
    planned_workouts: int = 0,
    planned_exercises: int = 0,
    actual_sets: int = 0,
    data_quality_label: str = "usable",
) -> WeeklyCoachSummaryQAInventory:
    return WeeklyCoachSummaryQAInventory(
        user_id=user_id,
        scenario=scenario,
        start_date=selected_date,
        end_date=selected_date,
        source="qa_date_range_debug",
        user_exists=True,
        user_name=f"QA User {user_id}",
        selected_range_has_data=any(
            value > 0
            for value in (
                recovery,
                nutrition,
                workout_sessions,
                workout_execution_sessions,
                planned_workouts,
                planned_exercises,
                actual_sets,
            )
        ),
        available_start_date="2026-05-31",
        available_end_date="2026-06-06",
        data_quality_label=data_quality_label,
        diagnosis_codes=("seeded_day_test",),
        limitations=(),
        fact_counts={
            "recovery": recovery,
            "nutrition": nutrition,
            "workout_sessions": workout_sessions,
            "workout_execution_sessions": workout_execution_sessions,
            "planned_workouts": planned_workouts,
            "planned_workout_exercises": planned_exercises,
            "actual_sets": actual_sets,
        },
        fact_date_bounds={},
        distinct_logged_days={},
        completed_counts={},
    )


def test_rich_day_summary_selects_fact_based_action() -> None:
    candidate = summarize_daily_narrative_inventory(
        inventory=_inventory(
            recovery=1,
            nutrition=3,
            workout_sessions=1,
            planned_workouts=1,
            planned_exercises=4,
            actual_sets=6,
        ),
        selected_date="2026-06-06",
    )

    assert candidate.recommended_test_label == DAILY_NARRATIVE_LABEL_RICH_DAY
    assert candidate.data_quality_label == "rich"
    assert candidate.richness_score > 0
    assert candidate.next_action.title == "Read the day before adding more"
    assert "useful move" not in candidate.next_action.reason.lower()
    assert "nutrition_present" in candidate.reason_codes
    assert "training_present" in candidate.reason_codes
    assert "actual_sets_present" in candidate.reason_codes


def test_training_without_nutrition_keeps_meal_logging_grounded() -> None:
    candidate = summarize_daily_narrative_inventory(
        inventory=_inventory(
            recovery=1,
            nutrition=0,
            workout_sessions=1,
            planned_workouts=1,
            planned_exercises=4,
        ),
        selected_date="2026-06-06",
    )

    assert (
        candidate.recommended_test_label
        == DAILY_NARRATIVE_LABEL_TRAINING_PRESENT_NUTRITION_MISSING
    )
    assert candidate.next_action.title == "Add a fueling anchor"
    assert (
        "training is present, but nutrition is missing"
        in candidate.next_action.reason.lower()
    )
    assert "useful move" not in candidate.next_action.reason.lower()


def test_no_data_day_is_penalized_and_labeled() -> None:
    candidate = summarize_daily_narrative_inventory(
        inventory=_inventory(data_quality_label="insufficient"),
        selected_date="2026-06-06",
    )

    assert candidate.recommended_test_label == DAILY_NARRATIVE_LABEL_NO_DATA
    assert candidate.data_quality_label == "insufficient"
    assert candidate.richness_score < 0
    assert "no_data_day" in candidate.reason_codes


def test_low_data_scenario_remains_cautious_even_with_counts() -> None:
    candidate = summarize_daily_narrative_inventory(
        inventory=_inventory(
            user_id=105,
            scenario="data_quality_limited",
            recovery=1,
            nutrition=2,
            workout_sessions=1,
        ),
        selected_date="2026-06-06",
    )

    assert candidate.data_quality_label == "limited"
    assert candidate.next_action.title == "Verify the daily picture"
    assert "light read" in candidate.next_action.reason
    assert "scenario_forces_caution" in candidate.reason_codes


def test_next_action_does_not_default_to_meal_logging_when_nutrition_present() -> None:
    action = select_daily_narrative_qa_next_action(
        selected_date="2026-06-06",
        start_date="2026-06-06",
        end_date="2026-06-06",
        data_quality_label="rich",
        recovery_present=True,
        nutrition_present=True,
        training_present=True,
        actual_sets_count=3,
        planned_exercises_count=4,
    )

    assert action.title == "Read the day before adding more"
    assert action.workflow_target == "daily_grounded_review"
    assert "generic" not in action.title.lower()
    assert "useful move" not in action.reason.lower()
