from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class FullReportSectionDefinition:
    section_id: str
    public_display_name: str
    current_source: str
    deterministic_fallback_owner: str
    provider_status: str
    evidence_source: str
    approved_claim_source: str
    render_fields: list[str]
    metadata_fields: list[str] = field(default_factory=list)
    maturity_level: int = 0
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
