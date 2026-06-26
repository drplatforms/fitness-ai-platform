from __future__ import annotations

import sqlite3
from dataclasses import asdict
from typing import Any

from database import get_connection
from models.nutrition_serving_unit_models import (
    ALLOWED_SERVING_UNIT_CONFIDENCE,
    SERVING_UNIT_CONFIDENCE_MODERATE,
    NutritionServingUnit,
    ServingUnitConversionEstimate,
    ServingUnitSeedResult,
    ServingUnitSeedSpec,
)
from services.food_normalization_service import (
    ensure_food_normalization_tables,
    get_canonical_food,
    get_nutrients_for_canonical_food,
    normalize_food_name,
)

SERVING_UNIT_TABLE_NAME = "canonical_food_serving_units"

DEFAULT_SERVING_UNIT_SEEDS: tuple[ServingUnitSeedSpec, ...] = (
    ServingUnitSeedSpec(
        canonical_food_display_name="White Rice, Cooked",
        unit_name="cup",
        unit_quantity=0.5,
        display_name="1/2 cup cooked white rice",
        grams_default=90,
        grams_min=80,
        grams_max=100,
        confidence="Moderate",
        source="manually_curated_v1",
        source_note="Household cooked-rice estimate; weigh for higher precision.",
        sort_order=10,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="White Rice, Cooked",
        unit_name="cup",
        unit_quantity=1,
        display_name="1 cup cooked white rice",
        grams_default=180,
        grams_min=160,
        grams_max=200,
        confidence="Moderate",
        source="manually_curated_v1",
        source_note="Household cooked-rice estimate; weigh for higher precision.",
        sort_order=20,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Brown Rice, Cooked",
        unit_name="cup",
        unit_quantity=0.5,
        display_name="1/2 cup cooked brown rice",
        grams_default=98,
        grams_min=85,
        grams_max=110,
        confidence="Moderate",
        source="manually_curated_v1",
        source_note="Household cooked-rice estimate; weigh for higher precision.",
        sort_order=10,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Brown Rice, Cooked",
        unit_name="cup",
        unit_quantity=1,
        display_name="1 cup cooked brown rice",
        grams_default=195,
        grams_min=170,
        grams_max=220,
        confidence="Moderate",
        source="manually_curated_v1",
        source_note="Household cooked-rice estimate; weigh for higher precision.",
        sort_order=20,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Egg, Large",
        unit_name="large egg",
        unit_quantity=1,
        display_name="1 large egg",
        grams_default=50,
        grams_min=45,
        grams_max=55,
        confidence="High",
        source="manually_curated_v1",
        source_note="Common large-egg edible portion estimate.",
        sort_order=10,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Banana",
        unit_name="medium banana",
        unit_quantity=1,
        display_name="1 medium banana",
        grams_default=118,
        grams_min=100,
        grams_max=136,
        confidence="Moderate",
        source="manually_curated_v1",
        source_note="Common medium-banana edible portion estimate.",
        sort_order=10,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Peanut Butter",
        unit_name="tablespoon",
        unit_quantity=1,
        display_name="1 tablespoon peanut butter",
        grams_default=16,
        grams_min=14,
        grams_max=18,
        confidence="High",
        source="manually_curated_v1",
        source_note="Common tablespoon weight estimate for peanut butter.",
        sort_order=10,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Peanut Butter",
        unit_name="tablespoon",
        unit_quantity=2,
        display_name="2 tablespoons peanut butter",
        grams_default=32,
        grams_min=28,
        grams_max=36,
        confidence="High",
        source="manually_curated_v1",
        source_note="Common two-tablespoon serving estimate for peanut butter.",
        sort_order=20,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Greek Yogurt, Plain",
        unit_name="cup",
        unit_quantity=1,
        display_name="1 cup Greek yogurt, plain",
        grams_default=245,
        grams_min=225,
        grams_max=265,
        confidence="Moderate",
        source="manually_curated_v1",
        source_note="Household cup estimate; brand labels vary.",
        sort_order=10,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Greek Yogurt, Plain",
        unit_name="container",
        unit_quantity=1,
        display_name="170g container Greek yogurt, plain",
        grams_default=170,
        grams_min=170,
        grams_max=170,
        confidence="High",
        source="manually_curated_v1",
        source_note="Common single-serve container size; verify package label.",
        sort_order=20,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Oats, Dry",
        unit_name="cup dry",
        unit_quantity=0.5,
        display_name="1/2 cup dry oats",
        grams_default=40,
        grams_min=35,
        grams_max=45,
        confidence="High",
        source="manually_curated_v1",
        source_note="Common dry rolled-oats household serving estimate.",
        sort_order=10,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Chicken Breast, Cooked, Skinless",
        unit_name="serving",
        unit_quantity=1,
        display_name="100g cooked chicken breast",
        grams_default=100,
        grams_min=100,
        grams_max=100,
        confidence="High",
        source="manually_curated_v1",
        source_note="Gram-based serving alias; equivalent to weighed amount.",
        sort_order=10,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Chicken Breast, Cooked, Skinless",
        unit_name="oz serving",
        unit_quantity=4,
        display_name="4 oz cooked chicken breast",
        grams_default=113,
        grams_min=110,
        grams_max=116,
        confidence="High",
        source="manually_curated_v1",
        source_note="Ounce-to-gram serving estimate rounded for food logging.",
        sort_order=20,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Olive Oil",
        unit_name="tablespoon",
        unit_quantity=1,
        display_name="1 tablespoon olive oil",
        grams_default=14,
        grams_min=13,
        grams_max=15,
        confidence="High",
        source="manually_curated_v1",
        source_note="Common tablespoon weight estimate for olive oil.",
        sort_order=10,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Olive Oil",
        unit_name="teaspoon",
        unit_quantity=1,
        display_name="1 teaspoon olive oil",
        grams_default=4.5,
        grams_min=4,
        grams_max=5,
        confidence="High",
        source="manually_curated_v1",
        source_note="Common teaspoon weight estimate for olive oil.",
        sort_order=20,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Potato, Baked",
        unit_name="medium potato",
        unit_quantity=1,
        display_name="1 medium baked potato",
        grams_default=173,
        grams_min=150,
        grams_max=200,
        confidence="Moderate",
        source="manually_curated_v1",
        source_note="Household medium-potato estimate; size varies.",
        sort_order=10,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Apple",
        unit_name="medium apple",
        unit_quantity=1,
        display_name="1 medium apple",
        grams_default=182,
        grams_min=160,
        grams_max=205,
        confidence="Moderate",
        source="manually_curated_v1",
        source_note="Household medium-apple edible portion estimate.",
        sort_order=10,
    ),
    ServingUnitSeedSpec(
        canonical_food_display_name="Whey Protein Powder, Generic",
        unit_name="scoop",
        unit_quantity=1,
        display_name="1 scoop whey protein powder",
        grams_default=30,
        grams_min=25,
        grams_max=35,
        confidence="Moderate",
        source="manually_curated_v1",
        source_note="Generic scoop estimate; package labels vary.",
        sort_order=10,
    ),
)


