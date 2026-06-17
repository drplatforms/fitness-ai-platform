from __future__ import annotations

import json
import sqlite3
import sys
import types

import database
from services import coordinator_service, report_service
from services.full_report_section_registry_service import (
    FULL_REPORT_SECTION_REGISTRY_VERSION,
    PROVIDER_STATUS_OPT_IN_FULL_REPORT_INTEGRATED,
    SECTION_ID_TRAINING,
    get_full_report_section_definition,
    get_full_report_section_ids,
    get_full_report_section_registry,
    get_provider_integrated_full_report_section_ids,
)
from services.training_report_section_provider_service import (
    FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED,
    TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    TRAINING_REPORT_SECTION_PROVIDER_ENV,
    build_configured_training_report_section_with_metadata,
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


def _seed_temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()

    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO users (id, name) VALUES (?, ?)", (102, "QA User"))
    conn.commit()
    conn.close()

    return db_path


def _latest_report_payload(user_id: int = 102) -> dict:
    row = report_service.get_latest_health_report(user_id)
    assert row is not None
    payload = dict(row)
    payload["report_metadata"] = json.loads(payload["report_metadata_json"])
    return payload


def test_full_report_section_registry_defines_current_public_sections():
    registry = get_full_report_section_registry()
    section_ids = get_full_report_section_ids()

    assert len(registry) >= 8
    assert section_ids == [section.section_id for section in registry]
    assert len(section_ids) == len(set(section_ids))
    assert {
        "overall_score",
        "profile_context",
        "grounded_recommendation",
        "nutrition_target_display",
        "training",
        "biggest_issue",
        "likely_cause",
        "priority_action",
        "best_recommendation",
    }.issubset(set(section_ids))

    for section in registry:
        assert section.section_id
        assert section.public_display_name
        assert section.current_source
        assert section.deterministic_fallback_owner
        assert section.evidence_source
        assert section.approved_claim_source
        assert section.render_fields
        assert 0 <= section.maturity_level <= 5


def test_training_is_only_full_report_provider_integrated_section():
    provider_integrated_sections = get_provider_integrated_full_report_section_ids()
    training = get_full_report_section_definition(SECTION_ID_TRAINING)

    assert provider_integrated_sections == ["training"]
    assert training is not None
    assert training.provider_status == PROVIDER_STATUS_OPT_IN_FULL_REPORT_INTEGRATED
    assert training.maturity_level == 5
    assert "direct_ollama remains opt-in" in training.notes
    assert "training_section_source" in training.metadata_fields

    for section in get_full_report_section_registry():
        if section.section_id != SECTION_ID_TRAINING:
            assert (
                section.provider_status != PROVIDER_STATUS_OPT_IN_FULL_REPORT_INTEGRATED
            )
            assert section.maturity_level < 5


def test_section_registry_metadata_is_safe_and_allowlisted(tmp_path, monkeypatch):
    _seed_temp_db(tmp_path, monkeypatch)
    section_result = coordinator_service.build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
    )

    metadata = coordinator_service.build_health_report_persistence_metadata(
        section_result,
        report_job_id="job-section-registry",
        report_status="completed",
        report_generation_mode="async_report_job",
        async_job_used=True,
        provider_enabled=False,
    )

    report_service.save_health_report(
        user_id=102,
        report_text="Safe report text with section registry metadata.",
        model_summary="deterministic",
        report_date="2026-06-14",
        report_metadata=metadata,
    )

    report = _latest_report_payload()
    persisted_metadata = report["report_metadata"]

    assert persisted_metadata["full_report_section_registry_version"] == (
        FULL_REPORT_SECTION_REGISTRY_VERSION
    )
    assert "training" in persisted_metadata["full_report_section_ids"].split(",")
    assert persisted_metadata["provider_integrated_report_sections"] == "training"
    assert "raw_output" not in report["report_metadata_json"]
    assert '"validation_errors"' not in report["report_metadata_json"]


def test_crewai_failure_persists_section_registry_metadata_and_retains_training(
    tmp_path,
    monkeypatch,
):
    _seed_temp_db(tmp_path, monkeypatch)
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

    monkeypatch.setitem(
        sys.modules,
        "crewai",
        types.SimpleNamespace(
            LLM=FakeLLM,
            Agent=FakeAgent,
            Task=FakeTask,
            Crew=FakeCrew,
        ),
    )

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
        report_job_id="job-section-registry-fail",
    )

    report = _latest_report_payload()
    persisted_metadata = report["report_metadata"]

    assert result.training_report_section_result.approved_section.source == (
        FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED
    )
    assert "Dumbbell Bench Press" in report["report_text"]
    assert "raw coordinator exception" not in report["report_text"]
    assert persisted_metadata["training_section_source"] == "direct_ollama_approved"
    assert persisted_metadata["full_report_section_registry_version"] == (
        FULL_REPORT_SECTION_REGISTRY_VERSION
    )
    assert persisted_metadata["provider_integrated_report_sections"] == "training"
    assert persisted_metadata["full_report_composer_source"] == (
        "deterministic_fallback_after_crewai_error"
    )
    assert persisted_metadata["coordinator_fallback_reason"] == (
        "crewai_coordinator_error"
    )
    assert "raw coordinator exception" not in report["report_metadata_json"]
