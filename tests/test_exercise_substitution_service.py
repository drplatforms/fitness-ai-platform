from dataclasses import asdict

from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.exercise_catalog_service import (
    find_catalog_entry_by_name,
    seed_exercise_catalog,
)
from services.exercise_substitution_service import (
    apply_substitution,
    get_substitution_candidates,
)
from services.workout_plan_persistence_service import (
    WorkoutPlanInvalidStatusError,
    WorkoutPlanNotFoundError,
    WorkoutPlanValidationError,
    complete_workout_plan,
    get_active_substitution_for_planned_exercise,
    get_actual_sets,
    get_planned_workout_exercises,
    get_substitutions_for_plan,
    get_workout_plan_instance,
    log_actual_set,
    select_current_workout_plan,
    start_selected_workout_plan,
)

USER_HOME_GYM_EQUIPMENT = [
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


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    seed_exercise_catalog()


def _select_plan_for_user(
    user_id: int,
    training_environment: str,
    available_equipment: list[str],
    unavailable_equipment: list[str],
):
    save_equipment_profile(
        user_id=user_id,
        training_environment=training_environment,
        available_equipment=available_equipment,
        unavailable_equipment=unavailable_equipment,
    )
    return select_current_workout_plan(user_id)


def _planned_exercise_by_pattern(selected: dict, movement_pattern: str):
    for planned_exercise in selected["planned_exercises"]:
        entry = find_catalog_entry_by_name(planned_exercise.name)
        if entry is not None and entry.movement_pattern == movement_pattern:
            return planned_exercise

    raise AssertionError(f"No planned exercise found for {movement_pattern}.")


def _candidate_names(candidates):
    return {candidate.name for candidate in candidates}


def test_substitution_candidates_return_same_movement_pattern(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")

    candidates = get_substitution_candidates(
        selected["workout_plan_instance"].id,
        planned_exercise.id,
    )

    assert candidates
    assert all(
        "same_movement_pattern" in candidate.compatibility_reason_codes
        or "compatible_movement_family" in candidate.compatibility_reason_codes
        for candidate in candidates
    )
    assert any(
        candidate.movement_pattern == "horizontal_pull" for candidate in candidates
    )


def test_substitution_candidates_reject_missing_plan(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    try:
        get_substitution_candidates(999999, 1)
    except WorkoutPlanNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing plan to raise WorkoutPlanNotFoundError.")


def test_substitution_candidates_reject_planned_exercise_from_another_plan(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected_a = _select_plan_for_user(
        user_id=102,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    selected_b = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    wrong_planned_exercise = selected_b["planned_exercises"][0]

    try:
        get_substitution_candidates(
            selected_a["workout_plan_instance"].id,
            wrong_planned_exercise.id,
        )
    except WorkoutPlanValidationError:
        pass
    else:
        raise AssertionError(
            "Expected planned exercise from another plan to be rejected."
        )


def test_substitution_candidates_exclude_unavailable_equipment(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="limited_equipment",
        available_equipment=["bodyweight", "dumbbell"],
        unavailable_equipment=[
            "adjustable_bench",
            "barbell",
            "cable",
            "machine",
            "plates",
            "pull_up_bar",
            "rack",
            "resistance_band",
        ],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")

    candidates = get_substitution_candidates(
        selected["workout_plan_instance"].id,
        planned_exercise.id,
    )

    assert candidates
    for candidate in candidates:
        assert set(candidate.required_equipment).issubset({"bodyweight", "dumbbell"})
        assert "machine" not in candidate.required_equipment
        assert "adjustable_bench" not in candidate.required_equipment


def test_substitution_candidates_exclude_machine_when_machine_unavailable(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")

    candidates = get_substitution_candidates(
        selected["workout_plan_instance"].id,
        planned_exercise.id,
    )

    assert candidates
    assert all(
        "machine" not in candidate.required_equipment for candidate in candidates
    )
    assert "Machine Row" not in _candidate_names(candidates)


def test_substitution_candidates_exclude_bench_when_bench_unavailable(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="limited_equipment",
        available_equipment=["bodyweight", "dumbbell"],
        unavailable_equipment=[
            "adjustable_bench",
            "barbell",
            "cable",
            "machine",
            "plates",
            "pull_up_bar",
            "rack",
            "resistance_band",
        ],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")

    candidates = get_substitution_candidates(
        selected["workout_plan_instance"].id,
        planned_exercise.id,
    )

    assert "Chest-Supported Row" not in _candidate_names(candidates)
    assert "Chest-Supported Dumbbell Row" not in _candidate_names(candidates)
    assert all(
        "adjustable_bench" not in candidate.required_equipment
        for candidate in candidates
    )


def test_substitution_candidates_include_home_gym_compatible_options(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")

    candidates = get_substitution_candidates(
        selected["workout_plan_instance"].id,
        planned_exercise.id,
    )
    names = _candidate_names(candidates)

    assert names & {
        "Dumbbell Row",
        "Chest-Supported Row",
        "Chest-Supported Dumbbell Row",
        "Band Row",
        "Barbell Row",
    }


def test_bodyweight_only_substitution_candidates_are_bodyweight_compatible(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="bodyweight_only",
        available_equipment=["bodyweight"],
        unavailable_equipment=[
            "adjustable_bench",
            "barbell",
            "bike",
            "cable",
            "dumbbell",
            "ez_bar",
            "machine",
            "plates",
            "pull_up_bar",
            "rack",
            "resistance_band",
            "treadmill",
        ],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")

    candidates = get_substitution_candidates(
        selected["workout_plan_instance"].id,
        planned_exercise.id,
    )

    for candidate in candidates:
        assert set(candidate.required_equipment).issubset({"bodyweight"})


def test_substitution_candidates_do_not_mutate_approved_plan_or_planned_rows(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    plan_id = selected["workout_plan_instance"].id
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")

    before_instance = asdict(get_workout_plan_instance(plan_id))
    before_planned = [
        asdict(exercise) for exercise in get_planned_workout_exercises(plan_id)
    ]

    candidates = get_substitution_candidates(plan_id, planned_exercise.id)

    after_instance = asdict(get_workout_plan_instance(plan_id))
    after_planned = [
        asdict(exercise) for exercise in get_planned_workout_exercises(plan_id)
    ]

    assert candidates
    assert before_instance == after_instance
    assert before_planned == after_planned


def test_substitution_candidates_endpoint_returns_bounded_metadata(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")
    client = TestClient(app)

    response = client.get(
        "/workout-plans/"
        f"{selected['workout_plan_instance'].id}/planned-exercises/"
        f"{planned_exercise.id}/substitution-candidates"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["substitution_candidates"]

    candidate = payload["substitution_candidates"][0]
    assert set(candidate) == {
        "catalog_exercise_id",
        "name",
        "movement_pattern",
        "required_equipment",
        "primary_muscle_groups",
        "exercise_type",
        "difficulty",
        "compatibility_reason_codes",
    }
    assert "actual_sets" not in candidate
    assert "notes" not in candidate


def _planned_exercise_and_candidate(selected: dict, movement_pattern: str):
    planned_exercise = _planned_exercise_by_pattern(selected, movement_pattern)
    candidates = get_substitution_candidates(
        selected["workout_plan_instance"].id,
        planned_exercise.id,
    )
    assert candidates
    return planned_exercise, candidates[0]


def test_selected_plan_can_apply_compatible_substitution(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise, candidate = _planned_exercise_and_candidate(
        selected,
        "horizontal_pull",
    )
    plan_id = selected["workout_plan_instance"].id

    result = apply_substitution(
        plan_instance_id=plan_id,
        planned_exercise_id=planned_exercise.id,
        replacement_catalog_exercise_id=candidate.catalog_exercise_id,
        substitution_reason="user_selected",
    )

    assert result["active_substitution"].workout_plan_instance_id == plan_id
    assert result["active_substitution"].planned_workout_exercise_id == (
        planned_exercise.id
    )
    assert result["active_substitution"].replacement_catalog_exercise_id == (
        candidate.catalog_exercise_id
    )
    assert result["active_substitution"].status == "active"
    assert result["previous_active_substitution_replaced"] is False


def test_started_plan_can_apply_compatible_substitution(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    plan_id = selected["workout_plan_instance"].id
    start_selected_workout_plan(plan_id)
    planned_exercise, candidate = _planned_exercise_and_candidate(
        selected,
        "horizontal_pull",
    )

    result = apply_substitution(
        plan_id,
        planned_exercise.id,
        candidate.catalog_exercise_id,
    )

    assert result["workout_plan_instance"].status == "started"
    assert result["active_substitution"].status == "active"


def test_in_progress_plan_can_apply_compatible_substitution(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    plan_id = selected["workout_plan_instance"].id
    started = start_selected_workout_plan(plan_id)
    planned_exercise, candidate = _planned_exercise_and_candidate(
        started,
        "horizontal_pull",
    )
    log_actual_set(
        plan_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "set_number": 1,
            "actual_reps": 10,
            "actual_weight": 25,
            "actual_rir": 2,
            "completed": True,
            "skipped": False,
        },
    )

    result = apply_substitution(
        plan_id,
        planned_exercise.id,
        candidate.catalog_exercise_id,
    )

    assert result["workout_plan_instance"].status == "in_progress"
    assert result["active_substitution"].status == "active"


def test_completed_plan_cannot_apply_substitution(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    plan_id = selected["workout_plan_instance"].id
    started = start_selected_workout_plan(plan_id)
    planned_exercise, candidate = _planned_exercise_and_candidate(
        started,
        "horizontal_pull",
    )
    log_actual_set(
        plan_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "set_number": 1,
            "actual_reps": 10,
            "actual_weight": 25,
            "actual_rir": 2,
            "completed": True,
            "skipped": False,
        },
    )
    complete_workout_plan(plan_id)

    try:
        apply_substitution(
            plan_id,
            planned_exercise.id,
            candidate.catalog_exercise_id,
        )
    except WorkoutPlanInvalidStatusError:
        pass
    else:
        raise AssertionError("Expected completed plan substitution to be rejected.")


def test_apply_substitution_rejects_missing_plan(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    try:
        apply_substitution(999999, 1, 1)
    except WorkoutPlanNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing plan to be rejected.")


def test_apply_substitution_rejects_planned_exercise_from_another_plan(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected_a = _select_plan_for_user(
        user_id=102,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    selected_b = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise, candidate = _planned_exercise_and_candidate(
        selected_b,
        "horizontal_pull",
    )

    try:
        apply_substitution(
            selected_a["workout_plan_instance"].id,
            planned_exercise.id,
            candidate.catalog_exercise_id,
        )
    except WorkoutPlanValidationError:
        pass
    else:
        raise AssertionError("Expected planned exercise from another plan rejection.")


def test_apply_substitution_rejects_unknown_catalog_exercise(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")

    try:
        apply_substitution(
            selected["workout_plan_instance"].id,
            planned_exercise.id,
            999999,
        )
    except WorkoutPlanValidationError:
        pass
    else:
        raise AssertionError("Expected unknown catalog exercise to be rejected.")


def test_apply_substitution_rejects_replacement_not_in_candidates(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")
    incompatible = find_catalog_entry_by_name("Push-Up")
    assert incompatible is not None

    try:
        apply_substitution(
            selected["workout_plan_instance"].id,
            planned_exercise.id,
            incompatible.id,
        )
    except WorkoutPlanValidationError:
        pass
    else:
        raise AssertionError("Expected incompatible replacement to be rejected.")


def test_apply_substitution_rejects_unavailable_equipment_replacement(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="limited_equipment",
        available_equipment=["bodyweight", "dumbbell"],
        unavailable_equipment=[
            "adjustable_bench",
            "barbell",
            "cable",
            "machine",
            "plates",
            "pull_up_bar",
            "rack",
            "resistance_band",
        ],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")
    bench_replacement = find_catalog_entry_by_name("Chest-Supported Row")
    assert bench_replacement is not None

    try:
        apply_substitution(
            selected["workout_plan_instance"].id,
            planned_exercise.id,
            bench_replacement.id,
        )
    except WorkoutPlanValidationError:
        pass
    else:
        raise AssertionError("Expected unavailable equipment replacement rejection.")


def test_apply_substitution_rejects_machine_replacement_when_unavailable(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")
    machine_replacement = find_catalog_entry_by_name("Machine Row")
    assert machine_replacement is not None

    try:
        apply_substitution(
            selected["workout_plan_instance"].id,
            planned_exercise.id,
            machine_replacement.id,
        )
    except WorkoutPlanValidationError:
        pass
    else:
        raise AssertionError("Expected machine replacement to be rejected.")


def test_second_apply_replaces_prior_active_substitution(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")
    candidates = get_substitution_candidates(
        selected["workout_plan_instance"].id,
        planned_exercise.id,
    )
    assert len(candidates) >= 2
    plan_id = selected["workout_plan_instance"].id

    first = apply_substitution(
        plan_id,
        planned_exercise.id,
        candidates[0].catalog_exercise_id,
    )
    second = apply_substitution(
        plan_id,
        planned_exercise.id,
        candidates[1].catalog_exercise_id,
    )
    substitutions = get_substitutions_for_plan(plan_id)
    active = get_active_substitution_for_planned_exercise(
        plan_id,
        planned_exercise.id,
    )

    assert first["active_substitution"].status == "active"
    assert second["previous_active_substitution_replaced"] is True
    assert [substitution.status for substitution in substitutions] == [
        "replaced",
        "active",
    ]
    assert active is not None
    assert active.id == second["active_substitution"].id


def test_apply_substitution_does_not_mutate_plan_planned_exercises_or_actual_sets(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    plan_id = selected["workout_plan_instance"].id
    planned_exercise, candidate = _planned_exercise_and_candidate(
        selected,
        "horizontal_pull",
    )

    before_instance = asdict(get_workout_plan_instance(plan_id))
    before_planned = [
        asdict(exercise) for exercise in get_planned_workout_exercises(plan_id)
    ]
    before_actual_sets = [asdict(actual_set) for actual_set in get_actual_sets(plan_id)]

    result = apply_substitution(
        plan_id,
        planned_exercise.id,
        candidate.catalog_exercise_id,
    )

    after_instance = asdict(get_workout_plan_instance(plan_id))
    after_planned = [
        asdict(exercise) for exercise in get_planned_workout_exercises(plan_id)
    ]
    after_actual_sets = [asdict(actual_set) for actual_set in get_actual_sets(plan_id)]

    assert result["active_substitution"].status == "active"
    assert before_instance == after_instance
    assert before_planned == after_planned
    assert before_actual_sets == after_actual_sets


def test_apply_substitution_endpoint_returns_active_record(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise, candidate = _planned_exercise_and_candidate(
        selected,
        "horizontal_pull",
    )
    client = TestClient(app)

    response = client.post(
        "/workout-plans/"
        f"{selected['workout_plan_instance'].id}/planned-exercises/"
        f"{planned_exercise.id}/substitute",
        json={
            "replacement_catalog_exercise_id": candidate.catalog_exercise_id,
            "substitution_reason": "user_selected",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["workout_plan_instance_id"] == selected["workout_plan_instance"].id
    assert payload["planned_workout_exercise_id"] == planned_exercise.id
    assert payload["active_substitution"]["status"] == "active"
    assert payload["active_substitution"]["replacement_catalog_exercise_id"] == (
        candidate.catalog_exercise_id
    )
    assert payload["previous_active_substitution_replaced"] is False
    assert payload["selected_candidate"]["catalog_exercise_id"] == (
        candidate.catalog_exercise_id
    )


def test_apply_substitution_endpoint_rejects_invalid_replacement(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = _select_plan_for_user(
        user_id=105,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    planned_exercise = _planned_exercise_by_pattern(selected, "horizontal_pull")
    incompatible = find_catalog_entry_by_name("Push-Up")
    assert incompatible is not None
    client = TestClient(app)

    response = client.post(
        "/workout-plans/"
        f"{selected['workout_plan_instance'].id}/planned-exercises/"
        f"{planned_exercise.id}/substitute",
        json={
            "replacement_catalog_exercise_id": incompatible.id,
            "substitution_reason": "user_selected",
        },
    )

    assert response.status_code == 400
