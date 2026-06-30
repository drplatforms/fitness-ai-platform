from __future__ import annotations

from datetime import date, timedelta

import database
from services.recovery_intelligence_service import build_recovery_intelligence


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (id, name, starting_weight)
        VALUES (?, ?, ?)
        """,
        (1, "Recovery Test User", 190.0),
    )
    conn.commit()
    conn.close()


def _insert_checkin(
    *,
    user_id: int = 1,
    target_date: str,
    sleep: float | None = 7.0,
    energy: int | None = 6,
    soreness: int | None = 3,
    weight: float | None = 190.0,
    created_at: str = "2026-06-14T08:00:00",
    notes: str | None = None,
) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO daily_checkins (
            user_id,
            checkin_date,
            body_weight,
            sleep_hours,
            energy_level,
            soreness_level,
            mood,
            notes,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            target_date,
            weight,
            sleep,
            energy,
            soreness,
            "okay",
            notes,
            created_at,
        ),
    )
    conn.commit()
    conn.close()


def _day(days_ago: int) -> str:
    return (date(2026, 6, 14) - timedelta(days=days_ago)).isoformat()


def test_no_checkins_returns_limited_unknown_safely(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_recovery_intelligence(user_id=1, target_date="2026-06-14")

    assert summary.readiness_level == "unknown"
    assert summary.fatigue_risk == "unknown"
    assert summary.confidence == "Limited"
    assert summary.current_day is None
    assert summary.windows["7"].checkin_days == 0
    assert "no_recovery_checkins_in_window" in summary.reason_codes
    assert "overtraining" not in summary.coach_safe_summary.lower()
    assert "diagnosis" not in summary.coach_safe_summary.lower()


def test_uses_checkin_date_not_created_at_for_windows(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_checkin(target_date="2026-06-01", created_at="2026-06-14T23:59:00")
    _insert_checkin(target_date="2026-06-14", sleep=8, energy=8, soreness=2)

    summary = build_recovery_intelligence(user_id=1, target_date="2026-06-14")

    assert summary.windows["7"].checkin_days == 1
    assert summary.current_day is not None
    assert summary.current_day.date == "2026-06-14"


def test_duplicate_same_date_checkins_are_deduped_by_latest_created_at(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_checkin(
        target_date="2026-06-14",
        sleep=5,
        energy=3,
        soreness=8,
        created_at="2026-06-14T06:00:00",
    )
    _insert_checkin(
        target_date="2026-06-14",
        sleep=8,
        energy=8,
        soreness=2,
        created_at="2026-06-14T09:00:00",
    )

    summary = build_recovery_intelligence(user_id=1, target_date="2026-06-14")

    assert summary.windows["7"].checkin_days == 1
    assert summary.windows["7"].average_sleep_hours == 8.0
    assert summary.current_day is not None
    assert summary.current_day.energy_level == 8.0
    assert "duplicate_checkins_deduped_by_latest_created_at" in summary.reason_codes


def test_window_averages_and_signal_classifications_are_bounded(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for days_ago, values in enumerate(
        [(0, 7.5, 8, 2), (1, 7.0, 7, 3), (2, 6.5, 6, 4), (3, 7.5, 8, 2), (4, 7.0, 7, 3)]
    ):
        _, sleep, energy, soreness = values
        _insert_checkin(
            target_date=_day(days_ago),
            sleep=sleep,
            energy=energy,
            soreness=soreness,
            weight=190 - days_ago * 0.2,
        )

    summary = build_recovery_intelligence(user_id=1, target_date="2026-06-14")
    window = summary.windows["7"]

    assert window.average_sleep_hours == 7.1
    assert window.average_energy_level == 7.2
    assert window.average_soreness_level == 2.8
    assert window.sleep_signal == "adequate"
    assert window.energy_signal == "strong"
    assert window.soreness_signal == "low"
    assert window.readiness_level in {"moderate", "high"}
    assert window.fatigue_risk in {"low", "moderate", "unknown", "high"}
    assert summary.confidence in {"Moderate", "High"}


def test_low_sleep_energy_and_high_soreness_lower_readiness(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for days_ago in range(5):
        _insert_checkin(
            target_date=_day(days_ago),
            sleep=5.5,
            energy=4,
            soreness=7,
        )

    summary = build_recovery_intelligence(user_id=1, target_date="2026-06-14")

    assert summary.readiness_level == "low"
    assert summary.fatigue_risk == "high"
    assert "overtraining" not in " ".join(summary.source_facts).lower()


def test_trend_comparison_requires_enough_data(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_checkin(target_date=_day(0))
    _insert_checkin(target_date=_day(8))

    summary = build_recovery_intelligence(user_id=1, target_date="2026-06-14")

    assert summary.trend_comparison is not None
    assert summary.trend_comparison.trend_direction == "unknown"
    assert summary.trend_comparison.confidence == "Limited"
    assert (
        "insufficient_recovery_trend_coverage" in summary.trend_comparison.reason_codes
    )


def test_trend_comparison_uses_recent_7_vs_prior_7(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for days_ago in [0, 1, 2, 3]:
        _insert_checkin(target_date=_day(days_ago), sleep=7.5, energy=8, soreness=2)
    for days_ago in [7, 8, 9, 10]:
        _insert_checkin(target_date=_day(days_ago), sleep=6.0, energy=5, soreness=5)

    summary = build_recovery_intelligence(user_id=1, target_date="2026-06-14")

    assert summary.trend_comparison is not None
    assert summary.trend_comparison.sleep_delta == 1.5
    assert summary.trend_comparison.energy_delta == 3.0
    assert summary.trend_comparison.soreness_delta == -3.0
    assert summary.trend_comparison.trend_direction == "improving"
    assert (
        "recent_7_vs_prior_7_recovery_trend_available"
        in summary.trend_comparison.reason_codes
    )


def test_reason_codes_and_limitations_populate_when_confidence_low(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for days_ago in [0, 1, 2]:
        _insert_checkin(target_date=_day(days_ago), sleep=None, energy=6, soreness=3)

    summary = build_recovery_intelligence(user_id=1, target_date="2026-06-14")

    assert summary.confidence in {"Low", "Limited"}
    assert summary.reason_codes
    assert "sleep_data_unavailable" in summary.reason_codes