def ensure_serving_unit_schema() -> None:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {SERVING_UNIT_TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_food_id INTEGER NOT NULL,
        unit_name TEXT NOT NULL,
        normalized_unit_name TEXT NOT NULL,
        unit_quantity REAL NOT NULL DEFAULT 1,
        display_name TEXT NOT NULL,
        grams_default REAL NOT NULL,
        grams_min REAL,
        grams_max REAL,
        confidence TEXT NOT NULL,
        source TEXT,
        source_note TEXT,
        user_override_allowed INTEGER NOT NULL DEFAULT 0,
        active INTEGER NOT NULL DEFAULT 1,
        sort_order INTEGER NOT NULL DEFAULT 100,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(canonical_food_id, normalized_unit_name, unit_quantity),
        FOREIGN KEY (canonical_food_id) REFERENCES canonical_foods(id),
        CHECK (LENGTH(TRIM(unit_name)) > 0),
        CHECK (unit_quantity > 0),
        CHECK (grams_default > 0),
        CHECK (grams_min IS NULL OR grams_min > 0),
        CHECK (grams_max IS NULL OR grams_max > 0),
        CHECK (grams_min IS NULL OR grams_default >= grams_min),
        CHECK (grams_max IS NULL OR grams_default <= grams_max),
        CHECK (confidence IN ('Low', 'Moderate', 'High'))
    )
    """)
    cursor.execute(f"""
    CREATE INDEX IF NOT EXISTS idx_{SERVING_UNIT_TABLE_NAME}_food_active
    ON {SERVING_UNIT_TABLE_NAME}(canonical_food_id, active)
    """)
    conn.commit()
    conn.close()


def _normalize_confidence(confidence: str | None) -> str:
    normalized = (confidence or SERVING_UNIT_CONFIDENCE_MODERATE).strip().title()
    if normalized == "Medium":
        normalized = SERVING_UNIT_CONFIDENCE_MODERATE
    if normalized not in ALLOWED_SERVING_UNIT_CONFIDENCE:
        raise ValueError("Serving unit confidence must be one of: Low, Moderate, High.")
    return normalized


def _validate_serving_unit_values(
    *,
    canonical_food_id: int,
    unit_name: str,
    unit_quantity: float,
    display_name: str,
    grams_default: float,
    grams_min: float | None,
    grams_max: float | None,
    confidence: str | None,
) -> tuple[float, float, float | None, float | None, str]:
    if get_canonical_food(canonical_food_id) is None:
        raise ValueError("Serving unit canonical_food_id must reference a known food.")
    if not unit_name or not unit_name.strip():
        raise ValueError("Serving unit unit_name must be non-empty.")
    if not display_name or not display_name.strip():
        raise ValueError("Serving unit display_name must be non-empty.")

    resolved_unit_quantity = float(unit_quantity)
    resolved_grams_default = float(grams_default)
    resolved_grams_min = None if grams_min is None else float(grams_min)
    resolved_grams_max = None if grams_max is None else float(grams_max)

    if resolved_unit_quantity <= 0:
        raise ValueError("Serving unit unit_quantity must be positive.")
    if resolved_grams_default <= 0:
        raise ValueError("Serving unit grams_default must be positive.")
    if resolved_grams_min is not None and resolved_grams_min <= 0:
        raise ValueError("Serving unit grams_min must be positive when present.")
    if resolved_grams_max is not None and resolved_grams_max <= 0:
        raise ValueError("Serving unit grams_max must be positive when present.")
    if resolved_grams_min is not None and resolved_grams_default < resolved_grams_min:
        raise ValueError("Serving unit grams_min cannot exceed grams_default.")
    if resolved_grams_max is not None and resolved_grams_default > resolved_grams_max:
        raise ValueError("Serving unit grams_default cannot exceed grams_max.")

    return (
        resolved_unit_quantity,
        resolved_grams_default,
        resolved_grams_min,
        resolved_grams_max,
        _normalize_confidence(confidence),
    )


def _row_to_serving_unit(row: sqlite3.Row) -> NutritionServingUnit:
    return NutritionServingUnit(
        id=int(row["id"]),
        canonical_food_id=int(row["canonical_food_id"]),
        unit_name=row["unit_name"],
        unit_quantity=float(row["unit_quantity"]),
        display_name=row["display_name"],
        grams_default=float(row["grams_default"]),
        grams_min=None if row["grams_min"] is None else float(row["grams_min"]),
        grams_max=None if row["grams_max"] is None else float(row["grams_max"]),
        confidence=row["confidence"],
        source=row["source"],
        source_note=row["source_note"],
        user_override_allowed=bool(row["user_override_allowed"]),
        active=bool(row["active"]),
        sort_order=int(row["sort_order"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _fetch_existing_serving_unit_id(
    cursor: sqlite3.Cursor,
    *,
    canonical_food_id: int,
    normalized_unit_name: str,
    unit_quantity: float,
) -> int | None:
    cursor.execute(
        f"""
        SELECT id
        FROM {SERVING_UNIT_TABLE_NAME}
        WHERE canonical_food_id = ?
          AND normalized_unit_name = ?
          AND unit_quantity = ?
        """,
        (canonical_food_id, normalized_unit_name, unit_quantity),
    )
    row = cursor.fetchone()
    return None if row is None else int(row["id"])


def create_or_update_serving_unit(
    *,
    canonical_food_id: int,
    unit_name: str,
    unit_quantity: float = 1,
    display_name: str | None = None,
    grams_default: float,
    grams_min: float | None = None,
    grams_max: float | None = None,
    confidence: str = SERVING_UNIT_CONFIDENCE_MODERATE,
    source: str | None = None,
    source_note: str | None = None,
    user_override_allowed: bool = False,
    active: bool = True,
    sort_order: int = 100,
) -> tuple[NutritionServingUnit, bool]:
    ensure_serving_unit_schema()

    resolved_display_name = (display_name or unit_name).strip()
    (
        resolved_unit_quantity,
        resolved_grams_default,
        resolved_grams_min,
        resolved_grams_max,
        resolved_confidence,
    ) = _validate_serving_unit_values(
        canonical_food_id=canonical_food_id,
        unit_name=unit_name,
        unit_quantity=unit_quantity,
        display_name=resolved_display_name,
        grams_default=grams_default,
        grams_min=grams_min,
        grams_max=grams_max,
        confidence=confidence,
    )
    normalized_unit_name = normalize_food_name(unit_name)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    existing_id = _fetch_existing_serving_unit_id(
        cursor,
        canonical_food_id=canonical_food_id,
        normalized_unit_name=normalized_unit_name,
        unit_quantity=resolved_unit_quantity,
    )
    cursor.execute(
        f"""
        INSERT INTO {SERVING_UNIT_TABLE_NAME} (
            canonical_food_id,
            unit_name,
            normalized_unit_name,
            unit_quantity,
            display_name,
            grams_default,
            grams_min,
            grams_max,
            confidence,
            source,
            source_note,
            user_override_allowed,
            active,
            sort_order,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(canonical_food_id, normalized_unit_name, unit_quantity)
        DO UPDATE SET
            unit_name = excluded.unit_name,
            display_name = excluded.display_name,
            grams_default = excluded.grams_default,
            grams_min = excluded.grams_min,
            grams_max = excluded.grams_max,
            confidence = excluded.confidence,
            source = excluded.source,
            source_note = excluded.source_note,
            user_override_allowed = excluded.user_override_allowed,
            active = excluded.active,
            sort_order = excluded.sort_order,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            canonical_food_id,
            unit_name.strip(),
            normalized_unit_name,
            resolved_unit_quantity,
            resolved_display_name,
            resolved_grams_default,
            resolved_grams_min,
            resolved_grams_max,
            resolved_confidence,
            source,
            source_note,
            1 if user_override_allowed else 0,
            1 if active else 0,
            int(sort_order),
        ),
    )
    conn.commit()
    serving_unit_id = existing_id or int(cursor.lastrowid)
    cursor.execute(
        f"SELECT * FROM {SERVING_UNIT_TABLE_NAME} WHERE id = ?",
        (serving_unit_id,),
    )
    row = cursor.fetchone()
    conn.close()

    return _row_to_serving_unit(row), existing_id is None


