"""Seed deterministic six-month QA data for users 101-105.

Run from the project root:
    python scripts/seed_longitudinal_qa_data.py

The seed is official, deterministic for a given end date, and safe to rerun. It
clears and reseeds only QA-owned per-user rows for users 101-105. It does not
modify user 1, non-QA users, canonical foods, exercise catalog rows, or global
reference data.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database  # noqa: E402
from services.exercise_catalog_service import seed_exercise_catalog  # noqa: E402
from services.food_normalization_service import (  # noqa: E402
    ensure_starter_canonical_foods_seeded,
)
from services.workout_plan_persistence_service import (  # noqa: E402
    ensure_workout_plan_persistence_tables,
)

SEED_MARKER = "longitudinal_qa_seed_v1"
QA_USER_IDS = (101, 102, 103, 104, 105)
DEFAULT_END_DATE = date(2026, 6, 14)
DEFAULT_DAY_COUNT = 180

PRODUCT_WORKOUT_TITLES = (
    "Recovery-Aware Strength Session",
    "Gradual Progression Strength Session",
    "Controlled Strength Practice",
    "Controlled Progression Session",
    "Manageable Baseline Session",
)

HOME_GYM_EQUIPMENT = [
    "bodyweight",
    "dumbbell",
    "adjustable_bench",
    "barbell",
    "ez_bar",
    "rack",
    "plates",
    "pull_up_bar",
    "resistance_band",
    "cable",
    "treadmill",
    "bike",
]

FORBIDDEN_PRODUCT_CONTEXT_TERMS = (
    "QA",
    "Seeded",
    "Test",
    "Placeholder",
    "Dummy",
    "Synthetic",
)

CANONICAL_FOOD_NAMES = (
    "Chicken Breast, Cooked, Skinless",
    "Turkey Breast, Cooked",
    "Tuna, Canned in Water",
    "Greek Yogurt, Plain",
    "Whey Protein Powder, Generic",
    "White Rice, Cooked",
    "Brown Rice, Cooked",
    "Oats, Dry",
    "Banana",
    "Blueberries",
    "Broccoli, Cooked",
    "Olive Oil",
    "Almonds",
    "Egg, Large",
)


@dataclass(frozen=True)
class LongitudinalQAUser:
    user_id: int
    name: str
    scenario: str
    gender: str | None
    age: int | None
    height_cm: float | None
    starting_weight: float | None
    goal_weight: float | None
    primary_goal: str | None
    activity_level: str | None
    training_environment: str
    training_days_per_week: int


@dataclass(frozen=True)
class SeededLongitudinalQAUser:
    user_id: int
    scenario: str
    recovery_checkins: int
    nutrition_days: int
    nutrition_entries: int
    completed_workouts: int
    actual_sets: int


QA_USERS = (
    LongitudinalQAUser(
        user_id=101,
        name="Recovery Limited Scenario User",
        scenario="recovery_limited",
        gender="Male",
        age=36,
        height_cm=177.0,
        starting_weight=190.0,
        goal_weight=180.0,
        primary_goal="strength_and_recomposition",
        activity_level="moderate",
        training_environment="home_gym",
        training_days_per_week=3,
    ),
    LongitudinalQAUser(
        user_id=102,
        name="Aligned Managed Scenario User",
        scenario="aligned_managed",
        gender="Male",
        age=35,
        height_cm=177.0,
        starting_weight=178.0,
        goal_weight=178.0,
        primary_goal="strength_progression",
        activity_level="moderate",
        training_environment="home_gym",
        training_days_per_week=4,
    ),
    LongitudinalQAUser(
        user_id=103,
        name="Nutrition Training Mismatch Scenario User",
        scenario="nutrition_training_mismatch",
        gender="Male",
        age=34,
        height_cm=178.0,
        starting_weight=185.0,
        goal_weight=182.0,
        primary_goal="performance",
        activity_level="moderate",
        training_environment="home_gym",
        training_days_per_week=3,
    ),
    LongitudinalQAUser(
        user_id=104,
        name="Improving After Deload Scenario User",
        scenario="improving_after_deload",
        gender="Male",
        age=37,
        height_cm=176.0,
        starting_weight=188.0,
        goal_weight=184.0,
        primary_goal="strength_progression",
        activity_level="moderate",
        training_environment="home_gym",
        training_days_per_week=3,
    ),
    LongitudinalQAUser(
        user_id=105,
        name="Data Quality Limited Scenario User",
        scenario="data_quality_limited",
        gender=None,
        age=None,
        height_cm=None,
        starting_weight=200.0,
        goal_weight=185.0,
        primary_goal="fat_loss",
        activity_level=None,
        training_environment="limited_equipment",
        training_days_per_week=2,
    ),
)

BASE_PLAN_EXERCISES = (
    {
        "name": "Dumbbell Bench Press",
        "sets": 3,
        "reps_min": 8,
        "reps_max": 10,
        "rir_min": 2,
        "rir_max": 3,
        "equipment_required": ["dumbbell", "adjustable_bench"],
    },
    {
        "name": "Romanian Deadlift",
        "sets": 3,
        "reps_min": 8,
        "reps_max": 10,
        "rir_min": 2,
        "rir_max": 3,
        "equipment_required": ["barbell"],
    },
    {
        "name": "Barbell Row",
        "sets": 3,
        "reps_min": 8,
        "reps_max": 10,
        "rir_min": 2,
        "rir_max": 3,
        "equipment_required": ["barbell"],
    },
    {
        "name": "Cable Crunch",
        "sets": 2,
        "reps_min": 12,
        "reps_max": 15,
        "rir_min": 2,
        "rir_max": 4,
        "equipment_required": ["cable"],
    },
)


def _parse_date(raw_value: str) -> date:
    try:
        return date.fromisoformat(raw_value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Date must use YYYY-MM-DD format.") from exc


def _iso(day: date) -> str:
    return day.isoformat()


def _timestamp(day: date, hour: int = 8, minute: int = 0) -> str:
    return (
        datetime.combine(day, datetime.min.time())
        .replace(hour=hour, minute=minute)
        .isoformat(sep=" ")
    )


def _date_series(*, end_date: date, day_count: int) -> list[date]:
    start_date = end_date - timedelta(days=day_count - 1)
    return [start_date + timedelta(days=index) for index in range(day_count)]


def _placeholders(values: tuple[int, ...]) -> str:
    return ",".join("?" for _ in values)


def _legacy_nutrient_name(nutrient_name: str) -> str:
    normalized = " ".join(nutrient_name.strip().lower().replace("_", " ").split())
    return {
        "calorie": "Calories",
        "calories": "Calories",
        "energy": "Calories",
        "protein": "Protein",
        "carbohydrate": "Carbohydrates",
        "carbohydrates": "Carbohydrates",
        "carbs": "Carbohydrates",
        "total carbohydrate": "Carbohydrates",
        "fat": "Fat",
        "total fat": "Fat",
        "fiber": "Fiber",
        "sugar": "Sugar",
        "sodium": "Sodium",
        "potassium": "Potassium",
        "magnesium": "Magnesium",
        "calcium": "Calcium",
        "iron": "Iron",
        "vitamin c": "Vitamin C",
        "vitamin d": "Vitamin D",
        "vitamin b12": "Vitamin B12",
        "zinc": "Zinc",
    }.get(normalized, nutrient_name.strip())


def _ensure_legacy_nutrient(cursor, nutrient_name: str, unit: str) -> int:
    legacy_name = _legacy_nutrient_name(nutrient_name)
    cursor.execute(
        "INSERT OR IGNORE INTO nutrients (name, unit) VALUES (?, ?)",
        (legacy_name, unit),
    )
    cursor.execute("SELECT id FROM nutrients WHERE name = ?", (legacy_name,))
    return int(cursor.fetchone()["id"])


def _ensure_legacy_foods_from_canonical(cursor) -> dict[str, int]:
    cursor.execute(
        f"""
        SELECT id, display_name
        FROM canonical_foods
        WHERE display_name IN ({",".join("?" for _ in CANONICAL_FOOD_NAMES)})
          AND active = 1
        """,
        CANONICAL_FOOD_NAMES,
    )
    canonical_rows = cursor.fetchall()
    if len(canonical_rows) < len(CANONICAL_FOOD_NAMES):
        found = {row["display_name"] for row in canonical_rows}
        missing = sorted(set(CANONICAL_FOOD_NAMES) - found)
        raise RuntimeError(f"Missing starter canonical foods: {missing}")

    legacy_food_ids: dict[str, int] = {}
    for row in canonical_rows:
        display_name = row["display_name"]
        legacy_name = f"Canonical: {display_name}"
        cursor.execute("INSERT OR IGNORE INTO foods (name) VALUES (?)", (legacy_name,))
        cursor.execute("SELECT id FROM foods WHERE name = ?", (legacy_name,))
        legacy_food_id = int(cursor.fetchone()["id"])
        legacy_food_ids[display_name] = legacy_food_id

        cursor.execute(
            "DELETE FROM food_nutrients WHERE food_id = ?", (legacy_food_id,)
        )
        cursor.execute(
            """
            SELECT nutrient_name, nutrient_unit, amount_per_100g
            FROM canonical_food_nutrients
            WHERE canonical_food_id = ?
            """,
            (int(row["id"]),),
        )
        for nutrient_row in cursor.fetchall():
            nutrient_id = _ensure_legacy_nutrient(
                cursor,
                nutrient_row["nutrient_name"],
                nutrient_row["nutrient_unit"],
            )
            cursor.execute(
                """
                INSERT INTO food_nutrients (food_id, nutrient_id, amount_per_100g)
                VALUES (?, ?, ?)
                """,
                (legacy_food_id, nutrient_id, float(nutrient_row["amount_per_100g"])),
            )

    return legacy_food_ids


def _clear_existing_qa_user_data(cursor) -> None:
    placeholders = _placeholders(QA_USER_IDS)

    cursor.execute(
        f"""
        DELETE FROM workout_plan_exercise_substitutions
        WHERE workout_plan_instance_id IN (
            SELECT id FROM workout_plan_instances WHERE user_id IN ({placeholders})
        )
        """,
        QA_USER_IDS,
    )
    cursor.execute(
        f"""
        DELETE FROM workout_execution_set_actuals
        WHERE workout_execution_session_id IN (
            SELECT id FROM workout_execution_sessions WHERE user_id IN ({placeholders})
        )
        """,
        QA_USER_IDS,
    )
    cursor.execute(
        f"""
        DELETE FROM workout_execution_sessions
        WHERE user_id IN ({placeholders})
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
    cursor.execute(
        f"DELETE FROM user_equipment_profiles WHERE user_id IN ({placeholders})",
        QA_USER_IDS,
    )


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
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                gender = excluded.gender,
                age = excluded.age,
                height_cm = excluded.height_cm,
                starting_weight = excluded.starting_weight,
                goal_weight = excluded.goal_weight,
                primary_goal = excluded.primary_goal,
                activity_level = excluded.activity_level
            """,
            (
                user.user_id,
                user.name,
                user.gender,
                user.age,
                user.height_cm,
                user.starting_weight,
                user.goal_weight,
                user.primary_goal,
                user.activity_level,
            ),
        )
        cursor.execute(
            """
            INSERT INTO user_equipment_profiles (
                user_id,
                training_environment,
                available_equipment_json,
                unavailable_equipment_json,
                updated_at
            )
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                training_environment = excluded.training_environment,
                available_equipment_json = excluded.available_equipment_json,
                unavailable_equipment_json = excluded.unavailable_equipment_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user.user_id,
                user.training_environment,
                json.dumps(HOME_GYM_EQUIPMENT),
                json.dumps(
                    ["machine"] if user.user_id != 105 else ["machine", "cable"]
                ),
            ),
        )


