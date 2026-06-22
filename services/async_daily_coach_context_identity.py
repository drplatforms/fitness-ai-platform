from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from typing import Any

from models.async_daily_coach_narrative_models import (
    DAILY_COACH_NARRATIVE_FORBIDDEN_DIAGNOSTIC_KEYS,
    DailyCoachNarrativeContextIdentity,
)


class DailyCoachNarrativeContextHashError(ValueError):
    """Raised when context hash inputs include forbidden unsafe fields."""


def _normalize_for_stable_json(value: Any) -> Any:
    if is_dataclass(value):
        return _normalize_for_stable_json(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_for_stable_json(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_normalize_for_stable_json(item) for item in value]
    return str(value)


def _find_forbidden_keys(value: Any, *, path: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_normalized = key_text.strip().lower()
            child_path = f"{path}.{key_text}" if path else key_text
            if key_normalized in DAILY_COACH_NARRATIVE_FORBIDDEN_DIAGNOSTIC_KEYS:
                findings.append(child_path)
            findings.extend(_find_forbidden_keys(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            findings.extend(_find_forbidden_keys(item, path=child_path))
    return findings


def build_daily_coach_narrative_context_hash(context_inputs: Mapping[str, Any]) -> str:
    """Build a deterministic hash from backend-approved context identity inputs.

    The helper uses stable JSON serialization with sorted dictionary keys. It
    rejects raw prompt/output fields so future async jobs do not accidentally key
    cache/persistence behavior on unsafe provider internals.
    """

    forbidden_keys = _find_forbidden_keys(context_inputs)
    if forbidden_keys:
        raise DailyCoachNarrativeContextHashError(
            "Context hash inputs contain forbidden raw/debug fields: "
            + ", ".join(sorted(forbidden_keys))
        )

    normalized = _normalize_for_stable_json(context_inputs)
    serialized = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_daily_coach_narrative_context_identity(
    *,
    user_id: int,
    target_date: str,
    next_action_id: str,
    workflow_target: str,
    provider: str,
    model: str,
    prompt_contract_version: str,
    validator_version: str,
    approved_context_inputs: Mapping[str, Any],
) -> DailyCoachNarrativeContextIdentity:
    """Create a context identity with a deterministic approved-context hash."""

    context_hash = build_daily_coach_narrative_context_hash(
        {
            "user_id": user_id,
            "target_date": target_date,
            "next_action_id": next_action_id,
            "workflow_target": workflow_target,
            "provider": provider,
            "model": model,
            "prompt_contract_version": prompt_contract_version,
            "validator_version": validator_version,
            "approved_context_inputs": approved_context_inputs,
        }
    )
    return DailyCoachNarrativeContextIdentity(
        user_id=user_id,
        target_date=target_date,
        next_action_id=next_action_id,
        workflow_target=workflow_target,
        provider=provider,
        model=model,
        prompt_contract_version=prompt_contract_version,
        validator_version=validator_version,
        context_hash=context_hash,
    )
