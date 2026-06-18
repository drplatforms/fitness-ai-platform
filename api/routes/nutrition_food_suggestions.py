from __future__ import annotations

from datetime import date as date_cls
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from models.nutrition_food_suggestion_models import ApprovedNutritionFoodSuggestions
from services.nutrition_food_suggestion_service import (
    build_approved_nutrition_food_suggestions,
)
from services.user_service import get_user_profile

router = APIRouter()


@router.get("/nutrition/{user_id}/food-suggestions")
def nutrition_food_suggestions_endpoint(
    user_id: int,
    suggestion_date: str | None = Query(default=None, alias="date"),
):
    """Return public-safe deterministic canonical food suggestions."""

    resolved_date = _resolve_suggestion_date(suggestion_date)
    _get_user_profile_or_404(user_id)

    try:
        approved_suggestions = build_approved_nutrition_food_suggestions(
            user_id,
            resolved_date,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message.lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=(
                "Nutrition food suggestion validation failed."
                if status_code == 400
                else "User not found."
            ),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive public-safe boundary
        raise HTTPException(
            status_code=500,
            detail="Nutrition food suggestion generation failed.",
        ) from exc

    return _build_public_response(approved_suggestions)


def _resolve_suggestion_date(suggestion_date: str | None) -> str:
    if suggestion_date is None:
        return date_cls.today().isoformat()

    try:
        return date_cls.fromisoformat(suggestion_date).isoformat()
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
    approved_suggestions: ApprovedNutritionFoodSuggestions,
) -> dict[str, Any]:
    return {
        "success": True,
        "user_id": approved_suggestions.user_id,
        "suggestion_date": approved_suggestions.suggestion_date,
        "primary_gap": approved_suggestions.primary_gap,
        "macro_gaps": [
            macro_gap.to_dict() for macro_gap in approved_suggestions.macro_gaps
        ],
        "suggestions": [
            suggestion.to_dict() for suggestion in approved_suggestions.suggestions
        ],
        "confidence": approved_suggestions.confidence,
        "reason_codes": list(approved_suggestions.reason_codes),
        "limitations": list(approved_suggestions.limitations),
    }
