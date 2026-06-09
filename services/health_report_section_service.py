from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable
from typing import Any

from models.health_report_section_models import (
    ApprovedHealthReportSection,
    ApprovedHealthReportSectionResult,
    CandidateHealthReportSection,
    HealthReportSectionRuntimeMetadata,
)
from services import ai_nutrition_explanation_service as explanation_service
from services.coaching_decision_service import build_coaching_decision
from services.user_state_service import build_user_health_state

HEALTH_REPORT_SECTION_PROVIDER_ENV = "HEALTH_REPORT_SECTION_PROVIDER"
HEALTH_REPORT_SECTION_MODEL_ENV = "HEALTH_REPORT_SECTION_MODEL"
HEALTH_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_ENV = (
    "HEALTH_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS"
)

HEALTH_REPORT_SECTION_PROVIDER_DETERMINISTIC = "deterministic"
HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA = "direct_ollama"
HEALTH_REPORT_SECTION_DEFAULT_MODEL = "ollama/qwen2.5:3b"
HEALTH_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS = 60.0
HEALTH_REPORT_SECTION_RAW_OUTPUT_PREVIEW_LIMIT = 500

REPORT_SECTION_PARSE_STATUS_NOT_ATTEMPTED = "not_attempted"
REPORT_SECTION_PARSE_STATUS_SUCCESS = "success"
REPORT_SECTION_PARSE_STATUS_FAILED = "failed"

REPORT_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED = "not_attempted"
REPORT_SECTION_VALIDATION_STATUS_SUCCESS = "success"
REPORT_SECTION_VALIDATION_STATUS_FAILED = "failed"

REPORT_SECTION_STATUS_NOT_ATTEMPTED = "not_attempted"
REPORT_SECTION_STATUS_APPROVED = "approved"
REPORT_SECTION_STATUS_REJECTED = "rejected"

FINAL_SECTION_SOURCE_DETERMINISTIC = "deterministic"
FINAL_SECTION_SOURCE_PROVIDER_APPROVED = "provider_approved"
FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"

FALLBACK_REASON_DETERMINISTIC_SELECTED = "deterministic_provider_selected"
FALLBACK_REASON_INVALID_PROVIDER = "invalid_provider"
FALLBACK_REASON_PROVIDER_EXCEPTION = "provider_exception"
FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT = "provider_non_string_output"
FALLBACK_REASON_CANDIDATE_PARSE_FAILURE = "candidate_parse_failure"
FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE = "candidate_validation_failure"

CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

CANDIDATE_HEALTH_REPORT_SECTION_ALLOWED_KEYS = {
    "section_summary",
    "key_observations",
    "coaching_interpretation",
    "suggested_focus",
    "limitations_context",
    "confidence",
    "reason_codes",
}

CANDIDATE_HEALTH_REPORT_SECTION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "section_summary",
        "key_observations",
        "coaching_interpretation",
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
        "coaching_interpretation": {"type": "string"},
        "suggested_focus": {"type": "string"},
        "limitations_context": {"type": "string"},
        "confidence": {
            "type": "string",
            "enum": ["Limited", "Low", "Moderate", "High"],
        },
        "reason_codes": {"type": "array", "items": {"type": "string"}},
    },
}

DirectOllamaGenerateCallable = Callable[[str, str, str, dict[str, Any], float], str]
normalize_ollama_model_name = explanation_service.normalize_ollama_model_name
call_direct_ollama_generate = explanation_service.call_direct_ollama_generate
DirectOllamaProviderError = explanation_service.DirectOllamaProviderError


def build_nutrition_health_report_section_context(
    *,
    user_id: int,
    report_date: str,
) -> dict[str, Any]:
    """Build bounded backend-approved context for the nutrition report section."""

    health_state = build_user_health_state(user_id)
    coaching_decision = build_coaching_decision(health_state)
    nutrition_context = explanation_service.build_nutrition_explanation_context(
        user_id,
        report_date,
    )
    compressed_nutrition_context = (
        explanation_service._compressed_provider_context_projection(nutrition_context)
    )

    return _compact_dict(
        {
            "section": "nutrition",
            "user_id": user_id,
            "report_date": report_date,
            "coaching_decision": _compact_dict(
                {
                    "scenario": getattr(coaching_decision, "scenario", None),
                    "primary_focus": getattr(coaching_decision, "primary_focus", None),
                    "nutrition_action": getattr(
                        coaching_decision,
                        "nutrition_action",
                        None,
                    ),
                    "confidence": getattr(coaching_decision, "confidence", None),
                }
            ),
            "approved_nutrition_context": compressed_nutrition_context,
        }
    )


