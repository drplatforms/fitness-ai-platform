from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.daily_coach as daily_coach_routes
from api.main import app
from models.daily_coach_synthesis_models import DailyCoachSynthesis
from services.daily_coach_value_narrative_service import (
    build_daily_coach_value_narrative_from_synthesis,
)


def _result():
    synthesis = DailyCoachSynthesis(
        user_id=102,
        synthesis_date="2026-06-27",
        scenario="aligned_managed",
        confidence="High",
        today_summary="Today supports steady execution.",
        recovery_signal="Recovery readiness is high, with fatigue risk currently low.",
        training_signal="No workout has been started today.",
        workout_guidance="Use the approved plan as written.",
        execution_context="No workout has been started today.",
        logging_focus="Protein is below target based on logged meals.",
        plan_fit_note="No plan-fit concern is strong enough to change today's plan.",
        recommended_focus="Use the approved plan and keep logging complete.",
        reason_codes=["unit_test"],
        limitations=[],
    )
    return build_daily_coach_value_narrative_from_synthesis(
        synthesis,
        value_context={"approved_recovery": {"readiness_level": "High"}},
        environ={},
    )


def test_daily_coach_narrative_normal_endpoint_hides_runtime_metadata(monkeypatch):
    monkeypatch.setattr(
        daily_coach_routes,
        "build_configured_daily_coach_value_narrative",
        lambda user_id, target_date=None: _result(),
    )

    response = TestClient(app).get(
        "/daily-coach/102/narrative",
        params={"date": "2026-06-27"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["approved_daily_coach_narrative"]["source"] == "deterministic"
    assert "runtime_metadata" not in payload
    assert "provider_context_summary" not in payload
    assert "raw_output" not in str(payload).lower()


def test_daily_coach_narrative_debug_endpoint_exposes_metadata(monkeypatch):
    monkeypatch.setattr(
        daily_coach_routes,
        "build_configured_daily_coach_value_narrative",
        lambda user_id, target_date=None: _result(),
    )

    response = TestClient(app).get("/daily-coach/102/narrative/debug")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["runtime_metadata"]["selected_provider"] == "deterministic"
    assert payload["provider_context_summary"]["has_recovery_values"] is True
