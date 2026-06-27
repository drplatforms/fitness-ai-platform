from datetime import date, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.async_daily_coach_narrative_models import (
    ApprovedDailyCoachNarrativePayload,
    DailyCoachNarrativeJob,
    DailyCoachNarrativeJobStatus,
)
from services.async_daily_coach_context_identity import (
    build_daily_coach_narrative_context_identity,
)
from services.daily_coach_async_narrative_service import (
    DailyCoachAsyncNarrativeService,
)
from services.daily_coach_narrative_preview_service import (
    DailyCoachNarrativePreviewError,
    build_daily_coach_narrative_preview,
)
from services.daily_coach_synthesis_service import (
    DailyCoachSynthesisValidationError,
    build_daily_coach_synthesis,
)
from services.daily_coach_today_card_service import (
    DailyCoachTodayCardValidationError,
    build_daily_coach_today_card,
)
from services.daily_coach_value_narrative_service import (
    DailyCoachValueNarrativeError,
    build_configured_daily_coach_value_narrative,
)
from services.daily_next_action_service import (
    DailyNextActionValidationError,
    build_daily_next_action,
)

router = APIRouter()

_DAILY_COACH_ASYNC_DEVELOPER_SERVICE = DailyCoachAsyncNarrativeService()
_DAILY_COACH_ASYNC_DEVELOPER_PROMPT_CONTRACT_VERSION = (
    "daily_coach_async_developer_prototype_v1"
)
_DAILY_COACH_ASYNC_DEVELOPER_VALIDATOR_VERSION = (
    "daily_coach_async_developer_validator_v1"
)
_DAILY_COACH_ASYNC_DEVELOPER_ALLOWED_SIMULATIONS = {
    "mark_stale",
    "expire",
    "approve_deterministic",
}


class DailyCoachAsyncDeveloperSimulationRequest(BaseModel):
    action: str


def _async_developer_target_date(target_date: str | None) -> str:
    return target_date or date.today().isoformat()


def _async_developer_approved_context_inputs(action) -> dict[str, object]:
    return {
        "daily_next_action": action.to_dict(),
        "developer_prototype": {
            "milestone": "Daily Coach Async Developer-Only Prototype v1",
            "developer_only": True,
            "provider_execution": "not_allowed",
            "normal_today_behavior": "unchanged",
        },
    }


def _build_async_developer_context_identity(
    *,
    user_id: int,
    target_date: str | None = None,
    provider: str = "deterministic",
    model: str = "deterministic",
):
    action_date = _async_developer_target_date(target_date)
    action = build_daily_next_action(user_id, target_date=action_date)
    return build_daily_coach_narrative_context_identity(
        user_id=user_id,
        target_date=action_date,
        next_action_id=action.action_id,
        workflow_target=action.workflow_target,
        provider=provider,
        model=model,
        prompt_contract_version=_DAILY_COACH_ASYNC_DEVELOPER_PROMPT_CONTRACT_VERSION,
        validator_version=_DAILY_COACH_ASYNC_DEVELOPER_VALIDATOR_VERSION,
        approved_context_inputs=_async_developer_approved_context_inputs(action),
    )


def _async_developer_payload(job: DailyCoachNarrativeJob) -> dict[str, object]:
    return {
        "job_id": job.id,
        "status": job.status_value,
        "target_date": job.target_date,
        "user_id": job.user_id,
        "workflow_target": job.workflow_target,
        "next_action_id": job.next_action_id,
        "context_hash": job.context_hash,
        "prompt_contract_version": job.prompt_contract_version,
        "validator_version": job.validator_version,
        "provider": job.provider,
        "model": job.model,
        "model_lane": job.model_lane.value,
        "bridge_approved": job.bridge_approved,
        "approval_eligible": job.approval_eligible,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "expires_at": job.expires_at,
        "sanitized_failure_reason": job.sanitized_failure_reason,
        "latency_ms": job.latency_ms,
        "approved_narrative": (
            job.approved_narrative.to_dict() if job.approved_narrative else None
        ),
    }


def _async_developer_response(
    *,
    user_id: int,
    context_identity,
    job: DailyCoachNarrativeJob | None,
) -> dict[str, object]:
    display_state = (
        _DAILY_COACH_ASYNC_DEVELOPER_SERVICE.classify_job_display_state(
            job, context_identity
        )
        if job is not None
        else "fallback_available"
    )
    return {
        "success": True,
        "developer_only": True,
        "normal_today_behavior_changed": False,
        "provider_execution": "not_attempted",
        "worker_queue_scheduler": "not_added",
        "persistence": "in_memory_only",
        "user_id": user_id,
        "display_state": display_state,
        "context_identity": context_identity.to_dict(),
        "async_narrative_job": _async_developer_payload(job) if job else None,
    }


