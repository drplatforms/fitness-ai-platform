from __future__ import annotations

from typing import Any

from database import get_connection
from models.nutrition_actuals_confidence_models import (
    NUTRITION_ACTUAL_COMPLETENESS_COMPLETE,
    NUTRITION_ACTUAL_COMPLETENESS_MISSING_NUTRIENTS,
    NUTRITION_ACTUAL_COMPLETENESS_PARTIAL,
    NUTRITION_ACTUAL_COMPLETENESS_UNKNOWN,
    NUTRITION_ACTUAL_CONFIDENCE_HIGH,
    NUTRITION_ACTUAL_CONFIDENCE_LOW,
    NUTRITION_ACTUAL_CONFIDENCE_MODERATE,
    NUTRITION_ACTUAL_CONFIDENCE_UNKNOWN,
    NUTRITION_ACTUAL_PRECISION_ESTIMATED,
    NUTRITION_ACTUAL_PRECISION_EXACT,
    NUTRITION_ACTUAL_PRECISION_LOW_CONFIDENCE,
    NUTRITION_ACTUAL_PRECISION_RANGED,
    NUTRITION_ACTUAL_PRECISION_UNKNOWN,
    NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS,
    NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT,
    NUTRITION_ACTUAL_SOURCE_RAW_GRAMS,
    NUTRITION_ACTUAL_SOURCE_UNKNOWN,
    NutritionActualInterpretation,
)
from services.nutrition_serving_unit_logging_service import (
    SERVING_UNIT_LOG_METADATA_TABLE_NAME,
)

