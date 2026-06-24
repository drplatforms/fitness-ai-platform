from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from models.weekly_coach_summary_models import WeeklyCoachSummaryContext
from services.qa_seed_data_verification_service import (
    DEFAULT_QA_USER_IDS,
    QA_USER_SCENARIOS,
    QASeedDomainSummary,
    QASeedUserSummary,
    validate_date_range,
    verify_qa_seed_data,
)

DEFAULT_QA_DATE_RANGE_USER_ID = 102
DEFAULT_QA_LOW_DATA_USER_ID = 105
DEFAULT_QA_DATE_RANGE_PRESET_KEY = "latest_seeded_week"

QA_DATE_RANGE_PRESETS: dict[str, tuple[str, str]] = {
    "latest_seeded_week": ("2026-05-31", "2026-06-06"),
    "previous_seeded_week": ("2026-05-24", "2026-05-30"),
    "recent_14_days": ("2026-05-24", "2026-06-06"),
    "recent_28_days": ("2026-05-10", "2026-06-06"),
}

QA_DATE_RANGE_PRESET_LABELS: dict[str, str] = {
    "latest_seeded_week": "Latest seeded week: 2026-05-31 through 2026-06-06",
    "previous_seeded_week": "Previous seeded week: 2026-05-24 through 2026-05-30",
    "recent_14_days": "Recent 14 days: 2026-05-24 through 2026-06-06",
    "recent_28_days": "Recent 28 days: 2026-05-10 through 2026-06-06",
    "custom": "Custom",
}

QA_USER_LABELS: dict[int, str] = {
    user_id: f"{user_id} {QA_USER_SCENARIOS.get(user_id, 'unknown')}"
    for user_id in DEFAULT_QA_USER_IDS
}


class WeeklyCoachSummaryQADataError(ValueError):
    """Raised for invalid QA date-range debug input."""


@dataclass(frozen=True)
class WeeklyCoachSummaryQAInventory:
    """Safe aggregate QA inventory for a selected user/date range."""

    user_id: int
    scenario: str
    start_date: str
    end_date: str
    source: str
    user_exists: bool
    user_name: str | None
    selected_range_has_data: bool
    available_start_date: str | None
    available_end_date: str | None
    data_quality_label: str
    diagnosis_codes: tuple[str, ...]
    limitations: tuple[str, ...]
    fact_counts: dict[str, int]
    fact_date_bounds: dict[str, dict[str, str | None]]
    distinct_logged_days: dict[str, int | None]
    completed_counts: dict[str, int | None]
    public_safe: bool = True
    displayable: bool = True
    deterministic_provider_free: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def qa_date_range_cache_key(
    user_id: int,
    start_date: date | str,
    end_date: date | str,
) -> str:
    selected_start, selected_end = validate_date_range(str(start_date), str(end_date))
    return f"user:{int(user_id)}|start:{selected_start}|end:{selected_end}"


def qa_range_preset_dates(preset_key: str) -> tuple[date, date]:
    if preset_key == "custom":
        preset_key = DEFAULT_QA_DATE_RANGE_PRESET_KEY
    if preset_key not in QA_DATE_RANGE_PRESETS:
        raise WeeklyCoachSummaryQADataError(f"Unknown QA range preset: {preset_key}")
    start_date, end_date = QA_DATE_RANGE_PRESETS[preset_key]
    return date.fromisoformat(start_date), date.fromisoformat(end_date)


def _domain_row_count(summary: QASeedDomainSummary | None) -> int:
    return int(summary.row_count or 0) if summary is not None else 0


def _domain_distinct_days(summary: QASeedDomainSummary | None) -> int | None:
    if summary is None or summary.distinct_logged_days is None:
        return None
    return int(summary.distinct_logged_days)


def _domain_completed_count(summary: QASeedDomainSummary | None) -> int | None:
    if summary is None or summary.completed_count is None:
        return None
    return int(summary.completed_count)


def _domain_bounds(summary: QASeedDomainSummary | None) -> dict[str, str | None]:
    if summary is None:
        return {"min_date": None, "max_date": None, "reason": "missing_domain"}
    return {
        "min_date": summary.min_date,
        "max_date": summary.max_date,
        "reason": summary.reason,
    }


