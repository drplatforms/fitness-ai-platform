from __future__ import annotations

from datetime import date as date_cls
from datetime import timedelta

from fastapi.testclient import TestClient

import api.routes.nutrition_trend as nutrition_trend_route
from api.main import app
from models.nutrition_trend_models import (
    BODYWEIGHT_TREND_STABLE,
    BODYWEIGHT_TREND_UNAVAILABLE,
    CALIBRATION_READINESS_NOT_READY,
    CALIBRATION_READINESS_USABLE,
    LOGGING_CONSISTENCY_INSUFFICIENT,
    LOGGING_CONSISTENCY_USABLE,
    BodyweightTrendSummary,
    NutritionCalibrationReadiness,
    NutritionIntakeTrendSummary,
    NutritionTrendWindow,
)


def _trend_window(
    *,
    user_id: int = 1,
    end_date: str = "2026-06-06",
    window_days: int = 28,
    logged_day_count: int = 10,
    complete_logging_day_count: int = 8,
    partial_logging_day_count: int = 2,
    bodyweight_available: bool = True,
    readiness_level: str = CALIBRATION_READINESS_USABLE,
) -> NutritionTrendWindow:
    start = date_cls.fromisoformat(end_date) - timedelta(days=window_days - 1)
    no_log_day_count = window_days - logged_day_count
    if bodyweight_available:
        bodyweight_summary = BodyweightTrendSummary(
            weigh_in_count=6,
            start_weight_lb=190.0,
            end_weight_lb=189.0,
            average_weight_lb=189.5,
            trend_direction=BODYWEIGHT_TREND_STABLE,
            weekly_rate_lb=-0.2,
            confidence="Low",
            reason_codes=["bodyweight_trend_available"],
            limitations=[
                "Bodyweight trend is available but based on limited weigh-ins."
            ],
        )
    else:
        bodyweight_summary = BodyweightTrendSummary(
            trend_direction=BODYWEIGHT_TREND_UNAVAILABLE,
            confidence="Limited",
            reason_codes=["bodyweight_trend_unavailable"],
            limitations=[
                "At least two bodyweight entries are needed for trend direction."
            ],
        )

    if readiness_level == CALIBRATION_READINESS_USABLE:
        readiness = NutritionCalibrationReadiness(
            calibration_allowed=True,
            readiness_level=CALIBRATION_READINESS_USABLE,
            minimum_window_met=True,
            preferred_window_met=window_days >= 28,
            logging_quality_met=True,
            bodyweight_trend_available=bodyweight_available,
            goal_context_available=True,
            training_context_available=True,
            reason_codes=["calibration_usable"],
            limitations=[],
        )
        confidence = "Moderate"
    else:
        readiness = NutritionCalibrationReadiness(
            calibration_allowed=False,
            readiness_level=CALIBRATION_READINESS_NOT_READY,
            minimum_window_met=window_days >= 14,
            preferred_window_met=window_days >= 28,
            logging_quality_met=False,
            bodyweight_trend_available=bodyweight_available,
            goal_context_available=True,
            training_context_available=False,
            reason_codes=["calibration_not_ready"],
            limitations=["Trend evidence is not ready for calibration."],
        )
        confidence = "Limited"

    if logged_day_count > 0:
        intake_summary = NutritionIntakeTrendSummary(
            average_calories=2100.0,
            average_protein_g=150.0,
            average_carbohydrate_g=240.0,
            average_fat_g=70.0,
            complete_logging_rate=round(complete_logging_day_count / window_days, 3),
            logging_consistency_status=LOGGING_CONSISTENCY_USABLE,
            confidence="Moderate",
            reason_codes=["logging_quality_usable"],
            limitations=[],
        )
    else:
        intake_summary = NutritionIntakeTrendSummary(
            complete_logging_rate=0.0,
            logging_consistency_status=LOGGING_CONSISTENCY_INSUFFICIENT,
            confidence="Limited",
            reason_codes=["logging_quality_insufficient"],
            limitations=[
                "Logging consistency is not strong enough for nutrition target calibration."
            ],
        )
        confidence = "Limited"

    return NutritionTrendWindow(
        user_id=user_id,
        start_date=start.isoformat(),
        end_date=end_date,
        window_days=window_days,
        logged_day_count=logged_day_count,
        complete_logging_day_count=complete_logging_day_count,
        partial_logging_day_count=partial_logging_day_count,
        no_log_day_count=no_log_day_count,
        intake_trend_summary=intake_summary,
        bodyweight_trend_summary=bodyweight_summary,
        calibration_readiness=readiness,
        confidence=confidence,
        reason_codes=["trend_window_created", "preferred_window_met"],
        limitations=([] if confidence != "Limited" else ["Trend evidence is limited."]),
    )


def _patch_user_and_service(monkeypatch, trend_window: NutritionTrendWindow):
    monkeypatch.setattr(
        nutrition_trend_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )
    monkeypatch.setattr(
        nutrition_trend_route,
        "build_nutrition_trend_window",
        lambda *, user_id, end_date, window_days: trend_window,
    )


