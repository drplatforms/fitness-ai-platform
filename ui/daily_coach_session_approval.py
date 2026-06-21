from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any

DAILY_COACH_SESSION_APPROVAL_STATE_KEY = "daily_coach_session_approved_narratives"
DAILY_COACH_SESSION_APPROVAL_KEY_PREFIX = "daily_coach_session_approved_narrative"
DAILY_COACH_SESSION_APPROVAL_PROVIDER = "direct_ollama"
DAILY_COACH_SESSION_APPROVAL_MODEL = "qwen2.5:3b"


@dataclass(frozen=True)
class DailyCoachSessionApprovalEligibility:
    eligible: bool
    reasons: list[str]


def build_daily_coach_session_approval_key(
    *,
    user_id: int | str | None,
    date: str | None,
    next_action_id: str | None,
    workflow_target: str | None,
    selected_provider: str | None,
    selected_model: str | None,
) -> str:
    """Build the exact session-only key for an approved Daily Coach narrative."""

    parts = [
        DAILY_COACH_SESSION_APPROVAL_KEY_PREFIX,
        str(user_id or ""),
        str(date or ""),
        str(next_action_id or ""),
        str(workflow_target or ""),
        str(selected_provider or ""),
        str(selected_model or ""),
    ]
    return "::".join(parts)


def build_daily_coach_session_approval_key_from_preview(
    preview: Mapping[str, Any],
) -> str:
    return build_daily_coach_session_approval_key(
        user_id=preview.get("user_id"),
        date=_string_value(preview.get("date")),
        next_action_id=_string_value(preview.get("next_action_id")),
        workflow_target=_string_value(preview.get("workflow_target")),
        selected_provider=_string_value(preview.get("selected_provider")),
        selected_model=_string_value(preview.get("selected_model")),
    )


def build_daily_coach_session_approval_key_from_context(
    context: Mapping[str, Any],
) -> str:
    return build_daily_coach_session_approval_key(
        user_id=context.get("user_id"),
        date=_string_value(context.get("date")),
        next_action_id=_string_value(context.get("next_action_id")),
        workflow_target=_string_value(context.get("workflow_target")),
        selected_provider=DAILY_COACH_SESSION_APPROVAL_PROVIDER,
        selected_model=DAILY_COACH_SESSION_APPROVAL_MODEL,
    )


def daily_coach_preview_approval_eligibility(
    preview: Mapping[str, Any],
) -> DailyCoachSessionApprovalEligibility:
    """Return whether a preview may be approved for current Streamlit session only."""

    reasons: list[str] = []
    narrative = preview.get("approved_narrative")

    if preview.get("provider_enabled") is not True:
        reasons.append("Provider preview is not enabled.")
    if preview.get("provider_attempted") is not True:
        reasons.append("Provider preview was not attempted.")
    if preview.get("selected_provider") != DAILY_COACH_SESSION_APPROVAL_PROVIDER:
        reasons.append("Only direct_ollama previews can be session-approved.")
    if preview.get("selected_model") != DAILY_COACH_SESSION_APPROVAL_MODEL:
        reasons.append("Only qwen2.5:3b can be session-approved for this bridge.")
    if preview.get("parse_success") is not True:
        reasons.append("Parse must succeed before session approval.")
    if preview.get("validation_success") is not True:
        reasons.append("Validation must succeed before session approval.")
    if preview.get("approved_narrative_returned") is not True:
        reasons.append(
            "An approved narrative must be returned before session approval."
        )
    if preview.get("fallback_used") is not False:
        reasons.append("Fallback output cannot be session-approved.")
    if preview.get("fallback_reason") not in (None, ""):
        reasons.append("Fallback reason must be empty before session approval.")
    if _forbidden_debug_leaks(preview):
        reasons.append("Forbidden/debug leaks block session approval.")
    if not isinstance(narrative, Mapping) or not _string_value(
        narrative.get("coach_note")
    ):
        reasons.append("Approved narrative text is required before session approval.")

    for key in ["user_id", "date", "next_action_id", "workflow_target"]:
        if preview.get(key) in (None, ""):
            reasons.append(f"Preview is missing required context key: {key}.")

    return DailyCoachSessionApprovalEligibility(
        eligible=not reasons,
        reasons=reasons,
    )