def find_serving_unit(serving_unit_id: int) -> NutritionServingUnit | None:
    ensure_serving_unit_schema()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM {SERVING_UNIT_TABLE_NAME} WHERE id = ?",
        (int(serving_unit_id),),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None
    return _row_to_serving_unit(row)


def get_serving_units_for_canonical_food(
    canonical_food_id: int,
) -> list[NutritionServingUnit]:
    ensure_serving_unit_schema()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT *
        FROM {SERVING_UNIT_TABLE_NAME}
        WHERE canonical_food_id = ?
        ORDER BY sort_order, display_name, id
        """,
        (int(canonical_food_id),),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_serving_unit(row) for row in rows]


def get_active_serving_units_for_canonical_food(
    canonical_food_id: int,
) -> list[NutritionServingUnit]:
    ensure_serving_unit_schema()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT *
        FROM {SERVING_UNIT_TABLE_NAME}
        WHERE canonical_food_id = ?
          AND active = 1
        ORDER BY sort_order, display_name, id
        """,
        (int(canonical_food_id),),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_serving_unit(row) for row in rows]


def count_active_serving_units() -> int:
    ensure_serving_unit_schema()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT COUNT(*) AS count FROM {SERVING_UNIT_TABLE_NAME} WHERE active = 1"
    )
    count = int(cursor.fetchone()["count"])
    conn.close()
    return count