_CANONICAL_FOOD_PREFIX = "Canonical: "
_CORE_NUTRIENTS = ("calories", "protein", "carbs", "fat")
_WIDE_GRAMS_RANGE_PERCENT_THRESHOLD = 25.0
_CONFIDENCE_MAP = {
    "High": NUTRITION_ACTUAL_CONFIDENCE_HIGH,
    "Moderate": NUTRITION_ACTUAL_CONFIDENCE_MODERATE,
    "Low": NUTRITION_ACTUAL_CONFIDENCE_LOW,
}
_NUTRIENT_ALIASES = {
    "calorie": "calories",
    "calories": "calories",
    "energy": "calories",
    "protein": "protein",
    "protein grams": "protein",
    "protein_grams": "protein",
    "carbohydrate": "carbs",
    "carbohydrates": "carbs",
    "carbs": "carbs",
    "total carbohydrate": "carbs",
    "fat": "fat",
    "total fat": "fat",
    "fats": "fat",
}


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _round(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _normalize_nutrient_name(name: str | None) -> str | None:
    if name is None:
        return None
    cleaned = " ".join(str(name).strip().lower().replace("_", " ").split())
    return _NUTRIENT_ALIASES.get(cleaned)


def _table_exists(table_name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    )
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def _food_entry_row(food_entry_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            food_entries.id AS food_entry_id,
            food_entries.user_id AS user_id,
            food_entries.food_id AS food_id,
            food_entries.grams AS grams,
            food_entries.entry_date AS entry_date,
            foods.name AS food_name
        FROM food_entries
        LEFT JOIN foods
            ON foods.id = food_entries.food_id
        WHERE food_entries.id = ?
        """,
        (int(food_entry_id),),
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def _serving_unit_metadata_row(food_entry_id: int) -> dict[str, Any] | None:
    if not _table_exists(SERVING_UNIT_LOG_METADATA_TABLE_NAME):
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            food_entry_id,
            resolved_grams,
            grams_min,
            grams_max,
            serving_unit_confidence,
            amount_source
        FROM {SERVING_UNIT_LOG_METADATA_TABLE_NAME}
        WHERE food_entry_id = ?
        """,
        (int(food_entry_id),),
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def _available_core_nutrients(food_id: int | None) -> set[str]:
    if food_id is None:
        return set()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT nutrients.name AS nutrient_name
        FROM food_nutrients
        JOIN nutrients
            ON nutrients.id = food_nutrients.nutrient_id
        WHERE food_nutrients.food_id = ?
        """,
        (int(food_id),),
    )
    rows = cursor.fetchall()
    conn.close()

    nutrients: set[str] = set()
    for row in rows:
        normalized = _normalize_nutrient_name(row["nutrient_name"])
        if normalized in _CORE_NUTRIENTS:
            nutrients.add(normalized)
    return nutrients


def _nutrient_completeness(
    available_nutrients: set[str],
) -> tuple[str, list[str], list[str], list[str], list[str]]:
    missing = [
        nutrient for nutrient in _CORE_NUTRIENTS if nutrient not in available_nutrients
    ]
    reason_codes: list[str] = []
    limitations: list[str] = []
    display_flags: list[str] = []

    if not available_nutrients:
        completeness = NUTRITION_ACTUAL_COMPLETENESS_MISSING_NUTRIENTS
        reason_codes.append("missing_nutrient_values")
        limitations.append(
            "Nutrient values are missing for this logged food; "
            "missing values were not treated as zero."
        )
        display_flags.append("show_missing_nutrient_limitation")
    elif missing:
        completeness = NUTRITION_ACTUAL_COMPLETENESS_PARTIAL
        reason_codes.append("missing_nutrient_values")
        limitations.append(
            "Some nutrient values are missing for this logged food; "
            "missing values were not treated as zero."
        )
        display_flags.append("show_missing_nutrient_limitation")
    else:
        completeness = NUTRITION_ACTUAL_COMPLETENESS_COMPLETE
        reason_codes.append("core_nutrients_available")

    return completeness, missing, reason_codes, limitations, display_flags


def _confidence_level(serving_unit_confidence: str | None, *, source_type: str) -> str:
    if source_type == NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT:
        return _CONFIDENCE_MAP.get(
            serving_unit_confidence or "", NUTRITION_ACTUAL_CONFIDENCE_UNKNOWN
        )
    if source_type == NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS:
        return NUTRITION_ACTUAL_CONFIDENCE_MODERATE
    if source_type == NUTRITION_ACTUAL_SOURCE_RAW_GRAMS:
        return NUTRITION_ACTUAL_CONFIDENCE_MODERATE
    return NUTRITION_ACTUAL_CONFIDENCE_UNKNOWN


def _classify_source(row: dict[str, Any], metadata: dict[str, Any] | None) -> str:
    if metadata is not None:
        return NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT
    food_name = str(row.get("food_name") or "")
    if food_name.startswith(_CANONICAL_FOOD_PREFIX):
        return NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS
    if food_name.strip():
        return NUTRITION_ACTUAL_SOURCE_RAW_GRAMS
    return NUTRITION_ACTUAL_SOURCE_UNKNOWN


def _grams_range_fields(
    *,
    resolved_grams: float | None,
    grams_min: float | None,
    grams_max: float | None,
) -> tuple[bool, float | None, float | None]:
    if grams_min is None or grams_max is None:
        return False, None, None

    grams_range_width = _round(float(grams_max) - float(grams_min))
    if grams_range_width is None or grams_range_width <= 0:
        return False, None, None

    grams_range_percent = None
    if resolved_grams is not None and resolved_grams > 0:
        grams_range_percent = round(
            grams_range_width / float(resolved_grams) * 100.0,
            1,
        )
    return True, grams_range_width, grams_range_percent


def _source_reason_codes(source_type: str) -> list[str]:
    if source_type == NUTRITION_ACTUAL_SOURCE_RAW_GRAMS:
        return ["raw_grams_entry", "user_entered_grams", "no_serving_unit_metadata"]
    if source_type == NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS:
        return [
            "canonical_food_entry",
            "user_entered_grams",
            "no_serving_unit_metadata",
        ]
    if source_type == NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT:
        return [
            "serving_unit_entry",
            "serving_unit_metadata_available",
            "resolved_grams_from_backend_serving_unit",
        ]
    return ["actual_source_unclassified"]


def build_nutrition_actual_interpretation(
    food_entry_id: int,
) -> NutritionActualInterpretation:
    """Classify one logged nutrition actual without mutating logging or totals."""

    row = _food_entry_row(food_entry_id)
    if row is None:
        return NutritionActualInterpretation(
            food_entry_id=int(food_entry_id),
            user_id=None,
            logged_date=None,
            source_type=NUTRITION_ACTUAL_SOURCE_UNKNOWN,
            precision=NUTRITION_ACTUAL_PRECISION_UNKNOWN,
            confidence_level=NUTRITION_ACTUAL_CONFIDENCE_UNKNOWN,
            nutrient_completeness=NUTRITION_ACTUAL_COMPLETENESS_UNKNOWN,
            has_serving_unit_metadata=False,
            has_grams_range=False,
            resolved_grams=None,
            limitations=["Actual source could not be classified safely."],
            reason_codes=["actual_source_unclassified", "food_entry_not_found"],
            display_flags=["show_actual_source_unknown"],
        )

    metadata = _serving_unit_metadata_row(food_entry_id)
    source_type = _classify_source(row, metadata)
    resolved_grams = _round(
        metadata["resolved_grams"] if metadata is not None else row.get("grams")
    )
    grams_min = _round(None if metadata is None else metadata.get("grams_min"))
    grams_max = _round(None if metadata is None else metadata.get("grams_max"))
    has_range, grams_range_width, grams_range_percent = _grams_range_fields(
        resolved_grams=resolved_grams,
        grams_min=grams_min,
        grams_max=grams_max,
    )

    serving_unit_confidence = (
        None if metadata is None else metadata.get("serving_unit_confidence")
    )
    confidence_level = _confidence_level(
        serving_unit_confidence,
        source_type=source_type,
    )

    if source_type in {
        NUTRITION_ACTUAL_SOURCE_RAW_GRAMS,
        NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS,
    }:
        precision = NUTRITION_ACTUAL_PRECISION_EXACT
    elif source_type == NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT:
        if has_range:
            precision = NUTRITION_ACTUAL_PRECISION_RANGED
        elif confidence_level == NUTRITION_ACTUAL_CONFIDENCE_LOW:
            precision = NUTRITION_ACTUAL_PRECISION_LOW_CONFIDENCE
        else:
            precision = NUTRITION_ACTUAL_PRECISION_ESTIMATED
    else:
        precision = NUTRITION_ACTUAL_PRECISION_UNKNOWN

    available_nutrients = _available_core_nutrients(row.get("food_id"))
    (
        nutrient_completeness,
        missing_nutrients,
        nutrient_reason_codes,
        nutrient_limitations,
        nutrient_display_flags,
    ) = _nutrient_completeness(available_nutrients)

    reason_codes = [*_source_reason_codes(source_type), *nutrient_reason_codes]
    limitations = list(nutrient_limitations)
    display_flags = list(nutrient_display_flags)

    if source_type == NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT:
        display_flags.append("show_serving_unit_provenance")
        if has_range:
            reason_codes.append("grams_range_available")
            display_flags.append("show_grams_range")
            if (
                grams_range_percent is not None
                and grams_range_percent >= _WIDE_GRAMS_RANGE_PERCENT_THRESHOLD
            ):
                reason_codes.append("wide_serving_unit_range")
                limitations.append("Serving-size estimate has a wider gram range.")
                display_flags.append("show_wide_range_limitation")
        if confidence_level == NUTRITION_ACTUAL_CONFIDENCE_LOW:
            reason_codes.append("low_confidence_serving_unit")
            limitations.append("Serving-unit confidence is limited.")
            display_flags.append("show_low_confidence_limitation")
        elif confidence_level == NUTRITION_ACTUAL_CONFIDENCE_UNKNOWN:
            reason_codes.append("unknown_serving_unit_confidence")
            limitations.append("Serving-unit confidence is unknown.")
            display_flags.append("show_unknown_confidence_limitation")

    if source_type == NUTRITION_ACTUAL_SOURCE_UNKNOWN:
        limitations.append("Actual source could not be classified safely.")
        display_flags.append("show_actual_source_unknown")

    return NutritionActualInterpretation(
        food_entry_id=int(food_entry_id),
        user_id=int(row["user_id"]),
        logged_date=str(row["entry_date"]),
        source_type=source_type,
        precision=precision,
        confidence_level=confidence_level,
        nutrient_completeness=nutrient_completeness,
        has_serving_unit_metadata=metadata is not None,
        has_grams_range=has_range,
        resolved_grams=resolved_grams,
        grams_min=grams_min,
        grams_max=grams_max,
        grams_range_width=grams_range_width,
        grams_range_percent=grams_range_percent,
        amount_source=None if metadata is None else metadata.get("amount_source"),
        serving_unit_confidence=serving_unit_confidence,
        missing_nutrients=missing_nutrients,
        limitations=_unique(limitations),
        reason_codes=_unique(reason_codes),
        display_flags=_unique(display_flags),
    )


def build_nutrition_actual_interpretations_for_date(
    *,
    user_id: int,
    target_date: str,
) -> list[NutritionActualInterpretation]:
    """Return public-safe actuals interpretations for a user's logged date."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id
        FROM food_entries
        WHERE user_id = ?
          AND entry_date = ?
        ORDER BY id
        """,
        (int(user_id), str(target_date)),
    )
    food_entry_ids = [int(row["id"]) for row in cursor.fetchall()]
    conn.close()

    return [
        build_nutrition_actual_interpretation(food_entry_id)
        for food_entry_id in food_entry_ids
    ]


def build_public_nutrition_actual_interpretation(
    food_entry_id: int,
) -> dict[str, object]:
    """Build a bounded public-safe dictionary for one logged actual."""

    return build_nutrition_actual_interpretation(food_entry_id).to_public_dict()


def _summarize_actual_interpretations(
    interpretations: list[NutritionActualInterpretation],
) -> dict[str, int]:
    """Build public-safe aggregate counts for actuals confidence debug output."""

    return {
        "total_entries": len(interpretations),
        "entries_with_serving_unit_metadata": sum(
            1 for item in interpretations if item.has_serving_unit_metadata
        ),
        "entries_with_grams_range": sum(
            1 for item in interpretations if item.has_grams_range
        ),
        "entries_with_low_or_unknown_confidence": sum(
            1
            for item in interpretations
            if item.confidence_level
            in {
                NUTRITION_ACTUAL_CONFIDENCE_LOW,
                NUTRITION_ACTUAL_CONFIDENCE_UNKNOWN,
            }
        ),
        "entries_with_missing_nutrients": sum(
            1
            for item in interpretations
            if item.nutrient_completeness
            in {
                NUTRITION_ACTUAL_COMPLETENESS_MISSING_NUTRIENTS,
                NUTRITION_ACTUAL_COMPLETENESS_PARTIAL,
                NUTRITION_ACTUAL_COMPLETENESS_UNKNOWN,
            }
        ),
    }


def build_public_nutrition_actuals_confidence_for_date(
    *,
    user_id: int,
    target_date: str,
) -> dict[str, object]:
    """Build public-safe actuals confidence/provenance debug output for a date."""

    interpretations = build_nutrition_actual_interpretations_for_date(
        user_id=int(user_id),
        target_date=str(target_date),
    )

    return {
        "success": True,
        "user_id": int(user_id),
        "date": str(target_date),
        "actuals": [item.to_public_dict() for item in interpretations],
        "summary": _summarize_actual_interpretations(interpretations),
    }
