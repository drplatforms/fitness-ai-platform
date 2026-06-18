from __future__ import annotations

import json
import sqlite3
import sys
import types

import pytest

import database
from services import coordinator_service, report_service
from services.coordinator_service import build_health_report_persistence_metadata
from services.training_report_section_provider_service import (
    FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
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

PUBLIC_REPORT_TEXT = """**Unified Health Report**

**Training Report Section:**
**Summary:** Dumbbell Bench Press is the approved reference point.
**Key Observations:**
- Dumbbell Bench Press was logged at 50 lb for 10 reps.
**Performance Interpretation:** Use the approved training details only.
**Fatigue / Recovery Interpretation:** One session does not prove a trend.
**Next Training Focus:** Keep logging load, reps, and RIR.
**Limitations:** This is one workout, not a full trend.
"""


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


def _latest_report_payload(user_id=102) -> dict:
    row = report_service.get_latest_health_report(user_id)
    assert row is not None
    payload = dict(row)
    payload["report_metadata"] = json.loads(payload["report_metadata_json"])
    return payload


def test_deterministic_report_persistence_stores_safe_public_content(temp_database):
    section_result = build_deterministic_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
    )
    metadata = build_health_report_persistence_metadata(
        section_result,
        report_job_id="job-det",
        report_status="completed",
        report_generation_mode="async_report_job",
        async_job_used=True,
        provider_enabled=False,
    )

    report_service.save_health_report(
        user_id=102,
        report_text=PUBLIC_REPORT_TEXT,
        model_summary="ollama/qwen3:8b",
        report_date="2026-06-14",
        report_metadata=metadata,
    )

    report = _latest_report_payload()

    assert report["report_text"] == PUBLIC_REPORT_TEXT
    assert report["report_date"] == "2026-06-14"
    assert report["report_metadata"]["provider_attempted"] is False
    assert report["report_metadata"]["selected_provider"] == "deterministic"
    assert report["report_metadata"]["training_section_source"] == "deterministic"
    assert report["report_metadata"]["async_job_used"] is True
    assert "raw_output" not in report["report_text"]
    assert "model_facing_quote_context" not in report["report_text"]


def test_provider_approved_report_persistence_stores_safe_metadata_only(
    temp_database,
    monkeypatch,
):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    section_result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=lambda *_args, **_kwargs: _valid_raw_section(),
    )
    metadata = build_health_report_persistence_metadata(
        section_result,
        report_job_id="job-approved",
        report_status="completed",
        report_generation_mode="async_report_job",
        async_job_used=True,
        provider_enabled=True,
    )
    metadata["raw_output"] = "THIS SHOULD NOT PERSIST"
    metadata["model_facing_quote_context"] = {"unsafe": True}
    metadata["approved_training_quote_context"] = {"unsafe": True}
    metadata["validation_errors"] = ["debug-only"]

    report_service.save_health_report(
        user_id=102,
        report_text=PUBLIC_REPORT_TEXT,
        model_summary="ollama/qwen3:8b",
        report_date="2026-06-14",
        report_metadata=metadata,
    )

    report = _latest_report_payload()
    persisted_metadata = report["report_metadata"]
    metadata_json = report["report_metadata_json"]

    assert (
        section_result.approved_section.source
        == FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED
    )
    assert persisted_metadata["provider_enabled"] is True
    assert persisted_metadata["provider_attempted"] is True
    assert persisted_metadata["selected_provider"] == "direct_ollama"
    assert persisted_metadata["training_section_source"] == "direct_ollama_approved"
    assert persisted_metadata["validation_errors_count"] == 0
    assert "raw_output" not in metadata_json
    assert "model_facing_quote_context" not in metadata_json
    assert "approved_training_quote_context" not in metadata_json
    assert '"validation_errors"' not in metadata_json


