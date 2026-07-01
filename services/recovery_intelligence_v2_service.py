from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from typing import Any

from database import get_connection
from models.recovery_intelligence_v2_models import (
    RecoveryBaseline,
    RecoveryDataQuality,
    RecoveryIndicatorInterpretation,
    RecoveryIntelligenceV2Summary,
    RecoveryRecentDelta,
    RecoverySourceFact,
    RecoveryV2IndicatorDay,
)

RECOVERY_INTELLIGENCE_V2_SERVICE_MODEL_VERSION = "recovery_intelligence_v2_service_v1"
SOURCE_TABLE = "daily_checkins"
BASELINE_WINDOW_DAYS = 28
RECENT_WINDOW_DAYS = 7
PRIOR_WINDOW_DAYS = 7
MIN_DELTA_CHECKIN_DAYS = 3
SLEEP_DEADBAND_HOURS = 0.3
ENERGY_DEADBAND = 0.5
SORENESS_DEADBAND = 0.5
BODY_WEIGHT_DEADBAND_LB = 0.5

FORBIDDEN_RECOVERY_LANGUAGE = (
    "overtraining",
    "injury",
    "illness",
    "diagnosis",
    "sleep disorder",
    "medical risk",
    "must deload",
    "forced deload",
    "automatic deload",
    "treatment",
)


class _CheckinDay(dict[str, Any]):
    """Internal normalized row container for daily check-ins."""


class _WindowStats(dict[str, Any]):
    """Internal aggregate stats for a date window."""