def _async_developer_deterministic_payload(
    job: DailyCoachNarrativeJob,
) -> ApprovedDailyCoachNarrativePayload:
    return ApprovedDailyCoachNarrativePayload(
        narrative=(
            "Developer-only simulated approval for the async Daily Coach lifecycle. "
            "Normal Today behavior remains deterministic and unchanged."
        ),
        key_takeaway="Async lifecycle inspection is isolated to Developer Mode.",
        recommended_focus="Use this only to validate job status and context identity.",
        source="developer_simulated_async_payload",
        provider=job.provider,
        model=job.model,
        validation_summary={
            "developer_only": True,
            "provider_execution": "not_attempted",
            "normal_today_behavior": "unchanged",
        },
    )


@router.get("/daily-coach/{user_id}/synthesis")
def daily_coach_synthesis(user_id: int):
    try:
        synthesis = build_daily_coach_synthesis(user_id)
    except DailyCoachSynthesisValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        "synthesis_date": synthesis.synthesis_date,
        "scenario": synthesis.scenario,
        "confidence": synthesis.confidence,
        "daily_coach_synthesis": synthesis.to_dict(),
    }


@router.get("/daily-coach/{user_id}/narrative")
def daily_coach_value_narrative(user_id: int, date: str | None = None):
    """Return approved Daily Coach narrative without provider runtime metadata."""

    try:
        result = build_configured_daily_coach_value_narrative(
            user_id,
            target_date=date,
        )
    except DailyCoachValueNarrativeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DailyCoachSynthesisValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return result.to_public_dict()


@router.get("/daily-coach/{user_id}/narrative/debug")
def daily_coach_value_narrative_debug(user_id: int, date: str | None = None):
    """Return approved Daily Coach narrative plus public-safe runtime metadata.

    This path is for QA/developer provider comparison. It does not return raw
    provider output, prompts, stack traces, or unvalidated provider text.
    """

    try:
        result = build_configured_daily_coach_value_narrative(
            user_id,
            target_date=date,
        )
    except DailyCoachValueNarrativeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DailyCoachSynthesisValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return result.to_debug_dict()


@router.get("/daily-coach/{user_id}/next-action")
def daily_next_action(user_id: int):
    try:
        action = build_daily_next_action(user_id)
    except DailyNextActionValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        "daily_next_action": action.to_dict(),
    }


@router.get("/daily-coach/{user_id}/today-card")
def daily_coach_today_card(user_id: int, date: str | None = None):
    """Return the deterministic public-safe Today Coach Note card.

    This normal product route does not call providers, return provider internals,
    persist narrative text, mutate reports, or expose debug payloads.
    """

    try:
        card = build_daily_coach_today_card(user_id, target_date=date)
    except DailyCoachTodayCardValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        "today_card": card.to_public_dict(),
    }


@router.post("/daily-coach/{user_id}/async-narrative/developer/jobs")
def create_daily_coach_async_developer_job(
    user_id: int,
    target_date: str | None = None,
    provider: str = "deterministic",
    model: str = "deterministic",
    expires_seconds: int = 3600,
):
    """Create a developer-only async narrative job shell.

    This route is a manual Developer Mode lifecycle harness. It does not call a
    provider, start background work, create persistence, or affect normal Today
    behavior.
    """

    try:
        context_identity = _build_async_developer_context_identity(
            user_id=user_id,
            target_date=target_date,
            provider=provider,
            model=model,
        )
        job = _DAILY_COACH_ASYNC_DEVELOPER_SERVICE.create_job(
            context_identity,
            expires_in=timedelta(seconds=max(1, expires_seconds)),
        )
    except DailyNextActionValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _async_developer_response(
        user_id=user_id,
        context_identity=context_identity,
        job=job,
    )


@router.get("/daily-coach/{user_id}/async-narrative/developer/jobs/latest")
def get_latest_daily_coach_async_developer_job(
    user_id: int,
    target_date: str | None = None,
    provider: str = "deterministic",
    model: str = "deterministic",
):
    """Inspect the latest developer-only async narrative job shell."""

    try:
        context_identity = _build_async_developer_context_identity(
            user_id=user_id,
            target_date=target_date,
            provider=provider,
            model=model,
        )
    except DailyNextActionValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    job = _DAILY_COACH_ASYNC_DEVELOPER_SERVICE.get_latest_job(
        user_id=user_id,
        target_date=context_identity.target_date,
        provider=provider,
        model=model,
    )
    return _async_developer_response(
        user_id=user_id,
        context_identity=context_identity,
        job=job,
    )


