from __future__ import annotations

from datetime import date

import database
from scripts.seed_longitudinal_qa_data import (
    DEFAULT_DAY_COUNT,
    FORBIDDEN_PRODUCT_CONTEXT_TERMS,
    QA_USER_IDS,
    seed_longitudinal_qa_data,
)
from scripts.spike_direct_ollama_training_report_section import (
    build_training_report_section_context,
    build_training_report_section_model_quote_context,
)
from services.training_execution_summary_service import build_training_execution_summary
from services.user_state_service import build_user_health_state

FIXED_END_DATE = date(2026, 6, 14)


def _count_rows(sql: str, params: tuple = ()) -> int:
    conn = database.get_connection()
    cursor = conn.cursor()
    value = int(cursor.execute(sql, params).fetchone()[0])
    conn.close()
    return value


def _all_rows(sql: str, params: tuple = ()):
    conn = database.get_connection()
    cursor = conn.cursor()
    rows = [dict(row) for row in cursor.execute(sql, params).fetchall()]
    conn.close()
    return rows


def _seed(tmp_path, monkeypatch, *, end_date: date = FIXED_END_DATE):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    return seed_longitudinal_qa_data(end_date=end_date)


def test_seed_longitudinal_qa_data_runs_and_is_idempotent(tmp_path, monkeypatch):
    first = _seed(tmp_path, monkeypatch)
    counts_after_first = {
        "users": _count_rows(
            "SELECT COUNT(*) FROM users WHERE id IN (101,102,103,104,105)"
        ),
        "checkins": _count_rows(
            "SELECT COUNT(*) FROM daily_checkins WHERE user_id IN (101,102,103,104,105)"
        ),
        "nutrition": _count_rows(
            "SELECT COUNT(*) FROM food_entries WHERE user_id IN (101,102,103,104,105)"
        ),
        "plans": _count_rows(
            "SELECT COUNT(*) FROM workout_plan_instances WHERE user_id IN (101,102,103,104,105)"
        ),
        "actuals": _count_rows(
            """
            SELECT COUNT(*)
            FROM workout_execution_set_actuals
            WHERE workout_execution_session_id IN (
                SELECT id FROM workout_execution_sessions WHERE user_id IN (101,102,103,104,105)
            )
            """
        ),
    }

    second = seed_longitudinal_qa_data(end_date=FIXED_END_DATE)
    counts_after_second = {
        "users": _count_rows(
            "SELECT COUNT(*) FROM users WHERE id IN (101,102,103,104,105)"
        ),
        "checkins": _count_rows(
            "SELECT COUNT(*) FROM daily_checkins WHERE user_id IN (101,102,103,104,105)"
        ),
        "nutrition": _count_rows(
            "SELECT COUNT(*) FROM food_entries WHERE user_id IN (101,102,103,104,105)"
        ),
        "plans": _count_rows(
            "SELECT COUNT(*) FROM workout_plan_instances WHERE user_id IN (101,102,103,104,105)"
        ),
        "actuals": _count_rows(
            """
            SELECT COUNT(*)
            FROM workout_execution_set_actuals
            WHERE workout_execution_session_id IN (
                SELECT id FROM workout_execution_sessions WHERE user_id IN (101,102,103,104,105)
            )
            """
        ),
    }

    assert [item.user_id for item in first] == list(QA_USER_IDS)
    assert [item.user_id for item in second] == list(QA_USER_IDS)
    assert counts_after_first == counts_after_second
    assert counts_after_second["users"] == 5
    assert counts_after_second["checkins"] >= 600
    assert counts_after_second["nutrition"] >= 500
    assert counts_after_second["plans"] >= 250
    assert counts_after_second["actuals"] >= 2500


def test_seed_preserves_real_user_and_global_catalogs(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)

    assert _count_rows("SELECT COUNT(*) FROM users WHERE id = 1") == 1
    assert _count_rows("SELECT COUNT(*) FROM canonical_foods") > 0
    assert _count_rows("SELECT COUNT(*) FROM exercise_catalog_exercises") > 0