def build_recovery_intelligence_v2(
    user_id: int,
    target_date: str | date | None = None,
) -> RecoveryIntelligenceV2Summary:
    """Build a read-only Recovery Intelligence v2 summary from daily_checkins.

    This service uses checkin_date as the primary source date. created_at/id are only
    used to collapse duplicate same-day check-ins to the latest row for that day.
    The service does not mutate the database and does not prescribe treatment,
    deloads, or progression decisions.
    """

    target = _parse_date(target_date) if target_date is not None else date.today()
    baseline_start = target - timedelta(days=BASELINE_WINDOW_DAYS - 1)
    rows = _load_checkin_rows(
        user_id=user_id, start_date=baseline_start, end_date=target
    )
    days_by_date, duplicate_days_collapsed = _dedupe_checkin_days(rows)

    baseline_stats = _window_stats(
        days_by_date=days_by_date,
        start_date=baseline_start,
        end_date=target,
        window_name="baseline_28_days",
    )
    recent_start = target - timedelta(days=RECENT_WINDOW_DAYS - 1)
    recent_stats = _window_stats(
        days_by_date=days_by_date,
        start_date=recent_start,
        end_date=target,
        window_name="recent_7_days",
    )
    prior_start = target - timedelta(days=RECENT_WINDOW_DAYS + PRIOR_WINDOW_DAYS - 1)
    prior_end = target - timedelta(days=RECENT_WINDOW_DAYS)
    prior_stats = _window_stats(
        days_by_date=days_by_date,
        start_date=prior_start,
        end_date=prior_end,
        window_name="prior_7_days",
    )

    current_day = _build_current_day(days_by_date.get(target.isoformat()))
    data_quality = _build_data_quality(
        baseline_stats=baseline_stats,
        target_date=target,
        duplicate_days_collapsed=duplicate_days_collapsed,
    )
    baseline = _build_baseline(baseline_stats)
    recent_vs_baseline = _build_delta(
        comparison_name="recent_vs_baseline",
        recent_stats=recent_stats,
        comparison_stats=baseline_stats,
        comparison_window_days=BASELINE_WINDOW_DAYS,
    )
    recent_vs_prior = _build_delta(
        comparison_name="recent_vs_prior",
        recent_stats=recent_stats,
        comparison_stats=prior_stats,
        comparison_window_days=PRIOR_WINDOW_DAYS,
    )

    sleep_interpretation = _build_indicator_interpretation(
        indicator_name="sleep",
        current_value=current_day.sleep_hours if current_day else None,
        recent_stats=recent_stats,
        baseline_stats=baseline_stats,
        prior_stats=prior_stats,
        data_quality=data_quality,
    )
    energy_interpretation = _build_indicator_interpretation(
        indicator_name="energy",
        current_value=current_day.energy_level if current_day else None,
        recent_stats=recent_stats,
        baseline_stats=baseline_stats,
        prior_stats=prior_stats,
        data_quality=data_quality,
    )
    soreness_interpretation = _build_indicator_interpretation(
        indicator_name="soreness",
        current_value=current_day.soreness_level if current_day else None,
        recent_stats=recent_stats,
        baseline_stats=baseline_stats,
        prior_stats=prior_stats,
        data_quality=data_quality,
    )
    body_weight_interpretation = _build_indicator_interpretation(
        indicator_name="body_weight",
        current_value=current_day.body_weight_lb if current_day else None,
        recent_stats=recent_stats,
        baseline_stats=baseline_stats,
        prior_stats=prior_stats,
        data_quality=data_quality,
    )
    checkin_consistency = _build_checkin_consistency_interpretation(
        recent_stats=recent_stats,
        baseline_stats=baseline_stats,
        data_quality=data_quality,
    )

    recovery_pressure = _classify_recovery_pressure(
        sleep_interpretation=sleep_interpretation,
        energy_interpretation=energy_interpretation,
        soreness_interpretation=soreness_interpretation,
        data_quality=data_quality,
    )
    readiness_classification = _classify_readiness(
        recovery_pressure=recovery_pressure,
        sleep_interpretation=sleep_interpretation,
        energy_interpretation=energy_interpretation,
        soreness_interpretation=soreness_interpretation,
        recent_vs_prior=recent_vs_prior,
        data_quality=data_quality,
    )
    fatigue_support = _classify_fatigue_support(
        readiness_classification=readiness_classification,
        recovery_pressure=recovery_pressure,
        data_quality=data_quality,
    )
    confidence = _summary_confidence(
        data_quality=data_quality,
        interpretations=(
            sleep_interpretation,
            energy_interpretation,
            soreness_interpretation,
            body_weight_interpretation,
            checkin_consistency,
        ),
    )
    reason_codes = _unique(
        [
            *data_quality.reason_codes,
            *baseline.reason_codes,
            *recent_vs_baseline.reason_codes,
            *recent_vs_prior.reason_codes,
            *sleep_interpretation.reason_codes,
            *energy_interpretation.reason_codes,
            *soreness_interpretation.reason_codes,
            *checkin_consistency.reason_codes,
        ]
    )
    limitations = _unique(
        [
            *data_quality.limitations,
            *baseline.limitations,
            *recent_vs_baseline.limitations,
            *recent_vs_prior.limitations,
            *sleep_interpretation.limitations,
            *energy_interpretation.limitations,
            *soreness_interpretation.limitations,
            *checkin_consistency.limitations,
        ]
    )
    if confidence in {"Limited", "Low"} and not (reason_codes or limitations):
        reason_codes.append("recovery_v2_confidence_limited")
        limitations.append(
            "Recovery v2 confidence is limited by available check-in data."
        )

    source_facts = _build_source_facts(
        target_date=target,
        data_quality=data_quality,
        recent_stats=recent_stats,
        baseline_stats=baseline_stats,
    )
    coach_safe_summary = _build_coach_safe_summary(
        readiness_classification=readiness_classification,
        recovery_pressure=recovery_pressure,
        data_quality=data_quality,
        confidence=confidence,
    )
    _guard_no_forbidden_language(
        [
            coach_safe_summary,
            *reason_codes,
            *limitations,
            *(fact.value_summary for fact in source_facts),
        ]
    )

    return RecoveryIntelligenceV2Summary(
        user_id=user_id,
        target_date=target.isoformat(),
        generated_at=datetime.now(UTC).isoformat(),
        source_table=SOURCE_TABLE,
        model_version=RECOVERY_INTELLIGENCE_V2_SERVICE_MODEL_VERSION,
        current_day=current_day,
        windows={
            "recent_7_days": _public_window(recent_stats),
            "prior_7_days": _public_window(prior_stats),
            "baseline_28_days": _public_window(baseline_stats),
        },
        baseline=baseline,
        recent_vs_baseline=recent_vs_baseline,
        recent_vs_prior=recent_vs_prior,
        sleep_interpretation=sleep_interpretation,
        energy_interpretation=energy_interpretation,
        soreness_interpretation=soreness_interpretation,
        body_weight_interpretation=body_weight_interpretation,
        checkin_consistency=checkin_consistency,
        readiness_classification=readiness_classification,
        recovery_pressure=recovery_pressure,
        fatigue_support=fatigue_support,
        data_quality=data_quality,
        confidence=confidence,
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


def _dedupe_checkin_days(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, _CheckinDay], int]:
    latest_rows: dict[str, dict[str, Any]] = {}
    duplicate_dates: set[str] = set()
    for row in rows:
        checkin_date = str(row.get("checkin_date"))
        if checkin_date in latest_rows:
            duplicate_dates.add(checkin_date)
        latest_rows[checkin_date] = row

    days = {
        checkin_date: _normalize_checkin_day(row)
        for checkin_date, row in sorted(latest_rows.items())
    }
    return days, len(duplicate_dates)


