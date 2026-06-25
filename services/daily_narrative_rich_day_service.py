from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from services.qa_seed_data_verification_service import DEFAULT_QA_USER_IDS
from services.weekly_coach_summary_qa_data_service import (
    QA_USER_LABELS,
    WeeklyCoachSummaryQADataError,
    WeeklyCoachSummaryQAInventory,
    inspect_weekly_summary_qa_range,
)

DAILY_NARRATIVE_LABEL_RICH_DAY = "rich_day"
DAILY_NARRATIVE_LABEL_TRAINING_AND_NUTRITION = "training_and_nutrition_day"
DAILY_NARRATIVE_LABEL_NUTRITION_PRESENT_TRAINING_MISSING = (
    "nutrition_present_training_missing"
)
DAILY_NARRATIVE_LABEL_TRAINING_PRESENT_NUTRITION_MISSING = (
    "training_present_nutrition_missing"
)
DAILY_NARRATIVE_LABEL_RECOVERY_ONLY = "recovery_only_day"
DAILY_NARRATIVE_LABEL_LOW_DATA = "low_data_day"
DAILY_NARRATIVE_LABEL_NO_DATA = "no_data_day"


@dataclass(frozen=True)
class DailyNarrativeQANextAction:
    action_id: str
    title: str
    reason: str
    workflow_target: str
    priority: int
    severity: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyNarrativeRichDayCandidate:
    user_id: int
    scenario: str
    date: str
    start_date: str
    end_date: str
    recovery_checkins_count: int
    nutrition_entries_count: int
    nutrition_logged: bool
    workout_sessions_count: int
    workout_execution_sessions_count: int
    planned_workouts_count: int
    planned_exercises_count: int
    actual_sets_count: int
    domains_present_count: int
    data_quality_label: str
    reason_codes: tuple[str, ...]
    richness_score: int
    recommended_test_label: str
    next_action: DailyNarrativeQANextAction
    limitations: tuple[str, ...] = ()
    public_safe: bool = True
    displayable: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["next_action"] = self.next_action.to_dict()
        return payload


@dataclass(frozen=True)
class DailyNarrativeRichDayScanResult:
    start_date: str
    end_date: str
    candidates: tuple[DailyNarrativeRichDayCandidate, ...]
    top_candidates: tuple[DailyNarrativeRichDayCandidate, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "top_candidates": [
                candidate.to_dict() for candidate in self.top_candidates
            ],
        }


def summarize_daily_narrative_inventory(
    *,
    inventory: WeeklyCoachSummaryQAInventory,
    selected_date: str,
) -> DailyNarrativeRichDayCandidate:
    """Summarize selected safe QA inventory for Daily Narrative reasoning."""

    fact_counts = inventory.fact_counts
    recovery_count = int(fact_counts.get("recovery", 0))
    nutrition_count = int(fact_counts.get("nutrition", 0))
    workout_sessions_count = int(fact_counts.get("workout_sessions", 0))
    workout_execution_sessions_count = int(
        fact_counts.get("workout_execution_sessions", 0)
    )
    planned_workouts_count = int(fact_counts.get("planned_workouts", 0))
    planned_exercises_count = int(fact_counts.get("planned_workout_exercises", 0))
    actual_sets_count = int(
        fact_counts.get("actual_sets", fact_counts.get("workout_sets", 0))
    )

    recovery_present = recovery_count > 0
    nutrition_present = nutrition_count > 0
    training_present = any(
        value > 0
        for value in (
            workout_sessions_count,
            workout_execution_sessions_count,
            planned_workouts_count,
            planned_exercises_count,
            actual_sets_count,
        )
    )
    domains_present_count = sum(
        1
        for present in (recovery_present, nutrition_present, training_present)
        if present
    )
    data_quality_label, reason_codes = _daily_data_quality_label_and_reasons(
        inventory=inventory,
        recovery_present=recovery_present,
        nutrition_present=nutrition_present,
        training_present=training_present,
        domains_present_count=domains_present_count,
        actual_sets_count=actual_sets_count,
    )
    recommended_label = _recommended_test_label(
        recovery_present=recovery_present,
        nutrition_present=nutrition_present,
        training_present=training_present,
        domains_present_count=domains_present_count,
        actual_sets_count=actual_sets_count,
    )
    richness_score = _richness_score(
        recovery_present=recovery_present,
        nutrition_present=nutrition_present,
        training_present=training_present,
        planned_workouts_count=planned_workouts_count,
        planned_exercises_count=planned_exercises_count,
        actual_sets_count=actual_sets_count,
        domains_present_count=domains_present_count,
        data_quality_label=data_quality_label,
    )
    next_action = select_daily_narrative_qa_next_action(
        selected_date=selected_date,
        start_date=inventory.start_date,
        end_date=inventory.end_date,
        data_quality_label=data_quality_label,
        recovery_present=recovery_present,
        nutrition_present=nutrition_present,
        training_present=training_present,
        actual_sets_count=actual_sets_count,
        planned_exercises_count=planned_exercises_count,
    )

    return DailyNarrativeRichDayCandidate(
        user_id=inventory.user_id,
        scenario=inventory.scenario,
        date=selected_date,
        start_date=inventory.start_date,
        end_date=inventory.end_date,
        recovery_checkins_count=recovery_count,
        nutrition_entries_count=nutrition_count,
        nutrition_logged=nutrition_present,
        workout_sessions_count=workout_sessions_count,
        workout_execution_sessions_count=workout_execution_sessions_count,
        planned_workouts_count=planned_workouts_count,
        planned_exercises_count=planned_exercises_count,
        actual_sets_count=actual_sets_count,
        domains_present_count=domains_present_count,
        data_quality_label=data_quality_label,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        richness_score=richness_score,
        recommended_test_label=recommended_label,
        next_action=next_action,
        limitations=tuple(dict.fromkeys(inventory.limitations)),
    )