def _recovery_values(
    user: LongitudinalQAUser, index: int, total_days: int
) -> tuple[float, int, int, str]:
    if user.scenario == "recovery_limited":
        sleep = 5.5 + ((index % 4) * 0.15)
        energy = [4, 3, 4, 3, 5][index % 5]
        soreness = [6, 7, 8, 7, 8][index % 5]
        note = "Low sleep and higher soreness make recovery the limiting context."
    elif user.scenario == "aligned_managed":
        sleep = 7.6 + ((index % 5) * 0.12)
        energy = [8, 8, 9, 8, 7][index % 5]
        soreness = [2, 3, 2, 2, 3][index % 5]
        note = "Stable recovery inputs support managed training decisions."
    elif user.scenario == "nutrition_training_mismatch":
        sleep = 7.0 + ((index % 4) * 0.1)
        energy = [6, 6, 5, 6, 7][index % 5]
        soreness = [4, 5, 6, 5, 6][index % 5]
        note = "Recovery is usable while nutrition consistency is the bigger question."
    elif user.scenario == "improving_after_deload":
        progress = index / max(total_days - 1, 1)
        sleep = 6.0 + (1.7 * progress) + ((index % 3) * 0.05)
        energy = min(8, 4 + round(progress * 4))
        soreness = max(2, 8 - round(progress * 6))
        note = "Recent recovery inputs are improving after a more limited early phase."
    else:
        sleep = [6.0, 6.8, 5.7, 7.1, 6.4][index % 5]
        energy = [5, 6, 4, 7, 5][index % 5]
        soreness = [3, 6, 4, 7, 5][index % 5]
        note = "Inputs are inconsistent, so confidence should stay limited."

    return round(sleep, 1), int(energy), int(soreness), note


