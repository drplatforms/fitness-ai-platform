from __future__ import annotations

from datetime import date, timedelta

import database
from models.nutrition_trend_models import (
    BODYWEIGHT_TREND_DECREASING,
    BODYWEIGHT_TREND_INCREASING,
    BODYWEIGHT_TREND_STABLE,
    BODYWEIGHT_TREND_UNAVAILABLE,
    CALIBRATION_READINESS_EARLY_SIGNAL,
    CALIBRATION_READINESS_NOT_READY,
    CALIBRATION_READINESS_STRONG,
    CALIBRATION_READINESS_USABLE,
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_CONSISTENCY_STRONG,
    LOGGING_CONSISTENCY_USABLE,
)
from services.food_normalization_service import (
    ensure_food_normalization_tables,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_service import add_canonical_food_entry
from services.nutrition_trend_service import (
    build_nutrition_trend_days,
    build_nutrition_trend_window,
    summarize_bodyweight_trend,
    summarize_nutrition_intake_trend,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()
    seed_starter_canonical_foods()
    _set_profile_context(1)


def _today() -> date:
    return date(2026, 6, 6)


def _day(days_ago: int) -> str:
    return (_today() - timedelta(days=days_ago)).isoformat()


def _canonical_id(query: str) -> int:
    results = search_canonical_foods(query, limit=1)
    assert results
    return int(results[0].canonical_food.id)


def _set_profile_context(
    user_id: int,
    *,
    primary_goal: str | None = "strength_and_recomposition",
    activity_level: str | None = "moderate",
) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE users
        SET primary_goal = ?, activity_level = ?, goal_weight = ?, starting_weight = ?
        WHERE id = ?
        """,
        (primary_goal, activity_level, 180.0, 190.0, user_id),
    )
    conn.commit()
    conn.close()


def _log_complete_day(user_id: int, target_date: str) -> None:
    add_canonical_food_entry(user_id, _canonical_id("chicken breast"), 150, target_date)
    add_canonical_food_entry(user_id, _canonical_id("rice"), 200, target_date)
    add_canonical_food_entry(user_id, _canonical_id("olive oil"), 10, target_date)


def _log_partial_day(user_id: int, target_date: str) -> None:
    add_canonical_food_entry(user_id, _canonical_id("banana"), 100, target_date)


def _log_calories_only_food(user_id: int, target_date: str) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO foods (name) VALUES (?)", ("Calories Only",))
    cursor.execute("SELECT id FROM foods WHERE name = ?", ("Calories Only",))
    food_id = int(cursor.fetchone()["id"])
    cursor.execute("SELECT id FROM nutrients WHERE name = ?", ("Calories",))
    calorie_nutrient_id = int(cursor.fetchone()["id"])
    cursor.execute(
        """
        INSERT INTO food_nutrients (food_id, nutrient_id, amount_per_100g)
        VALUES (?, ?, ?)
        """,
        (food_id, calorie_nutrient_id, 200.0),
    )
    cursor.execute(
        """
        INSERT INTO food_entries (user_id, food_id, grams, entry_date)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, food_id, 100.0, target_date),
    )
    conn.commit()
    conn.close()


def _insert_weight(user_id: int, target_date: str, weight: float) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO daily_checkins (user_id, checkin_date, body_weight, sleep_hours, energy_level, soreness_level)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, target_date, weight, 7.5, 4, 2),
    )
    conn.commit()
    conn.close()


def _insert_training_day(user_id: int, target_date: str) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workout_sessions (user_id, workout_date, workout_name, duration_minutes, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, target_date, "Trend Service Test Workout", 45, "test fixture"),
    )
    conn.commit()
    conn.close()


def _user_profile_snapshot(user_id: int) -> tuple:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT primary_goal, activity_level, goal_weight, starting_weight
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return tuple(row) if row else ()


