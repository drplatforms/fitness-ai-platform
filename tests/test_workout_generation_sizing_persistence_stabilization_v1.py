import ast
from pathlib import Path

from fastapi.testclient import TestClient

import database
from api.main import app
from models.workout_plan_models import CandidateWorkoutExercise, CandidateWorkoutPlan
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.user_state_service import build_user_health_state
from services.workout_plan_service import (
    approve_candidate_workout_plan,
    build_approved_workout_plan,
    build_workout_context,
)

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


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    seed_qa_scenarios()


def _save_home_gym_profile(user_id: int = 102):
    save_equipment_profile(
        user_id=user_id,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )


def _exercise_names(plan_payload: dict) -> list[str]:
    return [exercise["name"] for exercise in plan_payload["exercises"]]


def test_preview_size_ranges_are_not_silently_collapsed_to_four(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)
    client = TestClient(app)

    counts = {}
    for size in ["quick", "standard", "full"]:
        response = client.get(
            f"/workout-plans/preview/102?workout_size_preference={size}"
        )
        assert response.status_code == 200
        payload = response.json()
        counts[size] = len(payload["approved_workout_plan"]["exercises"])
        assert payload["workout_exercise_count"]["requested_size"] == size
        assert payload["workout_exercise_count"]["final_count"] == counts[size]

    assert 3 <= counts["quick"] <= 4
    assert 4 <= counts["standard"] <= 5
    assert 6 <= counts["full"] <= 7
    assert counts["full"] > counts["standard"] >= counts["quick"]
    assert not (counts["standard"] == counts["full"] == 4)


def test_preview_refresh_preserves_selected_size_range_intent(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)
    client = TestClient(app)

    initial = client.get(
        "/workout-plans/preview/102?workout_size_preference=full&preview_variation_index=0"
    ).json()["approved_workout_plan"]
    refreshed = client.get(
        "/workout-plans/preview/102?workout_size_preference=full&preview_variation_index=1"
    ).json()["approved_workout_plan"]
    repeated = client.get(
        "/workout-plans/preview/102?workout_size_preference=full&preview_variation_index=1"
    ).json()["approved_workout_plan"]

    assert 6 <= len(initial["exercises"]) <= 7
    assert 6 <= len(refreshed["exercises"]) <= 7
    assert _exercise_names(refreshed) == _exercise_names(repeated)
    assert _exercise_names(initial) != _exercise_names(refreshed)


def test_selected_and_active_state_ignore_later_preview_variations(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)
    client = TestClient(app)

    preview = client.get(
        "/workout-plans/preview/102?workout_size_preference=full&preview_variation_index=0"
    ).json()["approved_workout_plan"]
    selected = client.post(
        "/workout-plans/102/select-preview", json={"approved_workout_plan": preview}
    ).json()
    selected_names = [exercise["name"] for exercise in selected["planned_exercises"]]

    varied_preview = client.get(
        "/workout-plans/preview/102?workout_size_preference=full&preview_variation_index=1"
    ).json()["approved_workout_plan"]
    assert _exercise_names(varied_preview) != selected_names

    current = client.get("/workout-plans/current/102").json()["current_execution_state"]
    assert [
        exercise["name"] for exercise in current["planned_exercises"]
    ] == selected_names

    plan_instance_id = current["workout_plan_instance"]["id"]
    started = client.post(f"/workout-plans/{plan_instance_id}/start").json()
    assert [
        exercise["name"] for exercise in started["planned_exercises"]
    ] == selected_names

    current_after_start = client.get("/workout-plans/current/102").json()[
        "current_execution_state"
    ]
    assert [
        exercise["name"] for exercise in current_after_start["planned_exercises"]
    ] == selected_names


def test_internal_and_external_rotation_exercise_names_are_valid(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    context = build_workout_context(build_user_health_state(102))
    approved_base = build_approved_workout_plan(build_user_health_state(102))

    candidate = CandidateWorkoutPlan(
        title=approved_base.title,
        session_focus=approved_base.session_focus,
        duration_minutes=approved_base.duration_minutes,
        exercises=[
            CandidateWorkoutExercise(
                name="Cable Internal Rotation",
                sets=2,
                reps_min=10,
                reps_max=12,
                rir_min=2,
                rir_max=4,
                notes="Use controlled shoulder rotation and smooth reps.",
                equipment_required=["cable"],
            ),
            CandidateWorkoutExercise(
                name="Cable External Rotation",
                sets=2,
                reps_min=10,
                reps_max=12,
                rir_min=2,
                rir_max=4,
                notes="Use controlled shoulder rotation and smooth reps.",
                equipment_required=["cable"],
            ),
            *[
                CandidateWorkoutExercise(
                    name=exercise.name,
                    sets=exercise.sets,
                    reps_min=exercise.reps_min,
                    reps_max=exercise.reps_max,
                    rir_min=exercise.rir_min,
                    rir_max=exercise.rir_max,
                    notes=exercise.notes,
                    equipment_required=exercise.equipment_required,
                )
                for exercise in approved_base.exercises[:2]
            ],
        ],
        warmup=approved_base.warmup,
        cooldown=approved_base.cooldown,
        progression_guidance=approved_base.progression_guidance,
        rationale=approved_base.rationale,
        confidence=approved_base.confidence,
    )

    approved = approve_candidate_workout_plan(candidate, context)

    assert [exercise.name for exercise in approved.exercises[:2]] == [
        "Cable Internal Rotation",
        "Cable External Rotation",
    ]


def _function_source(name: str) -> str:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


def test_streamlit_selected_branch_does_not_generate_preview_state():
    plan_source = _function_source("render_workout_plan_section")
    selected_branch = plan_source.split("if active_plan_response:", maxsplit=1)[1]
    selected_branch = selected_branch.split("else:", maxsplit=1)[0]

    assert (
        "render_selected_workout_plan_controls(active_plan_response)" in selected_branch
    )
    assert "get_stable_workout_plan_preview(" not in selected_branch
    assert "Show different exercises" not in selected_branch
