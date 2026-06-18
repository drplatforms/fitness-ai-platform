from __future__ import annotations

from models.training_evidence_claim_models import ApprovedTrainingClaim
from services.training_evidence_claim_service import (
    CLAIM_TYPE_COMPLETE_REFERENCE_LIFT,
    CLAIM_TYPE_SCOPE_LIMIT,
    CLAIM_TYPE_SINGLE_SESSION_EFFORT,
    CLAIM_TYPE_SINGLE_SESSION_REP_PATTERN,
    build_training_evidence_context_from_quote_context,
    derive_approved_training_claims,
    validate_training_claim_language,
)


def _quote_context(
    *, reps: list[int] | None = None, rir: list[int] | None = None
) -> dict:
    return {
        "approved_workout_names": ["Upper Body Strength"],
        "approved_exercise_names": ["Dumbbell Bench Press"],
        "approved_training_summary_facts": [
            "Upper Body Strength was completed.",
            "Dumbbell Bench Press was logged at 50 lb for 8, 8, 8 reps.",
            "The final Dumbbell Bench Press set was logged at 1 RIR.",
        ],
        "approved_set_rep_load_rir_values": [
            {
                "workout_name": "Upper Body Strength",
                "exercise_name": "Dumbbell Bench Press",
                "actual_sets": 3,
                "actual_load_lb": 50,
                "actual_reps": reps if reps is not None else [8, 8, 8],
                "actual_rir": rir if rir is not None else [3, 2, 1],
            }
        ],
    }


def _claims_by_type(
    claims: list[ApprovedTrainingClaim],
) -> dict[str, ApprovedTrainingClaim]:
    return {claim.claim_type: claim for claim in claims}


def test_training_evidence_context_is_created_from_quote_context() -> None:
    context = build_training_evidence_context_from_quote_context(
        _quote_context(),
        required_quote_name="Upper Body Strength",
        required_fact_anchors=[
            "Dumbbell Bench Press was logged at 50 lb for 8, 8, 8 reps."
        ],
    )

    assert context.required_quote_name == "Upper Body Strength"
    assert context.workout_names == ["Upper Body Strength"]
    assert context.exercise_names == ["Dumbbell Bench Press"]
    assert context.set_rep_load_rir_values[0]["actual_reps"] == [8, 8, 8]


def test_approved_training_claim_model_preserves_contract_fields() -> None:
    claim = ApprovedTrainingClaim(
        claim_id="same_rep_pattern_dumbbell_bench_press",
        claim_type=CLAIM_TYPE_SINGLE_SESSION_REP_PATTERN,
        approved_meaning=(
            "Dumbbell Bench Press used the same rep count across all logged sets in this session."
        ),
        required_names=["Dumbbell Bench Press"],
        required_terms=["this session"],
        allowed_terms=["same rep count", "logged sets"],
        forbidden_scope=["trend", "progression"],
        source_fact_refs=["Dumbbell Bench Press"],
        scope="single_session",
    )

    payload = claim.to_dict()

    assert payload["claim_id"] == "same_rep_pattern_dumbbell_bench_press"
    assert payload["claim_type"] == CLAIM_TYPE_SINGLE_SESSION_REP_PATTERN
    assert payload["required_names"] == ["Dumbbell Bench Press"]
    assert payload["required_terms"] == ["this session"]
    assert payload["allowed_terms"] == ["same rep count", "logged sets"]
    assert payload["forbidden_scope"] == ["trend", "progression"]
    assert payload["scope"] == "single_session"
    assert payload["public_safe"] is True


def test_same_rep_claim_is_generated_only_when_all_logged_reps_match() -> None:
    context = build_training_evidence_context_from_quote_context(
        _quote_context(reps=[8, 8, 8]),
        required_quote_name="Upper Body Strength",
    )

    claims = derive_approved_training_claims(context)

    assert CLAIM_TYPE_SINGLE_SESSION_REP_PATTERN in _claims_by_type(claims)
    same_rep_claim = _claims_by_type(claims)[CLAIM_TYPE_SINGLE_SESSION_REP_PATTERN]
    assert "same rep count" in same_rep_claim.approved_meaning
    assert same_rep_claim.scope == "single_session"

    varied_context = build_training_evidence_context_from_quote_context(
        _quote_context(reps=[8, 7, 8]),
        required_quote_name="Upper Body Strength",
    )

    varied_claims = derive_approved_training_claims(varied_context)

    assert CLAIM_TYPE_SINGLE_SESSION_REP_PATTERN not in _claims_by_type(varied_claims)


