from fastapi import APIRouter, HTTPException

from services.daily_coach_synthesis_service import (
    DailyCoachSynthesisValidationError,
    build_daily_coach_synthesis,
)
from services.daily_next_action_service import (
    DailyNextActionValidationError,
    build_daily_next_action,
)

router = APIRouter()


@router.get("/daily-coach/{user_id}/synthesis")
def daily_coach_synthesis(user_id: int):
    try:
        synthesis = build_daily_coach_synthesis(user_id)
    except DailyCoachSynthesisValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        "synthesis_date": synthesis.synthesis_date,
        "scenario": synthesis.scenario,
        "confidence": synthesis.confidence,
        "daily_coach_synthesis": synthesis.to_dict(),
    }


@router.get("/daily-coach/{user_id}/next-action")
def daily_next_action(user_id: int):
    try:
        action = build_daily_next_action(user_id)
    except DailyNextActionValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        "daily_next_action": action.to_dict(),
    }
