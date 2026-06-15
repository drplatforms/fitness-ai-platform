from __future__ import annotations

import database
from scripts.seed_qa_scenarios import seed_qa_scenarios
from scripts.seed_training_execution_qa import (
    QA_USER_IDS,
    SEED_MARKER,
    clear_seeded_training_execution_qa,
    seed_training_execution_qa,
)
from scripts.seed_user_profiles import seed_user_profiles
from scripts.spike_direct_ollama_training_report_section import (
    build_training_report_section_context,
    build_training_report_section_model_quote_context,
)
from services.training_execution_summary_service import build_training_execution_summary

FORBIDDEN_PRODUCT_CONTEXT_TERMS = ["QA", "Seeded", "Test", "Debug", "Bridge"]


def _seed_base_context(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    seed_user_profiles()


def _count_rows(sql: str, params: tuple = ()) -> int:
    conn = database.get_connection()
    cursor = conn.cursor()
    value = int(cursor.execute(sql, params).fetchone()[0])
    conn.close()
    return value


def test_seed_training_execution_qa_creates_completed_planned_execution_rows(
    tmp_path, monkeypatch
):
    _seed_base_context(tmp_path, monkeypatch)

    seeded = seed_training_execution_qa()

    assert [item.user_id for item in seeded] == list(QA_USER_IDS)
    assert all(item.actual_set_count > 0 for item in seeded)
    assert all("QA" not in item.title for item in seeded)
    assert all("Seeded" not in item.title for item in seeded)

    for user_id in QA_USER_IDS:
        assert (
            _count_rows(
                """
                SELECT COUNT(*)
                FROM workout_plan_instances
                WHERE user_id = ?
                  AND status = 'completed'
                """,
                (user_id,),
            )
            == 1
        )
        assert (
            _count_rows(
                """
                SELECT COUNT(*)
                FROM workout_execution_sessions
                WHERE user_id = ?
                  AND status = 'completed'
                """,
                (user_id,),
            )
            == 1
        )

    assert _count_rows("""
            SELECT COUNT(*)
            FROM workout_execution_set_actuals
            WHERE workout_execution_session_id IN (
                SELECT id
                FROM workout_execution_sessions
                WHERE user_id IN (101, 102, 103, 104, 105)
            )
            """) >= len(QA_USER_IDS)


def test_seed_training_execution_qa_is_idempotent(tmp_path, monkeypatch):
    _seed_base_context(tmp_path, monkeypatch)

    first = seed_training_execution_qa()
    second = seed_training_execution_qa()

    assert len(first) == len(second) == len(QA_USER_IDS)

    for user_id in QA_USER_IDS:
        assert (
            _count_rows(
                """
                SELECT COUNT(*)
                FROM workout_plan_instances
                WHERE user_id = ?
                  AND status = 'completed'
                """,
                (user_id,),
            )
            == 1
        )


def test_seed_training_execution_qa_unblocks_training_report_evidence_context(
    tmp_path, monkeypatch
):
    _seed_base_context(tmp_path, monkeypatch)
    seed_training_execution_qa()

    context = build_training_report_section_context(
        user_id=102,
        report_date="2026-06-14",
    )
    model_context = build_training_report_section_model_quote_context(context)
    quote_context = context["approved_training_quote_context"]

    assert model_context.required_quote_name
    assert model_context.required_anchor_count >= 2
    assert model_context.required_fact_anchors
    assert quote_context["approved_workout_names"]
    assert quote_context["approved_exercise_names"]

    combined_product_context = "\n".join(
        quote_context["approved_workout_names"]
        + quote_context["approved_exercise_names"]
        + model_context.required_fact_anchors
        + model_context.supporting_training_details
    )
    for forbidden_term in FORBIDDEN_PRODUCT_CONTEXT_TERMS:
        assert forbidden_term not in combined_product_context


def test_seed_training_execution_qa_clears_only_marked_seed_rows(tmp_path, monkeypatch):
    _seed_base_context(tmp_path, monkeypatch)
    seed_training_execution_qa()

    removed = clear_seeded_training_execution_qa(remove_invalid_bridge_rows=False)

    assert removed == len(QA_USER_IDS)
    assert (
        _count_rows(
            """
            SELECT COUNT(*)
            FROM workout_sessions
            WHERE notes LIKE ?
            """,
            (f"{SEED_MARKER}:%",),
        )
        == 0
    )
    assert (
        _count_rows("""
            SELECT COUNT(*)
            FROM workout_plan_instances
            WHERE user_id IN (101, 102, 103, 104, 105)
            """)
        == 0
    )


def test_seed_training_execution_qa_produces_training_execution_summary(
    tmp_path, monkeypatch
):
    _seed_base_context(tmp_path, monkeypatch)
    seed_training_execution_qa()

    summary = build_training_execution_summary(102)

    assert summary.completed_execution_count == 1
    assert summary.average_completion_percentage is not None
    assert summary.average_actual_rir is not None
    assert (
        summary.sets_below_planned_reps
        + summary.sets_inside_planned_reps
        + summary.sets_above_planned_reps
    ) > 0
    assert summary.confidence in {"Limited", "Low", "Moderate", "High"}