def scan_daily_narrative_rich_days(
    *,
    user_id: int | None = None,
    start_date: str,
    end_date: str,
    top: int = 10,
    db_path: str | Path | None = None,
) -> DailyNarrativeRichDayScanResult:
    """Rank seeded QA user/day combinations by Daily Narrative usefulness."""

    selected_start = date.fromisoformat(start_date)
    selected_end = date.fromisoformat(end_date)
    if selected_start > selected_end:
        raise WeeklyCoachSummaryQADataError(
            "start_date must be before or equal to end_date."
        )

    user_ids = (int(user_id),) if user_id is not None else tuple(DEFAULT_QA_USER_IDS)
    for qa_user_id in user_ids:
        if qa_user_id not in QA_USER_LABELS:
            raise WeeklyCoachSummaryQADataError(
                "Daily Narrative rich-day scan supports QA users 101-105 only."
            )

    candidates: list[DailyNarrativeRichDayCandidate] = []
    current = selected_start
    while current <= selected_end:
        current_text = current.isoformat()
        for qa_user_id in user_ids:
            inventory = inspect_weekly_summary_qa_range(
                user_id=qa_user_id,
                start_date=current_text,
                end_date=current_text,
                db_path=db_path,
            )
            candidates.append(
                summarize_daily_narrative_inventory(
                    inventory=inventory,
                    selected_date=current_text,
                )
            )
        current += timedelta(days=1)

    sorted_candidates = tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                candidate.richness_score,
                candidate.domains_present_count,
                candidate.actual_sets_count,
                candidate.nutrition_entries_count,
                candidate.date,
            ),
            reverse=True,
        )
    )
    bounded_top = max(1, min(int(top or 10), 50))
    return DailyNarrativeRichDayScanResult(
        start_date=selected_start.isoformat(),
        end_date=selected_end.isoformat(),
        candidates=tuple(candidates),
        top_candidates=sorted_candidates[:bounded_top],
    )


def select_daily_narrative_qa_next_action(
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
) -> DailyNarrativeQANextAction:
    """Select a deterministic Daily Narrative action from selected safe facts."""

    range_label = "selected date" if start_date == end_date else "selected range"
    if training_present and nutrition_present and recovery_present:
        if actual_sets_count > 0 or planned_exercises_count > 0:
            return DailyNarrativeQANextAction(
                action_id="daily_narrative_qa_compare_training_fueling_recovery",
                title="Compare training, fueling, and recovery",
                reason=(
                    f"Because the {range_label} has recovery, nutrition, and training facts, "
                    "the useful move is to compare effort with fueling and recovery instead "
                    "of logging another random item."
                ),
                workflow_target="daily_grounded_review",
                priority=4,
                severity="success",
            )
        return DailyNarrativeQANextAction(
            action_id="daily_narrative_qa_compare_training_and_fueling",
            title="Compare training and fueling",
            reason=(
                f"Because the {range_label} has recovery, nutrition, and training context, "
                "the useful move is to compare effort with fueling instead of defaulting "
                "to generic logging advice."
            ),
            workflow_target="daily_grounded_review",
            priority=4,
            severity="success",
        )
    if training_present and nutrition_present:
        return DailyNarrativeQANextAction(
            action_id="daily_narrative_qa_compare_training_and_fueling",
            title="Compare training and fueling",
            reason=(
                f"Because the {range_label} has both training and nutrition facts, "
                "the useful move is to connect effort with fueling instead of asking "
                "for another basic meal log."
            ),
            workflow_target="daily_grounded_review",
            priority=4,
            severity="success",
        )
    if training_present and not nutrition_present:
        return DailyNarrativeQANextAction(
            action_id="daily_narrative_qa_log_nutrition_for_training_day",
            title="Log a meal or snack",
            reason=(
                f"Because training is present but nutrition is missing for the {range_label}, "
                "one meal entry gives the coach something real to compare against the training day."
            ),
            workflow_target="nutrition_quick_log",
            priority=3,
            severity="info",
        )
    if nutrition_present and not training_present:
        return DailyNarrativeQANextAction(
            action_id="daily_narrative_qa_review_nutrition_context",
            title="Review nutrition context",
            reason=(
                f"Because nutrition is present but training is missing for the {range_label}, "
                "the useful move is to keep the day grounded without inventing a training story."
            ),
            workflow_target="nutrition_context_review",
            priority=3,
            severity="info",
        )
    if recovery_present and not nutrition_present and not training_present:
        return DailyNarrativeQANextAction(
            action_id="daily_narrative_qa_add_one_context_entry",
            title="Add one context entry",
            reason=(
                f"Because only recovery is present for the {range_label}, one food or workout "
                "detail would help connect how the day felt to what actually happened."
            ),
            workflow_target="daily_logging_review",
            priority=3,
            severity="info",
        )
    if data_quality_label == "limited":
        return DailyNarrativeQANextAction(
            action_id="daily_narrative_qa_keep_logging_simple",
            title="Keep logging simple",
            reason=(
                f"Because the {range_label} has limited data quality, the useful move is "
                "to keep logging simple before drawing stronger conclusions."
            ),
            workflow_target="daily_logging_review",
            priority=4,
            severity="info",
        )
    return DailyNarrativeQANextAction(
        action_id="daily_narrative_qa_log_missing_nutrition",
        title="Log a meal or snack",
        reason=(
            f"Because there are no nutrition entries for the {range_label} ending {selected_date}, "
            "one simple meal or snack log gives the coach something real to work from."
        ),
        workflow_target="nutrition_quick_log",
        priority=3,
        severity="info",
    )


