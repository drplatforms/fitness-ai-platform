from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from models.workout_plan_models import (
    ApprovedPostWorkoutReviewSummary,
    ApprovedPostWorkoutReviewSummaryResult,
    CandidatePostWorkoutReviewSummary,
    PostWorkoutReviewContext,
    PostWorkoutReviewRuntimeMetadata,
)
from services.training_execution_summary_service import build_training_execution_summary
from services.workout_plan_persistence_service import (
    WorkoutPlanInvalidStatusError,
    WorkoutPlanNotFoundError,
    build_planned_vs_actual_summary,
    get_actual_sets,
    get_workout_execution_session_by_id,
    get_workout_plan_instance,
)
from services.workout_plan_service import (
    CANDIDATE_PARSE_STATUS_FAILED,
    CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
    CANDIDATE_PARSE_STATUS_SUCCESS,
    CANDIDATE_VALIDATION_STATUS_FAILED,
    CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
    CANDIDATE_VALIDATION_STATUS_SUCCESS,
    FALLBACK_REASON_INVALID_PROVIDER,
    FALLBACK_REASON_MALFORMED_JSON,
    FALLBACK_REASON_PROVIDER_EXCEPTION,
    FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT,
    FALLBACK_REASON_SCHEMA_MISMATCH,
    FALLBACK_REASON_VALIDATION_FAILURE,
    RAW_OUTPUT_PREVIEW_LIMIT,
    WORKOUT_PROVIDER_CREWAI,
    WORKOUT_PROVIDER_DETERMINISTIC,
    WorkoutCandidateParseError,
    _crew_result_to_raw_json,
    _crewai_workout_llm_kwargs,
    _fallback_crewai_workout_llm_kwargs,
    _provider_exception_summary,
)

logger = logging.getLogger(__name__)

POST_WORKOUT_REVIEW_PROVIDER_ENV = "POST_WORKOUT_REVIEW_PROVIDER"

FINAL_REVIEW_SOURCE_DETERMINISTIC = "deterministic"
FINAL_REVIEW_SOURCE_CREWAI_APPROVED = "crewai_approved"
FINAL_REVIEW_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"

_CONFIDENCE_RANK = {"Limited": 0, "Low": 1, "Moderate": 2, "High": 3}
_ALLOWED_POST_WORKOUT_REVIEW_CONFIDENCE_VALUES = {"Low", "Moderate", "High"}

_ALLOWED_POST_WORKOUT_REVIEW_FIELDS = {
    "session_summary",
    "completion_reflection",
    "effort_reflection",
    "reps_or_volume_reflection",
    "substitutions_or_skips_context",
    "logging_quality_note",
    "next_time_focus",
    "confidence",
}
_REQUIRED_POST_WORKOUT_REVIEW_FIELDS = set(_ALLOWED_POST_WORKOUT_REVIEW_FIELDS)

_POST_WORKOUT_REVIEW_FORBIDDEN_TERMS = [
    "overtraining",
    "stalled progress",
    "stalled weight loss",
    "stalled fat loss",
    "poor adherence",
    "lack of discipline",
    "failed",
    "failure",
    "automatic deload",
    "required deload",
    "must deload",
    "automatic load increase",
    "increase load automatically",
    "add weight automatically",
    "injury diagnosis",
    "diagnose",
    "medical",
    "pain means injury",
    "calorie target",
    "macro target",
    "protein target",
    "carb target",
    "fat target",
    "this proves",
    "this means",
    "failed to",
    "programming failure",
]

_POST_WORKOUT_REVIEW_PROGRAMMING_TERMS = [
    "change your exercises",
    "change exercises",
    "change your sets",
    "change sets",
    "change your reps",
    "change reps",
    "change your rir",
    "change rir",
    "next workout should",
    "next session should add",
    "add weight",
    "increase the weight",
    "increase weight",
    "increase load",
    "add more weight",
    "reduce the weight",
    "cut volume",
    "deload",
    "new exercise",
    "swap the exercise",
    "replace the exercise",
]