def _normalize_checkin_day(row: dict[str, Any]) -> _CheckinDay:
    return _CheckinDay(
        date=str(row.get("checkin_date")),
        sleep_hours=_optional_float(row.get("sleep_hours")),
        energy_level=_optional_float(row.get("energy_level")),
        soreness_level=_optional_float(row.get("soreness_level")),
        body_weight_lb=_optional_float(row.get("body_weight")),
        notes_present=bool(row.get("notes")),
    )


def _build_current_day(day: _CheckinDay | None) -> RecoveryV2IndicatorDay | None:
    if day is None:
        return None
    reason_codes = []
    limitations = []
    missing_count = 0
    for key, reason in (
        ("sleep_hours", "sleep_data_missing_current_day"),
        ("energy_level", "energy_data_missing_current_day"),
        ("soreness_level", "soreness_data_missing_current_day"),
    ):
        if day.get(key) is None:
            missing_count += 1
            reason_codes.append(reason)
    if missing_count >= 2:
        status = "limited"
        limitations.append("Current-day recovery check-in is missing multiple fields.")
    elif missing_count == 1:
        status = "partial"
    else:
        status = "usable"

    return RecoveryV2IndicatorDay(
        date=str(day["date"]),
        sleep_hours=day.get("sleep_hours"),
        energy_level=day.get("energy_level"),
        soreness_level=day.get("soreness_level"),
        body_weight_lb=day.get("body_weight_lb"),
        notes_present=bool(day.get("notes_present")),
        data_quality_status=status,
        reason_codes=reason_codes,
        limitations=limitations,
    )


def _window_stats(
    *,
    days_by_date: dict[str, _CheckinDay],
    start_date: date,
    end_date: date,
    window_name: str,
) -> _WindowStats:
    expected_days = (end_date - start_date).days + 1
    dates = [day.isoformat() for day in _inclusive_dates(start_date, end_date)]
    days = [days_by_date[day] for day in dates if day in days_by_date]
    sleep_values = [
        day["sleep_hours"] for day in days if day.get("sleep_hours") is not None
    ]
    energy_values = [
        day["energy_level"] for day in days if day.get("energy_level") is not None
    ]
    soreness_values = [
        day["soreness_level"] for day in days if day.get("soreness_level") is not None
    ]
    weight_values = [
        (day["date"], day["body_weight_lb"])
        for day in days
        if day.get("body_weight_lb") is not None
    ]
    return _WindowStats(
        window_name=window_name,
        start_date=start_date,
        end_date=end_date,
        expected_days=expected_days,
        checkin_days=len(days),
        checkin_rate=round(len(days) / expected_days, 2),
        average_sleep_hours=_round_average(sleep_values),
        average_energy_level=_round_average(energy_values),
        average_soreness_level=_round_average(soreness_values),
        latest_body_weight_lb=(weight_values[-1][1] if weight_values else None),
        average_body_weight_lb=_round_average([value for _, value in weight_values]),
        sleep_value_days=len(sleep_values),
        energy_value_days=len(energy_values),
        soreness_value_days=len(soreness_values),
        body_weight_value_days=len(weight_values),
        missing_sleep_days=expected_days - len(sleep_values),
        missing_energy_days=expected_days - len(energy_values),
        missing_soreness_days=expected_days - len(soreness_values),
        dates_with_checkin=[day["date"] for day in days],
        first_body_weight_lb=(weight_values[0][1] if weight_values else None),
        last_body_weight_lb=(weight_values[-1][1] if weight_values else None),
    )