def test_trend_window_endpoint_returns_14_day_window(monkeypatch):
    trend_window = _trend_window(window_days=14, end_date="2026-06-06")
    _patch_user_and_service(monkeypatch, trend_window)

    client = TestClient(app)
    response = client.get(
        "/nutrition/1/trend-window?end_date=2026-06-06&window_days=14"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["window_days"] == 14
    assert payload["start_date"] == "2026-05-24"


def test_trend_window_endpoint_returns_28_day_window(monkeypatch):
    trend_window = _trend_window(window_days=28, end_date="2026-06-06")
    _patch_user_and_service(monkeypatch, trend_window)

    client = TestClient(app)
    response = client.get(
        "/nutrition/1/trend-window?end_date=2026-06-06&window_days=28"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["window_days"] == 28
    assert payload["logged_day_count"] == 10
    assert payload["complete_logging_day_count"] == 8
    assert payload["partial_logging_day_count"] == 2
    assert payload["no_log_day_count"] == 18


def test_trend_window_endpoint_defaults_end_date_to_today(monkeypatch):
    captured: dict[str, str | int] = {}

    monkeypatch.setattr(
        nutrition_trend_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(
        *, user_id: int, end_date: str, window_days: int
    ) -> NutritionTrendWindow:
        captured["end_date"] = end_date
        captured["window_days"] = window_days
        return _trend_window(end_date=end_date, window_days=window_days)

    monkeypatch.setattr(
        nutrition_trend_route,
        "build_nutrition_trend_window",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/trend-window")

    assert response.status_code == 200
    assert captured["end_date"] == date_cls.today().isoformat()
    assert captured["window_days"] == 28


def test_trend_window_endpoint_invalid_date_returns_safe_400(monkeypatch):
    _patch_user_and_service(monkeypatch, _trend_window())

    client = TestClient(app)
    response = client.get("/nutrition/1/trend-window?end_date=06-06-2026")

    assert response.status_code == 400
    assert response.json()["detail"] == "end_date must use YYYY-MM-DD format."


def test_trend_window_endpoint_invalid_window_days_returns_safe_400(monkeypatch):
    _patch_user_and_service(monkeypatch, _trend_window())

    client = TestClient(app)
    response = client.get("/nutrition/1/trend-window?window_days=21")

    assert response.status_code == 400
    assert response.json()["detail"] == "window_days must be 14 or 28."


def test_trend_window_endpoint_nonexistent_user_returns_safe_404(monkeypatch):
    monkeypatch.setattr(nutrition_trend_route, "get_user_profile", lambda user_id: None)

    client = TestClient(app)
    response = client.get("/nutrition/999/trend-window?end_date=2026-06-06")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_trend_window_endpoint_represents_no_log_days_safely(monkeypatch):
    trend_window = _trend_window(
        logged_day_count=0,
        complete_logging_day_count=0,
        partial_logging_day_count=0,
        readiness_level=CALIBRATION_READINESS_NOT_READY,
    )
    _patch_user_and_service(monkeypatch, trend_window)

    client = TestClient(app)
    response = client.get(
        "/nutrition/1/trend-window?end_date=2026-06-06&window_days=28"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["logged_day_count"] == 0
    assert payload["no_log_day_count"] == 28
    assert payload["intake_trend_summary"]["average_calories"] is None
    assert (
        "logging_quality_insufficient"
        in payload["intake_trend_summary"]["reason_codes"]
    )


def test_trend_window_endpoint_represents_unavailable_bodyweight_trend(monkeypatch):
    trend_window = _trend_window(
        bodyweight_available=False,
        readiness_level=CALIBRATION_READINESS_NOT_READY,
    )
    _patch_user_and_service(monkeypatch, trend_window)

    client = TestClient(app)
    response = client.get(
        "/nutrition/1/trend-window?end_date=2026-06-06&window_days=28"
    )

    assert response.status_code == 200
    bodyweight_summary = response.json()["bodyweight_trend_summary"]
    assert bodyweight_summary["trend_direction"] == BODYWEIGHT_TREND_UNAVAILABLE
    assert bodyweight_summary["start_weight_lb"] is None
    assert bodyweight_summary["end_weight_lb"] is None
    assert "bodyweight_trend_unavailable" in bodyweight_summary["reason_codes"]


def test_trend_window_endpoint_includes_readiness_without_target_mutation(monkeypatch):
    _patch_user_and_service(monkeypatch, _trend_window())

    client = TestClient(app)
    response = client.get("/nutrition/1/trend-window?end_date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    assert (
        payload["calibration_readiness"]["readiness_level"]
        == CALIBRATION_READINESS_USABLE
    )
    assert "target_mutation" not in payload
    assert "calibrated_targets" not in payload
    assert "approved_macro_targets" not in payload


def test_trend_window_endpoint_does_not_expose_raw_or_provider_fields(monkeypatch):
    _patch_user_and_service(monkeypatch, _trend_window())

    client = TestClient(app)
    response = client.get("/nutrition/1/trend-window?end_date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    forbidden_keys = {
        "food_entries",
        "daily_checkins",
        "raw_sql",
        "debug_payload",
        "validator_internals",
        "stack_trace",
        "provider_metadata",
        "crewai_attempted",
        "ollama_base_url",
        "target_mutation",
    }
    assert forbidden_keys.isdisjoint(payload.keys())
    assert "trend_days" not in payload
    assert "metadata" not in payload
