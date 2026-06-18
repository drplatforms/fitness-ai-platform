"""Seed repeatable QA users for longitudinal cognition testing.

Run from the project root:
    python scripts/seed_qa_scenarios.py

The script only touches QA users 101-105 and is safe to rerun.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database  # noqa:  E402

QA_USER_IDS = tuple(range(101, 106))
TODAY = date.today()


@dataclass(frozen=True)
class QAUser:
    user_id: int
    name: str
    scenario: str
    primary_goal: str
    starting_weight: float
    goal_weight: float


QA_USERS = [
    QAUser(
        user_id=101,
        name="QA Under-Recovered Lifter",
        scenario="Under-recovered lifter",
        primary_goal="strength_and_recomposition",
        starting_weight=190.0,
        goal_weight=180.0,
    ),
    QAUser(
        user_id=102,
        name="QA Well-Recovered Baseline",
        scenario="Well-recovered baseline",
        primary_goal="strength_progression",
        starting_weight=178.0,
        goal_weight=178.0,
    ),
    QAUser(
        user_id=103,
        name="QA Nutrition Training Mismatch",
        scenario="Nutrition/training mismatch",
        primary_goal="performance",
        starting_weight=185.0,
        goal_weight=182.0,
    ),
    QAUser(
        user_id=104,
        name="QA Improving After Deload",
        scenario="Improving after deload",
        primary_goal="strength_progression",
        starting_weight=188.0,
        goal_weight=184.0,
    ),
    QAUser(
        user_id=105,
        name="QA Messy Incomplete Logging",
        scenario="Messy/incomplete logging",
        primary_goal="fat_loss",
        starting_weight=200.0,
        goal_weight=185.0,
    ),
]

FOODS = {
    "QA Complete Performance Meal": {
        "Calories": 650,
        "Protein": 42,
        "Carbohydrates": 78,
        "Fat": 18,
        "Sodium": 720,
        "Potassium": 820,
        "Magnesium": 95,
        "Calcium": 220,
        "Zinc": 5,
    },
    "QA Recovery Shake": {
        "Calories": 420,
        "Protein": 38,
        "Carbohydrates": 48,
        "Fat": 8,
        "Sodium": 280,
        "Potassium": 520,
        "Magnesium": 70,
        "Calcium": 240,
        "Zinc": 3,
    },
    "QA Low Carb Protein Snack": {
        "Calories": 220,
        "Protein": 28,
        "Carbohydrates": 8,
        "Fat": 7,
        "Sodium": 360,
        "Potassium": 260,
        "Magnesium": 35,
        "Calcium": 160,
        "Zinc": 2,
    },
    "QA Incomplete Protein Entry": {
        "Protein": 32,
    },
    "QA Incomplete Carb Entry": {
        "Carbohydrates": 35,
    },
    "QA Suspicious Micro Entry": {
        "Potassium": 25000,
        "Magnesium": 9000,
        "Zinc": 450,
        "Vitamin D": 9999,
    },
}

EXERCISES = [
    "Barbell Squat",
    "Barbell Bench Press",
    "Deadlift",
    "Overhead Press",
    "Barbell Row",
    "Romanian Deadlift",
    "Leg Press",
    "Clean and Jerk",
]


def _iso(day: date) -> str:
    return day.isoformat()


def _timestamp(day: date, hour: int = 8) -> str:
    return (
        datetime.combine(day, datetime.min.time()).replace(hour=hour).isoformat(sep=" ")
    )


def _get_nutrient_ids(cursor) -> dict[str, int]:
    cursor.execute("SELECT id, name FROM nutrients")
    return {row["name"]: row["id"] for row in cursor.fetchall()}


def _get_exercise_ids(cursor) -> dict[str, int]:
    cursor.execute("SELECT id, name FROM exercises")
    return {row["name"]: row["id"] for row in cursor.fetchall()}


def _ensure_foods(cursor) -> dict[str, int]:
    nutrient_ids = _get_nutrient_ids(cursor)
    food_ids: dict[str, int] = {}

    for food_name, nutrients in FOODS.items():
        cursor.execute("INSERT OR IGNORE INTO foods (name) VALUES (?)", (food_name,))
        cursor.execute("SELECT id FROM foods WHERE name = ?", (food_name,))
        food_id = cursor.fetchone()["id"]
        food_ids[food_name] = food_id

        cursor.execute("DELETE FROM food_nutrients WHERE food_id = ?", (food_id,))
        for nutrient_name, amount in nutrients.items():
            nutrient_id = nutrient_ids[nutrient_name]
            cursor.execute(
                """
                INSERT INTO food_nutrients (food_id, nutrient_id, amount_per_100g)
                VALUES (?, ?, ?)
                """,
                (food_id, nutrient_id, amount),
            )

    return food_ids


def _clear_existing_qa_data(cursor) -> None:
    placeholders = ",".join("?" for _ in QA_USER_IDS)

    cursor.execute(
        f"""
        DELETE FROM workout_execution_set_actuals
        WHERE workout_execution_session_id IN (
            SELECT id
            FROM workout_execution_sessions
            WHERE user_id IN ({placeholders})
        )
        """,
        QA_USER_IDS,
    )
    cursor.execute(
        f"""
        DELETE FROM planned_workout_exercises
        WHERE workout_plan_instance_id IN (
            SELECT id FROM workout_plan_instances WHERE user_id IN ({placeholders})
        )
        """,
        QA_USER_IDS,
    )
    cursor.execute(
        f"""
        DELETE FROM workout_execution_sessions
        WHERE workout_plan_instance_id IN (
            SELECT id FROM workout_plan_instances WHERE user_id IN ({placeholders})
        )
        """,
        QA_USER_IDS,
    )
    cursor.execute(
        f"DELETE FROM workout_plan_instances WHERE user_id IN ({placeholders})",
        QA_USER_IDS,
    )
    cursor.execute(
        f"""
        DELETE FROM workout_sets
        WHERE workout_session_id IN (
            SELECT id FROM workout_sessions WHERE user_id IN ({placeholders})
        )
        """,
        QA_USER_IDS,
    )
    cursor.execute(
        f"DELETE FROM workout_sessions WHERE user_id IN ({placeholders})", QA_USER_IDS
    )
    cursor.execute(
        f"DELETE FROM food_entries WHERE user_id IN ({placeholders})", QA_USER_IDS
    )
    cursor.execute(
        f"DELETE FROM daily_checkins WHERE user_id IN ({placeholders})", QA_USER_IDS
    )
    cursor.execute(
        f"DELETE FROM recovery_reports WHERE user_id IN ({placeholders})", QA_USER_IDS
    )
    cursor.execute(
        f"DELETE FROM health_reports WHERE user_id IN ({placeholders})", QA_USER_IDS
    )
    cursor.execute(f"DELETE FROM users WHERE id IN ({placeholders})", QA_USER_IDS)


def _seed_users(cursor) -> None:
    for user in QA_USERS:
        cursor.execute(
            """
            INSERT INTO users (
                id,
                name,
                gender,
                age,
                height_cm,
                starting_weight,
                goal_weight,
                primary_goal,
                activity_level
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user.user_id,
                user.name,
                "QA",
                35,
                177.0,
                user.starting_weight,
                user.goal_weight,
                user.primary_goal,
                "moderate",
            ),
        )