def _build_data_quality(
    *,
    baseline_stats: _WindowStats,
    target_date: date,
    duplicate_days_collapsed: int,
) -> RecoveryDataQuality:
    checkin_days = int(baseline_stats["checkin_days"])
    expected_days = int(baseline_stats["expected_days"])
    checkin_rate = float(baseline_stats["checkin_rate"])
    current_day_present = (
        target_date.isoformat() in baseline_stats["dates_with_checkin"]
    )

    reason_codes = []
    limitations = []
    if checkin_days == 0:
        status = "missing"
        confidence = "Limited"
        reason_codes.append("no_recovery_v2_checkins_available")
        limitations.append("Recovery v2 has no check-ins in the baseline window.")
    elif checkin_rate < 0.25:
        status = "limited"
        confidence = "Limited"
        reason_codes.append("limited_recovery_v2_checkin_coverage")
        limitations.append("Recovery v2 check-in coverage is limited.")
    elif checkin_rate < 0.5:
        status = "partial"
        confidence = "Low"
        reason_codes.append("partial_recovery_v2_checkin_coverage")
        limitations.append("Recovery v2 check-in coverage is partial.")
    elif checkin_rate < 0.85:
        status = "usable"
        confidence = "Moderate"
        reason_codes.append("usable_recovery_v2_checkin_coverage")
    else:
        status = "strong"
        confidence = "High"
        reason_codes.append("strong_recovery_v2_checkin_coverage")

    if duplicate_days_collapsed:
        reason_codes.append("duplicate_checkins_deduped_by_latest_created_at")
    if not current_day_present:
        reason_codes.append("target_date_checkin_missing")
        if confidence == "High":
            confidence = "Moderate"

    return RecoveryDataQuality(
        expected_days=expected_days,
        checkin_days=checkin_days,
        checkin_rate=checkin_rate,
        missing_sleep_days=int(baseline_stats["missing_sleep_days"]),
        missing_energy_days=int(baseline_stats["missing_energy_days"]),
        missing_soreness_days=int(baseline_stats["missing_soreness_days"]),
        duplicate_days_collapsed=duplicate_days_collapsed,
        stale_current_day=not current_day_present,
        status=status,
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=limitations,
    )


def _build_baseline(stats: _WindowStats) -> RecoveryBaseline:
    confidence = _window_confidence(
        int(stats["checkin_days"]), int(stats["expected_days"])
    )
    reason_codes = []
    limitations = []
    if confidence == "Limited":
        reason_codes.append("baseline_checkin_coverage_limited")
        limitations.append("Recovery baseline has limited check-in coverage.")
    elif confidence == "Low":
        reason_codes.append("baseline_checkin_coverage_low")
        limitations.append("Recovery baseline has low check-in coverage.")
    else:
        reason_codes.append("baseline_window_available")

    if stats["average_sleep_hours"] is None:
        reason_codes.append("baseline_sleep_unavailable")
    if stats["average_energy_level"] is None:
        reason_codes.append("baseline_energy_unavailable")
    if stats["average_soreness_level"] is None:
        reason_codes.append("baseline_soreness_unavailable")

    return RecoveryBaseline(
        baseline_window_days=int(stats["expected_days"]),
        start_date=stats["start_date"].isoformat(),
        end_date=stats["end_date"].isoformat(),
        checkin_days=int(stats["checkin_days"]),
        average_sleep_hours=stats["average_sleep_hours"],
        average_energy_level=stats["average_energy_level"],
        average_soreness_level=stats["average_soreness_level"],
        latest_body_weight_lb=stats["latest_body_weight_lb"],
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=limitations,
    )


