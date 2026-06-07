# =====================================
# Imports
# =====================================

from fastapi import FastAPI

from api.routes.daily_coach import router as daily_coach_router
from api.routes.equipment_profiles import router as equipment_profile_router
from api.routes.food_canonical_search import router as food_canonical_search_router
from api.routes.nutrition import router as nutrition_router
from api.routes.nutrition_food_suggestions import (
    router as nutrition_food_suggestion_router,
)
from api.routes.nutrition_target_calibration import (
    router as nutrition_target_calibration_router,
)
from api.routes.nutrition_target_formula import (
    router as nutrition_target_formula_router,
)
from api.routes.nutrition_target_vs_actual import (
    router as nutrition_target_vs_actual_router,
)
from api.routes.nutrition_trend import router as nutrition_trend_router
from api.routes.recommendations import router as recommendation_router
from api.routes.recovery import router as recovery_router
from api.routes.reports import router as report_router
from api.routes.workout_plans import router as workout_plan_router
from api.routes.workouts import router as workout_router

# =====================================
# App Initialization
# =====================================

app = FastAPI()
app.include_router(workout_router)
app.include_router(daily_coach_router)
app.include_router(equipment_profile_router)
app.include_router(food_canonical_search_router)
app.include_router(report_router)
app.include_router(recovery_router)
app.include_router(nutrition_target_vs_actual_router)
app.include_router(nutrition_target_formula_router)
app.include_router(nutrition_target_calibration_router)
app.include_router(nutrition_food_suggestion_router)
app.include_router(nutrition_trend_router)
app.include_router(nutrition_router)
app.include_router(recommendation_router)
app.include_router(workout_plan_router)


# =====================================
# Root Endpoint
# =====================================


@app.get("/")
def root():
    return {"message": "Fitness AI API is running"}


# =====================================
# Health Check Endpoint
# =====================================


@app.get("/health")
def health_check():
    return {"status": "healthy"}
