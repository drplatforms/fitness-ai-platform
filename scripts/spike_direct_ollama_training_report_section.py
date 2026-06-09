from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Keep CLI stdout machine-readable. Some project modules print database diagnostics
# while building context, so imports and context construction redirect noise to stderr.
with redirect_stdout(sys.stderr):
    from database import get_connection
    from services import ai_nutrition_explanation_service as explanation_service
    from services.training_execution_summary_service import (
        build_training_execution_summary,
    )
    from services.user_state_service import build_user_health_state
    from services.workout_plan_persistence_service import (
        ensure_workout_plan_persistence_tables,
    )

DIRECT_OLLAMA_TRAINING_REPORT_SECTION_PROVIDER_NAME = (
    "direct_ollama_training_report_section_spike"
)
DIRECT_OLLAMA_DEFAULT_BASE_URL = (
    explanation_service.NUTRITION_EXPLANATION_DEFAULT_BASE_URL
)
DIRECT_OLLAMA_RESPONSE_PREVIEW_LIMIT = 500
RECENT_TRAINING_EXECUTION_DETAIL_LIMIT = 3
MAX_PLANNED_EXERCISES_PER_WORKOUT = 8
MAX_ACTUAL_SETS_PER_WORKOUT = 24

TRAINING_SECTION_PARSE_STATUS_NOT_ATTEMPTED = "not_attempted"
TRAINING_SECTION_PARSE_STATUS_SUCCESS = "success"
TRAINING_SECTION_PARSE_STATUS_FAILED = "failed"

TRAINING_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED = "not_attempted"
TRAINING_SECTION_VALIDATION_STATUS_SUCCESS = "success"
TRAINING_SECTION_VALIDATION_STATUS_FAILED = "failed"

TRAINING_SECTION_STATUS_NOT_ATTEMPTED = "not_attempted"
TRAINING_SECTION_STATUS_APPROVED = "approved"
TRAINING_SECTION_STATUS_REJECTED = "rejected"

FINAL_SECTION_SOURCE_PROVIDER_APPROVED = "provider_approved"
FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"

FALLBACK_REASON_PROVIDER_EXCEPTION = "provider_exception"
FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT = "provider_non_string_output"
FALLBACK_REASON_CANDIDATE_PARSE_FAILURE = "candidate_parse_failure"
FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE = "candidate_validation_failure"

CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

CANDIDATE_TRAINING_REPORT_SECTION_ALLOWED_KEYS = {
    "section_summary",
    "key_observations",
    "performance_interpretation",
    "fatigue_recovery_interpretation",
    "suggested_focus",
    "limitations_context",
    "confidence",
    "reason_codes",
}

CANDIDATE_TRAINING_REPORT_SECTION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "section_summary",
        "key_observations",
        "performance_interpretation",
        "fatigue_recovery_interpretation",
        "suggested_focus",
        "limitations_context",
        "confidence",
        "reason_codes",
    ],
    "properties": {
        "section_summary": {"type": "string"},
        "key_observations": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5,
        },
        "performance_interpretation": {"type": "string"},
        "fatigue_recovery_interpretation": {"type": "string"},
        "suggested_focus": {"type": "string"},
        "limitations_context": {"type": "string"},
        "confidence": {
            "type": "string",
            "enum": ["Limited", "Low", "Moderate", "High"],
        },
        "reason_codes": {"type": "array", "items": {"type": "string"}},
    },
}

DirectOllamaGenerateCallable = explanation_service.DirectOllamaGenerateCallable
normalize_ollama_model_name = explanation_service.normalize_ollama_model_name
call_direct_ollama_generate = explanation_service.call_direct_ollama_generate


