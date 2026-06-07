from __future__ import annotations

from datetime import date as date_cls

from fastapi.testclient import TestClient

import api.routes.nutrition_target_calibration as calibration_route
from api.main import app
from models.nutrition_trend_models import (
    CALIBRATION_READINESS_EARLY_SIGNAL,
    CALIBRATION_READINESS_NOT_READY,
    CALIBRATION_READINESS_STRONG,
    CALIBRATION_READINESS_USABLE,
)
from services.nutrition_target_calibration_service import (
    RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT,
    RECOMMENDED_ACTION_INSUFFICIENT_DATA,
    RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS,
    RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE,
    NutritionTargetCalibrationMetadata,
    NutritionTargetCalibrationResult,
)


def _calibration_result(
    *,
    user_id: int = 1,
    calibration_date: str = "2026-06-06",
    window_days: int = 28,
    readiness_level: str = CALIBRATION_READINESS_NOT_READY,
    recommended_action: str = RECOMMENDED_ACTION_INSUFFICIENT_DATA,
    calibration_allowed: bool = False,
    confidence: str = "Limited",
    reason_codes: list[str] | None = None,
    limitations: list[str] | None = None,
) -> NutritionTargetCalibrationResult:
    return NutritionTargetCalibrationResult(
        user_id=user_id,
        calibration_date=calibration_date,
        window_days=window_days,
        calibration_allowed=calibration_allowed,
        readiness_level=readiness_level,
        recommended_action=recommended_action,
        calibrated_targets=None,
        confidence=confidence,
        reason_codes=reason_codes
        or [
            "calibration_assessment_created",
            "target_mutation_not_performed",
            recommended_action,
        ],
        limitations=limitations
        or [
            "Calibration assessment is read-only and does not mutate nutrition targets.",
            "Calibration is not ready because trend evidence is incomplete.",
        ],
        metadata=NutritionTargetCalibrationMetadata(
            generated_at="2026-06-06T00:00:00Z",
            inputs_used=["formula_derived_targets", "nutrition_trend_window"],
            reason_codes=[
                "deterministic_calibration_assessment",
                "target_mutation_not_performed",
            ],
            limitations=[
                "Calibration assessment is read-only and does not mutate nutrition targets."
            ],
        ),
    )


def _patch_user_and_service(
    monkeypatch,
    result: NutritionTargetCalibrationResult,
) -> None:
    monkeypatch.setattr(
        calibration_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )
    monkeypatch.setattr(
        calibration_route,
        "build_nutrition_target_calibration_result",
        lambda *, user_id, calibration_date, window_days: result,
    )


