from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.daily_coach as daily_coach_routes
from api.main import app


class _FakeSynthesis:
    synthesis_date = "2026-06-20"
    scenario = "aligned_managed"
    confidence = "High"

    def to_dict(self) -> dict[str, object]:
        return {
            "synthesis_date": self.synthesis_date,
            "scenario": self.scenario,
            "confidence": self.confidence,
            "today_summary": "Recovery and training context are stable today.",
            "recommended_focus": "Maintain the current direction.",
            "workout_guidance": "Use the approved workout plan as written.",
            "limitations": [],
        }


def test_daily_coach_synthesis_route_returns_public_safe_wrapper(monkeypatch):
    def fake_build_synthesis(user_id: int):
        assert user_id == 102
        return _FakeSynthesis()

    monkeypatch.setattr(
        daily_coach_routes,
        "build_daily_coach_synthesis",
        fake_build_synthesis,
    )

    response = TestClient(app).get("/daily-coach/102/synthesis")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 102
    assert payload["synthesis_date"] == "2026-06-20"
    assert payload["confidence"] == "High"
    assert payload["daily_coach_synthesis"]["today_summary"]
    assert "raw_output" not in str(payload).lower()
    assert "prompt" not in str(payload).lower()


def test_daily_coach_synthesis_route_maps_missing_user_to_404(monkeypatch):
    def fake_build_synthesis(user_id: int):
        raise ValueError("unknown user")

    monkeypatch.setattr(
        daily_coach_routes,
        "build_daily_coach_synthesis",
        fake_build_synthesis,
    )

    response = TestClient(app).get("/daily-coach/999/synthesis")

    assert response.status_code == 404
    assert response.json()["detail"] == "unknown user"