def _daily_data_quality_label_and_reasons(
    *,
    inventory: WeeklyCoachSummaryQAInventory,
    recovery_present: bool,
    nutrition_present: bool,
    training_present: bool,
    domains_present_count: int,
    actual_sets_count: int,
) -> tuple[str, list[str]]:
    reason_codes: list[str] = [
        f"qa_scenario_{inventory.scenario}",
        f"weekly_inventory_label_{inventory.data_quality_label}",
    ]
    if recovery_present:
        reason_codes.append("recovery_present")
    else:
        reason_codes.append("recovery_missing")
    if nutrition_present:
        reason_codes.append("nutrition_present")
    else:
        reason_codes.append("nutrition_missing")
    if training_present:
        reason_codes.append("training_present")
    else:
        reason_codes.append("training_missing")
    if actual_sets_count > 0:
        reason_codes.append("actual_sets_present")
    else:
        reason_codes.append("actual_sets_missing")
    reason_codes.append(f"domains_present_{domains_present_count}")

    if inventory.scenario == "data_quality_limited":
        reason_codes.extend(["scenario_forces_caution", "daily_quality_limited"])
        if not inventory.selected_range_has_data or domains_present_count == 0:
            reason_codes.append("no_data_day")
        return "limited", reason_codes
    if not inventory.selected_range_has_data or domains_present_count == 0:
        reason_codes.extend(["no_data_day", "daily_quality_insufficient"])
        return "insufficient", reason_codes
    if domains_present_count >= 3:
        reason_codes.extend(["multi_domain_day", "daily_quality_rich"])
        return "rich", reason_codes
    if domains_present_count == 2:
        reason_codes.extend(["two_domain_day", "daily_quality_usable"])
        return "usable", reason_codes
    reason_codes.extend(["single_domain_day", "daily_quality_limited"])
    return "limited", reason_codes


def _recommended_test_label(
    *,
    recovery_present: bool,
    nutrition_present: bool,
    training_present: bool,
    domains_present_count: int,
    actual_sets_count: int,
) -> str:
    if domains_present_count == 0:
        return DAILY_NARRATIVE_LABEL_NO_DATA
    if domains_present_count >= 3:
        return DAILY_NARRATIVE_LABEL_RICH_DAY
    if training_present and nutrition_present:
        return DAILY_NARRATIVE_LABEL_TRAINING_AND_NUTRITION
    if nutrition_present and not training_present:
        return DAILY_NARRATIVE_LABEL_NUTRITION_PRESENT_TRAINING_MISSING
    if training_present and not nutrition_present:
        return DAILY_NARRATIVE_LABEL_TRAINING_PRESENT_NUTRITION_MISSING
    if recovery_present:
        return DAILY_NARRATIVE_LABEL_RECOVERY_ONLY
    if actual_sets_count > 0:
        return DAILY_NARRATIVE_LABEL_TRAINING_PRESENT_NUTRITION_MISSING
    return DAILY_NARRATIVE_LABEL_LOW_DATA


def _richness_score(
    *,
    recovery_present: bool,
    nutrition_present: bool,
    training_present: bool,
    planned_workouts_count: int,
    planned_exercises_count: int,
    actual_sets_count: int,
    domains_present_count: int,
    data_quality_label: str,
) -> int:
    score = 0
    if recovery_present:
        score += 1
    if nutrition_present:
        score += 2
    if training_present:
        score += 2
    if planned_workouts_count > 0:
        score += 1
    if planned_exercises_count > 0:
        score += 1
    if actual_sets_count > 0:
        score += 3
    if domains_present_count >= 2:
        score += 2
    if domains_present_count >= 3:
        score += 3
    if data_quality_label == "insufficient":
        score -= 5
    if data_quality_label == "limited":
        score -= 2
    return score
