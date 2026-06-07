from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date as date_cls
from typing import Any

from models.ai_nutrition_explanation_models import (
    ApprovedNutritionExplanation,
    CandidateNutritionExplanation,
    NutritionExplanationContext,
)
from services.ai_nutrition_explanation_validation_service import (
    approve_nutrition_explanation_candidate,
    build_deterministic_fallback_nutrition_explanation,
    validate_approved_nutrition_explanation,
)
from services.nutrition_food_suggestion_service import (
    build_approved_nutrition_food_suggestions,
)
from services.nutrition_target_calibration_service import (
    build_nutrition_target_calibration_result,
)
from services.nutrition_target_formula_service import (
    build_nutrition_target_formula_inputs,
    calculate_nutrition_target_formula,
)
from services.nutrition_target_formula_validation_service import (
    approve_validated_macro_targets,
)
from services.nutrition_target_vs_actual_service import (
    build_approved_nutrition_guidance,
    build_target_vs_actual_nutrition_summary,
)
from services.nutrition_trend_service import build_nutrition_trend_window
from services.user_service import get_user_profile
from services.user_state_service import build_user_health_state

_CONTEXT_REASON_CODE = "approved_nutrition_explanation_context_built"
_FALLBACK_REASON_CODE = "deterministic_nutrition_explanation_service"
_CONTEXT_LIMITATION = (
    "Nutrition explanation is limited to approved backend nutrition context."
)
_CONFIDENCE_RANK = {"Limited": 0, "Low": 1, "Moderate": 2, "High": 3}


def build_nutrition_explanation_context(
    user_id: int,
    explanation_date: str | None = None,
    *,
    approved_macro_targets: Any | None = None,
    target_vs_actual_summary: Any | None = None,
    approved_nutrition_guidance: Any | None = None,
    approved_food_suggestions: Any | None = None,
    trend_window: Any | None = None,
    calibration_result: Any | None = None,
) -> NutritionExplanationContext:
    """Build approved deterministic context for a nutrition explanation.

    This service composes existing backend-approved nutrition services only. It does
    not call AI providers, infer missing facts, invent food suggestions, mutate
    targets, or apply calibration results.
    """

    resolved_date = explanation_date or date_cls.today().isoformat()

    target_summary = (
        target_vs_actual_summary
        or build_target_vs_actual_nutrition_summary(
            user_id,
            resolved_date,
        )
    )
    guidance = approved_nutrition_guidance or build_approved_nutrition_guidance(
        target_summary
    )
    food_suggestions = (
        approved_food_suggestions
        or build_approved_nutrition_food_suggestions(
            user_id,
            resolved_date,
            target_vs_actual_summary=target_summary,
        )
    )
    trend = trend_window or build_nutrition_trend_window(
        user_id,
        end_date=resolved_date,
        window_days=28,
    )
    calibration = calibration_result or build_nutrition_target_calibration_result(
        user_id,
        calibration_date=resolved_date,
        window_days=28,
        trend_window=trend,
    )
    macro_targets = approved_macro_targets or _build_approved_macro_targets(
        user_id=user_id,
        calculation_date=resolved_date,
    )

    approved_macro_targets_payload = _approved_macro_targets_projection(macro_targets)
    target_vs_actual_payload = _target_vs_actual_projection(target_summary)
    guidance_payload = _to_public_dict(guidance)
    food_suggestions_payload = _food_suggestions_projection(food_suggestions)
    trend_payload = _trend_window_projection(trend)
    calibration_payload = _calibration_projection(calibration)

    confidence = _minimum_confidence(
        _payload_confidence(approved_macro_targets_payload),
        _payload_confidence(target_vs_actual_payload),
        _payload_confidence(guidance_payload),
        _payload_confidence(food_suggestions_payload),
        _payload_confidence(trend_payload),
        _payload_confidence(calibration_payload),
    )
    reason_codes = _unique(
        [
            _CONTEXT_REASON_CODE,
            *_payload_list(approved_macro_targets_payload, "reason_codes"),
            *_payload_list(target_vs_actual_payload, "reason_codes"),
            *_payload_list(guidance_payload, "reason_codes"),
            *_payload_list(food_suggestions_payload, "reason_codes"),
            *_payload_list(trend_payload, "reason_codes"),
            *_payload_list(calibration_payload, "reason_codes"),
        ]
    )
    limitations = _unique(
        [
            *_payload_list(approved_macro_targets_payload, "limitations"),
            *_payload_list(target_vs_actual_payload, "limitations"),
            *_payload_list(guidance_payload, "limitations"),
            *_payload_list(food_suggestions_payload, "limitations"),
            *_payload_list(trend_payload, "limitations"),
            *_payload_list(calibration_payload, "limitations"),
        ]
    )

    if confidence in {"Limited", "Low"} and not limitations:
        limitations.append(_CONTEXT_LIMITATION)

    return NutritionExplanationContext(
        user_id=user_id,
        explanation_date=resolved_date,
        approved_macro_targets=approved_macro_targets_payload,
        target_vs_actual_summary=target_vs_actual_payload,
        approved_nutrition_guidance=guidance_payload,
        approved_food_suggestions=food_suggestions_payload,
        trend_summary=trend_payload,
        calibration_summary=calibration_payload,
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=limitations,
        display_flags=_payload_mapping(approved_macro_targets_payload, "display_flags"),
    )


