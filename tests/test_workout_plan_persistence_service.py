from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.workout_plan_persistence_service import (
    count_workout_plan_instances,
    get_planned_workout_exercises,
    get_workout_execution_session,
    get_workout_plan_instance,
    select_current_workout_plan,
)
from services.workout_service import create_workout_session


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()


def test_preview_endpoint_remains_stateless(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    before_count = count_workout_plan_instances(105)
    response = client.get("/workout-plans/preview/105")
    after_count = count_workout_plan_instances(105)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert before_count == 0
    assert after_count == 0


def test_select_workout_plan_creates_instance_snapshot_and_execution_session(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    selected = select_current_workout_plan(105)
    instance = selected["workout_plan_instance"]
    planned_exercises = selected["planned_exercises"]
    execution_session = selected["execution_session"]
    approved_plan = selected["approved_workout_plan"]

    assert instance.user_id == 105
    assert instance.status == "selected"
    assert instance.scenario == "data_quality_limited"
    assert instance.confidence == "Low"
    assert instance.title == approved_plan.title
    assert instance.approved_workout_plan.title == approved_plan.title
    assert instance.approved_workout_plan.scenario == approved_plan.scenario
    assert planned_exercises
    assert len(planned_exercises) == len(approved_plan.exercises)
    assert planned_exercises[0].exercise_order == 1
    assert planned_exercises[0].name == approved_plan.exercises[0].name
    assert execution_session.status == "selected"
    assert execution_session.user_id == 105
    assert execution_session.workout_plan_instance_id == instance.id
    assert execution_session.workout_session_id is None


def test_selected_plan_can_be_read_back_from_database(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(102)
    instance_id = selected["workout_plan_instance"].id

    stored_instance = get_workout_plan_instance(instance_id)
    stored_exercises = get_planned_workout_exercises(instance_id)
    stored_execution_session = get_workout_execution_session(instance_id)

    assert stored_instance is not None
    assert stored_instance.user_id == 102
    assert stored_instance.status == "selected"
    assert stored_instance.approved_workout_plan.exercises
    assert stored_exercises
    assert stored_execution_session is not None
    assert stored_execution_session.status == "selected"


def test_select_workout_plan_endpoint_smoke(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.post("/workout-plans/105/select")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 105
    assert payload["scenario"] == "data_quality_limited"
    assert payload["confidence"] == "Low"
    assert payload["workout_plan_instance"]["status"] == "selected"
    assert payload["workout_plan_instance"]["approved_workout_plan"]
    assert payload["planned_exercises"]
    assert payload["execution_session"]["status"] == "selected"
    assert payload["execution_session"]["workout_session_id"] is None


def test_select_rebuilds_server_side_and_respects_equipment_profile(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    save_equipment_profile(
        user_id=105,
        training_environment="bodyweight_only",
        available_equipment=[],
        unavailable_equipment=[],
    )

    selected = select_current_workout_plan(105)
    planned_exercises = selected["planned_exercises"]
    approved_plan = selected["approved_workout_plan"]

    assert approved_plan.exercises
    for exercise in approved_plan.exercises:
        assert exercise.equipment_required == ["bodyweight"]
    for planned_exercise in planned_exercises:
        assert planned_exercise.equipment_required == ["bodyweight"]


def test_manual_workout_logging_still_works_independently(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(105)

    session_id = create_workout_session(
        user_id=105,
        workout_name="Manual QA Workout",
        duration_minutes=30,
        notes="Manual logging remains independent.",
    )
    execution_session = get_workout_execution_session(
        selected["workout_plan_instance"].id
    )

    assert session_id
    assert execution_session is not None
    assert execution_session.workout_session_id is None
    assert execution_session.status == "selected"


def test_start_missing_workout_plan_endpoint_returns_404(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.post("/workout-plans/999999/start")

    assert response.status_code == 404


def test_start_selected_workout_plan_updates_statuses_and_creates_draft_session(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(105)
    instance_id = selected["workout_plan_instance"].id

    from services.workout_plan_persistence_service import start_selected_workout_plan

    started = start_selected_workout_plan(instance_id)
    instance = started["workout_plan_instance"]
    execution_session = started["execution_session"]

    assert instance.status == "started"
    assert execution_session.status == "started"
    assert execution_session.started_at is not None
    assert execution_session.workout_session_id is not None

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM workout_sessions WHERE id = ?",
        (execution_session.workout_session_id,),
    )
    workout_session = cursor.fetchone()
    conn.close()

    assert workout_session is not None
    assert workout_session["user_id"] == 105
    assert workout_session["workout_name"] == instance.title


def test_start_workout_plan_endpoint_smoke(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)
    selected_response = client.post("/workout-plans/105/select")
    instance_id = selected_response.json()["workout_plan_instance"]["id"]

    response = client.post(f"/workout-plans/{instance_id}/start")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["workout_plan_instance_id"] == instance_id
    assert payload["user_id"] == 105
    assert payload["scenario"] == "data_quality_limited"
    assert payload["workout_plan_instance"]["status"] == "started"
    assert payload["execution_session"]["status"] == "started"
    assert payload["execution_session"]["started_at"] is not None
    assert payload["execution_session"]["workout_session_id"] is not None
    assert payload["planned_exercises"]
    assert payload["approved_workout_plan"]


def test_start_rejects_already_started_workout_plan(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)
    selected_response = client.post("/workout-plans/105/select")
    instance_id = selected_response.json()["workout_plan_instance"]["id"]

    first_response = client.post(f"/workout-plans/{instance_id}/start")
    second_response = client.post(f"/workout-plans/{instance_id}/start")

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert (
        "Only selected workout plans can be started" in second_response.json()["detail"]
    )


def test_start_preserves_selected_plan_exercises(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(102)
    instance_id = selected["workout_plan_instance"].id
    before_exercises = get_planned_workout_exercises(instance_id)

    from services.workout_plan_persistence_service import start_selected_workout_plan

    start_selected_workout_plan(instance_id)
    after_exercises = get_planned_workout_exercises(instance_id)

    assert [exercise.name for exercise in after_exercises] == [
        exercise.name for exercise in before_exercises
    ]
    assert [exercise.exercise_order for exercise in after_exercises] == [
        exercise.exercise_order for exercise in before_exercises
    ]


def test_manual_workout_logging_still_independent_after_started_plan(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(105)
    instance_id = selected["workout_plan_instance"].id

    from services.workout_plan_persistence_service import start_selected_workout_plan

    started = start_selected_workout_plan(instance_id)
    linked_session_id = started["execution_session"].workout_session_id

    manual_session_id = create_workout_session(
        user_id=105,
        workout_name="Manual QA Workout After Plan Start",
        duration_minutes=25,
        notes="Manual logging remains independent after plan start.",
    )

    execution_session = get_workout_execution_session(instance_id)

    assert linked_session_id is not None
    assert manual_session_id != linked_session_id
    assert execution_session is not None
    assert execution_session.workout_session_id == linked_session_id
    assert execution_session.status == "started"