def count_canonical_foods_with_active_serving_units() -> int:
    ensure_serving_unit_schema()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT COUNT(DISTINCT canonical_food_id) AS count
        FROM {SERVING_UNIT_TABLE_NAME}
        WHERE active = 1
    """)
    count = int(cursor.fetchone()["count"])
    conn.close()
    return count


def estimate_grams_from_serving(
    serving_unit_id: int,
    quantity: float = 1,
) -> ServingUnitConversionEstimate:
    serving_unit = find_serving_unit(serving_unit_id)
    if serving_unit is None:
        raise ValueError("Serving unit not found.")

    requested_quantity = float(quantity)
    if requested_quantity <= 0:
        raise ValueError("Serving unit quantity must be greater than 0.")

    estimated_grams = serving_unit.grams_default * requested_quantity
    grams_min = (
        None
        if serving_unit.grams_min is None
        else serving_unit.grams_min * requested_quantity
    )
    grams_max = (
        None
        if serving_unit.grams_max is None
        else serving_unit.grams_max * requested_quantity
    )
    reason_codes = [
        "serving_unit_backend_estimate",
        f"serving_unit_confidence_{serving_unit.confidence.lower()}",
    ]
    if serving_unit.grams_min is not None or serving_unit.grams_max is not None:
        reason_codes.append("serving_unit_range_available")

    return ServingUnitConversionEstimate(
        serving_unit_id=serving_unit.id,
        canonical_food_id=serving_unit.canonical_food_id,
        requested_quantity=requested_quantity,
        estimated_grams=round(estimated_grams, 4),
        grams_min=None if grams_min is None else round(grams_min, 4),
        grams_max=None if grams_max is None else round(grams_max, 4),
        confidence=serving_unit.confidence,
        reason_codes=reason_codes,
    )


def estimate_nutrients_for_serving(
    canonical_food_id: int,
    serving_unit_id: int,
    quantity: float = 1,
) -> dict[str, dict[str, float | str]]:
    serving_unit = find_serving_unit(serving_unit_id)
    if serving_unit is None:
        raise ValueError("Serving unit not found.")
    if serving_unit.canonical_food_id != canonical_food_id:
        raise ValueError("Serving unit does not belong to the requested food.")

    conversion = estimate_grams_from_serving(serving_unit_id, quantity)
    nutrients = get_nutrients_for_canonical_food(canonical_food_id)
    result: dict[str, dict[str, float | str]] = {}
    for nutrient in nutrients:
        result[nutrient.nutrient_name] = {
            "amount": round(
                float(nutrient.amount_per_100g) * conversion.estimated_grams / 100.0,
                4,
            ),
            "unit": nutrient.nutrient_unit,
        }
    return result


def _find_active_canonical_food_id_by_display_name(display_name: str) -> int | None:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id
        FROM canonical_foods
        WHERE normalized_name = ?
          AND active = 1
        ORDER BY search_priority, display_name
        LIMIT 1
        """,
        (normalize_food_name(display_name),),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None
    return int(row["id"])