_POST_WORKOUT_REVIEW_INTERNAL_TERMS = [
    "backend",
    "schema",
    "validator",
    "validation",
    "fallback",
    "deterministic",
    "source of truth",
    "provider",
    "candidatepostworkoutreviewsummary",
    "approvedpostworkoutreviewsummary",
    "trainingexecutionsummary",
    "workoutexecutionsession",
]


def _raw_output_diagnostics(raw_output: str) -> dict[str, Any]:
    stripped = raw_output.strip()
    return {
        "raw_output_length": len(raw_output),
        "raw_output_preview_truncated": stripped[:RAW_OUTPUT_PREVIEW_LIMIT] or None,
        "markdown_wrapper_detected": stripped.startswith("```")
        or stripped.endswith("```"),
    }


def _require_string(payload: dict, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise WorkoutCandidateParseError(f"Missing or invalid string field: {key}")
    return value.strip()


def _reject_unapproved_fields(
    payload: dict,
    allowed_fields: set[str],
    field_path: str,
) -> None:
    extra_fields = set(payload) - allowed_fields
    if extra_fields:
        formatted = ", ".join(sorted(extra_fields))
        raise WorkoutCandidateParseError(
            f"Unexpected field(s) in {field_path}: {formatted}"
        )


def _fallback_reason_for_parse_error(exc: Exception) -> str:
    message = str(exc).lower()
    if "malformed" in message or "raw json" in message or "empty" in message:
        return FALLBACK_REASON_MALFORMED_JSON
    if "confidence" in message and "missing required field" not in message:
        return "invalid_confidence"
    return FALLBACK_REASON_SCHEMA_MISMATCH


def _bounded_confidence(confidence: str) -> str:
    if confidence in _ALLOWED_POST_WORKOUT_REVIEW_CONFIDENCE_VALUES:
        return confidence
    return "Low"


def _effort_delta_summary(rir_deviation: float | None) -> str:
    if rir_deviation is None:
        return "Actual effort cannot be compared because RIR logging is incomplete."
    if rir_deviation < -0.25:
        return "Actual effort was a little harder than the planned RIR target."
    if rir_deviation > 0.25:
        return "Actual effort was a little easier than the planned RIR target."
    return "Actual effort stayed close to the planned RIR range."


def _reps_completed_summary(summary) -> str:
    inside = summary.sets_inside_planned_reps
    below = summary.sets_below_planned_reps
    above = summary.sets_above_planned_reps
    if inside and not below and not above:
        return "Logged reps mostly landed inside the planned ranges."
    if below or above:
        return "Some logged reps differed from the planned ranges."
    return "Rep completion is hard to assess from the current logs."


def _volume_completion_summary(summary) -> str:
    return (
        f"{summary.completed_set_count} of {summary.planned_set_count} planned sets "
        f"were completed ({summary.completion_percentage:.0f}%)."
    )


def _logging_completeness(summary) -> str:
    incomplete_flags = {
        "incomplete_logging",
        "missing_actual_rir",
        "missing_actual_reps",
        "empty_completion",
    }
    if incomplete_flags & set(summary.deviation_flags):
        return "Some set-level logging is incomplete."
    return "Most set-level fields were logged."


def _review_safety_constraints() -> list[str]:
    return [
        "Do not prescribe the next workout.",
        "Do not recommend automatic load increases.",
        "Do not recommend deloads.",
        "Do not claim overtraining.",
        "Do not criticize adherence.",
    ]


def build_post_workout_review_context(execution_id: int) -> PostWorkoutReviewContext:
    execution_session = get_workout_execution_session_by_id(execution_id)
    if execution_session is None:
        raise WorkoutPlanNotFoundError(
            f"Workout execution session {execution_id} was not found."
        )
    if execution_session.status != "completed":
        raise WorkoutPlanInvalidStatusError(
            "Post-workout reviews require a completed workout execution session. "
            f"Execution session {execution_id} is currently {execution_session.status}."
        )

    plan_instance = get_workout_plan_instance(
        execution_session.workout_plan_instance_id
    )
    if plan_instance is None:
        raise WorkoutPlanNotFoundError(
            f"Workout plan instance {execution_session.workout_plan_instance_id} "
            "was not found."
        )

    summary = build_planned_vs_actual_summary(plan_instance.id)
    actual_sets = get_actual_sets(execution_session_id=execution_session.id)
    completed_actual_sets = [
        actual_set
        for actual_set in actual_sets
        if actual_set.completed and not actual_set.skipped
    ]
    actual_rirs = [
        actual_set.actual_rir
        for actual_set in completed_actual_sets
        if actual_set.actual_rir is not None
    ]

    planned_rir_min_values = [
        exercise.rir_min for exercise in plan_instance.approved_workout_plan.exercises
    ]
    planned_rir_max_values = [
        exercise.rir_max for exercise in plan_instance.approved_workout_plan.exercises
    ]
    training_execution_summary = build_training_execution_summary(plan_instance.user_id)

    approved_summary_facts = [
        _effort_delta_summary(summary.rir_deviation),
        _reps_completed_summary(summary),
        _volume_completion_summary(summary),
        _logging_completeness(summary),
        f"Recent completed planned workout count: {training_execution_summary.completed_execution_count}.",
    ]

    return PostWorkoutReviewContext(
        user_id=plan_instance.user_id,
        execution_id=execution_session.id,
        plan_instance_id=plan_instance.id,
        scenario=plan_instance.scenario,
        confidence=plan_instance.confidence,
        workout_title=plan_instance.approved_workout_plan.title,
        planned_duration_minutes=plan_instance.approved_workout_plan.duration_minutes,
        completed_at=execution_session.completed_at,
        completion_status=execution_session.status,
        exercise_count_planned=summary.planned_exercise_count,
        exercise_count_completed=summary.completed_exercise_count,
        planned_sets=summary.planned_set_count,
        completed_sets=summary.completed_set_count,
        skipped_exercise_count=summary.skipped_exercise_count,
        substitution_count=summary.substituted_exercise_count,
        planned_rir_range=[
            min(planned_rir_min_values) if planned_rir_min_values else None,
            max(planned_rir_max_values) if planned_rir_max_values else None,
        ],
        actual_rir_average=summary.average_actual_rir,
        actual_rir_min=min(actual_rirs) if actual_rirs else None,
        actual_rir_max=max(actual_rirs) if actual_rirs else None,
        effort_delta_summary=_effort_delta_summary(summary.rir_deviation),
        reps_completed_summary=_reps_completed_summary(summary),
        volume_completion_summary=_volume_completion_summary(summary),
        logging_completeness=_logging_completeness(summary),
        safety_constraints=_review_safety_constraints(),
        approved_summary_facts=approved_summary_facts,
        approved_workout_plan=plan_instance.approved_workout_plan,
        planned_vs_actual_summary=summary,
    )


def post_workout_review_context_to_llm_json(
    context: PostWorkoutReviewContext,
) -> dict[str, Any]:
    return {
        "user_id": context.user_id,
        "execution_id": context.execution_id,
        "plan_instance_id": context.plan_instance_id,
        "scenario": context.scenario,
        "confidence": context.confidence,
        "workout_title": context.workout_title,
        "planned_duration_minutes": context.planned_duration_minutes,
        "completed_at": context.completed_at,
        "completion_status": context.completion_status,
        "exercise_count_planned": context.exercise_count_planned,
        "exercise_count_completed": context.exercise_count_completed,
        "planned_sets": context.planned_sets,
        "completed_sets": context.completed_sets,
        "skipped_exercise_count": context.skipped_exercise_count,
        "substitution_count": context.substitution_count,
        "planned_rir_range": context.planned_rir_range,
        "actual_rir_average": context.actual_rir_average,
        "actual_rir_min": context.actual_rir_min,
        "actual_rir_max": context.actual_rir_max,
        "effort_delta_summary": context.effort_delta_summary,
        "reps_completed_summary": context.reps_completed_summary,
        "volume_completion_summary": context.volume_completion_summary,
        "logging_completeness": context.logging_completeness,
        "safety_constraints": list(context.safety_constraints),
        "approved_summary_facts": list(context.approved_summary_facts),
    }


def _format_review_number(value: float | int | None) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return f"{value:.1f}" if isinstance(value, float) else str(value)


def _has_incomplete_logging(context: PostWorkoutReviewContext) -> bool:
    return "incomplete" in context.logging_completeness.lower()


def _deterministic_session_summary(context: PostWorkoutReviewContext) -> str:
    if context.planned_sets:
        return (
            f"You completed {context.completed_sets} of {context.planned_sets} "
            "planned sets from the approved workout."
        )
    return "You completed the approved workout session and logged enough detail to review it."


def _deterministic_completion_reflection(context: PostWorkoutReviewContext) -> str:
    if context.planned_sets and context.completed_sets >= context.planned_sets:
        return (
            "You completed the planned work for this session, which gives a clear "
            "basis for comparing effort and execution against the plan."
        )
    if context.planned_sets and context.completed_sets > 0:
        return (
            "You completed part of the planned work, and the remaining gap is useful "
            "session context for review."
        )
    return (
        "Differences from the plan should be treated as session context rather than "
        "a negative judgment."
    )


def _deterministic_effort_reflection(context: PostWorkoutReviewContext) -> str:
    planned_min, planned_max = context.planned_rir_range
    if (
        context.actual_rir_average is not None
        and planned_min is not None
        and planned_max is not None
    ):
        return (
            f"Logged effort averaged around RIR {_format_review_number(context.actual_rir_average)}, "
            f"compared with the planned RIR {_format_review_number(planned_min)}-"
            f"{_format_review_number(planned_max)} range."
        )
    return "Effort comparison is limited because some RIR values were not logged."


def _deterministic_reps_or_volume_reflection(context: PostWorkoutReviewContext) -> str:
    summary = context.planned_vs_actual_summary
    if summary.planned_set_count:
        return f"Completed volume was about {summary.completion_percentage:.0f}% of the planned work."
    return "Review completed sets and reps against the plan to understand where the session matched or differed."


def _deterministic_substitution_skip_context(context: PostWorkoutReviewContext) -> str:
    if context.substitution_count and context.skipped_exercise_count:
        return "Substitutions and skipped work were logged and should be treated as context for this session."
    if context.substitution_count:
        return "Substitutions were logged and should be considered part of the session context."
    if context.skipped_exercise_count:
        return "Some planned work was skipped, which is useful context for reviewing the session."
    return "No substitutions or skipped exercises were logged."


def _deterministic_logging_quality_note(context: PostWorkoutReviewContext) -> str:
    if _has_incomplete_logging(context):
        return "More complete reps, weight, and RIR logging will make future reviews more accurate."
    return "Set-level logging was complete enough to support a useful review."


def build_deterministic_post_workout_review_summary(
    context: PostWorkoutReviewContext,
) -> ApprovedPostWorkoutReviewSummary:
    return ApprovedPostWorkoutReviewSummary(
        session_summary=_deterministic_session_summary(context),
        completion_reflection=_deterministic_completion_reflection(context),
        effort_reflection=_deterministic_effort_reflection(context),
        reps_or_volume_reflection=_deterministic_reps_or_volume_reflection(context),
        substitutions_or_skips_context=_deterministic_substitution_skip_context(
            context
        ),
        logging_quality_note=_deterministic_logging_quality_note(context),
        next_time_focus=(
            "For the next logged session, keep reps, weight, and RIR as complete as "
            "possible so the review has better context."
        ),
        confidence=_bounded_confidence(context.confidence),
    )


def parse_candidate_post_workout_review_summary_json(
    raw_output: str,
    *,
    strict: bool = True,
) -> CandidatePostWorkoutReviewSummary:
    if not isinstance(raw_output, str) or not raw_output.strip():
        raise WorkoutCandidateParseError(
            "Candidate post-workout review output is empty."
        )

    stripped_output = raw_output.strip()
    if stripped_output.startswith("```") or stripped_output.endswith("```"):
        raise WorkoutCandidateParseError(
            "Candidate post-workout review output must be raw JSON, not markdown."
        )

    try:
        payload = json.loads(stripped_output)
    except json.JSONDecodeError as exc:
        raise WorkoutCandidateParseError(
            "Malformed CandidatePostWorkoutReviewSummary JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise WorkoutCandidateParseError(
            "CandidatePostWorkoutReviewSummary JSON must be an object."
        )

    missing_fields = _REQUIRED_POST_WORKOUT_REVIEW_FIELDS - set(payload)
    if missing_fields:
        formatted = ", ".join(sorted(missing_fields))
        raise WorkoutCandidateParseError(
            "CandidatePostWorkoutReviewSummary missing required field(s): " + formatted
        )

    if strict:
        _reject_unapproved_fields(
            payload,
            _ALLOWED_POST_WORKOUT_REVIEW_FIELDS,
            "post_workout_review",
        )

    confidence = _require_string(payload, "confidence")
    if confidence not in _ALLOWED_POST_WORKOUT_REVIEW_CONFIDENCE_VALUES:
        raise WorkoutCandidateParseError(
            "CandidatePostWorkoutReviewSummary confidence is invalid."
        )

    return CandidatePostWorkoutReviewSummary(
        session_summary=_require_string(payload, "session_summary"),
        completion_reflection=_require_string(payload, "completion_reflection"),
        effort_reflection=_require_string(payload, "effort_reflection"),
        reps_or_volume_reflection=_require_string(payload, "reps_or_volume_reflection"),
        substitutions_or_skips_context=_require_string(
            payload, "substitutions_or_skips_context"
        ),
        logging_quality_note=_require_string(payload, "logging_quality_note"),
        next_time_focus=_require_string(payload, "next_time_focus"),
        confidence=confidence,
    )


def _post_workout_review_text_blob(candidate: CandidatePostWorkoutReviewSummary) -> str:
    return " ".join(
        [
            candidate.session_summary,
            candidate.completion_reflection,
            candidate.effort_reflection,
            candidate.reps_or_volume_reflection,
            candidate.substitutions_or_skips_context,
            candidate.logging_quality_note,
            candidate.next_time_focus,
        ]
    ).lower()


def validate_candidate_post_workout_review_summary(
    candidate: CandidatePostWorkoutReviewSummary,
    context: PostWorkoutReviewContext,
) -> list[str]:
    violations: list[str] = []

    if _CONFIDENCE_RANK.get(candidate.confidence, -1) > _CONFIDENCE_RANK.get(
        context.confidence,
        -1,
    ):
        violations.append(
            "Post-workout review confidence must not exceed context confidence."
        )

    fields = [
        candidate.session_summary,
        candidate.completion_reflection,
        candidate.effort_reflection,
        candidate.reps_or_volume_reflection,
        candidate.substitutions_or_skips_context,
        candidate.logging_quality_note,
        candidate.next_time_focus,
    ]
    if any(len(field) > 240 for field in fields):
        violations.append("Post-workout review fields must be concise.")

    text = _post_workout_review_text_blob(candidate)

    for term in _POST_WORKOUT_REVIEW_FORBIDDEN_TERMS:
        if term in text:
            violations.append("Post-workout review contains forbidden coaching claims.")
            break

    for term in _POST_WORKOUT_REVIEW_PROGRAMMING_TERMS:
        if term in text:
            violations.append(
                "Post-workout review must not prescribe programming changes."
            )
            break

    for term in _POST_WORKOUT_REVIEW_INTERNAL_TERMS:
        if term in text:
            violations.append("Post-workout review contains internal/debug language.")
            break

    return violations


def approve_candidate_post_workout_review_summary(
    candidate: CandidatePostWorkoutReviewSummary,
    context: PostWorkoutReviewContext,
) -> ApprovedPostWorkoutReviewSummary:
    return ApprovedPostWorkoutReviewSummary(
        session_summary=candidate.session_summary,
        completion_reflection=candidate.completion_reflection,
        effort_reflection=candidate.effort_reflection,
        reps_or_volume_reflection=candidate.reps_or_volume_reflection,
        substitutions_or_skips_context=candidate.substitutions_or_skips_context,
        logging_quality_note=candidate.logging_quality_note,
        next_time_focus=candidate.next_time_focus,
        confidence=candidate.confidence,
    )


def _deterministic_post_workout_review_summary_result(
    context: PostWorkoutReviewContext,
    metadata: PostWorkoutReviewRuntimeMetadata,
) -> ApprovedPostWorkoutReviewSummaryResult:
    return ApprovedPostWorkoutReviewSummaryResult(
        approved_post_workout_review_summary=build_deterministic_post_workout_review_summary(
            context
        ),
        runtime_metadata=metadata,
    )


def build_crewai_post_workout_review_summary_prompt(
    context: PostWorkoutReviewContext,
) -> str:
    safe_context = post_workout_review_context_to_llm_json(context)
    return f"""
You are a post-workout review JSON writer. Write like a calm coach reviewing a completed session, not like a policy document.

The workout has already been planned and completed. The programming decisions are already set.
Your job is only to summarize the completed session in concise, supportive coaching language.

Return one raw JSON object only. No markdown. No code fences. No commentary. No extra keys.

Required JSON object:
{{
  "session_summary": "one short sentence",
  "completion_reflection": "one short sentence",
  "effort_reflection": "one short sentence",
  "reps_or_volume_reflection": "one short sentence",
  "substitutions_or_skips_context": "one short sentence",
  "logging_quality_note": "one short sentence",
  "next_time_focus": "one short sentence",
  "confidence": "Low | Moderate | High"
}}

Approved context:
{json.dumps(safe_context, separators=(",", ":"), sort_keys=True)}

Rules:
- Use only the approved context.
- Do not change the workout plan.
- Do not prescribe the next workout.
- Do not recommend load increases.
- Do not recommend deloads.
- Do not make medical or injury claims.
- Do not claim overtraining.
- Do not claim stalled progress.
- Do not criticize adherence, discipline, or effort.
- Differences from the plan are session context, not a score or judgment.
- Substitutions and skipped items must be described neutrally as context.
- The next_time_focus field must only mention logging quality, review quality, execution awareness, or noting substitutions/skips.
- The next_time_focus field must not prescribe changes to the next workout.
- Do not make nutrition claims unless explicitly present in the context.
- Keep the tone neutral, supportive, practical, and coach-like.
- If data is incomplete, mention logging quality gently.
- Confidence must not exceed the approved context confidence.

Return JSON only.
""".strip()


def generate_crewai_post_workout_review_summary_json(
    context: PostWorkoutReviewContext,
) -> str:
    """Run optional CrewAI post-workout review summary generation.

    Returned text is untrusted and must pass strict parse/validation before use.
    """

    from crewai import LLM, Agent, Crew, Task

    llm_kwargs = _crewai_workout_llm_kwargs()
    try:
        llm = LLM(**llm_kwargs)
    except TypeError:
        logger.warning(
            "crewai_post_workout_review_llm_rejected_pass_through_kwargs",
            extra={
                "model": llm_kwargs.get("model"),
                "base_url": llm_kwargs.get("base_url"),
            },
        )
        llm = LLM(**_fallback_crewai_workout_llm_kwargs(llm_kwargs))

    review_agent = Agent(
        role="Post-Workout Review JSON Writer",
        goal="Summarize a completed workout without changing future programming.",
        backstory=(
            "You write concise, neutral post-workout reflections from approved "
            "planned-vs-actual data. You never prescribe future workout structure."
        ),
        llm=llm,
        verbose=False,
    )
    review_task = Task(
        description=build_crewai_post_workout_review_summary_prompt(context),
        expected_output="Raw CandidatePostWorkoutReviewSummary JSON object only.",
        agent=review_agent,
    )
    crew = Crew(agents=[review_agent], tasks=[review_task], verbose=False)
    result = crew.kickoff()
    return _crew_result_to_raw_json(result)


def _log_post_workout_review_runtime(
    context: PostWorkoutReviewContext,
    metadata: PostWorkoutReviewRuntimeMetadata,
    elapsed_ms: int,
) -> None:
    logger.info(
        "post_workout_review_provider_result",
        extra={
            "user_id": context.user_id,
            "execution_id": context.execution_id,
            "plan_instance_id": context.plan_instance_id,
            "configured_provider": metadata.configured_provider,
            "selected_provider": metadata.selected_provider,
            "crewai_attempted": metadata.crewai_attempted,
            "candidate_parse_status": metadata.candidate_parse_status,
            "candidate_validation_status": metadata.candidate_validation_status,
            "final_review_source": metadata.final_review_source,
            "fallback_used": metadata.fallback_used,
            "fallback_reason": metadata.fallback_reason,
            "validation_violations": metadata.validation_errors,
            "raw_output_length": metadata.raw_output_length,
            "markdown_wrapper_detected": metadata.markdown_wrapper_detected,
            "elapsed_ms": elapsed_ms,
        },
    )


def approve_post_workout_review_summary_json_or_fallback_with_metadata(
    raw_json: str,
    context: PostWorkoutReviewContext,
    *,
    configured_provider: str = WORKOUT_PROVIDER_DETERMINISTIC,
    selected_provider: str = WORKOUT_PROVIDER_DETERMINISTIC,
    crewai_attempted: bool = False,
) -> ApprovedPostWorkoutReviewSummaryResult:
    start_time = time.perf_counter()
    raw_diagnostics = _raw_output_diagnostics(raw_json)
    try:
        candidate = parse_candidate_post_workout_review_summary_json(raw_json)
        violations = validate_candidate_post_workout_review_summary(candidate, context)
        if violations:
            metadata = PostWorkoutReviewRuntimeMetadata(
                configured_provider=configured_provider,
                selected_provider=selected_provider,
                crewai_attempted=crewai_attempted,
                fallback_used=True,
                fallback_reason=FALLBACK_REASON_VALIDATION_FAILURE,
                review_valid=False,
                validation_errors=violations,
                candidate_parse_status=CANDIDATE_PARSE_STATUS_SUCCESS,
                candidate_validation_status=CANDIDATE_VALIDATION_STATUS_FAILED,
                final_review_source=FINAL_REVIEW_SOURCE_DETERMINISTIC_FALLBACK,
                **raw_diagnostics,
            )
            result = _deterministic_post_workout_review_summary_result(
                context, metadata
            )
        else:
            metadata = PostWorkoutReviewRuntimeMetadata(
                configured_provider=configured_provider,
                selected_provider=selected_provider,
                crewai_attempted=crewai_attempted,
                fallback_used=False,
                fallback_reason=None,
                review_valid=True,
                validation_errors=[],
                candidate_parse_status=CANDIDATE_PARSE_STATUS_SUCCESS,
                candidate_validation_status=CANDIDATE_VALIDATION_STATUS_SUCCESS,
                final_review_source=(
                    FINAL_REVIEW_SOURCE_CREWAI_APPROVED
                    if crewai_attempted
                    else FINAL_REVIEW_SOURCE_DETERMINISTIC
                ),
                **raw_diagnostics,
            )
            result = ApprovedPostWorkoutReviewSummaryResult(
                approved_post_workout_review_summary=approve_candidate_post_workout_review_summary(
                    candidate,
                    context,
                ),
                runtime_metadata=metadata,
            )
    except (ValueError, WorkoutCandidateParseError) as exc:
        metadata = PostWorkoutReviewRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=crewai_attempted,
            fallback_used=True,
            fallback_reason=_fallback_reason_for_parse_error(exc),
            review_valid=False,
            validation_errors=[str(exc)],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_FAILED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_review_source=FINAL_REVIEW_SOURCE_DETERMINISTIC_FALLBACK,
            **raw_diagnostics,
        )
        result = _deterministic_post_workout_review_summary_result(context, metadata)

    _log_post_workout_review_runtime(
        context,
        result.runtime_metadata,
        elapsed_ms=round((time.perf_counter() - start_time) * 1000),
    )
    return result


