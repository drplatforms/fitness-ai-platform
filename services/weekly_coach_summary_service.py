from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from models.weekly_coach_summary_models import (
    ApprovedWeeklyCoachSummary,
    CandidateWeeklyCoachSummary,
    WeeklyCoachSummaryConfidence,
    WeeklyCoachSummaryContext,
    WeeklyCoachSummaryFactBoundary,
    WeeklyCoachSummaryModelError,
    WeeklyCoachSummaryPeriod,
    WeeklyCoachSummarySource,
)


class WeeklyCoachSummaryServiceError(ValueError):
    """Raised when the deterministic weekly summary service cannot safely proceed."""


@dataclass(frozen=True)
class WeeklyCoachSummaryFixtureInput:
    """Bounded approved fixture input for the no-worker service shell.

    This is intentionally not a raw database row container. It exists so tests and
    developer preview can exercise the deterministic summary path before fact
    aggregation, persistence, worker, provider runtime, API, or UI milestones exist.
    """

    user_id: int
    week_start: date | str
    week_end: date | str
    training_days_logged: int = 0
    workouts_completed: int = 0
    planned_workouts: int = 0
    recovery_notes_available: bool = False
    nutrition_days_logged: int = 0
    protein_days_logged: int = 0
    average_energy: int | None = None
    average_soreness: int | None = None
    limitations: tuple[str, ...] = ()


STRONG_TRAINING_WORKOUTS = 3
GOOD_NUTRITION_LOGGING_DAYS = 4
GOOD_PROTEIN_LOGGING_DAYS = 4

UNSAFE_PUBLIC_SUMMARY_TERMS = (
    "you failed",
    "lack of discipline",
    "overtraining",
    "undereating",
    "burn this off",
    "compensate tomorrow",
    "you sabotaged",
    "stalled fat loss",
    "severe deficit",
    "critical deficit",
    "raw_provider_output",
    "rejected_provider_output",
    "full_prompt",
    "raw_context",
    "scratchpad",
    "chain_of_thought",
    "traceback",
    "stack trace",
)