def _seed_recovery_series(
    cursor,
    user_id: int,
    days: int,
    start_weight: float,
    sleep_values: Iterable[float],
    energy_values: Iterable[int],
    soreness_values: Iterable[int],
    note: str,
) -> None:
    sleep_list = list(sleep_values)
    energy_list = list(energy_values)
    soreness_list = list(soreness_values)

    for index in range(days):
        day = TODAY - timedelta(days=days - index - 1)
        weight = start_weight + (index * 0.08)
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
                _iso(day),
                round(weight, 1),
                sleep_list[index % len(sleep_list)],
                energy_list[index % len(energy_list)],
                soreness_list[index % len(soreness_list)],
                "qa",
                note,
                _timestamp(day),
            ),
        )


def _seed_food_entries(
    cursor, user_id: int, food_ids: dict[str, int], plan: list[tuple[str, float, int]]
) -> None:
    for food_name, grams, days_ago in plan:
        day = TODAY - timedelta(days=days_ago)
        cursor.execute(
            """
            INSERT INTO food_entries (user_id, food_id, grams, entry_date, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, food_ids[food_name], grams, _iso(day), _timestamp(day, hour=12)),
        )


def _seed_workout(
    cursor,
    user_id: int,
    exercise_ids: dict[str, int],
    workout_name: str,
    days_ago: int,
    rir: int,
    load_multiplier: float,
    duration_minutes: int = 55,
) -> None:
    day = TODAY - timedelta(days=days_ago)
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
            _iso(day),
            workout_name,
            duration_minutes,
            f"QA seeded workout at RIR {rir}",
            _timestamp(day, hour=18),
        ),
    )
    session_id = cursor.lastrowid

    workout_sets = [
        ("Barbell Squat", 5, 185 * load_multiplier),
        ("Barbell Bench Press", 6, 155 * load_multiplier),
        ("Barbell Row", 8, 135 * load_multiplier),
    ]

    if "deadlift" in workout_name.lower() or load_multiplier >= 1.15:
        workout_sets.append(("Deadlift", 4, 245 * load_multiplier))

    for set_number, (exercise_name, reps, weight) in enumerate(workout_sets, start=1):
        cursor.execute(
            """
            INSERT INTO workout_sets (
                workout_session_id,
                exercise_id,
                set_number,
                reps,
                weight,
                rir,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                exercise_ids[exercise_name],
                set_number,
                reps,
                round(weight, 1),
                rir,
                _timestamp(day, hour=18),
            ),
        )


