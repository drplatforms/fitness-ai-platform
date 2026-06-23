from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from models.weekly_coach_summary_models import (
    ApprovedWeeklyCoachSummary,
    CandidateWeeklyCoachSummary,
    WeeklyCoachSummaryConfidence,
    WeeklyCoachSummarySource,
)
from services.weekly_coach_summary_service import (
    approve_weekly_summary_candidate,
    approved_weekly_summary_to_public_sections,
    build_weekly_summary_context_from_fixture,
    generate_approved_weekly_summary,
    generate_candidate_weekly_summary,
)


def _moderate_context():
    return build_weekly_summary_context_from_fixture(
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        training_days_logged=4,
        workouts_completed=3,
        planned_workouts=4,
        recovery_notes_available=True,
        nutrition_days_logged=3,
        protein_days_logged=3,
        average_energy=7,
        average_soreness=4,
        limitations=("One nutrition day may be incomplete.",),
    )


def test_service_builds_valid_weekly_context_from_fixture_data() -> None:
    context = _moderate_context()

    assert context.user_id == 102
    assert context.period.week_start.isoformat() == "2026-06-15"
    assert context.period.week_end.isoformat() == "2026-06-21"
    assert context.fact_boundary.training_facts_available is True
    assert context.fact_boundary.workout_execution_facts_available is True
    assert "approved_backend_facts_only" in context.reason_codes
    assert "raw_database_rows" not in context.to_dict()


def test_service_generates_deterministic_candidate_summary() -> None:
    candidate = generate_candidate_weekly_summary(_moderate_context())

    assert isinstance(candidate, CandidateWeeklyCoachSummary)
    assert "consistency" in candidate.headline.lower()
    assert candidate.confidence == WeeklyCoachSummaryConfidence.MODERATE
    assert "weekly_training_consistency_detected" in candidate.reason_codes


def test_service_approves_safe_candidate_into_approved_summary() -> None:
    context = _moderate_context()
    candidate = generate_candidate_weekly_summary(context)
    approved = approve_weekly_summary_candidate(candidate, context)

    assert isinstance(approved, ApprovedWeeklyCoachSummary)
    assert approved.public_safe is True
    assert approved.displayable is True
    assert approved.source == WeeklyCoachSummarySource.DETERMINISTIC


def test_service_entry_point_returns_public_safe_displayable_summary() -> None:
    approved = generate_approved_weekly_summary(_moderate_context())

    assert approved.public_safe is True
    assert approved.displayable is True
    assert approved.source == WeeklyCoachSummarySource.DETERMINISTIC
    assert approved.confidence in {
        WeeklyCoachSummaryConfidence.MODERATE,
        WeeklyCoachSummaryConfidence.HIGH,
    }


def test_low_data_context_returns_deterministic_fallback() -> None:
    context = build_weekly_summary_context_from_fixture(
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        workouts_completed=0,
        planned_workouts=4,
        nutrition_days_logged=0,
        protein_days_logged=0,
        recovery_notes_available=False,
    )
    approved = generate_approved_weekly_summary(context)

    assert approved.source == WeeklyCoachSummarySource.DETERMINISTIC_FALLBACK
    assert approved.confidence == WeeklyCoachSummaryConfidence.LIMITED
    assert approved.public_safe is True
    assert approved.displayable is True
    assert "deterministic_fallback_used" in approved.reason_codes


def test_candidate_is_not_automatically_treated_as_approved() -> None:
    candidate = generate_candidate_weekly_summary(_moderate_context())

    assert isinstance(candidate, CandidateWeeklyCoachSummary)
    assert not isinstance(candidate, ApprovedWeeklyCoachSummary)
    assert not hasattr(candidate, "public_safe")
    assert not hasattr(candidate, "displayable")


def test_unsafe_candidate_language_triggers_fallback() -> None:
    context = _moderate_context()
    unsafe_candidate = CandidateWeeklyCoachSummary(
        headline="Weekly summary needs caution",
        weekly_overview="You completed useful training data this week.",
        recovery_observation="Recovery should be interpreted conservatively.",
        nutrition_observation="Nutrition logging supports only general guidance.",
        training_observation="Training data exists for a cautious review.",
        primary_pattern="The main pattern is controlled consistency.",
        recommended_focus="Keep the next week simple.",
        next_week_guidance="Use consistent logging before changing the plan.",
        confidence=WeeklyCoachSummaryConfidence.MODERATE,
        reason_codes=("weekly_training_consistency_detected",),
    )
    object.__setattr__(
        unsafe_candidate, "recommended_focus", "raw_provider_output leaked"
    )

    approved = approve_weekly_summary_candidate(unsafe_candidate, context)

    assert approved.source == WeeklyCoachSummarySource.DETERMINISTIC_FALLBACK
    assert "unsafe_candidate_language" in approved.reason_codes
    assert approved.public_safe is True
    assert approved.displayable is True


def test_reason_codes_and_confidence_reflect_data_quality() -> None:
    context = build_weekly_summary_context_from_fixture(
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        training_days_logged=1,
        workouts_completed=1,
        planned_workouts=4,
        nutrition_days_logged=1,
        protein_days_logged=0,
        recovery_notes_available=False,
    )
    approved = generate_approved_weekly_summary(context)

    assert approved.confidence == WeeklyCoachSummaryConfidence.LOW
    assert "mixed_signal_week" in approved.reason_codes
    assert "limited_nutrition_logging" in approved.reason_codes
    assert "limited_recovery_logging" in approved.reason_codes


def test_output_contains_no_raw_provider_or_internal_fields() -> None:
    approved = generate_approved_weekly_summary(_moderate_context())
    public_sections = approved_weekly_summary_to_public_sections(approved)
    public_text = " ".join(str(value) for value in public_sections.values()).lower()

    forbidden = (
        "raw_provider_output",
        "rejected_provider_output",
        "full_prompt",
        "raw_context",
        "scratchpad",
        "chain_of_thought",
        "traceback",
        "stack trace",
    )
    assert all(term not in public_text for term in forbidden)


def test_service_does_not_import_provider_runtime_ollama_crewai_database_or_streamlit() -> (
    None
):
    import services.weekly_coach_summary_service as service

    names = set(service.__dict__)
    assert "database" not in names
    assert "streamlit" not in names
    assert "ollama" not in names
    assert "crewai" not in names
    assert "direct_ollama" not in names


def test_developer_preview_script_runs_successfully() -> None:
    result = subprocess.run(
        [sys.executable, "tools/dev_weekly_coach_summary_preview.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Weekly Coach Summary Preview" in result.stdout
    assert "Source: deterministic" in result.stdout
    assert "Public safe: true" in result.stdout
    assert "Displayable: true" in result.stdout
    assert "raw_provider_output" not in result.stdout
    assert "scratchpad" not in result.stdout


def test_service_module_has_no_provider_runtime_dependency_text() -> None:
    source = Path("services/weekly_coach_summary_service.py").read_text(
        encoding="utf-8"
    )

    assert "daily_coach_async_provider_runtime_service" not in source
    assert "ollama" not in source.lower()
    assert "crewai" not in source.lower()
    assert "streamlit" not in source.lower()
    assert "sqlite" not in source.lower()
