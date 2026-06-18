from __future__ import annotations

import json
import sqlite3
import sys
import types

import pytest

import database
from services import coordinator_service, report_service
from services.nutrition_report_section_provider_service import (
    AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV,
    NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    NUTRITION_REPORT_SECTION_PROVIDER_ENV,
    build_configured_nutrition_report_section_with_metadata,
)
from tests.nutrition_provider_fixtures import (
    build_complete_nutrition_provider_evidence,
    valid_provider_candidate_json,
)


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


def test_default_full_report_nutrition_integration_does_not_attempt_provider(
    monkeypatch,
):
    monkeypatch.delenv(
        coordinator_service.AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED_ENV,
        raising=False,
    )
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        NUTRITION_REPORT_SECTION_PROVIDER_ENV,
        NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    calls = {"count": 0}

    def fail_if_called(*_args, **_kwargs):
        calls["count"] += 1
        raise AssertionError(
            "Nutrition provider must not run when full-report gate is disabled"
        )

    result = coordinator_service.build_full_report_nutrition_section_result(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=build_complete_nutrition_provider_evidence(),
        direct_ollama_generate=fail_if_called,
    )

    assert calls["count"] == 0
    assert result.safe_metadata["provider_attempted"] is False
    assert result.safe_metadata["selected_provider"] == "deterministic"
    assert result.safe_metadata["nutrition_section_source"] == "deterministic"


def test_full_report_nutrition_integration_gate_enabled_uses_fake_generator(
    monkeypatch,
):
    monkeypatch.setenv(
        coordinator_service.AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED_ENV,
        "true",
    )
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        NUTRITION_REPORT_SECTION_PROVIDER_ENV,
        NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    calls = []

    def fake_generate(*args):
        calls.append(args)
        return valid_provider_candidate_json()

    result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=build_complete_nutrition_provider_evidence(),
        direct_ollama_generate=fake_generate,
    )

    assert len(calls) == 1
    assert result.approved_section.source == "direct_ollama_approved"
    assert result.safe_metadata["provider_attempted"] is True
    assert result.safe_metadata["fallback_used"] is False


def test_full_report_renders_nutrition_section_separately_from_target_display():
    nutrition_result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=build_complete_nutrition_provider_evidence(),
        direct_ollama_generate=lambda *_args: valid_provider_candidate_json(),
    )
    report = coordinator_service.render_unified_health_report(
        coordinator_service.UnifiedHealthReport(
            overall_score=80,
            biggest_issue="Nutrition evidence is bounded by approved logs.",
            likely_cause="Available evidence supports a conservative nutrition focus.",
            priority_action="Use approved nutrition guidance only.",
            recommendation="Keep logging nutrition consistently.",
        ),
        nutrition_report_section_result=nutrition_result,
    )

    assert "**Nutrition Report Section:**" in report
    assert "Nutrition Target Display" not in report
    assert "raw_output" not in report
    assert "validation_errors" not in report


def test_invalid_full_report_nutrition_candidate_falls_back(monkeypatch):
    monkeypatch.setenv(
        coordinator_service.AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED_ENV,
        "true",
    )
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        NUTRITION_REPORT_SECTION_PROVIDER_ENV,
        NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=build_complete_nutrition_provider_evidence(),
        direct_ollama_generate=lambda *_args: "not-json",
    )

    assert result.approved_section.source.endswith("fallback")
    assert result.safe_metadata["provider_attempted"] is True
    assert result.safe_metadata["fallback_used"] is True
    assert result.safe_metadata["fallback_reason"] == "nutrition_provider_parse_failed"
    assert "not-json" not in str(result.safe_metadata)
    assert "validation_errors" not in result.safe_metadata