def approve_post_workout_review_summary_provider_or_fallback_with_metadata(
    review_provider,
    context: PostWorkoutReviewContext,
    *,
    configured_provider: str = WORKOUT_PROVIDER_CREWAI,
    selected_provider: str = WORKOUT_PROVIDER_CREWAI,
) -> ApprovedPostWorkoutReviewSummaryResult:
    start_time = time.perf_counter()
    try:
        raw_json = review_provider(context)
    except Exception as exc:
        exception_summary = _provider_exception_summary(exc)
        logger.exception(
            "post_workout_review_provider_exception",
            extra={
                "user_id": context.user_id,
                "execution_id": context.execution_id,
                "plan_instance_id": context.plan_instance_id,
                "configured_provider": configured_provider,
                "selected_provider": selected_provider,
                "exception_type": type(exc).__name__,
                "exception_summary": exception_summary,
            },
        )
        metadata = PostWorkoutReviewRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            review_valid=False,
            validation_errors=[exception_summary],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_review_source=FINAL_REVIEW_SOURCE_DETERMINISTIC_FALLBACK,
        )
        result = _deterministic_post_workout_review_summary_result(context, metadata)
        _log_post_workout_review_runtime(
            context,
            result.runtime_metadata,
            elapsed_ms=round((time.perf_counter() - start_time) * 1000),
        )
        return result

    if not isinstance(raw_json, str):
        metadata = PostWorkoutReviewRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            crewai_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT,
            review_valid=False,
            validation_errors=[
                "CandidatePostWorkoutReviewSummary provider returned non-string output."
            ],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_review_source=FINAL_REVIEW_SOURCE_DETERMINISTIC_FALLBACK,
        )
        result = _deterministic_post_workout_review_summary_result(context, metadata)
        _log_post_workout_review_runtime(
            context,
            result.runtime_metadata,
            elapsed_ms=round((time.perf_counter() - start_time) * 1000),
        )
        return result

    return approve_post_workout_review_summary_json_or_fallback_with_metadata(
        raw_json,
        context,
        configured_provider=configured_provider,
        selected_provider=selected_provider,
        crewai_attempted=True,
    )


