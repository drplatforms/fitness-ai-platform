from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import UTC, date, datetime
from typing import Any

from models.daily_coach_intelligence_models import DailyCoachIntelligenceSnapshot
from services.recovery_intelligence_service import build_recovery_intelligence
from services.recovery_intelligence_v2_service import build_recovery_intelligence_v2
from services.training_execution_summary_service import build_training_execution_summary
from services.workout_set_intelligence_service import build_workout_set_intelligence

DAILY_COACH_INTELLIGENCE_SNAPSHOT_VERSION = "daily_coach_intelligence_snapshot_v3"

_GAP_DATA_COMPLETENESS_STATUSES = {
    "missing",
    "limited",
    "partial",
    "pending",
    "unavailable",
}

FOUNDATION_LAYER_STATUS = {
    "recovery_intelligence": "implemented_v1",
    "recovery_intelligence_v2": "implemented_v1",
    "workout_set_intelligence": "implemented_v1",
    "trend_engine": "nutrition_trend_existing_only",
    "six_month_seed_data": "existing_qa_seed_data_only",
    "food_knowledge_expansion": "starter_catalog_existing_expansion_pending",
}


def build_daily_coach_intelligence_snapshot(
    user_id: int,
    target_date: str | None = None,
) -> DailyCoachIntelligenceSnapshot:
    """Build a read-only backend-owned source-data snapshot for Daily Coach.

    This snapshot is deterministic and does not call providers, mutate the DB,
    render Today UI, or persist provider output.
    """

    resolved_date = target_date or date.today().isoformat()
    recovery = build_recovery_intelligence(user_id=user_id, target_date=resolved_date)
    reason_codes = list(recovery.reason_codes)
    limitations = list(recovery.limitations)
    source_services = ["recovery_intelligence_service"]

    recovery_v2 = _read_recovery_intelligence_v2(
        user_id=user_id,
        target_date=resolved_date,
        reason_codes=reason_codes,
        limitations=limitations,
    )
    if recovery_v2 is not None:
        source_services.append("recovery_intelligence_v2_service")
        _extend_v2_limited_context(
            recovery_v2_dict=recovery_v2.to_dict(),
            reason_codes=reason_codes,
            limitations=limitations,
        )

    workout_set_intelligence = _read_workout_set_intelligence(
        user_id=user_id,
        target_date=resolved_date,
        reason_codes=reason_codes,
        limitations=limitations,
    )
    if workout_set_intelligence is not None:
        source_services.append("workout_set_intelligence_service")

    training_summary = _read_training_summary(user_id, reason_codes, limitations)
    if training_summary is not None:
        source_services.append("training_execution_summary_service")

    nutrition_window = _read_nutrition_trend_window(
        user_id=user_id,
        target_date=resolved_date,
        reason_codes=reason_codes,
        limitations=limitations,
    )
    if nutrition_window is not None:
        source_services.append("nutrition_trend_service")

    data_completeness = _build_data_completeness(
        recovery_dict=recovery.to_dict(),
        recovery_v2_dict=recovery_v2.to_dict() if recovery_v2 is not None else None,
        workout_set_dict=(
            workout_set_intelligence.to_dict()
            if workout_set_intelligence is not None
            else None
        ),
        training_summary=training_summary,
        nutrition_window=nutrition_window,
    )
    source_data_gaps = _build_source_data_gaps(data_completeness)
    reason_codes.extend(_reason_codes_for_gaps(data_completeness))

    return DailyCoachIntelligenceSnapshot(
        user_id=user_id,
        target_date=resolved_date,
        generated_at=datetime.now(UTC).isoformat(),
        snapshot_version=DAILY_COACH_INTELLIGENCE_SNAPSHOT_VERSION,
        source_services=source_services,
        recovery_intelligence=recovery,
        recovery_intelligence_v2=recovery_v2,
        workout_set_intelligence=workout_set_intelligence,
        training_execution_summary=training_summary,
        nutrition_trend_window=nutrition_window,
        foundation_layer_status=dict(FOUNDATION_LAYER_STATUS),
        data_completeness=data_completeness,
        source_data_gaps=source_data_gaps,
        reason_codes=_unique(reason_codes),
        limitations=_unique(limitations),
    )


def _read_recovery_intelligence_v2(
    *,
    user_id: int,
    target_date: str,
    reason_codes: list[str],
    limitations: list[str],
) -> Any | None:
    try:
        return build_recovery_intelligence_v2(
            user_id=user_id,
            target_date=target_date,
        )
    except (sqlite3.Error, ValueError):
        reason_codes.append("recovery_intelligence_v2_unavailable")
        limitations.append(
            "Recovery v2 intelligence unavailable due to a local data read issue."
        )
        return None


def _read_workout_set_intelligence(
    *,
    user_id: int,
    target_date: str,
    reason_codes: list[str],
    limitations: list[str],
) -> Any | None:
    try:
        return build_workout_set_intelligence(user_id=user_id, target_date=target_date)
    except sqlite3.Error as exc:
        reason_codes.append("workout_set_intelligence_unavailable")
        limitations.append(f"Workout set intelligence unavailable: {_safe_error(exc)}")
        return None


