from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from datetime import date as date_cls
from typing import Any

import requests
from requests import RequestException, Timeout

from models.ai_nutrition_explanation_models import (
    ApprovedNutritionExplanation,
    ApprovedNutritionExplanationResult,
    CandidateNutritionExplanation,
    NutritionExplanationContext,
    NutritionExplanationRuntimeMetadata,
)
from services.ai_nutrition_explanation_validation_service import (
    approve_nutrition_explanation_candidate,
    build_deterministic_fallback_nutrition_explanation,
    collect_nutrition_explanation_validation_errors,
    validate_approved_nutrition_explanation,
)
from services.nutrition_food_suggestion_service import (
    build_approved_nutrition_food_suggestions,
)
from services.nutrition_target_calibration_service import (
    build_nutrition_target_calibration_result,
)
from services.nutrition_target_formula_service import (
    build_nutrition_target_formula_inputs,
    calculate_nutrition_target_formula,
)
from services.nutrition_target_formula_validation_service import (
    approve_validated_macro_targets,
)
from services.nutrition_target_vs_actual_service import (
    build_approved_nutrition_guidance,
    build_target_vs_actual_nutrition_summary,
)
from services.nutrition_trend_service import build_nutrition_trend_window
from services.user_service import get_user_profile
from services.user_state_service import build_user_health_state

NUTRITION_EXPLANATION_PROVIDER_ENV = "NUTRITION_EXPLANATION_PROVIDER"
NUTRITION_EXPLANATION_MODEL_ENV = "NUTRITION_EXPLANATION_MODEL"
OLLAMA_BASE_URL_ENV = "OLLAMA_BASE_URL"
NUTRITION_EXPLANATION_DIRECT_OLLAMA_TIMEOUT_ENV = (
    "NUTRITION_EXPLANATION_DIRECT_OLLAMA_TIMEOUT_SECONDS"
)
NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC = "deterministic"
NUTRITION_EXPLANATION_PROVIDER_CREWAI = "crewai"
NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA = "direct_ollama"
NUTRITION_EXPLANATION_DEFAULT_MODEL = "ollama/qwen3:8b"
NUTRITION_EXPLANATION_DEFAULT_BASE_URL = "http://localhost:11434"
RAW_OUTPUT_PREVIEW_LIMIT = 500
NUTRITION_EXPLANATION_DIRECT_OLLAMA_DEFAULT_TIMEOUT_SECONDS = 60.0

_CONTEXT_REASON_CODE = "approved_nutrition_explanation_context_built"
_FALLBACK_REASON_CODE = "deterministic_nutrition_explanation_service"
_PROVIDER_REASON_CODE = "provider_nutrition_explanation_candidate"
_CONTEXT_LIMITATION = (
    "Nutrition explanation is limited to approved backend nutrition context."
)
_CONFIDENCE_RANK = {"Limited": 0, "Low": 1, "Moderate": 2, "High": 3}
_MACRO_TARGET_KEYS = {
    "calories": "calorie_target",
    "protein": "protein_target_g",
    "carbs": "carbohydrate_target_g",
    "fat": "fat_target_g",
}
_MACRO_ACTUAL_KEYS = {
    "calories": "logged_calories",
    "protein": "logged_protein",
    "carbs": "logged_carbs",
    "fat": "logged_fat",
}
_MACRO_UNITS = {
    "calories": "kcal",
    "protein": "g",
    "carbs": "g",
    "fat": "g",
}

FALLBACK_REASON_DETERMINISTIC_SELECTED = "deterministic_provider_selected"
FALLBACK_REASON_INVALID_PROVIDER = "invalid_provider_config"
FALLBACK_REASON_PROVIDER_EXCEPTION = "provider_exception"
FALLBACK_REASON_DIRECT_OLLAMA_TIMEOUT = "direct_ollama_timeout"
FALLBACK_REASON_DIRECT_OLLAMA_CONNECTION_ERROR = "direct_ollama_connection_error"
FALLBACK_REASON_DIRECT_OLLAMA_HTTP_ERROR = "direct_ollama_http_error"
FALLBACK_REASON_DIRECT_OLLAMA_MALFORMED_RESPONSE = "direct_ollama_malformed_response"
FALLBACK_REASON_DIRECT_OLLAMA_MISSING_RESPONSE_TEXT = (
    "direct_ollama_missing_response_text"
)
FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT = "provider_non_string_output"
FALLBACK_REASON_CANDIDATE_PARSE_FAILURE = "candidate_parse_failure"
FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE = "candidate_validation_failure"
FALLBACK_REASON_DETERMINISTIC_VALIDATION_FAILURE = "deterministic_validation_failure"

CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED = "not_attempted"
CANDIDATE_PARSE_STATUS_SUCCESS = "success"
CANDIDATE_PARSE_STATUS_FAILED = "failed"

CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED = "not_attempted"
CANDIDATE_VALIDATION_STATUS_SUCCESS = "success"
CANDIDATE_VALIDATION_STATUS_FAILED = "failed"

VALIDATION_STATUS_NOT_ATTEMPTED = "not_attempted"
VALIDATION_STATUS_APPROVED = "approved"
VALIDATION_STATUS_REJECTED = "rejected"

FINAL_EXPLANATION_SOURCE_DETERMINISTIC = "deterministic"
FINAL_EXPLANATION_SOURCE_PROVIDER_APPROVED = "provider_approved"
FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"

NutritionExplanationCandidateProvider = Callable[[NutritionExplanationContext], Any]
DirectOllamaGenerateCallable = Callable[[str, str, str, dict[str, Any], float], str]

CANDIDATE_NUTRITION_EXPLANATION_ALLOWED_KEYS = {
    "explanation_summary",
    "macro_context",
    "food_suggestion_context",
    "trend_context",
    "calibration_context",
    "limitations_context",
    "confidence",
    "reason_codes",
}

CANDIDATE_NUTRITION_EXPLANATION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "explanation_summary",
        "macro_context",
        "food_suggestion_context",
        "trend_context",
        "calibration_context",
        "limitations_context",
        "confidence",
        "reason_codes",
    ],
    "properties": {
        "explanation_summary": {"type": "string"},
        "macro_context": {"type": ["string", "null"]},
        "food_suggestion_context": {"type": ["string", "null"]},
        "trend_context": {"type": ["string", "null"]},
        "calibration_context": {"type": ["string", "null"]},
        "limitations_context": {"type": ["string", "null"]},
        "confidence": {
            "type": "string",
            "enum": ["Limited", "Low", "Moderate", "High"],
        },
        "reason_codes": {"type": "array", "items": {"type": "string"}},
    },
}


class DirectOllamaProviderError(RuntimeError):
    """Classified direct Ollama provider failure used for fallback metadata."""

    def __init__(self, fallback_reason: str, message: str) -> None:
        super().__init__(message)
        self.fallback_reason = fallback_reason


