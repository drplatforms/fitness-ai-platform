from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class WeeklyCoachSummaryProviderModelError(ValueError):
    """Raised when future provider contract data is unsafe or invalid."""


class ProviderConfidenceLabel(StrEnum):
    """Provider-facing confidence labels must match bounded summary language."""

    LIMITED = "Limited"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"


class ProviderValidationStatus(StrEnum):
    """Future provider validator status vocabulary."""

    NOT_ATTEMPTED = "not_attempted"
    APPROVED = "approved"
    REJECTED = "rejected"


APPROVED_WEEKLY_PROVIDER_MODEL = "qwen2.5:3b"
WEEKLY_PROVIDER_CONTEXT_SOURCE = "qa_date_range_debug"

WEEKLY_PROVIDER_ALLOWED_INPUT_FIELDS: tuple[str, ...] = (
    "user_id",
    "scenario",
    "start_date",
    "end_date",
    "source",
    "confidence",
    "data_quality_label",
    "limitations",
    "reason_codes",
    "fact_counts",
    "safe_recovery_summary",
    "safe_nutrition_summary",
    "safe_training_summary",
    "deterministic_baseline_summary",
    "voice_contract",
    "output_schema_name",
)

WEEKLY_PROVIDER_FORBIDDEN_INPUT_FIELDS: tuple[str, ...] = (
    "raw_db_rows",
    "raw_database_rows",
    "raw_food_logs",
    "raw_food_descriptions",
    "raw_daily_checkin_notes",
    "raw_workout_set_rows",
    "raw_sql",
    "secrets",
    "environment_values",
    "prompt",
    "raw_prompt",
    "full_prompt",
    "raw_context",
    "scratchpad",
    "chain_of_thought",
    "hidden_instructions",
    "provider_raw_output",
    "raw_provider_output",
    "rejected_provider_output",
)

WEEKLY_PROVIDER_REQUIRED_OUTPUT_FIELDS: tuple[str, ...] = (
    "title",
    "summary",
    "recovery_note",
    "nutrition_note",
    "training_note",
    "next_action",
    "confidence_label",
    "data_limitations",
    "facts_used",
    "safety_flags",
    "provider_model",
    "source_context_metadata",
    "generated_at",
)

WEEKLY_PROVIDER_FORBIDDEN_LANGUAGE: tuple[str, ...] = (
    "chain of thought",
    "scratchpad",
    "as an ai language model",
    "i do not have access",
    "you failed",
    "lack of discipline",
    "burn this off",
    "compensate tomorrow",
    "medical diagnosis",
    "clinically diagnosed",
    "guaranteed",
    "optimized",
    "perfect recovery",
)

WEEKLY_PROVIDER_VOICE_CONTRACT: tuple[str, ...] = (
    "warm but not cheesy",
    "plainspoken",
    "coach-like, not clinical",
    "specific to the facts",
    "grounded in because",
    "no fake hype",
    "no guilt or shame",
    "no vague wellness jargon",
    "one clear next move",
    "confidence matches data quality",
)


def weekly_provider_output_json_schema() -> dict[str, Any]:
    """Return the future qwen JSON-only output contract.

    This is design scaffolding only. It does not call a provider, parse live
    model output from Ollama, or authorize runtime execution.
    """

    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(WEEKLY_PROVIDER_REQUIRED_OUTPUT_FIELDS),
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 90},
            "summary": {"type": "string", "minLength": 1, "maxLength": 900},
            "recovery_note": {"type": "string", "minLength": 1, "maxLength": 500},
            "nutrition_note": {"type": "string", "minLength": 1, "maxLength": 500},
            "training_note": {"type": "string", "minLength": 1, "maxLength": 500},
            "next_action": {"type": "string", "minLength": 1, "maxLength": 280},
            "confidence_label": {
                "type": "string",
                "enum": [label.value for label in ProviderConfidenceLabel],
            },
            "data_limitations": {"type": "array", "items": {"type": "string"}},
            "facts_used": {"type": "array", "items": {"type": "string"}},
            "safety_flags": {"type": "array", "items": {"type": "string"}},
            "provider_model": {
                "type": "string",
                "const": APPROVED_WEEKLY_PROVIDER_MODEL,
            },
            "source_context_metadata": {"type": "object"},
            "generated_at": {"type": "string"},
        },
    }


