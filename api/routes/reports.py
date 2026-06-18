# =====================================
# Imports
# =====================================

import os
import threading
import time
import uuid
from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from services.coordinator_service import (
    AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV,
    generate_health_report,
    nutrition_section_provider_debug_metadata,
    nutrition_section_provider_job_metadata,
    training_section_provider_job_metadata,
)
from services.health_report_section_service import (
    build_configured_nutrition_health_report_section_with_metadata,
)
from services.report_service import get_health_report_history, get_latest_health_report
from services.user_state_service import build_user_health_state

report_jobs = {}
active_jobs = {}

# =====================================
# Router Initialization
# =====================================

router = APIRouter()

# =====================================
# User Health State Endpoint


@router.get("/health-state/{user_id}")
def user_health_state(user_id: int):
    health_state = build_user_health_state(user_id)

    return {
        "success": True,
        "health_state": asdict(health_state),
    }


# =====================================
# Background Report Worker
# =====================================


def _current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")


def _full_report_provider_enabled() -> bool:
    return os.getenv(
        AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV, ""
    ).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def _calculate_elapsed_seconds(job: dict) -> float | None:
    started_monotonic = job.get("started_monotonic")

    if started_monotonic is None:
        return None

    completed_monotonic = job.get("completed_monotonic")

    if completed_monotonic is None:
        return round(time.perf_counter() - started_monotonic, 2)

    return round(completed_monotonic - started_monotonic, 2)


def run_report_job(job_id, user_id):
    print("\n=== BACKGROUND JOB STARTED ===\n")

    try:
        report_jobs[job_id]["status"] = "running"

        report_jobs[job_id]["started_at"] = _current_timestamp()
        report_jobs[job_id]["started_monotonic"] = time.perf_counter()

        print("\n=== CALLING COORDINATOR SERVICE ===\n")

        report_date = report_jobs[job_id].get("report_date")
        provider_enabled = _full_report_provider_enabled()
        report_result = generate_health_report(
            user_id,
            report_date=report_date,
            allow_training_section_provider=True,
            return_training_section_result=True,
            report_job_id=job_id,
        )

        print("\n=== COORDINATOR SERVICE COMPLETED ===\n")

        report_jobs[job_id]["status"] = "completed"
        report_jobs[job_id]["completed_at"] = _current_timestamp()
        report_jobs[job_id]["completed_monotonic"] = time.perf_counter()
        report_jobs[job_id]["elapsed_seconds"] = _calculate_elapsed_seconds(
            report_jobs[job_id]
        )
        if hasattr(report_result, "report_text"):
            report_jobs[job_id]["report"] = report_result.report_text
            report_jobs[job_id]["training_section_provider"] = (
                training_section_provider_job_metadata(
                    report_result.training_report_section_result,
                    report_job_id=job_id,
                    provider_enabled=provider_enabled,
                )
            )
            report_jobs[job_id]["nutrition_section_provider"] = (
                nutrition_section_provider_job_metadata(
                    report_result.nutrition_report_section_result
                )
            )
            report_jobs[job_id]["nutrition_section_provider_debug"] = (
                nutrition_section_provider_debug_metadata(
                    report_result.nutrition_report_section_result
                )
            )
        else:
            report_jobs[job_id]["report"] = report_result
            report_jobs[job_id]["training_section_provider"] = (
                training_section_provider_job_metadata(
                    None,
                    report_job_id=job_id,
                    provider_enabled=provider_enabled,
                )
            )
            report_jobs[job_id]["nutrition_section_provider"] = (
                nutrition_section_provider_job_metadata(None)
            )
            report_jobs[job_id]["nutrition_section_provider_debug"] = (
                nutrition_section_provider_debug_metadata(None)
            )

    except Exception as e:
        print("\n=== REPORT JOB FAILED ===\n")

        print(e)

        report_jobs[job_id]["status"] = "failed"
        report_jobs[job_id]["completed_at"] = _current_timestamp()
        report_jobs[job_id]["completed_monotonic"] = time.perf_counter()
        report_jobs[job_id]["elapsed_seconds"] = _calculate_elapsed_seconds(
            report_jobs[job_id]
        )

        report_jobs[job_id]["report"] = str(e)

    finally:
        print("\n=== CLEANING UP ACTIVE JOB LOCK ===\n")

        if user_id in active_jobs:
            del active_jobs[user_id]