def build_nutrition_explanation_context(
    user_id: int,
    explanation_date: str | None = None,
    *,
    approved_macro_targets: Any | None = None,
    target_vs_actual_summary: Any | None = None,
    approved_nutrition_guidance: Any | None = None,
    approved_food_suggestions: Any | None = None,
    trend_window: Any | None = None,
    calibration_result: Any | None = None,
) -> NutritionExplanationContext:
    """Build approved deterministic context for a nutrition explanation.

    This service composes existing backend-approved nutrition services only. It does
    not call AI providers, infer missing facts, invent food suggestions, mutate
    targets, or apply calibration results.
    """

    resolved_date = explanation_date or date_cls.today().isoformat()

    target_summary = (
        target_vs_actual_summary
        or build_target_vs_actual_nutrition_summary(
            user_id,
            resolved_date,
        )
    )
    guidance = approved_nutrition_guidance or build_approved_nutrition_guidance(
        target_summary
    )
    food_suggestions = (
        approved_food_suggestions
        or build_approved_nutrition_food_suggestions(
            user_id,
            resolved_date,
            target_vs_actual_summary=target_summary,
        )
    )
    trend = trend_window or build_nutrition_trend_window(
        user_id,
        end_date=resolved_date,
        window_days=28,
    )
    calibration = calibration_result or build_nutrition_target_calibration_result(
        user_id,
        calibration_date=resolved_date,
        window_days=28,
        trend_window=trend,
    )
    macro_targets = approved_macro_targets or _build_approved_macro_targets(
        user_id=user_id,
        calculation_date=resolved_date,
    )

    approved_macro_targets_payload = _approved_macro_targets_projection(macro_targets)
    target_vs_actual_payload = _target_vs_actual_projection(target_summary)
    guidance_payload = _to_public_dict(guidance)
    food_suggestions_payload = _food_suggestions_projection(food_suggestions)
    trend_payload = _trend_window_projection(trend)
    calibration_payload = _calibration_projection(calibration)
    value_aware_payload = _value_aware_summary_from_payloads(
        approved_macro_targets_payload=approved_macro_targets_payload,
        target_vs_actual_payload=target_vs_actual_payload,
        food_suggestions_payload=food_suggestions_payload,
        trend_payload=trend_payload,
        calibration_payload=calibration_payload,
    )

    confidence = _minimum_confidence(
        _payload_confidence(approved_macro_targets_payload),
        _payload_confidence(target_vs_actual_payload),
        _payload_confidence(guidance_payload),
        _payload_confidence(food_suggestions_payload),
        _payload_confidence(trend_payload),
        _payload_confidence(calibration_payload),
    )
    reason_codes = _unique(
        [
            _CONTEXT_REASON_CODE,
            *_payload_list(approved_macro_targets_payload, "reason_codes"),
            *_payload_list(target_vs_actual_payload, "reason_codes"),
            *_payload_list(guidance_payload, "reason_codes"),
            *_payload_list(food_suggestions_payload, "reason_codes"),
            *_payload_list(trend_payload, "reason_codes"),
            *_payload_list(calibration_payload, "reason_codes"),
        ]
    )
    limitations = _unique(
        [
            *_payload_list(approved_macro_targets_payload, "limitations"),
            *_payload_list(target_vs_actual_payload, "limitations"),
            *_payload_list(guidance_payload, "limitations"),
            *_payload_list(food_suggestions_payload, "limitations"),
            *_payload_list(trend_payload, "limitations"),
            *_payload_list(calibration_payload, "limitations"),
        ]
    )

    if confidence in {"Limited", "Low"} and not limitations:
        limitations.append(_CONTEXT_LIMITATION)

    return NutritionExplanationContext(
        user_id=user_id,
        explanation_date=resolved_date,
        approved_macro_targets=approved_macro_targets_payload,
        target_vs_actual_summary=target_vs_actual_payload,
        approved_nutrition_guidance=guidance_payload,
        approved_food_suggestions=food_suggestions_payload,
        trend_summary=trend_payload,
        calibration_summary=calibration_payload,
        value_aware_summary=value_aware_payload,
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=limitations,
        display_flags=_payload_mapping(approved_macro_targets_payload, "display_flags"),
    )


def build_deterministic_nutrition_explanation_candidate(
    context: NutritionExplanationContext,
) -> CandidateNutritionExplanation:
    """Build deterministic candidate copy from approved context only.

    The candidate contains no provider-generated facts and intentionally avoids
    specific foods, serving amounts, and macro numbers. It can be used as a stable
    fallback candidate or as a baseline for future provider validation tests.
    """

    return CandidateNutritionExplanation(
        explanation_summary=_candidate_summary(context),
        macro_context=_candidate_macro_context(context),
        food_suggestion_context=_candidate_food_suggestion_context(context),
        trend_context=_candidate_trend_context(context),
        calibration_context=_candidate_calibration_context(context),
        limitations_context=_candidate_limitations_context(context),
        confidence=context.confidence,
        reason_codes=[_FALLBACK_REASON_CODE],
    )


def build_approved_nutrition_explanation(
    user_id: int,
    explanation_date: str | None = None,
    *,
    context: NutritionExplanationContext | None = None,
) -> ApprovedNutritionExplanation:
    """Return a validated deterministic ApprovedNutritionExplanation.

    This service does not call CrewAI, Ollama, external AI providers, RAG, or any
    runtime provider. It builds/uses approved backend context and returns a
    validator-approved deterministic fallback explanation.
    """

    resolved_context = context or build_nutrition_explanation_context(
        user_id,
        explanation_date,
    )
    candidate = build_deterministic_nutrition_explanation_candidate(resolved_context)

    try:
        approved = approve_nutrition_explanation_candidate(resolved_context, candidate)
    except ValueError:
        approved = build_deterministic_fallback_nutrition_explanation(resolved_context)

    if approved.source == "ai_validated":
        approved = ApprovedNutritionExplanation(
            user_id=approved.user_id,
            explanation_date=approved.explanation_date,
            explanation_summary=approved.explanation_summary,
            macro_context=approved.macro_context,
            food_suggestion_context=approved.food_suggestion_context,
            trend_context=approved.trend_context,
            calibration_context=approved.calibration_context,
            limitations_context=approved.limitations_context,
            confidence=approved.confidence,
            reason_codes=_unique([*approved.reason_codes, _FALLBACK_REASON_CODE]),
            limitations=approved.limitations,
            source="deterministic_fallback",
        )

    return validate_approved_nutrition_explanation(approved)


def approve_candidate_output_or_fallback_with_metadata(
    provider_output: Any,
    context: NutritionExplanationContext,
    *,
    configured_provider: str = NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC,
    selected_provider: str = NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC,
    configured_model: str | None = None,
    selected_model: str | None = None,
    provider_attempted: bool = False,
) -> ApprovedNutritionExplanationResult:
    """Approve a provider candidate or fall back to deterministic output.

    Provider output is never trusted. It is parsed into CandidateNutritionExplanation,
    validated against the approved context, and only then converted to an
    ApprovedNutritionExplanation. Validation errors and raw output diagnostics remain
    runtime/debug-only metadata.
    """

    raw_diagnostics = _raw_output_diagnostics(provider_output)
    candidate, parse_error = _parse_provider_candidate(provider_output)

    if candidate is None:
        metadata = _runtime_metadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            configured_model=_resolved_metadata_model(
                configured_model, configured_provider
            ),
            selected_model=_resolved_metadata_model(selected_model, selected_provider),
            provider_attempted=provider_attempted,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_CANDIDATE_PARSE_FAILURE,
            candidate_valid=False,
            validation_errors=[
                parse_error or "Provider candidate could not be parsed."
            ],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_FAILED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
            **raw_diagnostics,
        )
        return _deterministic_result(context, metadata)

    validation_errors = collect_nutrition_explanation_validation_errors(
        context,
        candidate,
    )
    if validation_errors:
        metadata = _runtime_metadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            configured_model=_resolved_metadata_model(
                configured_model, configured_provider
            ),
            selected_model=_resolved_metadata_model(selected_model, selected_provider),
            provider_attempted=provider_attempted,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE,
            candidate_valid=False,
            validation_errors=validation_errors,
            candidate_parse_status=CANDIDATE_PARSE_STATUS_SUCCESS,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_FAILED,
            validation_status=VALIDATION_STATUS_REJECTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
            **raw_diagnostics,
        )
        return _deterministic_result(context, metadata)

    approved = approve_nutrition_explanation_candidate(context, candidate)
    metadata = _runtime_metadata(
        configured_provider=configured_provider,
        selected_provider=selected_provider,
        configured_model=_resolved_metadata_model(
            configured_model, configured_provider
        ),
        selected_model=_resolved_metadata_model(selected_model, selected_provider),
        provider_attempted=provider_attempted,
        fallback_used=False,
        fallback_reason=None,
        candidate_valid=True,
        validation_errors=[],
        candidate_parse_status=CANDIDATE_PARSE_STATUS_SUCCESS,
        candidate_validation_status=CANDIDATE_VALIDATION_STATUS_SUCCESS,
        validation_status=VALIDATION_STATUS_APPROVED,
        final_explanation_source=FINAL_EXPLANATION_SOURCE_PROVIDER_APPROVED,
        **raw_diagnostics,
    )
    return ApprovedNutritionExplanationResult(
        approved_nutrition_explanation=validate_approved_nutrition_explanation(
            approved
        ),
        runtime_metadata=metadata,
    )


