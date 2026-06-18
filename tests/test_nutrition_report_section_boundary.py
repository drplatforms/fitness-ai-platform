from __future__ import annotations

import pytest

from models.nutrition_food_suggestion_models import (
    ApprovedFoodSuggestion,
    ApprovedNutritionFoodSuggestions,
    NutritionMacroGap,
)
from models.nutrition_report_section_models import (
    CLAIM_CONFIDENCE_LIMITED_BY_MISSING_LOGS,
    CLAIM_FOOD_SUGGESTION_AVAILABLE,
    CLAIM_LOGGING_INCOMPLETE,
    CLAIM_PROTEIN_BELOW_TARGET,
    NUTRITION_REPORT_SECTION_SOURCE_DETERMINISTIC,
    ApprovedNutritionClaim,
    ApprovedNutritionReportSection,
    CandidateNutritionReportSection,
    NutritionReportEvidenceContext,
)
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    TARGET_STATUS_BELOW,
    TARGET_STATUS_UNAVAILABLE,
    ApprovedNutritionGuidance,
    NutritionActuals,
    NutritionLoggingSummary,
    NutritionTargetComparison,
    TargetVsActualNutritionSummary,
)
from services.full_report_section_registry_service import (
    PROVIDER_STATUS_NONE,
    PROVIDER_STATUS_OPT_IN_FULL_REPORT_INTEGRATED,
    SECTION_ID_NUTRITION_REPORT,
    SECTION_ID_NUTRITION_TARGET_DISPLAY,
    SECTION_ID_TRAINING,
    get_full_report_section_definition,
    get_provider_integrated_full_report_section_ids,
)
from services.nutrition_report_section_service import (
    build_deterministic_nutrition_report_section,
    build_nutrition_report_evidence_context,
    derive_approved_nutrition_claims,
    validate_nutrition_report_section,
)


def _comparison(
    nutrient: str,
    *,
    actual: float | None = None,
    target_min: float | None = None,
    target_max: float | None = None,
    target_status: str = TARGET_STATUS_UNAVAILABLE,
    available: bool = False,
    confidence: str = "Limited",
) -> NutritionTargetComparison:
    return NutritionTargetComparison(
        nutrient=nutrient,
        actual=actual,
        target_min=target_min,
        target_max=target_max,
        delta_min=(
            actual - target_min
            if available and actual is not None and target_min is not None
            else None
        ),
        delta_max=(
            actual - target_max
            if available and actual is not None and target_max is not None
            else None
        ),
        percent_of_target=None,
        target_status=target_status,
        comparison_available=available,
        confidence=confidence,
        reason_codes=[f"{nutrient}_comparison_fixture"],
        limitations=(
            [] if available else [f"{nutrient.title()} comparison is unavailable."]
        ),
    )


def _summary_no_logs() -> TargetVsActualNutritionSummary:
    actuals = NutritionActuals(
        user_id=102,
        logging_date="2026-06-14",
        logging_window="calendar_day",
        logged_meal_count=0,
        entry_count=0,
        source_count=0,
        reason_codes=["no_nutrition_logs_today", "nutrition_actuals_unavailable"],
    )
    logging_summary = NutritionLoggingSummary(
        user_id=102,
        logging_date="2026-06-14",
        logging_completeness=LOGGING_COMPLETENESS_NO_LOGS,
        confidence="Limited",
        logged_meal_count=0,
        entry_count=0,
        reason_codes=["no_nutrition_logs_today", "nutrition_actuals_unavailable"],
        limitations=["No nutrition logs were found for this date."],
    )
    comparisons = {
        nutrient: _comparison(nutrient)
        for nutrient in ["calories", "protein", "carbs", "fat"]
    }
    return TargetVsActualNutritionSummary(
        user_id=102,
        date="2026-06-14",
        nutrition_actuals=actuals,
        logging_summary=logging_summary,
        comparisons=comparisons,
        logging_completeness=LOGGING_COMPLETENESS_NO_LOGS,
        confidence="Limited",
        reason_codes=["no_nutrition_logs_today", "nutrition_actuals_unavailable"],
        limitations=["No nutrition logs were found for this date."],
    )


