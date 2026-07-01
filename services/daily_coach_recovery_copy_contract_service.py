from __future__ import annotations

from dataclasses import asdict
from typing import Any

from models.daily_coach_intelligence_models import DailyCoachIntelligenceSnapshot
from models.daily_coach_recovery_copy_models import RecoveryAwareCoachCopyContract

_COPY_TONE_GUIDANCE = [
    "Use bounded wording such as appears, suggests, and based on available check-ins.",
    "Frame Recovery v2 as readiness context, not as a training command.",
    "Preserve confidence and data-quality limits near any recovery-aware copy.",
    "Keep body weight mentions contextual and non-causal.",
]

_FORBIDDEN_CLAIM_CATEGORIES = [
    "medical or diagnostic claims",
    "clinical advice or risk-certainty claims",
    "forced training-load changes",
    "automatic training-progression changes",
    "causal body-weight, fat-change, or nutrition-blame claims",
    "unsafe-to-train claims",
]

_LIMITED_STATUSES = {"missing", "limited", "partial"}
_LIMITED_CONFIDENCE = {"Limited", "Low"}


def build_recovery_aware_coach_copy_contract(
    daily_coach_context: DailyCoachIntelligenceSnapshot | dict[str, Any],
) -> RecoveryAwareCoachCopyContract:
    """Build a deterministic copy contract from Daily Coach Note recovery v2 facts.

    This service is read-only. It produces structured guidance for a future copy layer;
    it does not render Daily Coach Note copy, call providers, mutate persistence, or
    prescribe training changes.
    """

    context = _to_dict(daily_coach_context)
    user_id = _coerce_positive_int(context.get("user_id"))
    target_date = str(context.get("target_date") or "")
    source_services = [str(item) for item in context.get("source_services") or []]
    recovery_v2 = context.get("recovery_intelligence_v2")

    if not recovery_v2:
        return _unavailable_contract(
            user_id=user_id,
            target_date=target_date,
            source_services=source_services,
            context_reason_codes=context.get("reason_codes") or [],
            context_limitations=context.get("limitations") or [],
        )

    recovery = _to_dict(recovery_v2)
    data_quality = _to_dict(recovery.get("data_quality") or {})
    recovery_classification = str(recovery.get("readiness_classification") or "unknown")
    recovery_pressure = str(recovery.get("recovery_pressure") or "unknown")
    confidence = _bounded_confidence(str(recovery.get("confidence") or "Limited"))
    data_quality_status = _bounded_data_quality_status(
        str(data_quality.get("status") or "limited")
    )

    allowed_claims = _build_allowed_recovery_claims(recovery)
    required_caveats = _build_required_caveats(
        confidence=confidence,
        data_quality=data_quality,
        data_quality_status=data_quality_status,
    )
    reason_codes = _unique(
        [
            *_string_list(recovery.get("reason_codes")),
            *_string_list(data_quality.get("reason_codes")),
        ]
    )
    limitations = _unique(
        [
            *_string_list(recovery.get("limitations")),
            *_string_list(data_quality.get("limitations")),
        ]
    )
    if confidence in _LIMITED_CONFIDENCE and not required_caveats:
        required_caveats.append(
            "Recovery v2 confidence is limited by available check-in data."
        )
    if data_quality_status in _LIMITED_STATUSES and not required_caveats:
        required_caveats.append(
            "Recovery-aware copy should mention that check-in data is limited."
        )
    if "recovery_intelligence_v2_service" not in source_services:
        source_services.append("recovery_intelligence_v2_service")

    return RecoveryAwareCoachCopyContract(
        user_id=user_id,
        target_date=target_date,
        recovery_v2_available=True,
        recovery_classification=recovery_classification,
        recovery_pressure=recovery_pressure,
        confidence=confidence,
        data_quality_status=data_quality_status,
        allowed_recovery_claims=allowed_claims,
        required_caveats=_unique(required_caveats),
        forbidden_claims=list(_FORBIDDEN_CLAIM_CATEGORIES),
        copy_tone_guidance=list(_COPY_TONE_GUIDANCE),
        reason_codes=reason_codes,
        limitations=limitations,
        source_services=_unique(source_services),
    )


def _unavailable_contract(
    *,
    user_id: int,
    target_date: str,
    source_services: list[str],
    context_reason_codes: list[Any],
    context_limitations: list[Any],
) -> RecoveryAwareCoachCopyContract:
    return RecoveryAwareCoachCopyContract(
        user_id=user_id,
        target_date=target_date,
        recovery_v2_available=False,
        recovery_classification="unknown",
        recovery_pressure="unknown",
        confidence="Limited",
        data_quality_status="missing",
        allowed_recovery_claims=[
            "Recovery v2 is unavailable, so recovery-aware copy should not make "
            "specific recovery claims."
        ],
        required_caveats=[
            "Recovery v2 is unavailable for this Daily Coach Note context.",
            "Use only general check-in availability language until Recovery v2 is present.",
        ],
        forbidden_claims=list(_FORBIDDEN_CLAIM_CATEGORIES),
        copy_tone_guidance=list(_COPY_TONE_GUIDANCE),
        reason_codes=_unique(
            [
                "recovery_intelligence_v2_unavailable",
                *_string_list(context_reason_codes),
            ]
        ),
        limitations=_unique(
            [
                "Recovery-aware copy is limited because Recovery v2 facts are unavailable.",
                *_string_list(context_limitations),
            ]
        ),
        source_services=_unique(source_services),
    )