def _seed_under_recovered(cursor, food_ids, exercise_ids) -> None:
    _seed_recovery_series(
        cursor,
        user_id=101,
        days=42,
        start_weight=190.0,
        sleep_values=[5.4, 5.7, 5.2, 5.9, 5.5],
        energy_values=[4, 3, 4, 3],
        soreness_values=[7, 8, 7, 8],
        note="QA under-recovered trend: low sleep, rising soreness, declining energy.",
    )
    _seed_food_entries(
        cursor,
        101,
        food_ids,
        [
            ("QA Incomplete Protein Entry", 150, 0),
            ("QA Low Carb Protein Snack", 100, 0),
            ("QA Incomplete Carb Entry", 80, 1),
        ],
    )
    for days_ago in [1, 3, 5, 8, 11, 15]:
        _seed_workout(
            cursor, 101, exercise_ids, "QA Heavy Low-RIR Session", days_ago, 1, 1.2
        )


def _seed_well_recovered(cursor, food_ids, exercise_ids) -> None:
    _seed_recovery_series(
        cursor,
        user_id=102,
        days=42,
        start_weight=178.0,
        sleep_values=[7.6, 7.9, 8.1, 7.8],
        energy_values=[8, 8, 9, 8],
        soreness_values=[2, 3, 2, 2],
        note="QA baseline: supportive recovery and consistent energy.",
    )
    _seed_food_entries(
        cursor,
        102,
        food_ids,
        [
            ("QA Complete Performance Meal", 150, 0),
            ("QA Recovery Shake", 100, 0),
            ("QA Complete Performance Meal", 120, 1),
        ],
    )
    for days_ago in [1, 4, 7, 10, 14]:
        _seed_workout(
            cursor,
            102,
            exercise_ids,
            "QA Moderate Progression Session",
            days_ago,
            2,
            0.95,
        )


