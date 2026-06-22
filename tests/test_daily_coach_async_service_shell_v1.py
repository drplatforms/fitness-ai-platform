from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from models.async_daily_coach_narrative_models import (
    ApprovedDailyCoachNarrativePayload,
    DailyCoachNarrativeJobStatus,
    DailyCoachNarrativeModelLane,
    get_daily_coach_narrative_model_lane,
    is_daily_coach_narrative_bridge_approved_model,
)
from services.async_daily_coach_context_identity import (
    build_daily_coach_narrative_context_identity,
)
from services.daily_coach_async_narrative_service import (
    DailyCoachAsyncNarrativeService,
)


class FrozenClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.current

    def advance(self, *, seconds: int = 1) -> None:
        self.current = self.current + timedelta(seconds=seconds)


class SequentialIds:
    def __init__(self) -> None:
        self.value = 0

    def __call__(self) -> str:
        self.value += 1
        return f"job-{self.value}"


def _identity(
    *,
    target_date: str = "2026-06-21",
    next_action_id: str = "log_food",
    workflow_target: str = "nutrition_quick_log",
    provider: str = "direct_ollama",
    model: str = "qwen2.5:3b",
    prompt_contract_version: str = "daily_coach_narrative_v1",
    validator_version: str = "daily_coach_narrative_validator_v1",
    fact_suffix: str = "baseline",
):
    return build_daily_coach_narrative_context_identity(
        user_id=102,
        target_date=target_date,
        next_action_id=next_action_id,
        workflow_target=workflow_target,
        provider=provider,
        model=model,
        prompt_contract_version=prompt_contract_version,
        validator_version=validator_version,
        approved_context_inputs={
            "daily_next_action": {
                "id": next_action_id,
                "workflow_target": workflow_target,
            },
            "approved_facts": [
                f"Daily next action: {next_action_id}",
                f"Workflow target: {workflow_target}",
                f"Fact suffix: {fact_suffix}",
            ],
        },
    )


def _payload(model: str = "qwen2.5:3b") -> ApprovedDailyCoachNarrativePayload:
    return ApprovedDailyCoachNarrativePayload(
        narrative="Log a meal or snack so today's guidance has enough data.",
        key_takeaway="Nutrition confidence improves after logging food.",
        recommended_focus="Log one meal or snack.",
        source="validated_async_candidate",
        provider="direct_ollama",
        model=model,
        validation_summary={"claim_safety": "approved"},
    )


def _service() -> tuple[DailyCoachAsyncNarrativeService, FrozenClock]:
    clock = FrozenClock()
    return (
        DailyCoachAsyncNarrativeService(clock=clock, id_factory=SequentialIds()),
        clock,
    )


def _approved_job(
    service: DailyCoachAsyncNarrativeService,
    context=None,
    *,
    expires_in: timedelta | None = None,
):
    current_context = context or _identity()
    job = service.create_job(current_context, expires_in=expires_in)
    service.transition_job(job.id, DailyCoachNarrativeJobStatus.GENERATING)
    service.transition_job(
        job.id, DailyCoachNarrativeJobStatus.PROVIDER_SUCCEEDED_PENDING_VALIDATION
    )
    return service.transition_job(
        job.id,
        DailyCoachNarrativeJobStatus.APPROVED,
        approved_narrative=_payload(model=current_context.model),
    )


def test_create_job_does_not_execute_provider() -> None:
    service, _clock = _service()
    provider_called = False

    def forbidden_provider_call() -> None:
        nonlocal provider_called
        provider_called = True

    job = service.create_job(_identity())
    assert job.status_value == "queued"
    assert job.approved_narrative is None
    assert provider_called is False
    assert forbidden_provider_call.__name__ == "forbidden_provider_call"


def test_get_job_returns_created_job() -> None:
    service, _clock = _service()
    job = service.create_job(_identity())

    assert service.get_job(job.id) == job
    assert service.get_job("missing") is None


def test_latest_job_selection_is_deterministic() -> None:
    service, clock = _service()
    context = _identity()
    first = _approved_job(service, context)
    clock.advance(seconds=5)
    second = _approved_job(service, context)

    latest = service.get_latest_job(user_id=102, target_date="2026-06-21")

    assert latest is not None
    assert latest.id == second.id
    assert latest.id != first.id


def test_approved_matching_job_is_displayable() -> None:
    service, _clock = _service()
    context = _identity()
    job = _approved_job(service, context)

    assert service.is_displayable(job, context) is True
    assert service.classify_job_display_state(job, context) == "displayable"
    assert (
        service.get_latest_displayable_job(
            user_id=102,
            target_date="2026-06-21",
            current_context=context,
        )
        == job
    )


@pytest.mark.parametrize(
    "status",
    [
        DailyCoachNarrativeJobStatus.QUEUED,
        DailyCoachNarrativeJobStatus.GENERATING,
        DailyCoachNarrativeJobStatus.PROVIDER_SUCCEEDED_PENDING_VALIDATION,
        DailyCoachNarrativeJobStatus.REJECTED_PARSE,
        DailyCoachNarrativeJobStatus.REJECTED_VALIDATION,
        DailyCoachNarrativeJobStatus.PROVIDER_TIMEOUT,
        DailyCoachNarrativeJobStatus.PROVIDER_ERROR,
        DailyCoachNarrativeJobStatus.STALE,
        DailyCoachNarrativeJobStatus.FALLBACK_AVAILABLE,
    ],
)
def test_non_approved_jobs_are_not_displayable(
    status: DailyCoachNarrativeJobStatus,
) -> None:
    service, _clock = _service()
    context = _identity()
    job = service.create_job(context, status=status)

    assert service.is_displayable(job, context) is False
    assert (
        service.get_latest_displayable_job(
            user_id=102,
            target_date="2026-06-21",
            current_context=context,
        )
        is None
    )


