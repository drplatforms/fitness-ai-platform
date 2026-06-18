from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.equipment_profile_service import (
    equipment_profile_to_dict,
    get_effective_equipment_profile,
    get_equipment_profile,
    save_equipment_profile,
)

router = APIRouter()


class EquipmentProfileRequest(BaseModel):
    training_environment: str = "unknown"
    available_equipment: list[str] = Field(default_factory=list)
    unavailable_equipment: list[str] = Field(default_factory=list)


@router.get("/users/{user_id}/equipment-profile")
def get_user_equipment_profile(user_id: int):
    stored_profile = get_equipment_profile(user_id)
    effective_profile = stored_profile or get_effective_equipment_profile(user_id)

    return {
        "success": True,
        "user_id": user_id,
        "source": "explicit" if stored_profile else "default",
        "equipment_profile": equipment_profile_to_dict(effective_profile),
    }


@router.put("/users/{user_id}/equipment-profile")
def put_user_equipment_profile(user_id: int, payload: EquipmentProfileRequest):
    profile = save_equipment_profile(
        user_id=user_id,
        training_environment=payload.training_environment,
        available_equipment=payload.available_equipment,
        unavailable_equipment=payload.unavailable_equipment,
    )

    return {
        "success": True,
        "user_id": user_id,
        "source": "explicit",
        "equipment_profile": equipment_profile_to_dict(profile),
    }