def test_service_builds_insufficient_data_trend_window(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    window = build_nutrition_trend_window(
        1,
        end_date=_today().isoformat(),
        window_days=7,
    )

    assert window.window_days == 7
    assert window.logged_day_count == 0
    assert window.no_log_day_count == 7
    assert window.intake_trend_summary.average_calories is None
    assert (
        window.bodyweight_trend_summary.trend_direction == BODYWEIGHT_TREND_UNAVAILABLE
    )
    assert (
        window.calibration_readiness.readiness_level == CALIBRATION_READINESS_NOT_READY
    )
    assert window.calibration_readiness.calibration_allowed is False
    assert "minimum_window_not_met" in window.reason_codes


def test_service_builds_14_day_early_context_window(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for days_ago in range(8):
        _log_complete_day(1, _day(days_ago))
    for days_ago in range(8, 10):
        _log_partial_day(1, _day(days_ago))
    for index, days_ago in enumerate([13, 9, 5, 0]):
        _insert_weight(1, _day(days_ago), 190.0 - index * 0.2)
    _insert_training_day(1, _day(2))

    window = build_nutrition_trend_window(
        1, end_date=_today().isoformat(), window_days=14
    )

    assert window.window_days == 14
    assert window.logged_day_count == 10
    assert window.complete_logging_day_count == 8
    assert window.partial_logging_day_count == 2
    assert window.no_log_day_count == 4
    assert (
        window.intake_trend_summary.logging_consistency_status
        == LOGGING_CONSISTENCY_USABLE
    )
    assert (
        window.calibration_readiness.readiness_level
        == CALIBRATION_READINESS_EARLY_SIGNAL
    )
    assert window.calibration_readiness.minimum_window_met is True
    assert window.calibration_readiness.preferred_window_met is False
    assert window.calibration_readiness.calibration_allowed is False


def test_service_builds_28_day_preferred_context_window(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for days_ago in range(23):
        _log_complete_day(1, _day(days_ago))
    for days_ago in range(23, 25):
        _log_partial_day(1, _day(days_ago))
    for index, days_ago in enumerate([27, 24, 21, 18, 15, 12, 9, 6, 4, 2, 1, 0]):
        _insert_weight(1, _day(days_ago), 190.0 - index * 0.15)
    _insert_training_day(1, _day(3))

    window = build_nutrition_trend_window(
        1, end_date=_today().isoformat(), window_days=28
    )

    assert window.window_days == 28
    assert window.complete_logging_day_count == 23
    assert window.no_log_day_count == 3
    assert (
        window.intake_trend_summary.logging_consistency_status
        == LOGGING_CONSISTENCY_STRONG
    )
    assert window.bodyweight_trend_summary.weigh_in_count == 12
    assert window.calibration_readiness.readiness_level == CALIBRATION_READINESS_STRONG
    assert window.calibration_readiness.calibration_allowed is True
    assert "preferred_window_met" in window.reason_codes


def test_no_log_and_partial_days_are_counted_separately(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _log_complete_day(1, _day(0))
    _log_partial_day(1, _day(1))

    window = build_nutrition_trend_window(
        1, end_date=_today().isoformat(), window_days=4
    )

    assert window.complete_logging_day_count == 1
    assert window.partial_logging_day_count == 1
    assert window.logged_day_count == 2
    assert window.no_log_day_count == 2
    completeness_by_date = {
        day.date: day.logging_completeness for day in window.trend_days
    }
    assert completeness_by_date[_day(3)] == LOGGING_COMPLETENESS_NO_LOGS
    assert completeness_by_date[_day(1)] == LOGGING_COMPLETENESS_PARTIAL_DAY
    assert completeness_by_date[_day(0)] == LOGGING_COMPLETENESS_COMPLETE_ENOUGH


def test_missing_nutrient_values_are_not_coerced_to_zero(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _log_calories_only_food(1, _day(0))

    trend_days = build_nutrition_trend_days(
        user_id=1,
        start_date=_day(0),
        end_date=_day(0),
    )

    day = trend_days[0]
    assert day.logged_calories == 200.0
    assert day.logged_protein is None
    assert day.logged_carbohydrate is None
    assert day.logged_fat is None
    assert day.logging_completeness == LOGGING_COMPLETENESS_PARTIAL_DAY


def test_average_macros_are_calculated_only_from_present_logged_values(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _log_complete_day(1, _day(0))
    _log_calories_only_food(1, _day(1))

    trend_days = build_nutrition_trend_days(
        user_id=1,
        start_date=_day(1),
        end_date=_day(0),
    )
    summary = summarize_nutrition_intake_trend(trend_days)

    complete_day = next(day for day in trend_days if day.date == _day(0))
    assert summary.average_protein_g == complete_day.logged_protein
    assert summary.average_fat_g == complete_day.logged_fat
    assert summary.average_calories is not None
    assert summary.average_calories > complete_day.logged_calories / 2


def test_bodyweight_trend_unavailable_is_distinct_from_stable_trend(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    unavailable = summarize_bodyweight_trend(
        user_id=1,
        start_date=_day(13),
        end_date=_day(0),
    )
    _insert_weight(1, _day(13), 190.0)
    _insert_weight(1, _day(0), 190.1)
    stable = summarize_bodyweight_trend(
        user_id=1,
        start_date=_day(13),
        end_date=_day(0),
    )

    assert unavailable.trend_direction == BODYWEIGHT_TREND_UNAVAILABLE
    assert stable.trend_direction == BODYWEIGHT_TREND_STABLE
    assert stable.weigh_in_count == 2


def test_bodyweight_increasing_and_decreasing_trends_can_be_represented(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_weight(1, _day(14), 190.0)
    _insert_weight(1, _day(0), 187.5)
    decreasing = summarize_bodyweight_trend(
        user_id=1,
        start_date=_day(14),
        end_date=_day(0),
    )

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM daily_checkins WHERE user_id = ?", (1,))
    conn.commit()
    conn.close()
    _insert_weight(1, _day(14), 190.0)
    _insert_weight(1, _day(0), 192.5)
    increasing = summarize_bodyweight_trend(
        user_id=1,
        start_date=_day(14),
        end_date=_day(0),
    )

    assert decreasing.trend_direction == BODYWEIGHT_TREND_DECREASING
    assert increasing.trend_direction == BODYWEIGHT_TREND_INCREASING


def test_calibration_readiness_can_be_not_ready_early_usable_and_strong(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    insufficient = build_nutrition_trend_window(
        1, end_date=_today().isoformat(), window_days=7
    )

    for days_ago in range(16):
        _log_complete_day(1, _day(days_ago))
    for index, days_ago in enumerate([20, 14, 7, 0]):
        _insert_weight(1, _day(days_ago), 190.0 - index * 0.1)
    _insert_training_day(1, _day(2))
    early = build_nutrition_trend_window(
        1, end_date=_today().isoformat(), window_days=21
    )

    for days_ago in range(16, 21):
        _log_partial_day(1, _day(days_ago))
    usable = build_nutrition_trend_window(
        1, end_date=_today().isoformat(), window_days=28
    )

    for days_ago in range(16, 28):
        _log_complete_day(1, _day(days_ago))
    for index, days_ago in enumerate([27, 24, 21, 18, 15, 12, 9, 6, 4, 2, 1, 0]):
        _insert_weight(1, _day(days_ago), 191.0 - index * 0.1)
    strong = build_nutrition_trend_window(
        1, end_date=_today().isoformat(), window_days=28
    )

    assert (
        insufficient.calibration_readiness.readiness_level
        == CALIBRATION_READINESS_NOT_READY
    )
    assert (
        early.calibration_readiness.readiness_level
        == CALIBRATION_READINESS_EARLY_SIGNAL
    )
    assert usable.calibration_readiness.readiness_level in {
        CALIBRATION_READINESS_USABLE,
        CALIBRATION_READINESS_STRONG,
    }
    assert strong.calibration_readiness.readiness_level == CALIBRATION_READINESS_STRONG


def test_no_target_mutation_occurs_when_building_trend_window(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    before = _user_profile_snapshot(1)

    build_nutrition_trend_window(1, end_date=_today().isoformat(), window_days=14)

    after = _user_profile_snapshot(1)
    assert after == before
