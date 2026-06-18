from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

import api.routes.nutrition_target_vs_actual as nutrition_target_vs_actual_route
import database
from api.main import app
from models.nutrition_target_models import NutritionTargets
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    TARGET_STATUS_BELOW,
    TARGET_STATUS_NEAR,
    TARGET_STATUS_UNAVAILABLE,
)
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.nutrition_target_vs_actual_service import (
    build_approved_nutrition_guidance,
    build_nutrition_actuals,
    build_target_vs_actual_nutrition_summary,
    validate_target_vs_actual_nutrition_summary,
)
from services.user_state_service import build_user_health_state


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()


def _today() -> str:
    return date.today().isoformat()


def _future_date() -> str:
    return (date.today() + timedelta(days=7)).isoformat()


def _limited_targets() -> NutritionTargets:
    return NutritionTargets(
        body_weight_lb=190,
        calorie_target_min=2200,
        calorie_target_max=2500,
        protein_grams_min=140,
        protein_grams_max=180,
        carbohydrate_grams_min=180,
        carbohydrate_grams_max=260,
        fat_grams_min=60,
        fat_grams_max=90,
        confidence="Limited",
        allow_calorie_targets=False,
        allow_protein_targets=True,
        allow_carbohydrate_targets=False,
        allow_fat_targets=False,
        nutrition_display_message="Nutrition targets are limited.",
        reason_codes=["unit_test_limited_targets"],
    )


def _approved_targets(
    *, calories: bool = True, macros: bool = True
) -> NutritionTargets:
    return NutritionTargets(
        body_weight_lb=178,
        calorie_target_min=2200,
        calorie_target_max=2500,
        protein_grams_min=130,
        protein_grams_max=180,
        carbohydrate_grams_min=180,
        carbohydrate_grams_max=280,
        fat_grams_min=55,
        fat_grams_max=90,
        confidence="High",
        allow_calorie_targets=calories,
        allow_protein_targets=True,
        allow_carbohydrate_targets=macros,
        allow_fat_targets=macros,
        nutrition_display_message="Unit test targets.",
        reason_codes=["unit_test_approved_targets"],
    )


def _food_id(name: str) -> int:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM foods WHERE name = ?", (name,))
    food_id = cursor.fetchone()["id"]
    conn.close()
    return int(food_id)


def _insert_food_entry(
    user_id: int, food_name: str, grams: float, entry_date: str
) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO food_entries (user_id, food_id, grams, entry_date)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, _food_id(food_name), grams, entry_date),
    )
    conn.commit()
    conn.close()


def _set_user_field(user_id: int, field_name: str, value) -> None:
    allowed_fields = {
        "gender",
        "age",
        "height_cm",
        "starting_weight",
        "goal_weight",
        "primary_goal",
        "activity_level",
    }
    if field_name not in allowed_fields:
        raise ValueError(f"Unsupported test user field: {field_name}")

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE users SET {field_name} = ? WHERE id = ?",
        (value, user_id),
    )
    conn.commit()
    conn.close()