def _summary_protein_gap() -> TargetVsActualNutritionSummary:
    actuals = NutritionActuals(
        user_id=102,
        logging_date="2026-06-14",
        logging_window="calendar_day",
        logged_calories=2100,
        logged_protein=90,
        logged_carbs=220,
        logged_fat=70,
        logged_meal_count=4,
        entry_count=4,
        source_count=4,
        reason_codes=["nutrition_logs_available"],
    )
    logging_summary = NutritionLoggingSummary(
        user_id=102,
        logging_date="2026-06-14",
        logging_completeness=LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
        confidence="High",
        logged_meal_count=4,
        entry_count=4,
        reason_codes=["complete_enough_for_guidance"],
    )
    comparisons = {
        "calories": _comparison(
            "calories",
            actual=2100,
            target_min=2000,
            target_max=2400,
            target_status="near_target",
            available=True,
            confidence="High",
        ),
        "protein": _comparison(
            "protein",
            actual=90,
            target_min=140,
            target_max=180,
            target_status=TARGET_STATUS_BELOW,
            available=True,
            confidence="High",
        ),
        "carbs": _comparison(
            "carbs",
            actual=220,
            target_min=180,
            target_max=260,
            target_status="near_target",
            available=True,
            confidence="High",
        ),
        "fat": _comparison(
            "fat",
            actual=70,
            target_min=55,
            target_max=90,
            target_status="near_target",
            available=True,
            confidence="High",
        ),
    }
    return TargetVsActualNutritionSummary(
        user_id=102,
        date="2026-06-14",
        nutrition_actuals=actuals,
        logging_summary=logging_summary,
        comparisons=comparisons,
        logging_completeness=LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
        confidence="High",
        reason_codes=["complete_enough_for_guidance", "logged_protein_below_target"],
        limitations=[],
    )


def _summary_partial_logging() -> TargetVsActualNutritionSummary:
    actuals = NutritionActuals(
        user_id=102,
        logging_date="2026-06-14",
        logging_window="calendar_day",
        logged_protein=35,
        logged_meal_count=1,
        entry_count=1,
        source_count=1,
        reason_codes=["nutrition_logs_available", "missing_calorie_values"],
    )
    logging_summary = NutritionLoggingSummary(
        user_id=102,
        logging_date="2026-06-14",
        logging_completeness=LOGGING_COMPLETENESS_PARTIAL_DAY,
        confidence="Low",
        logged_meal_count=1,
        entry_count=1,
        missing_nutrient_fields=["calories", "carbohydrates", "fat"],
        reason_codes=["partial_nutrition_logging"],
        limitations=["Nutrition logging appears partial for this date."],
    )
    comparisons = {
        nutrient: _comparison(
            nutrient, actual=(35 if nutrient == "protein" else None), confidence="Low"
        )
        for nutrient in ["calories", "protein", "carbs", "fat"]
    }
    return TargetVsActualNutritionSummary(
        user_id=102,
        date="2026-06-14",
        nutrition_actuals=actuals,
        logging_summary=logging_summary,
        comparisons=comparisons,
        logging_completeness=LOGGING_COMPLETENESS_PARTIAL_DAY,
        confidence="Low",
        reason_codes=["partial_nutrition_logging", "calorie_delta_not_available"],
        limitations=["Nutrition logging appears partial for this date."],
    )


def _guidance(summary: TargetVsActualNutritionSummary) -> ApprovedNutritionGuidance:
    if summary.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS:
        return ApprovedNutritionGuidance(
            user_id=summary.user_id,
            date=summary.date,
            summary_message="No nutrition logs were found for this date.",
            protein_guidance="Protein comparison is limited until approved protein targets and logged protein are available.",
            calorie_guidance="Calories are not compared because calorie targets are currently limited.",
            macro_guidance="Macro comparisons are limited until logging is more complete.",
            logging_guidance="No nutrition logs were found for this date, so guidance should stay limited.",
            confidence="Limited",
            reason_codes=list(summary.reason_codes),
            limitations=list(summary.limitations),
        )
    if summary.logging_completeness == LOGGING_COMPLETENESS_PARTIAL_DAY:
        return ApprovedNutritionGuidance(
            user_id=summary.user_id,
            date=summary.date,
            summary_message="Nutrition logging is incomplete, so conclusions should stay limited.",
            protein_guidance="Protein comparison is limited until approved protein targets and logged protein are available.",
            calorie_guidance="Nutrition logging is incomplete, so calorie conclusions should stay limited.",
            macro_guidance="Macro comparisons are limited until logging is more complete.",
            logging_guidance="Logged intake is incomplete, so avoid making bigger nutrition changes from this day alone.",
            confidence="Low",
            reason_codes=list(summary.reason_codes),
            limitations=list(summary.limitations),
        )
    return ApprovedNutritionGuidance(
        user_id=summary.user_id,
        date=summary.date,
        summary_message="Logged nutrition can be compared cautiously with approved targets.",
        protein_guidance="Based on logged meals, protein is below today's target.",
        calorie_guidance="Logged calories are near the approved range based on complete-enough logs.",
        macro_guidance="Carbohydrate and fat logs can be compared cautiously against approved ranges.",
        logging_guidance="Logged intake is complete enough to support cautious nutrition guidance.",
        confidence="High",
        reason_codes=list(summary.reason_codes),
        limitations=list(summary.limitations),
    )


