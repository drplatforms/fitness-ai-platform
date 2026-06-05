from __future__ import annotations

from datetime import date as date_cls
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from models.nutrition_target_formula_models import (
    ApprovedMacroTargets,
    MacroTargetResult,
)
from services.nutrition_target_formula_service import (
    build_nutrition_target_formula_inputs,
    calculate_nutrition_target_formula,
)
from services.nutrition_target_formula_validation_service import (
    approve_validated_macro_targets,
)
from services.user_service import get_user_profile
from services.user_state_service import build_user_health_state

router = APIRouter()


@router.get("/nutrition/{user_id}/targets/formula")
def nutrition_target_formula_endpoint(
    user_id: int,
    target_date: str | None = Query(default=None, alias="date"),
):
    """Return public-safe, validated formula-derived macro targets."""

    resolved_date = _resolve_calculation_date(target_date)
    user_profile = _get_user_profile_or_404(user_id)

    try:
        health_state = build_user_health_state(user_id)
        formula_inputs = build_nutrition_target_formula_inputs(
            health_state,
            calculation_date=resolved_date,
            sex=_profile_value(user_profile, "gender"),
            input_source_metadata={"api_endpoint": "nutrition_target_formula"},
        )
        formula_result = calculate_nutrition_target_formula(formula_inputs)
        approved_targets = approve_validated_macro_targets(formula_result)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Nutrition target formula validation failed.",
        ) from exc

    return _build_public_response(
        user_id=user_id,
        calculation_date=resolved_date,
        approved_targets=approved_targets,
    )


def _resolve_calculation_date(target_date: str | None) -> str:
    if target_date is None:
        return date_cls.today().isoformat()

    try:
        return date_cls.fromisoformat(target_date).isoformat()
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


def _profile_value(user_profile: Any, key: str, default: Any = None) -> Any:
    try:
        return user_profile[key]
    except (KeyError, IndexError, TypeError):
        return default


def _build_public_response(
    *,
    user_id: int,
    calculation_date: str,
    approved_targets: ApprovedMacroTargets,
) -> dict[str, Any]:
    formula_metadata = approved_targets.formula_metadata.to_dict()
    display_flags = dict(approved_targets.display_flags)

    return {
        "success": True,
        "user_id": user_id,
        "calculation_date": calculation_date,
        "approved_macro_targets": {
            "calorie_target": _target_to_public_dict(
                approved_targets.calorie_target,
                display_allowed=display_flags["allow_calorie_targets"],
            ),
            "protein_target_g": _target_to_public_dict(
                approved_targets.protein_target_g,
                display_allowed=display_flags["allow_protein_targets"],
            ),
            "carbohydrate_target_g": _target_to_public_dict(
                approved_targets.carbohydrate_target_g,
                display_allowed=display_flags["allow_carbohydrate_targets"],
            ),
            "fat_target_g": _target_to_public_dict(
                approved_targets.fat_target_g,
                display_allowed=display_flags["allow_fat_targets"],
            ),
        },
        "formula_metadata": formula_metadata,
        "confidence": approved_targets.confidence,
        "display_flags": display_flags,
        "reason_codes": list(approved_targets.reason_codes),
        "limitations": list(approved_targets.limitations),
    }


def _target_to_public_dict(
    target: MacroTargetResult | None,
    *,
    display_allowed: bool,
) -> dict[str, Any] | None:
    if target is None:
        return None

    target_payload = target.to_dict()
    if not display_allowed:
        target_payload["value"] = None
        target_payload["min_value"] = None
        target_payload["max_value"] = None
        target_payload["display_value"] = None
        target_payload["display_allowed"] = False

    return target_payload