def test_calibration_endpoint_returns_insufficient_data_for_weak_evidence(monkeypatch):
    result = _calibration_result(
        reason_codes=[
            "calibration_assessment_created",
            "target_mutation_not_performed",
            "calibration_not_ready",
            "insufficient_data",
        ],
        limitations=[
            "Calibration assessment is read-only and does not mutate nutrition targets.",
            "Calibration is not ready because trend evidence is incomplete.",
        ],
    )
    _patch_user_and_service(monkeypatch, result)

    client = TestClient(app)
    response = client.get(
        "/nutrition/1/target-calibration?end_date=2026-06-06&window_days=28"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["recommended_action"] == RECOMMENDED_ACTION_INSUFFICIENT_DATA
    assert payload["readiness_level"] == CALIBRATION_READINESS_NOT_READY
    assert payload["calibration_allowed"] is False
    assert payload["calibrated_targets"] is None


def test_calibration_endpoint_returns_not_ready_when_window_insufficient(monkeypatch):
    result = _calibration_result(
        window_days=14,
        readiness_level=CALIBRATION_READINESS_NOT_READY,
        recommended_action=RECOMMENDED_ACTION_INSUFFICIENT_DATA,
        reason_codes=[
            "calibration_assessment_created",
            "target_mutation_not_performed",
            "minimum_window_not_met",
            "calibration_not_ready",
        ],
    )
    _patch_user_and_service(monkeypatch, result)

    client = TestClient(app)
    response = client.get(
        "/nutrition/1/target-calibration?end_date=2026-06-06&window_days=14"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["window_days"] == 14
    assert "minimum_window_not_met" in payload["reason_codes"]
    assert payload["recommended_action"] == RECOMMENDED_ACTION_INSUFFICIENT_DATA


def test_calibration_endpoint_supports_14_day_window(monkeypatch):
    captured: dict[str, int | str] = {}

    monkeypatch.setattr(
        calibration_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(
        *, user_id: int, calibration_date: str, window_days: int
    ) -> NutritionTargetCalibrationResult:
        captured["calibration_date"] = calibration_date
        captured["window_days"] = window_days
        return _calibration_result(
            calibration_date=calibration_date,
            window_days=window_days,
            readiness_level=CALIBRATION_READINESS_EARLY_SIGNAL,
            recommended_action=RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE,
            confidence="Low",
            reason_codes=[
                "calibration_assessment_created",
                "target_mutation_not_performed",
                "calibration_early_signal",
            ],
            limitations=[
                "Calibration assessment is read-only and does not mutate nutrition targets.",
                "Targets remain broad because trend evidence is limited.",
            ],
        )

    monkeypatch.setattr(
        calibration_route,
        "build_nutrition_target_calibration_result",
        fake_build,
    )

    client = TestClient(app)
    response = client.get(
        "/nutrition/1/target-calibration?end_date=2026-06-06&window_days=14"
    )

    assert response.status_code == 200
    assert captured["window_days"] == 14
    assert response.json()["window_days"] == 14


def test_calibration_endpoint_supports_28_day_window(monkeypatch):
    result = _calibration_result(
        window_days=28,
        readiness_level=CALIBRATION_READINESS_USABLE,
        recommended_action=RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS,
        calibration_allowed=True,
        confidence="Moderate",
        reason_codes=[
            "calibration_assessment_created",
            "target_mutation_not_performed",
            "calibration_usable",
            "current_targets_kept",
        ],
        limitations=[
            "Calibration assessment is read-only and does not mutate nutrition targets.",
            "Current data supports keeping formula-derived targets unchanged.",
        ],
    )
    _patch_user_and_service(monkeypatch, result)

    client = TestClient(app)
    response = client.get(
        "/nutrition/1/target-calibration?end_date=2026-06-06&window_days=28"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["window_days"] == 28
    assert payload["recommended_action"] == RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS


def test_calibration_endpoint_defaults_end_date_to_today(monkeypatch):
    captured: dict[str, str | int] = {}

    monkeypatch.setattr(
        calibration_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(
        *, user_id: int, calibration_date: str, window_days: int
    ) -> NutritionTargetCalibrationResult:
        captured["calibration_date"] = calibration_date
        captured["window_days"] = window_days
        return _calibration_result(calibration_date=calibration_date)

    monkeypatch.setattr(
        calibration_route,
        "build_nutrition_target_calibration_result",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/target-calibration")

    assert response.status_code == 200
    assert captured["calibration_date"] == date_cls.today().isoformat()
    assert captured["window_days"] == 28


def test_calibration_endpoint_invalid_date_returns_safe_400(monkeypatch):
    _patch_user_and_service(monkeypatch, _calibration_result())

    client = TestClient(app)
    response = client.get("/nutrition/1/target-calibration?end_date=06-06-2026")

    assert response.status_code == 400
    assert response.json()["detail"] == "end_date must use YYYY-MM-DD format."


def test_calibration_endpoint_invalid_window_days_returns_safe_400(monkeypatch):
    _patch_user_and_service(monkeypatch, _calibration_result())

    client = TestClient(app)
    response = client.get("/nutrition/1/target-calibration?window_days=21")

    assert response.status_code == 400
    assert response.json()["detail"] == "window_days must be 14 or 28."


def test_calibration_endpoint_nonexistent_user_returns_safe_404(monkeypatch):
    monkeypatch.setattr(
        calibration_route,
        "get_user_profile",
        lambda user_id: None,
    )

    client = TestClient(app)
    response = client.get("/nutrition/999/target-calibration?end_date=2026-06-06")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_calibration_endpoint_no_log_poor_log_window_blocks_calibration(monkeypatch):
    result = _calibration_result(
        reason_codes=[
            "calibration_assessment_created",
            "target_mutation_not_performed",
            "logging_quality_insufficient",
            "calibration_not_ready",
        ],
        limitations=[
            "Calibration assessment is read-only and does not mutate nutrition targets.",
            "Logging consistency is not strong enough for nutrition target calibration.",
        ],
    )
    _patch_user_and_service(monkeypatch, result)

    client = TestClient(app)
    response = client.get("/nutrition/1/target-calibration?end_date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    assert payload["calibration_allowed"] is False
    assert "logging_quality_insufficient" in payload["reason_codes"]


def test_calibration_endpoint_missing_bodyweight_trend_limits_calibration(monkeypatch):
    result = _calibration_result(
        recommended_action=RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE,
        confidence="Low",
        reason_codes=[
            "calibration_assessment_created",
            "target_mutation_not_performed",
            "bodyweight_trend_unavailable",
            "target_range_remains_broad",
        ],
        limitations=[
            "Calibration assessment is read-only and does not mutate nutrition targets.",
            "Bodyweight trend evidence is unavailable, so calibration is limited.",
        ],
    )
    _patch_user_and_service(monkeypatch, result)

    client = TestClient(app)
    response = client.get("/nutrition/1/target-calibration?end_date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommended_action"] == RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE
    assert "bodyweight_trend_unavailable" in payload["reason_codes"]


def test_calibration_endpoint_can_return_usable_or_strong_readiness(monkeypatch):
    result = _calibration_result(
        readiness_level=CALIBRATION_READINESS_STRONG,
        recommended_action=RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT,
        calibration_allowed=True,
        confidence="High",
        reason_codes=[
            "calibration_assessment_created",
            "target_mutation_not_performed",
            "calibration_strong",
            "future_refinement_candidate",
        ],
        limitations=[
            "Calibration assessment is read-only and does not mutate nutrition targets.",
            "The current trend window may support future target refinement after review.",
        ],
    )
    _patch_user_and_service(monkeypatch, result)

    client = TestClient(app)
    response = client.get("/nutrition/1/target-calibration?end_date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness_level"] == CALIBRATION_READINESS_STRONG
    assert payload["calibration_allowed"] is True
    assert (
        payload["recommended_action"]
        == RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT
    )


def test_calibration_endpoint_recommended_action_is_public_safe(monkeypatch):
    result = _calibration_result(
        recommended_action=RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE,
        confidence="Low",
        reason_codes=[
            "calibration_assessment_created",
            "target_mutation_not_performed",
            "target_range_remains_broad",
        ],
        limitations=[
            "Calibration assessment is read-only and does not mutate nutrition targets.",
            "Targets remain broad because trend evidence is limited.",
        ],
    )
    _patch_user_and_service(monkeypatch, result)

    client = TestClient(app)
    response = client.get("/nutrition/1/target-calibration?end_date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommended_action"] in {
        RECOMMENDED_ACTION_INSUFFICIENT_DATA,
        RECOMMENDED_ACTION_KEEP_CURRENT_TARGETS,
        RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE,
        RECOMMENDED_ACTION_ELIGIBLE_FOR_FUTURE_REFINEMENT,
    }
    joined = " ".join(payload["limitations"] + payload["reason_codes"]).lower()
    assert "true maintenance is exactly" not in joined
    assert "metabolism is damaged" not in joined
    assert "must cut calories" not in joined
    assert "failed your targets" not in joined


def test_calibration_endpoint_does_not_expose_raw_internal_fields(monkeypatch):
    result = _calibration_result()
    _patch_user_and_service(monkeypatch, result)

    client = TestClient(app)
    response = client.get("/nutrition/1/target-calibration?end_date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    forbidden_keys = {
        "food_entries",
        "daily_checkins",
        "raw_food_logs",
        "raw_checkins",
        "sql",
        "stack_trace",
        "provider_metadata",
        "crewai",
        "ollama",
        "target_mutation_payload",
    }
    assert forbidden_keys.isdisjoint(payload.keys())
    assert payload["calibrated_targets"] is None
    assert payload["metadata"]["inputs_used"] == [
        "formula_derived_targets",
        "nutrition_trend_window",
    ]
