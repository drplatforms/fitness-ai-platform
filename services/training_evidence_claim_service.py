from __future__ import annotations

import re
from typing import Any

from models.training_evidence_claim_models import (
    ApprovedTrainingClaim,
    TrainingClaimValidationResult,
    TrainingEvidenceContext,
)

CLAIM_TYPE_SINGLE_SESSION_REP_PATTERN = "single_session_rep_pattern"
CLAIM_TYPE_SINGLE_SESSION_EFFORT = "single_session_effort"
CLAIM_TYPE_COMPLETE_REFERENCE_LIFT = "complete_reference_lift"
CLAIM_TYPE_SCOPE_LIMIT = "scope_limit"

CLAIM_SCOPE_SINGLE_SESSION = "single_session"
CONFIDENCE_MODERATE = "Moderate"


def build_training_evidence_context_from_quote_context(
    quote_context: dict[str, Any],
    *,
    required_quote_name: str | None = None,
    required_fact_anchors: list[str] | None = None,
) -> TrainingEvidenceContext:
    """Build a reusable training-evidence context from approved quote data.

    The input is expected to be backend-approved quote context. This service does
    not query model output, does not infer recovery/progression, and does not
    create user-facing copy. It only prepares factual evidence for bounded claim
    derivation.
    """

    return TrainingEvidenceContext(
        workout_names=_string_list(quote_context.get("approved_workout_names", []))[:8],
        exercise_names=_string_list(quote_context.get("approved_exercise_names", []))[
            :20
        ],
        set_rep_load_rir_values=_dict_list(
            quote_context.get("approved_set_rep_load_rir_values", [])
        )[:12],
        training_summary_facts=_string_list(
            quote_context.get("approved_training_summary_facts", [])
        )[:24],
        required_quote_name=_safe_nonempty_string(required_quote_name),
        required_fact_anchors=_string_list(required_fact_anchors or [])[:24],
    )


def derive_approved_training_claims(
    evidence_context: TrainingEvidenceContext,
    *,
    limit: int = 12,
) -> list[ApprovedTrainingClaim]:
    """Derive backend-approved, single-session training claims.

    These claims are intentionally narrow. They may later feed a deterministic
    training report section, a direct-Ollama provider context, or a full report
    integration, but they do not approve broad trends, recovery status, form
    quality, adherence, or progression conclusions.
    """

    claims: list[ApprovedTrainingClaim] = []
    set_payloads = evidence_context.set_rep_load_rir_values
    signal_names = _training_signal_name_list(evidence_context.required_fact_anchors)

    for payload in set_payloads:
        exercise_name = _safe_nonempty_string(payload.get("exercise_name"))
        if not exercise_name:
            continue

        reps = [
            value
            for value in payload.get("actual_reps", [])
            if isinstance(value, int | float)
        ]
        rir_values = [
            value
            for value in payload.get("actual_rir", [])
            if isinstance(value, int | float)
        ]

        if len(reps) >= 2 and len(set(reps)) == 1:
            claims.append(_same_rep_pattern_claim(exercise_name=exercise_name))

        if rir_values and rir_values[-1] <= 1:
            final_rir = _format_number(rir_values[-1])
            claims.append(
                _high_effort_from_rir_claim(
                    exercise_name=exercise_name,
                    final_rir=final_rir,
                )
            )

    complete_reference_names = _complete_reference_lift_names(
        set_payloads,
        preferred_names=signal_names,
    )
    if complete_reference_names:
        claims.append(_complete_reference_lift_claim(complete_reference_names))

    quote_name = (
        evidence_context.required_quote_name
        or _first_workout_name_from_set_payloads(set_payloads)
    )
    if quote_name:
        claims.append(_single_session_scope_claim(quote_name))

    return claims[:limit]


def derive_approved_training_claim_dicts(
    evidence_context: TrainingEvidenceContext,
    *,
    limit: int = 12,
) -> list[dict[str, Any]]:
    return [
        claim.to_dict()
        for claim in derive_approved_training_claims(evidence_context, limit=limit)
    ]


