from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from models.nutrition_target_formula_models import (
    ApprovedMacroTargets,
    MacroTargetResult,
)
from models.nutrition_trend_models import (
    BODYWEIGHT_TREND_UNAVAILABLE,
    CALIBRATION_READINESS_EARLY_SIGNAL,
    CALIBRATION_READINESS_NOT_READY,
    CALIBRATION_READINESS_STRONG,
    CALIBRATION_READINESS_USABLE,
    LOGGING_CONSISTENCY_INSUFFICIENT,
    LOGGING_CONSISTENCY_STRONG,
    LOGGING_CONSISTENCY_USABLE,
    NutritionTrendWindow,
)
from services.nutrition_target_formula_service import (
    build_nutrition_target_formula_inputs,
    calculate_nutrition_target_formula,
)
from services.nutrition_target_formula_validation_service import (
    approve_validated_macro_targets,
)
from services.nutrition_trend_service import build_nutrition_trend_window
from services.user_service import get_user_profile
from services.user_state_service import build_user_health_state

CALIBRATION_CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

RECOMMENDED_ACTION_INSUFFICIENT_DATA = "insufficient_data"
RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS = "keep_current_targets"
RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE = "maintain_broad_range"
RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT = "eligible_for_future_refinement"

RECOMMENDED_ACTION_VALUES = {
    RECOMMENDED_ACTION_INSUFFICIENT_DATA,
    RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS,
    RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE,
    RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT,
}

FORBIDDEN_CALIBRATION_LANGUAGE = {
    "true maintenance is exactly",
    "metabolism is damaged",
    "must cut calories",
    "failed your target",
    "failed your targets",
    "medical treatment",
    "disease treatment",
    "fat-loss guarantee",
    "fat loss guarantee",
    "guaranteed fat loss",
    "eating disorder",
    "aggressive calorie reduction",
    "ai-generated target",
    "ai generated target",
}

READ_ONLY_CALIBRATION_LIMITATION = (
    "Calibration assessment is read-only and does not mutate nutrition targets."
)


@dataclass
class NutritionTargetCalibrationMetadata:
    service_name: str = "deterministic_nutrition_target_calibration"
    service_version: str = "v1"
    generated_at: str = ""
    inputs_used: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_required_text("service_name", self.service_name)
        _validate_required_text("service_version", self.service_version)
        _validate_safe_text_list("inputs_used", self.inputs_used)
        _validate_safe_text_list("assumptions", self.assumptions)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        if self.assumptions and not self.limitations:
            raise ValueError("limitations are required when assumptions are used")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NutritionTargetCalibrationResult:
    user_id: int
    calibration_date: str
    window_days: int
    calibration_allowed: bool
    readiness_level: str
    recommended_action: str
    calibrated_targets: None = None
    confidence: str = "Limited"
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    metadata: NutritionTargetCalibrationMetadata = field(
        default_factory=NutritionTargetCalibrationMetadata
    )

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_required_text("calibration_date", self.calibration_date)
        _validate_positive_int("window_days", self.window_days)
        _validate_readiness_level(self.readiness_level)
        _validate_recommended_action(self.recommended_action)
        _validate_confidence(self.confidence)
        _validate_safe_text_list("reason_codes", self.reason_codes)
        _validate_safe_text_list("limitations", self.limitations)
        if self.calibrated_targets is not None:
            raise ValueError("v1 calibration must not produce target mutation payloads")
        if self.confidence in {"Limited", "Low"} and not (
            self.reason_codes or self.limitations
        ):
            raise ValueError("Limited/Low calibration results require context")
        if self.recommended_action == RECOMMENDED_ACTION_INSUFFICIENT_DATA:
            if self.calibration_allowed:
                raise ValueError("insufficient_data cannot allow calibration")
        if self.recommended_action == RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT:
            if not self.calibration_allowed:
                raise ValueError(
                    "eligible_for_future_refinement requires calibration_allowed"
                )
        if "target_mutation_not_performed" not in self.reason_codes:
            raise ValueError(
                "Calibration result must record target mutation did not occur"
            )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = self.metadata.to_dict()
        return payload


