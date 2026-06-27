# =====================================
# Imports
# =====================================

from datetime import date as date_cls

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nutrition_actuals_confidence_service import (
    build_public_nutrition_actuals_confidence_for_date,
)
from services.nutrition_service import (
    CanonicalFoodInactiveError,
    CanonicalFoodLoggingError,
    CanonicalFoodNotFoundError,
    add_canonical_food_entry,
    add_food_entry,
    get_daily_nutrition,
    search_foods,
)
from services.nutrition_serving_unit_logging_service import (
    ServingUnitFoodMismatchError,
    ServingUnitInactiveError,
    ServingUnitLoggingError,
    ServingUnitNotFoundError,
    log_canonical_food_serving,
)

# =====================================
# Router Initialization
# =====================================

router = APIRouter()


# =====================================
# Request Models
# =====================================


class NutritionLogRequest(BaseModel):
    user_id: int
    food_id: int
    grams: float


class CanonicalNutritionLogRequest(BaseModel):
    canonical_food_id: int
    grams: float
    entry_date: str | None = None


class ServingUnitNutritionLogRequest(BaseModel):
    canonical_food_id: int
    serving_unit_id: int
    quantity: float
    meal: str | None = None
    logged_date: str | None = None


# =====================================
# Food Search Endpoint
# =====================================


@router.get("/foods/search")
def search_foods_endpoint(query: str):
    foods = search_foods(query)

    return {
        "success": True,
        "foods": foods,
    }


# =====================================
# Daily Nutrition Endpoint
# =====================================


@router.get("/nutrition/{user_id}/{entry_date}")
def daily_nutrition(user_id: int, entry_date: str):
    nutrition = get_daily_nutrition(user_id, entry_date)

    return {
        "success": True,
        "nutrition": nutrition,
    }


# =====================================
# Nutrition Actuals Confidence Debug Endpoint
# =====================================


@router.get("/nutrition/{user_id}/actuals-confidence/debug")
def nutrition_actuals_confidence_debug(user_id: int, date: str):
    try:
        date_cls.fromisoformat(date)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="date must use YYYY-MM-DD format.",
        ) from exc

    return build_public_nutrition_actuals_confidence_for_date(
        user_id=user_id,
        target_date=date,
    )


# =====================================
# Log Food Endpoint
# =====================================


@router.post("/nutrition/log")
def log_food_entry(entry: NutritionLogRequest):
    add_food_entry(
        user_id=entry.user_id,
        food_id=entry.food_id,
        grams=entry.grams,
    )

    return {
        "success": True,
        "message": "Food logged successfully.",
    }


@router.post("/nutrition/{user_id}/log-canonical")
def log_canonical_food_entry(
    user_id: int,
    entry: CanonicalNutritionLogRequest,
):
    if entry.entry_date is not None:
        try:
            date_cls.fromisoformat(entry.entry_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="entry_date must use YYYY-MM-DD format.",
            ) from exc

    try:
        logged_entry = add_canonical_food_entry(
            user_id=user_id,
            canonical_food_id=entry.canonical_food_id,
            grams=entry.grams,
            entry_date=entry.entry_date,
        )
    except CanonicalFoodNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanonicalFoodInactiveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CanonicalFoodLoggingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        **logged_entry,
    }


@router.post("/nutrition/{user_id}/log-serving")
def log_serving_unit_food_entry(
    user_id: int,
    entry: ServingUnitNutritionLogRequest,
):
    if entry.logged_date is not None:
        try:
            date_cls.fromisoformat(entry.logged_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="logged_date must use YYYY-MM-DD format.",
            ) from exc

    try:
        logged_entry = log_canonical_food_serving(
            user_id=user_id,
            canonical_food_id=entry.canonical_food_id,
            serving_unit_id=entry.serving_unit_id,
            quantity=entry.quantity,
            entry_date=entry.logged_date,
        )
    except CanonicalFoodNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ServingUnitNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanonicalFoodInactiveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServingUnitInactiveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServingUnitFoodMismatchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (CanonicalFoodLoggingError, ServingUnitLoggingError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        **logged_entry,
    }