def test_no_logs_returns_limited_confidence_and_safe_limitations(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(102, _future_date())
    guidance = build_approved_nutrition_guidance(summary)

    assert summary.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS
    assert summary.confidence == "Limited"
    assert "no_nutrition_logs_today" in summary.reason_codes
    assert "nutrition_actuals_unavailable" in summary.reason_codes
    assert summary.comparisons["protein"].target_status == TARGET_STATUS_UNAVAILABLE
    assert "No nutrition logs" in guidance.summary_message
    assert validate_target_vs_actual_nutrition_summary(summary, guidance) == []


def test_partial_logs_limit_calorie_conclusions(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        101,
        _today(),
        nutrition_targets=_approved_targets(),
    )
    guidance = build_approved_nutrition_guidance(summary)

    assert summary.logging_completeness in {
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    }
    assert summary.comparisons["calories"].comparison_available is False
    assert "calorie_delta_not_available" in summary.reason_codes
    assert "calorie conclusions should stay limited" in guidance.calorie_guidance
    assert validate_target_vs_actual_nutrition_summary(summary, guidance) == []


def test_protein_comparison_works_when_protein_target_is_approved(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(),
    )
    protein = summary.comparisons["protein"]

    assert protein.comparison_available is True
    assert protein.actual is not None
    assert protein.target_status in {TARGET_STATUS_BELOW, TARGET_STATUS_NEAR}
    assert "protein_target_available" in protein.reason_codes
    assert validate_target_vs_actual_nutrition_summary(summary) == []


def test_calorie_comparison_is_blocked_when_calorie_targets_not_approved(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(calories=False),
    )

    assert summary.comparisons["calories"].comparison_available is False
    assert summary.comparisons["calories"].target_status == TARGET_STATUS_UNAVAILABLE
    assert "calorie_target_unavailable" in summary.comparisons["calories"].reason_codes


def test_carbs_and_fats_compare_only_when_display_flags_and_confidence_allow(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    allowed_summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(macros=True),
    )
    blocked_summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(macros=False),
    )

    assert allowed_summary.comparisons["carbs"].comparison_available is True
    assert allowed_summary.comparisons["fat"].comparison_available is True
    assert blocked_summary.comparisons["carbs"].comparison_available is False
    assert blocked_summary.comparisons["fat"].comparison_available is False


