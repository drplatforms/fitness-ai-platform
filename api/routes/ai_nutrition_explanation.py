from __future__ import annotations

from datetime import date as date_cls
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from models.ai_nutrition_explanation_models import (
    ApprovedNutritionExplanation,
    ApprovedNutritionExplanationResult,
)
from services.ai_nutrition_explanation_service import (
    build_configured_approved_nutrition_explanation,
    build_configured_approved_nutrition_explanation_with_metadata,
)
from services.user_service import get_user_profile

router = APIRouter()


@router.get("/nutrition/{user_id}/explanation/preview")
def nutrition_explanation_preview_endpoint(
    user_id: int,
    explanation_date: str | None = Query(default=None, alias="date"),
):
    """Return public-safe deterministic approved nutrition explanation preview."""

    resolved_date = _resolve_explanation_date(explanation_date)
    _get_user_profile_or_404(user_id)

    try:
        approved_explanation = build_configured_approved_nutrition_explanation(
            user_id=user_id,
            explanation_date=resolved_date,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message.lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=(
                "AI nutrition explanation validation failed."
                if status_code == 400
                else "User not found."
            ),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive public-safe boundary
        raise HTTPException(
            status_code=500,
            detail="AI nutrition explanation generation failed.",
        ) from exc

    return _build_public_response(approved_explanation)


@router.get("/nutrition/{user_id}/explanation/debug")
def nutrition_explanation_debug_endpoint(
    user_id: int,
    explanation_date: str | None = Query(default=None, alias="date"),
):
    """Return developer-safe runtime metadata for nutrition explanation generation."""

    resolved_date = _resolve_explanation_date(explanation_date)
    _get_user_profile_or_404(user_id)

    try:
        result = build_configured_approved_nutrition_explanation_with_metadata(
            user_id=user_id,
            explanation_date=resolved_date,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message.lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=(
                "AI nutrition explanation validation failed."
                if status_code == 400
                else "User not found."
            ),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive debug-safe boundary
        raise HTTPException(
            status_code=500,
            detail="AI nutrition explanation generation failed.",
        ) from exc

    return _build_debug_response(result)


def _resolve_explanation_date(explanation_date: str | None) -> str:
    if explanation_date is None:
        return date_cls.today().isoformat()

    try:
        return date_cls.fromisoformat(explanation_date).isoformat()
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="date must use YYYY-MM-DD format.",
        ) from exc


def _get_user_profile_or_404(user_id: int) -> Any:
    user_profile = get_user_profile(user_id)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found.")
    return user_profile


def _build_public_response(
    approved_explanation: ApprovedNutritionExplanation,
) -> dict[str, Any]:
    explanation_payload = _approved_explanation_to_public_dict(approved_explanation)
    return {
        "success": True,
        "user_id": approved_explanation.user_id,
        "explanation_date": approved_explanation.explanation_date,
        "approved_nutrition_explanation": explanation_payload,
        "confidence": approved_explanation.confidence,
        "reason_codes": list(approved_explanation.reason_codes),
        "limitations": list(approved_explanation.limitations),
    }


def _approved_explanation_to_public_dict(
    approved_explanation: ApprovedNutritionExplanation,
) -> dict[str, Any]:
    """Build normal preview payload without debug/provider/runtime internals."""

    return {
        "explanation_summary": approved_explanation.explanation_summary,
        "macro_context": approved_explanation.macro_context,
        "food_suggestion_context": approved_explanation.food_suggestion_context,
        "trend_context": approved_explanation.trend_context,
        "calibration_context": approved_explanation.calibration_context,
        "limitations_context": approved_explanation.limitations_context,
        "confidence": approved_explanation.confidence,
        "reason_codes": list(approved_explanation.reason_codes),
        "limitations": list(approved_explanation.limitations),
    }


def _build_debug_response(
    result: ApprovedNutritionExplanationResult,
) -> dict[str, Any]:
    approved_explanation = result.approved_nutrition_explanation
    return {
        "success": True,
        "user_id": approved_explanation.user_id,
        "explanation_date": approved_explanation.explanation_date,
        "approved_nutrition_explanation": _approved_explanation_to_public_dict(
            approved_explanation
        ),
        "runtime_metadata": result.runtime_metadata.to_debug_dict(),
    }