def provider_input_contract_summary() -> dict[str, Any]:
    """Return safe provider-input design metadata for docs/tests."""

    return {
        "allowed_source": "WeeklyCoachSummaryContext",
        "allowed_fields": list(WEEKLY_PROVIDER_ALLOWED_INPUT_FIELDS),
        "forbidden_fields": list(WEEKLY_PROVIDER_FORBIDDEN_INPUT_FIELDS),
        "provider_model": APPROVED_WEEKLY_PROVIDER_MODEL,
        "provider_runtime_execution_authorized": False,
        "raw_rows_allowed": False,
        "prompt_or_scratchpad_allowed": False,
        "normal_ui_allowed": False,
    }


def assert_provider_input_is_design_safe(payload: dict[str, Any]) -> None:
    """Validate future provider input contract shape without calling a provider."""

    flattened_keys = _flatten_keys(payload)
    forbidden = set(flattened_keys).intersection(WEEKLY_PROVIDER_FORBIDDEN_INPUT_FIELDS)
    if forbidden:
        raise WeeklyCoachSummaryProviderModelError(
            f"Provider input contains forbidden fields: {sorted(forbidden)}"
        )
    unknown_top_level = set(payload).difference(WEEKLY_PROVIDER_ALLOWED_INPUT_FIELDS)
    if unknown_top_level:
        raise WeeklyCoachSummaryProviderModelError(
            f"Provider input contains fields outside the approved contract: {sorted(unknown_top_level)}"
        )
    source = str(payload.get("source", ""))
    if source and source != WEEKLY_PROVIDER_CONTEXT_SOURCE:
        raise WeeklyCoachSummaryProviderModelError(
            "Provider input source must be qa_date_range_debug for the prototype design."
        )


def parse_candidate_weekly_provider_output_json(
    raw_json: str,
) -> CandidateWeeklyCoachSummaryProviderOutput:
    """Parse candidate JSON using the design contract only.

    This parser is intentionally local and deterministic. It does not execute a
    provider and does not accept markdown wrappers or freeform text.
    """

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise WeeklyCoachSummaryProviderModelError(
            "Provider output must be valid JSON."
        ) from exc
    if not isinstance(parsed, dict):
        raise WeeklyCoachSummaryProviderModelError(
            "Provider output must be a JSON object."
        )
    return CandidateWeeklyCoachSummaryProviderOutput(**parsed)


@dataclass(frozen=True)
class CandidateWeeklyCoachSummaryProviderOutput:
    """Future provider candidate shape before validation/approval.

    This class is schema/design scaffolding. Constructing it never means output
    is approved, persisted, displayed, or generated by a live provider.
    """

    title: str
    summary: str
    recovery_note: str
    nutrition_note: str
    training_note: str
    next_action: str
    confidence_label: ProviderConfidenceLabel | str
    data_limitations: tuple[str, ...] | list[str] = field(default_factory=tuple)
    facts_used: tuple[str, ...] | list[str] = field(default_factory=tuple)
    safety_flags: tuple[str, ...] | list[str] = field(default_factory=tuple)
    provider_model: str = APPROVED_WEEKLY_PROVIDER_MODEL
    source_context_metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = "not_generated_design_only"

    def __post_init__(self) -> None:
        for field_name in (
            "title",
            "summary",
            "recovery_note",
            "nutrition_note",
            "training_note",
            "next_action",
            "provider_model",
            "generated_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _bounded_text(str(getattr(self, field_name)), field_name),
            )
        try:
            confidence = ProviderConfidenceLabel(str(self.confidence_label))
        except ValueError as exc:
            raise WeeklyCoachSummaryProviderModelError(
                "confidence_label must be Limited, Low, Moderate, or High."
            ) from exc
        object.__setattr__(self, "confidence_label", confidence)
        if self.provider_model != APPROVED_WEEKLY_PROVIDER_MODEL:
            raise WeeklyCoachSummaryProviderModelError(
                "Weekly Coach Summary provider design only approves qwen2.5:3b."
            )
        object.__setattr__(
            self,
            "data_limitations",
            _safe_text_tuple(self.data_limitations, "data_limitations"),
        )
        object.__setattr__(
            self, "facts_used", _safe_text_tuple(self.facts_used, "facts_used")
        )
        object.__setattr__(
            self, "safety_flags", _safe_text_tuple(self.safety_flags, "safety_flags")
        )
        _assert_no_forbidden_keys_or_values(self.source_context_metadata)
        if not self.facts_used:
            raise WeeklyCoachSummaryProviderModelError(
                "Provider candidate must name safe facts used for grounding."
            )
        if self.confidence_label == ProviderConfidenceLabel.HIGH and any(
            "limited" in value.lower() or "sparse" in value.lower()
            for value in [*self.data_limitations, *self.safety_flags]
        ):
            raise WeeklyCoachSummaryProviderModelError(
                "High confidence is not allowed when data limitations are present."
            )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence_label"] = self.confidence_label.value
        payload["data_limitations"] = list(self.data_limitations)
        payload["facts_used"] = list(self.facts_used)
        payload["safety_flags"] = list(self.safety_flags)
        return payload


