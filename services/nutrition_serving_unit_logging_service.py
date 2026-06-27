from __future__ import annotations

from dataclasses import asdict
from typing import Any

from database import get_connection
from models.nutrition_serving_unit_models import (
    NutritionServingUnitLogMetadata,
    NutritionServingUnitLogResponse,
)
from services.food_normalization_service import get_canonical_food
from services.nutrition_service import (
    CanonicalFoodInactiveError,
    CanonicalFoodNotFoundError,
    add_canonical_food_entry,
)
from services.nutrition_serving_unit_service import (
    ensure_serving_unit_schema,
    find_serving_unit,
)

SERVING_UNIT_LOG_METADATA_TABLE_NAME = "nutrition_serving_unit_log_metadata"
SERVING_UNIT_AMOUNT_SOURCE = "serving_unit_estimate"


class ServingUnitLoggingError(ValueError):
    """Base class for public-safe serving-unit logging failures."""


class ServingUnitNotFoundError(ServingUnitLoggingError):
    """Raised when a serving unit ID does not exist."""


class ServingUnitInactiveError(ServingUnitLoggingError):
    """Raised when a serving unit exists but is inactive."""


class ServingUnitFoodMismatchError(ServingUnitLoggingError):
    """Raised when a serving unit does not belong to the requested food."""


class ServingUnitQuantityError(ServingUnitLoggingError):
    """Raised when serving quantity is invalid."""


