from __future__ import annotations

from dataclasses import asdict, dataclass

DAILY_NARRATIVE_BANNED_COPY_FRAGMENTS = {
    "today's useful move",
    "useful move",
    "builds a clearer picture",
    "clearer picture",
    "without overcomplicating it",
    "keep logging simple",
    "keep your food logs straightforward and basic",
    "straightforward and basic",
    "start with one entry",
}

DAILY_NARRATIVE_VOICE_GOOD_EXAMPLES = (
    (
        "Training is logged, but nutrition is blank for this date. Add one meal "
        "entry so the coach can connect effort with fueling instead of guessing."
    ),
    (
        "There is enough here for a light read, not a verdict. Training, nutrition, "
        "and recovery all show up, so check whether they tell the same story before "
        "drawing a stronger conclusion."
    ),
    (
        "I do not have enough signal to make a strong call yet. Give me one concrete "
        "anchor today: a recovery check-in, a meal, or the workout you actually did."
    ),
)

DAILY_NARRATIVE_VOICE_BAD_EXAMPLES = (
    "Today's useful move is to log a meal or snack.",
    "This action builds a clearer picture of your nutrition state.",
    "Keep logging simple without overcomplicating it.",
)


@dataclass(frozen=True)
class DailyNarrativeCopyChoice:
    action_id: str
    title: str
    reason: str
    workflow_target: str
    priority: int
    severity: str
    copy_family: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_daily_narrative_qa_copy_choice(
    *,
    selected_date: str,
    start_date: str,
    end_date: str,
    data_quality_label: str,
    recovery_present: bool,
    nutrition_present: bool,
    training_present: bool,
    actual_sets_count: int = 0,
    planned_exercises_count: int = 0,
) -> DailyNarrativeCopyChoice:
    """Map selected QA facts to a less mechanical Daily Narrative action."""

    range_label = "selected date" if start_date == end_date else "selected range"
    any_signal = recovery_present or nutrition_present or training_present

    if not any_signal or data_quality_label == "insufficient":
        return DailyNarrativeCopyChoice(
            action_id="daily_narrative_qa_add_one_anchor",
            title="Add one concrete anchor",
            reason=(
                f"Because there is not enough signal for the {range_label} ending "
                f"{selected_date} to coach from yet. Add the easiest concrete "
                "anchor now: a recovery check-in, one meal entry, or the workout "
                "you actually completed."
            ),
            workflow_target="daily_logging_review",
            priority=3,
            severity="info",
            copy_family="no_data_anchor",
        )

    if data_quality_label == "limited":
        return DailyNarrativeCopyChoice(
            action_id="daily_narrative_qa_verify_daily_picture",
            title="Verify the daily picture",
            reason=(
                f"Because the {range_label} has some signal, but it is still a light read, "
                "not a verdict. Use the available entries to spot what is missing "
                "or weak before drawing a stronger training, fueling, or recovery "
                "conclusion."
            ),
            workflow_target="daily_logging_review",
            priority=4,
            severity="info",
            copy_family="limited_data_light_read",
        )

    if training_present and nutrition_present and recovery_present:
        if actual_sets_count > 0 or planned_exercises_count > 0:
            return DailyNarrativeCopyChoice(
                action_id="daily_narrative_qa_read_training_fueling_recovery",
                title="Read the day before adding more",
                reason=(
                    f"Because the {range_label} has recovery, nutrition, and training "
                    "signals. Check whether effort, fueling, and recovery tell the "
                    "same story before turning this into more logging."
                ),
                workflow_target="daily_grounded_review",
                priority=4,
                severity="success",
                copy_family="rich_day_multi_domain_read",
            )
        return DailyNarrativeCopyChoice(
            action_id="daily_narrative_qa_connect_day_signals",
            title="Connect the day's signals",
            reason=(
                f"Because the {range_label} has recovery, nutrition, and training context, "
                "Use it to make one grounded read of the day instead of defaulting "
                "to another generic logging task."
            ),
            workflow_target="daily_grounded_review",
            priority=4,
            severity="success",
            copy_family="rich_day_context_read",
        )

    if training_present and nutrition_present:
        return DailyNarrativeCopyChoice(
            action_id="daily_narrative_qa_connect_training_and_fueling",
            title="Connect training and fueling",
            reason=(
                f"Because training and nutrition both show up for the {range_label}, look "
                "at whether the meal logs support the training demand instead of "
                "adding another basic entry just to fill space."
            ),
            workflow_target="daily_grounded_review",
            priority=4,
            severity="success",
            copy_family="two_domain_training_nutrition",
        )

    if training_present and not nutrition_present:
        return DailyNarrativeCopyChoice(
            action_id="daily_narrative_qa_add_fueling_anchor",
            title="Add a fueling anchor",
            reason=(
                f"Because training is present, but nutrition is missing for the {range_label}, "
                "Add one honest meal entry so the coach can connect the work you did "
                "with the fuel around it."
            ),
            workflow_target="nutrition_quick_log",
            priority=3,
            severity="info",
            copy_family="training_present_nutrition_missing",
        )

    if nutrition_present and not training_present:
        return DailyNarrativeCopyChoice(
            action_id="daily_narrative_qa_ground_nutrition_note",
            title="Keep the nutrition note grounded",
            reason=(
                f"Because nutrition shows up, but training does not for the {range_label}, "
                "Treat this as a food-context note, not a full training read."
            ),
            workflow_target="nutrition_context_review",
            priority=3,
            severity="info",
            copy_family="nutrition_present_training_missing",
        )

    return DailyNarrativeCopyChoice(
        action_id="daily_narrative_qa_add_context_anchor",
        title="Add one concrete anchor",
        reason=(
            f"Because recovery is the only signal for the {range_label}, add either the "
            "workout you actually did or one meal entry so the day is not interpreted "
            "from how you felt alone."
        ),
        workflow_target="daily_logging_review",
        priority=3,
        severity="info",
        copy_family="single_domain_recovery_anchor",
    )


def contains_banned_daily_narrative_phrase(text: str) -> bool:
    lowered = text.lower()
    return any(
        fragment in lowered for fragment in DAILY_NARRATIVE_BANNED_COPY_FRAGMENTS
    )


def banned_daily_narrative_phrases_found(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(
        fragment
        for fragment in DAILY_NARRATIVE_BANNED_COPY_FRAGMENTS
        if fragment in lowered
    )