def _weight_for(user: LongitudinalQAUser, index: int, total_days: int) -> float | None:
    if user.starting_weight is None:
        return None

    progress = index / max(total_days - 1, 1)
    if user.scenario == "aligned_managed":
        delta = ((index % 10) - 5) * 0.03
    elif user.scenario == "improving_after_deload":
        delta = -2.2 * progress
    elif user.scenario == "nutrition_training_mismatch":
        delta = -0.8 * progress
    elif user.scenario == "data_quality_limited":
        delta = -1.0 * progress if index % 3 != 0 else 0.4
    else:
        delta = 0.6 * progress

    return round(user.starting_weight + delta, 1)


def _seed_recovery(cursor, user: LongitudinalQAUser, days: list[date]) -> int:
    inserted = 0
    for index, day in enumerate(days):
        if user.scenario == "data_quality_limited" and index % 3 == 0:
            continue
        if user.scenario == "nutrition_training_mismatch" and index % 9 == 0:
            continue

        sleep, energy, soreness, note = _recovery_values(user, index, len(days))
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
                user.user_id,
                _iso(day),
                _weight_for(user, index, len(days)),
                sleep,
                energy,
                soreness,
                "steady" if user.scenario != "data_quality_limited" else "variable",
                note,
                _timestamp(day, hour=7),
            ),
        )
        inserted += 1
    return inserted


