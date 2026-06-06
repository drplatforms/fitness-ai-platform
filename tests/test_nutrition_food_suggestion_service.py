from __future__ import annotations

import database
from models.nutrition_food_suggestion_models import NutritionMacroGap
from models.nutrition_target_models import NutritionTargets
from models.nutrition_target_vs_actual_models import TARGET_STATUS_UNAVAILABLE
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
    seed_starter_canonical_foods,
)
from services.nutrition_food_suggestion_service import (
    approve_food_suggestions,
    build_approved_nutrition_food_suggestions,
    build_nutrition_macro_gaps,
    get_canonical_food_suggestion_candidates,
    rank_food_suggestion_candidates,
)
from services.nutrition_service import add_canonical_food_entry
from services.nutrition_target_vs_actual_service import (
    build_target_vs_actual_nutrition_summary,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()
    seed_starter_canonical_foods()


def _approved_targets(
    *,
    protein: bool = True,
    calories: bool = False,
    macros: bool = False,
    confidence: str = "Moderate",
) -> NutritionTargets:
    return NutritionTargets(
        body_weight_lb=190,
        calorie_target_min=2200 if calories else None,
        calorie_target_max=2500 if calories else None,
        protein_grams_min=150 if protein else None,
        protein_grams_max=185 if protein else None,
        carbohydrate_grams_min=180 if macros else None,
        carbohydrate_grams_max=280 if macros else None,
        fat_grams_min=55 if macros else None,
        fat_grams_max=90 if macros else None,
        confidence=confidence,
        allow_calorie_targets=calories,
        allow_protein_targets=protein,
        allow_carbohydrate_targets=macros,
        allow_fat_targets=macros,
        nutrition_display_message="Unit test targets.",
        reason_codes=["unit_test_targets"],
    )


def _macro_gap(
    macro_name: str,
    *,
    target_status: str,
    display_allowed: bool = True,
    gap_value: float | None = None,
    reason_codes: list[str] | None = None,
    limitations: list[str] | None = None,
) -> NutritionMacroGap:
    unit = "kcal" if macro_name == "calories" else "g"
    return NutritionMacroGap(
        macro_name=macro_name,
        target_value=(
            (100.0 + gap_value)
            if display_allowed and gap_value
            else (100.0 if display_allowed else None)
        ),
        actual_value=100.0 if display_allowed else None,
        gap_value=gap_value,
        unit=unit,
        target_status=target_status,
        display_allowed=display_allowed,
        confidence="Moderate" if display_allowed else "Limited",
        reason_codes=reason_codes
        or (["target_not_approved"] if not display_allowed else []),
        limitations=limitations
        or (["Target is limited."] if not display_allowed else []),
    )


def _canonical_id_for_query(query: str) -> int:
    from services.food_normalization_service import search_canonical_foods

    results = search_canonical_foods(query, limit=1)
    assert results
    return int(results[0].canonical_food.id)


def _protein_gap_summary(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_id_for_query("chicken breast")
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=100,
        entry_date="2026-06-06",
    )
    return build_target_vs_actual_nutrition_summary(
        1,
        "2026-06-06",
        nutrition_targets=_approved_targets(),
    )


def test_build_nutrition_macro_gaps_detects_approved_protein_gap(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    gaps = build_nutrition_macro_gaps(summary)
    protein_gap = next(gap for gap in gaps if gap.macro_name == "protein_g")

    assert protein_gap.display_allowed is True
    assert protein_gap.target_status == "below_target"
    assert protein_gap.gap_value == 119.0
    assert "protein_gap_available" in protein_gap.reason_codes


def test_protein_gap_produces_approved_canonical_food_suggestions(
    tmp_path, monkeypatch
):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert approved.primary_gap == "protein_g"
    assert approved.suggestions
    assert "protein_gap_available" in approved.reason_codes
    assert all(suggestion.canonical_food_id > 0 for suggestion in approved.suggestions)
    assert all(
        suggestion.macro_gap_addressed == "protein_g"
        for suggestion in approved.suggestions
    )


def test_no_protein_target_produces_no_protein_suggestions_with_limitations(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_id_for_query("chicken breast")
    add_canonical_food_entry(1, chicken_id, 100, "2026-06-06")
    summary = build_target_vs_actual_nutrition_summary(
        1,
        "2026-06-06",
        nutrition_targets=_approved_targets(protein=False),
    )

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert approved.suggestions == []
    assert "target_not_approved" in approved.reason_codes
    assert approved.limitations
    protein_gap = next(
        gap for gap in approved.macro_gaps if gap.macro_name == "protein_g"
    )
    assert protein_gap.display_allowed is False


def test_blocked_protein_target_produces_no_suggestions(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    summary = build_target_vs_actual_nutrition_summary(
        1,
        "2026-06-06",
        nutrition_targets=_approved_targets(protein=False),
    )

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert approved.suggestions == []
    protein_gap = next(
        gap for gap in approved.macro_gaps if gap.macro_name == "protein_g"
    )
    assert protein_gap.target_status in {"limited", "unavailable"}
    assert protein_gap.display_allowed is False


def test_no_macro_gap_produces_no_suggestion_state(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_id_for_query("chicken breast")
    add_canonical_food_entry(1, chicken_id, 700, "2026-06-06")
    summary = build_target_vs_actual_nutrition_summary(
        1,
        "2026-06-06",
        nutrition_targets=_approved_targets(),
    )

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert approved.suggestions == []
    assert "no_macro_gap_detected" in approved.reason_codes


def test_protein_above_target_with_calorie_gap_uses_supported_gap_semantics():
    macro_gaps = [
        _macro_gap("protein_g", target_status="above_target", gap_value=None),
        _macro_gap(
            "calories",
            target_status="below_target",
            gap_value=400,
            reason_codes=["calorie_gap_available"],
        ),
        _macro_gap(
            "carbohydrate_g",
            target_status="near_target",
            gap_value=None,
        ),
        _macro_gap("fat_g", target_status="near_target", gap_value=None),
    ]

    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=[],
        summary_confidence="Moderate",
    )

    assert approved.suggestions == []
    assert "no_macro_gap_detected" not in approved.reason_codes
    assert "no_supported_suggestion_gap_available" in approved.reason_codes
    assert "no_protein_gap_available" in approved.reason_codes
    assert "calorie_gap_suggestions_not_enabled_v1" in approved.reason_codes
    assert any("Protein is not below target" in item for item in approved.limitations)


def test_protein_above_target_with_carbohydrate_gap_uses_supported_gap_semantics():
    macro_gaps = [
        _macro_gap("protein_g", target_status="above_target", gap_value=None),
        _macro_gap("calories", target_status="near_target", gap_value=None),
        _macro_gap(
            "carbohydrate_g",
            target_status="below_target",
            gap_value=75,
            reason_codes=["carbohydrate_gap_available"],
        ),
        _macro_gap("fat_g", target_status="near_target", gap_value=None),
    ]

    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=[],
        summary_confidence="Moderate",
    )

    assert approved.suggestions == []
    assert "no_macro_gap_detected" not in approved.reason_codes
    assert "no_supported_suggestion_gap_available" in approved.reason_codes
    assert "carbohydrate_gap_suggestions_not_enabled_v1" in approved.reason_codes
    assert any(
        "Carbohydrate food suggestions are not enabled" in item
        for item in approved.limitations
    )


def test_incomplete_logging_adds_cautious_limitations(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert approved.confidence == "Low"
    assert "logging_incomplete_limits_suggestions" in approved.reason_codes
    assert any(
        "logging appears incomplete" in limitation
        for limitation in approved.limitations
    )


def test_suggestions_use_canonical_nutrient_data(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )
    chicken = next(
        suggestion
        for suggestion in approved.suggestions
        if suggestion.display_name == "Chicken Breast, Cooked, Skinless"
    )

    assert chicken.suggested_grams == 200.0
    assert chicken.estimated_calories == 330.0
    assert chicken.estimated_protein_g == 62.0
    assert chicken.estimated_carbohydrate_g == 0.0
    assert chicken.estimated_fat_g == 7.2


def test_suggested_grams_are_positive_and_within_practical_bounds(
    tmp_path, monkeypatch
):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    for suggestion in approved.suggestions:
        assert suggestion.suggested_grams > 0
        if suggestion.display_name == "Chicken Breast, Cooked, Skinless":
            assert 100 <= suggestion.suggested_grams <= 200
        if suggestion.display_name == "Whey Protein Powder, Generic":
            assert 25 <= suggestion.suggested_grams <= 35


def test_estimated_nutrients_are_non_negative(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    for suggestion in approved.suggestions:
        assert (
            suggestion.estimated_calories is not None
            and suggestion.estimated_calories >= 0
        )
        assert (
            suggestion.estimated_protein_g is not None
            and suggestion.estimated_protein_g >= 0
        )
        assert (
            suggestion.estimated_carbohydrate_g is not None
            and suggestion.estimated_carbohydrate_g >= 0
        )
        assert (
            suggestion.estimated_fat_g is not None and suggestion.estimated_fat_g >= 0
        )


def test_foods_with_incomplete_nutrients_are_excluded(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    incomplete_food = create_canonical_food(
        "Incomplete Protein Canonical Food",
        "generic",
        search_priority=1,
    )
    create_canonical_food_nutrient(incomplete_food.id, "Protein", "g", 95)
    chicken_id = _canonical_id_for_query("chicken breast")
    add_canonical_food_entry(1, chicken_id, 100, "2026-06-06")
    summary = build_target_vs_actual_nutrition_summary(
        1,
        "2026-06-06",
        nutrition_targets=_approved_targets(),
    )
    gaps = build_nutrition_macro_gaps(summary)

    candidates = get_canonical_food_suggestion_candidates(gaps)

    assert all(
        candidate.canonical_food_id != incomplete_food.id for candidate in candidates
    )


def test_blocked_calorie_carb_fat_targets_do_not_generate_hard_suggestions(
    tmp_path, monkeypatch
):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert all(
        suggestion.macro_gap_addressed == "protein_g"
        for suggestion in approved.suggestions
    )
    blocked_macros = {
        gap.macro_name
        for gap in approved.macro_gaps
        if gap.target_status in {"limited", "unavailable", TARGET_STATUS_UNAVAILABLE}
    }
    assert {"calories", "carbohydrate_g", "fat_g"}.issubset(blocked_macros)


def test_ranking_is_deterministic(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)
    gaps = build_nutrition_macro_gaps(summary)
    candidates = get_canonical_food_suggestion_candidates(gaps)

    first = rank_food_suggestion_candidates(candidates, limit=5)
    second = rank_food_suggestion_candidates(list(reversed(candidates)), limit=5)

    assert [candidate.canonical_food_id for candidate in first] == [
        candidate.canonical_food_id for candidate in second
    ]


def test_no_forbidden_language_appears(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )
    text = " ".join(
        [suggestion.suggestion_summary for suggestion in approved.suggestions]
        + approved.reason_codes
        + approved.limitations
    ).lower()

    forbidden_terms = [
        "you must eat",
        "you failed",
        "burn this off",
        "skip meals",
        "compensate tomorrow",
        "fat-loss guarantee",
        "exact physiological certainty",
    ]
    assert not any(term in text for term in forbidden_terms)


def test_approve_food_suggestions_can_represent_no_suitable_food(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)
    gaps = build_nutrition_macro_gaps(summary)

    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=gaps,
        candidates=[],
        summary_confidence=summary.confidence,
    )

    assert approved.suggestions == []
    assert "no_suitable_canonical_food_found" in approved.reason_codes
    assert approved.limitations
