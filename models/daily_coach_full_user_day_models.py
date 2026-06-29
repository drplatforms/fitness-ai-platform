from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

DailyCoachFullUserDayProvider = Literal["deterministic", "direct_ollama", "openai"]
DailyCoachFullUserDayVariantId = Literal[
    "free_range_full_user_day_minimal",
    "free_range_full_user_day_practical_coach",
    "free_range_full_user_day_direct_coach",
    "free_range_full_user_day_strict_coach",
    "free_range_full_user_day_empathetic_coach",
    "free_range_full_user_day_hypeman_coach",
]


@dataclass(frozen=True)
class DailyCoachFullUserDayPacket:
    """Neutral structured user-day packet for free-range provider trials."""

    packet_version: str
    user_id: int
    date: str
    scenario_id: str
    user_profile: dict[str, Any] = field(default_factory=dict)
    today_context: dict[str, Any] = field(default_factory=dict)
    user_health_state_projection: dict[str, Any] = field(default_factory=dict)
    user_health_state_field_coverage: dict[str, Any] = field(default_factory=dict)
    nutrition: dict[str, Any] = field(default_factory=dict)
    food_candidates: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    ai_snack_candidates: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    macro_display_card: dict[str, Any] = field(default_factory=dict)
    food_option_card: dict[str, Any] = field(default_factory=dict)
    number_formatting: dict[str, Any] = field(default_factory=dict)
    training: dict[str, Any] = field(default_factory=dict)
    recovery: dict[str, Any] = field(default_factory=dict)
    deterministic_calculations: dict[str, Any] = field(default_factory=dict)
    do_not_infer: tuple[str, ...] = field(default_factory=tuple)
    context_sources: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachFullUserDayPromptVariant:
    variant_id: DailyCoachFullUserDayVariantId
    label: str
    purpose: str
    writer_instruction: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachFullUserDayProviderCallResult:
    raw_text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cached_input_tokens: int | None = None
    estimated_cost_usd: float | None = None
    cost_estimate_basis: str | None = None
    finish_reason: str | None = None
    completion_status: str | None = None
    max_output_tokens: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachFullUserDayDraftResult:
    scenario_id: str
    user_id: int
    date: str
    provider: DailyCoachFullUserDayProvider
    model: str | None
    variant_id: DailyCoachFullUserDayVariantId
    repeat_index: int
    skipped: bool
    skip_reason: str | None
    first_pass_draft: str
    provider_input_prompt: str | None
    full_user_day_packet: DailyCoachFullUserDayPacket | None
    runtime_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["full_user_day_packet"] = (
            self.full_user_day_packet.to_dict() if self.full_user_day_packet else None
        )
        return payload


@dataclass(frozen=True)
class DailyCoachFullUserDayTrialRunResult:
    run_id: str
    scenario_id: str
    user_id: int
    date: str
    provider: DailyCoachFullUserDayProvider
    model: str | None
    variants: tuple[DailyCoachFullUserDayDraftResult, ...]
    baseline_drift: dict[str, Any]
    runtime_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["variants"] = [variant.to_dict() for variant in self.variants]
        return payload