def _read_training_summary(
    user_id: int, reason_codes: list[str], limitations: list[str]
) -> dict[str, Any] | None:
    try:
        summary = build_training_execution_summary(user_id=user_id)
    except sqlite3.Error as exc:
        reason_codes.append("training_execution_summary_unavailable")
        limitations.append(
            f"Training execution summary unavailable: {_safe_error(exc)}"
        )
        return None
    return _to_dict(summary)


def _read_nutrition_trend_window(
    *, user_id: int, target_date: str, reason_codes: list[str], limitations: list[str]
) -> dict[str, Any] | None:
    try:
        from services.nutrition_trend_service import build_nutrition_trend_window

        window = build_nutrition_trend_window(
            user_id=user_id,
            end_date=target_date,
            window_days=14,
        )
    except (sqlite3.Error, ValueError) as exc:
        reason_codes.append("nutrition_trend_window_unavailable")
        limitations.append(f"Nutrition trend window unavailable: {_safe_error(exc)}")
        return None
    return _to_dict(window)


def _build_data_completeness(
    *,
    recovery_dict: dict[str, Any],
    recovery_v2_dict: dict[str, Any] | None,
    workout_set_dict: dict[str, Any] | None,
    training_summary: dict[str, Any] | None,
    nutrition_window: dict[str, Any] | None,
) -> dict[str, str]:
    windows = recovery_dict.get("windows") or {}
    primary = windows.get("7") or next(iter(windows.values()), {})
    recovery_status = "usable" if primary.get("checkin_days", 0) >= 3 else "limited"
    if primary.get("checkin_days", 0) == 0:
        recovery_status = "missing"

    recovery_v2_status = _recovery_v2_data_status(recovery_v2_dict)

    workout_set_status = "missing"
    if workout_set_dict is not None:
        completed = int(workout_set_dict.get("completed_execution_count") or 0)
        confidence = str(workout_set_dict.get("confidence") or "Limited")
        if completed > 0 and confidence in {"Moderate", "High"}:
            workout_set_status = "usable"
        elif completed > 0:
            workout_set_status = "limited"
        else:
            workout_set_status = "missing"

    training_status = "missing"
    if training_summary is not None:
        training_status = (
            "usable"
            if int(training_summary.get("completed_execution_count") or 0) > 0
            else "limited"
        )

    nutrition_status = "missing"
    if nutrition_window is not None:
        nutrition_status = (
            "usable"
            if int(nutrition_window.get("logged_day_count") or 0) > 0
            else "limited"
        )

    return {
        "recovery_intelligence": recovery_status,
        "recovery_intelligence_v2": recovery_v2_status,
        "workout_set_intelligence": workout_set_status,
        "training_execution_summary": training_status,
        "nutrition_trend_window": nutrition_status,
        "trend_engine": "partial_existing_nutrition_trend_only",
        "six_month_seed_data": "available_for_qa_if_seeded",
        "food_knowledge_expansion": "pending",
    }


def _recovery_v2_data_status(recovery_v2_dict: dict[str, Any] | None) -> str:
    if recovery_v2_dict is None:
        return "unavailable"
    data_quality = recovery_v2_dict.get("data_quality") or {}
    status = str(data_quality.get("status") or "limited")
    if status in {"strong", "usable"}:
        return "usable"
    if status in {"partial", "limited", "missing"}:
        return status
    return "limited"


def _extend_v2_limited_context(
    *,
    recovery_v2_dict: dict[str, Any],
    reason_codes: list[str],
    limitations: list[str],
) -> None:
    confidence = str(recovery_v2_dict.get("confidence") or "Limited")
    data_quality = recovery_v2_dict.get("data_quality") or {}
    data_status = str(data_quality.get("status") or "limited")
    if confidence not in {"Limited", "Low"} and data_status not in {
        "missing",
        "limited",
        "partial",
    }:
        return

    reason_codes.append("recovery_intelligence_v2_limited")
    limitations.append(
        "Recovery v2 intelligence is limited by available check-in data."
    )
    reason_codes.extend(
        str(code) for code in recovery_v2_dict.get("reason_codes") or []
    )
    reason_codes.extend(str(code) for code in data_quality.get("reason_codes") or [])
    limitations.extend(str(item) for item in recovery_v2_dict.get("limitations") or [])
    limitations.extend(str(item) for item in data_quality.get("limitations") or [])


def _build_source_data_gaps(data_completeness: dict[str, str]) -> list[str]:
    gaps: list[str] = []
    for layer, status in data_completeness.items():
        if status in _GAP_DATA_COMPLETENESS_STATUSES or status.startswith("not_"):
            gaps.append(f"{layer}: {status}")
    return gaps


def _reason_codes_for_gaps(data_completeness: dict[str, str]) -> list[str]:
    return [
        f"{layer}_{status}"
        for layer, status in data_completeness.items()
        if status in _GAP_DATA_COMPLETENESS_STATUSES or status.startswith("not_")
    ]


def _to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    try:
        return asdict(value)
    except TypeError:
        return dict(value)


def _safe_error(exc: Exception) -> str:
    return str(exc).replace("\n", " ")[:240]


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
