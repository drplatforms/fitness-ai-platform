from __future__ import annotations

import json
import sqlite3
import sys
import types

import pytest

import database
from services import coordinator_service, report_service
from services.coaching_decision_service import build_coaching_decision
from services.training_report_section_provider_service import (
    FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED,
    TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    TRAINING_REPORT_SECTION_PROVIDER_ENV,
    build_configured_training_report_section_with_metadata,
    build_deterministic_training_report_section_with_metadata,
)

APPROVED_CONTEXT = {
    "section": "training",
    "approved_training_quote_context": {
        "approved_workout_names": ["Upper Body Strength"],
        "approved_exercise_names": ["Dumbbell Bench Press"],
        "approved_training_numbers": [1, 2, 3, 8, 10, 50],
        "approved_set_rep_load_rir_values": [
            {
                "workout_name": "Upper Body Strength",
                "exercise_name": "Dumbbell Bench Press",
                "planned_sets": 3,
                "planned_reps": "8-10",
                "planned_rir": "2-3",
                "actual_sets": 1,
                "actual_reps": [10],
                "actual_load_lb": 50,
                "actual_rir": [1],
            }
        ],
        "approved_training_summary_facts": [
            "Upper Body Strength was completed.",
            "Dumbbell Bench Press was planned in Upper Body Strength for 3 sets, 8-10 reps, RIR 2-3.",
            "Dumbbell Bench Press was logged in Upper Body Strength for 1 set.",
            "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
            "The final Dumbbell Bench Press set was logged at 1 RIR.",
        ],
    },
}


@pytest.fixture()
def temp_database(tmp_path, monkeypatch):
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()

    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO users (id, name) VALUES (?, ?)", (102, "QA User"))
    conn.commit()
    conn.close()

    return db_path


def _valid_raw_section() -> str:
    return """
{
  "section_summary": "Dumbbell Bench Press is the lift worth paying attention to from Upper Body Strength.",
  "key_observations": [
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ],
  "performance_interpretation": "Dumbbell Bench Press is the reference point for the next Upper Body Strength choice.",
  "fatigue_recovery_interpretation": "Upper Body Strength can guide the next session without proving a recovery or fatigue pattern.",
  "suggested_focus": "Keep Dumbbell Bench Press as the reference point and continue logging load, reps, and RIR.",
  "limitations_context": "Upper Body Strength is one workout, not a full trend or recovery picture.",
  "confidence": "Moderate",
  "reason_codes": ["direct_ollama_training_report_section_candidate"]
}
""".strip()


def _latest_report_payload(user_id=102) -> dict:
    row = report_service.get_latest_health_report(user_id)
    assert row is not None
    payload = dict(row)
    payload["report_metadata"] = json.loads(payload["report_metadata_json"])
    return payload


def test_invalid_coordinator_output_uses_deterministic_composition_boundary(
    temp_database,
):
    health_state = coordinator_service.build_user_health_state(102)
    coaching_decision = build_coaching_decision(health_state)

    composition = coordinator_service.compose_full_report_from_coordinator_output(
        raw_text="raw_output prompt schema validation_errors should not render",
        health_state=health_state,
        coaching_decision=coaching_decision,
    )

    rendered = coordinator_service.render_unified_health_report(
        report=composition.report,
        health_state=health_state,
        coaching_decision=coaching_decision,
    )

    assert composition.coordinator_fallback_used is True
    assert composition.coordinator_fallback_reason == "invalid_coordinator_output"
    assert composition.full_report_composer_source == (
        "deterministic_fallback_after_invalid_coordinator_output"
    )
    assert "raw_output" not in rendered
    assert "validation_errors" not in rendered
    assert "prompt" not in rendered


