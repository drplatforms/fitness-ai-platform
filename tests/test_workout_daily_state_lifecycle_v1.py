from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.exercise_substitution_service import (
    apply_substitution,
    get_substitution_candidates,
)
from services.workout_daily_state_service import (
    STALE_WORKOUT_RESET_MESSAGE,
    clear_stale_workout_session_state_if_needed,
    resolve_workout_daily_state,
)
from services.workout_plan_persistence_service import (
    get_workout_plan_history,
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


def _set_plan_dates(plan_id: int, target: date) -> None:
    timestamp = f"{target.isoformat()} 09:00:00"
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE workout_plan_instances
        SET selected_at = ?, created_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (timestamp, timestamp, timestamp, plan_id),
    )
    cursor.execute(
        """
        UPDATE workout_execution_sessions
        SET created_at = ?, updated_at = ?
        WHERE workout_plan_instance_id = ?
        """,
        (timestamp, timestamp, plan_id),
    )
    conn.commit()
    conn.close()


def _set_active_plan_dates(plan_id: int, target: date) -> None:
    _set_plan_dates(plan_id, target)
    timestamp = f"{target.isoformat()} 10:00:00"
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE workout_execution_sessions
        SET started_at = ?, updated_at = ?
        WHERE workout_plan_instance_id = ?
        """,
        (timestamp, timestamp, plan_id),
    )
    cursor.execute(
        """
        UPDATE workout_sessions
        SET workout_date = ?
        WHERE id = (
            SELECT workout_session_id
            FROM workout_execution_sessions
            WHERE workout_plan_instance_id = ?
        )
        """,
        (target.isoformat(), plan_id),
    )
    conn.commit()
    conn.close()


def _mark_plan_completed_on(plan_id: int, target: date) -> None:
    timestamp = f"{target.isoformat()} 11:00:00"
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE workout_plan_instances
        SET status = ?, completed_at = ?, updated_at = ?
        WHERE id = ?
        """,
        ("completed", timestamp, timestamp, plan_id),
    )
    cursor.execute(
        """
        UPDATE workout_execution_sessions
        SET status = ?, completed_at = ?, updated_at = ?
        WHERE workout_plan_instance_id = ?
        """,
        ("completed", timestamp, timestamp, plan_id),
    )
    conn.commit()
    conn.close()


def _first_planned_exercise_with_candidates(selected: dict):
    plan_id = selected["workout_plan_instance"].id
    for planned_exercise in selected["planned_exercises"]:
        candidates = get_substitution_candidates(plan_id, planned_exercise.id)
        if candidates:
            return planned_exercise, candidates[0]
    raise AssertionError("Expected at least one substitution candidate.")