def validate_training_claim_language(
    text: str,
    approved_claims: list[ApprovedTrainingClaim | dict[str, Any]],
) -> TrainingClaimValidationResult:
    """Validate a small phrase against approved bounded claim scope.

    This helper is intentionally conservative and is not a replacement for the
    direct-Ollama section validator. It gives future callers and tests a reusable
    service-level boundary for allowed single-session claim language versus broad
    inference.
    """

    lowered = text.lower()
    claim_types = {_claim_type(claim) for claim in approved_claims}
    errors: list[str] = []

    if _contains_broad_consistency_claim(lowered):
        errors.append("Broad consistency claims are not approved training evidence.")

    if _contains_forbidden_progression_or_trend_claim(lowered):
        if CLAIM_TYPE_SCOPE_LIMIT not in claim_types or not _has_scope_limit_language(
            lowered
        ):
            errors.append(
                "Trend or progression claims are not approved training evidence."
            )

    if _contains_forbidden_effort_or_recovery_claim(lowered):
        errors.append(
            "Broad effort, fatigue, or recovery claims are not approved training evidence."
        )

    if _contains_form_or_execution_quality_claim(lowered):
        errors.append(
            "Form or execution-quality claims are not approved training evidence."
        )

    if (
        _contains_same_rep_language(lowered)
        and CLAIM_TYPE_SINGLE_SESSION_REP_PATTERN not in claim_types
    ):
        errors.append("Same-rep language requires an approved same-rep training claim.")

    if (
        _contains_high_effort_language(lowered)
        and CLAIM_TYPE_SINGLE_SESSION_EFFORT not in claim_types
    ):
        errors.append("High-effort language requires an approved RIR training claim.")

    return TrainingClaimValidationResult(
        claim_valid=not errors, validation_errors=errors
    )


def _same_rep_pattern_claim(*, exercise_name: str) -> ApprovedTrainingClaim:
    return ApprovedTrainingClaim(
        claim_id=f"same_rep_pattern_{_claim_id_slug(exercise_name)}",
        claim_type=CLAIM_TYPE_SINGLE_SESSION_REP_PATTERN,
        approved_meaning=(
            f"{exercise_name} used the same rep count across all logged sets in this session."
        ),
        required_names=[exercise_name],
        required_terms=["this session"],
        allowed_terms=[
            "same rep count",
            "steady reps",
            "consistent rep counts",
            "logged sets",
            "this session",
        ],
        forbidden_scope=[
            "trend",
            "progression",
            "consistency over time",
            "consistent performance",
        ],
        source_fact_refs=[exercise_name],
        scope=CLAIM_SCOPE_SINGLE_SESSION,
        confidence=CONFIDENCE_MODERATE,
        public_safe=True,
    )


def _high_effort_from_rir_claim(
    *,
    exercise_name: str,
    final_rir: str,
) -> ApprovedTrainingClaim:
    return ApprovedTrainingClaim(
        claim_id=f"high_effort_from_rir_{_claim_id_slug(exercise_name)}",
        claim_type=CLAIM_TYPE_SINGLE_SESSION_EFFORT,
        approved_meaning=(
            f"{exercise_name} finished with a final set at {final_rir} RIR, so effort was high within this logged session."
        ),
        required_names=[exercise_name],
        required_terms=["RIR", "this session"],
        allowed_terms=[
            "close to failure",
            "high effort",
            "effort context",
            "logged RIR",
            "this session",
        ],
        forbidden_scope=[
            "recovery",
            "fatigue pattern",
            "overall effort trend",
            "consistent effort",
        ],
        source_fact_refs=[exercise_name, f"final_rir:{final_rir}"],
        scope=CLAIM_SCOPE_SINGLE_SESSION,
        confidence=CONFIDENCE_MODERATE,
        public_safe=True,
    )


def _complete_reference_lift_claim(names: list[str]) -> ApprovedTrainingClaim:
    joined_names = _join_name_list(names)
    return ApprovedTrainingClaim(
        claim_id="complete_reference_lifts",
        claim_type=CLAIM_TYPE_COMPLETE_REFERENCE_LIFT,
        approved_meaning=(
            f"{joined_names} are the strongest reference lifts in this session because they have complete logged training details."
        ),
        required_names=names,
        allowed_terms=[
            "reference lifts",
            "clearest signal",
            "training decision",
            "complete logged training details",
        ],
        forbidden_scope=[
            "progression",
            "plan worked",
            "recovery is good",
            "form is strong",
        ],
        source_fact_refs=names,
        scope=CLAIM_SCOPE_SINGLE_SESSION,
        confidence=CONFIDENCE_MODERATE,
        public_safe=True,
    )


def _single_session_scope_claim(quote_name: str) -> ApprovedTrainingClaim:
    return ApprovedTrainingClaim(
        claim_id="single_session_scope",
        claim_type=CLAIM_TYPE_SCOPE_LIMIT,
        approved_meaning=(
            f"{quote_name} is a single-session observation and should not be treated as a trend."
        ),
        required_names=[quote_name],
        required_terms=["single-session", "trend"],
        allowed_terms=[
            "reference point",
            "not enough to prove",
            "one workout",
            "single-session",
            "not a trend",
        ],
        forbidden_scope=[
            "progression confirmed",
            "recovery pattern",
            "fatigue pattern",
        ],
        source_fact_refs=[quote_name],
        scope=CLAIM_SCOPE_SINGLE_SESSION,
        confidence=CONFIDENCE_MODERATE,
        public_safe=True,
    )