def _positive_int(value: int, field_name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise WeeklyCoachSummaryServiceError(
            f"{field_name} must be an integer."
        ) from exc
    if number < 0:
        raise WeeklyCoachSummaryServiceError(f"{field_name} must not be negative.")
    return number


def _bounded_rating(value: int | None, field_name: str) -> int | None:
    if value is None:
        return None
    number = _positive_int(value, field_name)
    if number > 10:
        raise WeeklyCoachSummaryServiceError(f"{field_name} must be between 0 and 10.")
    return number


def _safe_limitations(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    if not isinstance(values, tuple | list):
        raise WeeklyCoachSummaryServiceError(
            "limitations must be a tuple/list of text."
        )
    cleaned: list[str] = []
    for value in values:
        text = " ".join(str(value).strip().split())
        if text:
            cleaned.append(text)
    return tuple(cleaned)


def _contains_unsafe_public_text(*values: str) -> bool:
    combined = " ".join(values).lower()
    return any(term in combined for term in UNSAFE_PUBLIC_SUMMARY_TERMS)


def _confidence_for_fixture(
    *,
    workouts_completed: int,
    planned_workouts: int,
    recovery_notes_available: bool,
    nutrition_days_logged: int,
    protein_days_logged: int,
) -> WeeklyCoachSummaryConfidence:
    if workouts_completed <= 0:
        return WeeklyCoachSummaryConfidence.LIMITED

    complete_nutrition = nutrition_days_logged >= GOOD_NUTRITION_LOGGING_DAYS
    complete_protein = protein_days_logged >= GOOD_PROTEIN_LOGGING_DAYS
    strong_training = workouts_completed >= STRONG_TRAINING_WORKOUTS
    planned_training_signal = planned_workouts <= 0 or workouts_completed >= min(
        planned_workouts, STRONG_TRAINING_WORKOUTS
    )

    if (
        strong_training
        and recovery_notes_available
        and complete_nutrition
        and complete_protein
    ):
        return WeeklyCoachSummaryConfidence.HIGH
    if (
        strong_training
        and planned_training_signal
        and (recovery_notes_available or complete_nutrition)
    ):
        return WeeklyCoachSummaryConfidence.MODERATE
    return WeeklyCoachSummaryConfidence.LOW


def build_weekly_summary_context_from_fixture(
    *,
    user_id: int,
    week_start: date | str,
    week_end: date | str,
    training_days_logged: int = 0,
    workouts_completed: int = 0,
    planned_workouts: int = 0,
    recovery_notes_available: bool = False,
    nutrition_days_logged: int = 0,
    protein_days_logged: int = 0,
    average_energy: int | None = None,
    average_soreness: int | None = None,
    limitations: tuple[str, ...] | list[str] | None = None,
) -> WeeklyCoachSummaryContext:
    """Build a bounded weekly summary context from approved fixture values only.

    This function does not read the database, call providers, create jobs, persist
    summaries, or touch UI state.
    """

    training_days_logged = _positive_int(training_days_logged, "training_days_logged")
    workouts_completed = _positive_int(workouts_completed, "workouts_completed")
    planned_workouts = _positive_int(planned_workouts, "planned_workouts")
    nutrition_days_logged = _positive_int(
        nutrition_days_logged, "nutrition_days_logged"
    )
    protein_days_logged = _positive_int(protein_days_logged, "protein_days_logged")
    average_energy = _bounded_rating(average_energy, "average_energy")
    average_soreness = _bounded_rating(average_soreness, "average_soreness")
    safe_limitations = _safe_limitations(limitations)

    period = WeeklyCoachSummaryPeriod(
        user_id=user_id,
        week_start=week_start,
        week_end=week_end,
        generated_for_date=week_end,
    )
    confidence = _confidence_for_fixture(
        workouts_completed=workouts_completed,
        planned_workouts=planned_workouts,
        recovery_notes_available=recovery_notes_available,
        nutrition_days_logged=nutrition_days_logged,
        protein_days_logged=protein_days_logged,
    )

    reason_codes: list[str] = ["approved_backend_facts_only"]
    context_limitations = list(safe_limitations)

    if workouts_completed >= STRONG_TRAINING_WORKOUTS:
        reason_codes.append("weekly_training_consistency_detected")
    elif workouts_completed <= 0:
        reason_codes.append("insufficient_weekly_data")
        context_limitations.append(
            "No completed workouts are available for this weekly summary."
        )
    else:
        reason_codes.append("mixed_signal_week")

    if not recovery_notes_available:
        reason_codes.append("limited_recovery_logging")
        context_limitations.append("Recovery logging is limited for this week.")
    if nutrition_days_logged < GOOD_NUTRITION_LOGGING_DAYS:
        reason_codes.append("limited_nutrition_logging")
        context_limitations.append("Nutrition logging is limited for this week.")
    if protein_days_logged < GOOD_PROTEIN_LOGGING_DAYS:
        reason_codes.append("limited_protein_logging")
    if average_soreness is not None and average_soreness >= 7:
        reason_codes.append("conservative_progression_recommended")
    if average_energy is not None and average_energy <= 4:
        reason_codes.append("conservative_progression_recommended")

    boundary = WeeklyCoachSummaryFactBoundary(
        recovery_facts_available=bool(recovery_notes_available),
        nutrition_facts_available=nutrition_days_logged > 0,
        training_facts_available=training_days_logged > 0 or workouts_completed > 0,
        workout_execution_facts_available=workouts_completed > 0,
        daily_recommendation_facts_available=False,
        profile_context_available=False,
        data_quality_limited=confidence
        in {WeeklyCoachSummaryConfidence.LIMITED, WeeklyCoachSummaryConfidence.LOW}
        or bool(context_limitations),
        limitations=tuple(dict.fromkeys(context_limitations)),
    )

    completion_text = (
        f"{workouts_completed} of {planned_workouts} planned workouts were completed"
        if planned_workouts
        else f"{workouts_completed} workouts were completed"
    )
    training_summary = (
        f"Training facts show {completion_text} with {training_days_logged} logged training days."
        if workouts_completed > 0 or training_days_logged > 0
        else None
    )
    nutrition_summary = (
        f"Nutrition facts include {nutrition_days_logged} logged days and {protein_days_logged} protein-focused days."
        if nutrition_days_logged > 0 or protein_days_logged > 0
        else None
    )
    recovery_parts: list[str] = []
    if recovery_notes_available:
        recovery_parts.append("Recovery notes are available.")
    if average_energy is not None:
        recovery_parts.append(
            f"Average energy was logged around {average_energy} out of 10."
        )
    if average_soreness is not None:
        recovery_parts.append(
            f"Average soreness was logged around {average_soreness} out of 10."
        )
    recovery_summary = " ".join(recovery_parts) or None

    return WeeklyCoachSummaryContext(
        user_id=user_id,
        period=period,
        fact_boundary=boundary,
        confidence=confidence,
        scenario="weekly_coach_summary_fixture",
        recovery_summary=recovery_summary,
        nutrition_summary=nutrition_summary,
        training_summary=training_summary,
        workout_execution_summary=training_summary,
        recommendation_summary="Use this deterministic summary as a bounded coaching preview, not as provider output.",
        limitations=tuple(dict.fromkeys(context_limitations)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
    )


def _needs_fallback(context: WeeklyCoachSummaryContext) -> bool:
    return (
        context.confidence == WeeklyCoachSummaryConfidence.LIMITED
        or "insufficient_weekly_data" in context.reason_codes
        or not context.fact_boundary.training_facts_available
    )


def generate_candidate_weekly_summary(
    context: WeeklyCoachSummaryContext,
) -> CandidateWeeklyCoachSummary:
    """Generate a deterministic weekly summary candidate from bounded context."""

    if _needs_fallback(context):
        return CandidateWeeklyCoachSummary(
            headline="Weekly summary needs more complete data",
            weekly_overview="Not enough complete weekly data is available to make a strong pattern call yet.",
            recovery_observation="Recovery guidance should stay conservative until more recovery signals are logged.",
            nutrition_observation="Nutrition guidance should stay general until more nutrition entries are available.",
            training_observation="Training signal is limited because completed workout data is incomplete.",
            primary_pattern="Data quality is the main limitation for this weekly review.",
            recommended_focus="Keep logging workouts, recovery, and nutrition consistently before drawing stronger conclusions.",
            next_week_guidance="Use next week to build a clearer baseline with completed workouts and simple recovery notes.",
            confidence=WeeklyCoachSummaryConfidence.LIMITED,
            reason_codes=tuple(
                dict.fromkeys((*context.reason_codes, "deterministic_fallback_used"))
            ),
            limitations=tuple(
                dict.fromkeys(
                    (
                        *context.limitations,
                        "Weekly guidance is limited by incomplete data.",
                    )
                )
            ),
        )

    reason_codes = list(context.reason_codes)
    limitations = list(context.limitations)
    training_signal = "weekly_training_consistency_detected" in reason_codes
    conservative = "conservative_progression_recommended" in reason_codes
    nutrition_limited = "limited_nutrition_logging" in reason_codes
    recovery_limited = "limited_recovery_logging" in reason_codes

    headline = (
        "Solid training consistency with recovery-aware next steps"
        if training_signal
        else "Useful weekly signal with conservative next steps"
    )
    weekly_overview = (
        "You completed several planned training sessions this week, which gives enough signal to identify consistency as the strongest pattern."
        if training_signal
        else "This week has enough logged activity to identify a useful pattern, but the safest interpretation is still conservative."
    )
    recovery_observation = (
        "Recovery information is available, so progression can stay controlled while watching energy and soreness trends."
        if not recovery_limited
        else "Recovery logging is limited, so training guidance should avoid aggressive progression until energy and soreness are logged more consistently."
    )
    nutrition_observation = (
        "Nutrition logging is strong enough to support general weekly guidance without making precise body-composition claims."
        if not nutrition_limited
        else "Nutrition logging is incomplete, so nutrition guidance should stay general and focus on consistent entries around training days."
    )
    training_observation = (
        "Training consistency is the clearest signal this week; keep most work controlled and progress only when recovery stays steady."
        if training_signal
        else "Training was present but mixed, so the best next step is repeating the weekly rhythm before increasing difficulty."
    )
    primary_pattern = (
        "Consistency is improving, while data quality still limits stronger conclusions."
        if training_signal
        else "The main pattern is useful effort with limited evidence for stronger conclusions."
    )
    recommended_focus = (
        "Keep the weekly rhythm, log recovery and nutrition consistently, and use next week's completed sessions to decide whether progression is earned."
        if not conservative
        else "Keep progression controlled, prioritize clean execution, and confirm recovery before increasing training load."
    )
    next_week_guidance = (
        "Repeat the current structure, prioritize clean execution, and make only small increases if recovery stays steady."
        if training_signal
        else "Repeat the simplest successful structure from this week and use consistent logging to confirm the next pattern."
    )

    return CandidateWeeklyCoachSummary(
        headline=headline,
        weekly_overview=weekly_overview,
        recovery_observation=recovery_observation,
        nutrition_observation=nutrition_observation,
        training_observation=training_observation,
        primary_pattern=primary_pattern,
        recommended_focus=recommended_focus,
        next_week_guidance=next_week_guidance,
        confidence=context.confidence,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        limitations=tuple(dict.fromkeys(limitations)),
    )


def approve_weekly_summary_candidate(
    candidate: CandidateWeeklyCoachSummary,
    context: WeeklyCoachSummaryContext,
) -> ApprovedWeeklyCoachSummary:
    """Validate and approve a deterministic candidate into public-safe output."""

    public_values = (
        candidate.headline,
        candidate.weekly_overview,
        candidate.recovery_observation,
        candidate.nutrition_observation,
        candidate.training_observation,
        candidate.primary_pattern,
        candidate.recommended_focus,
        candidate.next_week_guidance,
    )
    if _contains_unsafe_public_text(*public_values):
        return build_weekly_summary_fallback(context, "unsafe_candidate_language")

    source = (
        WeeklyCoachSummarySource.DETERMINISTIC_FALLBACK
        if "deterministic_fallback_used" in candidate.reason_codes
        else WeeklyCoachSummarySource.DETERMINISTIC
    )
    return ApprovedWeeklyCoachSummary(
        headline=candidate.headline,
        weekly_overview=candidate.weekly_overview,
        recovery_observation=candidate.recovery_observation,
        nutrition_observation=candidate.nutrition_observation,
        training_observation=candidate.training_observation,
        primary_pattern=candidate.primary_pattern,
        recommended_focus=candidate.recommended_focus,
        next_week_guidance=candidate.next_week_guidance,
        confidence=candidate.confidence,
        source=source,
        public_safe=True,
        displayable=True,
        reason_codes=tuple(
            dict.fromkeys((*context.reason_codes, *candidate.reason_codes))
        ),
        limitations=tuple(
            dict.fromkeys((*context.limitations, *candidate.limitations))
        ),
    )


def build_weekly_summary_fallback(
    context: WeeklyCoachSummaryContext,
    reason: str,
) -> ApprovedWeeklyCoachSummary:
    """Return deterministic public-safe fallback for limited or unsafe input."""

    safe_reason = str(reason).strip() or "deterministic_fallback_used"
    return ApprovedWeeklyCoachSummary(
        headline="Weekly summary needs more complete data",
        weekly_overview="Not enough complete weekly data is available to make a strong pattern call yet. The safest focus is to keep logging consistently and build a clearer baseline.",
        recovery_observation="Recovery guidance should stay conservative until energy, soreness, sleep, or other recovery signals are logged more consistently.",
        nutrition_observation="Nutrition guidance should stay general until more food or macro entries are available across the week.",
        training_observation="Training guidance should focus on completing planned sessions and recording what was finished before making stronger progression decisions.",
        primary_pattern="Data quality is the main limitation for this weekly review.",
        recommended_focus="Keep logging workouts, recovery, and nutrition consistently before drawing stronger conclusions.",
        next_week_guidance="Use next week to build a clearer baseline with completed workouts, simple recovery notes, and consistent nutrition entries.",
        confidence=WeeklyCoachSummaryConfidence.LIMITED,
        source=WeeklyCoachSummarySource.DETERMINISTIC_FALLBACK,
        public_safe=True,
        displayable=True,
        reason_codes=tuple(
            dict.fromkeys(
                (*context.reason_codes, safe_reason, "deterministic_fallback_used")
            )
        ),
        limitations=tuple(
            dict.fromkeys(
                (*context.limitations, "Weekly guidance is limited by incomplete data.")
            )
        ),
    )


def generate_approved_weekly_summary(
    context: WeeklyCoachSummaryContext,
) -> ApprovedWeeklyCoachSummary:
    """Single deterministic service entry point.

    This function does not persist, create jobs, call providers, import UI modules,
    or require worker/queue/scheduler infrastructure.
    """

    try:
        candidate = generate_candidate_weekly_summary(context)
        return approve_weekly_summary_candidate(candidate, context)
    except (WeeklyCoachSummaryModelError, WeeklyCoachSummaryServiceError) as exc:
        return build_weekly_summary_fallback(
            context, f"service_validation_failed_{type(exc).__name__}"
        )


def approved_weekly_summary_to_public_sections(
    summary: ApprovedWeeklyCoachSummary,
) -> dict[str, Any]:
    """Return only public-safe display sections for developer preview/tests."""

    return {
        "headline": summary.headline,
        "weekly_overview": summary.weekly_overview,
        "recovery_observation": summary.recovery_observation,
        "nutrition_observation": summary.nutrition_observation,
        "training_observation": summary.training_observation,
        "primary_pattern": summary.primary_pattern,
        "recommended_focus": summary.recommended_focus,
        "next_week_guidance": summary.next_week_guidance,
        "confidence": summary.confidence.value,
        "source": summary.source.value,
        "public_safe": summary.public_safe,
        "displayable": summary.displayable,
        "reason_codes": summary.reason_codes,
        "limitations": summary.limitations,
    }