def approve_candidate_provider_or_fallback_with_metadata(
    candidate_provider: NutritionExplanationCandidateProvider,
    context: NutritionExplanationContext,
    *,
    configured_provider: str = NUTRITION_EXPLANATION_PROVIDER_CREWAI,
    selected_provider: str = NUTRITION_EXPLANATION_PROVIDER_CREWAI,
    configured_model: str | None = None,
    selected_model: str | None = None,
) -> ApprovedNutritionExplanationResult:
    """Run a provider and safely fall back if it is unavailable or invalid."""

    try:
        provider_output = candidate_provider(context)
    except Exception as exc:
        metadata = _runtime_metadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            configured_model=_resolved_metadata_model(
                configured_model, configured_provider
            ),
            selected_model=_resolved_metadata_model(selected_model, selected_provider),
            provider_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            candidate_valid=False,
            validation_errors=[type(exc).__name__],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
        )
        return _deterministic_result(context, metadata)

    if not isinstance(
        provider_output,
        str | dict | CandidateNutritionExplanation,
    ):
        metadata = _runtime_metadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            configured_model=_resolved_metadata_model(
                configured_model, configured_provider
            ),
            selected_model=_resolved_metadata_model(selected_model, selected_provider),
            provider_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT,
            candidate_valid=False,
            validation_errors=[
                "Nutrition explanation provider returned unsupported output."
            ],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
        )
        return _deterministic_result(context, metadata)

    return approve_candidate_output_or_fallback_with_metadata(
        provider_output,
        context,
        configured_provider=configured_provider,
        selected_provider=selected_provider,
        configured_model=_resolved_metadata_model(
            configured_model, configured_provider
        ),
        selected_model=_resolved_metadata_model(selected_model, selected_provider),
        provider_attempted=True,
    )


def build_crewai_nutrition_explanation_prompt(
    context: NutritionExplanationContext,
) -> str:
    """Build the compressed bounded nutrition explanation prompt for a provider.

    The provider receives only concise approved explanatory facts. Display-control
    metadata, formula metadata, dates, provider/debug/runtime fields, and raw reason-code
    dumps are intentionally omitted. Provider output remains untrusted until the strict
    parser and validator approve it.
    """

    provider_context_json = json.dumps(
        _compressed_provider_context_projection(context),
        sort_keys=True,
        default=str,
    )
    valid_example_json = json.dumps(
        _candidate_nutrition_explanation_example(),
        sort_keys=True,
    )
    return f"""
/no_think
Task: explain the approved nutrition context in concise, supportive language.

Strict output rules:
- Return JSON only: one raw JSON object and nothing else.
- Do not include markdown.
- Do not include code fences.
- Do not include comments.
- Do not include prose outside JSON.
- The first character must be {{ and the last character must be }}.
- Include exactly these top-level keys and no others.
- Do not include any keys not listed in the schema.
- Do not include display flags.
- Do not include display_flags.
- Do not include displayFlags.
- Do not include explanationDate.
- Do not include explanation_date.
- Do not include dates unless the schema explicitly requires them.
- Do not include target metadata.
- Do not include formula metadata.
- Do not include raw context fields.
- Do not include provider fields.
- Do not include runtime fields.
- Do not include validation fields.
- Do not include debug fields.
- Do not copy keys from the approved context into the output unless they are explicitly listed in the schema.
- You may quote numbers only when they appear in value_aware_context.
- You may quote foods only when they appear in value_aware_context.approved_food_suggestion_candidates.
- Do not calculate gaps; only restate gap values that appear in value_aware_context.

CandidateNutritionExplanation allowed output schema:
{{
  "explanation_summary": "string",
  "macro_context": "string or null",
  "food_suggestion_context": "string or null",
  "trend_context": "string or null",
  "calibration_context": "string or null",
  "limitations_context": "string or null",
  "confidence": "Limited | Low | Moderate | High",
  "reason_codes": ["string"]
}}

One valid JSON example:
{valid_example_json}

Approved context JSON:
{provider_context_json}

Forbidden language and behavior:
- Do not invent nutrition targets, logged actuals, foods, servings, macros, or nutrient values.
- Do not quote target ranges, logged actuals, gap values, or food details unless they are present in value_aware_context.
- Do not claim targets changed or calibration was applied.
- Do not create meal plans. Meal/snack framing must be brief and based only on approved food suggestions.
- Do not mention raw data, SQL, providers, CrewAI, Ollama, debug metadata, or validation metadata.
- Explain limitations instead of inventing details when context is limited.
- Keep each field concise.
- Confidence must be one of: Limited, Low, Moderate, High.
""".strip()