def test_high_effort_claim_is_generated_only_from_zero_or_one_rir() -> None:
    context = build_training_evidence_context_from_quote_context(
        _quote_context(rir=[3, 2, 1]),
        required_quote_name="Upper Body Strength",
    )

    claims = derive_approved_training_claims(context)

    assert CLAIM_TYPE_SINGLE_SESSION_EFFORT in _claims_by_type(claims)
    effort_claim = _claims_by_type(claims)[CLAIM_TYPE_SINGLE_SESSION_EFFORT]
    assert "1 RIR" in effort_claim.approved_meaning
    assert "this logged session" in effort_claim.approved_meaning

    moderate_context = build_training_evidence_context_from_quote_context(
        _quote_context(rir=[4, 3, 2]),
        required_quote_name="Upper Body Strength",
    )

    moderate_claims = derive_approved_training_claims(moderate_context)

    assert CLAIM_TYPE_SINGLE_SESSION_EFFORT not in _claims_by_type(moderate_claims)


def test_complete_reference_lift_claim_requires_complete_logged_details() -> None:
    context = build_training_evidence_context_from_quote_context(
        _quote_context(),
        required_quote_name="Upper Body Strength",
        required_fact_anchors=[
            "Dumbbell Bench Press was logged at 50 lb for 8, 8, 8 reps."
        ],
    )

    claims = derive_approved_training_claims(context)

    assert CLAIM_TYPE_COMPLETE_REFERENCE_LIFT in _claims_by_type(claims)

    incomplete_quote_context = _quote_context()
    incomplete_quote_context["approved_set_rep_load_rir_values"][0]["actual_rir"] = []
    incomplete_context = build_training_evidence_context_from_quote_context(
        incomplete_quote_context,
        required_quote_name="Upper Body Strength",
    )

    incomplete_claims = derive_approved_training_claims(incomplete_context)

    assert CLAIM_TYPE_COMPLETE_REFERENCE_LIFT not in _claims_by_type(incomplete_claims)


def test_single_session_scope_claim_is_generated_for_one_session_context() -> None:
    context = build_training_evidence_context_from_quote_context(
        _quote_context(),
        required_quote_name="Upper Body Strength",
    )

    claims = derive_approved_training_claims(context)

    assert CLAIM_TYPE_SCOPE_LIMIT in _claims_by_type(claims)
    scope_claim = _claims_by_type(claims)[CLAIM_TYPE_SCOPE_LIMIT]
    assert "single-session observation" in scope_claim.approved_meaning
    assert "trend" in scope_claim.approved_meaning


def test_bounded_same_rep_language_passes_when_approved() -> None:
    context = build_training_evidence_context_from_quote_context(
        _quote_context(),
        required_quote_name="Upper Body Strength",
    )
    claims = derive_approved_training_claims(context)

    result = validate_training_claim_language(
        "Dumbbell Bench Press used the same rep count across the logged sets in this session.",
        claims,
    )

    assert result.claim_valid is True
    assert result.validation_errors == []


def test_broad_consistency_language_fails_even_with_same_rep_claim() -> None:
    context = build_training_evidence_context_from_quote_context(
        _quote_context(),
        required_quote_name="Upper Body Strength",
    )
    claims = derive_approved_training_claims(context)

    result = validate_training_claim_language(
        "You are consistent and your consistency is improving over time.",
        claims,
    )

    assert result.claim_valid is False
    assert (
        "Broad consistency claims are not approved training evidence."
        in result.validation_errors
    )


def test_bounded_high_effort_language_passes_when_approved() -> None:
    context = build_training_evidence_context_from_quote_context(
        _quote_context(rir=[3, 2, 0]),
        required_quote_name="Upper Body Strength",
    )
    claims = derive_approved_training_claims(context)

    result = validate_training_claim_language(
        "Dumbbell Bench Press finished close to failure based on the logged RIR in this session.",
        claims,
    )

    assert result.claim_valid is True


def test_broad_effort_recovery_and_form_language_fails() -> None:
    context = build_training_evidence_context_from_quote_context(
        _quote_context(rir=[3, 2, 0]),
        required_quote_name="Upper Body Strength",
    )
    claims = derive_approved_training_claims(context)

    result = validate_training_claim_language(
        "This shows great effort overall, recovery looks good, and form is strong.",
        claims,
    )

    assert result.claim_valid is False
    assert (
        "Broad effort, fatigue, or recovery claims are not approved training evidence."
        in result.validation_errors
    )
    assert (
        "Form or execution-quality claims are not approved training evidence."
        in result.validation_errors
    )


def test_trend_and_progression_language_fails_without_explicit_scope_limit() -> None:
    context = build_training_evidence_context_from_quote_context(
        _quote_context(),
        required_quote_name="Upper Body Strength",
    )
    claims = derive_approved_training_claims(context)

    result = validate_training_claim_language(
        "Progression confirmed from this workout.",
        claims,
    )

    assert result.claim_valid is False
    assert (
        "Trend or progression claims are not approved training evidence."
        in result.validation_errors
    )