def build_nutrition_target_calibration_result(
    user_id: int,
    *,
    calibration_date: str | None = None,
    window_days: int = 28,
    trend_window: NutritionTrendWindow | None = None,
    approved_targets: ApprovedMacroTargets | None = None,
) -> NutritionTargetCalibrationResult:
    """Build a deterministic, read-only nutrition target calibration assessment.

    The service composes formula-derived targets and NutritionTrendWindow evidence.
    It does not mutate targets, overwrite formula results, infer maintenance calories,
    or modify user profile/activity/goal fields.
    """

    resolved_date = _resolve_date(calibration_date)
    trend = trend_window or build_nutrition_trend_window(
        user_id,
        end_date=resolved_date,
        window_days=window_days,
    )
    targets = approved_targets or _build_formula_targets(
        user_id=user_id,
        calculation_date=resolved_date,
    )
    return assess_nutrition_target_calibration(
        user_id=user_id,
        calibration_date=resolved_date,
        trend_window=trend,
        approved_targets=targets,
    )


def assess_nutrition_target_calibration(
    *,
    user_id: int,
    calibration_date: str,
    trend_window: NutritionTrendWindow,
    approved_targets: ApprovedMacroTargets,
) -> NutritionTargetCalibrationResult:
    _validate_positive_int("user_id", user_id)
    _validate_required_text("calibration_date", calibration_date)
    if not isinstance(trend_window, NutritionTrendWindow):
        raise ValueError("trend_window must be a NutritionTrendWindow")
    if not isinstance(approved_targets, ApprovedMacroTargets):
        raise ValueError("approved_targets must be ApprovedMacroTargets")
    if trend_window.user_id != user_id or approved_targets.user_id != user_id:
        raise ValueError("Calibration inputs must belong to the requested user_id")

    readiness = trend_window.calibration_readiness
    target_context = _target_context_status(approved_targets)
    recommended_action = _recommended_action(
        trend_window=trend_window,
        approved_targets=approved_targets,
        target_context_status=target_context,
    )
    calibration_allowed = _calibration_allowed(
        trend_window=trend_window,
        target_context_status=target_context,
        recommended_action=recommended_action,
    )
    confidence = _result_confidence(
        trend_window=trend_window,
        approved_targets=approved_targets,
        recommended_action=recommended_action,
    )
    reason_codes = _result_reason_codes(
        trend_window=trend_window,
        approved_targets=approved_targets,
        target_context_status=target_context,
        recommended_action=recommended_action,
    )
    limitations = _result_limitations(
        trend_window=trend_window,
        approved_targets=approved_targets,
        target_context_status=target_context,
        recommended_action=recommended_action,
    )

    metadata = NutritionTargetCalibrationMetadata(
        generated_at=_now_iso(),
        inputs_used=_metadata_inputs_used(
            trend_window=trend_window,
            approved_targets=approved_targets,
        ),
        reason_codes=[
            "deterministic_calibration_assessment",
            "target_mutation_not_performed",
        ],
        limitations=[READ_ONLY_CALIBRATION_LIMITATION],
    )

    return NutritionTargetCalibrationResult(
        user_id=user_id,
        calibration_date=calibration_date,
        window_days=trend_window.window_days,
        calibration_allowed=calibration_allowed,
        readiness_level=readiness.readiness_level,
        recommended_action=recommended_action,
        calibrated_targets=None,
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=limitations,
        metadata=metadata,
    )


def _build_formula_targets(
    *, user_id: int, calculation_date: str
) -> ApprovedMacroTargets:
    user_profile = get_user_profile(user_id)
    if not user_profile:
        raise ValueError(f"User with id {user_id} was not found.")
    health_state = build_user_health_state(user_id)
    inputs = build_nutrition_target_formula_inputs(
        health_state,
        calculation_date=calculation_date,
        sex=_row_value(user_profile, "gender"),
        input_source_metadata={"consumer": "nutrition_target_calibration_service"},
    )
    formula_result = calculate_nutrition_target_formula(inputs)
    return approve_validated_macro_targets(formula_result)