# =====================================
# Report Status Endpoint
# =====================================


@router.get("/reports/status/{job_id}")
def report_status(job_id: str):
    job = report_jobs.get(job_id)

    if not job:
        return {"success": False, "message": "Job not found."}

    elapsed_seconds = job.get("elapsed_seconds")

    if elapsed_seconds is None:
        elapsed_seconds = _calculate_elapsed_seconds(job)

    return {
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "report": job["report"],
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "elapsed_seconds": elapsed_seconds,
        "training_section_provider": job.get("training_section_provider"),
        "nutrition_section_provider": job.get("nutrition_section_provider"),
    }


@router.get("/reports/status/{job_id}/debug")
def report_status_debug(job_id: str):
    job = report_jobs.get(job_id)

    if not job:
        return {"success": False, "message": "Job not found."}

    elapsed_seconds = job.get("elapsed_seconds")

    if elapsed_seconds is None:
        elapsed_seconds = _calculate_elapsed_seconds(job)

    return {
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "report": job["report"],
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "elapsed_seconds": elapsed_seconds,
        "training_section_provider": job.get("training_section_provider"),
        "nutrition_section_provider": job.get("nutrition_section_provider"),
        "nutrition_section_provider_debug": job.get("nutrition_section_provider_debug"),
    }


# =====================================
# Generate AI Report Endpoint
# =====================================


@router.post("/reports/generate/{user_id}")
def generate_report(
    user_id: int,
    report_date: str | None = Query(default=None, alias="date"),
):
    print("\n=== GENERATE REPORT ENDPOINT HIT === \n")
    if user_id in active_jobs:
        existing_job_id = active_jobs[user_id]

        raise HTTPException(
            status_code=409,
            detail={
                "success": False,
                "message": "Report already generating.",
                "job_id": existing_job_id,
            },
        )

    job_id = str(uuid.uuid4())
    print(f"\n=== CREATED JOB {job_id} FOR USER {user_id} ===\n")
    print(f"\n=== RUNNING JOB {job_id} ===\n")

    active_jobs[user_id] = job_id

    report_jobs[job_id] = {
        "status": "queued",
        "report": None,
        "started_at": None,
        "completed_at": None,
        "elapsed_seconds": None,
        "started_monotonic": None,
        "completed_monotonic": None,
        "report_date": report_date,
        "training_section_provider": None,
        "nutrition_section_provider": None,
        "nutrition_section_provider_debug": None,
    }

    thread = threading.Thread(
        target=run_report_job, args=(job_id, user_id), daemon=True
    )

    thread.start()

    return {"success": True, "job_id": job_id, "status": "running"}


# =====================================
# Nutrition Report Section Debug Endpoint
# =====================================


@router.get("/reports/sections/nutrition/{user_id}/debug")
def nutrition_report_section_debug(
    user_id: int,
    report_date: str | None = Query(default=None, alias="date"),
):
    resolved_date = _resolve_report_section_date(report_date)

    try:
        result = build_configured_nutrition_health_report_section_with_metadata(
            user_id=user_id,
            report_date=resolved_date,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message.lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=(
                "Health report section validation failed."
                if status_code == 400
                else "User not found."
            ),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive debug-safe boundary
        raise HTTPException(
            status_code=500,
            detail="Health report section generation failed.",
        ) from exc

    approved_section = result.approved_section
    return {
        "success": True,
        "user_id": user_id,
        "section": approved_section.section,
        "report_date": resolved_date,
        "approved_section": approved_section.to_dict(),
        "runtime_metadata": result.runtime_metadata.to_debug_dict(),
    }


def _resolve_report_section_date(report_date: str | None) -> str:
    if report_date is None:
        return datetime.now().date().isoformat()

    try:
        return datetime.fromisoformat(report_date).date().isoformat()
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="date must use YYYY-MM-DD format.",
        ) from exc


# =====================================
# Latest AI Report Endpoint
# =====================================


@router.get("/reports/latest/{user_id}")
def latest_report(user_id: int):
    report = get_latest_health_report(user_id)

    if report:
        return {"success": True, "report": dict(report)}

    return {"success": False, "message": "No report found"}


# =====================================
# AI Report History Endpoint
# =====================================


@router.get("/reports/history/{user_id}")
def report_history(user_id: int):
    reports = get_health_report_history(user_id=user_id, limit=5)

    return {"success": True, "reports": [dict(report) for report in reports]}
