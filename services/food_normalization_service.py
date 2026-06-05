from __future__ import annotations

import json
import re
from dataclasses import asdict
from typing import Any

from database import get_connection
from models.food_normalization_models import (
    CanonicalFood,
    CanonicalFoodAlias,
    CanonicalFoodNutrient,
    CanonicalFoodSearchResult,
    FoodSourceLink,
    RawFoodSourceRecord,
)

ALLOWED_FOOD_TYPES = {"raw", "cooked", "prepared", "branded", "generic"}
ALLOWED_SOURCE_POLICIES = {"direct_source", "averaged_sources", "manually_curated"}
ALLOWED_NUTRIENT_CONFIDENCE = {"Limited", "Low", "Moderate", "High"}
ALLOWED_SOURCE_RELATIONSHIPS = {
    "primary",
    "supporting",
    "equivalent",
    "alternate_preparation",
}

STARTER_CANONICAL_FOODS = [
    {
        "display_name": "Chicken Breast, Cooked, Skinless",
        "food_type": "cooked",
        "aliases": ["chicken breast", "cooked chicken", "boneless chicken"],
        "search_priority": 10,
    },
    {
        "display_name": "Chicken Breast, Raw, Skinless",
        "food_type": "raw",
        "aliases": ["raw chicken breast", "uncooked chicken breast"],
        "search_priority": 20,
    },
    {
        "display_name": "White Rice, Cooked",
        "food_type": "cooked",
        "aliases": ["white rice", "cooked rice", "rice"],
        "search_priority": 10,
    },
    {
        "display_name": "Brown Rice, Cooked",
        "food_type": "cooked",
        "aliases": ["brown rice", "cooked brown rice"],
        "search_priority": 20,
    },
    {
        "display_name": "Egg, Large",
        "food_type": "generic",
        "aliases": ["egg", "large egg", "eggs"],
        "search_priority": 10,
    },
    {
        "display_name": "Ground Beef, 90/10",
        "food_type": "raw",
        "aliases": ["ground beef", "lean ground beef", "90/10 beef"],
        "search_priority": 20,
    },
    {
        "display_name": "Ground Beef, 80/20",
        "food_type": "raw",
        "aliases": ["80/20 beef", "ground chuck"],
        "search_priority": 30,
    },
    {
        "display_name": "Salmon, Cooked",
        "food_type": "cooked",
        "aliases": ["salmon", "cooked salmon"],
        "search_priority": 20,
    },
    {
        "display_name": "Greek Yogurt, Plain",
        "food_type": "generic",
        "aliases": ["greek yogurt", "plain greek yogurt", "yogurt"],
        "search_priority": 20,
    },
    {
        "display_name": "Oats, Dry",
        "food_type": "raw",
        "aliases": ["oats", "dry oats", "oatmeal"],
        "search_priority": 20,
    },
    {
        "display_name": "Banana",
        "food_type": "generic",
        "aliases": ["banana", "bananas"],
        "search_priority": 10,
    },
    {
        "display_name": "Potato, Baked",
        "food_type": "cooked",
        "aliases": ["potato", "baked potato"],
        "search_priority": 20,
    },
    {
        "display_name": "Sweet Potato, Baked",
        "food_type": "cooked",
        "aliases": ["sweet potato", "baked sweet potato"],
        "search_priority": 20,
    },
    {
        "display_name": "Broccoli, Cooked",
        "food_type": "cooked",
        "aliases": ["broccoli", "cooked broccoli"],
        "search_priority": 20,
    },
    {
        "display_name": "Olive Oil",
        "food_type": "generic",
        "aliases": ["olive oil", "oil"],
        "search_priority": 20,
    },
]


def normalize_food_name(value: str) -> str:
    normalized = value.strip().lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _normalize_food_type(food_type: str | None) -> str:
    normalized = normalize_food_name(food_type or "generic").replace(" ", "_")
    if normalized not in ALLOWED_FOOD_TYPES:
        return "generic"
    return normalized


def _normalize_default_unit(default_unit: str | None) -> str:
    normalized = normalize_food_name(default_unit or "grams")
    if normalized in {"g", "gram", "grams"}:
        return "grams"
    return normalized or "grams"