def _recommended_action(
    *,
    trend_window: NutritionTrendWindow,
    approved_targets: ApprovedMacroTargets,
    target_context_status: str,
) -> str:
    readiness_level = trend_window.calibration_readiness.readiness_level
    logging_status = trend_window.intake_trend_summary.logging_consistency_status
    bodyweight_unavailable = (
        trend_window.bodyweight_trend_summary.trend_direction
        == BODYWEIGHT_TREND_UNAVAILABLE
    )

    if readiness_level == CALIBRATION_READINESS_NOT_READY:
        return RECOMMENDED_ACTION_INSUFFICIENT_DATA
    if target_context_status != "formula_targets_usable":
        return RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE
    if bodyweight_unavailable or logging_status == LOGGING_CONSISTENCY_INSUFFICIENT:
        return RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE
    if readiness_level == CALIBRATION_READINESS_EARLY_SIGNAL:
        return RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE
    if readiness_level == CALIBRATION_READINESS_STRONG and _has_full_macro_context(
        approved_targets
    ):
        return RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT
    if readiness_level == CALIBRATION_READINESS_USABLE:
        return RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS
    return RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE


def _calibration_allowed(
    *,
    trend_window: NutritionTrendWindow,
    target_context_status: str,
    recommended_action: str,
) -> bool:
    if recommended_action == RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT:
        return True
    if recommended_action == RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS:
        return trend_window.calibration_readiness.calibration_allowed and (
            target_context_status == "formula_targets_usable"
        )
    return False


def _result_confidence(
    *,
    trend_window: NutritionTrendWindow,
    approved_targets: ApprovedMacroTargets,
    recommended_action: str,
) -> str:
    if recommended_action == RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT:
        return _min_confidence(trend_window.confidence, approved_targets.confidence)
    if recommended_action == RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS:
        return _min_confidence(trend_window.confidence, approved_targets.confidence)
    if recommended_action == RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE:
        return "Low" if trend_window.confidence != "Limited" else "Limited"
    return "Limited"


def _result_reason_codes(
    *,
    trend_window: NutritionTrendWindow,
    approved_targets: ApprovedMacroTargets,
    target_context_status: str,
    recommended_action: str,
) -> list[str]:
    reason_codes = [
        "calibration_assessment_created",
        "target_mutation_not_performed",
        "no_exact_maintenance_claim",
        target_context_status,
        recommended_action,
    ]
    reason_codes.extend(trend_window.reason_codes)
    reason_codes.extend(trend_window.calibration_readiness.reason_codes)
    reason_codes.extend(_target_reason_codes(approved_targets))

    if recommended_action == RECOMMENDED_ACTION_INSUFFICIENT_DATA:
        reason_codes.append("calibration_not_ready")
    elif recommended_action == RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE:
        reason_codes.append("target_range_remains_broad")
    elif recommended_action == RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS:
        reason_codes.append("current_targets_kept")
    elif recommended_action == RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT:
        reason_codes.append("future_refinement_candidate")

    return _unique(reason_codes)


def _result_limitations(
    *,
    trend_window: NutritionTrendWindow,
    approved_targets: ApprovedMacroTargets,
    target_context_status: str,
    recommended_action: str,
) -> list[str]:
    limitations = [READ_ONLY_CALIBRATION_LIMITATION]
    limitations.extend(trend_window.limitations)
    limitations.extend(trend_window.calibration_readiness.limitations)

    if target_context_status != "formula_targets_usable":
        limitations.append(
            "Formula-derived targets are still limited, so target ranges should remain broad."
        )
    if approved_targets.confidence in {"Limited", "Low"}:
        limitations.append(
            "Formula target confidence is not strong enough for target refinement."
        )
    if (
        trend_window.bodyweight_trend_summary.trend_direction
        == BODYWEIGHT_TREND_UNAVAILABLE
    ):
        limitations.append(
            "Bodyweight trend evidence is unavailable, so calibration is limited."
        )
    if trend_window.intake_trend_summary.logging_consistency_status not in {
        LOGGING_CONSISTENCY_USABLE,
        LOGGING_CONSISTENCY_STRONG,
    }:
        limitations.append(
            "Logging consistency is not strong enough for nutrition target calibration."
        )

    if recommended_action == RECOMMENDED_ACTION_INSUFFICIENT_DATA:
        limitations.append(
            "Calibration is not ready because trend evidence is incomplete."
        )
    elif recommended_action == RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE:
        limitations.append("Targets remain broad because trend evidence is limited.")
    elif recommended_action == RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS:
        limitations.append(
            "Current data supports keeping formula-derived targets unchanged."
        )
    elif recommended_action == RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT:
        limitations.append(
            "The current trend window may support future target refinement after review."
        )

    return _unique(limitations)