def _complete_reference_lift_names(
    set_payloads: list[dict[str, Any]],
    *,
    preferred_names: list[str],
    limit: int = 2,
) -> list[str]:
    complete_names: list[str] = []
    preferred_normalized = [_normalize_name(name) for name in preferred_names]
    payloads_by_name = {
        _normalize_name(str(payload.get("exercise_name", ""))): payload
        for payload in set_payloads
    }
    for normalized_name in preferred_normalized:
        payload = payloads_by_name.get(normalized_name)
        if payload and _has_complete_logged_training_details(payload):
            _append_unique_string(complete_names, str(payload.get("exercise_name")))
        if len(complete_names) >= limit:
            return complete_names

    for payload in set_payloads:
        if not _has_complete_logged_training_details(payload):
            continue
        exercise_name = _safe_nonempty_string(payload.get("exercise_name"))
        if exercise_name:
            _append_unique_string(complete_names, exercise_name)
        if len(complete_names) >= limit:
            break
    return complete_names


def _has_complete_logged_training_details(payload: dict[str, Any]) -> bool:
    return bool(
        _safe_nonempty_string(payload.get("exercise_name"))
        and payload.get("actual_sets") is not None
        and payload.get("actual_load_lb") is not None
        and isinstance(payload.get("actual_reps"), list)
        and payload.get("actual_reps")
        and isinstance(payload.get("actual_rir"), list)
        and payload.get("actual_rir")
    )


def _first_workout_name_from_set_payloads(
    set_payloads: list[dict[str, Any]],
) -> str | None:
    for payload in set_payloads:
        workout_name = _safe_nonempty_string(payload.get("workout_name"))
        if workout_name:
            return workout_name
    return None


def _training_signal_name_list(required_fact_anchors: list[str]) -> list[str]:
    names: list[str] = []
    for anchor in required_fact_anchors:
        if not _is_concrete_logged_performance_fact(anchor):
            continue
        name = _exercise_name_from_logged_performance_fact(anchor)
        if name:
            _append_unique_string(names, name)
        if len(names) >= 2:
            break
    return names


def _is_concrete_logged_performance_fact(fact: str) -> bool:
    lowered = fact.lower()
    return " was logged at " in lowered and " reps" in lowered


def _exercise_name_from_logged_performance_fact(fact: str) -> str | None:
    marker = " was logged at "
    if marker not in fact:
        return None
    exercise_name = fact.split(marker, 1)[0].strip()
    return exercise_name or None


def _format_number(value: int | float | None) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _join_name_list(names: list[str]) -> str:
    if not names:
        return "Training details"
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} and {names[-1]}"


def _claim_id_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "training_detail"


def _contains_same_rep_language(lowered: str) -> bool:
    return any(
        re.search(pattern, lowered)
        for pattern in [
            r"\bsame rep counts?\b",
            r"\bsteady reps\b",
            r"\bconsistent rep counts?\b",
        ]
    )


def _contains_high_effort_language(lowered: str) -> bool:
    return any(
        phrase in lowered
        for phrase in [
            "close to failure",
            "high effort",
            "effort context",
        ]
    )


def _contains_broad_consistency_claim(lowered: str) -> bool:
    return any(
        re.search(pattern, lowered)
        for pattern in [
            r"\byou (?:are|were) consistent\b",
            r"\bconsistent performance\b",
            r"\bconsistent effort\b",
            r"\bconsistency (?:trend|is improving|over time)\b",
            r"\bconsistent improvement\b",
            r"\bconsistent over time\b",
        ]
    )


def _contains_forbidden_progression_or_trend_claim(lowered: str) -> bool:
    return any(
        phrase in lowered
        for phrase in [
            "progression confirmed",
            "consistent improvement",
            "progress trend",
            "proves progress",
            "trend is improving",
        ]
    )


def _contains_forbidden_effort_or_recovery_claim(lowered: str) -> bool:
    return any(
        phrase in lowered
        for phrase in [
            "great effort overall",
            "consistently strong effort",
            "recovery handled it well",
            "recovery looks good",
            "fatigue is managed",
            "fatigue pattern",
            "recovery pattern",
        ]
    )


def _contains_form_or_execution_quality_claim(lowered: str) -> bool:
    return any(
        phrase in lowered
        for phrase in [
            "strong execution",
            "good form",
            "controlled reps",
            "form is strong",
            "well-executed",
            "quality work",
            "focused work",
        ]
    )


def _has_scope_limit_language(lowered: str) -> bool:
    return any(
        phrase in lowered
        for phrase in [
            "single-session",
            "single session",
            "not enough to call it a trend",
            "not enough to prove",
            "one workout",
        ]
    )


def _claim_type(claim: ApprovedTrainingClaim | dict[str, Any]) -> str | None:
    if isinstance(claim, ApprovedTrainingClaim):
        return claim.claim_type
    if isinstance(claim, dict):
        value = claim.get("claim_type")
        return value if isinstance(value, str) else None
    return None


def _safe_nonempty_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _append_unique_string(values: list[str], value: str | None) -> None:
    if not value:
        return
    normalized_existing = {_normalize_name(item) for item in values}
    if _normalize_name(value) not in normalized_existing:
        values.append(value)
