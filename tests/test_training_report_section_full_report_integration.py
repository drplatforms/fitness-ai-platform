from __future__ import annotations

from models.coordinator_models import UnifiedHealthReport
from services.coordinator_service import (
    AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV,
    build_full_report_training_section_result,
    render_unified_health_report,
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


def _base_report() -> UnifiedHealthReport:
    return UnifiedHealthReport(
        overall_score=80,
        biggest_issue="Training needs steady execution.",
        likely_cause="Current training evidence should stay bounded to logged data.",
        priority_action="Keep the next session deliberate.",
        recommendation="Use the approved training details without adding unsupported claims.",
    )


def test_full_report_training_section_provider_disabled_does_not_call_direct_ollama(
    monkeypatch,
):
    monkeypatch.delenv(
        AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV,
        raising=False,
    )
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    calls = {"count": 0}

    def fake_generate(*_args, **_kwargs):
        calls["count"] += 1
        raise AssertionError("full report provider gate should prevent provider call")

    result = build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert calls["count"] == 0
    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC
    assert result.runtime_metadata.user_id == 102
    assert result.runtime_metadata.report_date == "2026-06-14"
    assert result.runtime_metadata.provider_attempted is False
    assert result.runtime_metadata.fallback_used is False


def test_full_report_training_section_provider_requires_async_job_context(monkeypatch):
    monkeypatch.setenv(AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    calls = {"count": 0}

    def fake_generate(*_args, **_kwargs):
        calls["count"] += 1
        raise AssertionError("unsafe sync path should not call direct Ollama")

    result = build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=fake_generate,
    )

    assert calls["count"] == 0
    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.user_id == 102
    assert result.runtime_metadata.report_date == "2026-06-14"
    assert result.runtime_metadata.provider_attempted is False
    assert result.runtime_metadata.fallback_used is True
    assert (
        result.runtime_metadata.fallback_reason == "provider_requires_async_report_job"
    )


def test_full_report_training_section_opt_in_approved_provider_path(monkeypatch):
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
    assert result.runtime_metadata.user_id == 102
    assert result.runtime_metadata.report_date == "2026-06-14"
    assert result.runtime_metadata.provider_attempted is True
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.validation_status == "approved"


def test_full_report_training_section_opt_in_parser_failure_falls_back(monkeypatch):
    monkeypatch.setenv(AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )

    result = build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=lambda *_args, **_kwargs: "not json",
        allow_training_section_provider=True,
    )

    assert result.approved_section.source == FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    assert result.runtime_metadata.user_id == 102
    assert result.runtime_metadata.report_date == "2026-06-14"
    assert result.runtime_metadata.provider_attempted is True
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.candidate_parse_status == "failed"


def test_rendered_full_report_contains_approved_training_section_without_raw_debug(
    monkeypatch,
):
    monkeypatch.setenv(AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        TRAINING_REPORT_SECTION_PROVIDER_ENV,
        TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    section_result = build_full_report_training_section_result(
        user_id=102,
        report_date="2026-06-14",
        approved_context=APPROVED_CONTEXT,
        direct_ollama_generate=lambda *_args, **_kwargs: _valid_raw_section(),
        allow_training_section_provider=True,
    )

    rendered = render_unified_health_report(
        _base_report(),
        training_report_section_result=section_result,
    )

    assert "**Training Report Section:**" in rendered
    assert "Dumbbell Bench Press" in rendered
    assert "raw_output" not in rendered
    assert "raw_output_preview_truncated" not in rendered
    assert "model_facing_quote_context" not in rendered
    assert "approved_training_quote_context" not in rendered
    assert "candidate_parse_status" not in rendered
    assert "validation_errors" not in rendered
