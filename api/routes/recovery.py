# =====================================
# Imports
# =====================================

from fastapi import APIRouter
from pydantic import BaseModel

from services.recovery_service import (
    get_recent_recovery_metrics,
    get_recent_recovery_reports,
    save_recovery_checkin,
)

# =====================================
# Router Initialization
# =====================================

router = APIRouter()


# =====================================
# Request Models
# =====================================


class RecoveryCheckInRequest(BaseModel):
    user_id: int
    body_weight: float
    sleep_hours: float
    energy_level: int
    soreness_level: int
    mood: str
    notes: str


# =====================================
# Recovery Reports Endpoint
# =====================================


@router.get("/recovery/reports")
def recovery_reports():
    reports = get_recent_recovery_reports()

    return {"success": True, "reports": reports}


# =====================================
# Recovery Metrics Endpoint
# =====================================


@router.get("/recovery/metrics")
def recovery_metrics():
    metrics = get_recent_recovery_metrics()

    return {"success": True, "metrics": metrics}


# =====================================
# Recovery Check-In Endpoint
# =====================================


@router.post("/recovery/checkins")
def create_recovery_checkin(checkin: RecoveryCheckInRequest):
    checkin_id = save_recovery_checkin(
        user_id=checkin.user_id,
        body_weight=checkin.body_weight,
        sleep_hours=checkin.sleep_hours,
        energy_level=checkin.energy_level,
        soreness_level=checkin.soreness_level,
        mood=checkin.mood,
        notes=checkin.notes,
    )

    return {
        "success": True,
        "message": "Recovery check-in saved.",
        "checkin_id": checkin_id,
    }