def test_full_report_persistence_stores_nutrition_prefixed_safe_metadata(
    temp_database,
    monkeypatch,
):
    monkeypatch.setenv(
        coordinator_service.AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED_ENV,
        "true",
    )
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        NUTRITION_REPORT_SECTION_PROVIDER_ENV,
        NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    nutrition_result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=build_complete_nutrition_provider_evidence(),
        direct_ollama_generate=lambda *_args: valid_provider_candidate_json(),
    )
    training_result = coordinator_service.build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
    )
    metadata = coordinator_service.build_health_report_persistence_metadata(
        training_result,
        nutrition_report_section_result=nutrition_result,
        report_job_id="job-nutrition",
        report_generation_mode="async_report_job",
        async_job_used=True,
        provider_enabled=False,
    )
    metadata["raw_output"] = "do not persist"
    metadata["validation_errors"] = ["debug only"]
    metadata["nutrition_validation_error_categories"] = ["unsupported_numeric_value"]
    metadata["nutrition_validation_error_fields"] = ["target_alignment"]
    metadata["nutrition_first_validation_error_category"] = "unsupported_numeric_value"
    metadata["nutrition_first_validation_error_field"] = "target_alignment"

    report_service.save_health_report(
        user_id=102,
        report_text="Safe full report with an approved Nutrition Report Section.",
        model_summary="deterministic_test",
        report_date="2026-06-14",
        report_metadata=metadata,
    )

    report = _latest_report_payload()
    persisted = report["report_metadata"]
    metadata_json = report["report_metadata_json"]

    assert persisted["nutrition_full_report_integration_enabled"] is True
    assert persisted["nutrition_provider_attempted"] is True
    assert persisted["nutrition_selected_provider"] == "direct_ollama"
    assert persisted["nutrition_validation_errors_count"] == 0
    assert persisted["nutrition_section_source"] == "direct_ollama_approved"
    assert persisted["provider_integrated_report_sections"] == (
        "training,nutrition_report_section"
    )
    assert "raw_output" not in metadata_json
    assert '"validation_errors"' not in metadata_json
    assert "nutrition_validation_error_categories" not in metadata_json
    assert "nutrition_validation_error_fields" not in metadata_json
    assert "nutrition_first_validation_error_category" not in metadata_json
    assert "nutrition_first_validation_error_field" not in metadata_json


def test_fallback_nutrition_section_is_not_marked_provider_integrated(
    temp_database,
    monkeypatch,
):
    monkeypatch.setenv(
        coordinator_service.AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED_ENV,
        "true",
    )
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        NUTRITION_REPORT_SECTION_PROVIDER_ENV,
        NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    nutrition_result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=build_complete_nutrition_provider_evidence(),
        direct_ollama_generate=lambda *_args: "not-json",
    )
    training_result = coordinator_service.build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
    )

    metadata = coordinator_service.build_health_report_persistence_metadata(
        training_result,
        nutrition_report_section_result=nutrition_result,
        report_job_id="job-nutrition-fallback",
        report_generation_mode="async_report_job",
        async_job_used=True,
        provider_enabled=False,
    )

    report_service.save_health_report(
        user_id=102,
        report_text="Safe fallback report with deterministic Nutrition content.",
        model_summary="deterministic_test",
        report_date="2026-06-14",
        report_metadata=metadata,
    )

    persisted = _latest_report_payload()["report_metadata"]

    assert persisted["nutrition_candidate_valid"] is None
    assert persisted["nutrition_validation_status"] is None
    assert persisted["nutrition_fallback_used"] is True
    assert persisted["nutrition_fallback_reason"] == "nutrition_provider_parse_failed"
    assert persisted["nutrition_section_source"] == (
        "deterministic_nutrition_report_section_fallback"
    )
    assert persisted["provider_integrated_report_sections"] == "training"


def test_disabled_nutrition_provider_gate_is_not_marked_provider_integrated(
    temp_database,
    monkeypatch,
):
    monkeypatch.delenv(
        coordinator_service.AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED_ENV,
        raising=False,
    )
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        NUTRITION_REPORT_SECTION_PROVIDER_ENV,
        NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    nutrition_result = coordinator_service.build_full_report_nutrition_section_result(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=build_complete_nutrition_provider_evidence(),
        direct_ollama_generate=lambda *_args: valid_provider_candidate_json(),
    )
    training_result = coordinator_service.build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
    )

    metadata = coordinator_service.build_health_report_persistence_metadata(
        training_result,
        nutrition_report_section_result=nutrition_result,
        report_job_id="job-nutrition-disabled",
        report_generation_mode="async_report_job",
        async_job_used=True,
        provider_enabled=False,
    )

    report_service.save_health_report(
        user_id=102,
        report_text="Safe report with deterministic Nutrition content.",
        model_summary="deterministic_test",
        report_date="2026-06-14",
        report_metadata=metadata,
    )

    persisted = _latest_report_payload()["report_metadata"]

    assert persisted["nutrition_provider_attempted"] is False
    assert persisted["nutrition_section_source"] == "deterministic"
    assert persisted["provider_integrated_report_sections"] == "training"


