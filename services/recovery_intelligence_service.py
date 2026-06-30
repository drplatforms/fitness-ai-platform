from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from typing import Any

from database import get_connection
from models.recovery_intelligence_models import (
    RecoveryIntelligenceSummary,
    RecoverySignalDay,
    RecoveryTrendComparison,
    RecoveryWindowSummary,
)

RECOVERY_INTELLIGENCE_MODEL_VERSION = "recovery_intelligence_v1"
DEFAULT_WINDOWS = (7, 14, 28)
TREND_WINDOW_DAYS = 7
MIN_TREND_CHECKIN_DAYS = 3
SLEEP_DEADBAND_HOURS = 0.3
ENERGY_DEADBAND = 0.5
SORENESS_DEADBAND = 0.5

FORBIDDEN_RECOVERY_COACH_LANGUAGE = (
    "overtraining",
    "injury",
    "illness",
    "sleep disorder",
    "diagnosis",
    "medical risk",
)


def build_recovery_intelligence(
    user_id: int,
    target_date: str | None = None,
    windows: tuple[int, ...] = DEFAULT_WINDOWS,
) -> RecoveryIntelligenceSummary:
    """Build a read-only recovery intelligence summary from daily check-ins.

    Uses checkin_date as the primary date and only uses created_at/id for
    duplicate same-day resolution. This service does not diagnose or prescribe.
    """

    target = _parse_date(target_date) if target_date else date.today()
    resolved_windows = tuple(sorted({int(window) for window in windows if window > 0}))
    if not resolved_windows:
        resolved_windows = DEFAULT_WINDOWS

    max_window = max(max(resolved_windows), TREND_WINDOW_DAYS * 2)
    start = target - timedelta(days=max_window - 1)
    rows = _load_checkin_rows(user_id=user_id, start_date=start, end_date=target)
    days, dedupe_reason_codes = _dedupe_signal_days(rows)

    window_summaries = {
        str(window): _build_window_summary(
            days_by_date=days,
            window_days=window,
            target_date=target,
            dedupe_reason_codes=dedupe_reason_codes,
        )
        for window in resolved_windows
    }
    primary_window = (
        window_summaries.get("7") or window_summaries[str(resolved_windows[0])]
    )
    trend_comparison = _build_trend_comparison(days_by_date=days, target_date=target)
    current_day = days.get(target.isoformat())

    reason_codes = _unique(
        [
            *dedupe_reason_codes,
            *primary_window.reason_codes,
            *(trend_comparison.reason_codes if trend_comparison else []),
        ]
    )
    limitations = _unique(
        [
            *primary_window.limitations,
            *(trend_comparison.limitations if trend_comparison else []),
        ]
    )
    source_facts = _build_source_facts(primary_window, trend_comparison, current_day)
    coach_safe_summary = _coach_safe_summary(primary_window, trend_comparison)
    _guard_no_forbidden_language([coach_safe_summary, *source_facts])

    return RecoveryIntelligenceSummary(
        user_id=user_id,
        target_date=target.isoformat(),
        generated_at=datetime.now(UTC).isoformat(),
        source_table="daily_checkins",
        model_version=RECOVERY_INTELLIGENCE_MODEL_VERSION,
        current_day=current_day,
        windows=window_summaries,
        trend_comparison=trend_comparison,
        readiness_level=primary_window.readiness_level,
        fatigue_risk=primary_window.fatigue_risk,
        confidence=primary_window.confidence,
        source_facts=source_facts,
        coach_safe_summary=coach_safe_summary,
        reason_codes=reason_codes,
        limitations=limitations,
    )