def build_deterministic_nutrition_explanation_candidate(
    context: NutritionExplanationContext,
) -> CandidateNutritionExplanation:
    """Build deterministic candidate copy from approved context only.

    The candidate contains no provider-generated facts and intentionally avoids
    specific foods, serving amounts, and macro numbers. It can be used as a stable
    fallback candidate or as a baseline for future provider validation tests.
    """

    return CandidateNutritionExplanation(
        explanation_summary=_candidate_summary(context),
        macro_context=_candidate_macro_context(context),
        food_suggestion_context=_candidate_food_suggestion_context(context),
        trend_context=_candidate_trend_context(context),
        calibration_context=_candidate_calibration_context(context),
        limitations_context=_candidate_limitations_context(context),
        confidence=context.confidence,
        reason_codes=[_FALLBACK_REASON_CODE],
    )


def build_approved_nutrition_explanation(
    user_id: int,
    explanation_date: str | None = None,
    *,
    context: NutritionExplanationContext | None = None,
) -> ApprovedNutritionExplanation:
    """Return a validated deterministic ApprovedNutritionExplanation.

    This service does not call CrewAI, Ollama, external AI providers, RAG, or any
    runtime provider. It builds/uses approved backend context and returns a
    validator-approved deterministic fallback explanation.
    """

    resolved_context = context or build_nutrition_explanation_context(
        user_id,
        explanation_date,
    )
    candidate = build_deterministic_nutrition_explanation_candidate(resolved_context)

    try:
        approved = approve_nutrition_explanation_candidate(resolved_context, candidate)
    except ValueError:
        approved = build_deterministic_fallback_nutrition_explanation(resolved_context)

    if approved.source == "ai_validated":
        approved = ApprovedNutritionExplanation(
            user_id=approved.user_id,
            explanation_date=approved.explanation_date,
            explanation_summary=approved.explanation_summary,
            macro_context=approved.macro_context,
            food_suggestion_context=approved.food_suggestion_context,
            trend_context=approved.trend_context,
            calibration_context=approved.calibration_context,
            limitations_context=approved.limitations_context,
            confidence=approved.confidence,
            reason_codes=_unique([*approved.reason_codes, _FALLBACK_REASON_CODE]),
            limitations=approved.limitations,
            source="deterministic_fallback",
        )

    return validate_approved_nutrition_explanation(approved)


def _build_approved_macro_targets(*, user_id: int, calculation_date: str) -> Any:
    user_profile = get_user_profile(user_id)
    if not user_profile:
        raise ValueError(f"User with id {user_id} was not found.")
    health_state = build_user_health_state(user_id)
    inputs = build_nutrition_target_formula_inputs(
        health_state,
        calculation_date=calculation_date,
        sex=_row_value(user_profile, "gender"),
        input_source_metadata={"consumer": "ai_nutrition_explanation_service"},
    )
    formula_result = calculate_nutrition_target_formula(inputs)
    return approve_validated_macro_targets(formula_result)


