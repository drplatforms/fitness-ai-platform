import time

import pytest
from fastapi.testclient import TestClient

import api.routes.reports as reports_route
from api.main import app


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
    def fake_generate_health_report(user_id):
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


def test_duplicate_report_generation_while_running_returns_409(monkeypatch):
    def slow_fake_generate_health_report(user_id):
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
