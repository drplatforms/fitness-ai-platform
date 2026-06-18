from __future__ import annotations

from services.coordinator_service import (
    AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV,
    FALLBACK_REASON_FULL_REPORT_PROVIDER_REQUIRES_BACKGROUND_JOB,
    build_full_report_training_section_result,
    training_section_provider_job_metadata,
)
from services.training_report_section_provider_service import (
    FINAL_SECTION_SOURCE_DETERMINISTIC,
    FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
    FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED,
    TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    TRAINING_REPORT_SECTION_PROVIDER_ENV,
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


def test_provider_disabled_default_is_deterministic(monkeypatch):
    monkeypatch.delenv(
        AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV, raising=False
    )
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    calls = {"count": 0}

    def fake_generate(*_args, **_kwargs):
        calls["count"] += 1
        raise AssertionError(
            "disabled full-report provider must not call direct Ollama"
        )

    result = build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert calls["count"] == 0
    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC
    assert result.runtime_metadata.provider_attempted is False
    assert result.runtime_metadata.fallback_used is False


def test_enabled_provider_is_blocked_outside_async_job_context(monkeypatch):
    monkeypatch.setenv(AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    calls = {"count": 0}

    def fake_generate(*_args, **_kwargs):
        calls["count"] += 1
        raise AssertionError("unsafe sync context must not call direct Ollama")

    result = build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert calls["count"] == 0
    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.provider_attempted is False
    assert result.runtime_metadata.fallback_used is True
    assert (
        result.runtime_metadata.fallback_reason
        == FALLBACK_REASON_FULL_REPORT_PROVIDER_REQUIRES_BACKGROUND_JOB
    )


def test_enabled_provider_can_run_in_async_job_context(monkeypatch):
    monkeypatch.setenv(AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    result = build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=lambda *_args, **_kwargs: _valid_raw_section(),
        allow_training_section_provider=True,
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED
    assert result.runtime_metadata.provider_attempted is True
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.validation_status == "approved"


def test_async_job_metadata_is_safe_and_self_contained(monkeypatch):
    monkeypatch.delenv(
        AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV, raising=False
    )
    result = build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
        approved_context=APPROVED_CONTEXT,
    )

    metadata = training_section_provider_job_metadata(
        result,
        report_job_id="job-123",
        provider_enabled=False,
    )

    assert metadata == {
        "report_job_id": "job-123",
        "user_id": 102,
        "report_date": "2026-06-14",
        "provider_enabled": False,
        "provider_attempted": False,
        "selected_provider": "deterministic",
        "selected_model": "deterministic",
        "fallback_used": False,
        "fallback_reason": "full_report_training_section_provider_disabled",
        "training_section_source": "deterministic",
        "provider_latency_ms": None,
        "validation_status": "not_attempted",
        "validation_errors_count": 0,
    }
    assert "raw_output" not in str(metadata)
    assert "model_facing_quote_context" not in str(metadata)
