from __future__ import annotations

from datetime import date as date_cls
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from models.nutrition_trend_models import NutritionTrendWindow
from services.nutrition_trend_service import build_nutrition_trend_window
from services.user_service import get_user_profile

router = APIRouter()

_ALLOWED_WINDOW_DAYS = {14, 28}


@router.get("/nutrition/{user_id}/trend-window")
def nutrition_trend_window_endpoint(
    user_id: int,
    end_date: str | None = Query(default=None),
    window_days: int = Query(default=28),
):
    """Return public-safe deterministic nutrition trend evidence."""

    resolved_end_date = _resolve_end_date(end_date)
    resolved_window_days = _resolve_window_days(window_days)
    _get_user_profile_or_404(user_id)

    try:
        trend_window = build_nutrition_trend_window(
            user_id=user_id,
            end_date=resolved_end_date,
            window_days=resolved_window_days,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message.lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=(
                "Nutrition trend window validation failed."
                if status_code == 400
                else "User not found."
            ),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive public-safe boundary
        raise HTTPException(
            status_code=500,
            detail="Nutrition trend window generation failed.",
        ) from exc

    return _build_public_response(trend_window)


def _resolve_end_date(end_date: str | None) -> str:
    if end_date is None:
        return date_cls.today().isoformat()

    try:
        return date_cls.fromisoformat(end_date).isoformat()
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="end_date must use YYYY-MM-DD format.",
        ) from exc


def _resolve_window_days(window_days: int) -> int:
    if window_days not in _ALLOWED_WINDOW_DAYS:
        raise HTTPException(
            status_code=400,
            detail="window_days must be 14 or 28.",
        )
    return window_days


def _get_user_profile_or_404(user_id: int) -> Any:
    user_profile = get_user_profile(user_id)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found.")
    return user_profile


def _build_public_response(trend_window: NutritionTrendWindow) -> dict[str, Any]:
    """Build public-safe trend response without raw row/debug internals."""

    return {
        "success": True,
        "user_id": trend_window.user_id,
        "start_date": trend_window.start_date,
        "end_date": trend_window.end_date,
        "window_days": trend_window.window_days,
        "logged_day_count": trend_window.logged_day_count,
        "complete_logging_day_count": trend_window.complete_logging_day_count,
        "partial_logging_day_count": trend_window.partial_logging_day_count,
        "no_log_day_count": trend_window.no_log_day_count,
        "intake_trend_summary": trend_window.intake_trend_summary.to_dict(),
        "bodyweight_trend_summary": trend_window.bodyweight_trend_summary.to_dict(),
        "calibration_readiness": trend_window.calibration_readiness.to_dict(),
        "confidence": trend_window.confidence,
        "reason_codes": list(trend_window.reason_codes),
        "limitations": list(trend_window.limitations),
    }