def _normalize_source_policy(source_policy: str | None) -> str:
    normalized = normalize_food_name(source_policy or "manually_curated").replace(
        " ", "_"
    )
    if normalized not in ALLOWED_SOURCE_POLICIES:
        return "manually_curated"
    return normalized


def _normalize_confidence(confidence: str | None) -> str:
    if not confidence:
        return "Moderate"

    normalized = confidence.strip().title()
    if normalized not in ALLOWED_NUTRIENT_CONFIDENCE:
        return "Moderate"

    return normalized


def _normalize_relationship_type(relationship_type: str | None) -> str:
    normalized = normalize_food_name(relationship_type or "primary").replace(" ", "_")
    if normalized not in ALLOWED_SOURCE_RELATIONSHIPS:
        return "primary"
    return normalized


def _encode_json_payload(source_payload: dict[str, Any] | str | None) -> str | None:
    if source_payload is None:
        return None
    if isinstance(source_payload, str):
        return source_payload
    return json.dumps(source_payload, sort_keys=True)


def ensure_food_normalization_tables() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_food_source_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT NOT NULL,
        source_record_id TEXT NOT NULL,
        raw_description TEXT NOT NULL,
        brand_name TEXT,
        food_category TEXT,
        source_payload_json TEXT,
        license TEXT,
        source_url TEXT,
        imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(source_name, source_record_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS canonical_foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        display_name TEXT NOT NULL,
        normalized_name TEXT NOT NULL,
        food_type TEXT NOT NULL DEFAULT 'generic',
        default_unit TEXT NOT NULL DEFAULT 'grams',
        default_grams REAL,
        search_priority INTEGER NOT NULL DEFAULT 100,
        active INTEGER NOT NULL DEFAULT 1,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(normalized_name, food_type)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS canonical_food_aliases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_food_id INTEGER NOT NULL,
        alias TEXT NOT NULL,
        normalized_alias TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 100,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(canonical_food_id, normalized_alias),
        FOREIGN KEY (canonical_food_id) REFERENCES canonical_foods(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS canonical_food_nutrients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_food_id INTEGER NOT NULL,
        nutrient_name TEXT NOT NULL,
        nutrient_unit TEXT NOT NULL,
        amount_per_100g REAL NOT NULL,
        source_policy TEXT NOT NULL DEFAULT 'manually_curated',
        confidence TEXT NOT NULL DEFAULT 'Moderate',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(canonical_food_id, nutrient_name),
        FOREIGN KEY (canonical_food_id) REFERENCES canonical_foods(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_source_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_food_id INTEGER NOT NULL,
        raw_food_source_record_id INTEGER NOT NULL,
        relationship_type TEXT NOT NULL DEFAULT 'primary',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(canonical_food_id, raw_food_source_record_id, relationship_type),
        FOREIGN KEY (canonical_food_id) REFERENCES canonical_foods(id),
        FOREIGN KEY (raw_food_source_record_id) REFERENCES raw_food_source_records(id)
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_canonical_foods_normalized_name
    ON canonical_foods(normalized_name)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_canonical_food_aliases_normalized_alias
    ON canonical_food_aliases(normalized_alias)
    """)

    conn.commit()
    conn.close()


def _row_to_raw_food_source_record(row) -> RawFoodSourceRecord:
    return RawFoodSourceRecord(
        id=row["id"],
        source_name=row["source_name"],
        source_record_id=row["source_record_id"],
        raw_description=row["raw_description"],
        brand_name=row["brand_name"],
        food_category=row["food_category"],
        source_payload_json=row["source_payload_json"],
        license=row["license"],
        source_url=row["source_url"],
        imported_at=row["imported_at"],
        updated_at=row["updated_at"],
    )


def _row_to_canonical_food(row) -> CanonicalFood:
    return CanonicalFood(
        id=row["id"],
        display_name=row["display_name"],
        normalized_name=row["normalized_name"],
        food_type=row["food_type"],
        default_unit=row["default_unit"],
        default_grams=row["default_grams"],
        search_priority=row["search_priority"],
        active=bool(row["active"]),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_canonical_food_alias(row) -> CanonicalFoodAlias:
    return CanonicalFoodAlias(
        id=row["id"],
        canonical_food_id=row["canonical_food_id"],
        alias=row["alias"],
        normalized_alias=row["normalized_alias"],
        priority=row["priority"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_canonical_food_nutrient(row) -> CanonicalFoodNutrient:
    return CanonicalFoodNutrient(
        id=row["id"],
        canonical_food_id=row["canonical_food_id"],
        nutrient_name=row["nutrient_name"],
        nutrient_unit=row["nutrient_unit"],
        amount_per_100g=row["amount_per_100g"],
        source_policy=row["source_policy"],
        confidence=row["confidence"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_food_source_link(row) -> FoodSourceLink:
    return FoodSourceLink(
        id=row["id"],
        canonical_food_id=row["canonical_food_id"],
        raw_food_source_record_id=row["raw_food_source_record_id"],
        relationship_type=row["relationship_type"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_raw_food_source_record(
    source_name: str,
    source_record_id: str,
    raw_description: str,
    brand_name: str | None = None,
    food_category: str | None = None,
    source_payload: dict[str, Any] | str | None = None,
    license: str | None = None,
    source_url: str | None = None,
) -> RawFoodSourceRecord:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO raw_food_source_records (
            source_name,
            source_record_id,
            raw_description,
            brand_name,
            food_category,
            source_payload_json,
            license,
            source_url,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(source_name, source_record_id) DO UPDATE SET
            raw_description = excluded.raw_description,
            brand_name = excluded.brand_name,
            food_category = excluded.food_category,
            source_payload_json = excluded.source_payload_json,
            license = excluded.license,
            source_url = excluded.source_url,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            source_name.strip(),
            str(source_record_id).strip(),
            raw_description.strip(),
            brand_name,
            food_category,
            _encode_json_payload(source_payload),
            license,
            source_url,
        ),
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_name = ? AND source_record_id = ?
        """,
        (source_name.strip(), str(source_record_id).strip()),
    )
    row = cursor.fetchone()
    conn.close()

    return _row_to_raw_food_source_record(row)


def get_raw_food_source_record(record_id: int) -> RawFoodSourceRecord | None:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM raw_food_source_records WHERE id = ?",
        (record_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return _row_to_raw_food_source_record(row)


def create_canonical_food(
    display_name: str,
    food_type: str = "generic",
    default_unit: str = "grams",
    default_grams: float | None = None,
    search_priority: int = 100,
    active: bool = True,
    notes: str | None = None,
) -> CanonicalFood:
    ensure_food_normalization_tables()

    normalized_food_type = _normalize_food_type(food_type)
    normalized_name = normalize_food_name(display_name)
    normalized_unit = _normalize_default_unit(default_unit)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO canonical_foods (
            display_name,
            normalized_name,
            food_type,
            default_unit,
            default_grams,
            search_priority,
            active,
            notes,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(normalized_name, food_type) DO UPDATE SET
            display_name = excluded.display_name,
            default_unit = excluded.default_unit,
            default_grams = excluded.default_grams,
            search_priority = excluded.search_priority,
            active = excluded.active,
            notes = excluded.notes,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            display_name.strip(),
            normalized_name,
            normalized_food_type,
            normalized_unit,
            default_grams,
            int(search_priority),
            1 if active else 0,
            notes,
        ),
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM canonical_foods
        WHERE normalized_name = ? AND food_type = ?
        """,
        (normalized_name, normalized_food_type),
    )
    row = cursor.fetchone()
    conn.close()

    return _row_to_canonical_food(row)


def get_canonical_food(canonical_food_id: int) -> CanonicalFood | None:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM canonical_foods WHERE id = ?", (canonical_food_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return _row_to_canonical_food(row)


def create_canonical_food_alias(
    canonical_food_id: int,
    alias: str,
    priority: int = 100,
) -> CanonicalFoodAlias:
    ensure_food_normalization_tables()

    normalized_alias = normalize_food_name(alias)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO canonical_food_aliases (
            canonical_food_id,
            alias,
            normalized_alias,
            priority,
            updated_at
        )
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(canonical_food_id, normalized_alias) DO UPDATE SET
            alias = excluded.alias,
            priority = excluded.priority,
            updated_at = CURRENT_TIMESTAMP
        """,
        (canonical_food_id, alias.strip(), normalized_alias, int(priority)),
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM canonical_food_aliases
        WHERE canonical_food_id = ? AND normalized_alias = ?
        """,
        (canonical_food_id, normalized_alias),
    )
    row = cursor.fetchone()
    conn.close()

    return _row_to_canonical_food_alias(row)


def create_canonical_food_nutrient(
    canonical_food_id: int,
    nutrient_name: str,
    nutrient_unit: str,
    amount_per_100g: float,
    source_policy: str = "manually_curated",
    confidence: str = "Moderate",
) -> CanonicalFoodNutrient:
    ensure_food_normalization_tables()

    normalized_source_policy = _normalize_source_policy(source_policy)
    normalized_confidence = _normalize_confidence(confidence)

    if amount_per_100g < 0:
        raise ValueError("Canonical nutrient amount_per_100g cannot be negative.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO canonical_food_nutrients (
            canonical_food_id,
            nutrient_name,
            nutrient_unit,
            amount_per_100g,
            source_policy,
            confidence,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(canonical_food_id, nutrient_name) DO UPDATE SET
            nutrient_unit = excluded.nutrient_unit,
            amount_per_100g = excluded.amount_per_100g,
            source_policy = excluded.source_policy,
            confidence = excluded.confidence,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            canonical_food_id,
            nutrient_name.strip(),
            nutrient_unit.strip(),
            float(amount_per_100g),
            normalized_source_policy,
            normalized_confidence,
        ),
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM canonical_food_nutrients
        WHERE canonical_food_id = ? AND nutrient_name = ?
        """,
        (canonical_food_id, nutrient_name.strip()),
    )
    row = cursor.fetchone()
    conn.close()

    return _row_to_canonical_food_nutrient(row)


def link_canonical_food_to_source(
    canonical_food_id: int,
    raw_food_source_record_id: int,
    relationship_type: str = "primary",
) -> FoodSourceLink:
    ensure_food_normalization_tables()

    normalized_relationship = _normalize_relationship_type(relationship_type)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO food_source_links (
            canonical_food_id,
            raw_food_source_record_id,
            relationship_type,
            updated_at
        )
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(
            canonical_food_id,
            raw_food_source_record_id,
            relationship_type
        ) DO UPDATE SET
            updated_at = CURRENT_TIMESTAMP
        """,
        (canonical_food_id, raw_food_source_record_id, normalized_relationship),
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM food_source_links
        WHERE canonical_food_id = ?
          AND raw_food_source_record_id = ?
          AND relationship_type = ?
        """,
        (canonical_food_id, raw_food_source_record_id, normalized_relationship),
    )
    row = cursor.fetchone()
    conn.close()

    return _row_to_food_source_link(row)


def get_source_links_for_canonical_food(canonical_food_id: int) -> list[FoodSourceLink]:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM food_source_links
        WHERE canonical_food_id = ?
        ORDER BY
            CASE relationship_type
                WHEN 'primary' THEN 1
                WHEN 'equivalent' THEN 2
                WHEN 'supporting' THEN 3
                WHEN 'alternate_preparation' THEN 4
                ELSE 5
            END,
            id
        """,
        (canonical_food_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_food_source_link(row) for row in rows]


def get_aliases_for_canonical_food(canonical_food_id: int) -> list[CanonicalFoodAlias]:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM canonical_food_aliases
        WHERE canonical_food_id = ?
        ORDER BY priority, alias
        """,
        (canonical_food_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_canonical_food_alias(row) for row in rows]


def get_nutrients_for_canonical_food(
    canonical_food_id: int,
) -> list[CanonicalFoodNutrient]:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM canonical_food_nutrients
        WHERE canonical_food_id = ?
        ORDER BY nutrient_name
        """,
        (canonical_food_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_canonical_food_nutrient(row) for row in rows]


def _build_search_result(row) -> CanonicalFoodSearchResult:
    canonical_food = _row_to_canonical_food(row)
    aliases = [alias for alias in (row["aliases"] or "").split("||") if alias]
    return CanonicalFoodSearchResult(
        canonical_food=canonical_food,
        matched_on=row["matched_on"],
        matched_value=row["matched_value"],
        rank_score=row["rank_score"],
        aliases=aliases,
    )


def search_canonical_foods(
    search_term: str, limit: int = 10
) -> list[CanonicalFoodSearchResult]:
    ensure_food_normalization_tables()

    normalized_query = normalize_food_name(search_term)
    if not normalized_query:
        return []

    like_query = f"%{normalized_query}%"
    prefix_query = f"{normalized_query}%"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        WITH matched AS (
            SELECT
                canonical_foods.*,
                'display_name' AS matched_on,
                canonical_foods.display_name AS matched_value,
                CASE
                    WHEN canonical_foods.normalized_name = ? THEN 0
                    WHEN canonical_foods.normalized_name LIKE ? THEN 10
                    WHEN canonical_foods.normalized_name LIKE ? THEN 30
                    ELSE 80
                END + canonical_foods.search_priority AS rank_score
            FROM canonical_foods
            WHERE canonical_foods.active = 1
              AND canonical_foods.normalized_name LIKE ?

            UNION ALL

            SELECT
                canonical_foods.*,
                'alias' AS matched_on,
                canonical_food_aliases.alias AS matched_value,
                CASE
                    WHEN canonical_food_aliases.normalized_alias = ? THEN 5
                    WHEN canonical_food_aliases.normalized_alias LIKE ? THEN 15
                    WHEN canonical_food_aliases.normalized_alias LIKE ? THEN 35
                    ELSE 90
                END + canonical_foods.search_priority + canonical_food_aliases.priority AS rank_score
            FROM canonical_food_aliases
            JOIN canonical_foods
                ON canonical_food_aliases.canonical_food_id = canonical_foods.id
            WHERE canonical_foods.active = 1
              AND canonical_food_aliases.normalized_alias LIKE ?
        ),
        best_match AS (
            SELECT
                matched.*,
                ROW_NUMBER() OVER (
                    PARTITION BY matched.id
                    ORDER BY matched.rank_score, matched.display_name
                ) AS match_rank
            FROM matched
        )
        SELECT
            best_match.*,
            (
                SELECT GROUP_CONCAT(canonical_food_aliases.alias, '||')
                FROM canonical_food_aliases
                WHERE canonical_food_aliases.canonical_food_id = best_match.id
            ) AS aliases
        FROM best_match
        WHERE match_rank = 1
        ORDER BY rank_score, search_priority, display_name
        LIMIT ?
        """,
        (
            normalized_query,
            prefix_query,
            like_query,
            like_query,
            normalized_query,
            prefix_query,
            like_query,
            like_query,
            limit,
        ),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_build_search_result(row) for row in rows]


