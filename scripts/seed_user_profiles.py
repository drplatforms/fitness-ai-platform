"""Seed deterministic user profile/goal/setup data for QA and local testing.

Run from the project root:
    python scripts/seed_user_profiles.py

The script is safe to rerun. It upserts profile/equipment rows and only replaces
check-in/workout rows that it created with the seed_user_profiles_v1 marker.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database  # noqa: E402

SEED_MARKER = "seed_user_profiles_v1"
TODAY = date.today()

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
    "exercise_ball",
    "rope_cable_attachment",
]

HOME_GYM_UNAVAILABLE = ["machine", "kettlebell"]
LIMITED_EQUIPMENT = ["bodyweight", "dumbbell", "resistance_band"]
LIMITED_UNAVAILABLE = [
    "barbell",
    "cable",
    "machine",
    "rack",
    "plates",
    "pull_up_bar",
]


@dataclass(frozen=True)
class SeededUserProfile:
    user_id: int
    name: str
    scenario: str
    gender: str | None
    age: int | None
    height_cm: float | None
    starting_weight: float | None
    latest_body_weight: float | None
    goal_weight: float | None
    primary_goal: str | None
    activity_level: str | None
    training_environment: str
    available_equipment: list[str]
    unavailable_equipment: list[str]
    workout_count: int = 0
    recovery_checkins: int = 1


SEED_PROFILES = [
    SeededUserProfile(
        user_id=1,
        name="Dustin",
        scenario="Complete realistic primary user profile",
        gender="Male",
        age=37,
        height_cm=176.5,
        starting_weight=187.6,
        latest_body_weight=190.0,
        goal_weight=180.0,
        primary_goal="strength_and_recomposition",
        activity_level="moderate",
        training_environment="home_gym",
        available_equipment=HOME_GYM_EQUIPMENT,
        unavailable_equipment=HOME_GYM_UNAVAILABLE,
        workout_count=4,
        recovery_checkins=4,
    ),
    SeededUserProfile(
        user_id=102,
        name="QA Well-Recovered Baseline",
        scenario="Complete home-gym happy-path profile",
        gender="Male",
        age=35,
        height_cm=177.0,
        starting_weight=178.0,
        latest_body_weight=178.0,
        goal_weight=178.0,
        primary_goal="strength_progression",
        activity_level="moderate",
        training_environment="home_gym",
        available_equipment=HOME_GYM_EQUIPMENT,
        unavailable_equipment=HOME_GYM_UNAVAILABLE,
        workout_count=4,
        recovery_checkins=4,
    ),
    SeededUserProfile(
        user_id=103,
        name="QA Protein Only Formula Scenario",
        scenario="Body weight present with incomplete calorie formula inputs",
        gender=None,
        age=None,
        height_cm=None,
        starting_weight=185.0,
        latest_body_weight=185.0,
        goal_weight=None,
        primary_goal=None,
        activity_level=None,
        training_environment="home_gym",
        available_equipment=HOME_GYM_EQUIPMENT,
        unavailable_equipment=HOME_GYM_UNAVAILABLE,
        workout_count=3,
        recovery_checkins=2,
    ),
    SeededUserProfile(
        user_id=104,
        name="QA Missing Body Weight Scenario",
        scenario="Missing body weight limited-target profile",
        gender="Male",
        age=35,
        height_cm=177.0,
        starting_weight=None,
        latest_body_weight=None,
        goal_weight=184.0,
        primary_goal="strength_progression",
        activity_level="moderate",
        training_environment="home_gym",
        available_equipment=HOME_GYM_EQUIPMENT,
        unavailable_equipment=HOME_GYM_UNAVAILABLE,
        workout_count=2,
        recovery_checkins=0,
    ),
    SeededUserProfile(
        user_id=105,
        name="QA Data Quality Limited Profile",
        scenario="Data-quality-limited profile and logging context",
        gender=None,
        age=None,
        height_cm=None,
        starting_weight=200.0,
        latest_body_weight=200.0,
        goal_weight=185.0,
        primary_goal="fat_loss",
        activity_level=None,
        training_environment="limited_equipment",
        available_equipment=LIMITED_EQUIPMENT,
        unavailable_equipment=LIMITED_UNAVAILABLE,
        workout_count=1,
        recovery_checkins=1,
    ),
]


def _timestamp(days_ago: int = 0, hour: int = 8) -> str:
    day = TODAY - timedelta(days=days_ago)
    return (
        datetime.combine(day, datetime.min.time()).replace(hour=hour).isoformat(sep=" ")
    )


def _date(days_ago: int = 0) -> str:
    return (TODAY - timedelta(days=days_ago)).isoformat()


def _json_list(values: list[str]) -> str:
    return json.dumps(values)


def _upsert_user(cursor, profile: SeededUserProfile) -> None:
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
            profile.user_id,
            profile.name,
            profile.gender,
            profile.age,
            profile.height_cm,
            profile.starting_weight,
            profile.goal_weight,
            profile.primary_goal,
            profile.activity_level,
        ),
    )


def _upsert_equipment_profile(cursor, profile: SeededUserProfile) -> None:
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
            profile.user_id,
            profile.training_environment,
            _json_list(profile.available_equipment),
            _json_list(profile.unavailable_equipment),
        ),
    )


def _get_exercise_ids(cursor) -> dict[str, int]:
    cursor.execute("""
        SELECT id, name
        FROM exercises
        WHERE name IN ('Barbell Squat', 'Barbell Bench Press', 'Barbell Row')
        """)
    return {row["name"]: row["id"] for row in cursor.fetchall()}


def _clear_seeded_context(cursor, user_id: int) -> None:
    marker = f"{SEED_MARKER}:%"
    cursor.execute(
        """
        DELETE FROM workout_sets
        WHERE workout_session_id IN (
            SELECT id
            FROM workout_sessions
            WHERE user_id = ?
              AND notes LIKE ?
        )
        """,
        (user_id, marker),
    )
    cursor.execute(
        """
        DELETE FROM workout_sessions
        WHERE user_id = ?
          AND notes LIKE ?
        """,
        (user_id, marker),
    )
    cursor.execute(
        """
        DELETE FROM daily_checkins
        WHERE user_id = ?
          AND notes LIKE ?
        """,
        (user_id, marker),
    )

    # User 104 is intentionally the missing-body-weight formula scenario. Clear
    # existing check-ins for that test user so older QA scenario weight rows do
    # not accidentally supply body weight.
    if user_id == 104:
        cursor.execute("DELETE FROM daily_checkins WHERE user_id = ?", (user_id,))


def _seed_recovery_context(cursor, profile: SeededUserProfile) -> None:
    if profile.recovery_checkins <= 0:
        return

    for index in range(profile.recovery_checkins):
        days_ago = profile.recovery_checkins - index - 1
        body_weight = None
        if profile.latest_body_weight is not None:
            body_weight = round(profile.latest_body_weight - (days_ago * 0.2), 1)

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
                profile.user_id,
                _date(days_ago),
                body_weight,
                7.4 if profile.user_id in {1, 102} else 6.4,
                8 if profile.user_id in {1, 102} else 6,
                3 if profile.user_id in {1, 102} else 5,
                "seeded",
                f"{SEED_MARKER}: profile/bodyweight context for {profile.scenario}",
                _timestamp(days_ago, hour=8),
            ),
        )


def _seed_training_context(cursor, profile: SeededUserProfile) -> None:
    if profile.workout_count <= 0:
        return

    exercise_ids = _get_exercise_ids(cursor)
    missing = [
        name
        for name in ("Barbell Squat", "Barbell Bench Press", "Barbell Row")
        if name not in exercise_ids
    ]
    if missing:
        raise RuntimeError(f"Missing required seeded exercises: {', '.join(missing)}")

    for index in range(profile.workout_count):
        days_ago = index + 1
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
                profile.user_id,
                _date(days_ago),
                "Seeded Profile Context Strength Session",
                55,
                f"{SEED_MARKER}: deterministic training context",
                _timestamp(days_ago, hour=18),
            ),
        )
        workout_session_id = cursor.lastrowid

        for set_number, exercise_name in enumerate(
            ["Barbell Squat", "Barbell Bench Press", "Barbell Row"], start=1
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
                    exercise_ids[exercise_name],
                    set_number,
                    8,
                    135 + (index * 5),
                    3 if profile.user_id in {1, 102, 104} else 4,
                    _timestamp(days_ago, hour=18),
                ),
            )


def seed_user_profiles() -> list[SeededUserProfile]:
    database.initialize_database()
    conn = database.get_connection()
    cursor = conn.cursor()

    for profile in SEED_PROFILES:
        _clear_seeded_context(cursor, profile.user_id)
        _upsert_user(cursor, profile)
        _upsert_equipment_profile(cursor, profile)
        _seed_recovery_context(cursor, profile)
        _seed_training_context(cursor, profile)

    conn.commit()
    conn.close()

    return SEED_PROFILES


def main() -> None:
    seeded_profiles = seed_user_profiles()

    print("Seeded user profiles:")
    for profile in seeded_profiles:
        print(f"- user_id={profile.user_id}: {profile.scenario} ({profile.name})")


if __name__ == "__main__":
    main()