def _build_delta(
    *,
    comparison_name: str,
    recent_stats: _WindowStats,
    comparison_stats: _WindowStats,
    comparison_window_days: int,
) -> RecoveryRecentDelta:
    recent_checkins = int(recent_stats["checkin_days"])
    comparison_checkins = int(comparison_stats["checkin_days"])
    reason_codes = []
    limitations = []
    enough_data = (
        recent_checkins >= MIN_DELTA_CHECKIN_DAYS
        and comparison_checkins >= MIN_DELTA_CHECKIN_DAYS
    )
    if not enough_data:
        confidence = "Limited"
        trend_direction = "unknown"
        reason_codes.append(f"{comparison_name}_insufficient_checkin_coverage")
        limitations.append(f"{comparison_name} needs more check-in coverage.")
        return RecoveryRecentDelta(
            comparison_name=comparison_name,
            recent_window_days=RECENT_WINDOW_DAYS,
            comparison_window_days=comparison_window_days,
            sleep_delta=None,
            energy_delta=None,
            soreness_delta=None,
            body_weight_delta=None,
            trend_direction=trend_direction,
            confidence=confidence,
            reason_codes=reason_codes,
            limitations=limitations,
        )

    sleep_delta = _delta(
        recent_stats["average_sleep_hours"], comparison_stats["average_sleep_hours"]
    )
    energy_delta = _delta(
        recent_stats["average_energy_level"], comparison_stats["average_energy_level"]
    )
    soreness_delta = _delta(
        recent_stats["average_soreness_level"],
        comparison_stats["average_soreness_level"],
    )
    body_weight_delta = _delta(
        recent_stats["average_body_weight_lb"],
        comparison_stats["average_body_weight_lb"],
    )
    trend_direction = _trend_direction(
        sleep_delta=sleep_delta,
        energy_delta=energy_delta,
        soreness_delta=soreness_delta,
    )
    confidence = "Moderate"
    reason_codes.append(f"{comparison_name}_available")
    return RecoveryRecentDelta(
        comparison_name=comparison_name,
        recent_window_days=RECENT_WINDOW_DAYS,
        comparison_window_days=comparison_window_days,
        sleep_delta=sleep_delta,
        energy_delta=energy_delta,
        soreness_delta=soreness_delta,
        body_weight_delta=body_weight_delta,
        trend_direction=trend_direction,
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=limitations,
    )


def _build_indicator_interpretation(
    *,
    indicator_name: str,
    current_value: float | None,
    recent_stats: _WindowStats,
    baseline_stats: _WindowStats,
    prior_stats: _WindowStats,
    data_quality: RecoveryDataQuality,
) -> RecoveryIndicatorInterpretation:
    key = _indicator_stat_key(indicator_name)
    recent_average = recent_stats[key]
    baseline_value = baseline_stats[key]
    prior_average = prior_stats[key]
    delta_from_baseline = _delta(recent_average, baseline_value)
    delta_recent_vs_prior = _delta(recent_average, prior_average)
    status = _indicator_status(indicator_name, recent_average)
    trend_direction = _indicator_trend(indicator_name, delta_recent_vs_prior)
    confidence = _indicator_confidence(indicator_name, recent_stats, data_quality)
    reason_codes = []
    limitations = []
    if recent_average is None:
        reason_codes.append(f"{indicator_name}_recent_data_unavailable")
        limitations.append(f"Recent {indicator_name} data is unavailable.")
    elif confidence in {"Limited", "Low"}:
        reason_codes.append(f"{indicator_name}_coverage_{confidence.lower()}")
        limitations.append(
            f"{indicator_name} confidence is limited by logged coverage."
        )
    return RecoveryIndicatorInterpretation(
        indicator_name=indicator_name,
        current_value=current_value,
        baseline_value=baseline_value,
        recent_average=recent_average,
        prior_average=prior_average,
        delta_from_baseline=delta_from_baseline,
        delta_recent_vs_prior=delta_recent_vs_prior,
        status=status,
        trend_direction=trend_direction,
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=limitations,
    )