def test_seed_creates_six_month_recovery_and_nutrition_ranges(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)

    for user_id in QA_USER_IDS:
        rows = _all_rows(
            """
            SELECT MIN(checkin_date) AS min_date, MAX(checkin_date) AS max_date, COUNT(*) AS count
            FROM daily_checkins
            WHERE user_id = ?
            """,
            (user_id,),
        )[0]
        assert rows["min_date"] <= "2025-12-20"
        assert rows["max_date"] == "2026-06-14"
        if user_id == 105:
            assert 100 <= rows["count"] < DEFAULT_DAY_COUNT
        else:
            assert rows["count"] >= 150

    nutrition_counts = {
        row["user_id"]: row["nutrition_days"]
        for row in _all_rows(
            """
            SELECT user_id, COUNT(DISTINCT entry_date) AS nutrition_days
            FROM food_entries
            WHERE user_id IN (101,102,103,104,105)
            GROUP BY user_id
            """
        )
    }
    assert nutrition_counts[102] >= 150
    assert nutrition_counts[105] < nutrition_counts[102]


def test_seed_creates_clean_planned_execution_graph(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)

    for user_id in QA_USER_IDS:
        assert (
            _count_rows(
                "SELECT COUNT(*) FROM workout_plan_instances WHERE user_id = ? AND status = 'completed'",
                (user_id,),
            )
            >= 40
        )
        assert (
            _count_rows(
                "SELECT COUNT(*) FROM planned_workout_exercises WHERE workout_plan_instance_id IN (SELECT id FROM workout_plan_instances WHERE user_id = ?)",
                (user_id,),
            )
            > 0
        )
        assert (
            _count_rows(
                "SELECT COUNT(*) FROM workout_execution_sessions WHERE user_id = ? AND status = 'completed'",
                (user_id,),
            )
            >= 40
        )

    provider_facing_rows = _all_rows(
        """
        SELECT title AS value FROM workout_plan_instances WHERE user_id IN (101,102,103,104,105)
        UNION ALL
        SELECT workout_name AS value FROM workout_sessions WHERE user_id IN (101,102,103,104,105)
        UNION ALL
        SELECT name AS value FROM planned_workout_exercises WHERE workout_plan_instance_id IN (
            SELECT id FROM workout_plan_instances WHERE user_id IN (101,102,103,104,105)
        )
        """
    )
    combined = "\n".join(row["value"] for row in provider_facing_rows)
    for forbidden_term in FORBIDDEN_PRODUCT_CONTEXT_TERMS:
        assert forbidden_term not in combined


def test_seed_supports_health_state_scenario_patterns(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, end_date=date.today())

    recovery_limited = build_user_health_state(101)
    assert recovery_limited.recovery_state.fatigue_risk in {"High", "Moderate"}
    assert recovery_limited.training_state.training_load in {"High", "Moderate"}

    aligned = build_user_health_state(102)
    assert aligned.recovery_state.readiness_level == "High"
    assert aligned.nutrition_state.calorie_status != "Unknown"

    mismatch = build_user_health_state(103)
    assert mismatch.training_state.training_load in {"High", "Moderate"}

    improving = build_user_health_state(104)
    assert improving.recovery_state.readiness_level in {"High", "Moderate"}

    limited = build_user_health_state(105)
    assert limited.nutrition_state.calorie_status in {
        "Unknown",
        "Logged - Lower Intake",
    }


def test_seed_supports_training_execution_summary_and_evidence_contexts(
    tmp_path, monkeypatch
):
    _seed(tmp_path, monkeypatch)

    for user_id in (101, 102, 103, 104):
        summary = build_training_execution_summary(user_id)
        assert summary.completed_execution_count > 0
        assert summary.average_completion_percentage is not None
        assert summary.average_actual_rir is not None

        context = build_training_report_section_context(
            user_id=user_id,
            report_date="2026-06-14",
        )
        model_context = build_training_report_section_model_quote_context(context)
        assert model_context.required_quote_name
        assert model_context.required_anchor_count >= 2
        assert model_context.required_fact_anchors
        assert context["approved_training_quote_context"]["approved_workout_names"]
        assert context["approved_training_quote_context"]["approved_exercise_names"]

    limited_summary = build_training_execution_summary(105)
    assert limited_summary.completed_execution_count > 0
    assert limited_summary.confidence in {"Limited", "Low", "Moderate"}
    assert (
        limited_summary.incomplete_logging_count > 0
        or limited_summary.missing_actual_rir_count > 0
        or limited_summary.skipped_exercise_count > 0
    )
