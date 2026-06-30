from __future__ import annotations

import json
from datetime import date, timedelta

import database
from services.workout_set_intelligence_service import build_workout_set_intelligence


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (id, name, starting_weight)
        VALUES (?, ?, ?)
        """,
        (1, "Workout Set Test User", 190.0),
    )
    conn.commit()
    conn.close()


def _day(days_ago: int) -> str:
    return (date(2026, 6, 14) - timedelta(days=days_ago)).isoformat()


def _insert_completed_plan(
    *,
    user_id: int = 1,
    completed_at: str = "2026-06-14T10:00:00",
    title: str = "Strength Day",
    exercise_name: str = "Bench Press",
    sets: int = 3,
    reps_min: int = 8,
    reps_max: int = 10,
    rir_min: int = 2,
    rir_max: int = 3,
    actual_reps: list[int | None] | None = None,
    actual_rirs: list[int | None] | None = None,
    actual_weights: list[float | None] | None = None,
    completed_flags: list[int] | None = None,
    skipped_flags: list[int] | None = None,
    substitution_for_planned_exercise_id: int | None = None,
) -> int:
    actual_reps = actual_reps if actual_reps is not None else [8] * sets
    actual_rirs = actual_rirs if actual_rirs is not None else [2] * sets
    actual_weights = actual_weights if actual_weights is not None else [100.0] * sets
    completed_flags = (
        completed_flags if completed_flags is not None else [1] * len(actual_reps)
    )
    skipped_flags = (
        skipped_flags if skipped_flags is not None else [0] * len(actual_reps)
    )
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workout_plan_instances (
            user_id, status, scenario, confidence, title,
            approved_workout_plan_json, selected_at
        )
        VALUES (?, 'completed', 'unit_test', 'High', ?, ?, ?)
        """,
        (
            user_id,
            title,
            json.dumps({"title": title}),
            completed_at,
        ),
    )
    plan_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO planned_workout_exercises (
            workout_plan_instance_id, exercise_order, name, sets, reps_min,
            reps_max, rir_min, rir_max, notes, equipment_required_json
        )
        VALUES (?, 1, ?, ?, ?, ?, ?, ?, '', '[]')
        """,
        (plan_id, exercise_name, sets, reps_min, reps_max, rir_min, rir_max),
    )
    planned_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO workout_execution_sessions (
            workout_plan_instance_id, user_id, status, completed_at
        )
        VALUES (?, ?, 'completed', ?)
        """,
        (plan_id, user_id, completed_at),
    )
    session_id = int(cursor.lastrowid)
    for index, reps in enumerate(actual_reps, start=1):
        rir = actual_rirs[index - 1] if index - 1 < len(actual_rirs) else None
        weight = actual_weights[index - 1] if index - 1 < len(actual_weights) else None
        completed = (
            completed_flags[index - 1] if index - 1 < len(completed_flags) else 1
        )
        skipped = skipped_flags[index - 1] if index - 1 < len(skipped_flags) else 0
        cursor.execute(
            """
            INSERT INTO workout_execution_set_actuals (
                workout_execution_session_id, planned_workout_exercise_id,
                exercise_name, set_number, planned_reps_min, planned_reps_max,
                planned_rir_min, planned_rir_max, actual_reps, actual_weight,
                actual_rir, completed, skipped, substitution_for_planned_exercise_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                planned_id,
                exercise_name,
                index,
                reps_min,
                reps_max,
                rir_min,
                rir_max,
                reps,
                weight,
                rir,
                completed,
                skipped,
                substitution_for_planned_exercise_id,
            ),
        )
    conn.commit()
    conn.close()
    return plan_id


def test_no_completed_planned_executions_returns_limited_safely(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_workout_set_intelligence(user_id=1, target_date="2026-06-14")

    assert summary.completed_execution_count == 0
    assert summary.overall_completion_indicator == "no_planned_execution_data"
    assert summary.confidence == "Limited"
    assert "no_completed_planned_executions" in summary.reason_codes
    assert "overtraining" not in summary.coach_safe_summary.lower()


def test_uses_completed_planned_executions_only_and_respects_limit(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for days_ago in range(4):
        _insert_completed_plan(completed_at=f"{_day(days_ago)}T10:00:00")
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workout_plan_instances (
            user_id, status, scenario, confidence, title,
            approved_workout_plan_json, selected_at
        )
        VALUES (1, 'selected', 'unit_test', 'High', 'Not Completed', '{}', ?)
        """,
        ("2026-06-14T11:00:00",),
    )
    conn.commit()
    conn.close()

    summary = build_workout_set_intelligence(
        user_id=1, target_date="2026-06-14", recent_completed_limit=2
    )

    assert summary.completed_execution_count == 2
    assert len(summary.recent_plan_instance_ids) == 2
    assert summary.reason_codes