def test_missing_nutrient_fields_are_tracked_and_not_coerced_to_zero(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    actuals = build_nutrition_actuals(105, _today())
    summary = build_target_vs_actual_nutrition_summary(
        105,
        _today(),
        nutrition_targets=_limited_targets(),
    )

    assert actuals.entry_count > 0
    assert actuals.logged_calories is None
    assert actuals.logged_protein is not None
    assert actuals.missing_calorie_entries == actuals.entry_count
    assert "missing_calorie_values" in actuals.reason_codes
    assert "calories" in summary.logging_summary.missing_nutrient_fields
    assert summary.comparisons["calories"].comparison_available is False


def test_incomplete_logging_limits_macro_certainty(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        105,
        _today(),
        nutrition_targets=_approved_targets(),
    )
    guidance = build_approved_nutrition_guidance(summary)

    assert summary.logging_completeness in {
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    }
    assert "macro_targets_limited_by_logging_quality" in summary.reason_codes
    assert "Macro comparisons are limited" in guidance.macro_guidance


def test_low_entry_and_meal_count_reason_codes_appear(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    single_entry_date = (date.today() - timedelta(days=5)).isoformat()
    _insert_food_entry(102, "QA Recovery Shake", 100, single_entry_date)

    summary = build_target_vs_actual_nutrition_summary(
        102,
        single_entry_date,
        nutrition_targets=_approved_targets(),
    )

    assert summary.logging_completeness == LOGGING_COMPLETENESS_PARTIAL_DAY
    assert "entry_count_low" in summary.reason_codes
    assert "meal_count_low" in summary.reason_codes


def test_training_day_context_can_be_included_as_context_only(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(),
        training_day_context_available=True,
    )
    guidance = build_approved_nutrition_guidance(summary)
    combined = str(guidance.to_dict()).lower()

    assert "training_day_context_available" in summary.reason_codes
    assert "caused your workout" not in combined
    assert "caused poor performance" not in combined


def test_guidance_avoids_shame_restriction_medical_and_stalled_fat_loss_language(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        105,
        _today(),
        nutrition_targets=_limited_targets(),
    )
    guidance = build_approved_nutrition_guidance(summary)
    combined = str(guidance.to_dict()).lower()

    forbidden = [
        "you failed",
        "bad food",
        "medical",
        "supplement",
        "stalled fat loss",
        "must cut calories",
        "skip meals",
        "compensate tomorrow",
        "burn this off",
    ]
    assert not any(term in combined for term in forbidden)
    assert validate_target_vs_actual_nutrition_summary(summary, guidance) == []


def test_deterministic_output_remains_stable(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    first = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(),
    )
    second = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(),
    )

    assert first.to_dict() == second.to_dict()


def test_complete_enough_logs_can_compare_calories_cautiously(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _insert_food_entry(102, "QA Complete Performance Meal", 100, _today())

    summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(),
    )

    assert summary.logging_completeness == LOGGING_COMPLETENESS_COMPLETE_ENOUGH
    assert summary.comparisons["calories"].comparison_available is True
    assert "calorie_target_available" in summary.comparisons["calories"].reason_codes


@pytest.mark.parametrize("user_id", [101, 102, 103, 104, 105])
def test_seeded_users_build_safe_target_vs_actual_summaries(
    user_id, tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    health_state = build_user_health_state(user_id)

    summary = build_target_vs_actual_nutrition_summary(
        user_id,
        _today(),
        health_state=health_state,
    )
    guidance = build_approved_nutrition_guidance(summary)
    violations = validate_target_vs_actual_nutrition_summary(summary, guidance)

    assert summary.user_id == user_id
    assert summary.nutrition_actuals.user_id == user_id
    assert set(summary.comparisons) == {"calories", "protein", "carbs", "fat"}
    assert violations == []


def test_target_vs_actual_uses_formula_derived_protein_target_by_default(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(102, _today())
    protein = summary.comparisons["protein"]

    assert "formula_derived_targets" in summary.reason_codes
    assert protein.target_min is not None
    assert protein.target_max is not None
    assert protein.comparison_available is True
    assert "protein_target_available" in protein.reason_codes


def test_formula_protein_only_comparison_works_when_calories_are_blocked(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(102, _today())

    assert summary.comparisons["protein"].comparison_available is True
    assert summary.comparisons["calories"].comparison_available is False
    assert summary.comparisons["carbs"].comparison_available is False
    assert summary.comparisons["fat"].comparison_available is False
    assert "missing_sex" in summary.reason_codes
    assert "calorie_target_unavailable" in summary.comparisons["calories"].reason_codes
    assert "carbs_target_unavailable" in summary.comparisons["carbs"].reason_codes


def test_missing_body_weight_blocks_formula_protein_comparison(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    health_state = build_user_health_state(102)
    health_state.latest_body_weight = "Unknown"
    health_state.starting_weight = None

    summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        health_state=health_state,
    )

    protein = summary.comparisons["protein"]
    assert protein.comparison_available is False
    assert protein.target_min is None
    assert protein.target_max is None
    assert "missing_body_weight" in summary.reason_codes
    assert "protein_target_unavailable" in protein.reason_codes


@pytest.mark.parametrize(
    ("field_name", "expected_reason"),
    [
        ("height_cm", "missing_height"),
        ("age", "missing_age"),
        ("activity_level", "missing_activity_level"),
        ("primary_goal", "missing_primary_goal"),
    ],
)
def test_missing_formula_profile_fields_block_or_limit_calorie_comparison(
    field_name, expected_reason, tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    _set_user_field(102, "gender", "Male")
    _set_user_field(102, field_name, None)

    summary = build_target_vs_actual_nutrition_summary(102, _today())

    calories = summary.comparisons["calories"]
    assert calories.comparison_available is False
    assert calories.target_min is None
    assert calories.target_max is None
    assert expected_reason in summary.reason_codes


def test_complete_formula_targets_and_complete_logs_compare_all_macros(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    _set_user_field(102, "gender", "Male")
    _insert_food_entry(102, "QA Complete Performance Meal", 100, _today())

    summary = build_target_vs_actual_nutrition_summary(102, _today())

    assert summary.logging_completeness == LOGGING_COMPLETENESS_COMPLETE_ENOUGH
    assert summary.comparisons["calories"].comparison_available is True
    assert summary.comparisons["protein"].comparison_available is True
    assert summary.comparisons["carbs"].comparison_available is True
    assert summary.comparisons["fat"].comparison_available is True
    assert "calorie_target_available" in summary.comparisons["calories"].reason_codes
    assert "formula_derived_targets" in summary.reason_codes


def test_formula_metadata_limitations_inform_summary_without_public_internals(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(105, _today())
    combined = str(summary.to_dict()).lower()

    assert "formula_derived_targets" in summary.reason_codes
    assert summary.limitations
    assert "validator" not in combined
    assert "raw" not in combined
    assert "crewai" not in combined
    assert "ollama" not in combined
    assert "medical" not in combined


_PUBLIC_NUTRITION_TARGET_VS_ACTUAL_TOP_LEVEL_KEYS = {
    "success",
    "user_id",
    "date",
    "nutrition_actuals",
    "logging_summary",
    "target_vs_actual_summary",
    "approved_nutrition_guidance",
    "logging_completeness",
    "confidence",
    "reason_codes",
    "limitations",
}

_PUBLIC_NUTRITION_TARGET_VS_ACTUAL_FORBIDDEN_KEYS = {
    "raw_food_entries",
    "food_entries",
    "raw_foods",
    "raw_food_nutrients",
    "raw_nutrients",
    "raw_sql",
    "debug_payload",
    "validator_internals",
    "validation_errors",
    "stack_trace",
    "traceback",
    "provider_metadata",
    "crewai",
    "ollama",
    "unbounded_history",
    "private_notes",
}


def _collect_keys(value):
    keys = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(key)
            keys.update(_collect_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(_collect_keys(nested))
    return keys


def test_target_vs_actual_endpoint_returns_public_contract_for_user_with_logs(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get(f"/nutrition/102/target-vs-actual?date={_today()}")
    payload = response.json()

    assert response.status_code == 200
    assert set(payload) == _PUBLIC_NUTRITION_TARGET_VS_ACTUAL_TOP_LEVEL_KEYS
    assert payload["success"] is True
    assert payload["user_id"] == 102
    assert payload["date"] == _today()
    assert payload["nutrition_actuals"]["user_id"] == 102
    assert payload["logging_summary"]["user_id"] == 102
    assert payload["target_vs_actual_summary"]["comparisons"]
    assert payload["approved_nutrition_guidance"]["summary_message"]


def test_target_vs_actual_endpoint_returns_safe_no_logs_response(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get(f"/nutrition/102/target-vs-actual?date={_future_date()}")
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["logging_completeness"] == LOGGING_COMPLETENESS_NO_LOGS
    assert payload["confidence"] == "Limited"
    assert "no_nutrition_logs_today" in payload["reason_codes"]
    assert payload["nutrition_actuals"]["entry_count"] == 0
    assert (
        "No nutrition logs" in payload["approved_nutrition_guidance"]["summary_message"]
    )


def test_target_vs_actual_endpoint_supports_explicit_date_query_parameter(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    explicit_date = _future_date()
    client = TestClient(app)

    response = client.get(f"/nutrition/102/target-vs-actual?date={explicit_date}")

    assert response.status_code == 200
    assert response.json()["date"] == explicit_date


def test_target_vs_actual_endpoint_defaults_to_today_when_date_is_omitted(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/nutrition/102/target-vs-actual")

    assert response.status_code == 200
    assert response.json()["date"] == _today()


def test_target_vs_actual_endpoint_rejects_invalid_date_format(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/nutrition/102/target-vs-actual?date=not-a-date")

    assert response.status_code == 400
    assert "yyyy-mm-dd" in response.json()["detail"].lower()


def test_target_vs_actual_endpoint_nonexistent_user_returns_safe_404(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get(f"/nutrition/999999/target-vs-actual?date={_today()}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_target_vs_actual_endpoint_validation_failure_returns_safe_400(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    monkeypatch.setattr(
        nutrition_target_vs_actual_route,
        "validate_target_vs_actual_nutrition_summary",
        lambda summary, guidance: ["forced validation failure"],
    )
    client = TestClient(app)

    response = client.get(f"/nutrition/102/target-vs-actual?date={_today()}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Nutrition target-vs-actual validation failed."
    assert "forced validation failure" not in str(response.json())


def test_target_vs_actual_endpoint_does_not_expose_raw_or_internal_fields(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get(f"/nutrition/102/target-vs-actual?date={_today()}")
    payload = response.json()

    assert response.status_code == 200
    assert not (
        _collect_keys(payload) & _PUBLIC_NUTRITION_TARGET_VS_ACTUAL_FORBIDDEN_KEYS
    )


def test_target_vs_actual_endpoint_protein_comparison_requires_approved_target_and_logs(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    logged_response = client.get(f"/nutrition/102/target-vs-actual?date={_today()}")
    no_log_response = client.get(
        f"/nutrition/102/target-vs-actual?date={_future_date()}"
    )

    logged_protein = logged_response.json()["target_vs_actual_summary"]["comparisons"][
        "protein"
    ]
    no_log_protein = no_log_response.json()["target_vs_actual_summary"]["comparisons"][
        "protein"
    ]

    assert logged_response.status_code == 200
    assert logged_protein["comparison_available"] is True
    assert "protein_target_available" in logged_protein["reason_codes"]
    assert no_log_protein["comparison_available"] is False
    assert no_log_protein["target_status"] == TARGET_STATUS_UNAVAILABLE


def test_target_vs_actual_endpoint_calorie_comparison_limited_when_needed(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get(f"/nutrition/101/target-vs-actual?date={_today()}")
    payload = response.json()
    calories = payload["target_vs_actual_summary"]["comparisons"]["calories"]
    guidance = payload["approved_nutrition_guidance"]

    assert response.status_code == 200
    assert calories["comparison_available"] is False
    assert calories["target_status"] == TARGET_STATUS_UNAVAILABLE
    assert "calorie" in guidance["calorie_guidance"].lower()
    assert "limited" in guidance["calorie_guidance"].lower()


def test_target_vs_actual_endpoint_missing_nutrients_remain_tracked_not_zero(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get(f"/nutrition/105/target-vs-actual?date={_today()}")
    payload = response.json()
    actuals = payload["nutrition_actuals"]

    assert response.status_code == 200
    assert actuals["entry_count"] > 0
    assert actuals["logged_calories"] is None
    assert actuals["missing_calorie_entries"] == actuals["entry_count"]
    assert "missing_calorie_values" in actuals["reason_codes"]


def test_target_vs_actual_endpoint_avoids_unsafe_nutrition_language(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get(f"/nutrition/105/target-vs-actual?date={_today()}")
    combined = str(response.json()).lower()

    assert response.status_code == 200
    for term in [
        "you failed",
        "bad food",
        "medical",
        "supplement",
        "stalled fat loss",
        "must cut calories",
        "skip meals",
        "compensate tomorrow",
        "burn this off",
    ]:
        assert term not in combined


def test_target_vs_actual_endpoint_keeps_recommendation_and_daily_coach_shapes_stable(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    recommendation_response = client.get("/recommendations/daily/102")
    daily_coach_response = client.get("/daily-coach/102/synthesis")

    assert recommendation_response.status_code == 200
    assert set(recommendation_response.json()) == {
        "success",
        "user_id",
        "scenario",
        "confidence",
        "nutrition_targets",
        "training_constraints",
        "approved_action_plan",
        "rendered_recommendation",
    }
    assert daily_coach_response.status_code == 200
    assert set(daily_coach_response.json()) == {
        "success",
        "user_id",
        "synthesis_date",
        "scenario",
        "confidence",
        "daily_coach_synthesis",
    }
