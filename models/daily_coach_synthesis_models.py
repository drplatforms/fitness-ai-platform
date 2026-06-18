from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class DailyCoachSynthesis:
    user_id: int
    synthesis_date: str
    scenario: str
    confidence: str
    today_summary: str
    recovery_signal: str
    training_signal: str
    workout_guidance: str
    execution_context: str
    logging_focus: str
    plan_fit_note: str
    recommended_focus: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