@dataclass(frozen=True)
class CandidateTrainingReportSection:
    section_summary: str
    key_observations: list[str]
    performance_interpretation: str
    fatigue_recovery_interpretation: str
    suggested_focus: str
    limitations_context: str
    confidence: str
    reason_codes: list[str]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> CandidateTrainingReportSection:
        return cls(
            section_summary=payload["section_summary"],
            key_observations=list(payload["key_observations"]),
            performance_interpretation=payload["performance_interpretation"],
            fatigue_recovery_interpretation=payload["fatigue_recovery_interpretation"],
            suggested_focus=payload["suggested_focus"],
            limitations_context=payload["limitations_context"],
            confidence=payload["confidence"],
            reason_codes=list(payload["reason_codes"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedTrainingQuoteContext:
    approved_workout_names: list[str]
    approved_exercise_names: list[str]
    approved_training_numbers: list[int | float]
    approved_set_rep_load_rir_values: list[dict[str, Any]]
    approved_training_summary_facts: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DirectOllamaTrainingReportSectionSpikeResult:
    success: bool
    provider: str
    section: str
    configured_model: str
    selected_model: str
    user_id: int
    report_date: str
    ollama_base_url: str
    elapsed_seconds: float
    provider_attempted: bool
    candidate_parse_status: str
    candidate_validation_status: str
    validation_status: str
    candidate_valid: bool
    fallback_used: bool
    fallback_reason: str | None
    final_section_source: str
    approved_section: dict[str, Any]
    validation_errors: list[str] = field(default_factory=list)
    raw_output_length: int | None = None
    raw_output_preview_truncated: str | None = None
    markdown_wrapper_detected: bool = False
    extra_keys_detected: list[str] = field(default_factory=list)
    wrapper_object_detected: bool = False
    approved_training_quote_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_training_report_section_context(
    *,
    user_id: int,
    report_date: str,
    recent_execution_limit: int = RECENT_TRAINING_EXECUTION_DETAIL_LIMIT,
) -> dict[str, Any]:
    """Build bounded backend-approved context for the training section spike."""

    with redirect_stdout(sys.stderr):
        health_state = build_user_health_state(user_id)
        execution_summary = build_training_execution_summary(user_id)
        recent_executions = _load_recent_training_execution_details(
            user_id=user_id,
            limit=recent_execution_limit,
        )
    quote_context = build_approved_training_quote_context(
        recent_training_executions=recent_executions,
        training_execution_summary=execution_summary.to_dict(),
    )

    return _compact_dict(
        {
            "section": "training",
            "user_id": user_id,
            "report_date": report_date,
            "training_state": _compact_dict(
                {
                    "workout_summary": getattr(
                        health_state.training_state,
                        "workout_summary",
                        None,
                    ),
                    "has_workout_data": getattr(
                        health_state.training_state,
                        "has_workout_data",
                        None,
                    ),
                    "workout_count": getattr(
                        health_state.training_state,
                        "workout_count",
                        None,
                    ),
                    "adherence_level": getattr(
                        health_state.training_state,
                        "adherence_level",
                        None,
                    ),
                    "training_trend": getattr(
                        health_state.training_state,
                        "training_trend",
                        None,
                    ),
                    "total_volume_load": getattr(
                        health_state.training_state,
                        "total_volume_load",
                        None,
                    ),
                    "avg_rir": getattr(health_state.training_state, "avg_rir", None),
                    "training_load": getattr(
                        health_state.training_state,
                        "training_load",
                        None,
                    ),
                    "recovery_demand": getattr(
                        health_state.training_state,
                        "recovery_demand",
                        None,
                    ),
                }
            ),
            "recovery_constraints": _compact_dict(
                {
                    "recovery_score": getattr(
                        health_state.recovery_state,
                        "recovery_score",
                        None,
                    ),
                    "fatigue_risk": getattr(
                        health_state.recovery_state,
                        "fatigue_risk",
                        None,
                    ),
                    "readiness_level": getattr(
                        health_state.recovery_state,
                        "readiness_level",
                        None,
                    ),
                    "avg_sleep": getattr(
                        health_state.recovery_state, "avg_sleep", None
                    ),
                    "avg_energy": getattr(
                        health_state.recovery_state,
                        "avg_energy",
                        None,
                    ),
                    "avg_soreness": getattr(
                        health_state.recovery_state,
                        "avg_soreness",
                        None,
                    ),
                }
            ),
            "training_execution_summary": execution_summary.to_dict(),
            "recent_training_executions": recent_executions,
            "approved_training_quote_context": quote_context.to_dict(),
        }
    )


def build_approved_training_quote_context(
    *,
    recent_training_executions: list[dict[str, Any]],
    training_execution_summary: dict[str, Any] | None = None,
) -> ApprovedTrainingQuoteContext:
    """Build bounded quoteable training context from approved backend data."""

    workout_names: list[str] = []
    exercise_names: list[str] = []
    approved_numbers: list[int | float] = []
    set_rep_load_rir_values: list[dict[str, Any]] = []
    summary_facts: list[str] = []

    for execution in recent_training_executions:
        workout_name = _safe_nonempty_string(execution.get("workout_title"))
        if workout_name:
            _append_unique_string(workout_names, workout_name)
            summary_facts.append(f"{workout_name} was completed.")

        planned_by_name: dict[str, dict[str, Any]] = {}
        for planned in execution.get("planned_exercises", []):
            if not isinstance(planned, dict):
                continue
            exercise_name = _safe_nonempty_string(planned.get("exercise_name"))
            if not exercise_name:
                continue
            _append_unique_string(exercise_names, exercise_name)
            planned_by_name[_normalize_name(exercise_name)] = planned
            _extend_approved_numbers(
                approved_numbers,
                [
                    planned.get("planned_sets"),
                    planned.get("planned_reps_min"),
                    planned.get("planned_reps_max"),
                    planned.get("planned_rir_min"),
                    planned.get("planned_rir_max"),
                ],
            )
            planned_sets = planned.get("planned_sets")
            reps_text = _format_range(
                planned.get("planned_reps_min"), planned.get("planned_reps_max")
            )
            rir_text = _format_range(
                planned.get("planned_rir_min"), planned.get("planned_rir_max")
            )
            fact_parts: list[str] = []
            if planned_sets is not None:
                fact_parts.append(f"{planned_sets} sets")
            if reps_text:
                fact_parts.append(f"{reps_text} reps")
            if rir_text:
                fact_parts.append(f"RIR {rir_text}")
            if workout_name and fact_parts:
                summary_facts.append(
                    f"{exercise_name} was planned in {workout_name} for "
                    + ", ".join(fact_parts)
                    + "."
                )

        actual_sets_by_exercise: dict[str, list[dict[str, Any]]] = {}
        for actual in execution.get("actual_sets", []):
            if not isinstance(actual, dict):
                continue
            exercise_name = _safe_nonempty_string(actual.get("exercise_name"))
            if not exercise_name:
                continue
            _append_unique_string(exercise_names, exercise_name)
            normalized_exercise_name = _normalize_name(exercise_name)
            actual_sets_by_exercise.setdefault(normalized_exercise_name, []).append(
                actual
            )
            _extend_approved_numbers(
                approved_numbers,
                [
                    actual.get("set_number"),
                    actual.get("planned_reps_min"),
                    actual.get("planned_reps_max"),
                    actual.get("planned_rir_min"),
                    actual.get("planned_rir_max"),
                    actual.get("actual_reps"),
                    actual.get("actual_weight"),
                    actual.get("actual_rir"),
                ],
            )

        for normalized_exercise_name, actual_sets in actual_sets_by_exercise.items():
            if not actual_sets:
                continue
            exercise_name = _safe_nonempty_string(actual_sets[0].get("exercise_name"))
            planned = planned_by_name.get(normalized_exercise_name, {})
            rep_values = [
                actual.get("actual_reps")
                for actual in actual_sets
                if actual.get("actual_reps") is not None
            ]
            load_values = [
                actual.get("actual_weight")
                for actual in actual_sets
                if actual.get("actual_weight") is not None
            ]
            rir_values = [
                actual.get("actual_rir")
                for actual in actual_sets
                if actual.get("actual_rir") is not None
            ]
            actual_sets_count = len(actual_sets)
            _append_unique_number(approved_numbers, actual_sets_count)
            value_payload = _compact_dict(
                {
                    "workout_name": workout_name,
                    "exercise_name": exercise_name,
                    "planned_sets": planned.get("planned_sets"),
                    "planned_reps": _format_range(
                        planned.get("planned_reps_min"), planned.get("planned_reps_max")
                    ),
                    "planned_rir": _format_range(
                        planned.get("planned_rir_min"), planned.get("planned_rir_max")
                    ),
                    "actual_sets": actual_sets_count,
                    "actual_reps": rep_values,
                    "actual_load_lb": _single_distinct_number(load_values),
                    "actual_rir": rir_values,
                }
            )
            if value_payload:
                set_rep_load_rir_values.append(value_payload)
            if workout_name and exercise_name:
                summary_facts.append(
                    f"{exercise_name} was logged in {workout_name} for {actual_sets_count} set"
                    f"{'s' if actual_sets_count != 1 else ''}."
                )
            if exercise_name and rep_values and load_values:
                load_text = _format_number(_single_distinct_number(load_values))
                reps_text = ", ".join(_format_number(value) for value in rep_values)
                if load_text:
                    summary_facts.append(
                        f"{exercise_name} was logged at {load_text} lb for {reps_text} reps."
                    )
            if exercise_name and rir_values:
                final_rir = rir_values[-1]
                summary_facts.append(
                    f"The final {exercise_name} set was logged at {_format_number(final_rir)} RIR."
                )

    if training_execution_summary:
        for key in [
            "completed_execution_count",
            "average_completion_percentage",
            "average_planned_rir",
            "average_actual_rir",
            "average_rir_deviation",
        ]:
            value = training_execution_summary.get(key)
            if value is not None:
                _append_unique_number(approved_numbers, value)

    return ApprovedTrainingQuoteContext(
        approved_workout_names=workout_names[:8],
        approved_exercise_names=exercise_names[:20],
        approved_training_numbers=approved_numbers[:80],
        approved_set_rep_load_rir_values=set_rep_load_rir_values[:12],
        approved_training_summary_facts=_unique(summary_facts)[:24],
    )


def build_direct_ollama_training_report_section_prompt(
    approved_context: dict[str, Any],
) -> str:
    """Build the strict direct Ollama prompt for one training report section."""

    approved_context_json = json.dumps(approved_context, sort_keys=True, default=str)
    valid_example_json = json.dumps(_candidate_training_report_section_example())
    return f"""
/no_think
Task: write one concise training report section from approved backend context.

Strict output rules:
- Return JSON only: one raw JSON object and nothing else.
- Do not include markdown.
- Do not include code fences.
- Do not include comments.
- Do not include prose outside JSON.
- The first character must be {{ and the last character must be }}.
- Include exactly these top-level keys and no others.
- Do not include provider fields, runtime fields, debug fields, validation fields, or raw context keys.
- Do not copy backend context keys into the output unless they are explicitly listed in the schema.
- Use only approved_training_quote_context for exact names, numbers, and training facts.
- If approved workout or exercise names exist, mention at least one exact approved name.
- Quote only workout names from approved_workout_names.
- Quote only exercise names from approved_exercise_names.
- Quote only numbers from approved_training_numbers or approved_training_summary_facts.
- You may restate facts from approved_training_summary_facts.
- Do not calculate or infer volume load, average RIR, percentages, week-over-week change, progression, fatigue, or recovery status unless the exact fact is listed in approved_training_summary_facts.
- Do not invent workouts, exercises, sets, reps, loads, weights, RIR, progression, fatigue, recovery status, or health metrics.
- Do not prescribe a new workout plan or mutate backend recommendations.
- If detailed execution data is limited, say that training detail is limited.

CandidateTrainingReportSection allowed output schema:
{{
  "section_summary": "string",
  "key_observations": ["string"],
  "performance_interpretation": "string",
  "fatigue_recovery_interpretation": "string",
  "suggested_focus": "string",
  "limitations_context": "string",
  "confidence": "Limited | Low | Moderate | High",
  "reason_codes": ["string"]
}}

One valid JSON example:
{valid_example_json}

Approved context JSON:
{approved_context_json}

Forbidden language and behavior:
- Do not make medical, disease, diagnosis, treatment, cure, or injury claims.
- Do not invent progression claims or say performance improved unless approved_training_summary_facts supports it.
- Do not invent exact workout, exercise, set, rep, load, weight, or RIR values.
- Do not use phrases such as "source of truth", "validator", "fallback", "debug", "provider", "Ollama", or "CrewAI".
- Keep the section concise and user-facing.
- Confidence must be one of: Limited, Low, Moderate, High.
""".strip()


def run_direct_ollama_training_report_section_spike(
    *,
    model: str,
    user_id: int,
    report_date: str,
    approved_context: dict[str, Any] | None = None,
    ollama_base_url: str | None = None,
    generate: DirectOllamaGenerateCallable = call_direct_ollama_generate,
    timeout_seconds: float = 600,
) -> DirectOllamaTrainingReportSectionSpikeResult:
    """Run one isolated direct Ollama structured-output training section spike."""

    configured_model = model.strip()
    selected_model = normalize_ollama_model_name(configured_model)
    resolved_base_url = (
        ollama_base_url
        or os.getenv(explanation_service.OLLAMA_BASE_URL_ENV)
        or DIRECT_OLLAMA_DEFAULT_BASE_URL
    )
    resolved_context = approved_context or build_training_report_section_context(
        user_id=user_id,
        report_date=report_date,
    )
    prompt = build_direct_ollama_training_report_section_prompt(resolved_context)

    start = time.perf_counter()
    raw_output: Any | None = None
    provider_error: str | None = None

    try:
        raw_output = generate(
            resolved_base_url,
            selected_model,
            prompt,
            CANDIDATE_TRAINING_REPORT_SECTION_JSON_SCHEMA,
            timeout_seconds,
        )
    except Exception as exc:
        provider_error = f"{type(exc).__name__}: {exc}"

    elapsed_seconds = round(time.perf_counter() - start, 3)

    if provider_error is not None:
        return _fallback_result(
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            validation_errors=[provider_error],
            approved_context=resolved_context,
        )

    if not isinstance(raw_output, str):
        return _fallback_result(
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            fallback_reason=FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT,
            validation_errors=["Provider returned a non-string response."],
            approved_context=resolved_context,
        )

    diagnostics = detect_direct_ollama_training_section_output_diagnostics(raw_output)

    try:
        payload = _parse_candidate_training_section_payload(raw_output)
    except Exception as exc:
        return _fallback_result(
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            fallback_reason=FALLBACK_REASON_CANDIDATE_PARSE_FAILURE,
            validation_errors=[str(exc)],
            approved_context=resolved_context,
            raw_output=raw_output,
            candidate_parse_status=TRAINING_SECTION_PARSE_STATUS_FAILED,
            diagnostics=diagnostics,
        )

    candidate = CandidateTrainingReportSection.from_payload(payload)
    validation_errors = validate_candidate_training_report_section(
        candidate,
        approved_context=resolved_context,
    )
    if validation_errors:
        return _fallback_result(
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            fallback_reason=FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE,
            validation_errors=validation_errors,
            approved_context=resolved_context,
            raw_output=raw_output,
            candidate_parse_status=TRAINING_SECTION_PARSE_STATUS_SUCCESS,
            candidate_validation_status=TRAINING_SECTION_VALIDATION_STATUS_FAILED,
            validation_status=TRAINING_SECTION_STATUS_REJECTED,
            diagnostics=diagnostics,
        )

    return DirectOllamaTrainingReportSectionSpikeResult(
        success=True,
        provider=DIRECT_OLLAMA_TRAINING_REPORT_SECTION_PROVIDER_NAME,
        section="training",
        configured_model=configured_model,
        selected_model=selected_model,
        user_id=user_id,
        report_date=report_date,
        ollama_base_url=resolved_base_url,
        elapsed_seconds=elapsed_seconds,
        provider_attempted=True,
        candidate_parse_status=TRAINING_SECTION_PARSE_STATUS_SUCCESS,
        candidate_validation_status=TRAINING_SECTION_VALIDATION_STATUS_SUCCESS,
        validation_status=TRAINING_SECTION_STATUS_APPROVED,
        candidate_valid=True,
        fallback_used=False,
        fallback_reason=None,
        final_section_source=FINAL_SECTION_SOURCE_PROVIDER_APPROVED,
        approved_section=candidate.to_dict(),
        validation_errors=[],
        approved_training_quote_context=_approved_training_quote_context_from_context(
            resolved_context
        ),
        **diagnostics,
    )


def validate_candidate_training_report_section(
    candidate: CandidateTrainingReportSection,
    *,
    approved_context: dict[str, Any],
) -> list[str]:
    """Validate a structured training section candidate against approved context."""

    errors: list[str] = []
    candidate_payload = candidate.to_dict()
    text_fields = _candidate_text_fields(candidate)
    combined_text = "\n".join(text_fields)
    lowered = combined_text.lower()

    for field_name in [
        "section_summary",
        "performance_interpretation",
        "fatigue_recovery_interpretation",
        "suggested_focus",
        "limitations_context",
    ]:
        value = getattr(candidate, field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string.")

    if not candidate.key_observations:
        errors.append("key_observations must include at least one observation.")
    if len(candidate.key_observations) > 5:
        errors.append("key_observations must not include more than five observations.")
    for observation in candidate.key_observations:
        if not isinstance(observation, str) or not observation.strip():
            errors.append("key_observations must contain non-empty strings.")
            break

    if candidate.confidence not in CONFIDENCE_VALUES:
        errors.append("confidence must be Limited, Low, Moderate, or High.")

    if not isinstance(candidate.reason_codes, list) or not all(
        isinstance(code, str) and code.strip() for code in candidate.reason_codes
    ):
        errors.append("reason_codes must contain non-empty strings.")

    for text in text_fields:
        if "```" in text:
            errors.append(
                "Training report section fields must not include markdown code fences."
            )
            break

    internal_terms = [
        "source of truth",
        "validator",
        "validation",
        "fallback",
        "debug",
        "provider",
        "ollama",
        "crewai",
    ]
    for term in internal_terms:
        if term in lowered:
            errors.append(
                f"Training report section must not expose internal term: {term}."
            )

    medical_patterns = [
        r"\bdiagnos(?:e|is|ed)\b",
        r"\btreat(?:s|ment|ed)?\b",
        r"\bcure(?:s|d)?\b",
        r"\bmedical\s+advice\b",
        r"\bdisease\b",
        r"\binjury\s+(?:treatment|diagnosis|protocol)\b",
    ]
    for pattern in medical_patterns:
        if re.search(pattern, combined_text, flags=re.IGNORECASE):
            errors.append("Training report section must not make medical claims.")
            break

    unsupported_recommendation_patterns = [
        r"\b(?:add|increase|raise|bump)\s+(?:the\s+)?(?:weight|load|sets|reps)\b",
        r"\b(?:start|begin)\s+(?:a\s+)?new\s+(?:program|workout|plan)\b",
        r"\btrain\s+through\s+(?:pain|injury)\b",
    ]
    for pattern in unsupported_recommendation_patterns:
        if re.search(pattern, combined_text, flags=re.IGNORECASE):
            errors.append(
                "Training report section must not create unsupported progression or workout prescriptions."
            )
            break

    approved_names = _approved_training_names_from_context(approved_context)
    if approved_names:
        if not _text_mentions_any_approved_name(combined_text, approved_names):
            errors.append(
                "Training report section must mention at least one approved workout or exercise name when detailed training context exists."
            )

        if _contains_generic_training_copy(lowered):
            errors.append(
                "Training report section must not use vague training copy when approved training details exist."
            )

        unapproved_known_names = _unapproved_known_training_names(
            combined_text,
            approved_names=approved_names,
        )
        if unapproved_known_names:
            errors.append(
                "Training report section mentions unapproved workout or exercise names: "
                + ", ".join(sorted(unapproved_known_names))
            )

    unsupported_claims = _unsupported_training_claim_errors(
        lowered, approved_context=approved_context
    )
    errors.extend(unsupported_claims)

    unapproved_numbers = _unapproved_numbers_in_candidate(
        candidate_payload,
        approved_context=approved_context,
    )
    if unapproved_numbers:
        errors.append(
            "Training report section contains numbers not present in approved context: "
            + ", ".join(sorted(unapproved_numbers))
        )

    return _unique(errors)


def detect_direct_ollama_training_section_output_diagnostics(
    raw_output: str,
) -> dict[str, Any]:
    stripped = raw_output.strip()
    parsed_payload: Any | None = None
    extra_keys: list[str] = []
    wrapper_object_detected = False

    try:
        parsed_payload = json.loads(stripped)
    except Exception:
        parsed_payload = None

    if isinstance(parsed_payload, dict):
        payload_keys = set(parsed_payload)
        extra_keys = sorted(
            payload_keys - CANDIDATE_TRAINING_REPORT_SECTION_ALLOWED_KEYS
        )
        wrapper_object_detected = any(
            key in payload_keys
            for key in {
                "section",
                "report_section",
                "training_section",
                "candidate",
                "candidate_training_report_section",
                "output",
                "response",
            }
        )

    return {
        "raw_output_length": len(raw_output),
        "raw_output_preview_truncated": raw_output[
            :DIRECT_OLLAMA_RESPONSE_PREVIEW_LIMIT
        ],
        "markdown_wrapper_detected": _detect_markdown_wrapper(stripped),
        "extra_keys_detected": extra_keys,
        "wrapper_object_detected": wrapper_object_detected,
    }


def _parse_candidate_training_section_payload(raw_output: str) -> dict[str, Any]:
    stripped = raw_output.strip()
    if not stripped:
        raise ValueError("Provider training section output was empty.")
    _reject_markdown_or_code_fence(stripped)
    payload = json.loads(stripped)
    if not isinstance(payload, dict):
        raise ValueError("Provider training section JSON must be an object.")

    payload_keys = set(payload)
    missing_keys = CANDIDATE_TRAINING_REPORT_SECTION_ALLOWED_KEYS - payload_keys
    if missing_keys:
        raise ValueError(
            "Provider training section JSON is missing required keys: "
            + ", ".join(sorted(missing_keys))
        )

    extra_keys = payload_keys - CANDIDATE_TRAINING_REPORT_SECTION_ALLOWED_KEYS
    if extra_keys:
        raise ValueError(
            "Provider training section JSON included unsupported keys: "
            + ", ".join(sorted(extra_keys))
        )

    if not isinstance(payload.get("key_observations"), list):
        raise ValueError("key_observations must be an array.")
    if not isinstance(payload.get("reason_codes"), list):
        raise ValueError("reason_codes must be an array.")
    for key in [
        "section_summary",
        "performance_interpretation",
        "fatigue_recovery_interpretation",
        "suggested_focus",
        "limitations_context",
        "confidence",
    ]:
        if not isinstance(payload.get(key), str):
            raise ValueError(f"{key} must be a string.")

    return payload


def _load_recent_training_execution_details(
    *,
    user_id: int,
    limit: int,
) -> list[dict[str, Any]]:
    ensure_workout_plan_persistence_tables()
    conn = get_connection()
    cursor = conn.cursor()

    rows = cursor.execute(
        """
        SELECT id, title, status, scenario, confidence, completed_at, selected_at, created_at
        FROM workout_plan_instances
        WHERE user_id = ?
          AND status = 'completed'
        ORDER BY COALESCE(completed_at, selected_at, created_at) DESC,
                 id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()

    details: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows, start=1):
        plan_instance_id = int(row["id"])
        planned_rows = cursor.execute(
            """
            SELECT name, sets, reps_min, reps_max, rir_min, rir_max
            FROM planned_workout_exercises
            WHERE workout_plan_instance_id = ?
            ORDER BY exercise_order, id
            LIMIT ?
            """,
            (plan_instance_id, MAX_PLANNED_EXERCISES_PER_WORKOUT),
        ).fetchall()

        execution_session = cursor.execute(
            """
            SELECT id
            FROM workout_execution_sessions
            WHERE workout_plan_instance_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (plan_instance_id,),
        ).fetchone()

        actual_rows = []
        if execution_session:
            actual_rows = cursor.execute(
                """
                SELECT exercise_name, set_number, planned_reps_min, planned_reps_max,
                       planned_rir_min, planned_rir_max, actual_reps, actual_weight,
                       actual_rir, completed, skipped
                FROM workout_execution_set_actuals
                WHERE workout_execution_session_id = ?
                ORDER BY planned_workout_exercise_id, set_number, id
                LIMIT ?
                """,
                (int(execution_session["id"]), MAX_ACTUAL_SETS_PER_WORKOUT),
            ).fetchall()

        details.append(
            _compact_dict(
                {
                    "recent_position": row_index,
                    "workout_title": row["title"],
                    "completed_at": row["completed_at"],
                    "scenario": row["scenario"],
                    "confidence": row["confidence"],
                    "planned_exercises": [
                        _compact_dict(
                            {
                                "exercise_name": planned_row["name"],
                                "planned_sets": planned_row["sets"],
                                "planned_reps_min": planned_row["reps_min"],
                                "planned_reps_max": planned_row["reps_max"],
                                "planned_rir_min": planned_row["rir_min"],
                                "planned_rir_max": planned_row["rir_max"],
                            }
                        )
                        for planned_row in planned_rows
                    ],
                    "actual_sets": [
                        _compact_dict(
                            {
                                "exercise_name": actual_row["exercise_name"],
                                "set_number": actual_row["set_number"],
                                "planned_reps_min": actual_row["planned_reps_min"],
                                "planned_reps_max": actual_row["planned_reps_max"],
                                "planned_rir_min": actual_row["planned_rir_min"],
                                "planned_rir_max": actual_row["planned_rir_max"],
                                "actual_reps": actual_row["actual_reps"],
                                "actual_weight": actual_row["actual_weight"],
                                "actual_rir": actual_row["actual_rir"],
                                "completed": bool(actual_row["completed"]),
                                "skipped": bool(actual_row["skipped"]),
                            }
                        )
                        for actual_row in actual_rows
                    ],
                }
            )
        )

    conn.close()
    return details


def _reject_markdown_or_code_fence(text: str) -> None:
    if re.fullmatch(r"```(?:json)?\s*.*?\s*```", text, flags=re.DOTALL):
        raise ValueError(
            "Provider training section output must be raw JSON without markdown or code fences."
        )
    if text.startswith("```") or text.endswith("```"):
        raise ValueError(
            "Provider training section output must not include markdown code fences."
        )


def _detect_markdown_wrapper(text: str) -> bool:
    return bool(
        re.fullmatch(r"```(?:json)?\s*.*?\s*```", text, flags=re.DOTALL)
        or text.startswith("```")
        or text.endswith("```")
    )


def _fallback_result(
    *,
    configured_model: str,
    selected_model: str,
    user_id: int,
    report_date: str,
    ollama_base_url: str,
    elapsed_seconds: float,
    fallback_reason: str,
    validation_errors: list[str],
    approved_context: dict[str, Any] | None = None,
    raw_output: str | None = None,
    candidate_parse_status: str = TRAINING_SECTION_PARSE_STATUS_NOT_ATTEMPTED,
    candidate_validation_status: str = TRAINING_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED,
    validation_status: str = TRAINING_SECTION_STATUS_NOT_ATTEMPTED,
    diagnostics: dict[str, Any] | None = None,
) -> DirectOllamaTrainingReportSectionSpikeResult:
    if diagnostics is None:
        diagnostics = (
            detect_direct_ollama_training_section_output_diagnostics(raw_output)
            if isinstance(raw_output, str)
            else {
                "raw_output_length": None,
                "raw_output_preview_truncated": None,
                "markdown_wrapper_detected": False,
                "extra_keys_detected": [],
                "wrapper_object_detected": False,
            }
        )

    return DirectOllamaTrainingReportSectionSpikeResult(
        success=False,
        provider=DIRECT_OLLAMA_TRAINING_REPORT_SECTION_PROVIDER_NAME,
        section="training",
        configured_model=configured_model,
        selected_model=selected_model,
        user_id=user_id,
        report_date=report_date,
        ollama_base_url=ollama_base_url,
        elapsed_seconds=elapsed_seconds,
        provider_attempted=True,
        candidate_parse_status=candidate_parse_status,
        candidate_validation_status=candidate_validation_status,
        validation_status=validation_status,
        candidate_valid=False,
        fallback_used=True,
        fallback_reason=fallback_reason,
        final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
        approved_section=_deterministic_fallback_section().to_dict(),
        validation_errors=validation_errors,
        approved_training_quote_context=_approved_training_quote_context_from_context(
            approved_context
        ),
        **diagnostics,
    )


def _approved_training_quote_context_from_context(
    approved_context: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(approved_context, dict):
        return {}
    quote_context = approved_context.get("approved_training_quote_context")
    return quote_context if isinstance(quote_context, dict) else {}


def _deterministic_fallback_section() -> CandidateTrainingReportSection:
    return CandidateTrainingReportSection(
        section_summary="Training context is available from backend-approved workout execution data.",
        key_observations=[
            "Workout execution summaries remain backend-owned and should be interpreted conservatively."
        ],
        performance_interpretation=(
            "Use the approved training summary to review completion, effort, and logging quality."
        ),
        fatigue_recovery_interpretation=(
            "Recovery and fatigue context should stay bounded by logged readiness and execution data."
        ),
        suggested_focus="Keep workout logging consistent before changing training direction.",
        limitations_context=(
            "This deterministic fallback does not add AI-generated training claims."
        ),
        confidence="Limited",
        reason_codes=["deterministic_training_report_section_fallback"],
    )


def _candidate_training_report_section_example() -> dict[str, Any]:
    return {
        "section_summary": "Recent training execution has enough logged detail for cautious review.",
        "key_observations": [
            "Completed planned workout data can support a bounded training summary.",
            "Effort and completion should be interpreted only from approved execution details.",
        ],
        "performance_interpretation": (
            "The main training signal is consistency rather than a dramatic change."
        ),
        "fatigue_recovery_interpretation": (
            "Recovery context should be considered before changing training difficulty."
        ),
        "suggested_focus": "Review approved planned-vs-actual execution details before adjusting training.",
        "limitations_context": "This section only uses approved backend training context.",
        "confidence": "Moderate",
        "reason_codes": ["direct_ollama_training_report_section_candidate"],
    }


def _candidate_text_fields(candidate: CandidateTrainingReportSection) -> list[str]:
    return [
        candidate.section_summary,
        *candidate.key_observations,
        candidate.performance_interpretation,
        candidate.fatigue_recovery_interpretation,
        candidate.suggested_focus,
        candidate.limitations_context,
    ]


def _approved_training_names_from_context(approved_context: dict[str, Any]) -> set[str]:
    quote_context = _approved_training_quote_context_from_context(approved_context)
    names: set[str] = set()
    for key in ("approved_workout_names", "approved_exercise_names"):
        for value in quote_context.get(key, []):
            if isinstance(value, str):
                normalized = _normalize_name(value)
                if normalized:
                    names.add(normalized)
    return names


def _text_mentions_any_approved_name(text: str, approved_names: set[str]) -> bool:
    normalized_text = _normalize_name(text)
    return any(name in normalized_text for name in approved_names)


def _contains_generic_training_copy(lowered_text: str) -> bool:
    generic_phrases = [
        "training data is available",
        "workout data is available",
        "use the approved training data",
        "use the approved workout data",
        "training details are available",
        "workout details are available",
        "review the approved training context",
        "training load remains moderate",
        "training has been consistent",
        "volume appears balanced",
        "performance is stable",
        "continue gradual progression",
        "consistent volume",
    ]
    return any(phrase in lowered_text for phrase in generic_phrases)


def _unapproved_known_training_names(
    text: str,
    *,
    approved_names: set[str],
) -> set[str]:
    normalized_text = _normalize_name(text)
    known_names = {
        "barbell deadlift",
        "deadlift",
        "back squat",
        "front squat",
        "bench press",
        "overhead press",
        "barbell row",
        "lat pulldown",
        "leg press",
        "romanian deadlift",
        "power clean",
        "clean and jerk",
        "snatch",
    }
    unapproved: set[str] = set()
    for known_name in known_names:
        if known_name not in normalized_text:
            continue
        if any(known_name in approved_name for approved_name in approved_names):
            continue
        unapproved.add(known_name)
    return unapproved


def _unsupported_training_claim_errors(
    lowered_text: str,
    *,
    approved_context: dict[str, Any],
) -> list[str]:
    quote_context = _approved_training_quote_context_from_context(approved_context)
    approved_facts_text = "\n".join(
        str(fact).lower()
        for fact in quote_context.get("approved_training_summary_facts", [])
    )
    errors: list[str] = []

    unsupported_claim_groups = [
        (
            "Training report section must not invent volume-load claims.",
            ["volume load", "total volume", "training volume increased"],
        ),
        (
            "Training report section must not invent average RIR claims.",
            ["average rir", "avg rir", "average effort was rir"],
        ),
        (
            "Training report section must not invent percentage/progression claims.",
            [
                "%",
                " percent",
                "progression is trending",
                "strength is improving",
                "load increased",
                "week over week",
                "performance improved",
            ],
        ),
        (
            "Training report section must not invent fatigue or recovery conclusions.",
            [
                "fatigue is accumulating",
                "recovery is compromised",
                "training stress is excessive",
                "high fatigue",
                "low fatigue risk",
                "high readiness",
            ],
        ),
    ]
    for message, phrases in unsupported_claim_groups:
        if any(phrase in lowered_text for phrase in phrases) and not any(
            phrase in approved_facts_text for phrase in phrases
        ):
            errors.append(message)

    return errors


def _unapproved_numbers_in_candidate(
    candidate_payload: dict[str, Any],
    *,
    approved_context: dict[str, Any],
) -> set[str]:
    quote_context = _approved_training_quote_context_from_context(approved_context)
    allowed_numbers = _number_tokens_from_object(
        {
            "approved_training_numbers": quote_context.get(
                "approved_training_numbers", []
            ),
            "approved_set_rep_load_rir_values": quote_context.get(
                "approved_set_rep_load_rir_values", []
            ),
            "approved_training_summary_facts": quote_context.get(
                "approved_training_summary_facts", []
            ),
        }
    )
    found_numbers = _number_tokens_from_object(candidate_payload)
    return {number for number in found_numbers if number not in allowed_numbers}


def _number_tokens_from_object(value: Any) -> set[str]:
    tokens: set[str] = set()
    for item in _walk_values(value):
        if isinstance(item, bool):
            continue
        if isinstance(item, int | float):
            tokens.update(_number_text_variants(float(item)))
        elif isinstance(item, str):
            for match in re.findall(r"(?<![A-Za-z])-?\d+(?:\.\d+)?(?![A-Za-z])", item):
                tokens.update(_number_text_variants(float(match)))
    return tokens


def _number_text_variants(value: float) -> set[str]:
    variants = {str(value)}
    if value.is_integer():
        variants.add(str(int(value)))
        variants.add(f"{value:.1f}")
    else:
        variants.add(f"{value:.1f}".rstrip("0").rstrip("."))
        variants.add(f"{value:.2f}".rstrip("0").rstrip("."))
    return variants


def _walk_values(value: Any):
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_values(child)
    elif isinstance(value, list | tuple | set):
        for child in value:
            yield from _walk_values(child)
    else:
        yield value


def _walk_key_values(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk_key_values(child)
    elif isinstance(value, list | tuple | set):
        for child in value:
            yield from _walk_key_values(child)


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _safe_nonempty_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _append_unique_string(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _append_unique_number(values: list[int | float], value: Any) -> None:
    if isinstance(value, bool):
        return
    if not isinstance(value, int | float):
        return
    number: int | float = int(value) if float(value).is_integer() else float(value)
    if number not in values:
        values.append(number)


def _extend_approved_numbers(values: list[int | float], candidates: list[Any]) -> None:
    for candidate in candidates:
        _append_unique_number(values, candidate)


def _format_range(min_value: Any, max_value: Any) -> str | None:
    if min_value is None and max_value is None:
        return None
    if min_value is None:
        return _format_number(max_value)
    if max_value is None or min_value == max_value:
        return _format_number(min_value)
    return f"{_format_number(min_value)}-{_format_number(max_value)}"


def _single_distinct_number(values: list[Any]) -> int | float | None:
    normalized: list[int | float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int | float):
            continue
        number: int | float = int(value) if float(value).is_integer() else float(value)
        if number not in normalized:
            normalized.append(number)
    if len(normalized) == 1:
        return normalized[0]
    return None


def _format_number(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        return ""
    if isinstance(value, int | float) and float(value).is_integer():
        return str(int(value))
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if value == [] or value == {}:
            continue
        compact[key] = value
    return compact


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Direct Ollama structured-output training report section spike."
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--date", required=True, dest="report_date")
    parser.add_argument("--ollama-base-url", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=600)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = run_direct_ollama_training_report_section_spike(
        model=args.model,
        user_id=args.user_id,
        report_date=args.report_date,
        ollama_base_url=args.ollama_base_url,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