def seed_canonical_food_serving_units(
    seed_specs: (
        tuple[ServingUnitSeedSpec, ...] | list[ServingUnitSeedSpec]
    ) = DEFAULT_SERVING_UNIT_SEEDS,
) -> ServingUnitSeedResult:
    ensure_serving_unit_schema()

    result = ServingUnitSeedResult()
    for spec in seed_specs:
        canonical_food_id = _find_active_canonical_food_id_by_display_name(
            spec.canonical_food_display_name
        )
        if canonical_food_id is None:
            result.skipped_count += 1
            result.missing_canonical_foods.append(spec.canonical_food_display_name)
            continue

        serving_unit, was_inserted = create_or_update_serving_unit(
            canonical_food_id=canonical_food_id,
            unit_name=spec.unit_name,
            unit_quantity=spec.unit_quantity,
            display_name=spec.display_name,
            grams_default=spec.grams_default,
            grams_min=spec.grams_min,
            grams_max=spec.grams_max,
            confidence=spec.confidence,
            source=spec.source,
            source_note=spec.source_note,
            user_override_allowed=spec.user_override_allowed,
            active=spec.active,
            sort_order=spec.sort_order,
        )
        if was_inserted:
            result.inserted_count += 1
        else:
            result.updated_count += 1
        result.seeded_serving_units.append(serving_unit)

    result.active_serving_unit_count = count_active_serving_units()
    return result


def serving_unit_to_dict(serving_unit: NutritionServingUnit) -> dict[str, Any]:
    return asdict(serving_unit)


def serving_unit_seed_result_to_dict(result: ServingUnitSeedResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["seeded_serving_units"] = [
        serving_unit_to_dict(serving_unit)
        for serving_unit in result.seeded_serving_units
    ]
    return payload
