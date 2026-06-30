from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from models.recovery_intelligence_models import RecoveryIntelligenceSummary


@dataclass(frozen=True)
class DailyCoachIntelligenceSnapshot:
    user_id: int
    target_date: str
    generated_at: str
    snapshot_version: str
    source_services: list[str]
    recovery_intelligence: RecoveryIntelligenceSummary
    training_execution_summary: dict[str, Any] | None
    nutrition_trend_window: dict[str, Any] | None
    foundation_layer_status: dict[str, str]
    data_completeness: dict[str, str]
    source_data_gaps: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")
        if not self.target_date:
            raise ValueError("target_date is required")
        if not self.generated_at:
            raise ValueError("generated_at is required")
        if not self.snapshot_version:
            raise ValueError("snapshot_version is required")
        if not self.source_services:
            raise ValueError("source_services are required")
        if not isinstance(self.recovery_intelligence, RecoveryIntelligenceSummary):
            raise ValueError(
                "recovery_intelligence must be a RecoveryIntelligenceSummary"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