def _nutrition_food_plan(
    user: LongitudinalQAUser, index: int
) -> list[tuple[str, float]]:
    if user.scenario == "aligned_managed":
        return [
            ("Oats, Dry", 80 + (index % 3) * 5),
            ("Chicken Breast, Cooked, Skinless", 180),
            ("White Rice, Cooked", 260),
            ("Greek Yogurt, Plain", 220),
            ("Olive Oil", 12),
            ("Blueberries", 100),
        ]
    if user.scenario == "recovery_limited":
        return [
            ("Chicken Breast, Cooked, Skinless", 145),
            ("Brown Rice, Cooked", 140),
            ("Banana", 120),
            ("Greek Yogurt, Plain", 120),
        ]
    if user.scenario == "nutrition_training_mismatch":
        if index % 4 == 0:
            return [("Tuna, Canned in Water", 120)]
        return [
            ("Turkey Breast, Cooked", 130),
            ("White Rice, Cooked", 120 if index % 3 else 80),
            ("Banana", 100),
        ]
    if user.scenario == "improving_after_deload":
        if index < 75 and index % 3 == 0:
            return [("Greek Yogurt, Plain", 160), ("Banana", 100)]
        return [
            ("Chicken Breast, Cooked, Skinless", 170),
            ("Brown Rice, Cooked", 210),
            ("Broccoli, Cooked", 130),
            ("Greek Yogurt, Plain", 180),
        ]
    if index % 5 in {0, 1}:
        return []
    if index % 4 == 0:
        return [("Almonds", 45)]
    return [("Egg, Large", 110), ("Banana", 90)]