def _available_global_bounds(user: QASeedUserSummary) -> tuple[str | None, str | None]:
    min_dates = [
        summary.min_date
        for summary in user.global_bounds.values()
        if summary.min_date is not None
    ]
    max_dates = [
        summary.max_date
        for summary in user.global_bounds.values()
        if summary.max_date is not None
    ]
    return min(min_dates) if min_dates else None, max(max_dates) if max_dates else None


def _inventory_from_user_summary(
    user: QASeedUserSummary,
    *,
    start_date: str,
    end_date: str,
) -> WeeklyCoachSummaryQAInventory:
    available_start, available_end = _available_global_bounds(user)
    fact_counts = {
        domain: _domain_row_count(summary)
        for domain, summary in user.selected_range_counts.items()
    }
    data_quality_label = user.data_quality_label
    diagnosis_codes = list(user.diagnosis_codes)
    limitations = list(user.limitations)
    if user.scenario == "data_quality_limited":
        data_quality_label = "limited"
        diagnosis_codes.append("scenario_data_quality_limited")
        limitations.append(
            "QA user is a data-quality-limited scenario; keep conclusions cautious "
            "even when selected-range counts are present."
        )
    return WeeklyCoachSummaryQAInventory(
        user_id=user.user_id,
        scenario=user.scenario,
        start_date=start_date,
        end_date=end_date,
        source="qa_date_range_debug",
        user_exists=user.user_exists,
        user_name=user.user_name,
        selected_range_has_data=any(value > 0 for value in fact_counts.values()),
        available_start_date=available_start,
        available_end_date=available_end,
        data_quality_label=data_quality_label,
        diagnosis_codes=tuple(dict.fromkeys(diagnosis_codes)),
        limitations=tuple(dict.fromkeys(limitations)),
        fact_counts=fact_counts,
        fact_date_bounds={
            domain: _domain_bounds(summary)
            for domain, summary in user.selected_range_counts.items()
        },
        distinct_logged_days={
            domain: _domain_distinct_days(summary)
            for domain, summary in user.selected_range_counts.items()
        },
        completed_counts={
            domain: _domain_completed_count(summary)
            for domain, summary in user.selected_range_counts.items()
        },
    )


def inspect_weekly_summary_qa_range(
    *,
    user_id: int,
    start_date: date | str,
    end_date: date | str,
    db_path: str | Path | None = None,
) -> WeeklyCoachSummaryQAInventory:
    selected_start, selected_end = validate_date_range(str(start_date), str(end_date))
    user_id = int(user_id)
    if user_id not in DEFAULT_QA_USER_IDS:
        raise WeeklyCoachSummaryQADataError(
            "QA Date Range Debug supports QA users 101-105 only."
        )
    report = verify_qa_seed_data(
        db_path=db_path,
        user_ids=(user_id,),
        start_date=selected_start,
        end_date=selected_end,
    )
    if not report.users:
        raise WeeklyCoachSummaryQADataError(
            "QA seed verification returned no user inventory."
        )
    return _inventory_from_user_summary(
        report.users[0],
        start_date=selected_start,
        end_date=selected_end,
    )


def _training_days_from_inventory(inventory: WeeklyCoachSummaryQAInventory) -> int:
    return max(
        inventory.fact_counts.get("workout_sessions", 0),
        inventory.fact_counts.get("workout_execution_sessions", 0),
        int(inventory.completed_counts.get("workout_execution_sessions") or 0),
    )


def _completed_workouts_from_inventory(
    inventory: WeeklyCoachSummaryQAInventory,
) -> int:
    return max(
        inventory.fact_counts.get("workout_sessions", 0),
        inventory.fact_counts.get("workout_execution_sessions", 0),
        int(inventory.completed_counts.get("workout_execution_sessions") or 0),
    )


def build_weekly_summary_context_from_qa_range(
    *,
    user_id: int,
    start_date: date | str,
    end_date: date | str,
    db_path: str | Path | None = None,
) -> WeeklyCoachSummaryContext:
    # Lazy import avoids a module cycle while preserving the original public
    # service entry point for existing callers/tests. The actual context builder
    # is backend-owned and does not depend on Streamlit/UI labels.
    from services.weekly_coach_summary_qa_context_service import (
        build_weekly_summary_context_from_qa_range as build_context,
    )

    return build_context(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        db_path=db_path,
    )