def build_direct_ollama_health_report_section_prompt(
    approved_context: dict[str, Any],
    *,
    section: str = "nutrition",
) -> str:
    """Build the strict direct Ollama prompt for one report section."""

    approved_context_json = json.dumps(approved_context, sort_keys=True, default=str)
    valid_example_json = json.dumps(_candidate_health_report_section_example())
    return f"""
/no_think
Task: write one concise {section} report section from approved backend context.

Strict output rules:
- Return JSON only: one raw JSON object and nothing else.
- Do not include markdown.
- Do not include code fences.
- Do not include comments.
- Do not include prose outside JSON.
- The first character must be {{ and the last character must be }}.
- Include exactly these top-level keys and no others.
- Do not include dates unless the schema explicitly requires them.
- Do not include provider fields, runtime fields, debug fields, validation fields, or raw context keys.
- Do not copy backend context keys into the output unless they are explicitly listed in the schema.
- Quote numbers only when those exact values appear in the approved context.
- Mention foods only when they appear in approved food suggestion candidates.
- Do not invent targets, logged values, macro gaps, foods, serving sizes, workouts, recovery metrics, or health metrics.
- Do not calculate or mutate targets.
- Do not create meal plans, recipes, grocery lists, workout plans, or medical guidance.

CandidateHealthReportSection allowed output schema:
{{
  "section_summary": "string",
  "key_observations": ["string"],
  "coaching_interpretation": "string",
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
- Do not claim calibration changed targets.
- Do not say targets were adjusted, updated, or mutated.
- Do not invent exact calorie, protein, carbohydrate, or fat values.
- Do not invent food suggestions, servings, or macros.
- Do not use phrases such as "source of truth", "validator", "fallback", "debug", "provider", "Ollama", or "CrewAI".
- Keep the section concise and user-facing.
- Confidence must be one of: Limited, Low, Moderate, High.
""".strip()


def build_configured_nutrition_health_report_section_with_metadata(
    *,
    user_id: int,
    report_date: str,
    approved_context: dict[str, Any] | None = None,
    direct_ollama_generate: DirectOllamaGenerateCallable | None = None,
) -> ApprovedHealthReportSectionResult:
    """Build an approved nutrition report section using configured provider settings.

    Deterministic remains the default. Direct Ollama is opt-in and remains bounded
    by strict parsing, validation, and deterministic fallback.
    """

    configured_provider = _configured_health_report_section_provider()
    resolved_context = (
        approved_context
        or build_nutrition_health_report_section_context(
            user_id=user_id,
            report_date=report_date,
        )
    )

    if configured_provider == HEALTH_REPORT_SECTION_PROVIDER_DETERMINISTIC:
        metadata = _runtime_metadata(
            configured_provider=configured_provider,
            selected_provider=HEALTH_REPORT_SECTION_PROVIDER_DETERMINISTIC,
            configured_model=HEALTH_REPORT_SECTION_PROVIDER_DETERMINISTIC,
            selected_model=HEALTH_REPORT_SECTION_PROVIDER_DETERMINISTIC,
            provider_attempted=False,
            fallback_used=False,
            fallback_reason=FALLBACK_REASON_DETERMINISTIC_SELECTED,
            candidate_valid=True,
            validation_errors=[],
            candidate_parse_status=REPORT_SECTION_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=REPORT_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=REPORT_SECTION_STATUS_NOT_ATTEMPTED,
            final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC,
        )
        return _deterministic_result(
            approved_context=resolved_context,
            metadata=metadata,
            source=FINAL_SECTION_SOURCE_DETERMINISTIC,
        )

    if configured_provider == HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA:
        return approve_direct_ollama_nutrition_health_report_section_or_fallback(
            approved_context=resolved_context,
            user_id=user_id,
            report_date=report_date,
            generate=direct_ollama_generate or call_direct_ollama_generate,
        )

    metadata = _runtime_metadata(
        configured_provider=configured_provider,
        selected_provider=HEALTH_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        configured_model=HEALTH_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        selected_model=HEALTH_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        provider_attempted=False,
        fallback_used=True,
        fallback_reason=FALLBACK_REASON_INVALID_PROVIDER,
        candidate_valid=True,
        validation_errors=[f"Unsupported provider: {configured_provider}"],
        candidate_parse_status=REPORT_SECTION_PARSE_STATUS_NOT_ATTEMPTED,
        candidate_validation_status=REPORT_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED,
        validation_status=REPORT_SECTION_STATUS_NOT_ATTEMPTED,
        final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
    )
    return _deterministic_result(
        approved_context=resolved_context,
        metadata=metadata,
        source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
    )


