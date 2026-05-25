from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.workout_plan_persistence_service import (
    WorkoutPlanInvalidStatusError,
    WorkoutPlanValidationError,
    count_workout_plan_instances,
    get_actual_sets,
    get_execution_state,
    get_planned_workout_exercises,
    get_workout_execution_session,
    get_workout_plan_instance,
    log_actual_set,
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


def _started_plan(tmp_path, monkeypatch, user_id=105):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(user_id)
    instance_id = selected["workout_plan_instance"].id

    from services.workout_plan_persistence_service import start_selected_workout_plan

    started = start_selected_workout_plan(instance_id)
    return instance_id, started


def test_started_plan_can_read_execution_state(tmp_path, monkeypatch):
    instance_id, _started = _started_plan(tmp_path, monkeypatch)

    execution_state = get_execution_state(instance_id)

    assert execution_state["workout_plan_instance"].status == "started"
    assert execution_state["execution_session"].status == "started"
    assert execution_state["planned_exercises"]
    assert execution_state["actual_sets"] == []


def test_actual_set_can_be_logged_against_planned_exercise(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    result = log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "set_number": 1,
            "actual_reps": planned_exercise.reps_min,
            "actual_weight": 35.0,
            "actual_rir": planned_exercise.rir_max,
            "completed": True,
        },
    )

    actual_set = result["actual_set"]

    assert actual_set.planned_workout_exercise_id == planned_exercise.id
    assert actual_set.workout_execution_session_id == started["execution_session"].id
    assert (
        actual_set.workout_session_id == started["execution_session"].workout_session_id
    )
    assert actual_set.workout_set_id is None
    assert actual_set.exercise_name == planned_exercise.name
    assert actual_set.actual_reps == planned_exercise.reps_min
    assert actual_set.actual_weight == 35.0
    assert actual_set.actual_rir == planned_exercise.rir_max
    assert actual_set.completed is True
    assert actual_set.skipped is False


def test_first_actual_set_transitions_plan_and_session_to_in_progress(
    tmp_path, monkeypatch
):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    result = log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "actual_reps": planned_exercise.reps_min,
            "actual_rir": planned_exercise.rir_max,
        },
    )
    execution_state = result["execution_state"]

    assert execution_state["workout_plan_instance"].status == "in_progress"
    assert execution_state["execution_session"].status == "in_progress"


def test_actual_set_may_differ_from_planned_reps_and_rir(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    result = log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "actual_reps": planned_exercise.reps_max + 2,
            "actual_weight": 50.0,
            "actual_rir": max(planned_exercise.rir_min - 1, 0),
            "notes": "Felt stronger than planned.",
        },
    )

    actual_set = result["actual_set"]

    assert actual_set.actual_reps == planned_exercise.reps_max + 2
    assert actual_set.actual_rir == max(planned_exercise.rir_min - 1, 0)
    assert actual_set.notes == "Felt stronger than planned."


def test_skipped_planned_exercise_can_be_recorded(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    result = log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "set_number": 1,
            "completed": False,
            "skipped": True,
            "notes": "Skipped due to time.",
        },
    )

    actual_set = result["actual_set"]

    assert actual_set.skipped is True
    assert actual_set.completed is False
    assert actual_set.actual_reps is None
    assert actual_set.actual_weight is None
    assert actual_set.actual_rir is None