def ensure_serving_unit_log_metadata_schema() -> None:
    ensure_serving_unit_schema()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {SERVING_UNIT_LOG_METADATA_TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_entry_id INTEGER NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,
        canonical_food_id INTEGER NOT NULL,
        serving_unit_id INTEGER NOT NULL,
        serving_quantity REAL NOT NULL,
        resolved_grams REAL NOT NULL,
        grams_min REAL,
        grams_max REAL,
        serving_unit_confidence TEXT NOT NULL,
        amount_source TEXT NOT NULL,
        original_serving_display TEXT NOT NULL,
        source TEXT,
        source_notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (food_entry_id) REFERENCES food_entries(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (canonical_food_id) REFERENCES canonical_foods(id),
        FOREIGN KEY (serving_unit_id) REFERENCES canonical_food_serving_units(id),
        CHECK (food_entry_id > 0),
        CHECK (user_id > 0),
        CHECK (canonical_food_id > 0),
        CHECK (serving_unit_id > 0),
        CHECK (serving_quantity > 0),
        CHECK (resolved_grams > 0),
        CHECK (grams_min IS NULL OR grams_min > 0),
        CHECK (grams_max IS NULL OR grams_max > 0),
        CHECK (grams_min IS NULL OR resolved_grams >= grams_min),
        CHECK (grams_max IS NULL OR resolved_grams <= grams_max),
        CHECK (serving_unit_confidence IN ('Low', 'Moderate', 'High')),
        CHECK (LENGTH(TRIM(amount_source)) > 0),
        CHECK (LENGTH(TRIM(original_serving_display)) > 0)
    )
    """)
    cursor.execute(f"""
    CREATE INDEX IF NOT EXISTS idx_{SERVING_UNIT_LOG_METADATA_TABLE_NAME}_entry
    ON {SERVING_UNIT_LOG_METADATA_TABLE_NAME}(food_entry_id)
    """)
    cursor.execute(f"""
    CREATE INDEX IF NOT EXISTS idx_{SERVING_UNIT_LOG_METADATA_TABLE_NAME}_user_food_date
    ON {SERVING_UNIT_LOG_METADATA_TABLE_NAME}(user_id, canonical_food_id)
    """)
    conn.commit()
    conn.close()


def _validate_positive_quantity(quantity: float) -> float:
    try:
        resolved_quantity = float(quantity)
    except (TypeError, ValueError) as exc:
        raise ServingUnitQuantityError(
            "Serving unit quantity must be a positive number."
        ) from exc

    if resolved_quantity <= 0:
        raise ServingUnitQuantityError("Serving unit quantity must be greater than 0.")
    return resolved_quantity


def _round_grams(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def _format_quantity(quantity: float) -> str:
    return f"{quantity:g}"


def build_serving_unit_display(quantity: float, serving_unit_display_name: str) -> str:
    resolved_quantity = _validate_positive_quantity(quantity)
    display_name = " ".join(serving_unit_display_name.strip().split())
    quantity_text = _format_quantity(resolved_quantity)

    if resolved_quantity == 1:
        return display_name

    if display_name.startswith("1 "):
        return f"{quantity_text} {display_name[2:]}"

    return f"{quantity_text} x {display_name}"


def resolve_serving_unit_log_request(
    *,
    canonical_food_id: int,
    serving_unit_id: int,
    quantity: float,
) -> tuple[float, float | None, float | None, str, str]:
    """Validate a serving-unit log request and resolve it to grams."""

    canonical_food = get_canonical_food(int(canonical_food_id))
    if canonical_food is None:
        raise CanonicalFoodNotFoundError("Canonical food not found.")
    if not canonical_food.active:
        raise CanonicalFoodInactiveError("Canonical food is inactive.")

    serving_unit = find_serving_unit(int(serving_unit_id))
    if serving_unit is None:
        raise ServingUnitNotFoundError("Serving unit not found.")
    if not serving_unit.active:
        raise ServingUnitInactiveError("Serving unit is inactive.")
    if serving_unit.canonical_food_id != int(canonical_food_id):
        raise ServingUnitFoodMismatchError(
            "Serving unit does not belong to the requested canonical food."
        )

    resolved_quantity = _validate_positive_quantity(quantity)
    resolved_grams = _round_grams(serving_unit.grams_default * resolved_quantity)
    grams_min = _round_grams(
        None
        if serving_unit.grams_min is None
        else serving_unit.grams_min * resolved_quantity
    )
    grams_max = _round_grams(
        None
        if serving_unit.grams_max is None
        else serving_unit.grams_max * resolved_quantity
    )
    serving_display = build_serving_unit_display(
        resolved_quantity,
        serving_unit.display_name,
    )

    return (
        float(resolved_grams),
        grams_min,
        grams_max,
        serving_unit.confidence,
        serving_display,
    )


def _row_to_metadata(row: Any) -> NutritionServingUnitLogMetadata:
    return NutritionServingUnitLogMetadata(
        id=int(row["id"]),
        food_entry_id=int(row["food_entry_id"]),
        user_id=int(row["user_id"]),
        canonical_food_id=int(row["canonical_food_id"]),
        serving_unit_id=int(row["serving_unit_id"]),
        serving_quantity=float(row["serving_quantity"]),
        resolved_grams=float(row["resolved_grams"]),
        grams_min=None if row["grams_min"] is None else float(row["grams_min"]),
        grams_max=None if row["grams_max"] is None else float(row["grams_max"]),
        serving_unit_confidence=row["serving_unit_confidence"],
        amount_source=row["amount_source"],
        original_serving_display=row["original_serving_display"],
        source=row["source"],
        source_notes=row["source_notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_serving_unit_log_metadata(
    *,
    food_entry_id: int,
    user_id: int,
    canonical_food_id: int,
    serving_unit_id: int,
    serving_quantity: float,
    resolved_grams: float,
    grams_min: float | None,
    grams_max: float | None,
    serving_unit_confidence: str,
    amount_source: str,
    original_serving_display: str,
    source: str | None = None,
    source_notes: str | None = None,
) -> NutritionServingUnitLogMetadata:
    ensure_serving_unit_log_metadata_schema()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute(
        f"""
        INSERT INTO {SERVING_UNIT_LOG_METADATA_TABLE_NAME} (
            food_entry_id,
            user_id,
            canonical_food_id,
            serving_unit_id,
            serving_quantity,
            resolved_grams,
            grams_min,
            grams_max,
            serving_unit_confidence,
            amount_source,
            original_serving_display,
            source,
            source_notes,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            int(food_entry_id),
            int(user_id),
            int(canonical_food_id),
            int(serving_unit_id),
            float(serving_quantity),
            float(resolved_grams),
            grams_min,
            grams_max,
            serving_unit_confidence,
            amount_source,
            original_serving_display,
            source,
            source_notes,
        ),
    )
    metadata_id = int(cursor.lastrowid)
    conn.commit()
    cursor.execute(
        f"SELECT * FROM {SERVING_UNIT_LOG_METADATA_TABLE_NAME} WHERE id = ?",
        (metadata_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_metadata(row)


def get_serving_unit_log_metadata_for_food_entry(
    food_entry_id: int,
) -> NutritionServingUnitLogMetadata | None:
    ensure_serving_unit_log_metadata_schema()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT *
        FROM {SERVING_UNIT_LOG_METADATA_TABLE_NAME}
        WHERE food_entry_id = ?
        """,
        (int(food_entry_id),),
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_metadata(row)


def log_canonical_food_serving(
    *,
    user_id: int,
    canonical_food_id: int,
    serving_unit_id: int,
    quantity: float,
    entry_date: str | None = None,
) -> dict[str, Any]:
    """Log a canonical food by backend-approved serving unit.

    The existing canonical grams logging path remains the bridge into
    food_entries so Target-vs-Actual continues reading resolved grams exactly as
    it already does. This service only adds serving-unit provenance metadata.
    """

    serving_unit = find_serving_unit(int(serving_unit_id))
    if serving_unit is None:
        raise ServingUnitNotFoundError("Serving unit not found.")

    (
        resolved_grams,
        grams_min,
        grams_max,
        confidence,
        serving_display,
    ) = resolve_serving_unit_log_request(
        canonical_food_id=canonical_food_id,
        serving_unit_id=serving_unit_id,
        quantity=quantity,
    )
    resolved_quantity = _validate_positive_quantity(quantity)

    logged_entry = add_canonical_food_entry(
        user_id=user_id,
        canonical_food_id=canonical_food_id,
        grams=resolved_grams,
        entry_date=entry_date,
    )

    food_entry_id = int(logged_entry["logged_food_entry_id"])
    metadata = create_serving_unit_log_metadata(
        food_entry_id=food_entry_id,
        user_id=user_id,
        canonical_food_id=canonical_food_id,
        serving_unit_id=serving_unit_id,
        serving_quantity=resolved_quantity,
        resolved_grams=resolved_grams,
        grams_min=grams_min,
        grams_max=grams_max,
        serving_unit_confidence=confidence,
        amount_source=SERVING_UNIT_AMOUNT_SOURCE,
        original_serving_display=serving_display,
        source=serving_unit.source,
        source_notes=serving_unit.source_note,
    )

    response = NutritionServingUnitLogResponse(
        food_entry_id=food_entry_id,
        logged_food_entry_id=food_entry_id,
        canonical_food_id=int(canonical_food_id),
        serving_unit_id=int(serving_unit_id),
        display_name=str(logged_entry["display_name"]),
        serving_quantity=resolved_quantity,
        serving_display=serving_display,
        resolved_grams=resolved_grams,
        grams_min=grams_min,
        grams_max=grams_max,
        confidence=confidence,
        amount_source=SERVING_UNIT_AMOUNT_SOURCE,
        logged_date=str(logged_entry["logged_date"]),
        metadata_id=metadata.id,
        nutrient_summary=logged_entry.get("nutrient_summary"),
    )

    return asdict(response)
