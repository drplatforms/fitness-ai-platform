from dataclasses import dataclass, field


@dataclass
class CoachingDecision:
    scenario: str
    primary_focus: str
    training_action: str
    nutrition_action: str
    sleep_action: str
    monitoring_action: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