def test_substituted_exercise_can_be_recorded(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    result = log_actual_set(
        instance_id,
        {
            "substitution_for_planned_exercise_id": planned_exercise.id,
            "exercise_name": "Bodyweight Squat",
            "set_number": 1,
            "actual_reps": 12,
            "actual_rir": 3,
            "notes": "Substituted for available equipment.",
        },
    )

    actual_set = result["actual_set"]

    assert actual_set.planned_workout_exercise_id is None
    assert actual_set.substitution_for_planned_exercise_id == planned_exercise.id
    assert actual_set.exercise_name == "Bodyweight Squat"
    assert actual_set.planned_reps_min == planned_exercise.reps_min
    assert actual_set.planned_rir_max == planned_exercise.rir_max


def test_completed_and_skipped_cannot_both_be_true(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    try:
        log_actual_set(
            instance_id,
            {
                "planned_workout_exercise_id": planned_exercise.id,
                "completed": True,
                "skipped": True,
            },
        )
    except WorkoutPlanValidationError as exc:
        assert "completed and skipped cannot both be true" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanValidationError")


def test_invalid_actual_rir_is_rejected(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    try:
        log_actual_set(
            instance_id,
            {
                "planned_workout_exercise_id": planned_exercise.id,
                "actual_reps": 10,
                "actual_rir": 11,
            },
        )
    except WorkoutPlanValidationError as exc:
        assert "actual_rir must be between 0 and 10" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanValidationError")


def test_negative_reps_and_weight_are_rejected(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    try:
        log_actual_set(
            instance_id,
            {
                "planned_workout_exercise_id": planned_exercise.id,
                "actual_reps": -1,
                "actual_weight": 10,
                "actual_rir": 3,
            },
        )
    except WorkoutPlanValidationError as exc:
        assert "actual_reps must be non-negative" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanValidationError")

    try:
        log_actual_set(
            instance_id,
            {
                "planned_workout_exercise_id": planned_exercise.id,
                "actual_reps": 10,
                "actual_weight": -5,
                "actual_rir": 3,
            },
        )
    except WorkoutPlanValidationError as exc:
        assert "actual_weight must be non-negative" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanValidationError")


def test_planned_exercise_from_another_plan_is_rejected(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected_a = select_current_workout_plan(101)
    selected_b = select_current_workout_plan(102)

    from services.workout_plan_persistence_service import start_selected_workout_plan

    start_selected_workout_plan(selected_a["workout_plan_instance"].id)
    other_planned_exercise = selected_b["planned_exercises"][0]

    try:
        log_actual_set(
            selected_a["workout_plan_instance"].id,
            {
                "planned_workout_exercise_id": other_planned_exercise.id,
                "actual_reps": 8,
                "actual_rir": 3,
            },
        )
    except WorkoutPlanValidationError as exc:
        assert "planned_workout_exercise_id must belong" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanValidationError")


def test_cannot_log_actual_set_before_start(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(105)
    planned_exercise = selected["planned_exercises"][0]

    try:
        log_actual_set(
            selected["workout_plan_instance"].id,
            {
                "planned_workout_exercise_id": planned_exercise.id,
                "actual_reps": 8,
                "actual_rir": 3,
            },
        )
    except WorkoutPlanInvalidStatusError as exc:
        assert "started or in-progress" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanInvalidStatusError")


def test_workout_plan_execution_endpoint_returns_actual_sets(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    client = TestClient(app)
    planned_exercise = started["planned_exercises"][0]

    create_response = client.post(
        f"/workout-plans/{instance_id}/actual-sets",
        json={
            "planned_workout_exercise_id": planned_exercise.id,
            "actual_reps": planned_exercise.reps_min,
            "actual_weight": 40.0,
            "actual_rir": planned_exercise.rir_max,
        },
    )
    execution_response = client.get(f"/workout-plans/{instance_id}/execution")

    assert create_response.status_code == 200
    assert execution_response.status_code == 200
    payload = execution_response.json()
    assert payload["success"] is True
    assert payload["workout_plan_instance"]["status"] == "in_progress"
    assert payload["execution_session"]["status"] == "in_progress"
    assert len(payload["actual_sets"]) == 1
    assert payload["actual_sets"][0]["actual_reps"] == planned_exercise.reps_min


def test_actual_sets_can_be_read_by_execution_session_id(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]
    execution_session_id = started["execution_session"].id

    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "actual_reps": 10,
            "actual_rir": 3,
        },
    )

    actual_sets = get_actual_sets(execution_session_id=execution_session_id)

    assert len(actual_sets) == 1
    assert actual_sets[0].planned_workout_exercise_id == planned_exercise.id