def _food_suggestions(
    *,
    with_suggestion: bool,
    confidence: str = "High",
) -> ApprovedNutritionFoodSuggestions:
    protein_gap = NutritionMacroGap(
        macro_name="protein_g",
        target_value=140,
        actual_value=90 if with_suggestion else None,
        gap_value=50 if with_suggestion else None,
        unit="g",
        target_status=TARGET_STATUS_BELOW if with_suggestion else "limited",
        display_allowed=with_suggestion,
        confidence=confidence,
        reason_codes=(
            ["protein_gap_available"] if with_suggestion else ["target_not_approved"]
        ),
        limitations=(
            [] if with_suggestion else ["Protein target comparison is limited."]
        ),
    )
    suggestions = []
    if with_suggestion:
        suggestions.append(
            ApprovedFoodSuggestion(
                canonical_food_id=1,
                display_name="Chicken Breast, Cooked, Skinless",
                suggested_grams=150,
                estimated_calories=248,
                estimated_protein_g=46,
                estimated_carbohydrate_g=0,
                estimated_fat_g=5,
                macro_gap_addressed="protein_g",
                suggestion_summary="Chicken Breast, Cooked, Skinless can help close the approved protein gap.",
                confidence="High",
                reason_codes=["approved_canonical_food_suggestion"],
            )
        )
    return ApprovedNutritionFoodSuggestions(
        user_id=102,
        suggestion_date="2026-06-14",
        primary_gap="protein_g" if with_suggestion else None,
        macro_gaps=[protein_gap],
        suggestions=suggestions,
        confidence=confidence,
        reason_codes=(
            ["protein_gap_available"] if with_suggestion else ["target_not_approved"]
        ),
        limitations=[] if with_suggestion else ["No approved suggestion is available."],
    )


def _evidence(
    summary: TargetVsActualNutritionSummary,
    *,
    with_suggestion: bool = False,
) -> NutritionReportEvidenceContext:
    suggestions = _food_suggestions(
        with_suggestion=with_suggestion,
        confidence=summary.confidence,
    )
    return NutritionReportEvidenceContext(
        user_id=summary.user_id,
        report_date=summary.date,
        target_vs_actual_summary=summary.to_dict(),
        approved_nutrition_guidance=_guidance(summary).to_dict(),
        approved_food_suggestions=suggestions.to_dict(),
        confidence=summary.confidence,
        reason_codes=["nutrition_report_section_test_fixture", *summary.reason_codes],
        limitations=[*summary.limitations, *suggestions.limitations],
    )


def test_nutrition_report_section_is_distinct_from_target_display_in_registry():
    nutrition_section = get_full_report_section_definition(SECTION_ID_NUTRITION_REPORT)
    target_display = get_full_report_section_definition(
        SECTION_ID_NUTRITION_TARGET_DISPLAY
    )
    training = get_full_report_section_definition(SECTION_ID_TRAINING)

    assert nutrition_section is not None
    assert target_display is not None
    assert training is not None
    assert nutrition_section.section_id != target_display.section_id
    assert nutrition_section.maturity_level == 3
    assert target_display.maturity_level == 2
    assert nutrition_section.provider_status == PROVIDER_STATUS_NONE
    assert get_provider_integrated_full_report_section_ids() == ["training"]
    assert training.provider_status == PROVIDER_STATUS_OPT_IN_FULL_REPORT_INTEGRATED


def test_nutrition_report_section_fallback_handles_missing_logs_safely():
    evidence = _evidence(_summary_no_logs())

    section = build_deterministic_nutrition_report_section(evidence)
    validation = validate_nutrition_report_section(section, evidence_context=evidence)
    claim_types = {claim.claim_type for claim in section.approved_claims}
    text = " ".join(
        section.to_dict().values()
        if False
        else [
            section.section_summary,
            section.intake_snapshot,
            section.target_alignment,
            section.logging_quality,
            section.practical_food_focus,
            section.next_nutrition_action,
            section.limitations_context,
        ]
    ).lower()

    assert section.section_id == "nutrition_report_section"
    assert section.confidence == "Limited"
    assert CLAIM_LOGGING_INCOMPLETE in claim_types
    assert CLAIM_CONFIDENCE_LIMITED_BY_MISSING_LOGS in claim_types
    assert "no nutrition logs" in text
    assert "severe deficit" not in text
    assert "supplement" not in text
    assert validation.valid is True


