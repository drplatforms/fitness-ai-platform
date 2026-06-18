from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.workout_plan_persistence_service import (
    WorkoutPlanInvalidStatusError,
    WorkoutPlanValidationError,
    build_planned_vs_actual_summary,
    count_workout_plan_instances,
    get_actual_sets,
    get_execution_state,
    get_planned_workout_exercises,
    get_workout_execution_session,
    get_workout_plan_history,
    get_workout_plan_instance,
    log_actual_set,
    select_current_workout_plan,
    update_actual_set,
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


def test_planned_vs_actual_summary_counts_planned_exercises_and_sets(
    tmp_path, monkeypatch
):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercises = started["planned_exercises"]

    summary = build_planned_vs_actual_summary(instance_id)

    assert summary.planned_exercise_count == len(planned_exercises)
    assert summary.planned_set_count == sum(
        exercise.sets for exercise in planned_exercises
    )
    assert summary.actual_set_count == 0
    assert summary.completed_set_count == 0
    assert summary.completion_percentage == 0.0
    assert "empty_completion" in summary.deviation_flags
    assert "incomplete_logging" in summary.deviation_flags


def test_planned_vs_actual_summary_counts_completed_actual_sets(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "set_number": 1,
            "actual_reps": planned_exercise.reps_min,
            "actual_weight": 35.0,
            "actual_rir": planned_exercise.rir_max,
        },
    )
    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "set_number": 2,
            "actual_reps": planned_exercise.reps_max,
            "actual_weight": 35.0,
            "actual_rir": planned_exercise.rir_max,
        },
    )

    summary = build_planned_vs_actual_summary(instance_id)

    assert summary.completed_exercise_count == 1
    assert summary.actual_set_count == 2
    assert summary.completed_set_count == 2
    assert summary.skipped_set_count == 0
    assert summary.completion_percentage == round(
        (2 / summary.planned_set_count) * 100, 2
    )
    assert summary.sets_inside_planned_reps == 2


def test_planned_vs_actual_summary_excludes_skipped_from_actual_set_count(
    tmp_path, monkeypatch
):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "completed": False,
            "skipped": True,
            "notes": "Skipped due to time.",
        },
    )

    summary = build_planned_vs_actual_summary(instance_id)

    assert summary.actual_set_count == 0
    assert summary.completed_set_count == 0
    assert summary.skipped_set_count == 1
    assert summary.skipped_exercise_count == 1
    assert "skipped_exercises_present" in summary.deviation_flags


def test_planned_vs_actual_summary_counts_substitutions(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    log_actual_set(
        instance_id,
        {
            "substitution_for_planned_exercise_id": planned_exercise.id,
            "exercise_name": "Bodyweight Squat",
            "actual_reps": planned_exercise.reps_min,
            "actual_rir": planned_exercise.rir_max,
        },
    )

    summary = build_planned_vs_actual_summary(instance_id)

    assert summary.substituted_exercise_count == 1
    assert summary.actual_set_count == 1
    assert summary.completed_set_count == 1
    assert "substitutions_present" in summary.deviation_flags


def test_planned_vs_actual_summary_average_planned_rir_weighted_by_sets(
    tmp_path, monkeypatch
):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercises = started["planned_exercises"]
    expected = round(
        sum(
            ((exercise.rir_min + exercise.rir_max) / 2) * exercise.sets
            for exercise in planned_exercises
        )
        / sum(exercise.sets for exercise in planned_exercises),
        2,
    )

    summary = build_planned_vs_actual_summary(instance_id)

    assert summary.average_planned_rir == expected


def test_planned_vs_actual_summary_average_actual_rir_and_harder_flag(
    tmp_path, monkeypatch
):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "actual_reps": planned_exercise.reps_min,
            "actual_rir": max(planned_exercise.rir_min - 1, 0),
        },
    )

    summary = build_planned_vs_actual_summary(instance_id)

    assert summary.average_actual_rir == max(planned_exercise.rir_min - 1, 0)
    assert summary.rir_deviation is not None
    assert summary.rir_deviation < 0
    assert "actual_effort_harder_than_planned" in summary.deviation_flags