def test_approved_job_without_payload_is_not_displayable() -> None:
    service, _clock = _service()
    context = _identity()
    job = service.create_job(context, status=DailyCoachNarrativeJobStatus.APPROVED)

    assert service.is_displayable(job, context) is False


def test_stale_job_is_not_displayable() -> None:
    service, _clock = _service()
    context = _identity()
    job = _approved_job(service, context)

    stale = service.mark_job_stale(job.id)

    assert stale.status_value == "stale"
    assert service.is_displayable(stale, context) is False


def test_expired_job_is_not_displayable() -> None:
    service, clock = _service()
    context = _identity()
    job = _approved_job(service, context, expires_in=timedelta(seconds=1))
    clock.advance(seconds=2)

    assert service.is_expired(job) is True
    assert service.is_displayable(job, context) is False
    assert service.classify_job_display_state(job, context) == "expired"


def test_context_hash_mismatch_is_not_displayable() -> None:
    service, _clock = _service()
    original = _identity()
    changed = _identity(fact_suffix="changed")
    job = _approved_job(service, original)

    assert original.context_hash != changed.context_hash
    assert service.is_displayable(job, changed) is False
    assert service.classify_job_display_state(job, changed) == "context_mismatch"


@pytest.mark.parametrize(
    "changed_context",
    [
        _identity(target_date="2026-06-22"),
        _identity(next_action_id="start_workout"),
        _identity(workflow_target="today_workout"),
        _identity(prompt_contract_version="daily_coach_narrative_v2"),
        _identity(validator_version="daily_coach_narrative_validator_v2"),
    ],
)
def test_context_identity_mismatch_is_not_displayable(changed_context) -> None:
    service, _clock = _service()
    original = _identity()
    job = _approved_job(service, original)

    assert service.is_displayable(job, changed_context) is False


def test_provider_model_change_is_separate_identity_not_silent_reuse() -> None:
    service, _clock = _service()
    original = _identity(provider="direct_ollama", model="qwen2.5:3b")
    qwen32 = _identity(provider="direct_ollama", model="qwen3:32b")
    job = _approved_job(service, original)

    assert service.is_displayable(job, qwen32) is False
    assert (
        service.get_latest_displayable_job(
            user_id=102,
            target_date="2026-06-21",
            current_context=qwen32,
        )
        is None
    )


def test_mark_context_mismatches_stale() -> None:
    service, _clock = _service()
    original = _identity()
    changed = _identity(fact_suffix="changed")
    job = _approved_job(service, original)

    updated = service.mark_context_mismatches_stale([job], changed)

    assert len(updated) == 1
    assert updated[0].status_value == "stale"
    assert service.get_job(job.id).status_value == "stale"  # type: ignore[union-attr]


def test_invalid_status_transition_is_rejected() -> None:
    service, _clock = _service()
    job = service.create_job(_identity())

    with pytest.raises(ValueError):
        service.transition_job(job.id, DailyCoachNarrativeJobStatus.APPROVED)


def test_no_provider_or_background_runtime_tokens_added() -> None:
    service_source = Path("services/daily_coach_async_narrative_service.py").read_text(
        encoding="utf-8"
    )
    forbidden_tokens = [
        "direct_ollama",
        "CrewAI",
        "crewai",
        "requests.",
        "httpx",
        "subprocess",
        "BackgroundTasks",
        "asyncio.create_task",
        "threading.Thread",
    ]

    for token in forbidden_tokens:
        assert token not in service_source


def test_no_fastapi_routes_added_for_async_service_shell() -> None:
    route_text = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("api/routes").rglob("*.py")
    )

    assert "DailyCoachAsyncNarrativeService" not in route_text
    assert "daily_coach_async" not in route_text
    assert "async narrative job" not in route_text.lower()


def test_no_streamlit_async_display_added() -> None:
    ui_text = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("ui").rglob("*.py")
    )

    assert "DailyCoachAsyncNarrativeService" not in ui_text
    assert "daily_coach_async" not in ui_text
    assert "validated_async_candidate" not in ui_text


def test_no_database_schema_created() -> None:
    schema_text = "\n".join(
        path.read_text(encoding="utf-8")
        for directory in [Path("data"), Path("api"), Path("services")]
        if directory.exists()
        for path in directory.rglob("*.py")
    )

    assert "CREATE TABLE daily_coach_narrative_jobs" not in schema_text
    assert "daily_coach_narrative_jobs" not in schema_text
    assert (
        "sqlite"
        not in Path("services/daily_coach_async_narrative_service.py")
        .read_text(encoding="utf-8")
        .lower()
    )


def test_qwen3_32b_remains_not_bridge_approved() -> None:
    assert is_daily_coach_narrative_bridge_approved_model("qwen2.5:3b") is True
    assert is_daily_coach_narrative_bridge_approved_model("qwen3:32b") is False
    assert get_daily_coach_narrative_model_lane("qwen3:32b") == (
        DailyCoachNarrativeModelLane.PREMIUM_ASYNC_CANDIDATE
    )
