from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.reports as reports_route
from api.main import app
from models.health_report_section_models import (
    ApprovedHealthReportSection,
    ApprovedHealthReportSectionResult,
    HealthReportSectionRuntimeMetadata,
)


def _approved_section() -> ApprovedHealthReportSection:
    return ApprovedHealthReportSection(
        section="nutrition",
        section_summary="Protein is the main approved nutrition focus today.",
        key_observations=["Greek Yogurt, Plain is approved for the current gap."],
        coaching_interpretation="This is a practical nutrition support opportunity.",
        suggested_focus="Use approved Nutrition tab options if helpful.",
        limitations_context="Targets remain coaching estimates, not medical advice.",
        confidence="High",
        reason_codes=["direct_ollama_report_section_candidate"],
        source="provider_approved",
    )


def _runtime_metadata() -> HealthReportSectionRuntimeMetadata:
    return HealthReportSectionRuntimeMetadata(
        configured_provider="direct_ollama",
        selected_provider="direct_ollama",
        configured_model="ollama/qwen2.5:3b",
        selected_model="qwen2.5:3b",
        provider_attempted=True,
        fallback_used=False,
        fallback_reason=None,
        candidate_valid=True,
        validation_errors=[],
        candidate_parse_status="success",
        candidate_validation_status="success",
        validation_status="approved",
        final_section_source="provider_approved",
        raw_output_length=642,
        raw_output_preview_truncated="{...}",
        markdown_wrapper_detected=False,
        extra_keys_detected=[],
        wrapper_object_detected=False,
        elapsed_seconds=11.843,
    )


def test_nutrition_report_section_debug_endpoint_returns_metadata(monkeypatch):
    result = ApprovedHealthReportSectionResult(
        approved_section=_approved_section(),
        runtime_metadata=_runtime_metadata(),
    )

    monkeypatch.setattr(
        reports_route,
        "build_configured_nutrition_health_report_section_with_metadata",
        lambda user_id, report_date: result,
    )

    client = TestClient(app)
    response = client.get("/reports/sections/nutrition/102/debug?date=2026-06-06")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 102
    assert payload["section"] == "nutrition"
    assert payload["report_date"] == "2026-06-06"
    assert payload["approved_section"]["section_summary"]
    assert payload["runtime_metadata"]["configured_provider"] == "direct_ollama"
    assert payload["runtime_metadata"]["selected_model"] == "qwen2.5:3b"
    assert payload["runtime_metadata"]["raw_output_preview_truncated"] == "{...}"


def test_nutrition_report_section_debug_endpoint_defaults_date(monkeypatch):
    captured: dict[str, str] = {}
    result = ApprovedHealthReportSectionResult(
        approved_section=_approved_section(),
        runtime_metadata=_runtime_metadata(),
    )

    def fake_build(user_id: int, report_date: str):
        captured["report_date"] = report_date
        return result

    monkeypatch.setattr(
        reports_route,
        "build_configured_nutrition_health_report_section_with_metadata",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/reports/sections/nutrition/102/debug")

    assert response.status_code == 200
    assert captured["report_date"]
    assert response.json()["report_date"] == captured["report_date"]


def test_nutrition_report_section_debug_endpoint_invalid_date_returns_400():
    client = TestClient(app)
    response = client.get("/reports/sections/nutrition/102/debug?date=06-06-2026")

    assert response.status_code == 400
    assert response.json()["detail"] == "date must use YYYY-MM-DD format."


def test_existing_latest_report_endpoint_does_not_expose_section_metadata(monkeypatch):
    monkeypatch.setattr(
        reports_route,
        "get_latest_health_report",
        lambda user_id: {
            "id": 1,
            "user_id": user_id,
            "report_text": "Existing public report text",
            "created_at": "2026-06-06 12:00:00",
        },
    )

    client = TestClient(app)
    response = client.get("/reports/latest/102")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "runtime_metadata" not in payload["report"]
    assert "configured_model" not in payload["report"]
    assert "selected_model" not in payload["report"]
    assert "raw_output_preview_truncated" not in payload["report"]