@dataclass(frozen=True)
class WeeklyCoachSummaryProviderRuntimeDesignContract:
    """Non-executing summary of the approved future runtime design."""

    provider_model: str = APPROVED_WEEKLY_PROVIDER_MODEL
    provider_execution_authorized: bool = False
    developer_mode_preview_only: bool = True
    public_default_display_authorized: bool = False
    automatic_generation_authorized: bool = False
    crewai_authorized: bool = False
    lifecycle_policy_required: bool = True
    deterministic_fallback_required: bool = True
    raw_provider_output_display_allowed: bool = False
    rejected_provider_output_persistence_allowed: bool = False

    def __post_init__(self) -> None:
        if self.provider_model != APPROVED_WEEKLY_PROVIDER_MODEL:
            raise WeeklyCoachSummaryProviderModelError(
                "Only qwen2.5:3b is approved for the future prototype design."
            )
        if self.provider_execution_authorized:
            raise WeeklyCoachSummaryProviderModelError(
                "This design milestone must not authorize provider execution."
            )
        if self.public_default_display_authorized:
            raise WeeklyCoachSummaryProviderModelError(
                "Public/default display remains deferred."
            )
        if self.crewai_authorized:
            raise WeeklyCoachSummaryProviderModelError("CrewAI remains deferred.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _bounded_text(value: str, field_name: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise WeeklyCoachSummaryProviderModelError(f"{field_name} must not be empty.")
    lowered = normalized.lower()
    for phrase in WEEKLY_PROVIDER_FORBIDDEN_LANGUAGE:
        if phrase in lowered:
            raise WeeklyCoachSummaryProviderModelError(
                f"{field_name} contains unsafe or non-public provider language."
            )
    return normalized


def _safe_text_tuple(
    values: tuple[str, ...] | list[str], field_name: str
) -> tuple[str, ...]:
    if not isinstance(values, tuple | list):
        raise WeeklyCoachSummaryProviderModelError(
            f"{field_name} must be a list/tuple of text."
        )
    return tuple(_bounded_text(str(value), field_name) for value in values)


def _flatten_keys(payload: Any) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            keys.append(str(key))
            keys.extend(_flatten_keys(value))
    elif isinstance(payload, list | tuple):
        for value in payload:
            keys.extend(_flatten_keys(value))
    return tuple(keys)


def _assert_no_forbidden_keys_or_values(payload: Any) -> None:
    flattened_keys = set(_flatten_keys(payload))
    forbidden_keys = flattened_keys.intersection(WEEKLY_PROVIDER_FORBIDDEN_INPUT_FIELDS)
    if forbidden_keys:
        raise WeeklyCoachSummaryProviderModelError(
            f"Provider output metadata contains forbidden fields: {sorted(forbidden_keys)}"
        )
    rendered = str(payload).lower()
    for forbidden in WEEKLY_PROVIDER_FORBIDDEN_INPUT_FIELDS:
        if forbidden in rendered:
            raise WeeklyCoachSummaryProviderModelError(
                "Provider output metadata contains forbidden raw context markers."
            )
