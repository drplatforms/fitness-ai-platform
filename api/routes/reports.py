# =====================================
# Imports
# =====================================

import uuid
import threading

from fastapi import APIRouter, HTTPException

from services.report_service import get_latest_health_report, get_health_report_history

from services.coordinator_service import generate_health_report

report_jobs = {}
active_jobs = {}

# =====================================
# Router Initialization
# =====================================

router = APIRouter()
report_jobs = {}

# =====================================
# Background Report Worker
# =====================================


def run_report_job(job_id, user_id):
    print("\n=== BACKGROUND JOB STARTED ===\n")

    try:
        report_jobs[job_id]["status"] = "running"

        from datetime import datetime

        report_jobs[job_id]["started_at"] = datetime.now().strftime(
            "%Y-%m-%d %I:%M:%S %p"
        )

        report_jobs[job_id]["completed_at"] = datetime.now().strftime(
            "%Y-%m-%d %I:%M:%S %p"
        )

        print("\n=== CALLING COORDINATOR SERVICE ===\n")

        report = generate_health_report(user_id)

        print("\n=== COORDINATOR SERVICE COMPLETED ===\n")

        report_jobs[job_id]["status"] = "completed"

        report_jobs[job_id]["report"] = report

    except Exception as e:
        print("\n=== REPORT JOB FAILED ===\n")

        print(e)

        report_jobs[job_id]["status"] = "failed"

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

    return {
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "report": job["report"],
    }


# =====================================
# Generate AI Report Endpoint
# =====================================


@router.post("/reports/generate/{user_id}")
def generate_report(user_id: int):
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

    active_jobs[user_id] = job_id

    report_jobs[job_id] = {
        "status": "queued",
        "report": None,
        "started_at": None,
        "completed_at": None,
    }

    thread = threading.Thread(target=run_report_job, args=(job_id, user_id))

    thread.start()

    return {"success": True, "job_id": job_id, "status": "running"}


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