def _target_context_status(approved_targets: ApprovedMacroTargets) -> str:
    display_flags = approved_targets.display_flags
    if approved_targets.confidence in {"Limited", "Low"}:
        return "formula_targets_limited"
    if not display_flags.get("allow_calorie_targets", False):
        return "formula_calorie_target_limited"
    if not display_flags.get("allow_protein_targets", False):
        return "formula_protein_target_limited"
    return "formula_targets_usable"


def _target_reason_codes(approved_targets: ApprovedMacroTargets) -> list[str]:
    reason_codes = list(approved_targets.reason_codes)
    for target in _target_values(approved_targets):
        if target is not None:
            reason_codes.extend(target.reason_codes)
    return reason_codes


def _has_full_macro_context(approved_targets: ApprovedMacroTargets) -> bool:
    flags = approved_targets.display_flags
    return all(
        flags.get(flag, False)
        for flag in (
            "allow_calorie_targets",
            "allow_protein_targets",
            "allow_carbohydrate_targets",
            "allow_fat_targets",
        )
    )


def _target_values(
    approved_targets: ApprovedMacroTargets,
) -> list[MacroTargetResult | None]:
    return [
        approved_targets.calorie_target,
        approved_targets.protein_target_g,
        approved_targets.carbohydrate_target_g,
        approved_targets.fat_target_g,
    ]


def _metadata_inputs_used(
    *, trend_window: NutritionTrendWindow, approved_targets: ApprovedMacroTargets
) -> list[str]:
    inputs = ["formula_derived_targets", "nutrition_trend_window"]
    if approved_targets.display_flags.get("allow_calorie_targets", False):
        inputs.append("approved_calorie_target")
    if approved_targets.display_flags.get("allow_protein_targets", False):
        inputs.append("approved_protein_target")
    if trend_window.logged_day_count > 0:
        inputs.append("logged_intake_trend")
    if (
        trend_window.bodyweight_trend_summary.trend_direction
        != BODYWEIGHT_TREND_UNAVAILABLE
    ):
        inputs.append("bodyweight_trend")
    if trend_window.calibration_readiness.goal_context_available:
        inputs.append("goal_context")
    if trend_window.calibration_readiness.training_context_available:
        inputs.append("training_context")
    return inputs


def _resolve_date(value: str | None) -> str:
    if value is None:
        return date.today().isoformat()
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD format") from exc


def _row_value(row: Any, key: str) -> Any:
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _min_confidence(left: str, right: str) -> str:
    rank = {"Limited": 0, "Low": 1, "Moderate": 2, "High": 3}
    value_by_rank = {rank_value: value for value, rank_value in rank.items()}
    return value_by_rank[min(rank[left], rank[right])]


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _validate_required_text(field_name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    _validate_safe_text_list(field_name, [value])


def _validate_positive_int(field_name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_confidence(confidence: str) -> None:
    if confidence not in CALIBRATION_CONFIDENCE_VALUES:
        raise ValueError(f"Invalid confidence: {confidence}")


def _validate_readiness_level(readiness_level: str) -> None:
    if readiness_level not in {
        CALIBRATION_READINESS_NOT_READY,
        CALIBRATION_READINESS_EARLY_SIGNAL,
        CALIBRATION_READINESS_USABLE,
        CALIBRATION_READINESS_STRONG,
    }:
        raise ValueError(f"Invalid readiness_level: {readiness_level}")


def _validate_recommended_action(recommended_action: str) -> None:
    if recommended_action not in RECOMMENDED_ACTION_VALUES:
        raise ValueError(f"Invalid recommended_action: {recommended_action}")


def _validate_safe_text_list(field_name: str, values: list[str]) -> None:
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must contain strings")
        normalized = value.lower()
        for phrase in FORBIDDEN_CALIBRATION_LANGUAGE:
            if phrase in normalized:
                raise ValueError(
                    "Forbidden nutrition calibration language is not allowed"
                )