def build_configured_nutrition_health_report_section(
    *,
    user_id: int,
    report_date: str,
) -> ApprovedHealthReportSection:
    """Return only the public approved nutrition report section."""

    return build_configured_nutrition_health_report_section_with_metadata(
        user_id=user_id,
        report_date=report_date,
    ).approved_section


def approve_direct_ollama_nutrition_health_report_section_or_fallback(
    *,
    approved_context: dict[str, Any],
    user_id: int,
    report_date: str,
    generate: DirectOllamaGenerateCallable = call_direct_ollama_generate,
) -> ApprovedHealthReportSectionResult:
    configured_model = _configured_health_report_section_model()
    selected_model = normalize_ollama_model_name(configured_model)
    base_url = os.getenv(
        explanation_service.OLLAMA_BASE_URL_ENV,
        explanation_service.NUTRITION_EXPLANATION_DEFAULT_BASE_URL,
    )
    timeout_seconds = _configured_direct_ollama_timeout_seconds()
    prompt = build_direct_ollama_health_report_section_prompt(
        approved_context,
        section="nutrition",
    )

    start = time.perf_counter()
    raw_output: Any | None = None
    try:
        raw_output = generate(
            base_url,
            selected_model,
            prompt,
            CANDIDATE_HEALTH_REPORT_SECTION_JSON_SCHEMA,
            timeout_seconds,
        )
    except DirectOllamaProviderError as exc:
        elapsed_seconds = round(time.perf_counter() - start, 3)
        metadata = _runtime_metadata(
            configured_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
            selected_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=True,
            fallback_used=True,
            fallback_reason=exc.fallback_reason,
            candidate_valid=False,
            validation_errors=[str(exc)],
            candidate_parse_status=REPORT_SECTION_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=REPORT_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=REPORT_SECTION_STATUS_NOT_ATTEMPTED,
            final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
            elapsed_seconds=elapsed_seconds,
        )
        return _deterministic_result(
            approved_context=approved_context,
            metadata=metadata,
            source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
        )
    except Exception as exc:
        elapsed_seconds = round(time.perf_counter() - start, 3)
        metadata = _runtime_metadata(
            configured_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
            selected_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            candidate_valid=False,
            validation_errors=[f"{type(exc).__name__}: {exc}"],
            candidate_parse_status=REPORT_SECTION_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=REPORT_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=REPORT_SECTION_STATUS_NOT_ATTEMPTED,
            final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
            elapsed_seconds=elapsed_seconds,
        )
        return _deterministic_result(
            approved_context=approved_context,
            metadata=metadata,
            source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
        )

    elapsed_seconds = round(time.perf_counter() - start, 3)

    if not isinstance(raw_output, str):
        metadata = _runtime_metadata(
            configured_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
            selected_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT,
            candidate_valid=False,
            validation_errors=["Provider returned a non-string response."],
            candidate_parse_status=REPORT_SECTION_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=REPORT_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=REPORT_SECTION_STATUS_NOT_ATTEMPTED,
            final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
            elapsed_seconds=elapsed_seconds,
        )
        return _deterministic_result(
            approved_context=approved_context,
            metadata=metadata,
            source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
        )

    diagnostics = detect_direct_ollama_section_output_diagnostics(raw_output)

    try:
        payload = parse_candidate_health_report_section_payload(raw_output)
    except Exception as exc:
        metadata = _runtime_metadata(
            configured_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
            selected_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_CANDIDATE_PARSE_FAILURE,
            candidate_valid=False,
            validation_errors=[str(exc)],
            candidate_parse_status=REPORT_SECTION_PARSE_STATUS_FAILED,
            candidate_validation_status=REPORT_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=REPORT_SECTION_STATUS_NOT_ATTEMPTED,
            final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
            elapsed_seconds=elapsed_seconds,
            **diagnostics,
        )
        return _deterministic_result(
            approved_context=approved_context,
            metadata=metadata,
            source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
        )

    candidate = CandidateHealthReportSection.from_payload(payload)
    validation_errors = validate_candidate_health_report_section(
        candidate,
        approved_context=approved_context,
    )
    if validation_errors:
        metadata = _runtime_metadata(
            configured_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
            selected_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE,
            candidate_valid=False,
            validation_errors=validation_errors,
            candidate_parse_status=REPORT_SECTION_PARSE_STATUS_SUCCESS,
            candidate_validation_status=REPORT_SECTION_VALIDATION_STATUS_FAILED,
            validation_status=REPORT_SECTION_STATUS_REJECTED,
            final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
            elapsed_seconds=elapsed_seconds,
            **diagnostics,
        )
        return _deterministic_result(
            approved_context=approved_context,
            metadata=metadata,
            source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
        )

    approved_section = ApprovedHealthReportSection.from_candidate(
        candidate,
        section="nutrition",
        source=FINAL_SECTION_SOURCE_PROVIDER_APPROVED,
    )
    metadata = _runtime_metadata(
        configured_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
        selected_provider=HEALTH_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
        configured_model=configured_model,
        selected_model=selected_model,
        provider_attempted=True,
        fallback_used=False,
        fallback_reason=None,
        candidate_valid=True,
        validation_errors=[],
        candidate_parse_status=REPORT_SECTION_PARSE_STATUS_SUCCESS,
        candidate_validation_status=REPORT_SECTION_VALIDATION_STATUS_SUCCESS,
        validation_status=REPORT_SECTION_STATUS_APPROVED,
        final_section_source=FINAL_SECTION_SOURCE_PROVIDER_APPROVED,
        elapsed_seconds=elapsed_seconds,
        **diagnostics,
    )
    return ApprovedHealthReportSectionResult(
        approved_section=approved_section,
        runtime_metadata=metadata,
    )


