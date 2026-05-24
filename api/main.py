# =====================================
# Imports
# =====================================

from fastapi import FastAPI

from api.routes.nutrition import router as nutrition_router
from api.routes.recommendations import router as recommendation_router
from api.routes.recovery import router as recovery_router
from api.routes.reports import router as report_router
from api.routes.workouts import router as workout_router

# =====================================
# App Initialization
# =====================================

app = FastAPI()
app.include_router(workout_router)
app.include_router(report_router)
app.include_router(recovery_router)
app.include_router(nutrition_router)
app.include_router(recommendation_router)


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
