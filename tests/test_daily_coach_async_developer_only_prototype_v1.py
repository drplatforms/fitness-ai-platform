from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from fastapi.testclient import TestClient

import api.routes.daily_coach as daily_coach_routes
from api.main import app
from models.daily_next_action_models import DailyNextAction
from services.daily_coach_async_narrative_service import (
    DailyCoachAsyncNarrativeService,
)


@dataclass(frozen=True)
class FakeTodayCard:
    payload: dict[str, object] = field(
        default_factory=lambda: {
            "date": "2026-06-22",
            "card_title": "Today’s Coach Note",
            "coach_note": "Start with the deterministic next action.",
            "next_action_title": "Log a meal or snack",
            "cta_label": "Log food",
        }
    )

    def to_public_dict(self) -> dict[str, object]:
        return dict(self.payload)


def _fake_next_action(*_args, **_kwargs) -> DailyNextAction:
    return DailyNextAction(
        action_id="log_food",
        title="Log a meal or snack",
        summary="Add today’s food intake so nutrition guidance has enough data.",
        reason="Today's nutrition state is limited until more food data is logged.",
        priority=3,
        workflow_target="nutrition_quick_log",
        severity="info",
        evidence={"source": "test"},
    )


def _reset_developer_service(monkeypatch) -> None:
    monkeypatch.setattr(
        daily_coach_routes,
        "_DAILY_COACH_ASYNC_DEVELOPER_SERVICE",
        DailyCoachAsyncNarrativeService(),
    )
    monkeypatch.setattr(
        daily_coach_routes,
        "build_daily_next_action",
        _fake_next_action,
    )


def test_developer_only_route_can_create_async_job_shell(monkeypatch) -> None:
    _reset_developer_service(monkeypatch)
    client = TestClient(app)

    response = client.post(
        "/daily-coach/102/async-narrative/developer/jobs",
        params={"target_date": "2026-06-22"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["developer_only"] is True
    assert payload["normal_today_behavior_changed"] is False
    assert payload["provider_execution"] == "not_attempted"
    assert payload["worker_queue_scheduler"] == "not_added"
    assert payload["persistence"] == "in_memory_only"
    assert payload["display_state"] == "queued"

    job = payload["async_narrative_job"]
    assert job["status"] == "queued"
    assert job["user_id"] == 102
    assert job["target_date"] == "2026-06-22"
    assert job["next_action_id"] == "log_food"
    assert job["workflow_target"] == "nutrition_quick_log"
    assert job["approved_narrative"] is None
    assert job["context_hash"]


def test_developer_only_route_can_read_latest_job_status(monkeypatch) -> None:
    _reset_developer_service(monkeypatch)
    client = TestClient(app)

    created = client.post(
        "/daily-coach/102/async-narrative/developer/jobs",
        params={"target_date": "2026-06-22"},
    ).json()
    latest = client.get(
        "/daily-coach/102/async-narrative/developer/jobs/latest",
        params={"target_date": "2026-06-22"},
    )

    assert latest.status_code == 200
    payload = latest.json()
    assert (
        payload["async_narrative_job"]["job_id"]
        == (created["async_narrative_job"]["job_id"])
    )
    assert payload["display_state"] == "queued"


def test_developer_only_simulated_approval_uses_deterministic_payload(
    monkeypatch,
) -> None:
    _reset_developer_service(monkeypatch)
    client = TestClient(app)

    created = client.post(
        "/daily-coach/102/async-narrative/developer/jobs",
        params={"target_date": "2026-06-22"},
    ).json()
    job_id = created["async_narrative_job"]["job_id"]

    approved = client.post(
        f"/daily-coach/102/async-narrative/developer/jobs/{job_id}/simulate",
        params={"target_date": "2026-06-22"},
        json={"action": "approve_deterministic"},
    )

    assert approved.status_code == 200
    payload = approved.json()
    assert payload["display_state"] == "displayable"
    job = payload["async_narrative_job"]
    assert job["status"] == "approved"
    assert job["latency_ms"] == 0
    assert job["approved_narrative"]["source"] == "developer_simulated_async_payload"
    assert job["approved_narrative"]["validation_summary"] == {
        "developer_only": True,
        "provider_execution": "not_attempted",
        "normal_today_behavior": "unchanged",
    }


def test_developer_only_route_can_inspect_context_mismatch(monkeypatch) -> None:
    _reset_developer_service(monkeypatch)
    client = TestClient(app)

    created = client.post(
        "/daily-coach/102/async-narrative/developer/jobs",
        params={"target_date": "2026-06-22", "model": "deterministic"},
    ).json()
    job_id = created["async_narrative_job"]["job_id"]
    client.post(
        f"/daily-coach/102/async-narrative/developer/jobs/{job_id}/simulate",
        params={"target_date": "2026-06-22", "model": "deterministic"},
        json={"action": "approve_deterministic"},
    )

    changed_context = client.get(
        f"/daily-coach/102/async-narrative/developer/jobs/{job_id}",
        params={"target_date": "2026-06-22", "model": "qwen3:32b"},
    )

    assert changed_context.status_code == 200
    payload = changed_context.json()
    assert payload["display_state"] == "context_mismatch"
    assert payload["context_identity"]["model_lane"] == "premium_async_candidate"
    assert payload["context_identity"]["bridge_approved"] is False


def test_normal_today_card_response_remains_public_and_async_free(monkeypatch) -> None:
    monkeypatch.setattr(
        daily_coach_routes,
        "build_daily_coach_today_card",
        lambda *_args, **_kwargs: FakeTodayCard(),
    )
    client = TestClient(app)

    response = client.get("/daily-coach/102/today-card")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "today_card" in payload
    assert "async_narrative_job" not in payload
    assert "context_identity" not in payload
    assert "runtime_metadata" not in payload
    assert "provider_execution" not in payload


def test_developer_prototype_does_not_add_provider_worker_or_persistence_tokens() -> (
    None
):
    route_text = Path("api/routes/daily_coach.py").read_text(encoding="utf-8")
    forbidden_tokens = [
        "requests.",
        "httpx",
        "subprocess",
        "BackgroundTasks",
        "asyncio.create_task",
        "threading.Thread",
        "CREATE TABLE daily_coach_narrative_jobs",
        "daily_coach_narrative_jobs",
    ]

    for token in forbidden_tokens:
        assert token not in route_text
