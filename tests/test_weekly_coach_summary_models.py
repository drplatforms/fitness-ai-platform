from __future__ import annotations

from dataclasses import fields
from datetime import date

import pytest

from models.weekly_coach_summary_models import (
    WEEKLY_COACH_SUMMARY_FORBIDDEN_APPROVED_FIELDS,
    ApprovedWeeklyCoachSummary,
    CandidateWeeklyCoachSummary,
    WeeklyCoachSummaryConfidence,
    WeeklyCoachSummaryContext,
    WeeklyCoachSummaryFactBoundary,
    WeeklyCoachSummaryJobRecord,
    WeeklyCoachSummaryJobStatus,
    WeeklyCoachSummaryModelError,
    WeeklyCoachSummaryPeriod,
    WeeklyCoachSummaryRuntimeMetadata,
    WeeklyCoachSummarySource,
)


def _candidate(**overrides: object) -> CandidateWeeklyCoachSummary:
    payload: dict[str, object] = {
        "headline": "Steady week with useful signals",
        "weekly_overview": "Training and nutrition logs were consistent enough for a bounded weekly review.",
        "recovery_observation": "Recovery signals look usable but should be interpreted carefully.",
        "nutrition_observation": "Nutrition logging supports a general pattern observation.",
        "training_observation": "Training work was consistent enough to summarize.",
        "primary_pattern": "Consistency is the main signal for this week.",
        "recommended_focus": "Keep the next week simple and repeatable.",
        "next_week_guidance": "Focus on logging quality and controlled progression.",
        "confidence": WeeklyCoachSummaryConfidence.MODERATE,
        "reason_codes": ("weekly_pattern",),
        "limitations": ("Review depends on logged data quality.",),
    }
    payload.update(overrides)
    return CandidateWeeklyCoachSummary(**payload)


def _approved(**overrides: object) -> ApprovedWeeklyCoachSummary:
    candidate = _candidate()
    payload: dict[str, object] = candidate.to_dict()
    payload.update(
        {
            "source": WeeklyCoachSummarySource.DETERMINISTIC,
            "public_safe": True,
            "displayable": True,
        }
    )
    payload.update(overrides)
    return ApprovedWeeklyCoachSummary(**payload)


def test_valid_weekly_period_can_be_constructed() -> None:
    period = WeeklyCoachSummaryPeriod(
        user_id=102,
        week_start=date(2026, 6, 15),
        week_end=date(2026, 6, 21),
        timezone="America/New_York",
        generated_for_date="2026-06-22",
    )

    assert period.to_dict()["week_start"] == "2026-06-15"
    assert period.to_dict()["week_end"] == "2026-06-21"
    assert period.to_dict()["generated_for_date"] == "2026-06-22"


def test_week_start_after_week_end_is_rejected() -> None:
    with pytest.raises(WeeklyCoachSummaryModelError):
        WeeklyCoachSummaryPeriod(
            user_id=102,
            week_start=date(2026, 6, 22),
            week_end=date(2026, 6, 15),
        )


def test_open_ended_or_overlong_period_is_rejected() -> None:
    with pytest.raises(WeeklyCoachSummaryModelError):
        WeeklyCoachSummaryPeriod(
            user_id=102,
            week_start=date(2026, 6, 1),
            week_end=date(2026, 6, 30),
        )


def test_weekly_context_uses_fact_boundary_not_raw_rows() -> None:
    period = WeeklyCoachSummaryPeriod(
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
    )
    boundary = WeeklyCoachSummaryFactBoundary(
        recovery_facts_available=True,
        nutrition_facts_available=True,
        training_facts_available=True,
        data_quality_limited=True,
        limitations=("Some meals may be missing.",),
    )
    context = WeeklyCoachSummaryContext(
        user_id=102,
        period=period,
        fact_boundary=boundary,
        confidence="Moderate",
        training_summary="Three logged training sessions are available.",
        reason_codes=("training_facts",),
    )

    payload = context.to_dict()
    assert payload["fact_boundary"]["training_facts_available"] is True
    assert "raw_database_rows" not in payload