def _build_checkin_consistency_interpretation(
    *,
    recent_stats: _WindowStats,
    baseline_stats: _WindowStats,
    data_quality: RecoveryDataQuality,
) -> RecoveryIndicatorInterpretation:
    current_value = float(recent_stats["checkin_rate"])
    baseline_value = float(baseline_stats["checkin_rate"])
    delta_from_baseline = round(current_value - baseline_value, 2)
    status = (
        "unknown"
        if data_quality.status == "missing"
        else (
            "normal"
            if current_value >= 0.7
            else "borderline"
            if current_value >= 0.4
            else "low"
        )
    )
    trend_direction = (
        "unknown"
        if data_quality.status == "missing"
        else (
            "improving"
            if delta_from_baseline > 0.1
            else "worsening"
            if delta_from_baseline < -0.1
            else "stable"
        )
    )
    confidence = data_quality.confidence
    reason_codes = []
    limitations = []
    if confidence in {"Limited", "Low"}:
        reason_codes.append("checkin_consistency_limited")
        limitations.append("Check-in consistency is limited by available logs.")
    return RecoveryIndicatorInterpretation(
        indicator_name="checkin_consistency",
        current_value=current_value,
        baseline_value=baseline_value,
        recent_average=current_value,
        prior_average=None,
        delta_from_baseline=delta_from_baseline,
        delta_recent_vs_prior=None,
        status=status,
        trend_direction=trend_direction,
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=limitations,
    )


def _classify_recovery_pressure(
    *,
    sleep_interpretation: RecoveryIndicatorInterpretation,
    energy_interpretation: RecoveryIndicatorInterpretation,
    soreness_interpretation: RecoveryIndicatorInterpretation,
    data_quality: RecoveryDataQuality,
) -> str:
    if data_quality.status == "missing":
        return "unknown"
    high_pressure_count = 0
    moderate_pressure_count = 0
    if sleep_interpretation.status == "low":
        high_pressure_count += 1
    elif sleep_interpretation.status == "borderline":
        moderate_pressure_count += 1
    if energy_interpretation.status == "low":
        high_pressure_count += 1
    elif energy_interpretation.status == "borderline":
        moderate_pressure_count += 1
    if soreness_interpretation.status == "high":
        high_pressure_count += 1
    elif soreness_interpretation.status == "borderline":
        moderate_pressure_count += 1

    if high_pressure_count >= 2 or (
        soreness_interpretation.status == "high" and high_pressure_count >= 1
    ):
        return "high"
    if high_pressure_count == 1 or moderate_pressure_count >= 2:
        return "moderate"
    return "low"


def _classify_readiness(
    *,
    recovery_pressure: str,
    sleep_interpretation: RecoveryIndicatorInterpretation,
    energy_interpretation: RecoveryIndicatorInterpretation,
    soreness_interpretation: RecoveryIndicatorInterpretation,
    recent_vs_prior: RecoveryRecentDelta,
    data_quality: RecoveryDataQuality,
) -> str:
    if data_quality.status == "missing" or recovery_pressure == "unknown":
        return "unknown"
    if data_quality.confidence == "Limited" or recovery_pressure == "high":
        return "recovery_limited"
    statuses = {
        sleep_interpretation.status,
        energy_interpretation.status,
        soreness_interpretation.status,
    }
    if recent_vs_prior.trend_direction == "mixed" or "mixed" in statuses:
        return "mixed"
    if recent_vs_prior.trend_direction == "improving" and recovery_pressure != "high":
        return "improving"
    if (
        recovery_pressure == "low"
        and sleep_interpretation.status
        in {
            "normal",
            "high",
        }
        and energy_interpretation.status in {"normal", "high"}
    ):
        return "supportive"
    return "manageable"


def _classify_fatigue_support(
    *,
    readiness_classification: str,
    recovery_pressure: str,
    data_quality: RecoveryDataQuality,
) -> str:
    if data_quality.status == "missing" or recovery_pressure == "unknown":
        return "unknown"
    if readiness_classification in {"supportive", "improving"}:
        return "supportive"
    if readiness_classification == "recovery_limited" or recovery_pressure == "high":
        return "limiting"
    return "mixed"


