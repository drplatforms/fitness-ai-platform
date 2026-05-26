from __future__ import annotations

import json
from dataclasses import asdict

from database import get_connection
from models.equipment_profile_models import EquipmentProfile

ALLOWED_TRAINING_ENVIRONMENTS = {
    "commercial_gym",
    "home_gym",
    "bodyweight_only",
    "limited_equipment",
    "unknown",
}

ALL_KNOWN_EQUIPMENT = [
    "adjustable_bench",
    "barbell",
    "bike",
    "bodyweight",
    "cable",
    "dumbbell",
    "exercise_ball",
    "ez_bar",
    "kettlebell",
    "machine",
    "plates",
    "pull_up_bar",
    "rack",
    "resistance_band",
    "rope_cable_attachment",
    "treadmill",
]

DEFAULT_AVAILABLE_EQUIPMENT = [
    "adjustable_bench",
    "barbell",
    "bodyweight",
    "cable",
    "dumbbell",
    "machine",
    "plates",
    "rack",
]

HOME_GYM_AVAILABLE_EQUIPMENT = [
    "adjustable_bench",
    "barbell",
    "bike",
    "bodyweight",
    "cable",
    "dumbbell",
    "exercise_ball",
    "ez_bar",
    "plates",
    "pull_up_bar",
    "rack",
    "resistance_band",
    "rope_cable_attachment",
    "treadmill",
]

EQUIPMENT_BY_TRAINING_ENVIRONMENT = {
    "commercial_gym": DEFAULT_AVAILABLE_EQUIPMENT,
    "home_gym": HOME_GYM_AVAILABLE_EQUIPMENT,
    "bodyweight_only": ["bodyweight"],
    "limited_equipment": ["bodyweight", "dumbbell"],
    "unknown": DEFAULT_AVAILABLE_EQUIPMENT,
}


def _normalize_equipment(equipment: str) -> str:
    return equipment.strip().lower().replace(" ", "_")


def _normalize_training_environment(training_environment: str | None) -> str:
    if not training_environment:
        return "unknown"

    normalized = training_environment.strip().lower().replace(" ", "_")
    if normalized not in ALLOWED_TRAINING_ENVIRONMENTS:
        return "unknown"

    return normalized


def _unique_preserve_order(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _normalize_equipment_list(values: list[str] | None) -> list[str]:
    if not values:
        return []

    return _unique_preserve_order([_normalize_equipment(value) for value in values])


def _equipment_for_environment(training_environment: str) -> list[str]:
    return list(EQUIPMENT_BY_TRAINING_ENVIRONMENT[training_environment])


def _default_unavailable_for_environment(
    training_environment: str,
    available_equipment: list[str],
) -> list[str]:
    if training_environment in {"bodyweight_only", "limited_equipment", "home_gym"}:
        return [
            equipment
            for equipment in ALL_KNOWN_EQUIPMENT
            if equipment not in set(available_equipment)
        ]

    return []


def _encode_json_list(values: list[str]) -> str:
    return json.dumps(_normalize_equipment_list(values))


def _decode_json_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []

    try:
        decoded = json.loads(raw_value)
    except json.JSONDecodeError:
        return []

    if not isinstance(decoded, list):
        return []

    return _normalize_equipment_list([str(value) for value in decoded])


def ensure_equipment_profile_table() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_equipment_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        training_environment TEXT NOT NULL,
        available_equipment_json TEXT NOT NULL,
        unavailable_equipment_json TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


def _row_to_equipment_profile(row) -> EquipmentProfile:
    training_environment = _normalize_training_environment(row["training_environment"])
    available_equipment = _decode_json_list(row["available_equipment_json"])
    unavailable_equipment = _decode_json_list(row["unavailable_equipment_json"])

    return EquipmentProfile(
        user_id=row["user_id"],
        training_environment=training_environment,
        available_equipment=available_equipment,
        unavailable_equipment=unavailable_equipment,
        confidence="High",
        reason_codes=[
            "explicit_equipment_profile",
            f"training_environment_{training_environment}",
        ],
    )


def build_default_equipment_profile(user_id: int) -> EquipmentProfile:
    training_environment = "unknown"
    available_equipment = _equipment_for_environment(training_environment)

    return EquipmentProfile(
        user_id=user_id,
        training_environment=training_environment,
        available_equipment=available_equipment,
        unavailable_equipment=[],
        confidence="Low",
        reason_codes=[
            "no_explicit_equipment_profile",
            "safe_default_equipment_assumptions",
        ],
    )


def get_equipment_profile(user_id: int) -> EquipmentProfile | None:
    ensure_equipment_profile_table()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM user_equipment_profiles
        WHERE user_id = ?
        """,
        (user_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return _row_to_equipment_profile(row)


def get_effective_equipment_profile(user_id: int) -> EquipmentProfile:
    profile = get_equipment_profile(user_id)
    if profile is not None:
        return profile

    return build_default_equipment_profile(user_id)


def save_equipment_profile(
    user_id: int,
    training_environment: str = "unknown",
    available_equipment: list[str] | None = None,
    unavailable_equipment: list[str] | None = None,
) -> EquipmentProfile:
    ensure_equipment_profile_table()

    normalized_environment = _normalize_training_environment(training_environment)
    normalized_available = _normalize_equipment_list(available_equipment)
    if not normalized_available:
        normalized_available = _equipment_for_environment(normalized_environment)

    normalized_unavailable = _normalize_equipment_list(unavailable_equipment)
    if not normalized_unavailable:
        normalized_unavailable = _default_unavailable_for_environment(
            normalized_environment,
            normalized_available,
        )

    # If the same value appears in both lists, availability wins. This keeps
    # request handling forgiving while still producing a clean constraint set.
    normalized_unavailable = [
        equipment
        for equipment in normalized_unavailable
        if equipment not in set(normalized_available)
    ]

    conn = get_connection()
    cursor = conn.cursor()

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
            user_id,
            normalized_environment,
            _encode_json_list(normalized_available),
            _encode_json_list(normalized_unavailable),
        ),
    )

    conn.commit()
    conn.close()

    profile = get_equipment_profile(user_id)
    if profile is None:
        raise RuntimeError("Failed to save equipment profile.")

    return profile


def equipment_profile_to_dict(profile: EquipmentProfile) -> dict:
    return asdict(profile)
