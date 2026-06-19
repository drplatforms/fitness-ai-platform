from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.daily_coach as daily_coach_routes
from api.main import app
from models.daily_coach_narrative_models import DailyCoachNarrativePreviewResult


def _preview_payload(
    *, provider_attempted: bool = False
) -> DailyCoachNarrativePreviewResult:
    return DailyCoachNarrativePreviewResult(
        user_id=102,
        date="2026-06-19",
        next_action_id="log_food",
        next_action_title="Log a meal or snack",
        workflow_target="nutrition_quick_log",
        provider_enabled=provider_attempted,
        provider_attempted=provider_attempted,
        selected_provider="direct_ollama" if provider_attempted else "deterministic",
        selected_model="qwen3:8b" if provider_attempted else None,
        parse_success=provider_attempted,
        validation_success=provider_attempted,
        fallback_used=not provider_attempted,
        fallback_reason=None if provider_attempted else "provider_disabled",
        approved_narrative=(
            {
                "coach_note": "Log a meal or snack to improve today's nutrition picture.",
                "key_takeaway": "More food logging gives today's guidance a clearer base.",
                "recommended_focus": "Log a meal or snack",
                "confidence_language": "Keep this limited until more food data is logged.",
                "used_approved_facts": [
                    "Daily next action: Log a meal or snack",
                    "Daily next action reason: Today's nutrition state is limited until more food data is logged.",
                ],
                "avoided_claims": ["No invented claim."],
            }
            if provider_attempted
            else None
        ),
        deterministic_fallback_note=(
            "Log a meal or snack: Today's nutrition state is limited until more food "
            "data is logged."
        ),
        approved_focus="Log a meal or snack",
        context_summary={
            "approved_facts_count": 13,
            "approved_facts_summary": ["Daily next action: Log a meal or snack"],
            "approved_limitations_count": 2,
            "approved_limitations_summary": ["Nutrition confidence is limited."],
            "forbidden_claim_categories_count": 15,
            "forbidden_claim_categories_summary": ["invented food"],
        },
        latency_ms=0,
    )


def test_narrative_preview_debug_route_returns_public_safe_payload(monkeypatch):
    calls = []

    def fake_build_preview(
        user_id: int,
        *,
        target_date: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float = 300.0,
    ):
        calls.append(
            {
                "user_id": user_id,
                "target_date": target_date,
                "provider": provider,
                "model_name": model_name,
                "timeout_seconds": timeout_seconds,
            }
        )
        return _preview_payload(provider_attempted=provider == "direct_ollama")

    monkeypatch.setattr(
        daily_coach_routes,
        "build_daily_coach_narrative_preview",
        fake_build_preview,
    )

    client = TestClient(app)
    response = client.get(
        "/daily-coach/102/narrative-preview/debug",
        params={"provider": "direct_ollama", "model": "qwen3:8b", "date": "2026-06-19"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    preview = payload["daily_coach_narrative_preview"]
    assert preview["provider_attempted"] is True
    assert preview["selected_model"] == "qwen3:8b"
    assert preview["fallback_used"] is False
    assert preview["approved_narrative"]["recommended_focus"] == "Log a meal or snack"
    assert "raw_output" not in str(payload).lower()
    assert "prompt" not in str(payload).lower()
    assert "validation_errors" not in str(payload).lower()
    assert calls == [
        {
            "user_id": 102,
            "target_date": "2026-06-19",
            "provider": "direct_ollama",
            "model_name": "qwen3:8b",
            "timeout_seconds": 300.0,
        }
    ]


def test_narrative_preview_debug_route_defaults_to_deterministic(monkeypatch):
    def fake_build_preview(
        user_id: int,
        *,
        target_date: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float = 300.0,
    ):
        assert provider == "deterministic"
        assert model_name is None
        return _preview_payload(provider_attempted=False)

    monkeypatch.setattr(
        daily_coach_routes,
        "build_daily_coach_narrative_preview",
        fake_build_preview,
    )

    client = TestClient(app)
    response = client.get("/daily-coach/102/narrative-preview/debug")

    assert response.status_code == 200
    preview = response.json()["daily_coach_narrative_preview"]
    assert preview["provider_attempted"] is False
    assert preview["fallback_used"] is True
    assert preview["fallback_reason"] == "provider_disabled"
    assert preview["approved_narrative"] is None
    assert preview["deterministic_fallback_note"]


def test_narrative_preview_debug_route_maps_invalid_preview_request_to_400(monkeypatch):
    from services.daily_coach_narrative_preview_service import (
        DailyCoachNarrativePreviewError,
    )

    def fake_build_preview(*args, **kwargs):
        raise DailyCoachNarrativePreviewError("bad provider")

    monkeypatch.setattr(
        daily_coach_routes,
        "build_daily_coach_narrative_preview",
        fake_build_preview,
    )

    client = TestClient(app)
    response = client.get(
        "/daily-coach/102/narrative-preview/debug",
        params={"provider": "unsafe_provider"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "bad provider"