def build_daily_coach_session_approval_record(
    preview: Mapping[str, Any],
) -> dict[str, Any]:
    eligibility = daily_coach_preview_approval_eligibility(preview)
    if not eligibility.eligible:
        raise ValueError("Daily Coach preview is not eligible for session approval.")

    narrative = preview.get("approved_narrative") or {}
    key = build_daily_coach_session_approval_key_from_preview(preview)
    return {
        "approval_key": key,
        "user_id": preview.get("user_id"),
        "date": _string_value(preview.get("date")),
        "next_action_id": _string_value(preview.get("next_action_id")),
        "next_action_title": _string_value(preview.get("next_action_title")),
        "workflow_target": _string_value(preview.get("workflow_target")),
        "selected_provider": DAILY_COACH_SESSION_APPROVAL_PROVIDER,
        "selected_model": DAILY_COACH_SESSION_APPROVAL_MODEL,
        "coach_note": _string_value(narrative.get("coach_note")),
        "key_takeaway": _string_value(narrative.get("key_takeaway")),
        "recommended_focus": _string_value(narrative.get("recommended_focus")),
        "confidence_language": _string_value(narrative.get("confidence_language")),
        "display_label": "Session-approved coach note",
        "session_only": True,
        "persisted": False,
    }


def store_daily_coach_session_approved_narrative(
    session_state: MutableMapping[str, Any],
    preview: Mapping[str, Any],
) -> dict[str, Any]:
    record = build_daily_coach_session_approval_record(preview)
    approvals = session_state.setdefault(DAILY_COACH_SESSION_APPROVAL_STATE_KEY, {})
    if not isinstance(approvals, MutableMapping):
        approvals = {}
        session_state[DAILY_COACH_SESSION_APPROVAL_STATE_KEY] = approvals
    approvals[record["approval_key"]] = record
    return record


def get_daily_coach_session_approved_narrative(
    session_state: Mapping[str, Any],
    active_context: Mapping[str, Any],
) -> dict[str, Any] | None:
    approvals = session_state.get(DAILY_COACH_SESSION_APPROVAL_STATE_KEY) or {}
    if not isinstance(approvals, Mapping):
        return None

    key = build_daily_coach_session_approval_key_from_context(active_context)
    record = approvals.get(key)
    if not isinstance(record, Mapping):
        return None

    if not _record_matches_context(record, active_context):
        return None
    return dict(record)


def clear_daily_coach_session_approved_narrative(
    session_state: MutableMapping[str, Any],
    approval_key: str,
) -> None:
    approvals = session_state.get(DAILY_COACH_SESSION_APPROVAL_STATE_KEY) or {}
    if isinstance(approvals, MutableMapping):
        approvals.pop(approval_key, None)


def _record_matches_context(
    record: Mapping[str, Any],
    context: Mapping[str, Any],
) -> bool:
    expected = {
        "user_id": context.get("user_id"),
        "date": _string_value(context.get("date")),
        "next_action_id": _string_value(context.get("next_action_id")),
        "workflow_target": _string_value(context.get("workflow_target")),
        "selected_provider": DAILY_COACH_SESSION_APPROVAL_PROVIDER,
        "selected_model": DAILY_COACH_SESSION_APPROVAL_MODEL,
    }
    return all(record.get(key) == value for key, value in expected.items())


def _forbidden_debug_leaks(preview: Mapping[str, Any]) -> list[Any]:
    leaks = preview.get("forbidden_debug_leaks")
    if leaks:
        return list(leaks) if isinstance(leaks, list | tuple | set) else [leaks]

    diagnostics = preview.get("developer_diagnostics") or {}
    if isinstance(diagnostics, Mapping):
        diagnostic_leaks = diagnostics.get("forbidden_debug_leaks")
        if diagnostic_leaks:
            return (
                list(diagnostic_leaks)
                if isinstance(diagnostic_leaks, list | tuple | set)
                else [diagnostic_leaks]
            )
    return []


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