def _should_seed_nutrition(user: LongitudinalQAUser, index: int) -> bool:
    if user.scenario == "aligned_managed":
        return index % 12 != 0
    if user.scenario == "recovery_limited":
        return index % 4 != 0
    if user.scenario == "nutrition_training_mismatch":
        return index % 3 != 0
    if user.scenario == "improving_after_deload":
        return index >= 75 or index % 2 == 0
    return index % 3 == 0 or index % 7 == 0


def _seed_nutrition(
    cursor,
    user: LongitudinalQAUser,
    days: list[date],
    food_ids: dict[str, int],
) -> tuple[int, int]:
    nutrition_days = 0
    nutrition_entries = 0
    for index, day in enumerate(days):
        if not _should_seed_nutrition(user, index):
            continue
        entries = _nutrition_food_plan(user, index)
        if not entries:
            continue
        nutrition_days += 1
        for food_name, grams in entries:
            cursor.execute(
                """
                INSERT INTO food_entries (user_id, food_id, grams, entry_date, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user.user_id,
                    food_ids[food_name],
                    float(grams),
                    _iso(day),
                    _timestamp(day, hour=12, minute=index % 50),
                ),
            )
            nutrition_entries += 1
    return nutrition_days, nutrition_entries


def _workout_days(user: LongitudinalQAUser, days: list[date]) -> list[date]:
    selected: list[date] = []
    weekday_map = {
        2: {1, 4},
        3: {0, 2, 5},
        4: {0, 2, 4, 6},
    }
    target_weekdays = weekday_map[user.training_days_per_week]
    for index, day in enumerate(days):
        if day.weekday() not in target_weekdays:
            continue
        if user.scenario == "data_quality_limited" and index % 5 == 0:
            continue
        selected.append(day)
    return selected


def _plan_exercises_for(
    user: LongitudinalQAUser, workout_index: int
) -> list[dict[str, Any]]:
    exercises = [dict(exercise) for exercise in BASE_PLAN_EXERCISES]
    if user.scenario == "recovery_limited":
        for exercise in exercises:
            exercise["rir_min"] = 2
            exercise["rir_max"] = 4
    elif user.scenario == "nutrition_training_mismatch":
        for exercise in exercises:
            exercise["rir_min"] = 1
            exercise["rir_max"] = 3
    elif user.scenario == "improving_after_deload" and workout_index < 20:
        for exercise in exercises:
            exercise["rir_min"] = 1
            exercise["rir_max"] = 2
    elif user.scenario == "data_quality_limited":
        exercises = exercises[:3]
        for exercise in exercises:
            exercise["sets"] = 2
            exercise["rir_min"] = 2
            exercise["rir_max"] = 5
    return exercises


def _workout_title_for(user: LongitudinalQAUser, workout_index: int) -> str:
    if user.scenario == "recovery_limited":
        titles = (
            "Recovery-Aware Strength Session",
            "Manageable Baseline Session",
            "Controlled Strength Practice",
        )
    elif user.scenario == "aligned_managed":
        titles = (
            "Gradual Progression Strength Session",
            "Controlled Progression Session",
            "Manageable Baseline Session",
        )
    elif user.scenario == "nutrition_training_mismatch":
        titles = (
            "Controlled Strength Practice",
            "Gradual Progression Strength Session",
            "Manageable Baseline Session",
        )
    elif user.scenario == "improving_after_deload":
        titles = (
            "Controlled Progression Session",
            "Recovery-Aware Strength Session",
            "Gradual Progression Strength Session",
        )
    else:
        titles = ("Manageable Baseline Session", "Controlled Strength Practice")
    return titles[workout_index % len(titles)]


def _approved_plan_payload(
    *,
    title: str,
    scenario: str,
    exercises: list[dict[str, Any]],
    duration_minutes: int,
) -> dict[str, Any]:
    return {
        "title": title,
        "session_focus": "Strength practice with controlled execution and logged effort.",
        "duration_minutes": duration_minutes,
        "exercises": [
            {
                "name": exercise["name"],
                "sets": exercise["sets"],
                "reps_min": exercise["reps_min"],
                "reps_max": exercise["reps_max"],
                "rir_min": exercise["rir_min"],
                "rir_max": exercise["rir_max"],
                "notes": "Use controlled reps and stop within the planned effort range.",
                "equipment_required": exercise["equipment_required"],
            }
            for exercise in exercises
        ],
        "warmup": "Ramp up gradually with easy movement and lighter sets.",
        "cooldown": "Finish with easy breathing and light mobility.",
        "progression_guidance": "Adjust only after reviewing logged load, reps, and RIR.",
        "rationale": "This session keeps training decisions tied to logged execution data.",
        "confidence": "Moderate" if scenario != "data_quality_limited" else "Limited",
        "scenario": scenario,
        "reason_codes": ["longitudinal_data_foundation"],
    }


def _legacy_exercise_ids(cursor) -> dict[str, int]:
    cursor.execute("SELECT id, name FROM exercises")
    return {row["name"]: int(row["id"]) for row in cursor.fetchall()}


def _actual_rir_for(
    user: LongitudinalQAUser, workout_index: int, set_index: int
) -> int | None:
    if user.scenario == "recovery_limited":
        return [1, 1, 0, 2][(workout_index + set_index) % 4]
    if user.scenario == "aligned_managed":
        return [2, 3, 2, 3][(workout_index + set_index) % 4]
    if user.scenario == "nutrition_training_mismatch":
        return [1, 2, 1, 2][(workout_index + set_index) % 4]
    if user.scenario == "improving_after_deload":
        return (
            [1, 1, 2][set_index % 3] if workout_index < 20 else [2, 3, 2][set_index % 3]
        )
    if (workout_index + set_index) % 5 == 0:
        return None
    return [3, 4, 2][set_index % 3]


def _actual_weight_for(
    user: LongitudinalQAUser, exercise_index: int, workout_index: int
) -> float:
    base = {
        "recovery_limited": 40.0,
        "aligned_managed": 55.0,
        "nutrition_training_mismatch": 50.0,
        "improving_after_deload": 45.0,
        "data_quality_limited": 30.0,
    }[user.scenario]
    progression = workout_index * (
        0.12 if user.scenario != "data_quality_limited" else 0.04
    )
    return round(base + (exercise_index * 12.5) + progression, 1)


def _seed_workouts(
    cursor, user: LongitudinalQAUser, days: list[date]
) -> tuple[int, int]:
    exercise_ids = _legacy_exercise_ids(cursor)
    completed_workouts = 0
    actual_sets = 0

    for workout_index, day in enumerate(_workout_days(user, days)):
        exercises = _plan_exercises_for(user, workout_index)
        title = _workout_title_for(user, workout_index)
        duration = 45 if user.scenario == "data_quality_limited" else 55
        timestamp = _timestamp(day, hour=18, minute=workout_index % 50)
        approved_plan = _approved_plan_payload(
            title=title,
            scenario=user.scenario,
            exercises=exercises,
            duration_minutes=duration,
        )

        cursor.execute(
            """
            INSERT INTO workout_plan_instances (
                user_id,
                status,
                scenario,
                confidence,
                title,
                approved_workout_plan_json,
                selected_at,
                completed_at,
                created_at,
                updated_at
            )
            VALUES (?, 'completed', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user.user_id,
                user.scenario,
                approved_plan["confidence"],
                title,
                json.dumps(approved_plan, sort_keys=True),
                timestamp,
                timestamp,
                timestamp,
                timestamp,
            ),
        )
        plan_instance_id = int(cursor.lastrowid)

        planned_ids: list[int] = []
        for exercise_order, exercise in enumerate(exercises, start=1):
            cursor.execute(
                """
                INSERT INTO planned_workout_exercises (
                    workout_plan_instance_id,
                    exercise_order,
                    name,
                    sets,
                    reps_min,
                    reps_max,
                    rir_min,
                    rir_max,
                    notes,
                    equipment_required_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_instance_id,
                    exercise_order,
                    exercise["name"],
                    exercise["sets"],
                    exercise["reps_min"],
                    exercise["reps_max"],
                    exercise["rir_min"],
                    exercise["rir_max"],
                    "Use controlled reps and log load, reps, and RIR.",
                    json.dumps(exercise["equipment_required"]),
                    timestamp,
                ),
            )
            planned_ids.append(int(cursor.lastrowid))

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
                user.user_id,
                _iso(day),
                title,
                duration,
                "Planned execution row for longitudinal data foundation.",
                timestamp,
            ),
        )
        workout_session_id = int(cursor.lastrowid)

        cursor.execute(
            """
            INSERT INTO workout_execution_sessions (
                workout_plan_instance_id,
                user_id,
                status,
                workout_session_id,
                started_at,
                completed_at,
                created_at,
                updated_at
            )
            VALUES (?, ?, 'completed', ?, ?, ?, ?, ?)
            """,
            (
                plan_instance_id,
                user.user_id,
                workout_session_id,
                timestamp,
                timestamp,
                timestamp,
                timestamp,
            ),
        )
        execution_session_id = int(cursor.lastrowid)

        for exercise_index, exercise in enumerate(exercises, start=1):
            planned_id = planned_ids[exercise_index - 1]
            skipped_exercise = (
                user.scenario == "data_quality_limited"
                and (workout_index + exercise_index) % 4 == 0
            )
            logged_sets = exercise["sets"]
            if user.scenario == "data_quality_limited" and exercise_index == len(
                exercises
            ):
                logged_sets = max(1, exercise["sets"] - 1)
            if (
                user.scenario == "recovery_limited"
                and (workout_index + exercise_index) % 9 == 0
            ):
                logged_sets = max(1, exercise["sets"] - 1)

            for set_number in range(1, logged_sets + 1):
                actual_rir = _actual_rir_for(user, workout_index, set_number)
                completed = not skipped_exercise
                actual_reps = None if skipped_exercise else exercise["reps_max"]
                actual_weight = (
                    None
                    if skipped_exercise
                    else _actual_weight_for(
                        user,
                        exercise_index,
                        workout_index,
                    )
                )
                if (
                    user.scenario == "nutrition_training_mismatch"
                    and set_number == logged_sets
                    and exercise_index % 2 == 0
                ):
                    actual_reps = exercise["reps_min"] - 1
                if user.scenario == "data_quality_limited" and actual_rir is None:
                    actual_reps = exercise["reps_max"] if not skipped_exercise else None
                    completed = not skipped_exercise

                cursor.execute(
                    """
                    INSERT INTO workout_execution_set_actuals (
                        workout_execution_session_id,
                        planned_workout_exercise_id,
                        workout_session_id,
                        exercise_name,
                        set_number,
                        planned_reps_min,
                        planned_reps_max,
                        planned_rir_min,
                        planned_rir_max,
                        actual_reps,
                        actual_weight,
                        actual_rir,
                        completed,
                        skipped,
                        notes,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        execution_session_id,
                        planned_id,
                        workout_session_id,
                        exercise["name"],
                        set_number,
                        exercise["reps_min"],
                        exercise["reps_max"],
                        exercise["rir_min"],
                        exercise["rir_max"],
                        actual_reps,
                        actual_weight,
                        actual_rir,
                        1 if completed else 0,
                        1 if skipped_exercise else 0,
                        "Actual set row from longitudinal data foundation.",
                        timestamp,
                        timestamp,
                    ),
                )
                actual_sets += 1

                legacy_exercise_id = exercise_ids.get(exercise["name"])
                if (
                    legacy_exercise_id is not None
                    and completed
                    and actual_reps is not None
                ):
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
                            workout_session_id,
                            legacy_exercise_id,
                            set_number,
                            actual_reps,
                            actual_weight,
                            actual_rir,
                            timestamp,
                        ),
                    )

        completed_workouts += 1

    return completed_workouts, actual_sets


