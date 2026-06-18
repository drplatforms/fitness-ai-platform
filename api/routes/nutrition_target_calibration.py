from __future__ import annotations

from datetime import date as date_cls
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from services.nutrition_target_calibration_service import (
    NutritionTargetCalibrationResult,
    build_nutrition_target_calibration_result,
)
from services.user_service import get_user_profile

router = APIRouter()

_ALLOWED_WINDOW_DAYS = {14, 28}


@router.get("/nutrition/{user_id}/target-calibration")
def nutrition_target_calibration_endpoint(
    user_id: int,
    end_date: str | None = Query(default=None),
    window_days: int = Query(default=28),
):
    """Return public-safe deterministic nutrition target calibration context."""

    resolved_end_date = _resolve_end_date(end_date)
    resolved_window_days = _resolve_window_days(window_days)
    _get_user_profile_or_404(user_id)

    try:
        calibration_result = build_nutrition_target_calibration_result(
            user_id=user_id,
            calibration_date=resolved_end_date,
            window_days=resolved_window_days,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message.lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=(
                "Nutrition target calibration validation failed."
                if status_code == 400
                else "User not found."
            ),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive public-safe boundary
        raise HTTPException(
            status_code=500,
            detail="Nutrition target calibration generation failed.",
        ) from exc

    return _build_public_response(calibration_result)


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


def _build_public_response(
    calibration_result: NutritionTargetCalibrationResult,
) -> dict[str, Any]:
    """Build public-safe calibration response without raw trend/debug internals."""

    return {
        "success": True,
        "user_id": calibration_result.user_id,
        "calibration_date": calibration_result.calibration_date,
        "window_days": calibration_result.window_days,
        "calibration_allowed": calibration_result.calibration_allowed,
        "readiness_level": calibration_result.readiness_level,
        "recommended_action": calibration_result.recommended_action,
        "calibrated_targets": None,
        "confidence": calibration_result.confidence,
        "reason_codes": list(calibration_result.reason_codes),
        "limitations": list(calibration_result.limitations),
        "metadata": calibration_result.metadata.to_dict(),
    }