def test_approved_nutrition_section_survives_crewai_coordinator_failure(
    temp_database,
    monkeypatch,
):
    monkeypatch.setenv(
        coordinator_service.AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED_ENV,
        "true",
    )
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        NUTRITION_REPORT_SECTION_PROVIDER_ENV,
        NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
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

    approved_nutrition_result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=build_complete_nutrition_provider_evidence(),
        direct_ollama_generate=lambda *_args: valid_provider_candidate_json(),
    )
    monkeypatch.setattr(
        coordinator_service,
        "build_full_report_nutrition_section_result",
        lambda **_kwargs: approved_nutrition_result,
    )

    result = coordinator_service.generate_health_report(
        102,
        report_date="2026-06-14",
        return_training_section_result=True,
        report_job_id="job-nutrition-coordinator-fail",
    )

    report = _latest_report_payload()
    persisted = report["report_metadata"]

    assert result.nutrition_report_section_result.approved_section.source == (
        "direct_ollama_approved"
    )
    assert "**Nutrition Report Section:**" in report["report_text"]
    assert "Nutrition logging is complete enough" in report["report_text"]
    assert "raw coordinator exception" not in report["report_text"]
    assert persisted["nutrition_section_source"] == "direct_ollama_approved"
    assert persisted["nutrition_provider_attempted"] is True
    assert persisted["coordinator_fallback_used"] is True
    assert "raw coordinator exception" not in report["report_metadata_json"]


def test_full_report_nutrition_debug_metadata_exposes_diagnostics_not_persistence(
    temp_database,
    monkeypatch,
):
    monkeypatch.setenv(
        coordinator_service.AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED_ENV,
        "true",
    )
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        NUTRITION_REPORT_SECTION_PROVIDER_ENV,
        NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    nutrition_result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=build_complete_nutrition_provider_evidence(),
        direct_ollama_generate=lambda *_args: valid_provider_candidate_json(
            target_alignment="Protein appears below the approved target with a 40 g gap."
        ),
    )
    debug_metadata = coordinator_service.nutrition_section_provider_debug_metadata(
        nutrition_result
    )
    safe_metadata = coordinator_service.nutrition_section_provider_job_metadata(
        nutrition_result
    )

    assert debug_metadata["nutrition_validation_errors_count"] > 0
    assert debug_metadata["validation_error_categories"]
    assert debug_metadata["first_validation_error_category"] is not None
    assert "validation_error_categories" not in safe_metadata
    assert "first_validation_error_category" not in safe_metadata

    report_service.save_health_report(
        user_id=102,
        report_text="Safe full report with diagnostic metadata excluded from history.",
        model_summary="deterministic_test",
        report_date="2026-06-14",
        report_metadata=debug_metadata,
    )

    report = _latest_report_payload()
    metadata_json = report["report_metadata_json"]
    assert "validation_error_categories" not in metadata_json
    assert "validation_error_fields" not in metadata_json
    assert "first_validation_error_category" not in metadata_json
    assert "first_validation_error_field" not in metadata_json


def test_debug_metadata_uses_validation_failure_when_category_mapping_is_empty():
    class FakeNutritionResult:
        safe_metadata = {
            "validation_errors_count": 1,
            "validation_status": "rejected",
            "nutrition_section_source": "deterministic_nutrition_report_section_fallback",
        }
        approved_section = None
        validation_error_categories = []
        validation_error_fields = []

    debug_metadata = coordinator_service.nutrition_section_provider_debug_metadata(
        FakeNutritionResult()
    )

    assert debug_metadata["validation_error_categories"] == ["validation_failure"]
    assert debug_metadata["first_validation_error_category"] == "validation_failure"
    assert debug_metadata["validation_error_fields"] == []
