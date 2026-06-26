from pathlib import Path

from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile

USER_HOME_GYM_EQUIPMENT = [
    "adjustable_bench",
    "barbell",
    "bike",
    "bodyweight",
    "cable",
    "dumbbell",
    "exercise_ball",
    "ez_bar",
    "plates",
    "pull_up_bar",
    "rack",
    "resistance_band",
    "rope_cable_attachment",
    "treadmill",
]

USER_HOME_GYM_NO_SPECIALTY_ATTACHMENTS = [
    "adjustable_bench",
    "barbell",
    "bike",
    "bodyweight",
    "cable",
    "dumbbell",
    "ez_bar",
    "plates",
    "pull_up_bar",
    "rack",
    "resistance_band",
    "treadmill",
]


def _seed_home_gym(tmp_path, monkeypatch, user_id: int = 102) -> None:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    seed_qa_scenarios()
    save_equipment_profile(
        user_id=user_id,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )


def _seed_home_gym_without_specialty_attachments(
    tmp_path, monkeypatch, user_id: int = 102
) -> None:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    seed_qa_scenarios()
    save_equipment_profile(
        user_id=user_id,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_NO_SPECIALTY_ATTACHMENTS,
        unavailable_equipment=["exercise_ball", "machine", "rope_cable_attachment"],
    )


def _preview(client: TestClient, *, size: str, variation_index: int) -> dict:
    response = client.get(
        f"/workout-plans/preview/102?"
        f"workout_size_preference={size}&preview_variation_index={variation_index}"
    )
    assert response.status_code == 200
    return response.json()["approved_workout_plan"]


def _names(plan: dict) -> list[str]:
    return [exercise["name"] for exercise in plan["exercises"]]


def _rotation_group(name: str) -> str:
    normalized = name.strip().lower()
    if "pallof press" in normalized:
        return "pallof_press"
    return normalized


def _rotation_groups(names: list[str]) -> list[str]:
    return [_rotation_group(name) for name in names]


def _equipment(plan: dict) -> set[str]:
    return {
        equipment
        for exercise in plan["exercises"]
        for equipment in exercise["equipment_required"]
    }


def _assert_overlap_slots_rotate(
    previous_names: list[str], refreshed_names: list[str]
) -> None:
    overlap = min(len(previous_names), len(refreshed_names))
    assert overlap >= 3
    repeated_slots = [
        index
        for index, (previous, refreshed) in enumerate(
            zip(previous_names[:overlap], refreshed_names[:overlap], strict=False)
        )
        if previous == refreshed
    ]
    assert repeated_slots == []


def test_refreshed_preview_rotates_every_overlapping_slot_when_valid(
    tmp_path, monkeypatch
):
    _seed_home_gym(tmp_path, monkeypatch)
    client = TestClient(app)

    expected_ranges = {
        "quick": range(3, 5),
        "standard": range(4, 6),
        "full": range(6, 8),
    }

    for size, expected_range in expected_ranges.items():
        initial = _preview(client, size=size, variation_index=0)
        refreshed = _preview(client, size=size, variation_index=1)
        repeated_refreshed = _preview(client, size=size, variation_index=1)

        initial_names = _names(initial)
        refreshed_names = _names(refreshed)

        assert len(initial_names) in expected_range
        assert len(refreshed_names) in expected_range
        assert refreshed_names == _names(repeated_refreshed)
        assert len(refreshed_names) == len(set(refreshed_names))
        assert len(_rotation_groups(refreshed_names)) == len(
            set(_rotation_groups(refreshed_names))
        )
        assert not (_equipment(refreshed) & {"machine"})
        assert _equipment(refreshed).issubset(set(USER_HOME_GYM_EQUIPMENT))
        _assert_overlap_slots_rotate(initial_names, refreshed_names)


def test_full_preview_rotation_changes_later_accessory_slots(tmp_path, monkeypatch):
    _seed_home_gym(tmp_path, monkeypatch)
    client = TestClient(app)

    initial = _preview(client, size="full", variation_index=0)
    refreshed = _preview(client, size="full", variation_index=1)

    initial_names = _names(initial)
    refreshed_names = _names(refreshed)

    assert len(initial_names) in range(6, 8)
    assert len(refreshed_names) in range(6, 8)
    _assert_overlap_slots_rotate(initial_names, refreshed_names)

    # The prior implementation could rotate the main four slots while repeating
    # the later accessory slot. Full-slot rotation should avoid that when the
    # slot has safe same-pattern alternatives available.
    assert initial_names[5] != refreshed_names[5]


def test_user_home_gym_without_specialty_attachments_rotates_observed_failures(
    tmp_path, monkeypatch
):
    _seed_home_gym_without_specialty_attachments(tmp_path, monkeypatch)
    client = TestClient(app)

    for size in ["quick", "standard", "full"]:
        previous_names = _names(_preview(client, size=size, variation_index=0))
        for variation_index in range(1, 5):
            refreshed_names = _names(
                _preview(client, size=size, variation_index=variation_index)
            )

            _assert_overlap_slots_rotate(previous_names, refreshed_names)
            assert len(refreshed_names) == len(set(refreshed_names))
            assert len(_rotation_groups(refreshed_names)) == len(
                set(_rotation_groups(refreshed_names))
            )

            previous_names = refreshed_names
