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
    "adding random data",
    "random data",
    "before you treat the plan as automatic",
}

DAILY_NARRATIVE_AWKWARD_COPY_FRAGMENTS = {
    "selected date",
    "because the selected date",
    "selected range",
    "not enough signal",
    "signal for the",
    "concrete anchor",
    "light read",
    "verify the daily picture",
    "nutrition note",
    "food-context note",
    "because there is",
    "because nutrition",
}

DAILY_NARRATIVE_VOICE_GOOD_EXAMPLES = (
    (
        "I see food logged today, but no workout. That means this can be a "
        "nutrition-based read, not a full training recommendation."
    ),
    (
        "Training is logged, but food is missing. Add one meal or snack so the "
        "coach can connect the work you did with how you fueled it."
    ),
    (
        "Today's advice is limited. Log a recovery check-in, a meal or snack, or "
        "the workout you completed so the coach has enough to work with."
    ),
    (
        "You have enough logged to review the day before adding more entries. "
        "Check whether training, food, and recovery point in the same direction "
        "before making a stronger call."
    ),
)

DAILY_NARRATIVE_VOICE_BAD_EXAMPLES = (
    "Today's useful move is to log a meal or snack.",
    "This action builds a clearer picture of your nutrition state.",
    "Keep logging simple without overcomplicating it.",
    "Add one concrete anchor because there is not enough signal for the selected date.",
    "Keep the nutrition note grounded because nutrition shows up for the selected date.",
    "Verify the daily picture before drawing conclusions from this light read.",
    "You have enough logged to compare the day instead of adding random data.",
    "Use recovery before the workout before you treat the plan as automatic.",
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
    """Map selected QA facts to a more natural Daily Narrative action."""

    del selected_date, start_date, end_date
    any_entries = recovery_present or nutrition_present or training_present

    if not any_entries or data_quality_label == "insufficient":
        return DailyNarrativeCopyChoice(
            action_id="daily_narrative_qa_today_advice_limited",
            title="Today's advice is limited",
            reason=(
                "Log a recovery check-in, a meal or snack, or the workout you "
                "completed so the coach has enough to work with."
            ),
            workflow_target="daily_logging_review",
            priority=3,
            severity="info",
            copy_family="no_data_start_point",
        )

    if data_quality_label == "limited":
        return DailyNarrativeCopyChoice(
            action_id="daily_narrative_qa_get_on_same_page",
            title="Let's get on the same page",
            reason=(
                "There are a few entries here, but not enough detail for a strong "
                "coaching read. Add the easiest missing piece today so the next "
                "recommendation has more to work with."
            ),
            workflow_target="daily_logging_review",
            priority=4,
            severity="info",
            copy_family="low_data_practical_next_step",
        )

    if training_present and nutrition_present and recovery_present:
        if actual_sets_count > 0 or planned_exercises_count > 0:
            return DailyNarrativeCopyChoice(
                action_id="daily_narrative_qa_compare_the_day",
                title="Compare the day",
                reason=(
                    "You have enough logged to review the day before adding more "
                    "entries. Check whether training, food, and recovery point in "
                    "the same direction before making a stronger call."
                ),
                workflow_target="daily_grounded_review",
                priority=4,
                severity="success",
                copy_family="rich_day_interpretation",
            )
        return DailyNarrativeCopyChoice(
            action_id="daily_narrative_qa_read_what_is_there",
            title="Read what is already there",
            reason=(
                "Recovery, food, and training are all present. Use them to make "
                "one grounded read of the day instead of adding another generic "
                "logging task."
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
                "Training and food are both logged. Check whether the meals around "
                "the workout match the kind of effort you put in."
            ),
            workflow_target="daily_grounded_review",
            priority=4,
            severity="success",
            copy_family="two_domain_training_nutrition",
        )

    if training_present and not nutrition_present:
        return DailyNarrativeCopyChoice(
            action_id="daily_narrative_qa_add_food_around_workout",
            title="Add the food around the workout",
            reason=(
                "Training is logged, but food is missing. Add one meal or snack "
                "so the coach can connect the work you did with how you fueled it."
            ),
            workflow_target="nutrition_quick_log",
            priority=3,
            severity="info",
            copy_family="training_without_fueling",
        )

    if nutrition_present and not training_present:
        return DailyNarrativeCopyChoice(
            action_id="daily_narrative_qa_nutrition_based_read",
            title="Keep this nutrition-based",
            reason=(
                "I see food logged today, but no workout. That means this can be "
                "a nutrition-based read, not a full training recommendation."
            ),
            workflow_target="nutrition_context_review",
            priority=3,
            severity="info",
            copy_family="nutrition_only_read",
        )

    return DailyNarrativeCopyChoice(
        action_id="daily_narrative_qa_add_missing_training_or_food",
        title="Add what happened today",
        reason=(
            "Recovery is the only clear piece right now. Add the workout you did "
            "or one meal entry so the coach is not reading the day from how you "
            "felt alone."
        ),
        workflow_target="daily_logging_review",
        priority=3,
        severity="info",
        copy_family="single_domain_recovery_next_step",
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


def awkward_daily_narrative_phrases_found(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(
        fragment
        for fragment in DAILY_NARRATIVE_AWKWARD_COPY_FRAGMENTS
        if fragment in lowered
    )


def contains_awkward_daily_narrative_phrase(text: str) -> bool:
    return bool(awkward_daily_narrative_phrases_found(text))