def _approved_macro_targets_projection(approved_targets: Any) -> dict[str, Any]:
    payload = _to_public_dict(approved_targets)
    if not payload:
        return {}
    return {
        "user_id": payload.get("user_id"),
        "calculation_date": payload.get("calculation_date"),
        "confidence": payload.get("confidence"),
        "display_flags": payload.get("display_flags", {}),
        "calorie_target": _target_projection(payload.get("calorie_target")),
        "protein_target_g": _target_projection(payload.get("protein_target_g")),
        "carbohydrate_target_g": _target_projection(
            payload.get("carbohydrate_target_g")
        ),
        "fat_target_g": _target_projection(payload.get("fat_target_g")),
        "formula_metadata": _formula_metadata_projection(
            payload.get("formula_metadata")
        ),
        "reason_codes": payload.get("reason_codes", []),
        "limitations": payload.get("limitations", []),
    }


def _target_projection(target: Any) -> dict[str, Any] | None:
    if not isinstance(target, dict):
        return None
    return {
        "target_type": target.get("target_type"),
        "value": target.get("value"),
        "min_value": target.get("min_value"),
        "max_value": target.get("max_value"),
        "display_value": target.get("display_value"),
        "unit": target.get("unit"),
        "confidence": target.get("confidence"),
        "display_allowed": target.get("display_allowed"),
        "reason_codes": target.get("reason_codes", []),
        "limitations": target.get("limitations", []),
    }


def _formula_metadata_projection(metadata: Any) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    return {
        "formula_name": metadata.get("formula_name"),
        "formula_version": metadata.get("formula_version"),
        "calculation_date": metadata.get("calculation_date"),
        "target_basis": metadata.get("target_basis"),
        "reason_codes": metadata.get("reason_codes", []),
        "limitations": metadata.get("limitations", []),
    }


def _target_vs_actual_projection(summary: Any) -> dict[str, Any]:
    payload = _to_public_dict(summary)
    if not payload:
        return {}
    actuals = payload.get("nutrition_actuals") or {}
    logging_summary = payload.get("logging_summary") or {}
    comparisons = payload.get("comparisons") or {}
    return {
        "user_id": payload.get("user_id"),
        "date": payload.get("date"),
        "logging_completeness": payload.get("logging_completeness"),
        "confidence": payload.get("confidence"),
        "nutrition_actuals": {
            "logged_calories": actuals.get("logged_calories"),
            "logged_protein": actuals.get("logged_protein"),
            "logged_carbs": actuals.get("logged_carbs"),
            "logged_fat": actuals.get("logged_fat"),
            "logged_meal_count": actuals.get("logged_meal_count"),
            "entry_count": actuals.get("entry_count"),
        },
        "logging_summary": {
            "logging_completeness": logging_summary.get("logging_completeness"),
            "confidence": logging_summary.get("confidence"),
            "logged_meal_count": logging_summary.get("logged_meal_count"),
            "entry_count": logging_summary.get("entry_count"),
            "missing_nutrient_fields": logging_summary.get(
                "missing_nutrient_fields", []
            ),
            "reason_codes": logging_summary.get("reason_codes", []),
            "limitations": logging_summary.get("limitations", []),
        },
        "comparisons": {
            macro: _comparison_projection(comparison)
            for macro, comparison in comparisons.items()
            if macro in {"calories", "protein", "carbs", "fat"}
        },
        "reason_codes": payload.get("reason_codes", []),
        "limitations": payload.get("limitations", []),
    }


def _comparison_projection(comparison: Any) -> dict[str, Any]:
    if not isinstance(comparison, dict):
        return {}
    return {
        "nutrient": comparison.get("nutrient"),
        "actual": comparison.get("actual"),
        "target_min": comparison.get("target_min"),
        "target_max": comparison.get("target_max"),
        "target_status": comparison.get("target_status"),
        "comparison_available": comparison.get("comparison_available"),
        "confidence": comparison.get("confidence"),
        "reason_codes": comparison.get("reason_codes", []),
        "limitations": comparison.get("limitations", []),
    }


