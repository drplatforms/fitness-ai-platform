from dataclasses import dataclass, field


@dataclass
class EquipmentProfile:
    user_id: int
    training_environment: str = "unknown"
    available_equipment: list[str] = field(default_factory=list)
    unavailable_equipment: list[str] = field(default_factory=list)
    confidence: str = "Low"
    reason_codes: list[str] = field(default_factory=list)