def test_planned_vs_actual_summary_easier_effort_flag(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "actual_reps": planned_exercise.reps_min,
            "actual_rir": min(planned_exercise.rir_max + 3, 10),
        },
    )

    summary = build_planned_vs_actual_summary(instance_id)

    assert summary.rir_deviation is not None
    assert summary.rir_deviation > 0
    assert "actual_effort_easier_than_planned" in summary.deviation_flags


def test_planned_vs_actual_summary_rep_deviation_counts_below_inside_above(
    tmp_path, monkeypatch
):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    for set_number, reps in enumerate(
        [
            planned_exercise.reps_min - 1,
            planned_exercise.reps_min,
            planned_exercise.reps_max + 1,
        ],
        start=1,
    ):
        log_actual_set(
            instance_id,
            {
                "planned_workout_exercise_id": planned_exercise.id,
                "set_number": set_number,
                "actual_reps": reps,
                "actual_rir": planned_exercise.rir_max,
            },
        )

    summary = build_planned_vs_actual_summary(instance_id)

    assert summary.sets_below_planned_reps == 1
    assert summary.sets_inside_planned_reps == 1
    assert summary.sets_above_planned_reps == 1
    assert summary.rep_deviation == {
        "sets_below_planned_reps": 1,
        "sets_inside_planned_reps": 1,
        "sets_above_planned_reps": 1,
    }
    assert "reps_below_plan" in summary.deviation_flags
    assert "reps_above_plan" in summary.deviation_flags


def test_planned_vs_actual_summary_flags_missing_actual_rir_and_reps(
    tmp_path, monkeypatch
):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]

    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "completed": False,
            "skipped": False,
            "notes": "Started logging but details are incomplete.",
        },
    )

    summary = build_planned_vs_actual_summary(instance_id)

    assert "missing_actual_rir" in summary.deviation_flags
    assert "missing_actual_reps" in summary.deviation_flags
    assert "incomplete_logging" in summary.deviation_flags


def test_planned_vs_actual_summary_keeps_manual_logging_independent(
    tmp_path, monkeypatch
):
    instance_id, _started = _started_plan(tmp_path, monkeypatch)
    manual_session_id = create_workout_session(
        user_id=105,
        workout_name="Manual Session Not Part Of Plan Summary",
        duration_minutes=20,
        notes="Manual logging remains independent.",
    )

    summary = build_planned_vs_actual_summary(instance_id)

    assert manual_session_id
    assert summary.actual_set_count == 0
    assert "empty_completion" in summary.deviation_flags


def _in_progress_plan(tmp_path, monkeypatch, user_id=105):
    instance_id, started = _started_plan(tmp_path, monkeypatch, user_id=user_id)
    planned_exercise = started["planned_exercises"][0]
    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "set_number": 1,
            "actual_reps": planned_exercise.reps_min,
            "actual_weight": 35.0,
            "actual_rir": planned_exercise.rir_max,
        },
    )
    return instance_id, started


def test_in_progress_plan_can_complete(tmp_path, monkeypatch):
    from services.workout_plan_persistence_service import complete_workout_plan

    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)

    result = complete_workout_plan(instance_id)

    assert result["workout_plan_instance"].status == "completed"
    assert result["execution_session"].status == "completed"
    assert result["workout_plan_instance"].completed_at is not None
    assert result["execution_session"].completed_at is not None
    assert result["planned_vs_actual_summary"].completed_set_count == 1


def test_complete_endpoint_returns_summary(tmp_path, monkeypatch):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.post(f"/workout-plans/{instance_id}/complete")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["workout_plan_instance"]["status"] == "completed"
    assert payload["execution_session"]["status"] == "completed"
    assert payload["workout_plan_instance"]["completed_at"] is not None
    assert payload["execution_session"]["completed_at"] is not None
    assert payload["planned_vs_actual_summary"]["completed_set_count"] == 1


def test_selected_plan_cannot_complete(tmp_path, monkeypatch):
    from services.workout_plan_persistence_service import complete_workout_plan

    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(105)
    instance_id = selected["workout_plan_instance"].id

    try:
        complete_workout_plan(instance_id)
    except WorkoutPlanInvalidStatusError as exc:
        assert "Only in-progress workout plans can be completed" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanInvalidStatusError")


