from dataclasses import asdict

from fastapi import APIRouter

from services.nutrition_target_service import nutrition_targets_to_user_dict
from services.recommendation_engine_service import (
    build_approved_action_plan,
    build_recommendation_context,
    render_approved_action_plan,
)
from services.user_state_service import build_user_health_state

router = APIRouter()


@router.get("/recommendations/daily/{user_id}")
def daily_recommendation(user_id: int):
    health_state = build_user_health_state(user_id)
    context = build_recommendation_context(health_state)
    approved_plan = build_approved_action_plan(health_state)

    return {
        "success": True,
        "user_id": user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "nutrition_targets": nutrition_targets_to_user_dict(context.nutrition_targets),
        "training_constraints": asdict(context.training_constraints),
        "approved_action_plan": asdict(approved_plan),
        "rendered_recommendation": render_approved_action_plan(approved_plan),
    }