def test_provider_fallback_report_persistence_records_safe_fallback_metadata(
    temp_database,
    monkeypatch,
):
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    section_result = build_configured_training_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=lambda *_args, **_kwargs: "not json",
    )
    metadata = build_health_report_persistence_metadata(
        section_result,
        report_job_id="job-fallback",
        report_status="completed",
        report_generation_mode="async_report_job",
        async_job_used=True,
        provider_enabled=True,
    )

    report_service.save_health_report(
        user_id=102,
        report_text="Deterministic fallback report text stayed public-safe.",
        model_summary="ollama/qwen3:8b",
        report_date="2026-06-14",
        report_metadata=metadata,
    )

    report = _latest_report_payload()

    assert (
        section_result.approved_section.source
        == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    )
    assert report["report_metadata"]["provider_attempted"] is True
    assert report["report_metadata"]["fallback_used"] is True
    assert report["report_metadata"]["fallback_reason"] is not None
    assert (
        report["report_metadata"]["training_section_source"] == "deterministic_fallback"
    )
    assert report["report_metadata"]["validation_status"] != "approved"
    assert "not json" not in report["report_text"]


@pytest.mark.parametrize(
    "forbidden_term",
    [
        "raw_output",
        "raw_output_preview_truncated",
        "model_facing_quote_context",
        "approved_training_quote_context",
        "candidate_parse_status",
        "validation_errors",
        "prompt",
        "schema",
    ],
)
def test_public_report_persistence_rejects_debug_provider_terms(
    temp_database,
    forbidden_term,
):
    with pytest.raises(ValueError, match="forbidden debug/provider terms"):
        report_service.save_health_report(
            user_id=102,
            report_text=f"This public report accidentally includes {forbidden_term}.",
            model_summary="ollama/qwen3:8b",
            report_date="2026-06-14",
        )


def test_report_history_keeps_metadata_separate_from_public_text(temp_database):
    report_service.save_health_report(
        user_id=102,
        report_text="Safe public report history item.",
        model_summary="ollama/qwen3:8b",
        report_date="2026-06-14",
        report_metadata={
            "provider_attempted": True,
            "selected_provider": "direct_ollama",
            "training_section_source": "direct_ollama_approved",
            "raw_output": "drop this",
        },
    )

    rows = report_service.get_health_report_history(102, limit=5)
    assert len(rows) == 1
    report = dict(rows[0])

    assert report["report_text"] == "Safe public report history item."
    assert "raw_output" not in report["report_text"]
    assert "raw_output" not in report["report_metadata_json"]
    assert (
        json.loads(report["report_metadata_json"])["selected_provider"]
        == "direct_ollama"
    )


def test_crewai_failure_persists_safe_fallback_report_with_provider_metadata(
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
            raise RuntimeError("simulated crew failure should not persist")

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

    def fake_build_training_section_result(**_kwargs):
        return approved_training_section_result

    monkeypatch.setattr(
        coordinator_service,
        "build_full_report_training_section_result",
        fake_build_training_section_result,
    )

    result = coordinator_service.generate_health_report(
        102,
        report_date="2026-06-14",
        allow_training_section_provider=True,
        return_training_section_result=True,
        report_job_id="job-crewai-fail",
    )

    report = _latest_report_payload()
    persisted_metadata = report["report_metadata"]

    assert result.training_report_section_result.approved_section.source == (
        FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED
    )
    assert report["report_date"] == "2026-06-14"
    assert report["model_summary"] == "deterministic_fallback_after_crewai_error"
    assert "simulated crew failure" not in report["report_text"]
    assert "raw_output" not in report["report_text"]
    assert "validation_errors" not in report["report_text"]
    assert persisted_metadata["report_job_id"] == "job-crewai-fail"
    assert persisted_metadata["report_status"] == (
        "completed_with_full_report_fallback"
    )
    assert persisted_metadata["report_generation_mode"] == "async_report_job"
    assert persisted_metadata["async_job_used"] is True
    assert persisted_metadata["provider_enabled"] is True
    assert persisted_metadata["provider_attempted"] is True
    assert persisted_metadata["selected_provider"] == "direct_ollama"
    assert persisted_metadata["selected_model"] == "qwen2.5:3b"
    assert persisted_metadata["fallback_used"] is False
    assert persisted_metadata["training_section_source"] == "direct_ollama_approved"
    assert persisted_metadata["validation_status"] == "approved"
    assert persisted_metadata["validation_errors_count"] == 0
    assert "raw_output" not in report["report_metadata_json"]
    assert "model_facing_quote_context" not in report["report_metadata_json"]
    assert '"validation_errors"' not in report["report_metadata_json"]