def _food_suggestions_projection(food_suggestions: Any) -> dict[str, Any]:
    payload = _to_public_dict(food_suggestions)
    if not payload:
        return {}
    suggestions = payload.get("suggestions") or []
    macro_gaps = payload.get("macro_gaps") or []
    return {
        "user_id": payload.get("user_id"),
        "suggestion_date": payload.get("suggestion_date"),
        "primary_gap": payload.get("primary_gap"),
        "macro_gaps": [
            {
                "macro_name": gap.get("macro_name"),
                "target_status": gap.get("target_status"),
                "display_allowed": gap.get("display_allowed"),
                "confidence": gap.get("confidence"),
                "reason_codes": gap.get("reason_codes", []),
                "limitations": gap.get("limitations", []),
            }
            for gap in macro_gaps
            if isinstance(gap, dict)
        ],
        "suggestions": [
            {
                "canonical_food_id": suggestion.get("canonical_food_id"),
                "display_name": suggestion.get("display_name"),
                "suggested_grams": suggestion.get("suggested_grams"),
                "estimated_calories": suggestion.get("estimated_calories"),
                "estimated_protein_g": suggestion.get("estimated_protein_g"),
                "estimated_carbohydrate_g": suggestion.get("estimated_carbohydrate_g"),
                "estimated_fat_g": suggestion.get("estimated_fat_g"),
                "macro_gap_addressed": suggestion.get("macro_gap_addressed"),
                "confidence": suggestion.get("confidence"),
                "reason_codes": suggestion.get("reason_codes", []),
                "limitations": suggestion.get("limitations", []),
            }
            for suggestion in suggestions
            if isinstance(suggestion, dict)
        ],
        "confidence": payload.get("confidence"),
        "reason_codes": payload.get("reason_codes", []),
        "limitations": payload.get("limitations", []),
    }


def _trend_window_projection(trend_window: Any) -> dict[str, Any]:
    payload = _to_public_dict(trend_window)
    if not payload:
        return {}
    intake_summary = payload.get("intake_trend_summary") or {}
    bodyweight_summary = payload.get("bodyweight_trend_summary") or {}
    readiness = payload.get("calibration_readiness") or {}
    return {
        "user_id": payload.get("user_id"),
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date"),
        "window_days": payload.get("window_days"),
        "logged_day_count": payload.get("logged_day_count"),
        "complete_logging_day_count": payload.get("complete_logging_day_count"),
        "partial_logging_day_count": payload.get("partial_logging_day_count"),
        "no_log_day_count": payload.get("no_log_day_count"),
        "intake_trend_summary": {
            "average_calories": intake_summary.get("average_calories"),
            "average_protein_g": intake_summary.get("average_protein_g"),
            "average_carbohydrate_g": intake_summary.get("average_carbohydrate_g"),
            "average_fat_g": intake_summary.get("average_fat_g"),
            "complete_logging_rate": intake_summary.get("complete_logging_rate"),
            "logging_consistency_status": intake_summary.get(
                "logging_consistency_status"
            ),
            "confidence": intake_summary.get("confidence"),
            "reason_codes": intake_summary.get("reason_codes", []),
            "limitations": intake_summary.get("limitations", []),
        },
        "bodyweight_trend_summary": {
            "weigh_in_count": bodyweight_summary.get("weigh_in_count"),
            "trend_direction": bodyweight_summary.get("trend_direction"),
            "weekly_rate_lb": bodyweight_summary.get("weekly_rate_lb"),
            "confidence": bodyweight_summary.get("confidence"),
            "reason_codes": bodyweight_summary.get("reason_codes", []),
            "limitations": bodyweight_summary.get("limitations", []),
        },
        "calibration_readiness": {
            "calibration_allowed": readiness.get("calibration_allowed"),
            "readiness_level": readiness.get("readiness_level"),
            "minimum_window_met": readiness.get("minimum_window_met"),
            "preferred_window_met": readiness.get("preferred_window_met"),
            "logging_quality_met": readiness.get("logging_quality_met"),
            "bodyweight_trend_available": readiness.get("bodyweight_trend_available"),
            "goal_context_available": readiness.get("goal_context_available"),
            "training_context_available": readiness.get("training_context_available"),
            "reason_codes": readiness.get("reason_codes", []),
            "limitations": readiness.get("limitations", []),
        },
        "confidence": payload.get("confidence"),
        "reason_codes": payload.get("reason_codes", []),
        "limitations": payload.get("limitations", []),
    }