def test_started_plan_with_no_actual_sets_cannot_complete(tmp_path, monkeypatch):
    from services.workout_plan_persistence_service import complete_workout_plan

    instance_id, _started = _started_plan(tmp_path, monkeypatch)

    try:
        complete_workout_plan(instance_id)
    except WorkoutPlanInvalidStatusError as exc:
        assert "Only in-progress workout plans can be completed" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanInvalidStatusError")


def test_completed_plan_cannot_complete_again(tmp_path, monkeypatch):
    from services.workout_plan_persistence_service import complete_workout_plan

    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)

    first_result = complete_workout_plan(instance_id)
    assert first_result["workout_plan_instance"].status == "completed"

    try:
        complete_workout_plan(instance_id)
    except WorkoutPlanInvalidStatusError as exc:
        assert "Only in-progress workout plans can be completed" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanInvalidStatusError")


def test_completion_preserves_actual_set_rows(tmp_path, monkeypatch):
    from services.workout_plan_persistence_service import complete_workout_plan

    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    before_actual_sets = get_actual_sets(plan_instance_id=instance_id)

    complete_workout_plan(instance_id)
    after_actual_sets = get_actual_sets(plan_instance_id=instance_id)

    assert len(before_actual_sets) == 1
    assert len(after_actual_sets) == 1
    assert after_actual_sets[0].id == before_actual_sets[0].id
    assert after_actual_sets[0].actual_reps == before_actual_sets[0].actual_reps


def test_skipped_and_unlogged_planned_exercises_do_not_block_completion(
    tmp_path, monkeypatch
):
    from services.workout_plan_persistence_service import complete_workout_plan

    instance_id, started = _started_plan(tmp_path, monkeypatch)
    first_planned_exercise = started["planned_exercises"][0]
    second_planned_exercise = started["planned_exercises"][1]

    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": first_planned_exercise.id,
            "actual_reps": first_planned_exercise.reps_min,
            "actual_rir": first_planned_exercise.rir_max,
        },
    )
    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": second_planned_exercise.id,
            "completed": False,
            "skipped": True,
            "notes": "Skipped due to time.",
        },
    )

    result = complete_workout_plan(instance_id)
    summary = result["planned_vs_actual_summary"]

    assert result["workout_plan_instance"].status == "completed"
    assert summary.skipped_set_count == 1
    assert "skipped_exercises_present" in summary.deviation_flags
    assert "incomplete_logging" in summary.deviation_flags


