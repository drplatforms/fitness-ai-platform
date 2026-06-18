from __future__ import annotations

from dataclasses import asdict, dataclass, field

DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN = "complete_recovery_checkin"
DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE = "keep_training_conservative"
DAILY_NEXT_ACTION_LOG_FOOD = "log_food"
DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS = "review_nutrition_targets"
DAILY_NEXT_ACTION_REVIEW_WORKOUT = "review_workout"
DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE = "review_report_guidance"

DAILY_NEXT_ACTION_IDS = {
    DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN,
    DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
    DAILY_NEXT_ACTION_LOG_FOOD,
    DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS,
    DAILY_NEXT_ACTION_REVIEW_WORKOUT,
    DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE,
}

DAILY_NEXT_ACTION_WORKFLOW_TARGETS = {
    "today_recovery_checkin",
    "today_recovery_aware_workout",
    "nutrition_quick_log",
    "nutrition_target_vs_actual",
    "workout_preview",
    "reports_guidance",
}

DAILY_NEXT_ACTION_SEVERITIES = {"info", "warning", "success"}


@dataclass(frozen=True)
class DailyNextAction:
    action_id: str
    title: str
    summary: str
    reason: str
    priority: int
    workflow_target: str
    severity: str
    evidence: dict[str, object] = field(default_factory=dict)
    is_available: bool = True
    blocked_reason: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