def _calibration_projection(calibration_result: Any) -> dict[str, Any]:
    payload = _to_public_dict(calibration_result)
    if not payload:
        return {}
    return {
        "user_id": payload.get("user_id"),
        "calibration_date": payload.get("calibration_date"),
        "window_days": payload.get("window_days"),
        "calibration_allowed": payload.get("calibration_allowed"),
        "readiness_level": payload.get("readiness_level"),
        "recommended_action": payload.get("recommended_action"),
        "calibrated_targets": None,
        "confidence": payload.get("confidence"),
        "reason_codes": payload.get("reason_codes", []),
        "limitations": payload.get("limitations", []),
        "metadata": _calibration_metadata_projection(payload.get("metadata")),
    }


def _calibration_metadata_projection(metadata: Any) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    return {
        "service_name": metadata.get("service_name"),
        "service_version": metadata.get("service_version"),
        "inputs_used": metadata.get("inputs_used", []),
        "reason_codes": metadata.get("reason_codes", []),
        "limitations": metadata.get("limitations", []),
    }


def _candidate_summary(context: NutritionExplanationContext) -> str:
    if context.confidence in {"Moderate", "High"}:
        return "Approved nutrition context is available for this date."
    return "Nutrition explanation is limited because the approved context is limited for this date."


def _candidate_macro_context(context: NutritionExplanationContext) -> str | None:
    comparisons = context.target_vs_actual_summary.get("comparisons")
    if isinstance(comparisons, dict):
        protein = comparisons.get("protein")
        if isinstance(protein, dict) and protein.get("target_status") == "below_target":
            return "Based on today’s logged meals, protein is below target."
        return "Target-vs-Actual details are based on approved backend calculations."
    if context.approved_macro_targets:
        return "Targets are still formula-derived."
    return None


def _candidate_food_suggestion_context(
    context: NutritionExplanationContext,
) -> str | None:
    suggestions = context.approved_food_suggestions.get("suggestions")
    if isinstance(suggestions, list) and suggestions:
        return "The Nutrition tab has approved food suggestions that may help close the gap."
    reason_codes = context.approved_food_suggestions.get("reason_codes")
    if isinstance(reason_codes, list) and reason_codes:
        return "Food suggestions are limited by approved backend context for this date."
    return None


def _candidate_trend_context(context: NutritionExplanationContext) -> str | None:
    if context.trend_summary:
        return "Trend evidence is summarized from deterministic logged data."
    return None


def _candidate_calibration_context(context: NutritionExplanationContext) -> str | None:
    if context.calibration_summary:
        readiness = context.calibration_summary.get("readiness_level")
        if readiness in {"not_ready", "early_signal"}:
            return (
                "Targets are still formula-derived; more trend evidence may be needed."
            )
        return (
            "Targets are still formula-derived; calibration readiness is context only."
        )
    return None


def _candidate_limitations_context(context: NutritionExplanationContext) -> str | None:
    if context.limitations:
        return "Some explanation details are limited by approved context limitations."
    if context.confidence in {"Limited", "Low"}:
        return "Use the Nutrition tab for approved target, logging, trend, and calibration detail."
    return None


def _to_public_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    raise ValueError(
        f"Unsupported nutrition explanation context payload: {type(value)}"
    )


def _payload_confidence(payload: dict[str, Any]) -> str:
    confidence = payload.get("confidence")
    if confidence in _CONFIDENCE_RANK:
        return str(confidence)
    return "Limited" if payload else "High"


def _payload_list(payload: dict[str, Any], key: str) -> list[str]:
    values = payload.get(key)
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str) and value]


def _payload_mapping(payload: dict[str, Any], key: str) -> dict[str, bool]:
    value = payload.get(key)
    if not isinstance(value, dict):
        return {}
    return {
        str(map_key): map_value
        for map_key, map_value in value.items()
        if isinstance(map_value, bool)
    }


def _minimum_confidence(*values: str) -> str:
    valid = [value for value in values if value in _CONFIDENCE_RANK]
    if not valid:
        return "Limited"
    return min(valid, key=lambda value: _CONFIDENCE_RANK[value])


def _row_value(row: Any, field_name: str) -> Any:
    if row is None:
        return None
    if hasattr(row, "keys") and field_name in row.keys():
        return row[field_name]
    if isinstance(row, dict):
        return row.get(field_name)
    return getattr(row, field_name, None)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