def test_valid_candidate_weekly_summary_can_be_constructed() -> None:
    candidate = _candidate(confidence="High")

    assert candidate.confidence == WeeklyCoachSummaryConfidence.HIGH
    assert candidate.to_dict()["headline"] == "Steady week with useful signals"


def test_candidate_required_user_facing_sections_cannot_be_empty() -> None:
    with pytest.raises(WeeklyCoachSummaryModelError):
        _candidate(weekly_overview="   ")


def test_approved_summary_can_be_constructed_when_public_safe_and_displayable() -> None:
    approved = _approved(source="deterministic")

    assert approved.public_safe is True
    assert approved.displayable is True
    assert approved.source == WeeklyCoachSummarySource.DETERMINISTIC


def test_non_public_safe_output_cannot_be_displayable() -> None:
    with pytest.raises(WeeklyCoachSummaryModelError):
        _approved(public_safe=False, displayable=True)


def test_non_public_safe_output_can_be_held_non_displayable_for_rejection_metadata() -> (
    None
):
    approved = _approved(public_safe=False, displayable=False)

    assert approved.public_safe is False
    assert approved.displayable is False


def test_confidence_source_and_status_values_are_constrained() -> None:
    with pytest.raises(WeeklyCoachSummaryModelError):
        _candidate(confidence="Certain")
    with pytest.raises(WeeklyCoachSummaryModelError):
        _approved(source="raw_provider")
    with pytest.raises(WeeklyCoachSummaryModelError):
        WeeklyCoachSummaryJobRecord(
            job_id="weekly-1",
            user_id=102,
            period=WeeklyCoachSummaryPeriod(
                user_id=102,
                week_start="2026-06-15",
                week_end="2026-06-21",
            ),
            status="queued_worker_started",
            created_at="2026-06-22T12:00:00",
            updated_at="2026-06-22T12:00:00",
        )


def test_status_and_source_export_known_values() -> None:
    assert WeeklyCoachSummaryJobStatus.APPROVED.value == "approved"
    assert WeeklyCoachSummarySource.PROVIDER_APPROVED.value == "provider_approved"
    assert WeeklyCoachSummarySource.PROVIDER_APPROVED.value != "qwen3"


def test_forbidden_language_is_rejected() -> None:
    with pytest.raises(WeeklyCoachSummaryModelError):
        _candidate(
            recommended_focus="You failed this week and need to compensate tomorrow."
        )


def test_approved_summary_has_no_raw_provider_or_prompt_fields() -> None:
    approved_fields = {field.name for field in fields(ApprovedWeeklyCoachSummary)}

    assert approved_fields.isdisjoint(WEEKLY_COACH_SUMMARY_FORBIDDEN_APPROVED_FIELDS)
    assert "raw_provider_output" not in approved_fields
    assert "rejected_provider_output" not in approved_fields
    assert "full_prompt" not in approved_fields
    assert "raw_context" not in approved_fields
    assert "scratchpad" not in approved_fields


def test_runtime_metadata_is_sanitized_only() -> None:
    metadata = WeeklyCoachSummaryRuntimeMetadata(
        provider_attempted=False,
        fallback_used=True,
        fallback_reason="Provider runtime is deferred for this milestone.",
        parse_status="not_attempted",
        validation_status="not_attempted",
        final_summary_source="deterministic_fallback",
        validation_errors=("No provider runtime is configured.",),
    )

    payload = metadata.to_dict()
    assert payload["fallback_used"] is True
    assert payload["final_summary_source"] == "deterministic_fallback"
    assert "raw_provider_output" not in payload
    assert "traceback" not in payload


def test_job_record_is_contract_only_and_does_not_require_persistence_or_provider() -> (
    None
):
    period = WeeklyCoachSummaryPeriod(
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
    )
    record = WeeklyCoachSummaryJobRecord(
        job_id="weekly-102-2026-06-15",
        user_id=102,
        period=period,
        status=WeeklyCoachSummaryJobStatus.CREATED,
        created_at="2026-06-22T12:00:00",
        updated_at="2026-06-22T12:00:00",
        approved_summary=None,
    )

    payload = record.to_dict()
    assert payload["status"] == "created"
    assert payload["approved_summary"] is None
    assert payload["runtime_metadata"]["provider_attempted"] is False
