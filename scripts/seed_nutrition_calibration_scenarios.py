# ruff: noqa: E402
"""Seed deterministic nutrition calibration QA scenarios.

Run from the project root:
    python scripts/seed_nutrition_calibration_scenarios.py

The script is safe to rerun. It seeds QA users 102-105 with fixed-date
nutrition/bodyweight/training evidence for trend-window and calibration QA. It
only clears seed-owned check-ins/workouts and canonical food log rows for these
QA users inside the fixed scenario window.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database  # noqa: E402
from scripts.seed_user_profiles import seed_user_profiles  # noqa: E402
from services.food_normalization_service import (  # noqa: E402
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_service import add_canonical_food_entry  # noqa: E402

SEED_MARKER = "seed_nutrition_calibration_scenarios_v1"
SEED_END_DATE = date(2026, 6, 6)
SCENARIO_USER_IDS = (102, 103, 104, 105)
MAX_WINDOW_DAYS = 28


@dataclass(frozen=True)
class CalibrationScenarioSeedResult:
    user_id: int
    scenario: str
    end_date: str
    window_days: int
    expected_readiness: str


def _date(days_ago: int) -> str:
    return (SEED_END_DATE - timedelta(days=days_ago)).isoformat()


def _timestamp(days_ago: int = 0, hour: int = 8) -> str:
    day = SEED_END_DATE - timedelta(days=days_ago)
    return (
        datetime.combine(day, datetime.min.time()).replace(hour=hour).isoformat(sep=" ")
    )


def _canonical_food_id(query: str) -> int:
    results = search_canonical_foods(query, limit=1)
    if not results:
        raise RuntimeError(f"Canonical food is required for seed scenario: {query}")
    return int(results[0].canonical_food.id)


def _clear_seeded_scenario_data() -> None:
    start_date = _date(MAX_WINDOW_DAYS - 1)
    end_date = SEED_END_DATE.isoformat()
    placeholders = ",".join("?" for _ in SCENARIO_USER_IDS)

    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"""
        DELETE FROM food_entries
        WHERE user_id IN ({placeholders})
          AND entry_date BETWEEN ? AND ?
          AND food_id IN (
              SELECT id
              FROM foods
              WHERE name LIKE 'Canonical:%'
          )
        """,
        (*SCENARIO_USER_IDS, start_date, end_date),
    )

    cursor.execute(
        f"""
        DELETE FROM daily_checkins
        WHERE user_id IN ({placeholders})
          AND notes LIKE ?
        """,
        (*SCENARIO_USER_IDS, f"{SEED_MARKER}:%"),
    )

    cursor.execute(
        f"""
        SELECT id
        FROM workout_sessions
        WHERE user_id IN ({placeholders})
          AND notes LIKE ?
        """,
        (*SCENARIO_USER_IDS, f"{SEED_MARKER}:%"),
    )
    workout_session_ids = [int(row["id"]) for row in cursor.fetchall()]
    if workout_session_ids:
        session_placeholders = ",".join("?" for _ in workout_session_ids)
        cursor.execute(
            f"""
            DELETE FROM workout_sets
            WHERE workout_session_id IN ({session_placeholders})
            """,
            workout_session_ids,
        )
        cursor.execute(
            f"""
            DELETE FROM workout_sessions
            WHERE id IN ({session_placeholders})
            """,
            workout_session_ids,
        )

    conn.commit()
    conn.close()


def _log_complete_day(user_id: int, target_date: str) -> None:
    add_canonical_food_entry(
        user_id=user_id,
        canonical_food_id=_canonical_food_id("chicken breast"),
        grams=160,
        entry_date=target_date,
    )
    add_canonical_food_entry(
        user_id=user_id,
        canonical_food_id=_canonical_food_id("rice"),
        grams=220,
        entry_date=target_date,
    )
    add_canonical_food_entry(
        user_id=user_id,
        canonical_food_id=_canonical_food_id("olive oil"),
        grams=10,
        entry_date=target_date,
    )


def _log_partial_day(user_id: int, target_date: str) -> None:
    add_canonical_food_entry(
        user_id=user_id,
        canonical_food_id=_canonical_food_id("banana"),
        grams=120,
        entry_date=target_date,
    )


def _insert_weight(user_id: int, target_date: str, body_weight: float) -> None:
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
            body_weight,
            7.5,
            4,
            2,
            "steady",
            f"{SEED_MARKER}: calibration scenario weigh-in",
            f"{target_date} 08:00:00",
        ),
    )
    conn.commit()
    conn.close()


def _insert_training_day(user_id: int, target_date: str) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workout_sessions (
            user_id,
            workout_date,
            workout_name,
            duration_minutes,
            notes,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            target_date,
            "Seeded Calibration Scenario Training Session",
            50,
            f"{SEED_MARKER}: deterministic training context",
            f"{target_date} 18:00:00",
        ),
    )
    conn.commit()
    conn.close()


def _set_user_context(
    user_id: int,
    *,
    primary_goal: str | None,
    activity_level: str | None,
    goal_weight: float | None = None,
) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE users
        SET primary_goal = ?,
            activity_level = ?,
            goal_weight = COALESCE(?, goal_weight)
        WHERE id = ?
        """,
        (primary_goal, activity_level, goal_weight, user_id),
    )
    conn.commit()
    conn.close()