def parse_candidate_health_report_section_payload(raw_output: str) -> dict[str, Any]:
    stripped = raw_output.strip()
    if not stripped:
        raise ValueError("Provider section output was empty.")
    _reject_markdown_or_code_fences(stripped)
    if not stripped.startswith("{") or not stripped.endswith("}"):
        raise ValueError("Provider section output must be one raw JSON object.")

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Provider section output was not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Provider section output must be a JSON object.")

    _reject_wrapper_object(payload)
    _reject_extra_or_missing_keys(payload)
    _reject_invalid_payload_types(payload)
    return payload


def validate_candidate_health_report_section(
    candidate: CandidateHealthReportSection,
    *,
    approved_context: dict[str, Any],
) -> list[str]:
    """Validate a structured report section candidate against approved context."""

    errors: list[str] = []
    candidate_payload = candidate.to_dict()
    text_fields = _candidate_text_fields(candidate)
    combined_text = "\n".join(text_fields)

    for field_name in [
        "section_summary",
        "coaching_interpretation",
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
                "Report section fields must not include markdown code fences."
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
    lowered = combined_text.lower()
    for term in internal_terms:
        if term in lowered:
            errors.append(f"Report section must not expose internal term: {term}.")

    medical_patterns = [
        r"\bdiagnos(?:e|is|ed)\b",
        r"\btreat(?:s|ment|ed)?\b",
        r"\bcure(?:s|d)?\b",
        r"\bmedical\s+advice\b",
        r"\bdisease\b",
    ]
    for pattern in medical_patterns:
        if re.search(pattern, combined_text, flags=re.IGNORECASE):
            errors.append("Report section must not make medical claims.")
            break

    mutation_patterns = [
        r"\btargets?\s+(?:were|was|are|is)\s+(?:changed|adjusted|updated|modified|mutated)\b",
        r"\bcalibration\s+(?:changed|adjusted|updated|modified|mutated|applied)\b",
        r"\bI\s+(?:changed|adjusted|updated|modified)\s+(?:your\s+)?targets?\b",
    ]
    for pattern in mutation_patterns:
        if re.search(pattern, combined_text, flags=re.IGNORECASE):
            errors.append(
                "Report section must not claim target mutation or calibration."
            )
            break

    vague_patterns = [
        r"\bapproved\s+(?:context|data|information)\s+is\s+available\b",
        r"\bnutrition\s+context\s+is\s+available\b",
        r"\buse\s+the\s+approved\s+context\b",
    ]
    if _has_specific_approved_nutrition_context(approved_context):
        for pattern in vague_patterns:
            if re.search(pattern, combined_text, flags=re.IGNORECASE):
                errors.append(
                    "Report section must use specific approved nutrition context when available."
                )
                break

    unapproved_numbers = _unapproved_numbers_in_candidate(
        candidate_payload,
        approved_context=approved_context,
    )
    if unapproved_numbers:
        errors.append(
            "Report section contains numbers not present in approved context: "
            + ", ".join(sorted(unapproved_numbers))
        )

    return _unique(errors)


def detect_direct_ollama_section_output_diagnostics(raw_output: str) -> dict[str, Any]:
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
        extra_keys = sorted(payload_keys - CANDIDATE_HEALTH_REPORT_SECTION_ALLOWED_KEYS)
        wrapper_object_detected = any(
            key in payload_keys
            for key in {
                "section",
                "report_section",
                "candidate",
                "candidate_health_report_section",
                "output",
                "response",
            }
        )

    return {
        "raw_output_length": len(raw_output),
        "raw_output_preview_truncated": raw_output[
            :HEALTH_REPORT_SECTION_RAW_OUTPUT_PREVIEW_LIMIT
        ],
        "markdown_wrapper_detected": _detect_markdown_wrapper(stripped),
        "extra_keys_detected": extra_keys,
        "wrapper_object_detected": wrapper_object_detected,
    }


def _configured_health_report_section_provider() -> str:
    return os.getenv(
        HEALTH_REPORT_SECTION_PROVIDER_ENV,
        HEALTH_REPORT_SECTION_PROVIDER_DETERMINISTIC,
    ).strip()


def _configured_health_report_section_model() -> str:
    return os.getenv(
        HEALTH_REPORT_SECTION_MODEL_ENV, HEALTH_REPORT_SECTION_DEFAULT_MODEL
    )


def _configured_direct_ollama_timeout_seconds() -> float:
    raw = os.getenv(HEALTH_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_ENV)
    if not raw:
        return HEALTH_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        return HEALTH_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS
    return value if value > 0 else HEALTH_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS


def _runtime_metadata(**kwargs: Any) -> HealthReportSectionRuntimeMetadata:
    return HealthReportSectionRuntimeMetadata(**kwargs)


def _deterministic_result(
    *,
    approved_context: dict[str, Any],
    metadata: HealthReportSectionRuntimeMetadata,
    source: str,
) -> ApprovedHealthReportSectionResult:
    return ApprovedHealthReportSectionResult(
        approved_section=build_deterministic_nutrition_health_report_section(
            approved_context,
            source=source,
        ),
        runtime_metadata=metadata,
    )


def build_deterministic_nutrition_health_report_section(
    approved_context: dict[str, Any],
    *,
    source: str = FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
) -> ApprovedHealthReportSection:
    nutrition_context = approved_context.get("approved_nutrition_context") or {}
    value_context = nutrition_context.get("value_aware_context") or {}
    macro_statuses = value_context.get("macro_statuses") or {}
    food_candidates = value_context.get("approved_food_suggestion_candidates") or []
    confidence = str(nutrition_context.get("confidence") or "Limited")
    if confidence not in CONFIDENCE_VALUES:
        confidence = "Limited"

    protein_status = macro_statuses.get("protein") or macro_statuses.get("protein_g")
    calorie_status = macro_statuses.get("calories") or macro_statuses.get("calorie")

    observations: list[str] = []
    if protein_status:
        observations.append(f"Protein status is {protein_status} based on logged data.")
    if calorie_status:
        observations.append(f"Calorie status is {calorie_status} based on logged data.")
    if food_candidates:
        first_candidate = food_candidates[0]
        display_name = first_candidate.get("display_name")
        if display_name:
            observations.append(
                f"{display_name} is an approved food suggestion option."
            )
    if not observations:
        observations.append("Nutrition context is limited for this section.")

    return ApprovedHealthReportSection(
        section="nutrition",
        section_summary="Nutrition should be reviewed against approved logged data and target context.",
        key_observations=observations[:5],
        coaching_interpretation=(
            "Use the approved nutrition targets, logged actuals, and food suggestion "
            "context without making unsupported conclusions."
        ),
        suggested_focus=(
            "Keep nutrition logging complete and use approved Nutrition tab suggestions "
            "when a supported macro gap exists."
        ),
        limitations_context=(
            "This section is limited to backend-approved nutrition context and is not "
            "medical nutrition advice."
        ),
        confidence=confidence,
        reason_codes=[
            "deterministic_nutrition_report_section",
            "backend_approved_context_only",
        ],
        source=source,
    )


def _reject_markdown_or_code_fences(stripped_output: str) -> None:
    if _detect_markdown_wrapper(stripped_output):
        raise ValueError("Provider section output must not be markdown wrapped.")
    if "```" in stripped_output:
        raise ValueError("Provider section output must not contain code fences.")


def _detect_markdown_wrapper(stripped_output: str) -> bool:
    lowered = stripped_output.lower()
    return lowered.startswith("```json") or lowered.startswith("```")


def _reject_wrapper_object(payload: dict[str, Any]) -> None:
    wrapper_keys = {
        "section",
        "report_section",
        "candidate",
        "candidate_health_report_section",
        "output",
        "response",
    }
    present = sorted(set(payload).intersection(wrapper_keys))
    if present:
        raise ValueError(
            "Provider section output used a wrapper object: " + ", ".join(present)
        )


def _reject_extra_or_missing_keys(payload: dict[str, Any]) -> None:
    keys = set(payload)
    extra = sorted(keys - CANDIDATE_HEALTH_REPORT_SECTION_ALLOWED_KEYS)
    missing = sorted(CANDIDATE_HEALTH_REPORT_SECTION_ALLOWED_KEYS - keys)
    if extra:
        raise ValueError(
            "Provider section output included unsupported keys: " + ", ".join(extra)
        )
    if missing:
        raise ValueError(
            "Provider section output is missing required keys: " + ", ".join(missing)
        )


def _reject_invalid_payload_types(payload: dict[str, Any]) -> None:
    for key in [
        "section_summary",
        "coaching_interpretation",
        "suggested_focus",
        "limitations_context",
        "confidence",
    ]:
        if not isinstance(payload.get(key), str):
            raise ValueError(f"Provider section output field {key} must be a string.")
    observations = payload.get("key_observations")
    if not isinstance(observations, list) or not all(
        isinstance(item, str) for item in observations
    ):
        raise ValueError("Provider section output key_observations must be strings.")
    reason_codes = payload.get("reason_codes")
    if not isinstance(reason_codes, list) or not all(
        isinstance(item, str) for item in reason_codes
    ):
        raise ValueError("Provider section output reason_codes must be strings.")


def _candidate_text_fields(candidate: CandidateHealthReportSection) -> list[str]:
    return [
        candidate.section_summary,
        *candidate.key_observations,
        candidate.coaching_interpretation,
        candidate.suggested_focus,
        candidate.limitations_context,
    ]


def _candidate_health_report_section_example() -> dict[str, Any]:
    return {
        "section_summary": "Nutrition logging is complete enough to review today.",
        "key_observations": [
            "Protein is below target based on logged meals.",
            "Approved food suggestions are available in the Nutrition tab.",
        ],
        "coaching_interpretation": (
            "Nutrition support should be matched to training demand while keeping "
            "logging complete."
        ),
        "suggested_focus": "Use approved food suggestions to support the current macro gap.",
        "limitations_context": "Targets remain coaching estimates, not medical advice.",
        "confidence": "Moderate",
        "reason_codes": ["direct_ollama_report_section_candidate"],
    }


def _has_specific_approved_nutrition_context(approved_context: dict[str, Any]) -> bool:
    nutrition_context = approved_context.get("approved_nutrition_context") or {}
    value_context = nutrition_context.get("value_aware_context") or {}
    return bool(
        value_context.get("macro_statuses")
        or value_context.get("logged_actuals")
        or value_context.get("approved_food_suggestion_candidates")
        or value_context.get("display_targets")
    )


def _unapproved_numbers_in_candidate(
    candidate_payload: dict[str, Any],
    *,
    approved_context: dict[str, Any],
) -> set[str]:
    approved_numbers = _numbers_in_obj(approved_context)
    candidate_numbers = _numbers_in_obj(candidate_payload)
    return {number for number in candidate_numbers if number not in approved_numbers}


def _numbers_in_obj(value: Any) -> set[str]:
    numbers: set[str] = set()
    if isinstance(value, dict):
        for nested in value.values():
            numbers.update(_numbers_in_obj(nested))
        return numbers
    if isinstance(value, list | tuple | set):
        for nested in value:
            numbers.update(_numbers_in_obj(nested))
        return numbers
    if isinstance(value, int | float) and not isinstance(value, bool):
        numbers.add(_normalize_number(value))
        return numbers
    if isinstance(value, str):
        for match in re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", value):
            numbers.add(_normalize_number(match))
    return numbers


def _normalize_number(value: Any) -> str:
    text = str(value).strip()
    try:
        numeric = float(text)
    except ValueError:
        return text
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:g}"


def _compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if value is not None and value != [] and value != {}
    }


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value not in seen:
            unique_values.append(value)
            seen.add(value)
    return unique_values
