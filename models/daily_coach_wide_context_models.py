from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

DailyCoachWideContextProvider = Literal["deterministic", "direct_ollama", "openai"]
DailyCoachWideContextVariantId = Literal[
    "current_narrow_path",
    "wide_context_minimal_prompt",
    "wide_context_practical_coach",
    "wide_context_direct_coach",
    "wide_context_no_style_guidance",
]


@dataclass(frozen=True)
class DailyCoachWideContextPacket:
    """Sanitized backend-approved context packet for ceiling-trial writers."""

    packet_version: str
    user_id: int
    date: str
    scenario_id: str
    day_context: dict[str, Any] = field(default_factory=dict)
    available_daily_data: tuple[str, ...] = field(default_factory=tuple)
    missing_daily_data: tuple[str, ...] = field(default_factory=tuple)
    profile_context: dict[str, Any] = field(default_factory=dict)
    nutrition_context: dict[str, Any] = field(default_factory=dict)
    food_choices: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    training_context: dict[str, Any] = field(default_factory=dict)
    recovery_context: dict[str, Any] = field(default_factory=dict)
    allowed_interpretations: tuple[str, ...] = field(default_factory=tuple)
    blocked_interpretations: tuple[str, ...] = field(default_factory=tuple)
    display_policy: dict[str, Any] = field(default_factory=dict)
    context_sources: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachWideContextPromptVariant:
    variant_id: DailyCoachWideContextVariantId
    label: str
    purpose: str
    writer_instruction: str
    uses_wide_context: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachWideContextProviderCallResult:
    raw_text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cached_input_tokens: int | None = None
    estimated_cost_usd: float | None = None
    cost_estimate_basis: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachWideContextDraftResult:
    scenario_id: str
    user_id: int
    date: str
    provider: DailyCoachWideContextProvider
    model: str | None
    variant_id: DailyCoachWideContextVariantId
    skipped: bool
    skip_reason: str | None
    first_pass_draft: str
    writer_prompt: str | None
    deterministic_baseline: str
    current_narrow_path_output: str | None
    wide_context_packet: DailyCoachWideContextPacket | None
    runtime_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["wide_context_packet"] = (
            self.wide_context_packet.to_dict() if self.wide_context_packet else None
        )
        return payload


@dataclass(frozen=True)
class DailyCoachWideContextTrialRunResult:
    run_id: str
    scenario_id: str
    user_id: int
    date: str
    provider: DailyCoachWideContextProvider
    model: str | None
    variants: tuple[DailyCoachWideContextDraftResult, ...]
    baseline_drift: dict[str, Any]
    runtime_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["variants"] = [variant.to_dict() for variant in self.variants]
        return payload