def seed_longitudinal_qa_data(
    *,
    end_date: date = DEFAULT_END_DATE,
    day_count: int = DEFAULT_DAY_COUNT,
) -> list[SeededLongitudinalQAUser]:
    """Seed users 101-105 with deterministic longitudinal QA data."""

    if day_count < 120:
        raise ValueError("day_count must be at least 120 for longitudinal QA data.")

    database.initialize_database()
    ensure_workout_plan_persistence_tables()
    ensure_starter_canonical_foods_seeded()
    seed_exercise_catalog()

    conn = database.get_connection()
    cursor = conn.cursor()

    try:
        _clear_existing_qa_user_data(cursor)
        _seed_users(cursor)
        food_ids = _ensure_legacy_foods_from_canonical(cursor)
        days = _date_series(end_date=end_date, day_count=day_count)

        seeded: list[SeededLongitudinalQAUser] = []
        for user in QA_USERS:
            recovery_count = _seed_recovery(cursor, user, days)
            nutrition_days, nutrition_entries = _seed_nutrition(
                cursor,
                user,
                days,
                food_ids,
            )
            completed_workouts, actual_sets = _seed_workouts(cursor, user, days)
            seeded.append(
                SeededLongitudinalQAUser(
                    user_id=user.user_id,
                    scenario=user.scenario,
                    recovery_checkins=recovery_count,
                    nutrition_days=nutrition_days,
                    nutrition_entries=nutrition_entries,
                    completed_workouts=completed_workouts,
                    actual_sets=actual_sets,
                )
            )

        conn.commit()
        return seeded
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--end-date",
        type=_parse_date,
        default=DEFAULT_END_DATE,
        help="Inclusive seed end date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--day-count",
        type=int,
        default=DEFAULT_DAY_COUNT,
        help="Number of days to seed ending at --end-date.",
    )
    args = parser.parse_args()

    seeded = seed_longitudinal_qa_data(
        end_date=args.end_date,
        day_count=args.day_count,
    )
    print("Seeded longitudinal QA data:")
    for item in seeded:
        print(
            "- "
            f"user_id={item.user_id} "
            f"scenario={item.scenario} "
            f"recovery_checkins={item.recovery_checkins} "
            f"nutrition_days={item.nutrition_days} "
            f"nutrition_entries={item.nutrition_entries} "
            f"completed_workouts={item.completed_workouts} "
            f"actual_sets={item.actual_sets}"
        )


if __name__ == "__main__":
    main()