def generate_crewai_nutrition_explanation_candidate_json(
    context: NutritionExplanationContext,
) -> str:
    """Run the optional CrewAI/Ollama nutrition explanation provider.

    This path is optional and disabled by default. The returned string is untrusted
    and must be parsed/validated before it can become public output.
    """

    from crewai import LLM, Agent, Crew, Task

    llm = LLM(
        model=os.getenv(
            NUTRITION_EXPLANATION_MODEL_ENV,
            NUTRITION_EXPLANATION_DEFAULT_MODEL,
        ),
        base_url=os.getenv(OLLAMA_BASE_URL_ENV, NUTRITION_EXPLANATION_DEFAULT_BASE_URL),
        temperature=0,
    )
    agent = Agent(
        role="Bounded Nutrition Explanation Writer",
        goal="Generate CandidateNutritionExplanation JSON from approved context only.",
        backstory=(
            "You explain approved backend nutrition facts without inventing targets, "
            "foods, servings, macros, calibration state, or medical claims."
        ),
        llm=llm,
        verbose=False,
    )
    task = Task(
        description=build_crewai_nutrition_explanation_prompt(context),
        expected_output="Raw CandidateNutritionExplanation JSON object only.",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = getattr(result, "raw", None)
    return str(raw) if raw is not None else str(result)


def normalize_ollama_model_name(model: str) -> str:
    """Normalize a CrewAI-style Ollama model name for direct Ollama REST calls."""

    stripped = model.strip()
    if stripped.startswith("ollama/"):
        return stripped.removeprefix("ollama/")
    return stripped


def call_direct_ollama_generate(
    base_url: str,
    selected_model: str,
    prompt: str,
    response_schema: dict[str, Any],
    timeout_seconds: float,
) -> str:
    """Call Ollama /api/generate with JSON-schema structured output.

    The raw response remains untrusted until the existing parser and validator
    approve it. This function only handles transport and response-shape errors.
    """

    endpoint = f"{base_url.rstrip('/')}/api/generate"
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "format": response_schema,
        "stream": False,
        "options": {"temperature": 0},
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
    except Timeout as exc:
        raise DirectOllamaProviderError(
            FALLBACK_REASON_DIRECT_OLLAMA_TIMEOUT,
            f"Direct Ollama request timed out after {timeout_seconds:g} seconds.",
        ) from exc
    except RequestException as exc:
        fallback_reason = (
            FALLBACK_REASON_DIRECT_OLLAMA_HTTP_ERROR
            if getattr(exc, "response", None) is not None
            else FALLBACK_REASON_DIRECT_OLLAMA_CONNECTION_ERROR
        )
        raise DirectOllamaProviderError(fallback_reason, str(exc)) from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise DirectOllamaProviderError(
            FALLBACK_REASON_DIRECT_OLLAMA_MALFORMED_RESPONSE,
            "Direct Ollama response body was not valid JSON.",
        ) from exc

    if not isinstance(body, dict):
        raise DirectOllamaProviderError(
            FALLBACK_REASON_DIRECT_OLLAMA_MALFORMED_RESPONSE,
            "Direct Ollama response payload was not a JSON object.",
        )

    raw_output = body.get("response")
    if not isinstance(raw_output, str) or not raw_output.strip():
        raise DirectOllamaProviderError(
            FALLBACK_REASON_DIRECT_OLLAMA_MISSING_RESPONSE_TEXT,
            "Direct Ollama response did not include a non-empty text response field.",
        )
    return raw_output


def generate_direct_ollama_nutrition_explanation_candidate_json(
    context: NutritionExplanationContext,
    *,
    generate: DirectOllamaGenerateCallable = call_direct_ollama_generate,
) -> str:
    """Run direct Ollama structured output for nutrition explanations.

    This provider is optional and disabled by default. The returned string is
    untrusted and must still pass the strict parser and validator before approval.
    """

    configured_model = _configured_nutrition_explanation_model()
    selected_model = normalize_ollama_model_name(configured_model)
    base_url = os.getenv(OLLAMA_BASE_URL_ENV, NUTRITION_EXPLANATION_DEFAULT_BASE_URL)
    timeout_seconds = _configured_direct_ollama_timeout_seconds()
    return generate(
        base_url,
        selected_model,
        build_crewai_nutrition_explanation_prompt(context),
        CANDIDATE_NUTRITION_EXPLANATION_JSON_SCHEMA,
        timeout_seconds,
    )


def approve_direct_ollama_provider_or_fallback_with_metadata(
    context: NutritionExplanationContext,
    *,
    generate: DirectOllamaGenerateCallable = call_direct_ollama_generate,
) -> ApprovedNutritionExplanationResult:
    """Run the direct Ollama provider with classified deterministic fallback."""

    configured_model = _configured_nutrition_explanation_model()
    selected_model = normalize_ollama_model_name(configured_model)

    try:
        provider_output = generate_direct_ollama_nutrition_explanation_candidate_json(
            context,
            generate=generate,
        )
    except DirectOllamaProviderError as exc:
        metadata = _runtime_metadata(
            configured_provider=NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
            selected_provider=NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=True,
            fallback_used=True,
            fallback_reason=exc.fallback_reason,
            candidate_valid=False,
            validation_errors=[str(exc)],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
        )
        return _deterministic_result(context, metadata)
    except Exception as exc:
        metadata = _runtime_metadata(
            configured_provider=NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
            selected_provider=NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=True,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            candidate_valid=False,
            validation_errors=[type(exc).__name__],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
        )
        return _deterministic_result(context, metadata)

    return approve_candidate_output_or_fallback_with_metadata(
        provider_output,
        context,
        configured_provider=NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
        selected_provider=NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
        configured_model=configured_model,
        selected_model=selected_model,
        provider_attempted=True,
    )


def build_configured_approved_nutrition_explanation_with_metadata(
    user_id: int,
    explanation_date: str | None = None,
    *,
    context: NutritionExplanationContext | None = None,
    candidate_provider: NutritionExplanationCandidateProvider | None = None,
    direct_ollama_generate: DirectOllamaGenerateCallable | None = None,
) -> ApprovedNutritionExplanationResult:
    """Build an approved nutrition explanation using configured provider settings.

    Deterministic remains the default. Invalid provider settings, provider errors,
    parse failures, and validator rejections all fall back to deterministic approved
    output with debug-only runtime metadata.
    """

    resolved_context = context or build_nutrition_explanation_context(
        user_id,
        explanation_date,
    )
    configured_provider = _configured_nutrition_explanation_provider()

    if configured_provider == NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC:
        metadata = _runtime_metadata(
            configured_provider=configured_provider,
            selected_provider=NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC,
            configured_model=NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC,
            selected_model=NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC,
            provider_attempted=False,
            fallback_used=False,
            fallback_reason=FALLBACK_REASON_DETERMINISTIC_SELECTED,
            candidate_valid=True,
            validation_errors=[],
            candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC,
        )
        return _deterministic_result(resolved_context, metadata)

    if configured_provider == NUTRITION_EXPLANATION_PROVIDER_CREWAI:
        return approve_candidate_provider_or_fallback_with_metadata(
            candidate_provider or generate_crewai_nutrition_explanation_candidate_json,
            resolved_context,
            configured_provider=configured_provider,
            selected_provider=NUTRITION_EXPLANATION_PROVIDER_CREWAI,
            configured_model=_configured_nutrition_explanation_model(),
            selected_model=_configured_nutrition_explanation_model(),
        )

    if configured_provider == NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA:
        if candidate_provider is not None:
            configured_model = _configured_nutrition_explanation_model()
            selected_model = normalize_ollama_model_name(configured_model)
            return approve_candidate_provider_or_fallback_with_metadata(
                candidate_provider,
                resolved_context,
                configured_provider=configured_provider,
                selected_provider=NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
                configured_model=configured_model,
                selected_model=selected_model,
            )
        return approve_direct_ollama_provider_or_fallback_with_metadata(
            resolved_context,
            generate=direct_ollama_generate or call_direct_ollama_generate,
        )

    metadata = _runtime_metadata(
        configured_provider=configured_provider,
        selected_provider=NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC,
        configured_model=NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC,
        selected_model=NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC,
        provider_attempted=False,
        fallback_used=True,
        fallback_reason=FALLBACK_REASON_INVALID_PROVIDER,
        candidate_valid=True,
        validation_errors=[f"Unsupported provider: {configured_provider}"],
        candidate_parse_status=CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
        candidate_validation_status=CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
        validation_status=VALIDATION_STATUS_NOT_ATTEMPTED,
        final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
    )
    return _deterministic_result(resolved_context, metadata)


def build_configured_approved_nutrition_explanation(
    user_id: int,
    explanation_date: str | None = None,
    *,
    context: NutritionExplanationContext | None = None,
) -> ApprovedNutritionExplanation:
    """Return only the public approved explanation for the configured provider."""

    return build_configured_approved_nutrition_explanation_with_metadata(
        user_id,
        explanation_date,
        context=context,
    ).approved_nutrition_explanation


def _deterministic_result(
    context: NutritionExplanationContext,
    metadata: NutritionExplanationRuntimeMetadata,
) -> ApprovedNutritionExplanationResult:
    try:
        approved = build_approved_nutrition_explanation(
            context.user_id,
            context.explanation_date,
            context=context,
        )
    except ValueError:
        approved = build_deterministic_fallback_nutrition_explanation(context)
        metadata = _runtime_metadata(
            configured_provider=metadata.configured_provider or metadata.provider,
            selected_provider=NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC,
            configured_model=metadata.configured_model,
            selected_model=NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC,
            provider_attempted=metadata.provider_attempted,
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_DETERMINISTIC_VALIDATION_FAILURE,
            candidate_valid=False,
            validation_errors=["Deterministic explanation validation failed."],
            candidate_parse_status=metadata.candidate_parse_status,
            candidate_validation_status=metadata.candidate_validation_status,
            validation_status=VALIDATION_STATUS_REJECTED,
            final_explanation_source=FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
        )
    return ApprovedNutritionExplanationResult(
        approved_nutrition_explanation=validate_approved_nutrition_explanation(
            approved
        ),
        runtime_metadata=metadata,
    )


def _runtime_metadata(
    *,
    configured_provider: str,
    selected_provider: str,
    configured_model: str | None = None,
    selected_model: str | None = None,
    provider_attempted: bool,
    fallback_used: bool,
    fallback_reason: str | None,
    candidate_valid: bool,
    validation_errors: list[str],
    candidate_parse_status: str,
    candidate_validation_status: str = CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
    validation_status: str,
    final_explanation_source: str,
    raw_output_length: int | None = None,
    raw_output_preview_truncated: str | None = None,
    markdown_wrapper_detected: bool = False,
) -> NutritionExplanationRuntimeMetadata:
    return NutritionExplanationRuntimeMetadata(
        provider=selected_provider,
        fallback_used=fallback_used,
        validation_status=validation_status,
        validation_errors=list(validation_errors),
        raw_output_preview_truncated=raw_output_preview_truncated,
        raw_output_length=raw_output_length,
        configured_provider=configured_provider,
        selected_provider=selected_provider,
        configured_model=_resolved_metadata_model(
            configured_model, configured_provider
        ),
        selected_model=_resolved_metadata_model(selected_model, selected_provider),
        provider_attempted=provider_attempted,
        fallback_reason=fallback_reason,
        candidate_valid=candidate_valid,
        candidate_parse_status=candidate_parse_status,
        candidate_validation_status=candidate_validation_status,
        final_explanation_source=final_explanation_source,
        markdown_wrapper_detected=markdown_wrapper_detected,
    )


def _configured_nutrition_explanation_provider() -> str:
    return (
        os.getenv(
            NUTRITION_EXPLANATION_PROVIDER_ENV,
            NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC,
        )
        .strip()
        .lower()
    )


def _configured_nutrition_explanation_model() -> str:
    return os.getenv(
        NUTRITION_EXPLANATION_MODEL_ENV,
        NUTRITION_EXPLANATION_DEFAULT_MODEL,
    ).strip()


def _configured_direct_ollama_timeout_seconds() -> float:
    raw_timeout = os.getenv(NUTRITION_EXPLANATION_DIRECT_OLLAMA_TIMEOUT_ENV)
    if raw_timeout is None or not raw_timeout.strip():
        return NUTRITION_EXPLANATION_DIRECT_OLLAMA_DEFAULT_TIMEOUT_SECONDS

    try:
        timeout_seconds = float(raw_timeout)
    except ValueError:
        return NUTRITION_EXPLANATION_DIRECT_OLLAMA_DEFAULT_TIMEOUT_SECONDS

    if timeout_seconds <= 0:
        return NUTRITION_EXPLANATION_DIRECT_OLLAMA_DEFAULT_TIMEOUT_SECONDS
    return timeout_seconds


def _resolved_metadata_model(model: str | None, provider: str | None) -> str:
    if model:
        return model
    if provider in {
        NUTRITION_EXPLANATION_PROVIDER_CREWAI,
        NUTRITION_EXPLANATION_PROVIDER_DIRECT_OLLAMA,
    }:
        return _configured_nutrition_explanation_model()
    return NUTRITION_EXPLANATION_PROVIDER_DETERMINISTIC


def _parse_provider_candidate(
    provider_output: Any,
) -> tuple[CandidateNutritionExplanation | None, str | None]:
    if isinstance(provider_output, CandidateNutritionExplanation):
        return provider_output, None

    try:
        if isinstance(provider_output, dict):
            return CandidateNutritionExplanation(**provider_output), None

        if isinstance(provider_output, str):
            candidate_payload = _parse_candidate_json_payload(provider_output)
            return CandidateNutritionExplanation(**candidate_payload), None
    except Exception as exc:
        return None, str(exc)

    return None, "Provider candidate output type is unsupported."


def _parse_candidate_json_payload(raw_output: str) -> dict[str, Any]:
    stripped = raw_output.strip()
    if not stripped:
        raise ValueError("Provider candidate output was empty.")
    _reject_markdown_or_code_fence(stripped)
    payload = json.loads(stripped)
    if not isinstance(payload, dict):
        raise ValueError("Provider candidate JSON must be an object.")
    return payload


def _reject_markdown_or_code_fence(text: str) -> None:
    if re.fullmatch(r"```(?:json)?\s*.*?\s*```", text, flags=re.DOTALL):
        raise ValueError(
            "Provider candidate output must be raw JSON without markdown or code fences."
        )
    if text.startswith("```") or text.endswith("```"):
        raise ValueError(
            "Provider candidate output must not include markdown code fences."
        )


def _compressed_provider_context_projection(
    context: NutritionExplanationContext,
) -> dict[str, Any]:
    """Return the compact approved context exposed to optional AI providers.

    This intentionally differs from NutritionExplanationContext.to_dict(). The provider
    does not need backend display controls, dates, formula metadata, debug/runtime data,
    raw reason-code dumps, raw source records, or unbounded nested service payloads.
    """

    return {
        "confidence": context.confidence,
        "macro_context": _compressed_macro_context(context),
        "food_suggestion_context": _compressed_food_suggestion_context(context),
        "trend_context": _compressed_trend_context(context),
        "calibration_context": _compressed_calibration_context(context),
        "limitations_context": _compressed_limitations_context(context),
        "value_aware_context": _compressed_value_aware_context(context),
    }


def _candidate_nutrition_explanation_example() -> dict[str, Any]:
    return {
        "explanation_summary": (
            "Approved nutrition context is available, but it should be interpreted "
            "within the current confidence limits."
        ),
        "macro_context": "Logged macro context is available from backend calculations.",
        "food_suggestion_context": (
            "The Nutrition tab may have approved food suggestions if a supported gap exists."
        ),
        "trend_context": "Trend context is available only from deterministic logged data.",
        "calibration_context": (
            "Targets remain formula-derived until backend calibration is approved."
        ),
        "limitations_context": (
            "Use the Nutrition tab for approved target, logging, trend, and calibration detail."
        ),
        "confidence": "Moderate",
        "reason_codes": ["provider_candidate_from_approved_context"],
    }


def _compressed_macro_context(context: NutritionExplanationContext) -> dict[str, Any]:
    target_summary = context.target_vs_actual_summary
    logging_summary = target_summary.get("logging_summary") or {}
    comparisons = target_summary.get("comparisons") or {}
    return _compact_dict(
        {
            "confidence": target_summary.get("confidence"),
            "logging_completeness": target_summary.get("logging_completeness")
            or logging_summary.get("logging_completeness"),
            "logged_meal_count": logging_summary.get("logged_meal_count"),
            "entry_count": logging_summary.get("entry_count"),
            "macro_statuses": {
                macro: _compact_dict(
                    {
                        "target_status": comparison.get("target_status"),
                        "comparison_available": comparison.get("comparison_available"),
                        "confidence": comparison.get("confidence"),
                    }
                )
                for macro, comparison in comparisons.items()
                if macro in {"calories", "protein", "carbs", "fat"}
                and isinstance(comparison, dict)
            },
            "limitations": _bounded_strings(target_summary.get("limitations", [])),
        }
    )


def _compressed_food_suggestion_context(
    context: NutritionExplanationContext,
) -> dict[str, Any]:
    payload = context.approved_food_suggestions
    suggestions = payload.get("suggestions") or []
    macro_gaps = payload.get("macro_gaps") or []
    return _compact_dict(
        {
            "confidence": payload.get("confidence"),
            "primary_gap": payload.get("primary_gap"),
            "approved_suggestion_count": (
                len(suggestions) if isinstance(suggestions, list) else 0
            ),
            "supported_gap_statuses": [
                _compact_dict(
                    {
                        "macro_name": gap.get("macro_name"),
                        "target_status": gap.get("target_status"),
                        "confidence": gap.get("confidence"),
                    }
                )
                for gap in macro_gaps
                if isinstance(gap, dict)
            ],
            "limitations": _bounded_strings(payload.get("limitations", [])),
        }
    )


def _compressed_value_aware_context(
    context: NutritionExplanationContext,
) -> dict[str, Any]:
    """Return display-approved values the provider may quote.

    Backend remains the source of truth for targets, actuals, gaps, statuses,
    confidence, logging quality, and food suggestion candidates. The provider may
    explain these values, but it must not compute or invent values of its own.
    """

    if context.value_aware_summary:
        return _compact_dict(context.value_aware_summary)

    return _value_aware_summary_from_payloads(
        approved_macro_targets_payload=context.approved_macro_targets,
        target_vs_actual_payload=context.target_vs_actual_summary,
        food_suggestions_payload=context.approved_food_suggestions,
        trend_payload=context.trend_summary,
        calibration_payload=context.calibration_summary,
    )


def _value_aware_summary_from_payloads(
    *,
    approved_macro_targets_payload: dict[str, Any],
    target_vs_actual_payload: dict[str, Any],
    food_suggestions_payload: dict[str, Any],
    trend_payload: dict[str, Any],
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    return _compact_dict(
        {
            "approved_target_ranges": _approved_target_ranges_for_provider(
                approved_macro_targets_payload
            ),
            "logged_actuals": _logged_actuals_for_provider(target_vs_actual_payload),
            "macro_statuses_and_gaps": _macro_statuses_and_gaps_for_provider(
                approved_macro_targets_payload,
                target_vs_actual_payload,
            ),
            "approved_food_suggestion_candidates": (
                _approved_food_suggestion_candidates_for_provider(
                    food_suggestions_payload
                )
            ),
            "logging_summary": _logging_summary_for_provider(target_vs_actual_payload),
            "trend_snapshot": _trend_snapshot_for_provider(trend_payload),
            "calibration_snapshot": _calibration_snapshot_for_provider(
                calibration_payload
            ),
        }
    )


def _approved_target_ranges_for_provider(
    targets: dict[str, Any],
) -> list[dict[str, Any]]:
    approved_ranges: list[dict[str, Any]] = []
    for macro, target_key in _MACRO_TARGET_KEYS.items():
        target = targets.get(target_key)
        if not _target_value_display_approved(target):
            continue
        approved_ranges.append(
            _compact_dict(
                {
                    "macro": macro,
                    "unit": target.get("unit") or _MACRO_UNITS[macro],
                    "target_min": _rounded_nutrition_value(target.get("min_value")),
                    "target_max": _rounded_nutrition_value(target.get("max_value")),
                    "display_value": target.get("display_value"),
                    "confidence": target.get("confidence"),
                }
            )
        )
    return approved_ranges


def _logged_actuals_for_provider(
    target_vs_actual_payload: dict[str, Any],
) -> dict[str, Any]:
    actuals = target_vs_actual_payload.get("nutrition_actuals") or {}
    return _compact_dict(
        {
            macro: _compact_dict(
                {
                    "actual": _rounded_nutrition_value(actuals.get(actual_key)),
                    "unit": _MACRO_UNITS[macro],
                }
            )
            for macro, actual_key in _MACRO_ACTUAL_KEYS.items()
            if _is_number(actuals.get(actual_key))
        }
    )


def _macro_statuses_and_gaps_for_provider(
    approved_macro_targets_payload: dict[str, Any],
    target_vs_actual_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    comparisons = target_vs_actual_payload.get("comparisons") or {}
    statuses: list[dict[str, Any]] = []
    for macro, target_key in _MACRO_TARGET_KEYS.items():
        comparison = comparisons.get(macro)
        if not isinstance(comparison, dict):
            continue
        target = approved_macro_targets_payload.get(target_key)
        target_display_approved = _target_value_display_approved(target)
        status_payload: dict[str, Any] = {
            "macro": macro,
            "target_status": comparison.get("target_status"),
            "comparison_available": comparison.get("comparison_available"),
            "confidence": comparison.get("confidence"),
            "unit": _MACRO_UNITS[macro],
        }
        actual = comparison.get("actual") or comparison.get("actual_value")
        if _is_number(actual):
            status_payload["actual"] = _rounded_nutrition_value(actual)
        if target_display_approved:
            status_payload.update(_approved_gap_values(comparison))
        statuses.append(_compact_dict(status_payload))
    return statuses


def _approved_gap_values(comparison: dict[str, Any]) -> dict[str, Any]:
    actual = comparison.get("actual") or comparison.get("actual_value")
    target_min = comparison.get("target_min")
    target_max = comparison.get("target_max")
    status = comparison.get("target_status")
    payload: dict[str, Any] = {
        "target_min": _rounded_nutrition_value(target_min),
        "target_max": _rounded_nutrition_value(target_max),
    }
    if status == "below_target" and _is_number(actual) and _is_number(target_min):
        payload["gap_to_target_min"] = _rounded_nutrition_value(
            max(float(target_min) - float(actual), 0.0)
        )
    elif status == "above_target" and _is_number(actual) and _is_number(target_max):
        payload["amount_above_target_max"] = _rounded_nutrition_value(
            max(float(actual) - float(target_max), 0.0)
        )
    return _compact_dict(payload)


def _approved_food_suggestion_candidates_for_provider(
    food_suggestions_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    suggestions = food_suggestions_payload.get("suggestions") or []
    if not isinstance(suggestions, list):
        return []
    return [
        _compact_dict(
            {
                "display_name": suggestion.get("display_name"),
                "suggested_grams": _rounded_nutrition_value(
                    suggestion.get("suggested_grams")
                ),
                "estimated_calories": _rounded_nutrition_value(
                    suggestion.get("estimated_calories")
                ),
                "estimated_protein_g": _rounded_nutrition_value(
                    suggestion.get("estimated_protein_g")
                ),
                "estimated_carbohydrate_g": _rounded_nutrition_value(
                    suggestion.get("estimated_carbohydrate_g")
                ),
                "estimated_fat_g": _rounded_nutrition_value(
                    suggestion.get("estimated_fat_g")
                ),
                "macro_gap_addressed": suggestion.get("macro_gap_addressed"),
                "confidence": suggestion.get("confidence"),
            }
        )
        for suggestion in suggestions[:3]
        if isinstance(suggestion, dict)
    ]


def _logging_summary_for_provider(
    target_vs_actual_payload: dict[str, Any],
) -> dict[str, Any]:
    logging_summary = target_vs_actual_payload.get("logging_summary") or {}
    return _compact_dict(
        {
            "logging_completeness": target_vs_actual_payload.get("logging_completeness")
            or logging_summary.get("logging_completeness"),
            "confidence": logging_summary.get("confidence")
            or target_vs_actual_payload.get("confidence"),
            "logged_meal_count": logging_summary.get("logged_meal_count"),
            "entry_count": logging_summary.get("entry_count"),
        }
    )


def _trend_snapshot_for_provider(trend: dict[str, Any]) -> dict[str, Any]:
    intake_summary = trend.get("intake_trend_summary") or {}
    bodyweight_summary = trend.get("bodyweight_trend_summary") or {}
    return _compact_dict(
        {
            "window_days": trend.get("window_days"),
            "logged_day_count": trend.get("logged_day_count"),
            "complete_logging_day_count": trend.get("complete_logging_day_count"),
            "logging_consistency_status": intake_summary.get(
                "logging_consistency_status"
            ),
            "complete_logging_rate": _rounded_nutrition_value(
                intake_summary.get("complete_logging_rate")
            ),
            "bodyweight_trend_direction": bodyweight_summary.get("trend_direction"),
            "bodyweight_weekly_rate_lb": _rounded_nutrition_value(
                bodyweight_summary.get("weekly_rate_lb")
            ),
            "confidence": trend.get("confidence"),
        }
    )


def _calibration_snapshot_for_provider(
    calibration: dict[str, Any],
) -> dict[str, Any]:
    return _compact_dict(
        {
            "calibration_allowed": calibration.get("calibration_allowed"),
            "readiness_level": calibration.get("readiness_level"),
            "recommended_action": calibration.get("recommended_action"),
            "confidence": calibration.get("confidence"),
        }
    )


def _target_value_display_approved(target: Any) -> bool:
    return isinstance(target, dict) and target.get("display_allowed") is True


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _rounded_nutrition_value(value: Any) -> int | float | None:
    if not _is_number(value):
        return None
    rounded = round(float(value), 1)
    if rounded.is_integer():
        return int(rounded)
    return rounded


def _compressed_trend_context(context: NutritionExplanationContext) -> dict[str, Any]:
    payload = context.trend_summary
    intake_summary = payload.get("intake_trend_summary") or {}
    bodyweight_summary = payload.get("bodyweight_trend_summary") or {}
    readiness = payload.get("calibration_readiness") or {}
    return _compact_dict(
        {
            "confidence": payload.get("confidence"),
            "window_days": payload.get("window_days"),
            "logged_day_count": payload.get("logged_day_count"),
            "complete_logging_day_count": payload.get("complete_logging_day_count"),
            "partial_logging_day_count": payload.get("partial_logging_day_count"),
            "no_log_day_count": payload.get("no_log_day_count"),
            "logging_consistency_status": intake_summary.get(
                "logging_consistency_status"
            ),
            "bodyweight_trend_direction": bodyweight_summary.get("trend_direction"),
            "bodyweight_trend_confidence": bodyweight_summary.get("confidence"),
            "calibration_readiness_level": readiness.get("readiness_level"),
            "limitations": _bounded_strings(payload.get("limitations", [])),
        }
    )


def _compressed_calibration_context(
    context: NutritionExplanationContext,
) -> dict[str, Any]:
    payload = context.calibration_summary
    return _compact_dict(
        {
            "confidence": payload.get("confidence"),
            "calibration_allowed": payload.get("calibration_allowed"),
            "readiness_level": payload.get("readiness_level"),
            "recommended_action": payload.get("recommended_action"),
            "limitations": _bounded_strings(payload.get("limitations", [])),
        }
    )


def _compressed_limitations_context(
    context: NutritionExplanationContext,
) -> dict[str, Any]:
    return _compact_dict(
        {
            "confidence": context.confidence,
            "limitations": _bounded_strings(context.limitations),
        }
    )


def _compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in payload.items() if value not in (None, "", [], {})
    }


def _bounded_strings(values: Any, *, limit: int = 5) -> list[str]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str) and value][:limit]


def _markdown_wrapper_detected(raw_output: str) -> bool:
    stripped = raw_output.strip()
    return bool(
        stripped.startswith("```")
        or stripped.endswith("```")
        or re.fullmatch(r"```(?:json)?\s*.*?\s*```", stripped, flags=re.DOTALL)
    )


def _raw_output_diagnostics(provider_output: Any) -> dict[str, Any]:
    if provider_output is None:
        return {
            "raw_output_length": 0,
            "raw_output_preview_truncated": None,
            "markdown_wrapper_detected": False,
        }
    if isinstance(provider_output, str):
        raw = provider_output
    elif isinstance(provider_output, CandidateNutritionExplanation):
        raw = json.dumps(provider_output.to_dict(), sort_keys=True)
    else:
        raw = json.dumps(provider_output, sort_keys=True, default=str)
    stripped = raw.strip()
    return {
        "raw_output_length": len(raw),
        "raw_output_preview_truncated": stripped[:RAW_OUTPUT_PREVIEW_LIMIT] or None,
        "markdown_wrapper_detected": _markdown_wrapper_detected(stripped),
    }


def _build_approved_macro_targets(*, user_id: int, calculation_date: str) -> Any:
    user_profile = get_user_profile(user_id)
    if not user_profile:
        raise ValueError(f"User with id {user_id} was not found.")
    health_state = build_user_health_state(user_id)
    inputs = build_nutrition_target_formula_inputs(
        health_state,
        calculation_date=calculation_date,
        sex=_row_value(user_profile, "gender"),
        input_source_metadata={"consumer": "ai_nutrition_explanation_service"},
    )
    formula_result = calculate_nutrition_target_formula(inputs)
    return approve_validated_macro_targets(formula_result)


def _approved_macro_targets_projection(approved_targets: Any) -> dict[str, Any]:
    payload = _to_public_dict(approved_targets)
    if not payload:
        return {}
    return {
        "user_id": payload.get("user_id"),
        "calculation_date": payload.get("calculation_date"),
        "confidence": payload.get("confidence"),
        "display_flags": payload.get("display_flags", {}),
        "calorie_target": _target_projection(payload.get("calorie_target")),
        "protein_target_g": _target_projection(payload.get("protein_target_g")),
        "carbohydrate_target_g": _target_projection(
            payload.get("carbohydrate_target_g")
        ),
        "fat_target_g": _target_projection(payload.get("fat_target_g")),
        "formula_metadata": _formula_metadata_projection(
            payload.get("formula_metadata")
        ),
        "reason_codes": payload.get("reason_codes", []),
        "limitations": payload.get("limitations", []),
    }


def _target_projection(target: Any) -> dict[str, Any] | None:
    if not isinstance(target, dict):
        return None
    return {
        "target_type": target.get("target_type"),
        "value": target.get("value"),
        "min_value": target.get("min_value"),
        "max_value": target.get("max_value"),
        "display_value": target.get("display_value"),
        "unit": target.get("unit"),
        "confidence": target.get("confidence"),
        "display_allowed": target.get("display_allowed"),
        "reason_codes": target.get("reason_codes", []),
        "limitations": target.get("limitations", []),
    }


def _formula_metadata_projection(metadata: Any) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    return {
        "formula_name": metadata.get("formula_name"),
        "formula_version": metadata.get("formula_version"),
        "calculation_date": metadata.get("calculation_date"),
        "target_basis": metadata.get("target_basis"),
        "reason_codes": metadata.get("reason_codes", []),
        "limitations": metadata.get("limitations", []),
    }


def _target_vs_actual_projection(summary: Any) -> dict[str, Any]:
    payload = _to_public_dict(summary)
    if not payload:
        return {}
    actuals = payload.get("nutrition_actuals") or {}
    logging_summary = payload.get("logging_summary") or {}
    comparisons = payload.get("comparisons") or {}
    return {
        "user_id": payload.get("user_id"),
        "date": payload.get("date"),
        "logging_completeness": payload.get("logging_completeness"),
        "confidence": payload.get("confidence"),
        "nutrition_actuals": {
            "logged_calories": actuals.get("logged_calories"),
            "logged_protein": actuals.get("logged_protein"),
            "logged_carbs": actuals.get("logged_carbs"),
            "logged_fat": actuals.get("logged_fat"),
            "logged_meal_count": actuals.get("logged_meal_count"),
            "entry_count": actuals.get("entry_count"),
        },
        "logging_summary": {
            "logging_completeness": logging_summary.get("logging_completeness"),
            "confidence": logging_summary.get("confidence"),
            "logged_meal_count": logging_summary.get("logged_meal_count"),
            "entry_count": logging_summary.get("entry_count"),
            "missing_nutrient_fields": logging_summary.get(
                "missing_nutrient_fields", []
            ),
            "reason_codes": logging_summary.get("reason_codes", []),
            "limitations": logging_summary.get("limitations", []),
        },
        "comparisons": {
            macro: _comparison_projection(comparison)
            for macro, comparison in comparisons.items()
            if macro in {"calories", "protein", "carbs", "fat"}
        },
        "reason_codes": payload.get("reason_codes", []),
        "limitations": payload.get("limitations", []),
    }


def _comparison_projection(comparison: Any) -> dict[str, Any]:
    if not isinstance(comparison, dict):
        return {}
    return {
        "nutrient": comparison.get("nutrient"),
        "actual": comparison.get("actual"),
        "target_min": comparison.get("target_min"),
        "target_max": comparison.get("target_max"),
        "target_status": comparison.get("target_status"),
        "comparison_available": comparison.get("comparison_available"),
        "confidence": comparison.get("confidence"),
        "reason_codes": comparison.get("reason_codes", []),
        "limitations": comparison.get("limitations", []),
    }


def _food_suggestions_projection(food_suggestions: Any) -> dict[str, Any]:
    payload = _to_public_dict(food_suggestions)
    if not payload:
        return {}
    suggestions = payload.get("suggestions") or []
    macro_gaps = payload.get("macro_gaps") or []
    return {
        "user_id": payload.get("user_id"),
        "suggestion_date": payload.get("suggestion_date"),
        "primary_gap": payload.get("primary_gap"),
        "macro_gaps": [
            {
                "macro_name": gap.get("macro_name"),
                "target_status": gap.get("target_status"),
                "display_allowed": gap.get("display_allowed"),
                "confidence": gap.get("confidence"),
                "reason_codes": gap.get("reason_codes", []),
                "limitations": gap.get("limitations", []),
            }
            for gap in macro_gaps
            if isinstance(gap, dict)
        ],
        "suggestions": [
            {
                "canonical_food_id": suggestion.get("canonical_food_id"),
                "display_name": suggestion.get("display_name"),
                "suggested_grams": suggestion.get("suggested_grams"),
                "estimated_calories": suggestion.get("estimated_calories"),
                "estimated_protein_g": suggestion.get("estimated_protein_g"),
                "estimated_carbohydrate_g": suggestion.get("estimated_carbohydrate_g"),
                "estimated_fat_g": suggestion.get("estimated_fat_g"),
                "macro_gap_addressed": suggestion.get("macro_gap_addressed"),
                "confidence": suggestion.get("confidence"),
                "reason_codes": suggestion.get("reason_codes", []),
                "limitations": suggestion.get("limitations", []),
            }
            for suggestion in suggestions
            if isinstance(suggestion, dict)
        ],
        "confidence": payload.get("confidence"),
        "reason_codes": payload.get("reason_codes", []),
        "limitations": payload.get("limitations", []),
    }


def _trend_window_projection(trend_window: Any) -> dict[str, Any]:
    payload = _to_public_dict(trend_window)
    if not payload:
        return {}
    intake_summary = payload.get("intake_trend_summary") or {}
    bodyweight_summary = payload.get("bodyweight_trend_summary") or {}
    readiness = payload.get("calibration_readiness") or {}
    return {
        "user_id": payload.get("user_id"),
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date"),
        "window_days": payload.get("window_days"),
        "logged_day_count": payload.get("logged_day_count"),
        "complete_logging_day_count": payload.get("complete_logging_day_count"),
        "partial_logging_day_count": payload.get("partial_logging_day_count"),
        "no_log_day_count": payload.get("no_log_day_count"),
        "intake_trend_summary": {
            "average_calories": intake_summary.get("average_calories"),
            "average_protein_g": intake_summary.get("average_protein_g"),
            "average_carbohydrate_g": intake_summary.get("average_carbohydrate_g"),
            "average_fat_g": intake_summary.get("average_fat_g"),
            "complete_logging_rate": intake_summary.get("complete_logging_rate"),
            "logging_consistency_status": intake_summary.get(
                "logging_consistency_status"
            ),
            "confidence": intake_summary.get("confidence"),
            "reason_codes": intake_summary.get("reason_codes", []),
            "limitations": intake_summary.get("limitations", []),
        },
        "bodyweight_trend_summary": {
            "weigh_in_count": bodyweight_summary.get("weigh_in_count"),
            "trend_direction": bodyweight_summary.get("trend_direction"),
            "weekly_rate_lb": bodyweight_summary.get("weekly_rate_lb"),
            "confidence": bodyweight_summary.get("confidence"),
            "reason_codes": bodyweight_summary.get("reason_codes", []),
            "limitations": bodyweight_summary.get("limitations", []),
        },
        "calibration_readiness": {
            "calibration_allowed": readiness.get("calibration_allowed"),
            "readiness_level": readiness.get("readiness_level"),
            "minimum_window_met": readiness.get("minimum_window_met"),
            "preferred_window_met": readiness.get("preferred_window_met"),
            "logging_quality_met": readiness.get("logging_quality_met"),
            "bodyweight_trend_available": readiness.get("bodyweight_trend_available"),
            "goal_context_available": readiness.get("goal_context_available"),
            "training_context_available": readiness.get("training_context_available"),
            "reason_codes": readiness.get("reason_codes", []),
            "limitations": readiness.get("limitations", []),
        },
        "confidence": payload.get("confidence"),
        "reason_codes": payload.get("reason_codes", []),
        "limitations": payload.get("limitations", []),
    }


def _calibration_projection(calibration_result: Any) -> dict[str, Any]:
    payload = _to_public_dict(calibration_result)
    if not payload:
        return {}
    return {
        "user_id": payload.get("user_id"),
        "calibration_date": payload.get("calibration_date"),
        "window_days": payload.get("window_days"),
        "calibration_allowed": payload.get("calibration_allowed"),
        "readiness_level": payload.get("readiness_level"),
        "recommended_action": payload.get("recommended_action"),
        "calibrated_targets": None,
        "confidence": payload.get("confidence"),
        "reason_codes": payload.get("reason_codes", []),
        "limitations": payload.get("limitations", []),
        "metadata": _calibration_metadata_projection(payload.get("metadata")),
    }


def _calibration_metadata_projection(metadata: Any) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    return {
        "service_name": metadata.get("service_name"),
        "service_version": metadata.get("service_version"),
        "inputs_used": metadata.get("inputs_used", []),
        "reason_codes": metadata.get("reason_codes", []),
        "limitations": metadata.get("limitations", []),
    }


def _candidate_summary(context: NutritionExplanationContext) -> str:
    if context.confidence in {"Moderate", "High"}:
        return "Approved nutrition context is available for this date."
    return "Nutrition explanation is limited because the approved context is limited for this date."


def _candidate_macro_context(context: NutritionExplanationContext) -> str | None:
    comparisons = context.target_vs_actual_summary.get("comparisons")
    if isinstance(comparisons, dict):
        protein = comparisons.get("protein")
        if isinstance(protein, dict) and protein.get("target_status") == "below_target":
            return "Based on today’s logged meals, protein is below target."
        return "Target-vs-Actual details are based on approved backend calculations."
    if context.approved_macro_targets:
        return "Targets are still formula-derived."
    return None


def _candidate_food_suggestion_context(
    context: NutritionExplanationContext,
) -> str | None:
    suggestions = context.approved_food_suggestions.get("suggestions")
    if isinstance(suggestions, list) and suggestions:
        return "The Nutrition tab has approved food suggestions that may help close the gap."
    reason_codes = context.approved_food_suggestions.get("reason_codes")
    if isinstance(reason_codes, list) and reason_codes:
        return "Food suggestions are limited by approved backend context for this date."
    return None


def _candidate_trend_context(context: NutritionExplanationContext) -> str | None:
    if context.trend_summary:
        return "Trend evidence is summarized from deterministic logged data."
    return None


def _candidate_calibration_context(context: NutritionExplanationContext) -> str | None:
    if context.calibration_summary:
        readiness = context.calibration_summary.get("readiness_level")
        if readiness in {"not_ready", "early_signal"}:
            return (
                "Targets are still formula-derived; more trend evidence may be needed."
            )
        return (
            "Targets are still formula-derived; calibration readiness is context only."
        )
    return None


def _candidate_limitations_context(context: NutritionExplanationContext) -> str | None:
    if context.limitations:
        return "Some explanation details are limited by approved context limitations."
    if context.confidence in {"Limited", "Low"}:
        return "Use the Nutrition tab for approved target, logging, trend, and calibration detail."
    return None


def _to_public_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    raise ValueError(
        f"Unsupported nutrition explanation context payload: {type(value)}"
    )


def _payload_confidence(payload: dict[str, Any]) -> str:
    confidence = payload.get("confidence")
    if confidence in _CONFIDENCE_RANK:
        return str(confidence)
    return "Limited" if payload else "High"


def _payload_list(payload: dict[str, Any], key: str) -> list[str]:
    values = payload.get(key)
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str) and value]


def _payload_mapping(payload: dict[str, Any], key: str) -> dict[str, bool]:
    value = payload.get(key)
    if not isinstance(value, dict):
        return {}
    return {
        str(map_key): map_value
        for map_key, map_value in value.items()
        if isinstance(map_value, bool)
    }


def _minimum_confidence(*values: str) -> str:
    valid = [value for value in values if value in _CONFIDENCE_RANK]
    if not valid:
        return "Limited"
    return min(valid, key=lambda value: _CONFIDENCE_RANK[value])


def _row_value(row: Any, field_name: str) -> Any:
    if row is None:
        return None
    if hasattr(row, "keys") and field_name in row.keys():
        return row[field_name]
    if isinstance(row, dict):
        return row.get(field_name)
    return getattr(row, field_name, None)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