def _load_checkin_rows(
    *, user_id: int, start_date: date, end_date: date
) -> list[dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT id,
               user_id,
               checkin_date,
               body_weight,
               sleep_hours,
               energy_level,
               soreness_level,
               mood,
               notes,
               created_at
        FROM daily_checkins
        WHERE user_id = ?
          AND checkin_date >= ?
          AND checkin_date <= ?
        ORDER BY checkin_date ASC,
                 COALESCE(created_at, '') ASC,
                 id ASC
        """,
        (user_id, start_date.isoformat(), end_date.isoformat()),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _dedupe_signal_days(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, RecoverySignalDay], list[str]]:
    latest_rows: dict[str, dict[str, Any]] = {}
    duplicate_dates: set[str] = set()
    for row in rows:
        checkin_date = str(row.get("checkin_date"))
        if checkin_date in latest_rows:
            duplicate_dates.add(checkin_date)
        latest_rows[checkin_date] = row

    days = {
        checkin_date: _signal_day_from_row(row)
        for checkin_date, row in sorted(latest_rows.items())
    }
    reason_codes = []
    if duplicate_dates:
        reason_codes.append("duplicate_checkins_deduped_by_latest_created_at")
    return days, reason_codes


def _signal_day_from_row(row: dict[str, Any]) -> RecoverySignalDay:
    sleep = _optional_float(row.get("sleep_hours"))
    energy = _optional_float(row.get("energy_level"))
    soreness = _optional_float(row.get("soreness_level"))
    body_weight = _optional_float(row.get("body_weight"))
    flags = []
    if sleep is None:
        flags.append("sleep_missing")
    if energy is None:
        flags.append("energy_missing")
    if soreness is None:
        flags.append("soreness_missing")
    if body_weight is None:
        flags.append("body_weight_missing")
    return RecoverySignalDay(
        date=str(row.get("checkin_date")),
        sleep_hours=sleep,
        energy_level=energy,
        soreness_level=soreness,
        body_weight_lb=body_weight,
        mood=row.get("mood") or None,
        notes_present=bool(row.get("notes")),
        data_quality_flags=flags,
    )


def _build_window_summary(
    *,
    days_by_date: dict[str, RecoverySignalDay],
    window_days: int,
    target_date: date,
    dedupe_reason_codes: list[str],
) -> RecoveryWindowSummary:
    start = target_date - timedelta(days=window_days - 1)
    dates = [day.isoformat() for day in _inclusive_dates(start, target_date)]
    window_days_data = [days_by_date[day] for day in dates if day in days_by_date]
    sleep_values = [
        day.sleep_hours for day in window_days_data if day.sleep_hours is not None
    ]
    energy_values = [
        day.energy_level for day in window_days_data if day.energy_level is not None
    ]
    soreness_values = [
        day.soreness_level for day in window_days_data if day.soreness_level is not None
    ]
    weights = [
        (day.date, day.body_weight_lb)
        for day in window_days_data
        if day.body_weight_lb is not None
    ]

    avg_sleep = _round_average(sleep_values)
    avg_energy = _round_average(energy_values)
    avg_soreness = _round_average(soreness_values)
    sleep_signal = _classify_sleep(avg_sleep)
    energy_signal = _classify_energy(avg_energy)
    soreness_signal = _classify_soreness(avg_soreness)
    checkin_days = len(window_days_data)
    checkin_rate = round(checkin_days / window_days, 2)
    confidence = _classify_confidence(window_days, checkin_days)
    readiness_level = _classify_readiness(
        sleep_signal=sleep_signal,
        energy_signal=energy_signal,
        soreness_signal=soreness_signal,
        confidence=confidence,
    )
    fatigue_risk = _classify_fatigue_risk(
        sleep_signal=sleep_signal,
        energy_signal=energy_signal,
        soreness_signal=soreness_signal,
        confidence=confidence,
    )
    latest_weight = weights[-1][1] if weights else None
    body_weight_delta = (
        round(float(weights[-1][1]) - float(weights[0][1]), 1)
        if len(weights) >= 2
        else None
    )
    reason_codes = list(dedupe_reason_codes)
    limitations = []
    if checkin_days == 0:
        reason_codes.append("no_recovery_checkins_in_window")
        limitations.append("No recovery check-ins were logged in this window.")
    elif confidence == "Limited":
        reason_codes.append("limited_recovery_checkin_coverage")
        limitations.append("Recovery check-in coverage is limited for this window.")
    elif confidence == "Low":
        reason_codes.append("low_recovery_checkin_coverage")
    if not sleep_values:
        reason_codes.append("sleep_data_unavailable")
    if not energy_values:
        reason_codes.append("energy_data_unavailable")
    if not soreness_values:
        reason_codes.append("soreness_data_unavailable")
    if len(weights) < 2:
        reason_codes.append("body_weight_delta_unavailable")

    return RecoveryWindowSummary(
        window_days=window_days,
        start_date=start.isoformat(),
        end_date=target_date.isoformat(),
        expected_days=window_days,
        checkin_days=checkin_days,
        checkin_rate=checkin_rate,
        average_sleep_hours=avg_sleep,
        average_energy_level=avg_energy,
        average_soreness_level=avg_soreness,
        latest_body_weight_lb=latest_weight,
        body_weight_delta_lb=body_weight_delta,
        sleep_signal=sleep_signal,
        energy_signal=energy_signal,
        soreness_signal=soreness_signal,
        readiness_level=readiness_level,
        fatigue_risk=fatigue_risk,
        confidence=confidence,
        reason_codes=_unique(reason_codes),
        limitations=_unique(limitations),
    )


def _build_trend_comparison(
    *, days_by_date: dict[str, RecoverySignalDay], target_date: date
) -> RecoveryTrendComparison:
    recent_start = target_date - timedelta(days=TREND_WINDOW_DAYS - 1)
    prior_end = recent_start - timedelta(days=1)
    prior_start = prior_end - timedelta(days=TREND_WINDOW_DAYS - 1)
    recent_days = _days_in_range(days_by_date, recent_start, target_date)
    prior_days = _days_in_range(days_by_date, prior_start, prior_end)
    if (
        len(recent_days) < MIN_TREND_CHECKIN_DAYS
        or len(prior_days) < MIN_TREND_CHECKIN_DAYS
    ):
        return RecoveryTrendComparison(
            recent_window_days=TREND_WINDOW_DAYS,
            prior_window_days=TREND_WINDOW_DAYS,
            sleep_delta=None,
            energy_delta=None,
            soreness_delta=None,
            body_weight_delta=None,
            trend_direction="unknown",
            confidence="Limited",
            reason_codes=["insufficient_recovery_trend_coverage"],
            limitations=[
                "Recovery trend comparison requires at least three check-in days "
                "in both recent and prior 7-day windows."
            ],
        )

    sleep_delta = _delta(
        _avg_attr(recent_days, "sleep_hours"),
        _avg_attr(prior_days, "sleep_hours"),
    )
    energy_delta = _delta(
        _avg_attr(recent_days, "energy_level"),
        _avg_attr(prior_days, "energy_level"),
    )
    soreness_delta = _delta(
        _avg_attr(recent_days, "soreness_level"),
        _avg_attr(prior_days, "soreness_level"),
    )
    body_weight_delta = _delta(
        _latest_attr(recent_days, "body_weight_lb"),
        _latest_attr(prior_days, "body_weight_lb"),
    )
    trend_direction = _classify_trend_direction(
        sleep_delta=sleep_delta,
        energy_delta=energy_delta,
        soreness_delta=soreness_delta,
    )
    confidence = "Moderate"
    reason_codes = ["recent_7_vs_prior_7_recovery_trend_available"]
    if trend_direction == "stable":
        reason_codes.append("recovery_trend_within_deadbands")
    return RecoveryTrendComparison(
        recent_window_days=TREND_WINDOW_DAYS,
        prior_window_days=TREND_WINDOW_DAYS,
        sleep_delta=sleep_delta,
        energy_delta=energy_delta,
        soreness_delta=soreness_delta,
        body_weight_delta=body_weight_delta,
        trend_direction=trend_direction,
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=[],
    )


def _days_in_range(
    days_by_date: dict[str, RecoverySignalDay], start: date, end: date
) -> list[RecoverySignalDay]:
    wanted = {day.isoformat() for day in _inclusive_dates(start, end)}
    return [day for key, day in sorted(days_by_date.items()) if key in wanted]


def _classify_sleep(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value >= 7.0:
        return "adequate"
    if value >= 6.0:
        return "borderline"
    return "low"


def _classify_energy(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value >= 7.0:
        return "strong"
    if value >= 5.0:
        return "usable"
    return "low"


def _classify_soreness(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value <= 3.0:
        return "low"
    if value < 7.0:
        return "moderate"
    return "high"


def _classify_confidence(window_days: int, checkin_days: int) -> str:
    if checkin_days == 0:
        return "Limited"
    checkin_rate = checkin_days / window_days
    if checkin_days >= 7 and checkin_rate >= 0.75:
        return "High"
    if checkin_days >= 5 and checkin_rate >= 0.5:
        return "Moderate"
    if checkin_days >= 3:
        return "Low"
    return "Limited"


def _classify_readiness(
    *, sleep_signal: str, energy_signal: str, soreness_signal: str, confidence: str
) -> str:
    if confidence == "Limited" or "unknown" in {
        sleep_signal,
        energy_signal,
        soreness_signal,
    }:
        return "unknown"
    if sleep_signal == "low" or energy_signal == "low" or soreness_signal == "high":
        return "low"
    if (
        sleep_signal == "adequate"
        and energy_signal == "strong"
        and soreness_signal in {"low", "moderate"}
    ):
        return "high"
    return "moderate"


def _classify_fatigue_risk(
    *, sleep_signal: str, energy_signal: str, soreness_signal: str, confidence: str
) -> str:
    if confidence == "Limited" or "unknown" in {
        sleep_signal,
        energy_signal,
        soreness_signal,
    }:
        return "unknown"
    red_flags = sum(
        [sleep_signal == "low", energy_signal == "low", soreness_signal == "high"]
    )
    borderline_flags = sum(
        [
            sleep_signal == "borderline",
            energy_signal == "usable",
            soreness_signal == "moderate",
        ]
    )
    if red_flags >= 2 or (soreness_signal == "high" and energy_signal == "low"):
        return "high"
    if red_flags == 1 or borderline_flags >= 2:
        return "moderate"
    return "low"


def _classify_trend_direction(
    *,
    sleep_delta: float | None,
    energy_delta: float | None,
    soreness_delta: float | None,
) -> str:
    improvements = 0
    worsenings = 0
    if sleep_delta is not None:
        if sleep_delta > SLEEP_DEADBAND_HOURS:
            improvements += 1
        elif sleep_delta < -SLEEP_DEADBAND_HOURS:
            worsenings += 1
    if energy_delta is not None:
        if energy_delta > ENERGY_DEADBAND:
            improvements += 1
        elif energy_delta < -ENERGY_DEADBAND:
            worsenings += 1
    if soreness_delta is not None:
        if soreness_delta < -SORENESS_DEADBAND:
            improvements += 1
        elif soreness_delta > SORENESS_DEADBAND:
            worsenings += 1
    if improvements and worsenings:
        return "mixed"
    if improvements:
        return "improving"
    if worsenings:
        return "worsening"
    return "stable"


def _build_source_facts(
    window: RecoveryWindowSummary,
    trend: RecoveryTrendComparison | None,
    current_day: RecoverySignalDay | None,
) -> list[str]:
    facts: list[str] = []
    if window.checkin_days == 0:
        facts.append("No recovery check-ins were logged in the primary 7-day window.")
    else:
        facts.append(
            f"Primary recovery window has {window.checkin_days}/"
            f"{window.expected_days} check-in days."
        )
    if window.average_sleep_hours is not None:
        facts.append(
            f"Average sleep in the primary window is {window.average_sleep_hours} hours."
        )
    if window.average_energy_level is not None:
        facts.append(
            f"Average energy in the primary window is {window.average_energy_level}/10."
        )
    if window.average_soreness_level is not None:
        facts.append(
            f"Average soreness in the primary window is {window.average_soreness_level}/10."
        )
    if current_day:
        facts.append("A recovery check-in exists for the target date.")
    if trend and trend.trend_direction != "unknown":
        facts.append(f"Recent recovery trend direction is {trend.trend_direction}.")
    return facts


def _coach_safe_summary(
    window: RecoveryWindowSummary, trend: RecoveryTrendComparison | None
) -> str:
    if window.confidence == "Limited":
        return (
            "Recovery data is limited, so treat readiness as unknown "
            "until more check-ins are logged."
        )
    if window.readiness_level == "low":
        return (
            "Recent recovery signals look lower than ideal based on logged sleep, "
            "energy, and soreness."
        )
    if window.readiness_level == "high":
        return (
            "Recent recovery signals look supportive based on logged sleep, "
            "energy, and soreness."
        )
    if trend and trend.trend_direction in {"improving", "worsening", "mixed"}:
        return (
            f"Recent recovery looks {trend.trend_direction} compared with the "
            "prior week, with confidence limited to logged check-ins."
        )
    return (
        "Recent recovery signals are usable but should be interpreted with "
        "the logged check-in coverage."
    )


def _guard_no_forbidden_language(values: list[str]) -> None:
    text = "\n".join(values).lower()
    if any(term in text for term in FORBIDDEN_RECOVERY_COACH_LANGUAGE):
        raise ValueError("Recovery intelligence produced forbidden diagnostic language")


def _inclusive_dates(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _parse_date(value: str | None) -> date:
    if value is None:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD format") from exc


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def _avg_attr(days: list[RecoverySignalDay], attr: str) -> float | None:
    values = [getattr(day, attr) for day in days if getattr(day, attr) is not None]
    return _round_average(values)


def _latest_attr(days: list[RecoverySignalDay], attr: str) -> float | None:
    values = [getattr(day, attr) for day in days if getattr(day, attr) is not None]
    return values[-1] if values else None


def _delta(recent: float | None, prior: float | None) -> float | None:
    if recent is None or prior is None:
        return None
    return round(recent - prior, 1)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