def seed_starter_canonical_foods() -> list[CanonicalFood]:
    ensure_food_normalization_tables()

    seeded_foods = []
    for seed_food in STARTER_CANONICAL_FOODS:
        food = create_canonical_food(
            display_name=seed_food["display_name"],
            food_type=seed_food["food_type"],
            default_unit="grams",
            default_grams=100.0,
            search_priority=seed_food["search_priority"],
            active=True,
            notes="Starter canonical food for app-facing search.",
        )
        seeded_foods.append(food)

        for index, alias in enumerate(seed_food["aliases"]):
            create_canonical_food_alias(
                canonical_food_id=food.id,
                alias=alias,
                priority=10 + index,
            )

    return seeded_foods


def canonical_food_to_dict(food: CanonicalFood) -> dict[str, Any]:
    return asdict(food)


def raw_food_source_record_to_dict(record: RawFoodSourceRecord) -> dict[str, Any]:
    return asdict(record)


def canonical_search_result_to_dict(
    result: CanonicalFoodSearchResult,
) -> dict[str, Any]:
    return {
        "canonical_food": canonical_food_to_dict(result.canonical_food),
        "matched_on": result.matched_on,
        "matched_value": result.matched_value,
        "rank_score": result.rank_score,
        "aliases": result.aliases,
    }