def _summary_confidence(
    *,
    data_quality: RecoveryDataQuality,
    interpretations: Iterable[RecoveryIndicatorInterpretation],
) -> str:
    if data_quality.confidence in {"Limited", "Low"}:
        return data_quality.confidence
    if any(item.confidence == "Limited" for item in interpretations):
        return "Low"
    if any(item.confidence == "Low" for item in interpretations):
        return "Moderate"
    return data_quality.confidence


def _build_source_facts(
    *,
    target_date: date,
    data_quality: RecoveryDataQuality,
    recent_stats: _WindowStats,
    baseline_stats: _WindowStats,
) -> list[RecoverySourceFact]:
    facts = [
        RecoverySourceFact(
            source_table=SOURCE_TABLE,
            field_name="checkin_date",
            observed_date=target_date.isoformat(),
            value_summary="checkin_date is used as the primary recovery v2 date field",
            confidence="High",
        ),
        RecoverySourceFact(
            source_table=SOURCE_TABLE,
            field_name="sleep_hours",
            observed_date=None,
            value_summary=_fact_value_summary(
                "recent sleep average", recent_stats["average_sleep_hours"]
            ),
            confidence=data_quality.confidence,
        ),
        RecoverySourceFact(
            source_table=SOURCE_TABLE,
            field_name="energy_level",
            observed_date=None,
            value_summary=_fact_value_summary(
                "recent energy average", recent_stats["average_energy_level"]
            ),
            confidence=data_quality.confidence,
        ),
        RecoverySourceFact(
            source_table=SOURCE_TABLE,
            field_name="soreness_level",
            observed_date=None,
            value_summary=_fact_value_summary(
                "recent soreness average", recent_stats["average_soreness_level"]
            ),
            confidence=data_quality.confidence,
        ),
        RecoverySourceFact(
            source_table=SOURCE_TABLE,
            field_name="body_weight",
            observed_date=None,
            value_summary=_fact_value_summary(
                "baseline body weight value", baseline_stats["latest_body_weight_lb"]
            ),
            confidence=data_quality.confidence,
        ),
    ]
    _guard_no_forbidden_language([fact.value_summary for fact in facts])
    return facts


def _build_coach_safe_summary(
    *,
    readiness_classification: str,
    recovery_pressure: str,
    data_quality: RecoveryDataQuality,
    confidence: str,
) -> str:
    if data_quality.status == "missing":
        return "Recovery v2 has no check-ins in the baseline window, so readiness should stay unknown."
    if confidence in {"Limited", "Low"}:
        return "Recovery v2 has limited check-in coverage, so the training read should stay conservative."
    if recovery_pressure == "high":
        return "Recent recovery indicators look limiting, so the training read should stay conservative."
    if readiness_classification in {"supportive", "improving"}:
        return (
            "Recent recovery indicators look supportive with usable check-in coverage."
        )
    if readiness_classification == "mixed":
        return "Recent recovery indicators are mixed, so the training read should stay cautious."
    return (
        "Recent recovery indicators look manageable with the available check-in data."
    )


def _public_window(stats: _WindowStats) -> dict[str, Any]:
    return {
        "window_name": stats["window_name"],
        "start_date": stats["start_date"].isoformat(),
        "end_date": stats["end_date"].isoformat(),
        "expected_days": stats["expected_days"],
        "checkin_days": stats["checkin_days"],
        "checkin_rate": stats["checkin_rate"],
        "average_sleep_hours": stats["average_sleep_hours"],
        "average_energy_level": stats["average_energy_level"],
        "average_soreness_level": stats["average_soreness_level"],
        "latest_body_weight_lb": stats["latest_body_weight_lb"],
    }


def _indicator_stat_key(indicator_name: str) -> str:
    if indicator_name == "sleep":
        return "average_sleep_hours"
    if indicator_name == "energy":
        return "average_energy_level"
    if indicator_name == "soreness":
        return "average_soreness_level"
    if indicator_name == "body_weight":
        return "average_body_weight_lb"
    raise ValueError(f"Unsupported indicator: {indicator_name}")