def test_nutrition_report_section_handles_incomplete_logs_without_unsupported_claims():
    evidence = _evidence(_summary_partial_logging())

    section = build_deterministic_nutrition_report_section(evidence)
    validation = validate_nutrition_report_section(section, evidence_context=evidence)
    claim_types = {claim.claim_type for claim in section.approved_claims}
    text = "\n".join(
        [
            section.section_summary,
            section.target_alignment,
            section.logging_quality,
            section.next_nutrition_action,
        ]
    ).lower()

    assert CLAIM_LOGGING_INCOMPLETE in claim_types
    assert CLAIM_PROTEIN_BELOW_TARGET not in claim_types
    assert "protein appears below" not in text
    assert "calories appear below" not in text
    assert "protein comparison is limited" in text
    assert validation.valid is True


def test_nutrition_report_claims_derive_from_backend_target_actual_and_food_data():
    evidence = _evidence(_summary_protein_gap(), with_suggestion=True)

    claims = derive_approved_nutrition_claims(evidence)
    section = build_deterministic_nutrition_report_section(evidence)
    validation = validate_nutrition_report_section(section, evidence_context=evidence)
    claim_types = {claim.claim_type for claim in claims}

    assert CLAIM_PROTEIN_BELOW_TARGET in claim_types
    assert CLAIM_FOOD_SUGGESTION_AVAILABLE in claim_types
    assert section.source.endswith("fallback")
    assert "Chicken Breast" in section.practical_food_focus
    assert "150 g" in section.practical_food_focus
    assert validation.valid is True


def test_nutrition_report_validation_rejects_medical_supplement_and_unsupported_calorie_claims():
    evidence = _evidence(_summary_partial_logging())
    safe_claim = ApprovedNutritionClaim(
        claim_type=CLAIM_LOGGING_INCOMPLETE,
        claim_text="Nutrition logging is incomplete, so conclusions should stay limited.",
        evidence_fields=["logging_summary.logging_completeness"],
        confidence="Low",
        reason_codes=["nutrition_logging_incomplete"],
    )
    bad_candidate = CandidateNutritionReportSection(
        section_summary="Nutrition logging is incomplete, so conclusions should stay limited.",
        intake_snapshot="One nutrition entry is logged for this report date.",
        target_alignment="Calories appear below the approved range based on complete-enough logs.",
        logging_quality="Logged intake is incomplete, so avoid bigger changes from this day alone.",
        practical_food_focus="No approved canonical food suggestion is available from the current evidence.",
        next_nutrition_action="Keep logging complete meals and review approved Nutrition tab guidance.",
        limitations_context="This section stays limited because calorie comparison is unavailable.",
        confidence="Low",
        reason_codes=["unit_test_unsafe_candidate"],
    )

    bad_section = ApprovedNutritionReportSection.from_candidate(
        bad_candidate,
        approved_claims=[safe_claim],
        source=NUTRITION_REPORT_SECTION_SOURCE_DETERMINISTIC,
    )
    validation = validate_nutrition_report_section(
        bad_section, evidence_context=evidence
    )

    assert validation.valid is False
    assert any(
        "Calorie target-alignment" in error for error in validation.validation_errors
    )

    with pytest.raises(ValueError, match="supplement"):
        CandidateNutritionReportSection(
            section_summary="Nutrition logging is incomplete, so conclusions should stay limited.",
            intake_snapshot="One nutrition entry is logged for this report date.",
            target_alignment="Target alignment should stay limited.",
            logging_quality="Logged intake is incomplete.",
            practical_food_focus="Supplements should be used to close the gap.",
            next_nutrition_action="Keep logging complete meals.",
            limitations_context="This section stays conservative.",
            confidence="Low",
            reason_codes=["unit_test_unsafe_candidate"],
        )


def test_build_context_uses_existing_backend_owned_services(monkeypatch):
    summary = _summary_protein_gap()
    suggestions = _food_suggestions(with_suggestion=True)

    monkeypatch.setattr(
        "services.nutrition_report_section_service.build_target_vs_actual_nutrition_summary",
        lambda *_args, **_kwargs: summary,
    )
    monkeypatch.setattr(
        "services.nutrition_report_section_service.build_approved_nutrition_food_suggestions",
        lambda *_args, **_kwargs: suggestions,
    )

    evidence = build_nutrition_report_evidence_context(
        user_id=102,
        report_date="2026-06-14",
    )

    assert evidence.user_id == 102
    assert evidence.report_date == "2026-06-14"
    assert evidence.target_vs_actual_summary["confidence"] == "High"
    assert evidence.approved_food_suggestions["suggestions"]
    assert "nutrition_report_section_evidence_context" in evidence.reason_codes
