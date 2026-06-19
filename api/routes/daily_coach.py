from fastapi import APIRouter, HTTPException

from services.daily_coach_narrative_preview_service import (
    DailyCoachNarrativePreviewError,
    build_daily_coach_narrative_preview,
)
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


@router.get("/daily-coach/{user_id}/narrative-preview/debug")
def daily_coach_narrative_preview_debug(
    user_id: int,
    provider: str = "deterministic",
    model: str | None = None,
    date: str | None = None,
    timeout_seconds: float = 300.0,
):
    """Return a public-safe developer-only Daily Coach Narrative preview.

    This debug path never returns rejected provider text, raw prompts, raw model
    payloads, stack traces, or validation internals. Provider output appears only
    when parsed and validated. Otherwise the deterministic fallback note is used.
    """

    try:
        preview = build_daily_coach_narrative_preview(
            user_id,
            target_date=date,
            provider=provider,
            model_name=model,
            timeout_seconds=timeout_seconds,
        )
    except DailyCoachNarrativePreviewError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "success": True,
        "daily_coach_narrative_preview": preview.to_dict(),
    }