def _indicator_status(indicator_name: str, value: float | None) -> str:
    if value is None:
        return "unknown"
    if indicator_name == "sleep":
        if value < 6.0:
            return "low"
        if value < 7.0:
            return "borderline"
        if value > 9.5:
            return "high"
        return "normal"
    if indicator_name == "energy":
        if value < 5.0:
            return "low"
        if value < 7.0:
            return "borderline"
        return "normal"
    if indicator_name == "soreness":
        if value >= 7.0:
            return "high"
        if value > 3.0:
            return "borderline"
        return "normal"
    if indicator_name == "body_weight":
        return "normal"
    return "unknown"


def _indicator_trend(indicator_name: str, delta_value: float | None) -> str:
    if delta_value is None:
        return "unknown"
    deadband = _deadband_for_indicator(indicator_name)
    if abs(delta_value) <= deadband:
        return "stable"
    if indicator_name == "soreness":
        return "improving" if delta_value < 0 else "worsening"
    if indicator_name in {"sleep", "energy"}:
        return "improving" if delta_value > 0 else "worsening"
    if indicator_name == "body_weight":
        return "stable" if abs(delta_value) <= BODY_WEIGHT_DEADBAND_LB else "mixed"
    return "unknown"


def _indicator_confidence(
    indicator_name: str, stats: _WindowStats, data_quality: RecoveryDataQuality
) -> str:
    if data_quality.status == "missing":
        return "Limited"
    value_days_key = {
        "sleep": "sleep_value_days",
        "energy": "energy_value_days",
        "soreness": "soreness_value_days",
        "body_weight": "body_weight_value_days",
    }[indicator_name]
    value_days = int(stats[value_days_key])
    if value_days == 0:
        return "Limited"
    if value_days < MIN_DELTA_CHECKIN_DAYS:
        return "Low"
    if value_days < RECENT_WINDOW_DAYS:
        return "Moderate"
    return "High"


def _trend_direction(
    *,
    sleep_delta: float | None,
    energy_delta: float | None,
    soreness_delta: float | None,
) -> str:
    directions = [
        _indicator_trend("sleep", sleep_delta),
        _indicator_trend("energy", energy_delta),
        _indicator_trend("soreness", soreness_delta),
    ]
    usable = [direction for direction in directions if direction != "unknown"]
    if not usable:
        return "unknown"
    improving = usable.count("improving")
    worsening = usable.count("worsening")
    if improving and worsening:
        return "mixed"
    if improving:
        return "improving"
    if worsening:
        return "worsening"
    return "stable"


def _deadband_for_indicator(indicator_name: str) -> float:
    if indicator_name == "sleep":
        return SLEEP_DEADBAND_HOURS
    if indicator_name == "energy":
        return ENERGY_DEADBAND
    if indicator_name == "soreness":
        return SORENESS_DEADBAND
    if indicator_name == "body_weight":
        return BODY_WEIGHT_DEADBAND_LB
    return 0.0


def _window_confidence(checkin_days: int, expected_days: int) -> str:
    if checkin_days == 0:
        return "Limited"
    rate = checkin_days / expected_days
    if rate < 0.25:
        return "Limited"
    if rate < 0.5:
        return "Low"
    if rate < 0.85:
        return "Moderate"
    return "High"


def _delta(recent_value: float | None, comparison_value: float | None) -> float | None:
    if recent_value is None or comparison_value is None:
        return None
    return round(float(recent_value) - float(comparison_value), 2)


def _fact_value_summary(label: str, value: float | None) -> str:
    return f"{label} is unavailable" if value is None else f"{label} is available"


def _inclusive_dates(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def _round_average(values: Iterable[float]) -> float | None:
    items = [float(value) for value in values if value is not None]
    if not items:
        return None
    return round(sum(items) / len(items), 2)


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def _guard_no_forbidden_language(values: Iterable[str]) -> None:
    text = " ".join(value for value in values if value).lower()
    blocked = [term for term in FORBIDDEN_RECOVERY_LANGUAGE if term in text]
    if blocked:
        raise ValueError(f"Forbidden recovery v2 language emitted: {blocked[0]}")