def _build_allowed_recovery_claims(recovery: dict[str, Any]) -> list[str]:
    claims: list[str] = []
    _append_indicator_claim(
        claims,
        label="sleep",
        indicator=_to_dict(recovery.get("sleep_interpretation") or {}),
    )
    _append_indicator_claim(
        claims,
        label="energy",
        indicator=_to_dict(recovery.get("energy_interpretation") or {}),
    )
    _append_indicator_claim(
        claims,
        label="soreness",
        indicator=_to_dict(recovery.get("soreness_interpretation") or {}),
    )

    recovery_pressure = str(recovery.get("recovery_pressure") or "unknown")
    if recovery_pressure in {"low", "moderate", "high"}:
        claims.append(
            f"Recent recovery pressure appears {recovery_pressure} based on "
            "available check-in data."
        )

    confidence = _bounded_confidence(str(recovery.get("confidence") or "Limited"))
    claims.append(f"Recovery v2 confidence is {confidence}.")

    body_weight = _to_dict(recovery.get("body_weight_interpretation") or {})
    if _has_body_weight_context(body_weight):
        claims.append(
            "Body weight is present as context only and is not causal evidence."
        )

    data_quality = _to_dict(recovery.get("data_quality") or {})
    status = _bounded_data_quality_status(str(data_quality.get("status") or "limited"))
    if status in _LIMITED_STATUSES:
        claims.append("Check-in data is limited or incomplete.")

    return _unique(claims)


def _append_indicator_claim(
    claims: list[str], *, label: str, indicator: dict[str, Any]
) -> None:
    status = str(indicator.get("status") or "unknown")
    if status == "unknown":
        return

    confidence = _bounded_confidence(str(indicator.get("confidence") or "Limited"))
    if confidence == "Limited":
        claims.append(
            f"{label.capitalize()} has limited check-in support, so wording should "
            "stay cautious."
        )
        return

    if label == "sleep":
        descriptor = _sleep_descriptor(status)
    elif label == "energy":
        descriptor = _energy_descriptor(status)
    else:
        descriptor = _soreness_descriptor(status)

    if descriptor:
        claims.append(
            f"{label.capitalize()} appears {descriptor} based on recent check-ins."
        )


def _sleep_descriptor(status: str) -> str | None:
    if status in {"low", "borderline"}:
        return "lower than baseline"
    if status == "high":
        return "higher than baseline"
    if status == "normal":
        return "near baseline"
    if status == "mixed":
        return "mixed"
    return None


def _energy_descriptor(status: str) -> str | None:
    if status in {"low", "borderline"}:
        return "lower than baseline"
    if status == "high":
        return "higher than baseline"
    if status == "normal":
        return "near baseline"
    if status == "mixed":
        return "mixed"
    return None


def _soreness_descriptor(status: str) -> str | None:
    if status == "high":
        return "elevated"
    if status == "borderline":
        return "somewhat elevated"
    if status == "normal":
        return "near baseline"
    if status in {"low", "mixed"}:
        return status
    return None


def _build_required_caveats(
    *, confidence: str, data_quality: dict[str, Any], data_quality_status: str
) -> list[str]:
    caveats: list[str] = []
    if confidence in _LIMITED_CONFIDENCE:
        caveats.append(
            "Mention that Recovery v2 confidence is limited before using recovery facts."
        )
    if data_quality_status in _LIMITED_STATUSES:
        caveats.append(
            "Mention that available check-in data is limited, partial, or missing."
        )
    checkin_days = data_quality.get("checkin_days")
    expected_days = data_quality.get("expected_days")
    if isinstance(checkin_days, int) and isinstance(expected_days, int):
        if checkin_days < expected_days:
            caveats.append(
                f"Recovery v2 is based on {checkin_days} of {expected_days} "
                "expected check-in days."
            )
    return caveats


def _has_body_weight_context(body_weight: dict[str, Any]) -> bool:
    for key in (
        "current_value",
        "baseline_value",
        "recent_average",
        "prior_average",
        "delta_from_baseline",
        "delta_recent_vs_prior",
    ):
        if body_weight.get(key) is not None:
            return True
    return False


def _bounded_confidence(value: str) -> str:
    return value if value in {"Limited", "Low", "Moderate", "High"} else "Limited"


def _bounded_data_quality_status(value: str) -> str:
    return (
        value
        if value in {"missing", "limited", "partial", "usable", "strong"}
        else "limited"
    )


def _to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        return value.to_dict()
    try:
        return asdict(value)
    except TypeError:
        return dict(value)


def _string_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, list):
        return [str(value) for value in values if value]
    return [str(values)]


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _coerce_positive_int(value: Any) -> int:
    try:
        user_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("user_id is required") from exc
    if user_id <= 0:
        raise ValueError("user_id must be positive")
    return user_id
