from __future__ import annotations

from datetime import date as date_cls

from fastapi.testclient import TestClient

import api.routes.nutrition_food_suggestions as food_suggestion_route
from api.main import app
from models.nutrition_food_suggestion_models import (
    ApprovedFoodSuggestion,
    ApprovedNutritionFoodSuggestions,
    NutritionMacroGap,
)


def _protein_gap() -> NutritionMacroGap:
    return NutritionMacroGap(
        macro_name="protein_g",
        target_value=150,
        actual_value=110,
        gap_value=40,
        unit="g",
        target_status="below_target",
        display_allowed=True,
        confidence="Moderate",
        reason_codes=["protein_gap_available"],
        limitations=[],
    )


def _blocked_gap(macro_name: str) -> NutritionMacroGap:
    return NutritionMacroGap(
        macro_name=macro_name,
        target_value=None,
        actual_value=None,
        gap_value=None,
        unit="kcal" if macro_name == "calories" else "g",
        target_status="limited",
        display_allowed=False,
        confidence="Low",
        reason_codes=["target_not_approved"],
        limitations=[f"{macro_name} target is limited."],
    )


def _approved_suggestion_response(
    *,
    user_id: int = 1,
    suggestion_date: str = "2026-06-06",
    suggestions: list[ApprovedFoodSuggestion] | None = None,
    primary_gap: str | None = "protein_g",
    reason_codes: list[str] | None = None,
    limitations: list[str] | None = None,
    confidence: str = "Low",
) -> ApprovedNutritionFoodSuggestions:
    macro_gaps = [
        _protein_gap(),
        _blocked_gap("calories"),
        _blocked_gap("carbohydrate_g"),
        _blocked_gap("fat_g"),
    ]
    return ApprovedNutritionFoodSuggestions(
        user_id=user_id,
        suggestion_date=suggestion_date,
        primary_gap=primary_gap,
        macro_gaps=macro_gaps,
        suggestions=suggestions if suggestions is not None else [_chicken_suggestion()],
        confidence=confidence,
        reason_codes=reason_codes or ["protein_gap_available"],
        limitations=limitations
        or ["Suggestions are limited because logging appears incomplete."],
    )


def _chicken_suggestion() -> ApprovedFoodSuggestion:
    return ApprovedFoodSuggestion(
        canonical_food_id=1,
        display_name="Chicken Breast, Cooked, Skinless",
        suggested_grams=150,
        estimated_calories=247.5,
        estimated_protein_g=46.5,
        estimated_carbohydrate_g=0,
        estimated_fat_g=5.4,
        macro_gap_addressed="protein_g",
        suggestion_summary=(
            "150g Chicken Breast, Cooked, Skinless adds about 46.5g protein."
        ),
        confidence="Moderate",
        reason_codes=[
            "canonical_food_catalog_available",
            "canonical_food_nutrients_available",
            "protein_suggestion_available",
        ],
        limitations=[],
    )


def _patch_user_and_service(monkeypatch, approved: ApprovedNutritionFoodSuggestions):
    monkeypatch.setattr(
        food_suggestion_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )
    monkeypatch.setattr(
        food_suggestion_route,
        "build_approved_nutrition_food_suggestions",
        lambda user_id, suggestion_date: approved,
    )