def test_composition_metadata_is_allowlisted_and_safe(temp_database):
    section_result = build_deterministic_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
    )
    metadata = coordinator_service.build_health_report_persistence_metadata(
        section_result,
        report_job_id="job-composition",
        report_status="completed_with_full_report_fallback",
        report_generation_mode="async_report_job",
        full_report_composer_source="deterministic_fallback_after_crewai_error",
        coordinator_attempted=True,
        coordinator_fallback_used=True,
        coordinator_fallback_reason="crewai_coordinator_error",
        async_job_used=True,
        provider_enabled=False,
    )
    metadata["raw_crewai_error"] = "do not persist this raw exception"
    metadata["validation_errors"] = ["debug-only"]

    report_service.save_health_report(
        user_id=102,
        report_text="Safe deterministic fallback full report.",
        model_summary="deterministic_fallback_after_crewai_error",
        report_date="2026-06-14",
        report_metadata=metadata,
    )

    report = _latest_report_payload()
    persisted_metadata = report["report_metadata"]

    assert persisted_metadata["full_report_composer_source"] == (
        "deterministic_fallback_after_crewai_error"
    )
    assert persisted_metadata["coordinator_attempted"] is True
    assert persisted_metadata["coordinator_fallback_used"] is True
    assert persisted_metadata["coordinator_fallback_reason"] == (
        "crewai_coordinator_error"
    )
    assert "raw_crewai_error" not in report["report_metadata_json"]
    assert '"validation_errors"' not in report["report_metadata_json"]


def test_crewai_failure_retains_provider_training_section_and_composition_metadata(
    temp_database,
    monkeypatch,
):
    monkeypatch.setenv(
        coordinator_service.AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV,
        "true",
    )
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    class FakeLLM:
        def __init__(self, *_args, **_kwargs):
            pass

    class FakeAgent:
        def __init__(self, *_args, **_kwargs):
            pass

    class FakeTask:
        def __init__(self, *_args, **_kwargs):
            pass

    class FakeCrew:
        def __init__(self, *_args, **_kwargs):
            pass

        def kickoff(self):
            raise RuntimeError("raw coordinator exception should not persist")

    fake_crewai = types.SimpleNamespace(
        LLM=FakeLLM,
        Agent=FakeAgent,
        Task=FakeTask,
        Crew=FakeCrew,
    )
    monkeypatch.setitem(sys.modules, "crewai", fake_crewai)

    approved_training_section_result = (
        build_configured_training_report_section_with_metadata(
            user_id=102,
            report_date="2026-06-14",
            approved_context=APPROVED_CONTEXT,
            direct_ollama_generate=lambda *_args, **_kwargs: _valid_raw_section(),
        )
    )

    monkeypatch.setattr(
        coordinator_service,
        "build_full_report_training_section_result",
        lambda **_kwargs: approved_training_section_result,
    )

    result = coordinator_service.generate_health_report(
        102,
        report_date="2026-06-14",
        allow_training_section_provider=True,
        return_training_section_result=True,
        report_job_id="job-composition-fail",
    )

    report = _latest_report_payload()
    persisted_metadata = report["report_metadata"]

    assert result.training_report_section_result.approved_section.source == (
        FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED
    )
    assert "Dumbbell Bench Press" in report["report_text"]
    assert "raw coordinator exception" not in report["report_text"]
    assert "raw_output" not in report["report_text"]
    assert report["model_summary"] == "deterministic_fallback_after_crewai_error"
    assert persisted_metadata["training_section_source"] == "direct_ollama_approved"
    assert persisted_metadata["provider_attempted"] is True
    assert persisted_metadata["fallback_used"] is False
    assert persisted_metadata["full_report_composer_source"] == (
        "deterministic_fallback_after_crewai_error"
    )
    assert persisted_metadata["coordinator_attempted"] is True
    assert persisted_metadata["coordinator_fallback_used"] is True
    assert persisted_metadata["coordinator_fallback_reason"] == (
        "crewai_coordinator_error"
    )
    assert "raw coordinator exception" not in report["report_metadata_json"]