def _configured_post_workout_review_provider() -> str:
    return (
        os.getenv(POST_WORKOUT_REVIEW_PROVIDER_ENV, WORKOUT_PROVIDER_DETERMINISTIC)
        .strip()
        .lower()
    )


def build_configured_post_workout_review_summary_with_metadata(
    execution_id: int,
) -> ApprovedPostWorkoutReviewSummaryResult:
    context = build_post_workout_review_context(execution_id)
    provider = _configured_post_workout_review_provider()

    if provider == WORKOUT_PROVIDER_DETERMINISTIC:
        metadata = PostWorkoutReviewRuntimeMetadata(
            configured_provider=provider,
            selected_provider=WORKOUT_PROVIDER_DETERMINISTIC,
            crewai_attempted=False,
            fallback_used=False,
            fallback_reason=None,
            review_valid=True,
            validation_errors=[],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            final_review_source=FINAL_REVIEW_SOURCE_DETERMINISTIC,
        )
        result = _deterministic_post_workout_review_summary_result(context, metadata)
        _log_post_workout_review_runtime(context, result.runtime_metadata, elapsed_ms=0)
        return result

    if provider == WORKOUT_PROVIDER_CREWAI:
        return approve_post_workout_review_summary_provider_or_fallback_with_metadata(
            generate_crewai_post_workout_review_summary_json,
            context,
            configured_provider=provider,
            selected_provider=WORKOUT_PROVIDER_CREWAI,
        )

    metadata = PostWorkoutReviewRuntimeMetadata(
        configured_provider=provider,
        selected_provider=WORKOUT_PROVIDER_DETERMINISTIC,
        crewai_attempted=False,
        fallback_used=True,
        fallback_reason=FALLBACK_REASON_INVALID_PROVIDER,
        review_valid=True,
        validation_errors=[f"Unsupported post-workout review provider: {provider}"],
        candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
        candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
        final_review_source=FINAL_REVIEW_SOURCE_DETERMINISTIC_FALLBACK,
    )
    result = _deterministic_post_workout_review_summary_result(context, metadata)
    _log_post_workout_review_runtime(context, result.runtime_metadata, elapsed_ms=0)
    return result