def test_food_suggestions_endpoint_returns_approved_protein_suggestions(monkeypatch):
    approved = _approved_suggestion_response()
    _patch_user_and_service(monkeypatch, approved)

    client = TestClient(app)
    response = client.get("/nutrition/1/food-suggestions?date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["suggestion_date"] == "2026-06-06"
    assert payload["primary_gap"] == "protein_g"
    assert payload["suggestions"]
    assert payload["suggestions"][0]["canonical_food_id"] == 1
    assert payload["suggestions"][0]["macro_gap_addressed"] == "protein_g"


def test_food_suggestions_endpoint_returns_no_suggestion_state(monkeypatch):
    approved = _approved_suggestion_response(
        suggestions=[],
        primary_gap=None,
        reason_codes=["no_macro_gap_detected"],
        limitations=["No approved macro gap is available for food suggestions."],
    )
    _patch_user_and_service(monkeypatch, approved)

    client = TestClient(app)
    response = client.get("/nutrition/1/food-suggestions?date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    assert payload["suggestions"] == []
    assert payload["primary_gap"] is None
    assert "no_macro_gap_detected" in payload["reason_codes"]
    assert payload["limitations"]


def test_food_suggestions_endpoint_returns_limitations_for_incomplete_logging(
    monkeypatch,
):
    approved = _approved_suggestion_response(
        reason_codes=[
            "protein_gap_available",
            "logging_incomplete_limits_suggestions",
        ],
        limitations=["Suggestions are limited because logging appears incomplete."],
        confidence="Low",
    )
    _patch_user_and_service(monkeypatch, approved)

    client = TestClient(app)
    response = client.get("/nutrition/1/food-suggestions?date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    assert payload["confidence"] == "Low"
    assert "logging_incomplete_limits_suggestions" in payload["reason_codes"]
    assert any("logging appears incomplete" in item for item in payload["limitations"])


def test_food_suggestions_endpoint_returns_no_protein_suggestions_when_blocked(
    monkeypatch,
):
    approved = ApprovedNutritionFoodSuggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        primary_gap=None,
        macro_gaps=[
            _blocked_gap("protein_g"),
            _blocked_gap("calories"),
            _blocked_gap("carbohydrate_g"),
            _blocked_gap("fat_g"),
        ],
        suggestions=[],
        confidence="Limited",
        reason_codes=["target_not_approved"],
        limitations=["Protein food suggestions require an approved protein target."],
    )
    _patch_user_and_service(monkeypatch, approved)

    client = TestClient(app)
    response = client.get("/nutrition/1/food-suggestions?date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    assert payload["suggestions"] == []
    assert payload["macro_gaps"][0]["macro_name"] == "protein_g"
    assert payload["macro_gaps"][0]["display_allowed"] is False
    assert "target_not_approved" in payload["reason_codes"]


def test_food_suggestions_endpoint_defaults_to_today(monkeypatch):
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        food_suggestion_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(
        user_id: int, suggestion_date: str
    ) -> ApprovedNutritionFoodSuggestions:
        captured["date"] = suggestion_date
        return _approved_suggestion_response(suggestion_date=suggestion_date)

    monkeypatch.setattr(
        food_suggestion_route,
        "build_approved_nutrition_food_suggestions",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/food-suggestions")

    assert response.status_code == 200
    assert captured["date"] == date_cls.today().isoformat()
    assert response.json()["suggestion_date"] == date_cls.today().isoformat()


def test_food_suggestions_endpoint_supports_explicit_date(monkeypatch):
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        food_suggestion_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(
        user_id: int, suggestion_date: str
    ) -> ApprovedNutritionFoodSuggestions:
        captured["date"] = suggestion_date
        return _approved_suggestion_response(suggestion_date=suggestion_date)

    monkeypatch.setattr(
        food_suggestion_route,
        "build_approved_nutrition_food_suggestions",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/food-suggestions?date=2026-06-01")

    assert response.status_code == 200
    assert captured["date"] == "2026-06-01"
    assert response.json()["suggestion_date"] == "2026-06-01"


def test_food_suggestions_endpoint_rejects_invalid_date(monkeypatch):
    monkeypatch.setattr(
        food_suggestion_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/food-suggestions?date=06-06-2026")

    assert response.status_code == 400
    assert response.json()["detail"] == "date must use YYYY-MM-DD format."


def test_food_suggestions_endpoint_returns_404_for_nonexistent_user(monkeypatch):
    monkeypatch.setattr(food_suggestion_route, "get_user_profile", lambda user_id: None)

    client = TestClient(app)
    response = client.get("/nutrition/9999/food-suggestions?date=2026-06-06")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_food_suggestions_endpoint_does_not_expose_raw_source_payloads(monkeypatch):
    approved = _approved_suggestion_response()
    _patch_user_and_service(monkeypatch, approved)

    client = TestClient(app)
    response = client.get("/nutrition/1/food-suggestions?date=2026-06-06")

    assert response.status_code == 200
    payload_text = str(response.json()).lower()
    forbidden_terms = [
        "source_payload_json",
        "raw_food_source_records",
        "food_entries",
        "sql",
        "stack trace",
        "crewai",
        "ollama",
        "provider",
        "ai-generated",
    ]
    assert not any(term in payload_text for term in forbidden_terms)


def test_food_suggestions_endpoint_uses_canonical_nutrient_estimates(monkeypatch):
    approved = _approved_suggestion_response()
    _patch_user_and_service(monkeypatch, approved)

    client = TestClient(app)
    response = client.get("/nutrition/1/food-suggestions?date=2026-06-06")

    suggestion = response.json()["suggestions"][0]
    assert suggestion["estimated_calories"] == 247.5
    assert suggestion["estimated_protein_g"] == 46.5
    assert suggestion["estimated_carbohydrate_g"] == 0
    assert suggestion["estimated_fat_g"] == 5.4
    assert suggestion["suggested_grams"] > 0


def test_blocked_calorie_carb_fat_targets_do_not_create_hard_suggestions(monkeypatch):
    approved = _approved_suggestion_response()
    _patch_user_and_service(monkeypatch, approved)

    client = TestClient(app)
    response = client.get("/nutrition/1/food-suggestions?date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    assert all(
        suggestion["macro_gap_addressed"] == "protein_g"
        for suggestion in payload["suggestions"]
    )
    blocked_macro_names = {
        gap["macro_name"]
        for gap in payload["macro_gaps"]
        if gap["target_status"] == "limited"
    }
    assert {"calories", "carbohydrate_g", "fat_g"}.issubset(blocked_macro_names)


def test_food_suggestions_endpoint_returns_safe_400_for_service_validation_failure(
    monkeypatch,
):
    monkeypatch.setattr(
        food_suggestion_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )
    monkeypatch.setattr(
        food_suggestion_route,
        "build_approved_nutrition_food_suggestions",
        lambda user_id, suggestion_date: (_ for _ in ()).throw(
            ValueError("internal validator details")
        ),
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/food-suggestions?date=2026-06-06")

    assert response.status_code == 400
    assert response.json()["detail"] == "Nutrition food suggestion validation failed."
    assert "internal validator details" not in response.text