def _seed_nutrition_training_mismatch(cursor, food_ids, exercise_ids) -> None:
    _seed_recovery_series(
        cursor,
        user_id=103,
        days=35,
        start_weight=185.0,
        sleep_values=[7.0, 7.2, 7.4, 7.1],
        energy_values=[6, 6, 5, 6],
        soreness_values=[5, 6, 5, 6],
        note="QA mismatch: decent sleep with hard training and incomplete nutrition.",
    )
    _seed_food_entries(
        cursor,
        103,
        food_ids,
        [
            ("QA Incomplete Protein Entry", 90, 0),
            ("QA Incomplete Carb Entry", 60, 0),
            ("QA Low Carb Protein Snack", 80, 1),
        ],
    )
    for days_ago in [1, 2, 5, 8, 12]:
        _seed_workout(
            cursor,
            103,
            exercise_ids,
            "QA Hard Training Incomplete Fuel",
            days_ago,
            1,
            1.15,
        )


def _seed_improving_after_deload(cursor, food_ids, exercise_ids) -> None:
    _seed_recovery_series(
        cursor,
        user_id=104,
        days=28,
        start_weight=188.0,
        sleep_values=[6.0, 6.2, 7.1, 7.4, 7.6, 7.7, 7.8],
        energy_values=[4, 5, 6, 7, 7, 8, 8],
        soreness_values=[8, 7, 6, 4, 3, 3, 2],
        note="QA improving trend: deload and recovery behavior improving recently.",
    )
    _seed_food_entries(
        cursor,
        104,
        food_ids,
        [
            ("QA Complete Performance Meal", 130, 0),
            ("QA Recovery Shake", 100, 0),
            ("QA Complete Performance Meal", 110, 1),
        ],
    )
    for days_ago, rir, load in [
        (18, 1, 1.15),
        (14, 1, 1.1),
        (7, 3, 0.85),
        (3, 3, 0.85),
        (1, 2, 0.9),
    ]:
        _seed_workout(
            cursor,
            104,
            exercise_ids,
            "QA Deload Improvement Session",
            days_ago,
            rir,
            load,
        )


def _seed_messy_incomplete_logging(cursor, food_ids, exercise_ids) -> None:
    _seed_recovery_series(
        cursor,
        user_id=105,
        days=21,
        start_weight=200.0,
        sleep_values=[6.4, 7.0, 5.9, 6.8],
        energy_values=[5, 7, 4, 6],
        soreness_values=[3, 6, 4, 7],
        note="QA messy logging: inconsistent inputs and suspicious micronutrient values.",
    )
    _seed_food_entries(
        cursor,
        105,
        food_ids,
        [
            ("QA Suspicious Micro Entry", 100, 0),
            ("QA Incomplete Protein Entry", 75, 0),
            ("QA Incomplete Carb Entry", 40, 2),
        ],
    )
    for days_ago, rir, load in [(2, 4, 0.75), (9, 1, 1.2), (17, 3, 0.8)]:
        _seed_workout(
            cursor,
            105,
            exercise_ids,
            "QA Inconsistent Logging Session",
            days_ago,
            rir,
            load,
        )


def seed_qa_scenarios() -> list[QAUser]:
    database.initialize_database()
    conn = database.get_connection()
    cursor = conn.cursor()

    _clear_existing_qa_data(cursor)
    _seed_users(cursor)
    food_ids = _ensure_foods(cursor)
    exercise_ids = _get_exercise_ids(cursor)

    missing_exercises = [name for name in EXERCISES if name not in exercise_ids]
    if missing_exercises:
        names = ", ".join(missing_exercises)
        raise RuntimeError(f"Missing required seeded exercises: {names}")

    _seed_under_recovered(cursor, food_ids, exercise_ids)
    _seed_well_recovered(cursor, food_ids, exercise_ids)
    _seed_nutrition_training_mismatch(cursor, food_ids, exercise_ids)
    _seed_improving_after_deload(cursor, food_ids, exercise_ids)
    _seed_messy_incomplete_logging(cursor, food_ids, exercise_ids)

    conn.commit()
    conn.close()

    return QA_USERS


def main() -> None:
    seeded_users = seed_qa_scenarios()

    print("Seeded QA scenarios:")
    for user in seeded_users:
        print(f"- user_id={user.user_id}: {user.scenario} ({user.name})")


if __name__ == "__main__":
    main()
