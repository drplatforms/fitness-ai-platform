import time

import pytest
from fastapi.testclient import TestClient

import api.routes.reports as reports_route
from api.main import app
from services.coordinator_service import FullHealthReportGenerationResult
from services.training_report_section_provider_service import (
    build_deterministic_training_report_section_with_metadata,
)


@pytest.fixture(autouse=True)
def clear_report_job_state():
    reports_route.report_jobs.clear()
    reports_route.active_jobs.clear()
    yield
    reports_route.report_jobs.clear()
    reports_route.active_jobs.clear()


def _wait_for_status(client: TestClient, job_id: str, expected_status: str, timeout=3):
    deadline = time.time() + timeout

    while time.time() < deadline:
        response = client.get(f"/reports/status/{job_id}")
        data = response.json()

        if data.get("success") and data.get("status") == expected_status:
            return data

        time.sleep(0.05)

    pytest.fail(f"Job {job_id} did not reach status {expected_status}.")


def test_report_status_returns_timing_metadata_with_mocked_report(monkeypatch):
    def fake_generate_health_report(user_id, **_kwargs):
        return "Fake QA report"

    monkeypatch.setattr(
        reports_route, "generate_health_report", fake_generate_health_report
    )

    client = TestClient(app)

    generate_response = client.post("/reports/generate/1")
    generate_data = generate_response.json()

    assert generate_response.status_code == 200
    assert generate_data["success"] is True

    job_id = generate_data["job_id"]
    completed_data = _wait_for_status(client, job_id, "completed")

    assert completed_data["report"] == "Fake QA report"
    assert completed_data["started_at"] is not None
    assert completed_data["completed_at"] is not None
    assert completed_data["elapsed_seconds"] is not None
    assert completed_data["elapsed_seconds"] >= 0
    assert completed_data["training_section_provider"]["provider_attempted"] is False


def test_report_status_returns_safe_training_section_provider_metadata(monkeypatch):
    def fake_generate_health_report(user_id, report_date=None, **_kwargs):
        section_result = build_deterministic_training_report_section_with_metadata(
            user_id=user_id,
            report_date=report_date or "2026-06-14",
        )
        return FullHealthReportGenerationResult(
            report_text="Fake QA report with provider metadata",
            training_report_section_result=section_result,
        )

    monkeypatch.setattr(
        reports_route, "generate_health_report", fake_generate_health_report
    )

    client = TestClient(app)

    response = client.post("/reports/generate/102?date=2026-06-14")
    assert response.status_code == 200

    completed_data = _wait_for_status(client, response.json()["job_id"], "completed")
    provider_metadata = completed_data["training_section_provider"]

    assert provider_metadata["report_job_id"] == response.json()["job_id"]
    assert provider_metadata["user_id"] == 102
    assert provider_metadata["report_date"] == "2026-06-14"
    assert provider_metadata["provider_attempted"] is False
    assert provider_metadata["selected_provider"] == "deterministic"
    assert provider_metadata["validation_errors_count"] == 0
    assert "raw_output" not in str(provider_metadata)
    assert "model_facing_quote_context" not in str(provider_metadata)


def test_duplicate_report_generation_while_running_returns_409(monkeypatch):
    def slow_fake_generate_health_report(user_id, **_kwargs):
        time.sleep(0.3)
        return "Slow fake QA report"

    monkeypatch.setattr(
        reports_route, "generate_health_report", slow_fake_generate_health_report
    )

    client = TestClient(app)

    first_response = client.post("/reports/generate/1")
    assert first_response.status_code == 200

    second_response = client.post("/reports/generate/1")
    second_data = second_response.json()

    assert second_response.status_code == 409
    assert second_data["detail"]["success"] is False
    assert second_data["detail"]["message"] == "Report already generating."
    assert second_data["detail"]["job_id"] == first_response.json()["job_id"]

    _wait_for_status(client, first_response.json()["job_id"], "completed")


def test_report_status_debug_returns_nutrition_provider_diagnostics(monkeypatch):
    def fake_generate_health_report(user_id, report_date=None, **_kwargs):
        class FakeNutritionResult:
            safe_metadata = {
                "provider_enabled": True,
                "provider_attempted": True,
                "selected_provider": "direct_ollama",
                "selected_model": "qwen2.5:3b",
                "parse_status": "success",
                "candidate_valid": False,
                "validation_status": "rejected",
                "validation_errors_count": 1,
                "fallback_used": True,
                "fallback_reason": "nutrition_provider_validation_failed",
                "fallback_source": "nutrition_provider_contract_fallback",
                "nutrition_section_source": "deterministic_nutrition_report_section_fallback",
                "provider_latency_ms": 123,
            }
            approved_section = None
            validation_error_categories = ["unsupported_numeric_value"]
            validation_error_fields = ["target_alignment"]

        return FullHealthReportGenerationResult(
            report_text="Fake QA report with Nutrition diagnostics",
            nutrition_report_section_result=FakeNutritionResult(),
        )

    monkeypatch.setattr(
        reports_route, "generate_health_report", fake_generate_health_report
    )

    client = TestClient(app)
    response = client.post("/reports/generate/102?date=2026-06-14")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    completed_data = _wait_for_status(client, job_id, "completed")
    assert "nutrition_section_provider_debug" not in completed_data

    debug_data = client.get(f"/reports/status/{job_id}/debug").json()
    nutrition_debug = debug_data["nutrition_section_provider_debug"]

    assert nutrition_debug["nutrition_validation_errors_count"] == 1
    assert nutrition_debug["validation_error_categories"] == [
        "unsupported_numeric_value"
    ]
    assert nutrition_debug["validation_error_fields"] == ["target_alignment"]
    assert (
        nutrition_debug["first_validation_error_category"]
        == "unsupported_numeric_value"
    )
    assert nutrition_debug["first_validation_error_field"] == "target_alignment"