def test_does_not_use_unlinked_manual_workout_sets_as_planned_evidence(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO exercises (name) VALUES ('Manual Curl')")
    exercise_id = int(cursor.lastrowid)
    cursor.execute("""
        INSERT INTO workout_sessions (user_id, workout_date, workout_name)
        VALUES (1, '2026-06-14', 'Manual Session')
        """)
    session_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO workout_sets (workout_session_id, exercise_id, set_number, reps, weight, rir)
        VALUES (?, ?, 1, 12, 25, 2)
        """,
        (session_id, exercise_id),
    )
    conn.commit()
    conn.close()

    summary = build_workout_set_intelligence(user_id=1, target_date="2026-06-14")

    assert summary.completed_execution_count == 0
    assert "manual_workout_logs_not_used_for_planned_vs_actual" in summary.reason_codes


def test_session_and_exercise_indicators_are_bounded_and_calculated(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        completed_at="2026-06-14T10:00:00",
        actual_reps=[8, 9, 10],
        actual_rirs=[2, 2, 3],
        actual_weights=[100, 100, 100],
    )

    summary = build_workout_set_intelligence(user_id=1, target_date="2026-06-14")
    session = summary.session_summaries[0]
    exercise = summary.exercise_indicators[0]

    assert session.completion_percentage == 100.0
    assert session.average_planned_rir == 2.5
    assert session.average_actual_rir == 2.33
    assert session.effort_indicator == "as_planned"
    assert session.rep_range_indicator == "mostly_inside_range"
    assert session.logging_quality == "complete"
    assert exercise.exercise_name == "Bench Press"
    assert exercise.completion_indicator in {
        "limited_data",
        "mostly_completed",
        "partially_completed",
        "frequently_incomplete",
    }
    assert exercise.effort_indicator == "as_planned"
    assert exercise.rep_range_indicator == "mostly_inside_range"
    assert exercise.load_indicator == "insufficient_comparable_load_data"


def test_lower_actual_rir_means_harder_and_higher_means_easier(
    tmp_path, monkeypatch
) -> None:
    first_db = tmp_path / "harder"
    first_db.mkdir()
    _seed_test_db(first_db, monkeypatch)
    _insert_completed_plan(completed_at="2026-06-14T10:00:00", actual_rirs=[0, 1, 1])
    harder = build_workout_set_intelligence(user_id=1, target_date="2026-06-14")
    assert harder.overall_effort_indicator == "harder_than_planned"

    second_db = tmp_path / "easier"
    second_db.mkdir()
    _seed_test_db(second_db, monkeypatch)
    _insert_completed_plan(completed_at="2026-06-14T10:00:00", actual_rirs=[4, 4, 5])
    easier = build_workout_set_intelligence(user_id=1, target_date="2026-06-14")
    assert easier.overall_effort_indicator == "easier_than_planned"


def test_missing_actuals_lower_confidence_and_add_reasons(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        actual_reps=[8, None, 9],
        actual_rirs=[2, None, 3],
        actual_weights=[100.0, None, 100.0],
    )

    summary = build_workout_set_intelligence(user_id=1, target_date="2026-06-14")

    assert summary.confidence in {"Limited", "Low"}
    assert "missing_actual_reps_lowers_confidence" in summary.reason_codes
    assert "missing_actual_rir_lowers_confidence" in summary.reason_codes
    assert "missing_actual_weight_limits_load_indicator" in summary.reason_codes


def test_skips_substitutions_and_below_range_are_reported_safely(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        actual_reps=[6, 7, 8],
        actual_rirs=[2, 2, 2],
        completed_flags=[1, 1, 0],
        skipped_flags=[0, 0, 1],
        substitution_for_planned_exercise_id=99,
    )

    summary = build_workout_set_intelligence(user_id=1, target_date="2026-06-14")

    assert summary.overall_rep_range_indicator in {"often_below_range", "mixed"}
    assert summary.confidence in {"Limited", "Low"}
    assert "skipped_sets_lowers_confidence" in summary.reason_codes
    assert "substitution_lowers_confidence" in summary.reason_codes
    assert "indicator" in " ".join(summary.source_facts).lower()
    forbidden = ["failed", "poor adherence", "must deload", "add weight automatically"]
    serialized = json.dumps(summary.to_dict()).lower()
    assert not any(term in serialized for term in forbidden)


def test_load_indicator_compares_same_exercise_weights_conservatively(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        completed_at="2026-06-10T10:00:00", actual_weights=[100, 100, 100]
    )
    _insert_completed_plan(
        completed_at="2026-06-14T10:00:00", actual_weights=[105, 105, 105]
    )

    summary = build_workout_set_intelligence(user_id=1, target_date="2026-06-14")
    exercise = summary.exercise_indicators[0]

    assert exercise.latest_actual_weight == 105.0
    assert exercise.prior_actual_weight == 100.0
    assert exercise.weight_delta == 5.0
    assert exercise.load_indicator == "increasing"
