from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.user_state_service import build_user_health_state
from services.workout_plan_persistence_service import (
    WorkoutPlanInvalidStatusError,
    WorkoutPlanNotFoundError,
    WorkoutPlanValidationError,
    complete_workout_plan,
    get_execution_state,
    log_actual_set,
    select_current_workout_plan,
    start_selected_workout_plan,
)
from services.workout_plan_service import (
    build_approved_workout_plan,
    build_workout_context,
    render_approved_workout_plan,
)

router = APIRouter()


class ActualSetPayload(BaseModel):
    planned_workout_exercise_id: int | None = None
    exercise_name: str | None = None
    set_number: int | None = None
    actual_reps: int | None = None
    actual_weight: float | None = None
    actual_rir: int | None = None
    completed: bool = True
    skipped: bool = False
    substitution_for_planned_exercise_id: int | None = None
    notes: str | None = None


@router.get("/workout-plans/preview/{user_id}")
def workout_plan_preview(user_id: int):
    health_state = build_user_health_state(user_id)
    context = build_workout_context(health_state)
    approved_plan = build_approved_workout_plan(health_state)

    return {
        "success": True,
        "user_id": user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "training_constraints": asdict(context.training_constraints),
        "workout_constraints": asdict(context.workout_constraints),
        "approved_workout_plan": asdict(approved_plan),
        "rendered_workout_plan": render_approved_workout_plan(approved_plan),
    }


@router.post("/workout-plans/{user_id}/select")
def select_workout_plan(user_id: int):
    selected = select_current_workout_plan(user_id)
    workout_plan_instance = selected["workout_plan_instance"]
    execution_session = selected["execution_session"]
    approved_plan = selected["approved_workout_plan"]

    return {
        "success": True,
        "user_id": user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "workout_plan_instance": asdict(workout_plan_instance),
        "planned_exercises": [
            asdict(exercise) for exercise in selected["planned_exercises"]
        ],
        "execution_session": asdict(execution_session),
        "approved_workout_plan": asdict(approved_plan),
    }


@router.post("/workout-plans/{plan_instance_id}/start")
def start_workout_plan(plan_instance_id: int):
    try:
        started = start_selected_workout_plan(plan_instance_id)
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkoutPlanInvalidStatusError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    workout_plan_instance = started["workout_plan_instance"]
    execution_session = started["execution_session"]
    approved_plan = started["approved_workout_plan"]

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "user_id": workout_plan_instance.user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "workout_plan_instance": asdict(workout_plan_instance),
        "planned_exercises": [
            asdict(exercise) for exercise in started["planned_exercises"]
        ],
        "execution_session": asdict(execution_session),
        "approved_workout_plan": asdict(approved_plan),
    }


@router.get("/workout-plans/{plan_instance_id}/execution")
def workout_plan_execution_state(plan_instance_id: int):
    try:
        execution_state = get_execution_state(plan_instance_id)
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkoutPlanInvalidStatusError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    workout_plan_instance = execution_state["workout_plan_instance"]
    approved_plan = execution_state["approved_workout_plan"]

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "user_id": workout_plan_instance.user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "workout_plan_instance": asdict(workout_plan_instance),
        "execution_session": asdict(execution_state["execution_session"]),
        "planned_exercises": [
            asdict(exercise) for exercise in execution_state["planned_exercises"]
        ],
        "actual_sets": [
            asdict(actual_set) for actual_set in execution_state["actual_sets"]
        ],
        "approved_workout_plan": asdict(approved_plan),
    }


@router.post("/workout-plans/{plan_instance_id}/actual-sets")
def create_workout_plan_actual_set(
    plan_instance_id: int,
    payload: ActualSetPayload,
):
    try:
        result = log_actual_set(
            plan_instance_id,
            payload.model_dump(exclude_none=True),
        )
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (WorkoutPlanInvalidStatusError, WorkoutPlanValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    execution_state = result["execution_state"]

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "actual_set": asdict(result["actual_set"]),
        "workout_plan_instance": asdict(execution_state["workout_plan_instance"]),
        "execution_session": asdict(execution_state["execution_session"]),
        "actual_sets": [
            asdict(actual_set) for actual_set in execution_state["actual_sets"]
        ],
    }


@router.post("/workout-plans/{plan_instance_id}/complete")
def complete_workout_plan_execution(plan_instance_id: int):
    try:
        result = complete_workout_plan(plan_instance_id)
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkoutPlanInvalidStatusError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "workout_plan_instance": asdict(result["workout_plan_instance"]),
        "execution_session": asdict(result["execution_session"]),
        "planned_vs_actual_summary": asdict(result["planned_vs_actual_summary"]),
    }
