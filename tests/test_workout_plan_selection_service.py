from dataclasses import asdict, replace

import database
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.user_state_service import build_user_health_state
from services.workout_plan_persistence_service import (
    approved_workout_plan_from_payload,
    get_planned_workout_exercises,
    select_approved_workout_plan,
)
from services.workout_plan_service import build_approved_workout_plan


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()


def test_select_approved_workout_plan_persists_exact_visible_preview(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    health_state = build_user_health_state(102)
    visible_preview = build_approved_workout_plan(
        health_state,
        workout_size_preference="standard",
    )
    selected = select_approved_workout_plan(102, visible_preview)

    planned_exercises = selected["planned_exercises"]

    assert selected["workout_plan_instance"].status == "selected"
    assert selected["approved_workout_plan"].title == visible_preview.title
    assert [exercise.name for exercise in planned_exercises] == [
        exercise.name for exercise in visible_preview.exercises
    ]
    assert [exercise.sets for exercise in planned_exercises] == [
        exercise.sets for exercise in visible_preview.exercises
    ]


def test_select_approved_workout_plan_does_not_rebuild_when_visible_preview_differs(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    health_state = build_user_health_state(102)
    visible_preview = build_approved_workout_plan(health_state)
    changed_preview = replace(
        visible_preview,
        exercises=list(reversed(visible_preview.exercises)),
    )

    selected = select_approved_workout_plan(102, changed_preview)
    planned_exercises = get_planned_workout_exercises(
        selected["workout_plan_instance"].id
    )

    assert [exercise.name for exercise in planned_exercises] == [
        exercise.name for exercise in changed_preview.exercises
    ]
    assert [exercise.name for exercise in planned_exercises] != [
        exercise.name for exercise in visible_preview.exercises
    ]


def test_approved_workout_plan_payload_round_trips_for_selection(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    health_state = build_user_health_state(105)
    visible_preview = build_approved_workout_plan(health_state)

    approved_plan = approved_workout_plan_from_payload(asdict(visible_preview))
    selected = select_approved_workout_plan(105, approved_plan)

    assert selected["workout_plan_instance"].user_id == 105
    assert [exercise.name for exercise in selected["planned_exercises"]] == [
        exercise.name for exercise in visible_preview.exercises
    ]


def test_select_preview_endpoint_persists_exact_visible_preview(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app

    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    preview_response = client.get("/workout-plans/preview/102")
    visible_plan = preview_response.json()["approved_workout_plan"]

    select_response = client.post(
        "/workout-plans/102/select-preview",
        json={"approved_workout_plan": visible_plan},
    )

    assert select_response.status_code == 200
    payload = select_response.json()
    assert payload["success"] is True
    assert [exercise["name"] for exercise in payload["planned_exercises"]] == [
        exercise["name"] for exercise in visible_plan["exercises"]
    ]
