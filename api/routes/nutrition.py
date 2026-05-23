# =====================================
# Imports
# =====================================

from fastapi import APIRouter
from pydantic import BaseModel

from services.nutrition_service import (
    add_food_entry,
    get_daily_nutrition,
    search_foods,
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
