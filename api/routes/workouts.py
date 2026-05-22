# =====================================
# Imports
# =====================================

from fastapi import APIRouter

from api.models.workout_models import WorkoutRequest
from services.workout_service import (
    add_workout_set,
    create_workout_session,
    get_all_exercises,
    get_recent_workouts,
)

# =====================================
# Router Initialization
# =====================================

router = APIRouter()


# =====================================
# Recent Workouts Endpoint
# =====================================


@router.get("/workouts/{user_id}")
def recent_workouts(user_id: int):
    workouts = get_recent_workouts(user_id)

    return {"success": True, "workouts": workouts}


# =====================================
# Get Exercises Endpoint
# =====================================


@router.get("/exercises")
def get_exercises():
    exercises = get_all_exercises()

    return {
        "success": True,
        "exercises": exercises,
    }


# =====================================
# Create Workout Endpoint
# =====================================


@router.post("/workouts/create")
def create_workout(payload: WorkoutRequest):
    session_id = create_workout_session(
        user_id=payload.user_id,
        workout_name=payload.workout_name,
        duration_minutes=payload.duration_minutes,
        notes=payload.notes,
    )

    for set_data in payload.sets:
        add_workout_set(
            workout_session_id=session_id,
            exercise_id=set_data.exercise_id,
            set_number=set_data.set_number,
            reps=set_data.reps,
            weight=set_data.weight,
            rir=set_data.rir,
        )

    return {"success": True, "session_id": session_id}
