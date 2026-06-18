from dataclasses import dataclass, field


@dataclass
class WorkoutConstraints:
    available_equipment: list[str] = field(default_factory=list)
    unavailable_equipment: list[str] = field(default_factory=list)
    preferred_movements: list[str] = field(default_factory=list)
    avoid_movements: list[str] = field(default_factory=list)
    movement_restrictions: list[str] = field(default_factory=list)
    sore_regions: list[str] = field(default_factory=list)
    recent_exercises: list[str] = field(default_factory=list)
    confidence: str = "Low"
    reason_codes: list[str] = field(default_factory=list)