def test_complete_missing_plan_endpoint_returns_404(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.post("/workout-plans/999999/complete")

    assert response.status_code == 404


def test_completion_keeps_manual_workout_logging_independent(tmp_path, monkeypatch):
    from services.workout_plan_persistence_service import complete_workout_plan

    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    manual_session_id = create_workout_session(
        user_id=105,
        workout_name="Manual Session During Plan Completion",
        duration_minutes=20,
        notes="Manual logging remains independent after completion.",
    )

    result = complete_workout_plan(instance_id)

    assert manual_session_id
    assert result["execution_session"].workout_session_id != manual_session_id
    assert result["workout_plan_instance"].status == "completed"


def test_planned_vs_actual_endpoint_returns_summary_for_in_progress_plan(
    tmp_path, monkeypatch
):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get(f"/workout-plans/{instance_id}/planned-vs-actual")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["workout_plan_instance"]["status"] == "in_progress"
    assert payload["execution_session"]["status"] == "in_progress"
    assert payload["planned_vs_actual_summary"]["completed_set_count"] == 1
    assert payload["planned_exercises"]
    assert payload["actual_sets"]


def test_planned_vs_actual_endpoint_returns_summary_for_completed_plan(
    tmp_path, monkeypatch
):
    from services.workout_plan_persistence_service import complete_workout_plan

    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    complete_workout_plan(instance_id)
    client = TestClient(app)

    response = client.get(f"/workout-plans/{instance_id}/planned-vs-actual")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["workout_plan_instance"]["status"] == "completed"
    assert payload["execution_session"]["status"] == "completed"
    assert payload["planned_vs_actual_summary"]["completed_set_count"] == 1


def test_planned_vs_actual_missing_plan_returns_404(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/workout-plans/999999/planned-vs-actual")

    assert response.status_code == 404


def test_planned_vs_actual_plan_without_execution_session_returns_clear_error(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(105)
    instance_id = selected["workout_plan_instance"].id

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM workout_execution_sessions WHERE workout_plan_instance_id = ?",
        (instance_id,),
    )
    conn.commit()
    conn.close()

    client = TestClient(app)
    response = client.get(f"/workout-plans/{instance_id}/planned-vs-actual")

    assert response.status_code == 400
    assert "has no execution session" in response.json()["detail"]


def test_planned_vs_actual_selected_plan_is_rejected(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(105)
    instance_id = selected["workout_plan_instance"].id
    client = TestClient(app)

    response = client.get(f"/workout-plans/{instance_id}/planned-vs-actual")

    assert response.status_code == 400
    assert "started, in-progress, or completed" in response.json()["detail"]


def test_planned_vs_actual_started_plan_returns_empty_summary_flags(
    tmp_path, monkeypatch
):
    instance_id, _started = _started_plan(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get(f"/workout-plans/{instance_id}/planned-vs-actual")

    assert response.status_code == 200
    payload = response.json()
    summary = payload["planned_vs_actual_summary"]
    assert payload["workout_plan_instance"]["status"] == "started"
    assert summary["actual_set_count"] == 0
    assert "empty_completion" in summary["deviation_flags"]
    assert "incomplete_logging" in summary["deviation_flags"]


def test_planned_vs_actual_endpoint_summary_matches_service(tmp_path, monkeypatch):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    expected_summary = build_planned_vs_actual_summary(instance_id)
    client = TestClient(app)

    response = client.get(f"/workout-plans/{instance_id}/planned-vs-actual")

    assert response.status_code == 200
    payload = response.json()
    summary = payload["planned_vs_actual_summary"]
    assert summary["completion_percentage"] == expected_summary.completion_percentage
    assert summary["completed_set_count"] == expected_summary.completed_set_count
    assert summary["planned_set_count"] == expected_summary.planned_set_count
    assert summary["deviation_flags"] == expected_summary.deviation_flags


def test_planned_vs_actual_endpoint_does_not_mutate_planned_or_actual_rows(
    tmp_path, monkeypatch
):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    planned_before = get_planned_workout_exercises(instance_id)
    actual_before = get_actual_sets(plan_instance_id=instance_id)
    client = TestClient(app)

    response = client.get(f"/workout-plans/{instance_id}/planned-vs-actual")

    planned_after = get_planned_workout_exercises(instance_id)
    actual_after = get_actual_sets(plan_instance_id=instance_id)
    assert response.status_code == 200
    assert [exercise.id for exercise in planned_after] == [
        exercise.id for exercise in planned_before
    ]
    assert [actual_set.id for actual_set in actual_after] == [
        actual_set.id for actual_set in actual_before
    ]


def test_planned_vs_actual_endpoint_keeps_manual_logging_independent(
    tmp_path, monkeypatch
):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    manual_session_id = create_workout_session(
        user_id=105,
        workout_name="Manual Session Near Planned Summary",
        duration_minutes=20,
        notes="Manual logging remains independent from planned-vs-actual.",
    )
    client = TestClient(app)

    response = client.get(f"/workout-plans/{instance_id}/planned-vs-actual")

    assert response.status_code == 200
    assert manual_session_id
    assert response.json()["planned_vs_actual_summary"]["actual_set_count"] == 1


def test_in_progress_actual_set_can_be_edited(tmp_path, monkeypatch):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    actual_set = get_actual_sets(plan_instance_id=instance_id)[0]

    result = update_actual_set(
        instance_id,
        actual_set.id,
        {
            "actual_reps": 12,
            "actual_weight": 42.5,
            "actual_rir": 2,
            "notes": "Corrected after review.",
        },
    )

    updated = result["actual_set"]
    assert updated.id == actual_set.id
    assert updated.actual_reps == 12
    assert updated.actual_weight == 42.5
    assert updated.actual_rir == 2
    assert updated.notes == "Corrected after review."
    assert result["workout_plan_instance"].status == "in_progress"


def test_completed_actual_set_can_be_corrected_and_preserves_completion(
    tmp_path, monkeypatch
):
    from services.workout_plan_persistence_service import complete_workout_plan

    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    complete_result = complete_workout_plan(instance_id)
    completed_at = complete_result["workout_plan_instance"].completed_at
    execution_completed_at = complete_result["execution_session"].completed_at
    actual_set = get_actual_sets(plan_instance_id=instance_id)[0]

    result = update_actual_set(
        instance_id,
        actual_set.id,
        {
            "actual_reps": 11,
            "actual_weight": 40.0,
            "actual_rir": 3,
        },
    )

    assert result["actual_set"].actual_reps == 11
    assert result["workout_plan_instance"].status == "completed"
    assert result["execution_session"].status == "completed"
    assert result["workout_plan_instance"].completed_at == completed_at
    assert result["execution_session"].completed_at == execution_completed_at


def test_actual_set_edit_endpoint_returns_updated_summary(tmp_path, monkeypatch):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    actual_set = get_actual_sets(plan_instance_id=instance_id)[0]
    client = TestClient(app)

    response = client.patch(
        f"/workout-plans/{instance_id}/actual-sets/{actual_set.id}",
        json={"actual_reps": 1, "actual_rir": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["actual_set"]["actual_reps"] == 1
    assert payload["planned_vs_actual_summary"]["sets_below_planned_reps"] == 1
    assert "reps_below_plan" in payload["planned_vs_actual_summary"]["deviation_flags"]


def test_selected_plan_actual_set_edit_is_rejected(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(105)

    try:
        update_actual_set(
            selected["workout_plan_instance"].id,
            1,
            {"actual_reps": 10},
        )
    except WorkoutPlanInvalidStatusError as exc:
        assert "in-progress or completed workout plans" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanInvalidStatusError")


def test_started_plan_actual_set_edit_is_rejected(tmp_path, monkeypatch):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    actual_set_result = log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": started["planned_exercises"][0].id,
            "actual_reps": started["planned_exercises"][0].reps_min,
            "actual_rir": started["planned_exercises"][0].rir_max,
        },
    )
    actual_set = actual_set_result["actual_set"]

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE workout_plan_instances SET status = ? WHERE id = ?",
        ("started", instance_id),
    )
    cursor.execute(
        """
        UPDATE workout_execution_sessions
        SET status = ?
        WHERE workout_plan_instance_id = ?
        """,
        ("started", instance_id),
    )
    conn.commit()
    conn.close()

    try:
        update_actual_set(instance_id, actual_set.id, {"actual_reps": 10})
    except WorkoutPlanInvalidStatusError as exc:
        assert "in-progress or completed workout plans" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanInvalidStatusError")


def test_actual_set_from_another_plan_edit_is_rejected(tmp_path, monkeypatch):
    first_instance_id, _first_started = _in_progress_plan(tmp_path, monkeypatch)
    second_selected = select_current_workout_plan(105)
    from services.workout_plan_persistence_service import start_selected_workout_plan

    second_started = start_selected_workout_plan(
        second_selected["workout_plan_instance"].id
    )
    second_exercise = second_started["planned_exercises"][0]
    second_result = log_actual_set(
        second_selected["workout_plan_instance"].id,
        {
            "planned_workout_exercise_id": second_exercise.id,
            "actual_reps": second_exercise.reps_min,
            "actual_rir": second_exercise.rir_max,
        },
    )

    try:
        update_actual_set(
            first_instance_id,
            second_result["actual_set"].id,
            {"actual_reps": 10},
        )
    except WorkoutPlanValidationError as exc:
        assert "actual_set_id must belong" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanValidationError")


def test_planned_exercise_from_another_plan_edit_is_rejected(tmp_path, monkeypatch):
    first_instance_id, _first_started = _in_progress_plan(tmp_path, monkeypatch)
    second_selected = select_current_workout_plan(105)
    second_planned_exercise = get_planned_workout_exercises(
        second_selected["workout_plan_instance"].id
    )[0]
    actual_set = get_actual_sets(plan_instance_id=first_instance_id)[0]

    try:
        update_actual_set(
            first_instance_id,
            actual_set.id,
            {"planned_workout_exercise_id": second_planned_exercise.id},
        )
    except WorkoutPlanValidationError as exc:
        assert "planned_workout_exercise_id must belong" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanValidationError")


def test_substitution_pointer_from_another_plan_edit_is_rejected(tmp_path, monkeypatch):
    first_instance_id, _first_started = _in_progress_plan(tmp_path, monkeypatch)
    second_selected = select_current_workout_plan(105)
    second_planned_exercise = get_planned_workout_exercises(
        second_selected["workout_plan_instance"].id
    )[0]
    actual_set = get_actual_sets(plan_instance_id=first_instance_id)[0]

    try:
        update_actual_set(
            first_instance_id,
            actual_set.id,
            {"substitution_for_planned_exercise_id": second_planned_exercise.id},
        )
    except WorkoutPlanValidationError as exc:
        assert "substitution_for_planned_exercise_id must belong" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanValidationError")


def test_completed_row_can_become_skipped(tmp_path, monkeypatch):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    actual_set = get_actual_sets(plan_instance_id=instance_id)[0]

    result = update_actual_set(
        instance_id,
        actual_set.id,
        {
            "completed": False,
            "skipped": True,
            "actual_reps": None,
            "actual_weight": None,
            "actual_rir": None,
            "notes": "Corrected as skipped.",
        },
    )

    updated = result["actual_set"]
    assert updated.completed is False
    assert updated.skipped is True
    assert updated.actual_reps is None
    assert updated.actual_rir is None
    assert result["planned_vs_actual_summary"].skipped_set_count == 1


def test_skipped_row_can_become_completed_with_required_actual_data(
    tmp_path, monkeypatch
):
    instance_id, started = _started_plan(tmp_path, monkeypatch)
    planned_exercise = started["planned_exercises"][0]
    skipped_result = log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "completed": False,
            "skipped": True,
            "notes": "Initially skipped.",
        },
    )

    result = update_actual_set(
        instance_id,
        skipped_result["actual_set"].id,
        {
            "completed": True,
            "skipped": False,
            "actual_reps": planned_exercise.reps_min,
            "actual_weight": 35.0,
            "actual_rir": planned_exercise.rir_max,
        },
    )

    updated = result["actual_set"]
    assert updated.completed is True
    assert updated.skipped is False
    assert updated.actual_reps == planned_exercise.reps_min
    assert result["planned_vs_actual_summary"].completed_set_count == 1


def test_completed_and_skipped_together_edit_is_rejected(tmp_path, monkeypatch):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    actual_set = get_actual_sets(plan_instance_id=instance_id)[0]

    try:
        update_actual_set(
            instance_id,
            actual_set.id,
            {"completed": True, "skipped": True},
        )
    except WorkoutPlanValidationError as exc:
        assert "completed and skipped cannot both be true" in str(exc)
    else:
        raise AssertionError("Expected WorkoutPlanValidationError")


def test_invalid_actual_rir_reps_weight_and_set_number_edits_are_rejected(
    tmp_path, monkeypatch
):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    actual_set = get_actual_sets(plan_instance_id=instance_id)[0]

    invalid_payloads = [
        {"actual_rir": 11},
        {"actual_reps": -1},
        {"actual_weight": -5.0},
        {"set_number": 0},
    ]

    for payload in invalid_payloads:
        try:
            update_actual_set(instance_id, actual_set.id, payload)
        except WorkoutPlanValidationError:
            pass
        else:
            raise AssertionError(f"Expected rejection for {payload}")


def test_planned_vs_actual_summary_updates_after_actual_set_correction(
    tmp_path, monkeypatch
):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    actual_set = get_actual_sets(plan_instance_id=instance_id)[0]
    before_summary = build_planned_vs_actual_summary(instance_id)

    result = update_actual_set(
        instance_id,
        actual_set.id,
        {"actual_reps": 1, "actual_rir": 1},
    )
    after_summary = result["planned_vs_actual_summary"]

    assert before_summary.sets_below_planned_reps == 0
    assert after_summary.sets_below_planned_reps == 1
    assert "reps_below_plan" in after_summary.deviation_flags
    assert "actual_effort_harder_than_planned" in after_summary.deviation_flags


def test_workout_plan_history_endpoint_returns_empty_list_for_user_with_no_plans(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/workout-plans/history/105")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 105
    assert payload["workout_plan_instances"] == []


def test_workout_plan_history_returns_selected_plan(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(105)
    instance_id = selected["workout_plan_instance"].id
    client = TestClient(app)

    response = client.get("/workout-plans/history/105")

    assert response.status_code == 200
    payload = response.json()
    history = payload["workout_plan_instances"]
    assert len(history) == 1
    item = history[0]
    assert item["workout_plan_instance"]["id"] == instance_id
    assert item["workout_plan_instance"]["status"] == "selected"
    assert item["execution_session"]["status"] == "selected"
    assert item["approved_workout_title"] == selected["approved_workout_plan"].title
    assert (
        item["approved_workout_session_focus"]
        == selected["approved_workout_plan"].session_focus
    )
    assert item["planned_vs_actual_summary"] is None


def test_workout_plan_history_returns_started_plan_without_summary(
    tmp_path, monkeypatch
):
    instance_id, _started = _started_plan(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/workout-plans/history/105")

    assert response.status_code == 200
    item = response.json()["workout_plan_instances"][0]
    assert item["workout_plan_instance"]["id"] == instance_id
    assert item["workout_plan_instance"]["status"] == "started"
    assert item["execution_session"]["status"] == "started"
    assert item["planned_vs_actual_summary"] is None


def test_workout_plan_history_returns_in_progress_plan_with_summary(
    tmp_path, monkeypatch
):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/workout-plans/history/105")

    assert response.status_code == 200
    item = response.json()["workout_plan_instances"][0]
    assert item["workout_plan_instance"]["id"] == instance_id
    assert item["workout_plan_instance"]["status"] == "in_progress"
    assert item["execution_session"]["status"] == "in_progress"
    assert item["planned_vs_actual_summary"]["completed_set_count"] == 1


def test_workout_plan_history_returns_completed_plan_with_completed_at_and_summary(
    tmp_path, monkeypatch
):
    from services.workout_plan_persistence_service import complete_workout_plan

    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    complete_workout_plan(instance_id)
    client = TestClient(app)

    response = client.get("/workout-plans/history/105")

    assert response.status_code == 200
    item = response.json()["workout_plan_instances"][0]
    assert item["workout_plan_instance"]["id"] == instance_id
    assert item["workout_plan_instance"]["status"] == "completed"
    assert item["workout_plan_instance"]["completed_at"] is not None
    assert item["execution_session"]["status"] == "completed"
    assert item["execution_session"]["completed_at"] is not None
    assert item["planned_vs_actual_summary"]["completed_set_count"] == 1


def test_workout_plan_history_sorts_newest_first(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    first = select_current_workout_plan(105)["workout_plan_instance"]
    second = select_current_workout_plan(105)["workout_plan_instance"]
    client = TestClient(app)

    response = client.get("/workout-plans/history/105")

    assert response.status_code == 200
    ids = [
        item["workout_plan_instance"]["id"]
        for item in response.json()["workout_plan_instances"]
    ]
    assert ids == [second.id, first.id]


def test_workout_plan_history_service_matches_endpoint_summary(tmp_path, monkeypatch):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    history = get_workout_plan_history(105)
    client = TestClient(app)

    response = client.get("/workout-plans/history/105")

    assert response.status_code == 200
    service_summary = history[0]["planned_vs_actual_summary"]
    endpoint_summary = response.json()["workout_plan_instances"][0][
        "planned_vs_actual_summary"
    ]
    assert history[0]["workout_plan_instance"].id == instance_id
    assert (
        endpoint_summary["completed_set_count"] == service_summary.completed_set_count
    )
    assert endpoint_summary["planned_set_count"] == service_summary.planned_set_count


def test_workout_plan_history_keeps_manual_logging_independent(tmp_path, monkeypatch):
    instance_id, _started = _in_progress_plan(tmp_path, monkeypatch)
    manual_session_id = create_workout_session(
        user_id=105,
        workout_name="Manual Workout Near Plan History",
        duration_minutes=20,
        notes="Manual logging remains independent from plan history.",
    )
    client = TestClient(app)

    response = client.get("/workout-plans/history/105")

    assert response.status_code == 200
    assert manual_session_id
    history = response.json()["workout_plan_instances"]
    assert len(history) == 1
    assert history[0]["workout_plan_instance"]["id"] == instance_id
    assert history[0]["planned_vs_actual_summary"]["actual_set_count"] == 1
