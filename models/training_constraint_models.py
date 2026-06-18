from dataclasses import dataclass, field


@dataclass
class TrainingConstraints:
    recommended_rir_min: int | None
    recommended_rir_max: int | None
    low_rir_guidance: str
    progression_guidance: str
    recovery_constraint: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
