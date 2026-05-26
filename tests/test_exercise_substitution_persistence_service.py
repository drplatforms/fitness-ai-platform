from dataclasses import asdict

import database
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.exercise_catalog_service import (
    find_catalog_entry_by_name,
    seed_exercise_catalog,
)
from services.exercise_substitution_service import get_substitution_candidates
from services.workout_plan_persistence_service import (
    WorkoutPlanInvalidStatusError,
    WorkoutPlanNotFoundError,
    WorkoutPlanValidationError,
    complete_workout_plan,
    create_substitution_record,
    ensure_workout_plan_persistence_tables,
    get_active_substitution_for_planned_exercise,
    get_actual_sets,
    get_planned_workout_exercises,
    get_substitutions_for_plan,
    get_workout_execution_session,
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


def _table_names() -> set[str]:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    names = {row["name"] for row in cursor.fetchall()}
    conn.close()
    return names


def _select_plan_with_catalog_candidates(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(102)
    planned_exercise = selected["planned_exercises"][0]

    candidates = get_substitution_candidates(
        selected["workout_plan_instance"].id,
        planned_exercise.id,
    )
    if not candidates:
        planned_exercise = selected["planned_exercises"][1]
        candidates = get_substitution_candidates(
            selected["workout_plan_instance"].id,
            planned_exercise.id,
        )

    assert candidates
    return selected, planned_exercise, candidates[0]


def test_substitution_table_initializes(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    ensure_workout_plan_persistence_tables()

    assert "workout_plan_exercise_substitutions" in _table_names()


def test_create_substitution_record_links_plan_execution_and_planned_exercise(
    tmp_path,
    monkeypatch,
):
    selected, planned_exercise, candidate = _select_plan_with_catalog_candidates(
        tmp_path,
        monkeypatch,
    )
    instance_id = selected["workout_plan_instance"].id
    execution_session = get_workout_execution_session(instance_id)

    substitution = create_substitution_record(
        plan_instance_id=instance_id,
        planned_exercise_id=planned_exercise.id,
        replacement_catalog_exercise_id=candidate.catalog_exercise_id,
        substitution_reason="equipment_fit",
    )

    assert execution_session is not None
    assert substitution.workout_plan_instance_id == instance_id
    assert substitution.workout_execution_session_id == execution_session.id
    assert substitution.planned_workout_exercise_id == planned_exercise.id
    assert substitution.original_exercise_name == planned_exercise.name
    assert substitution.replacement_exercise_name == candidate.name
    assert substitution.replacement_catalog_exercise_id == candidate.catalog_exercise_id
    assert substitution.substitution_reason == "equipment_fit"
    assert substitution.status == "active"


def test_get_substitutions_for_plan_returns_records(tmp_path, monkeypatch):
    selected, planned_exercise, candidate = _select_plan_with_catalog_candidates(
        tmp_path,
        monkeypatch,
    )
    instance_id = selected["workout_plan_instance"].id

    created = create_substitution_record(
        plan_instance_id=instance_id,
        planned_exercise_id=planned_exercise.id,
        replacement_catalog_exercise_id=candidate.catalog_exercise_id,
    )

    substitutions = get_substitutions_for_plan(instance_id)

    assert [substitution.id for substitution in substitutions] == [created.id]


def test_get_active_substitution_for_planned_exercise(tmp_path, monkeypatch):
    selected, planned_exercise, candidate = _select_plan_with_catalog_candidates(
        tmp_path,
        monkeypatch,
    )
    instance_id = selected["workout_plan_instance"].id

    created = create_substitution_record(
        plan_instance_id=instance_id,
        planned_exercise_id=planned_exercise.id,
        replacement_catalog_exercise_id=candidate.catalog_exercise_id,
    )

    active = get_active_substitution_for_planned_exercise(
        instance_id,
        planned_exercise.id,
    )

    assert active is not None
    assert active.id == created.id
    assert active.status == "active"


def test_new_active_substitution_replaces_previous_active_record(
    tmp_path,
    monkeypatch,
):
    selected, planned_exercise, first_candidate = _select_plan_with_catalog_candidates(
        tmp_path,
        monkeypatch,
    )
    instance_id = selected["workout_plan_instance"].id
    candidates = get_substitution_candidates(instance_id, planned_exercise.id)
    assert len(candidates) >= 2

    first = create_substitution_record(
        plan_instance_id=instance_id,
        planned_exercise_id=planned_exercise.id,
        replacement_catalog_exercise_id=first_candidate.catalog_exercise_id,
    )
    second = create_substitution_record(
        plan_instance_id=instance_id,
        planned_exercise_id=planned_exercise.id,
        replacement_catalog_exercise_id=candidates[1].catalog_exercise_id,
    )

    substitutions = get_substitutions_for_plan(instance_id)
    active = get_active_substitution_for_planned_exercise(
        instance_id,
        planned_exercise.id,
    )

    assert [substitution.status for substitution in substitutions] == [
        "replaced",
        "active",
    ]
    assert active is not None
    assert active.id == second.id
    assert first.id != second.id


def test_create_substitution_record_rejects_missing_plan(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    replacement = find_catalog_entry_by_name("Dumbbell Row")
    assert replacement is not None
    assert replacement.id is not None

    try:
        create_substitution_record(
            plan_instance_id=999999,
            planned_exercise_id=1,
            replacement_catalog_exercise_id=replacement.id,
        )
    except WorkoutPlanNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing plan to be rejected.")


def test_create_substitution_record_rejects_planned_exercise_from_another_plan(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected_a = select_current_workout_plan(102)
    selected_b = select_current_workout_plan(105)
    replacement = find_catalog_entry_by_name("Dumbbell Row")
    assert replacement is not None
    assert replacement.id is not None

    wrong_planned_exercise = selected_b["planned_exercises"][0]

    try:
        create_substitution_record(
            plan_instance_id=selected_a["workout_plan_instance"].id,
            planned_exercise_id=wrong_planned_exercise.id,
            replacement_catalog_exercise_id=replacement.id,
        )
    except WorkoutPlanValidationError:
        pass
    else:
        raise AssertionError("Expected cross-plan planned exercise to be rejected.")


def test_create_substitution_record_rejects_unknown_catalog_exercise(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(102)
    planned_exercise = selected["planned_exercises"][0]

    try:
        create_substitution_record(
            plan_instance_id=selected["workout_plan_instance"].id,
            planned_exercise_id=planned_exercise.id,
            replacement_catalog_exercise_id=999999,
        )
    except WorkoutPlanValidationError:
        pass
    else:
        raise AssertionError("Expected unknown catalog exercise to be rejected.")


def test_create_substitution_record_rejects_completed_plan(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(102)
    instance_id = selected["workout_plan_instance"].id
    planned_exercise = selected["planned_exercises"][0]
    replacement = find_catalog_entry_by_name("Dumbbell Row")
    assert replacement is not None
    assert replacement.id is not None

    start_selected_workout_plan(instance_id)
    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "set_number": 1,
            "actual_reps": 8,
            "actual_weight": 20,
            "actual_rir": 2,
            "completed": True,
            "skipped": False,
        },
    )
    complete_workout_plan(instance_id)

    try:
        create_substitution_record(
            plan_instance_id=instance_id,
            planned_exercise_id=planned_exercise.id,
            replacement_catalog_exercise_id=replacement.id,
        )
    except WorkoutPlanInvalidStatusError:
        pass
    else:
        raise AssertionError("Expected completed plan substitution to be rejected.")


def test_substitution_record_preserves_plan_snapshot_and_planned_exercises(
    tmp_path,
    monkeypatch,
):
    selected, planned_exercise, candidate = _select_plan_with_catalog_candidates(
        tmp_path,
        monkeypatch,
    )
    instance_id = selected["workout_plan_instance"].id

    before_instance = get_workout_plan_instance(instance_id)
    before_planned_exercises = get_planned_workout_exercises(instance_id)
    assert before_instance is not None
    before_instance_dict = asdict(before_instance)
    before_planned_dicts = [asdict(exercise) for exercise in before_planned_exercises]

    create_substitution_record(
        plan_instance_id=instance_id,
        planned_exercise_id=planned_exercise.id,
        replacement_catalog_exercise_id=candidate.catalog_exercise_id,
    )

    after_instance = get_workout_plan_instance(instance_id)
    after_planned_exercises = get_planned_workout_exercises(instance_id)

    assert after_instance is not None
    assert asdict(after_instance) == before_instance_dict
    assert [asdict(exercise) for exercise in after_planned_exercises] == (
        before_planned_dicts
    )


def test_substitution_record_does_not_mutate_actual_set_rows(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(102)
    instance_id = selected["workout_plan_instance"].id
    planned_exercise = selected["planned_exercises"][0]
    replacement = find_catalog_entry_by_name("Dumbbell Row")
    assert replacement is not None
    assert replacement.id is not None

    start_selected_workout_plan(instance_id)
    log_actual_set(
        instance_id,
        {
            "planned_workout_exercise_id": planned_exercise.id,
            "set_number": 1,
            "actual_reps": 8,
            "actual_weight": 20,
            "actual_rir": 2,
            "completed": True,
            "skipped": False,
        },
    )
    before_actual_sets = [
        asdict(actual_set) for actual_set in get_actual_sets(instance_id)
    ]

    create_substitution_record(
        plan_instance_id=instance_id,
        planned_exercise_id=planned_exercise.id,
        replacement_catalog_exercise_id=replacement.id,
    )

    after_actual_sets = [
        asdict(actual_set) for actual_set in get_actual_sets(instance_id)
    ]

    assert after_actual_sets == before_actual_sets