def _seed_user_102_strong() -> None:
    for days_ago in range(23):
        _log_complete_day(102, _date(days_ago))
    for days_ago in range(23, 25):
        _log_partial_day(102, _date(days_ago))

    for index, days_ago in enumerate([27, 24, 21, 18, 15, 12, 9, 6, 4, 2, 1, 0]):
        _insert_weight(102, _date(days_ago), 178.0 + (index % 3 - 1) * 0.1)

    for days_ago in [24, 17, 10, 3]:
        _insert_training_day(102, _date(days_ago))


def _seed_user_103_early_signal() -> None:
    for days_ago in range(8):
        _log_complete_day(103, _date(days_ago))
    for days_ago in range(8, 10):
        _log_partial_day(103, _date(days_ago))

    for index, days_ago in enumerate([13, 9, 5, 0]):
        _insert_weight(103, _date(days_ago), 185.0 - index * 0.2)

    _insert_training_day(103, _date(2))


def _seed_user_104_not_ready() -> None:
    _log_partial_day(104, _date(0))
    # Intentionally no seed-owned bodyweight check-ins for this missing-bodyweight
    # scenario. The user profile also lacks bodyweight context.
    _insert_training_day(104, _date(1))


def _seed_user_105_data_quality_limited() -> None:
    for days_ago in [0, 3, 9, 18]:
        _log_partial_day(105, _date(days_ago))
    for days_ago in [5, 14]:
        _log_complete_day(105, _date(days_ago))

    for index, days_ago in enumerate([21, 7]):
        _insert_weight(105, _date(days_ago), 200.0 - index * 0.4)

    _insert_training_day(105, _date(6))


def seed_nutrition_calibration_scenarios() -> list[CalibrationScenarioSeedResult]:
    database.initialize_database()
    seed_starter_canonical_foods()
    seed_user_profiles()
    _clear_seeded_scenario_data()
    _set_user_context(
        103,
        primary_goal="strength_progression",
        activity_level="moderate",
        goal_weight=185.0,
    )

    _seed_user_102_strong()
    _seed_user_103_early_signal()
    _seed_user_104_not_ready()
    _seed_user_105_data_quality_limited()

    return [
        CalibrationScenarioSeedResult(
            user_id=102,
            scenario="28-day strong/usable calibration QA scenario",
            end_date=SEED_END_DATE.isoformat(),
            window_days=28,
            expected_readiness="strong_or_usable",
        ),
        CalibrationScenarioSeedResult(
            user_id=103,
            scenario="14-day early-signal calibration QA scenario",
            end_date=SEED_END_DATE.isoformat(),
            window_days=14,
            expected_readiness="early_signal",
        ),
        CalibrationScenarioSeedResult(
            user_id=104,
            scenario="not-ready sparse/missing-bodyweight calibration QA scenario",
            end_date=SEED_END_DATE.isoformat(),
            window_days=28,
            expected_readiness="not_ready",
        ),
        CalibrationScenarioSeedResult(
            user_id=105,
            scenario="data-quality-limited calibration QA scenario",
            end_date=SEED_END_DATE.isoformat(),
            window_days=28,
            expected_readiness="not_ready_or_early_signal_with_limitations",
        ),
    ]


def main() -> None:
    seeded = seed_nutrition_calibration_scenarios()
    print("Seeded nutrition calibration scenarios:")
    for scenario in seeded:
        print(
            "- "
            f"user_id={scenario.user_id}: {scenario.scenario}; "
            f"end_date={scenario.end_date}; window_days={scenario.window_days}; "
            f"expected_readiness={scenario.expected_readiness}"
        )


if __name__ == "__main__":
    main()