@router.get("/daily-coach/{user_id}/async-narrative/developer/jobs/{job_id}")
def get_daily_coach_async_developer_job(
    user_id: int,
    job_id: str,
    target_date: str | None = None,
    provider: str = "deterministic",
    model: str = "deterministic",
):
    """Inspect one developer-only async narrative job shell by id."""

    try:
        context_identity = _build_async_developer_context_identity(
            user_id=user_id,
            target_date=target_date,
            provider=provider,
            model=model,
        )
    except DailyNextActionValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    job = _DAILY_COACH_ASYNC_DEVELOPER_SERVICE.get_job(job_id)
    if job is None or job.user_id != user_id:
        raise HTTPException(status_code=404, detail="Developer async job not found")

    return _async_developer_response(
        user_id=user_id,
        context_identity=context_identity,
        job=job,
    )


@router.post("/daily-coach/{user_id}/async-narrative/developer/jobs/{job_id}/simulate")
def simulate_daily_coach_async_developer_job(
    user_id: int,
    job_id: str,
    request: DailyCoachAsyncDeveloperSimulationRequest,
    target_date: str | None = None,
    provider: str = "deterministic",
    model: str = "deterministic",
):
    """Simulate safe developer-only lifecycle transitions.

    Simulated approval uses deterministic test copy only. It is not provider
    output and is never used by normal Today behavior.
    """

    action = request.action.strip().lower()
    if action not in _DAILY_COACH_ASYNC_DEVELOPER_ALLOWED_SIMULATIONS:
        raise HTTPException(status_code=400, detail="Unsupported developer simulation")

    try:
        context_identity = _build_async_developer_context_identity(
            user_id=user_id,
            target_date=target_date,
            provider=provider,
            model=model,
        )
    except DailyNextActionValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    job = _DAILY_COACH_ASYNC_DEVELOPER_SERVICE.get_job(job_id)
    if job is None or job.user_id != user_id:
        raise HTTPException(status_code=404, detail="Developer async job not found")

    try:
        if action == "mark_stale":
            job = _DAILY_COACH_ASYNC_DEVELOPER_SERVICE.mark_job_stale(job_id)
        elif action == "expire":
            job = _DAILY_COACH_ASYNC_DEVELOPER_SERVICE.expire_job(job_id)
        elif action == "approve_deterministic":
            if job.status_value == DailyCoachNarrativeJobStatus.QUEUED.value:
                job = _DAILY_COACH_ASYNC_DEVELOPER_SERVICE.transition_job(
                    job_id,
                    DailyCoachNarrativeJobStatus.GENERATING,
                )
            if job.status_value == DailyCoachNarrativeJobStatus.GENERATING.value:
                job = _DAILY_COACH_ASYNC_DEVELOPER_SERVICE.transition_job(
                    job_id,
                    DailyCoachNarrativeJobStatus.PROVIDER_SUCCEEDED_PENDING_VALIDATION,
                )
            if (
                job.status_value
                == DailyCoachNarrativeJobStatus.PROVIDER_SUCCEEDED_PENDING_VALIDATION.value
            ):
                job = _DAILY_COACH_ASYNC_DEVELOPER_SERVICE.transition_job(
                    job_id,
                    DailyCoachNarrativeJobStatus.APPROVED,
                    approved_narrative=_async_developer_deterministic_payload(job),
                    latency_ms=0,
                )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _async_developer_response(
        user_id=user_id,
        context_identity=context_identity,
        job=job,
    )


@router.get("/daily-coach/{user_id}/narrative-preview/debug")
def daily_coach_narrative_preview_debug(
    user_id: int,
    provider: str = "deterministic",
    model: str | None = None,
    date: str | None = None,
    timeout_seconds: float = 300.0,
    qa_preview: bool = False,
    lookback_days: int = 1,
):
    """Return a public-safe developer-only Daily Coach Narrative preview.

    This debug path never returns rejected provider text, raw prompts, raw model
    payloads, stack traces, or validation internals. Provider output appears only
    when parsed and validated. Otherwise the deterministic fallback note is used.
    """

    try:
        preview_kwargs = {
            "target_date": date,
            "provider": provider,
            "model_name": model,
            "timeout_seconds": timeout_seconds,
        }
        if qa_preview:
            preview_kwargs["qa_preview"] = qa_preview
        if lookback_days != 1:
            preview_kwargs["lookback_days"] = lookback_days
        preview = build_daily_coach_narrative_preview(user_id, **preview_kwargs)
    except DailyCoachNarrativePreviewError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "success": True,
        "daily_coach_narrative_preview": preview.to_dict(),
    }
