from __future__ import annotations

from datetime import date as date_cls

from fastapi import APIRouter, HTTPException, Query

from services.nutrition_target_vs_actual_service import (
    build_approved_nutrition_guidance,
    build_target_vs_actual_nutrition_summary,
    validate_target_vs_actual_nutrition_summary,
)

router = APIRouter()


@router.get("/nutrition/{user_id}/target-vs-actual")
def nutrition_target_vs_actual_endpoint(
    user_id: int,
    target_date: str | None = Query(default=None, alias="date"),
):
    """Return public-safe nutrition target-vs-actual summary and guidance."""

    if target_date is None:
        resolved_date = date_cls.today().isoformat()
    else:
        try:
            resolved_date = date_cls.fromisoformat(target_date).isoformat()
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="date must use YYYY-MM-DD format.",
            ) from exc

    try:
        summary = build_target_vs_actual_nutrition_summary(user_id, resolved_date)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status_code, detail=message) from exc

    guidance = build_approved_nutrition_guidance(summary)
    validation_errors = validate_target_vs_actual_nutrition_summary(summary, guidance)
    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail="Nutrition target-vs-actual validation failed.",
        )

    return {
        "success": True,
        "user_id": user_id,
        "date": resolved_date,
        "nutrition_actuals": summary.nutrition_actuals.to_dict(),
        "logging_summary": summary.logging_summary.to_dict(),
        "target_vs_actual_summary": summary.to_dict(),
        "approved_nutrition_guidance": guidance.to_dict(),
        "logging_completeness": summary.logging_completeness,
        "confidence": summary.confidence,
        "reason_codes": list(summary.reason_codes),
        "limitations": list(summary.limitations),
    }