def test_no_workout_today_resolves_to_clean_state(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    state = resolve_workout_daily_state(102, target_date=date(2026, 6, 20))

    assert state.state == "no_workout_today"
    assert state.stale_state_detected is False
    assert state.selected_plan_id is None
    assert state.active_plan_id is None


def test_today_selected_and_active_workouts_are_preserved(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)
    today = date(2026, 6, 20)

    selected = select_current_workout_plan(102, workout_size_preference="standard")
    selected_plan_id = selected["workout_plan_instance"].id
    _set_plan_dates(selected_plan_id, today)

    selected_state = resolve_workout_daily_state(102, target_date=today)
    assert selected_state.state == "selected_today"
    assert selected_state.selected_plan_id == selected_plan_id
    assert selected_state.stale_state_detected is False

    start_selected_workout_plan(selected_plan_id)
    _set_active_plan_dates(selected_plan_id, today)

    active_state = resolve_workout_daily_state(102, target_date=today)
    assert active_state.state == "active_today"
    assert active_state.active_plan_id == selected_plan_id
    assert active_state.stale_state_detected is False


def test_prior_date_selected_workout_expires_without_deleting_history(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)
    today = date(2026, 6, 20)
    yesterday = today - timedelta(days=1)

    selected = select_current_workout_plan(102, workout_size_preference="standard")
    plan_id = selected["workout_plan_instance"].id
    _set_plan_dates(plan_id, yesterday)

    state = resolve_workout_daily_state(102, target_date=today)

    assert state.state == "expired_uncompleted_prior"
    assert state.expired_plan_id == plan_id
    assert state.expired_plan_date == yesterday.isoformat()
    assert state.stale_state_detected is True
    assert state.user_safe_message == STALE_WORKOUT_RESET_MESSAGE

    history_ids = [
        item["workout_plan_instance"].id for item in get_workout_plan_history(102)
    ]
    assert plan_id in history_ids


def test_prior_date_active_workout_expires_but_completed_prior_is_preserved(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)
    today = date(2026, 6, 20)
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    completed = select_current_workout_plan(102, workout_size_preference="quick")
    completed_id = completed["workout_plan_instance"].id
    _set_plan_dates(completed_id, two_days_ago)
    _mark_plan_completed_on(completed_id, two_days_ago)

    selected = select_current_workout_plan(102, workout_size_preference="standard")
    active_id = selected["workout_plan_instance"].id
    start_selected_workout_plan(active_id)
    _set_active_plan_dates(active_id, yesterday)

    state = resolve_workout_daily_state(102, target_date=today)

    assert state.state == "expired_uncompleted_prior"
    assert state.expired_plan_id == active_id

    history = get_workout_plan_history(102)
    completed_history = [
        item for item in history if item["workout_plan_instance"].id == completed_id
    ]
    assert completed_history
    assert completed_history[0]["workout_plan_instance"].status == "completed"


def test_today_completed_workout_resolves_completed_today(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)
    today = date(2026, 6, 20)

    selected = select_current_workout_plan(102, workout_size_preference="quick")
    plan_id = selected["workout_plan_instance"].id
    _set_plan_dates(plan_id, today)
    _mark_plan_completed_on(plan_id, today)

    state = resolve_workout_daily_state(102, target_date=today)

    assert state.state == "completed_today"
    assert state.completed_workout_id == plan_id
    assert state.stale_state_detected is False


def test_stale_substitution_state_is_marked_for_clear_but_today_state_is_preserved(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)
    today = date(2026, 6, 20)
    yesterday = today - timedelta(days=1)

    selected = select_current_workout_plan(102, workout_size_preference="standard")
    plan_id = selected["workout_plan_instance"].id
    planned_exercise, candidate = _first_planned_exercise_with_candidates(selected)
    apply_substitution(
        plan_instance_id=plan_id,
        planned_exercise_id=planned_exercise.id,
        replacement_catalog_exercise_id=candidate.catalog_exercise_id,
        substitution_reason="user_selected",
    )
    _set_plan_dates(plan_id, yesterday)

    state = resolve_workout_daily_state(102, target_date=today)
    assert state.state == "expired_uncompleted_prior"
    assert state.substitution_state_should_clear is True

    session_state = {
        "selected_workout_plan_response": {"workout_plan_instance": {"id": plan_id}},
        "started_workout_plan_response": None,
        "completed_workout_plan_response": None,
        "visible_substitution_candidates": [{"name": "stale"}],
        "applied_substitution_responses": {"stale": {"name": "stale"}},
        "substitution_apply_message": "stale",
        "substitution_apply_error": "stale",
        "substitution_apply_error_detail": "stale",
        "substitution_flow_ready_to_do_workout": True,
        "actual_set_logging_message": "stale",
        "actual_set_editing_message": "stale",
        "actual_set_editing_error": "stale",
        "actual_set_edit_response": {"stale": True},
    }

    assert clear_stale_workout_session_state_if_needed(session_state, state) is True
    assert session_state["selected_workout_plan_response"] is None
    assert session_state["visible_substitution_candidates"] == []
    assert session_state["applied_substitution_responses"] == {}
    assert session_state["substitution_flow_ready_to_do_workout"] is False

    today_selected = select_current_workout_plan(
        102, workout_size_preference="standard"
    )
    today_plan_id = today_selected["workout_plan_instance"].id
    _set_plan_dates(today_plan_id, today)
    today_state = resolve_workout_daily_state(102, target_date=today)
    assert today_state.state == "selected_today"
    assert today_state.selected_plan_id == today_plan_id
    assert today_state.substitution_state_should_clear is False


def test_current_workout_route_returns_only_today_relevant_state(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)
    client = TestClient(app)
    today = date(2026, 6, 20)
    yesterday = today - timedelta(days=1)

    selected = select_current_workout_plan(102, workout_size_preference="standard")
    stale_id = selected["workout_plan_instance"].id
    _set_plan_dates(stale_id, yesterday)

    stale_response = client.get(f"/workout-plans/current/102?target_date={today}")
    assert stale_response.status_code == 200
    stale_payload = stale_response.json()
    assert stale_payload["workout_daily_state"]["state"] == "expired_uncompleted_prior"
    assert stale_payload["workout_daily_state"]["expired_plan_id"] == stale_id
    assert stale_payload["current_execution_state"] is None

    today_selected = select_current_workout_plan(
        102, workout_size_preference="standard"
    )
    today_id = today_selected["workout_plan_instance"].id
    _set_plan_dates(today_id, today)

    today_response = client.get(f"/workout-plans/current/102?target_date={today}")
    assert today_response.status_code == 200
    today_payload = today_response.json()
    assert today_payload["workout_daily_state"]["state"] == "selected_today"
    assert (
        today_payload["current_execution_state"]["workout_plan_instance"]["id"]
        == today_id
    )


def test_normal_workout_ui_uses_user_safe_lifecycle_copy() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")

    assert "workout_daily_state_message" in source
    assert "unfinished workout from a previous day" in source
    assert "/workout-plans/current/{user_id}" in source

    normal_ui_forbidden_terms = [
        "stale cache",
        "invalid state",
        "expired object",
        "session_state cleared",
        "substitution state purged",
        "No matching workout_plan_id",
    ]
    for term in normal_ui_forbidden_terms:
        assert term not in source
