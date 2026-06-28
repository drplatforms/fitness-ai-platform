from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

from models.daily_coach_synthesis_models import DailyCoachSynthesis
from models.daily_coach_value_narrative_models import (
    DAILY_COACH_VALUE_NARRATIVE_SOURCE_DETERMINISTIC,
    DAILY_COACH_VALUE_NARRATIVE_SOURCE_DETERMINISTIC_FALLBACK,
    DAILY_COACH_VALUE_NARRATIVE_SOURCE_DIRECT_OLLAMA_APPROVED,
    DAILY_COACH_VALUE_NARRATIVE_SOURCE_OPENAI_APPROVED,
    DAILY_COACH_VALUE_NARRATIVE_STATUS_APPROVED,
    DAILY_COACH_VALUE_NARRATIVE_STATUS_NOT_ATTEMPTED,
    DAILY_COACH_VALUE_NARRATIVE_STATUS_REJECTED,
    DAILY_COACH_VALUE_NARRATIVE_VALIDATION_FAILED,
    DAILY_COACH_VALUE_NARRATIVE_VALIDATION_NOT_ATTEMPTED,
    DAILY_COACH_VALUE_NARRATIVE_VALIDATION_SUCCESS,
    ApprovedDailyCoachValueNarrative,
    ApprovedNarrativeValueClaim,
    CandidateDailyCoachValueNarrative,
    DailyCoachApprovedContextBriefSentence,
    DailyCoachClaimBackingGuide,
    DailyCoachTodayStory,
    DailyCoachValueNarrativeResult,
    DailyCoachValueNarrativeRuntimeMetadata,
    DailyCoachVerbosityBudget,
)
from services.daily_coach_narrative_validation_service import (
    parse_daily_coach_value_narrative_candidate,
    validate_daily_coach_value_narrative_candidate,
)
from services.daily_coach_synthesis_service import build_daily_coach_synthesis
from services.nutrition_food_suggestion_service import (
    build_approved_nutrition_food_suggestions,
)
from services.nutrition_target_vs_actual_service import (
    build_target_vs_actual_nutrition_summary,
)
from services.user_state_service import build_user_health_state

DAILY_COACH_VALUE_NARRATIVE_PROVIDER_ENV = "DAILY_COACH_NARRATIVE_PROVIDER"
DAILY_COACH_VALUE_NARRATIVE_MODEL_ENV = "DAILY_COACH_NARRATIVE_MODEL"
DAILY_COACH_VALUE_NARRATIVE_DIRECT_OLLAMA_TIMEOUT_ENV = (
    "DAILY_COACH_NARRATIVE_DIRECT_OLLAMA_TIMEOUT_SECONDS"
)
DAILY_COACH_VALUE_NARRATIVE_OPENAI_TIMEOUT_ENV = (
    "DAILY_COACH_NARRATIVE_OPENAI_TIMEOUT_SECONDS"
)
OLLAMA_BASE_URL_ENV = "OLLAMA_BASE_URL"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_BASE_URL_ENV = "OPENAI_BASE_URL"

PROVIDER_DETERMINISTIC = "deterministic"
PROVIDER_DIRECT_OLLAMA = "direct_ollama"
PROVIDER_OPENAI = "openai"

DEFAULT_DIRECT_OLLAMA_MODEL = "ollama/qwen3:8b"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"

DailyCoachNarrativeProviderCallable = Callable[[str, str, float], str]

_CANDIDATE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "headline",
        "summary",
        "nutrition_note",
        "training_note",
        "recovery_note",
        "priority_action",
        "confidence",
        "reason_codes",
        "quoted_values_used",
    ],
    "properties": {
        "headline": {"type": "string"},
        "summary": {"type": "string"},
        "nutrition_note": {"type": "string"},
        "training_note": {"type": "string"},
        "recovery_note": {"type": "string"},
        "priority_action": {"type": "string"},
        "confidence": {
            "type": "string",
            "enum": ["Limited", "Low", "Moderate", "High"],
        },
        "reason_codes": {"type": "array", "items": {"type": "string"}},
        "quoted_values_used": {"type": "array", "items": {"type": "string"}},
    },
}


_V3_HARD_FAIL_STYLE_PHRASES = {
    "main lever",
    "effort anchor",
    "planned effort range",
    "bigger nutrition overhaul",
    "backend-approved",
    "approved context",
    "claim keys",
    "validator",
    "schema",
    "json",
    "based on the provided data",
    "as an ai coach",
}

_V3_ROBOTIC_PHRASES = {
    "make nutrition support",
    "keep training controlled",
    "markers remain stable",
    "maintain current direction",
    "progress gradually",
    "supports confident training while staying inside",
}


class DailyCoachValueNarrativeError(ValueError):
    """Raised when Daily Coach value-aware narrative input is invalid."""


def build_configured_daily_coach_value_narrative(
    user_id: int,
    *,
    target_date: str | None = None,
    environ: Mapping[str, str] | None = None,
    direct_ollama_generate: DailyCoachNarrativeProviderCallable | None = None,
    openai_generate: DailyCoachNarrativeProviderCallable | None = None,
) -> DailyCoachValueNarrativeResult:
    """Build Daily Coach narrative using configured provider with fallback."""

    env = os.environ if environ is None else environ
    synthesis = build_daily_coach_synthesis(user_id)
    health_state = build_user_health_state(user_id)
    value_context = build_daily_coach_value_aware_provider_context(
        user_id=user_id,
        narrative_date=target_date or synthesis.synthesis_date,
        synthesis=synthesis,
        health_state=health_state,
    )
    return build_daily_coach_value_narrative_from_synthesis(
        synthesis,
        value_context=value_context,
        environ=env,
        direct_ollama_generate=direct_ollama_generate,
        openai_generate=openai_generate,
    )


def build_daily_coach_value_narrative_from_synthesis(
    synthesis: DailyCoachSynthesis,
    *,
    value_context: dict[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    direct_ollama_generate: DailyCoachNarrativeProviderCallable | None = None,
    openai_generate: DailyCoachNarrativeProviderCallable | None = None,
) -> DailyCoachValueNarrativeResult:
    env = os.environ if environ is None else environ
    configured_provider = _normalize_provider(
        env.get(DAILY_COACH_VALUE_NARRATIVE_PROVIDER_ENV)
    )
    configured_model = env.get(DAILY_COACH_VALUE_NARRATIVE_MODEL_ENV)
    value_context = value_context or build_minimal_value_context_from_synthesis(
        synthesis
    )
    _enrich_provider_context_packaging(value_context)

    if configured_provider == PROVIDER_DETERMINISTIC:
        approved = _deterministic_narrative(
            synthesis,
            source=DAILY_COACH_VALUE_NARRATIVE_SOURCE_DETERMINISTIC,
        )
        return _result(
            synthesis=synthesis,
            approved=approved,
            metadata=DailyCoachValueNarrativeRuntimeMetadata(
                configured_provider=PROVIDER_DETERMINISTIC,
                selected_provider=PROVIDER_DETERMINISTIC,
                configured_model=configured_model,
                selected_model=None,
                provider_attempted=False,
                fallback_used=False,
                fallback_reason=None,
                candidate_parse_status="not_attempted",
                candidate_validation_status=DAILY_COACH_VALUE_NARRATIVE_VALIDATION_NOT_ATTEMPTED,
                validation_status=DAILY_COACH_VALUE_NARRATIVE_STATUS_NOT_ATTEMPTED,
                final_narrative_source=DAILY_COACH_VALUE_NARRATIVE_SOURCE_DETERMINISTIC,
            ),
            value_context=value_context,
        )

    if configured_provider not in {PROVIDER_DIRECT_OLLAMA, PROVIDER_OPENAI}:
        return _fallback_result(
            synthesis=synthesis,
            value_context=value_context,
            configured_provider=env.get(DAILY_COACH_VALUE_NARRATIVE_PROVIDER_ENV) or "",
            selected_provider=PROVIDER_DETERMINISTIC,
            configured_model=configured_model,
            selected_model=None,
            provider_attempted=False,
            fallback_reason="invalid_provider",
            candidate_parse_status="not_attempted",
            candidate_validation_status=DAILY_COACH_VALUE_NARRATIVE_VALIDATION_NOT_ATTEMPTED,
            validation_status=DAILY_COACH_VALUE_NARRATIVE_STATUS_NOT_ATTEMPTED,
        )

    selected_model = _selected_model(configured_provider, configured_model)
    prompt = build_daily_coach_value_narrative_prompt(
        synthesis,
        value_context=value_context,
    )
    timeout_seconds = _provider_timeout(configured_provider, env)
    provider_generate = _resolve_provider_generate(
        configured_provider,
        env,
        direct_ollama_generate=direct_ollama_generate,
        openai_generate=openai_generate,
    )

    try:
        raw_output = provider_generate(selected_model, prompt, timeout_seconds)
    except Exception as exc:
        return _fallback_result(
            synthesis=synthesis,
            value_context=value_context,
            configured_provider=configured_provider,
            selected_provider=configured_provider,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=True,
            fallback_reason=_provider_exception_reason(configured_provider, exc),
            candidate_parse_status="not_attempted",
            candidate_validation_status=DAILY_COACH_VALUE_NARRATIVE_VALIDATION_NOT_ATTEMPTED,
            validation_status=DAILY_COACH_VALUE_NARRATIVE_STATUS_NOT_ATTEMPTED,
            raw_output=None,
        )

    markdown_wrapper_detected = _markdown_wrapper_detected(raw_output)
    candidate, parse_error = parse_daily_coach_value_narrative_candidate(raw_output)
    if candidate is None:
        return _fallback_result(
            synthesis=synthesis,
            value_context=value_context,
            configured_provider=configured_provider,
            selected_provider=configured_provider,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=True,
            fallback_reason=parse_error or "candidate_parse_failure",
            candidate_parse_status="failed",
            candidate_validation_status=DAILY_COACH_VALUE_NARRATIVE_VALIDATION_NOT_ATTEMPTED,
            validation_status=DAILY_COACH_VALUE_NARRATIVE_STATUS_NOT_ATTEMPTED,
            raw_output=raw_output,
            markdown_wrapper_detected=markdown_wrapper_detected,
        )

    validation_errors = validate_daily_coach_value_narrative_candidate(
        candidate,
        synthesis=synthesis,
        value_context=value_context,
    )
    if validation_errors:
        return _fallback_result(
            synthesis=synthesis,
            value_context=value_context,
            configured_provider=configured_provider,
            selected_provider=configured_provider,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=True,
            fallback_reason="candidate_validation_failure",
            candidate_parse_status="success",
            candidate_validation_status=DAILY_COACH_VALUE_NARRATIVE_VALIDATION_FAILED,
            validation_status=DAILY_COACH_VALUE_NARRATIVE_STATUS_REJECTED,
            raw_output=raw_output,
            markdown_wrapper_detected=markdown_wrapper_detected,
            validation_errors=validation_errors,
        )

    final_source = (
        DAILY_COACH_VALUE_NARRATIVE_SOURCE_DIRECT_OLLAMA_APPROVED
        if configured_provider == PROVIDER_DIRECT_OLLAMA
        else DAILY_COACH_VALUE_NARRATIVE_SOURCE_OPENAI_APPROVED
    )
    approved = _approved_from_candidate(candidate, synthesis, source=final_source)
    return _result(
        synthesis=synthesis,
        approved=approved,
        metadata=DailyCoachValueNarrativeRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=configured_provider,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=True,
            fallback_used=False,
            fallback_reason=None,
            candidate_parse_status="success",
            candidate_validation_status=DAILY_COACH_VALUE_NARRATIVE_VALIDATION_SUCCESS,
            validation_status=DAILY_COACH_VALUE_NARRATIVE_STATUS_APPROVED,
            final_narrative_source=final_source,
            raw_output_length=len(raw_output),
            raw_output_preview_truncated=False,
            markdown_wrapper_detected=markdown_wrapper_detected,
        ),
        value_context=value_context,
    )


def build_daily_coach_value_aware_provider_context(
    *,
    user_id: int,
    narrative_date: str,
    synthesis: DailyCoachSynthesis,
    health_state: Any,
) -> dict[str, Any]:
    """Build compact backend-approved value context for provider candidates."""

    context = {
        "user_id": user_id,
        "narrative_date": narrative_date,
        "daily_coach_synthesis": _synthesis_provider_context(synthesis),
        "approved_recovery": _approved_recovery_context(health_state, synthesis),
        "approved_nutrition": _approved_nutrition_context(user_id, narrative_date),
        "approved_training": _approved_training_context(synthesis),
        "approved_limitations": list(synthesis.limitations),
        "approved_reason_codes": _bounded_list(synthesis.reason_codes, limit=12),
    }
    context["approved_value_claims"] = _build_approved_value_claims(context)
    _enrich_provider_context_packaging(context)
    return context


def build_minimal_value_context_from_synthesis(
    synthesis: DailyCoachSynthesis,
) -> dict[str, Any]:
    context = {
        "user_id": synthesis.user_id,
        "narrative_date": synthesis.synthesis_date,
        "daily_coach_synthesis": _synthesis_provider_context(synthesis),
        "approved_recovery": {"recovery_signal": synthesis.recovery_signal},
        "approved_nutrition": {},
        "approved_training": _approved_training_context(synthesis),
        "approved_limitations": list(synthesis.limitations),
        "approved_reason_codes": _bounded_list(synthesis.reason_codes, limit=12),
    }
    context["approved_value_claims"] = _build_approved_value_claims(context)
    _enrich_provider_context_packaging(context)
    return context


def build_daily_coach_value_narrative_prompt(
    synthesis: DailyCoachSynthesis,
    *,
    value_context: dict[str, Any],
) -> str:
    example = {
        "headline": "Clean Strength Day",
        "summary": "You are clear to train today, but nutrition should not be ignored.",
        "nutrition_note": "Protein is the easiest fix today; use one approved option if it fits your meals.",
        "training_note": "Keep a couple reps in reserve and make clean execution the win.",
        "recovery_note": "Readiness is High and fatigue risk is Low, so you do not need to back off today.",
        "priority_action": "Get the planned strength session done cleanly, then choose one simple approved protein option.",
        "confidence": synthesis.confidence,
        "reason_codes": ["provider_candidate_value_aware"],
        "quoted_values_used": [
            "recovery.readiness_level",
            "recovery.fatigue_risk",
            "nutrition.protein.status",
            "training.rir_range",
        ],
    }
    _enrich_provider_context_packaging(value_context)
    field_roles = value_context.get("field_role_guidance") or _field_role_guidance()
    approved_context_brief = value_context.get("approved_context_brief") or {}
    claim_backing_map = value_context.get("claim_backing_map") or {}
    verbosity_budget = value_context.get("verbosity_budget") or {}
    voice_examples = value_context.get("voice_examples") or _voice_examples()
    claim_rules = value_context.get("claim_usage_rules") or _claim_usage_rules(
        value_context.get("claim_budgets")
        or _claim_budgets(
            value_context,
            _display_allowed_claims(value_context.get("approved_value_claims") or []),
            _build_today_story(
                value_context,
                _display_allowed_claims(
                    value_context.get("approved_value_claims") or []
                ),
            ),
        )
    )
    today_story_payload = {
        "today_story": value_context.get("today_story"),
        "claim_budgets": value_context.get("claim_budgets"),
        "adaptive_verbosity_guidance": value_context.get("adaptive_verbosity_guidance"),
    }
    return (
        "Write a Daily Coach card from the supplied safe facts and context.\n"
        "The voice should sound like a real practical coach talking to a person.\n"
        "Target useful, grounded, scannable coaching; not maximum brevity and not a report.\n"
        "Use approved_context_brief as the conversation starter, then rewrite naturally instead of copying backend-shaped phrases.\n"
        "Use 3-6 high-value approved claims when context is rich; use fewer when context is thin, limited, or data-quality-limited.\n"
        "Use verbosity_budget to decide length. Allow more words only when they improve usefulness, connect nutrition/training/recovery, or clarify the priority action.\n"
        "Do not pad, repeat metrics, or turn the card into a report.\n"
        "Prefer claim_backing_map allowed phrasings for natural language. Avoid every disallowed phrasing.\n"
        "Do not dump all claims. Prefer normal coach language over framework language.\n"
        "Use limitations as uncertainty/context, not as user blame.\n"
        "Do not mention backend, approved context, validator, schema, provider, JSON, claim keys, or internal process in user-facing fields.\n"
        "Every concrete value/status/food/amount used in prose must be declared in quoted_values_used.\n"
        "quoted_values_used may contain only exact keys from approved_value_claims. Never use food names, amounts, or phrases as quote keys.\n"
        "Return one raw JSON object only. No markdown, no code fences, no prose wrapper, no extra keys.\n"
        "Do not calculate targets, gaps, readiness, fatigue, servings, or nutrition values.\n"
        "Do not say recovery is missing when recovery_signal or approved recovery values exist.\n"
        "Do not say the user is under-eating unless that exact claim is approved.\n"
        "Do not say the user needs calories unless calorie targets are display-approved.\n"
        "Do not prescribe exact food amounts unless approved food suggestions include those amounts.\n"
        "Avoid these robotic phrases in user-facing fields: main lever, effort anchor, planned effort range, bigger nutrition overhaul, based on the provided data, as an AI coach.\n\n"
        "APPROVED_CONTEXT_BRIEF:\n"
        f"{json.dumps(approved_context_brief, indent=2, default=str)}\n\n"
        "CLAIM_BACKING_MAP:\n"
        f"{json.dumps(claim_backing_map, indent=2, default=str)}\n\n"
        "VOICE_EXAMPLES:\n"
        f"{json.dumps(voice_examples, indent=2, default=str)}\n\n"
        "VERBOSITY_BUDGET:\n"
        f"{json.dumps(verbosity_budget, indent=2, default=str)}\n\n"
        "FIELD_ROLE_GUIDANCE:\n"
        f"{json.dumps(field_roles, indent=2, default=str)}\n\n"
        "CLAIM_USAGE_RULES:\n"
        f"{json.dumps(claim_rules, indent=2, default=str)}\n\n"
        "TODAY_STORY_AND_CLAIM_BUDGETS:\n"
        f"{json.dumps(today_story_payload, indent=2, default=str)}\n\n"
        "REQUIRED_JSON_SCHEMA:\n"
        f"{json.dumps(_CANDIDATE_SCHEMA, indent=2)}\n\n"
        "VALID_EXAMPLE_SHAPE_ONLY:\n"
        f"{json.dumps(example, indent=2)}\n\n"
        "approved_value_context:\n"
        f"{json.dumps(value_context, indent=2, default=str)}\n\n"
        "Return the JSON object now."
    )


def call_direct_ollama_daily_coach_narrative(
    model_name: str,
    prompt: str,
    timeout_seconds: float,
    *,
    ollama_base_url: str | None = None,
) -> str:
    base_url = (
        ollama_base_url or os.getenv(OLLAMA_BASE_URL_ENV) or DEFAULT_OLLAMA_BASE_URL
    ).rstrip("/")
    selected_model = _normalize_ollama_model(model_name)
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "format": _CANDIDATE_SCHEMA,
        "options": {"temperature": 0.1},
    }
    request = urllib.request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        response_payload = json.loads(response.read().decode("utf-8"))
    raw_text = response_payload.get("response")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise DailyCoachValueNarrativeError("direct_ollama_missing_response")
    return raw_text


def call_openai_daily_coach_narrative(
    model_name: str,
    prompt: str,
    timeout_seconds: float,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    resolved_api_key = api_key or os.getenv(OPENAI_API_KEY_ENV)
    if not resolved_api_key:
        raise DailyCoachValueNarrativeError("openai_missing_api_key")

    client_kwargs: dict[str, Any] = {"api_key": resolved_api_key}
    configured_base_url = base_url or os.getenv(OPENAI_BASE_URL_ENV)
    if configured_base_url:
        client_kwargs["base_url"] = configured_base_url.rstrip("/")

    try:
        from openai import OpenAI

        client = OpenAI(**client_kwargs)
        response = client.responses.create(
            model=model_name,
            instructions="Return exact JSON only for the requested schema.",
            input=prompt,
            max_output_tokens=1200,
            timeout=timeout_seconds,
        )
    except Exception as exc:  # pragma: no cover - exercised via mocked SDK tests
        reason = _classify_openai_provider_exception(exc)
        raise DailyCoachValueNarrativeError(reason) from exc

    raw_text = _extract_openai_response_text(response)
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise DailyCoachValueNarrativeError("openai_missing_response")
    return raw_text


def _extract_openai_response_text(response: Any) -> str | None:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output = getattr(response, "output", None)
    if not isinstance(output, list):
        return output_text if isinstance(output_text, str) else None

    text_parts: list[str] = []
    for item in output:
        content = getattr(item, "content", None)
        if not isinstance(content, list):
            continue
        for part in content:
            text = getattr(part, "text", None)
            if isinstance(text, str):
                text_parts.append(text)
    return "".join(text_parts) or (
        output_text if isinstance(output_text, str) else None
    )


def _classify_openai_provider_exception(exc: Exception) -> str:
    text = str(exc).lower()
    class_name = exc.__class__.__name__.lower()
    status_code = getattr(exc, "status_code", None)
    error_code = _openai_error_code(exc)

    if (
        status_code in {401, 403}
        or "authentication" in class_name
        or "permissiondenied" in class_name
        or "invalid api key" in text
        or "incorrect api key" in text
        or "authentication" in text
    ):
        return "openai_authentication_failed"
    if (
        status_code == 404
        or error_code == "model_not_found"
        or "model_not_found" in text
        or "model not found" in text
        or "does not exist" in text
    ):
        return "openai_model_not_found"
    if (
        error_code == "insufficient_quota"
        or "insufficient_quota" in text
        or "insufficient quota" in text
        or "quota" in text
    ):
        return "openai_insufficient_quota"
    if status_code == 429 or "ratelimit" in class_name or "rate limit" in text:
        return "openai_rate_limited"
    if "timeout" in class_name or "timed out" in text or "timeout" in text:
        return "openai_timeout"
    if "connection" in class_name or "network" in text or "connection" in text:
        return "openai_connection_error"
    if status_code is not None:
        return "openai_api_response_error"
    return "openai_provider_error"


def _openai_error_code(exc: Exception) -> str | None:
    code = getattr(exc, "code", None)
    if isinstance(code, str):
        return code.lower()
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            body_code = error.get("code")
            if isinstance(body_code, str):
                return body_code.lower()
    return None


def _resolve_provider_generate(
    provider: str,
    env: Mapping[str, str],
    *,
    direct_ollama_generate: DailyCoachNarrativeProviderCallable | None,
    openai_generate: DailyCoachNarrativeProviderCallable | None,
) -> DailyCoachNarrativeProviderCallable:
    if provider == PROVIDER_DIRECT_OLLAMA:
        if direct_ollama_generate is not None:
            return direct_ollama_generate

        def generate(model: str, prompt: str, timeout: float) -> str:
            return call_direct_ollama_daily_coach_narrative(
                model,
                prompt,
                timeout,
                ollama_base_url=env.get(OLLAMA_BASE_URL_ENV),
            )

        return generate

    if provider == PROVIDER_OPENAI:
        if openai_generate is not None:
            return openai_generate

        def generate(model: str, prompt: str, timeout: float) -> str:
            api_key = env.get(OPENAI_API_KEY_ENV)
            if not api_key:
                raise DailyCoachValueNarrativeError("openai_missing_api_key")
            return call_openai_daily_coach_narrative(
                model,
                prompt,
                timeout,
                api_key=api_key,
                base_url=env.get(OPENAI_BASE_URL_ENV),
            )

        return generate

    raise DailyCoachValueNarrativeError("unsupported_provider")


def _deterministic_narrative(
    synthesis: DailyCoachSynthesis,
    *,
    source: str,
) -> ApprovedDailyCoachValueNarrative:
    return ApprovedDailyCoachValueNarrative(
        headline="Daily Coach",
        summary=synthesis.today_summary,
        nutrition_note=synthesis.logging_focus,
        training_note=synthesis.workout_guidance,
        recovery_note=synthesis.recovery_signal,
        priority_action=synthesis.recommended_focus,
        confidence=synthesis.confidence,
        source=source,
        reason_codes=_bounded_list(
            ["daily_coach_value_narrative_deterministic"] + synthesis.reason_codes,
            limit=16,
        ),
        limitations=list(synthesis.limitations),
        quoted_values_used=[],
    )


def _approved_from_candidate(
    candidate: CandidateDailyCoachValueNarrative,
    synthesis: DailyCoachSynthesis,
    *,
    source: str,
) -> ApprovedDailyCoachValueNarrative:
    return ApprovedDailyCoachValueNarrative(
        headline=candidate.headline,
        summary=candidate.summary,
        nutrition_note=candidate.nutrition_note,
        training_note=candidate.training_note,
        recovery_note=candidate.recovery_note,
        priority_action=candidate.priority_action,
        confidence=candidate.confidence,
        source=source,
        reason_codes=_bounded_list(
            ["daily_coach_value_narrative_provider_approved"] + candidate.reason_codes,
            limit=16,
        ),
        limitations=list(synthesis.limitations),
        quoted_values_used=list(candidate.quoted_values_used),
    )


def render_daily_coach_value_narrative(
    narrative: ApprovedDailyCoachValueNarrative,
) -> str:
    return "\n".join(
        [
            f"## {narrative.headline}",
            f"**What matters today:** {narrative.summary}",
            f"**Nutrition:** {narrative.nutrition_note}",
            f"**Training:** {narrative.training_note}",
            f"**Recovery:** {narrative.recovery_note}",
            f"**Priority action:** {narrative.priority_action}",
        ]
    )


def _fallback_result(
    *,
    synthesis: DailyCoachSynthesis,
    value_context: dict[str, Any],
    configured_provider: str,
    selected_provider: str,
    configured_model: str | None,
    selected_model: str | None,
    provider_attempted: bool,
    fallback_reason: str,
    candidate_parse_status: str,
    candidate_validation_status: str,
    validation_status: str,
    raw_output: str | None = None,
    markdown_wrapper_detected: bool = False,
    validation_errors: list[str] | None = None,
) -> DailyCoachValueNarrativeResult:
    approved = _deterministic_narrative(
        synthesis,
        source=DAILY_COACH_VALUE_NARRATIVE_SOURCE_DETERMINISTIC_FALLBACK,
    )
    return _result(
        synthesis=synthesis,
        approved=approved,
        metadata=DailyCoachValueNarrativeRuntimeMetadata(
            configured_provider=configured_provider,
            selected_provider=selected_provider,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=provider_attempted,
            fallback_used=True,
            fallback_reason=fallback_reason,
            candidate_parse_status=candidate_parse_status,
            candidate_validation_status=candidate_validation_status,
            validation_status=validation_status,
            final_narrative_source=DAILY_COACH_VALUE_NARRATIVE_SOURCE_DETERMINISTIC_FALLBACK,
            raw_output_length=len(raw_output) if raw_output is not None else None,
            raw_output_preview_truncated=False if raw_output is not None else None,
            markdown_wrapper_detected=markdown_wrapper_detected,
            validation_errors=validation_errors or [],
        ),
        value_context=value_context,
    )


def _result(
    *,
    synthesis: DailyCoachSynthesis,
    approved: ApprovedDailyCoachValueNarrative,
    metadata: DailyCoachValueNarrativeRuntimeMetadata,
    value_context: dict[str, Any],
) -> DailyCoachValueNarrativeResult:
    return DailyCoachValueNarrativeResult(
        user_id=synthesis.user_id,
        narrative_date=synthesis.synthesis_date,
        approved_daily_coach_narrative=approved,
        rendered_narrative=render_daily_coach_value_narrative(approved),
        runtime_metadata=metadata,
        provider_context_summary=_provider_context_summary(value_context),
    )


def _synthesis_provider_context(synthesis: DailyCoachSynthesis) -> dict[str, Any]:
    return {
        "scenario": synthesis.scenario,
        "confidence": synthesis.confidence,
        "today_summary": synthesis.today_summary,
        "recovery_signal": synthesis.recovery_signal,
        "training_signal": synthesis.training_signal,
        "workout_guidance": synthesis.workout_guidance,
        "execution_context": synthesis.execution_context,
        "logging_focus": synthesis.logging_focus,
        "plan_fit_note": synthesis.plan_fit_note,
        "recommended_focus": synthesis.recommended_focus,
    }


def _approved_recovery_context(
    health_state: Any, synthesis: DailyCoachSynthesis
) -> dict[str, Any]:
    recovery = getattr(health_state, "recovery_state", None)
    return _compact_dict(
        {
            "readiness_level": getattr(recovery, "readiness_level", None),
            "fatigue_risk": getattr(recovery, "fatigue_risk", None),
            "recovery_score": getattr(recovery, "recovery_score", None),
            "avg_sleep": getattr(recovery, "avg_sleep", None),
            "avg_energy": getattr(recovery, "avg_energy", None),
            "avg_soreness": getattr(recovery, "avg_soreness", None),
            "recovery_signal": synthesis.recovery_signal,
        }
    )


def _approved_training_context(synthesis: DailyCoachSynthesis) -> dict[str, Any]:
    return {
        "training_signal": synthesis.training_signal,
        "workout_guidance": synthesis.workout_guidance,
        "execution_context": synthesis.execution_context,
        "plan_fit_note": synthesis.plan_fit_note,
    }


def _approved_nutrition_context(user_id: int, narrative_date: str) -> dict[str, Any]:
    try:
        summary = build_target_vs_actual_nutrition_summary(user_id, narrative_date)
    except Exception:
        return {"available": False}

    context: dict[str, Any] = {
        "available": True,
        "date": summary.date,
        "logging_completeness": summary.logging_completeness,
        "confidence": summary.confidence,
        "actuals": _compact_dict(summary.nutrition_actuals.to_dict()),
        "macro_status": {},
        "limitations": list(summary.limitations),
    }
    for macro_name, comparison in summary.comparisons.items():
        context["macro_status"][macro_name] = _compact_dict(
            {
                "actual": comparison.actual,
                "target_min": comparison.target_min,
                "target_max": comparison.target_max,
                "delta_min": comparison.delta_min,
                "delta_max": comparison.delta_max,
                "target_status": comparison.target_status,
                "display_allowed": comparison.comparison_available,
                "confidence": comparison.confidence,
                "limitations": comparison.limitations,
            }
        )

    try:
        suggestions = build_approved_nutrition_food_suggestions(
            user_id,
            narrative_date,
            target_vs_actual_summary=summary,
            limit=3,
        )
    except Exception:
        suggestions = None
    if suggestions is not None:
        context["approved_food_suggestions"] = [
            _compact_dict(
                {
                    "display_name": suggestion.display_name,
                    "suggested_grams": suggestion.suggested_grams,
                    "estimated_calories": suggestion.estimated_calories,
                    "estimated_protein_g": suggestion.estimated_protein_g,
                    "estimated_carbohydrate_g": suggestion.estimated_carbohydrate_g,
                    "estimated_fat_g": suggestion.estimated_fat_g,
                    "macro_gap_addressed": suggestion.macro_gap_addressed,
                    "confidence": suggestion.confidence,
                    "summary": suggestion.suggestion_summary,
                }
            )
            for suggestion in suggestions.suggestions[:3]
        ]
        context["food_suggestion_confidence"] = suggestions.confidence
        context["food_suggestion_limitations"] = list(suggestions.limitations)
    return context


def _build_approved_value_claims(context: dict[str, Any]) -> list[dict[str, Any]]:
    claims: list[ApprovedNarrativeValueClaim] = []
    confidence = context.get("daily_coach_synthesis", {}).get("confidence")
    recovery = context.get("approved_recovery") or {}
    if isinstance(recovery, dict):
        _add_claim(
            claims,
            key="recovery.readiness_level",
            label="readiness",
            value=recovery.get("readiness_level"),
            claim_type="recovery",
            aliases=[f"readiness is {recovery.get('readiness_level')}"],
            source="approved_recovery",
            confidence=confidence,
            priority=1,
            section_hint="recovery_note",
            coaching_use="support_recovery_action",
            display_hint="Use as a status, not as a medical conclusion.",
            value_style="status_only",
        )
        _add_claim(
            claims,
            key="recovery.fatigue_risk",
            label="fatigue risk",
            value=recovery.get("fatigue_risk"),
            claim_type="recovery",
            aliases=[f"fatigue risk is {recovery.get('fatigue_risk')}"],
            source="approved_recovery",
            confidence=confidence,
            priority=1,
            section_hint="recovery_note",
            coaching_use="support_recovery_action",
            display_hint="Use to explain training confidence without overclaiming.",
            value_style="status_only",
        )
        _add_claim(
            claims,
            key="recovery.recovery_score",
            label="recovery score",
            value=recovery.get("recovery_score"),
            claim_type="recovery",
            aliases=[
                f"recovery score is {recovery.get('recovery_score')}",
                str(recovery.get("recovery_score")),
            ],
            source="approved_recovery",
            confidence=confidence,
            priority=2,
            section_hint="recovery_note",
            coaching_use="support_recovery_action",
            display_hint="Use only if a score helps; status language is preferred.",
            value_style="exact_value_allowed",
        )
        for key, label in [
            ("avg_sleep", "average sleep"),
            ("avg_energy", "average energy"),
            ("avg_soreness", "average soreness"),
        ]:
            value = recovery.get(key)
            _add_claim(
                claims,
                key=f"recovery.{key}",
                label=label,
                value=value,
                claim_type="recovery",
                aliases=[str(value), f"{label} {value}"],
                source="approved_recovery",
                confidence=confidence,
                priority=3,
                section_hint="recovery_note",
                coaching_use="support_recovery_action",
                display_hint="Supporting recovery detail; avoid fact dumping.",
                value_style="exact_value_allowed",
            )

    nutrition = context.get("approved_nutrition") or {}
    if isinstance(nutrition, dict):
        actuals = nutrition.get("actuals") or {}
        if isinstance(actuals, dict):
            for key, label, unit in [
                ("logged_calories", "logged calories", "kcal"),
                ("logged_protein_g", "logged protein", "g"),
                ("logged_carbs_g", "logged carbohydrates", "g"),
                ("logged_fat_g", "logged fat", "g"),
            ]:
                value = actuals.get(key)
                priority = 2 if key == "logged_protein_g" else 3
                _add_claim(
                    claims,
                    key=f"nutrition.actuals.{key}",
                    label=label,
                    value=value,
                    unit=unit,
                    claim_type="nutrition_actual",
                    aliases=[
                        _format_value_alias(value, unit),
                        f"{label} {_format_value_alias(value, unit)}",
                    ],
                    source="target_vs_actual_summary",
                    confidence=nutrition.get("confidence"),
                    priority=priority,
                    section_hint="nutrition_note",
                    coaching_use="support_nutrition_action",
                    display_hint="Use exact logged amount only when it improves specificity.",
                    value_style="exact_value_allowed",
                )
        macro_status = nutrition.get("macro_status") or {}
        if isinstance(macro_status, dict):
            for macro_name, macro in macro_status.items():
                if not isinstance(macro, dict):
                    continue
                display_allowed = bool(macro.get("display_allowed"))
                target_status = macro.get("target_status")
                priority = 1 if macro_name == "protein" else 2
                _add_claim(
                    claims,
                    key=f"nutrition.{macro_name}.status",
                    label=f"{macro_name} status",
                    value=target_status,
                    claim_type="nutrition_gap",
                    aliases=[
                        f"{macro_name} is {target_status}",
                        f"{macro_name} {target_status}",
                    ],
                    display_allowed=display_allowed,
                    source="target_vs_actual_summary",
                    confidence=macro.get("confidence") or nutrition.get("confidence"),
                    priority=priority,
                    section_hint=(
                        "nutrition_note" if macro_name != "calories" else "summary"
                    ),
                    coaching_use="support_nutrition_action",
                    display_hint="Use as a qualitative status; avoid turning it into a new target.",
                    value_style="status_only",
                )
                for key in ["target_min", "target_max", "delta_min", "delta_max"]:
                    _add_claim(
                        claims,
                        key=f"nutrition.{macro_name}.{key}",
                        label=f"{macro_name} {key}",
                        value=macro.get(key),
                        unit="kcal" if macro_name == "calories" else "g",
                        claim_type=(
                            "nutrition_target" if "target" in key else "nutrition_gap"
                        ),
                        aliases=[
                            _format_value_alias(
                                macro.get(key),
                                "kcal" if macro_name == "calories" else "g",
                            )
                        ],
                        display_allowed=display_allowed,
                        source="target_vs_actual_summary",
                        confidence=macro.get("confidence")
                        or nutrition.get("confidence"),
                        priority=3,
                        section_hint="nutrition_note",
                        coaching_use="support_nutrition_action",
                        display_hint="Low-priority exact value; use only if clearly helpful.",
                        value_style="exact_value_allowed",
                    )
        suggestions = nutrition.get("approved_food_suggestions") or []
        if isinstance(suggestions, list):
            for index, suggestion in enumerate(suggestions[:3], start=1):
                if not isinstance(suggestion, dict):
                    continue
                prefix = f"nutrition.food_suggestion.{index}"
                display_name = suggestion.get("display_name")
                _add_claim(
                    claims,
                    key=f"{prefix}.display_name",
                    label="food suggestion",
                    value=display_name,
                    claim_type="recommendation",
                    aliases=[str(display_name)],
                    source="approved_food_suggestions",
                    confidence=suggestion.get("confidence")
                    or nutrition.get("food_suggestion_confidence"),
                    priority=2,
                    section_hint="priority_action",
                    coaching_use="prioritize_action",
                    display_hint="Use as an option, not a command.",
                    value_style="food_option",
                )
                _add_claim(
                    claims,
                    key=f"{prefix}.suggested_grams",
                    label="suggested grams",
                    value=suggestion.get("suggested_grams"),
                    unit="g",
                    claim_type="recommendation",
                    aliases=[
                        _format_value_alias(suggestion.get("suggested_grams"), "g")
                    ],
                    source="approved_food_suggestions",
                    confidence=suggestion.get("confidence")
                    or nutrition.get("food_suggestion_confidence"),
                    priority=3,
                    section_hint="priority_action",
                    coaching_use="prioritize_action",
                    display_hint="Use only when the approved serving amount matters.",
                    value_style="exact_value_allowed",
                )

    training = context.get("approved_training") or {}
    if isinstance(training, dict):
        training_text = " ".join(str(value) for value in training.values() if value)
        rir_match = re.search(
            r"RIR\s*(\d+(?:\.\d+)?)\s*[-ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“]\s*(\d+(?:\.\d+)?)",
            training_text,
            re.IGNORECASE,
        )
        if rir_match:
            rir_value = f"{rir_match.group(1)}-{rir_match.group(2)}"
            _add_claim(
                claims,
                key="training.rir_range",
                label="RIR range",
                value=rir_value,
                claim_type="training",
                aliases=[
                    f"RIR {rir_value}",
                    f"RIR {rir_match.group(1)}-{rir_match.group(2)}",
                ],
                source="daily_coach_synthesis",
                confidence=confidence,
                priority=1,
                section_hint="training_note",
                coaching_use="support_training_action",
                display_hint="Use as an effort range; prefer natural language such as a couple reps in reserve.",
                value_style="range_allowed",
            )

    for index, limitation in enumerate(
        context.get("approved_limitations") or [], start=1
    ):
        _add_claim(
            claims,
            key=f"limitation.{index}",
            label="limitation",
            value=limitation,
            claim_type="limitation",
            aliases=[str(limitation)],
            source="daily_coach_synthesis",
            confidence=confidence,
            priority=2,
            section_hint="summary",
            coaching_use="contextualize_limit",
            display_hint="Use as uncertainty/context, not as user blame.",
            value_style="limitation_only",
        )
    return [claim.to_dict() for claim in claims]


def _add_claim(
    claims: list[ApprovedNarrativeValueClaim],
    *,
    key: str,
    label: str,
    value: Any,
    claim_type: str,
    unit: str | None = None,
    aliases: list[str] | None = None,
    display_allowed: bool = True,
    source: str,
    confidence: str | None = None,
    priority: int = 3,
    section_hint: str | None = None,
    coaching_use: str | None = None,
    display_hint: str | None = None,
    value_style: str | None = None,
) -> None:
    if value is None:
        return
    if isinstance(value, str) and value in {"", "Unknown", "unknown"}:
        return
    claims.append(
        ApprovedNarrativeValueClaim(
            key=key,
            label=label,
            value=value,
            unit=unit,
            aliases=[
                alias for alias in (aliases or []) if alias and "None" not in str(alias)
            ],
            claim_type=claim_type,  # type: ignore[arg-type]
            display_allowed=display_allowed,
            source=source,
            confidence=confidence,
            priority=max(1, min(3, int(priority))),
            section_hint=section_hint,  # type: ignore[arg-type]
            coaching_use=coaching_use,  # type: ignore[arg-type]
            display_hint=display_hint,
            value_style=value_style,  # type: ignore[arg-type]
        )
    )


def _enrich_provider_context_packaging(context: dict[str, Any]) -> None:
    if not isinstance(context.get("approved_value_claims"), list):
        context["approved_value_claims"] = _build_approved_value_claims(context)
    claims = _display_allowed_claims(context.get("approved_value_claims") or [])
    today_story = _build_today_story(context, claims)
    claim_budgets = _claim_budgets(context, claims, today_story)
    verbosity_budget = _verbosity_budget(context, claims, today_story)
    context["today_story"] = today_story.to_dict()
    context["claim_budgets"] = claim_budgets
    context["verbosity_budget"] = verbosity_budget.to_dict()
    context["approved_context_brief"] = _approved_context_brief(
        context, claims, today_story
    )
    context["claim_backing_map"] = _claim_backing_map(claims)
    context["voice_examples"] = _voice_examples()
    context["adaptive_verbosity_guidance"] = _adaptive_verbosity_guidance(
        context, claims, claim_budgets, verbosity_budget
    )
    context["provider_task_context"] = _provider_task_context(
        context, claims, claim_budgets
    )
    context["high_value_claims"] = _high_value_claim_keys(
        claims, max_claims=int(claim_budgets["total"]["max"])
    )
    context["preferred_claims_by_field"] = _preferred_claims_by_field(
        claims, claim_budgets
    )
    context["claim_usage_rules"] = _claim_usage_rules(claim_budgets)
    context["field_role_guidance"] = _field_role_guidance()


def _build_today_story(
    context: dict[str, Any], claims: list[dict[str, Any]]
) -> DailyCoachTodayStory:
    claim_keys = {str(claim.get("key")) for claim in claims}
    synthesis = context.get("daily_coach_synthesis") or {}
    limitations = context.get("approved_limitations") or []
    food_keys = [
        key for key in claim_keys if key.startswith("nutrition.food_suggestion")
    ]
    calories_key = (
        "nutrition.calories.status"
        if "nutrition.calories.status" in claim_keys
        else None
    )
    protein_key = (
        "nutrition.protein.status" if "nutrition.protein.status" in claim_keys else None
    )
    rir_key = "training.rir_range" if "training.rir_range" in claim_keys else None
    readiness_key = (
        "recovery.readiness_level" if "recovery.readiness_level" in claim_keys else None
    )
    fatigue_key = (
        "recovery.fatigue_risk" if "recovery.fatigue_risk" in claim_keys else None
    )
    limitation_keys = [key for key in claim_keys if key.startswith("limitation.")]
    has_recovery = bool(readiness_key or fatigue_key)
    has_training = bool(rir_key)
    has_nutrition = bool(calories_key or protein_key or food_keys)
    data_limited = _context_is_data_quality_limited(context)

    if data_limited:
        day_type = "data_quality_check"
        human_label = "Logging Check Day"
        main_tension = (
            "Useful context exists, but logging quality limits stronger conclusions."
        )
        desired_move = "Keep the advice simple and improve the next useful log entry."
    elif has_nutrition and has_training and has_recovery:
        day_type = "nutrition_supported_strength_day"
        human_label = "Nutrition-Supported Strength Day"
        main_tension = "Training is appropriate today, but nutrition intake may need simple support."
        desired_move = (
            "Connect clean training execution with one simple nutrition support action."
        )
    elif has_nutrition:
        day_type = "nutrition_support"
        human_label = "Nutrition Support Day"
        main_tension = "The clearest improvement today is a simple nutrition action."
        desired_move = "Use one approved food or logging action if it fits the day."
    elif has_training:
        day_type = "training_execution_focus"
        human_label = "Training Execution Day"
        main_tension = (
            "The win today is doing the planned work without chasing extra intensity."
        )
        desired_move = "Complete the planned work cleanly and stay within the approved effort range."
    elif limitation_keys or limitations:
        day_type = "maintain_and_log"
        human_label = "Maintain and Log Day"
        main_tension = (
            "The available context is useful but not complete enough for a bigger call."
        )
        desired_move = "Keep the next action small, specific, and easy to verify."
    else:
        day_type = "controlled_progress"
        human_label = "Steady Execution Day"
        main_tension = "Today does not need a major adjustment."
        desired_move = str(
            synthesis.get("recommended_focus")
            or "Keep the next action simple and specific."
        )

    primary_claim_keys = [
        key
        for key in [calories_key, protein_key, rir_key, readiness_key, fatigue_key]
        if key is not None
    ]
    for key in sorted(food_keys):
        if len(primary_claim_keys) >= 6:
            break
        if key.endswith(".display_name"):
            primary_claim_keys.append(key)
    optional_action_claim_keys = [
        key for key in sorted(food_keys) if key not in primary_claim_keys
    ]

    training_implication = (
        "Do the planned session without turning it into a max-effort day."
        if has_training
        else "Do not invent training details beyond the approved plan context."
    )
    nutrition_implication = (
        "Use one simple approved food option if it fits the day."
        if food_keys
        else (
            "Use nutrition status only when it makes the action clearer."
            if has_nutrition
            else "Keep nutrition language cautious because approved nutrition context is limited."
        )
    )
    recovery_implication = (
        "Recovery does not require backing off today."
        if has_recovery
        else "Avoid claiming recovery details that are not approved."
    )
    avoid_overreaction = "Do not turn this into a max-effort workout, a full nutrition reset, or a trend claim."

    return DailyCoachTodayStory(
        day_type=day_type,  # type: ignore[arg-type]
        why=main_tension,
        nutrition_angle=nutrition_implication,
        training_angle=training_implication,
        recovery_angle=recovery_implication,
        priority_angle=desired_move,
        avoid_overreaction_angle=avoid_overreaction,
        primary_claim_keys=primary_claim_keys,
        optional_action_claim_keys=optional_action_claim_keys[:3],
        limitation_claim_keys=sorted(limitation_keys)[:2],
        human_label=human_label,
        main_tension=main_tension,
        training_implication=training_implication,
        nutrition_implication=nutrition_implication,
        recovery_implication=recovery_implication,
        avoid_overreaction=avoid_overreaction,
        desired_coaching_move=desired_move,
    )


def _claim_budgets(
    context: dict[str, Any],
    claims: list[dict[str, Any]],
    today_story: DailyCoachTodayStory,
) -> dict[str, Any]:
    rich_context = _rich_context_available(context, claims, today_story)
    total_min = 3 if rich_context else 1
    total_max = 6 if rich_context else min(4, max(1, len(claims)))
    return {
        "total": {
            "min": total_min,
            "max": total_max,
            "use_fewer_when": "context is thin, limited, sparse, or data-quality-limited",
        },
        "summary": {"min": 1 if rich_context else 0, "max": 2},
        "nutrition_note": {"min": 1 if rich_context else 0, "max": 2},
        "training_note": {"min": 1 if rich_context else 0, "max": 1},
        "recovery_note": {"min": 1 if rich_context else 0, "max": 2},
        "priority_action": {"min": 1 if rich_context else 0, "max": 2},
    }


def _rich_context_available(
    context: dict[str, Any],
    claims: list[dict[str, Any]],
    today_story: DailyCoachTodayStory,
) -> bool:
    domain_count = sum(
        1
        for prefix in ["nutrition.", "training.", "recovery."]
        if any(str(claim.get("key") or "").startswith(prefix) for claim in claims)
    )
    return (
        len(claims) >= 5
        and domain_count >= 3
        and bool(today_story.primary_claim_keys)
        and not _context_is_data_quality_limited(context)
    )


def _verbosity_budget(
    context: dict[str, Any],
    claims: list[dict[str, Any]],
    today_story: DailyCoachTodayStory,
) -> DailyCoachVerbosityBudget:
    if _context_is_data_quality_limited(context):
        return DailyCoachVerbosityBudget(
            mode="limited",
            target_words_min=60,
            target_words_max=100,
            guidance="Be brief and emphasize what can be trusted.",
        )
    if _rich_context_available(context, claims, today_story):
        return DailyCoachVerbosityBudget(
            mode="rich",
            target_words_min=120,
            target_words_max=180,
            guidance="Use enough detail to connect nutrition, training, and recovery naturally. Do not pad.",
        )
    return DailyCoachVerbosityBudget(
        mode="normal",
        target_words_min=90,
        target_words_max=130,
        guidance="Use a short but useful card. Add detail only when it improves the action.",
    )


def _adaptive_verbosity_guidance(
    context: dict[str, Any],
    claims: list[dict[str, Any]],
    claim_budgets: dict[str, Any],
    verbosity_budget: DailyCoachVerbosityBudget,
) -> dict[str, Any]:
    return {
        "target": "useful, grounded, scannable coaching",
        "not_the_target": "maximum brevity or maximum verbosity",
        "recommended_word_budget": f"{verbosity_budget.target_words_min}-{verbosity_budget.target_words_max}",
        "mode": verbosity_budget.mode,
        "allow_more_words_when": [
            "approved context is rich",
            "extra words improve the priority action",
            "multiple domains need to be connected",
            "food/training/recovery context must be explained clearly",
        ],
        "keep_shorter_when": [
            "context is sparse",
            "wording becomes generic",
            "prose becomes a report",
            "the model repeats metrics",
            "the model adds unsupported explanations",
        ],
        "claim_budget_max": claim_budgets["total"]["max"],
        "available_claim_count": len(claims),
    }


def _approved_context_brief(
    context: dict[str, Any],
    claims: list[dict[str, Any]],
    today_story: DailyCoachTodayStory,
) -> dict[str, Any]:
    available = {str(claim.get("key")) for claim in claims}
    sentences: list[DailyCoachApprovedContextBriefSentence] = []

    def add_sentence(text: str, claim_keys: list[str]) -> None:
        backed_keys = [key for key in claim_keys if key in available]
        if backed_keys and not _contains_framework_phrase(text):
            sentences.append(
                DailyCoachApprovedContextBriefSentence(
                    text=text,
                    claim_keys=backed_keys,
                )
            )

    if "training.rir_range" in available:
        add_sentence(
            "Today's training should stay clean and controlled instead of becoming a max-effort session.",
            ["training.rir_range"],
        )
    if {
        "recovery.readiness_level",
        "recovery.fatigue_risk",
    }.issubset(available):
        add_sentence(
            "Recovery looks favorable: readiness is High and fatigue risk is Low.",
            ["recovery.readiness_level", "recovery.fatigue_risk"],
        )
    if {
        "nutrition.calories.status",
        "nutrition.protein.status",
    }.issubset(available):
        add_sentence(
            "Nutrition is the main support area today because calories and protein are below target.",
            ["nutrition.calories.status", "nutrition.protein.status"],
        )
    elif "nutrition.protein.status" in available:
        add_sentence(
            "Protein is the easiest nutrition lever to clean up today.",
            ["nutrition.protein.status"],
        )
    food_key = _first_claim_key_with_suffix(
        available, "nutrition.food_suggestion", ".display_name"
    )
    if food_key:
        display_name = _claim_value_by_key(claims, food_key)
        if display_name:
            add_sentence(
                f"One approved option is {display_name}.",
                [food_key],
            )
    if today_story.desired_coaching_move and today_story.primary_claim_keys:
        add_sentence(
            str(today_story.desired_coaching_move),
            list(today_story.primary_claim_keys)[:3],
        )

    return {"sentences": [sentence.to_dict() for sentence in sentences[:5]]}


def _claim_backing_map(claims: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    claim_keys = {str(claim.get("key")) for claim in claims}
    backing: dict[str, DailyCoachClaimBackingGuide] = {}

    def add(
        label: str,
        claim_key: str,
        *,
        allowed: list[str],
        disallowed: list[str],
    ) -> None:
        if claim_key in claim_keys:
            backing[label] = DailyCoachClaimBackingGuide(
                claim_key=claim_key,
                allowed_phrasings=allowed,
                disallowed_phrasings=disallowed,
            )

    add(
        "calories are below target",
        "nutrition.calories.status",
        allowed=[
            "calories are below target",
            "calories are lagging",
            "calorie intake is behind the target",
        ],
        disallowed=[
            "you are underfed",
            "you are in a severe deficit",
            "you are compromising recovery",
        ],
    )
    add(
        "protein is below target",
        "nutrition.protein.status",
        allowed=[
            "protein is below target",
            "protein is the easiest fix today",
            "a simple protein option would help support the day",
        ],
        disallowed=[
            "you failed protein",
            "you are losing muscle",
            "you need protein immediately",
        ],
    )
    food_key = _first_claim_key_with_suffix(
        claim_keys, "nutrition.food_suggestion", ".display_name"
    )
    if food_key:
        display_name = (
            _claim_value_by_key(claims, food_key) or "the approved food option"
        )
        add(
            f"{display_name} is approved",
            food_key,
            allowed=[
                f"an approved option like {display_name}",
                f"one simple option is {display_name}",
            ],
            disallowed=[
                f"you must eat {display_name}",
                f"{display_name} is required",
                f"{display_name} will fix the day",
            ],
        )
    add(
        "RIR range",
        "training.rir_range",
        allowed=[
            "keep a couple reps in reserve",
            "stay within RIR 2-4",
            "do not turn it into a max-effort day",
        ],
        disallowed=["go to failure", "push past the plan", "increase intensity"],
    )
    add(
        "readiness is High",
        "recovery.readiness_level",
        allowed=[
            "readiness is High",
            "recovery is on your side",
            "you are clear to train today",
        ],
        disallowed=[
            "you are fully recovered",
            "you cannot overdo it",
            "recovery guarantees performance",
        ],
    )
    add(
        "fatigue risk is Low",
        "recovery.fatigue_risk",
        allowed=[
            "fatigue risk is Low",
            "fatigue does not require backing off today",
        ],
        disallowed=["there is no fatigue", "fatigue is not a concern at all"],
    )
    return {label: guide.to_dict() for label, guide in backing.items()}


def _voice_examples() -> dict[str, list[dict[str, str]]]:
    return {
        "examples": [
            {
                "bad": "Calories are below target today, so make nutrition support the main lever while keeping training controlled.",
                "better": "You're clear to train today, but don't make the workout do all the work. Get the planned strength session done cleanly, then use one simple approved food option if it fits your meals.",
            },
            {
                "bad": "Use RIR 2-4 as your effort anchor.",
                "better": "Keep a couple reps in reserve and make clean execution the win.",
            },
            {
                "bad": "Protein is also below target; adding a simple protein option can support the day without turning this into a bigger nutrition overhaul.",
                "better": "Protein is the easiest fix today. A simple approved option is enough; this does not need to become a full meal-plan reset.",
            },
            {
                "bad": "Recovery supports confident training while staying inside the planned effort range.",
                "better": "Recovery is on your side today, so you do not need to back off Ã¢â‚¬â€ just do not turn it into a max-effort session.",
            },
        ]
    }


def _context_is_data_quality_limited(context: dict[str, Any]) -> bool:
    synthesis = context.get("daily_coach_synthesis") or {}
    scenario = str(synthesis.get("scenario") or "").lower()
    if scenario == "data_quality_limited":
        return True
    return any(
        "data quality" in str(item).lower()
        for item in context.get("approved_limitations") or []
    )


def _contains_framework_phrase(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in _V3_HARD_FAIL_STYLE_PHRASES)


def _first_claim_key_with_suffix(
    claim_keys: set[str], prefix: str, suffix: str
) -> str | None:
    for key in sorted(claim_keys):
        if key.startswith(prefix) and key.endswith(suffix):
            return key
    return None


def _claim_value_by_key(claims: list[dict[str, Any]], claim_key: str) -> str | None:
    for claim in claims:
        if str(claim.get("key") or "") == claim_key:
            value = claim.get("value")
            return str(value) if value not in {None, "", "Unknown", "unknown"} else None
    return None


def _display_allowed_claims(claims: Any) -> list[dict[str, Any]]:
    if not isinstance(claims, list):
        return []
    allowed: list[dict[str, Any]] = []
    for claim in claims:
        if not isinstance(claim, dict) or not bool(claim.get("display_allowed", True)):
            continue
        key = claim.get("key")
        if isinstance(key, str) and key.strip():
            allowed.append(_claim_with_default_metadata(claim))
    return allowed


def _claim_with_default_metadata(claim: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(claim)
    key = str(enriched.get("key") or "")
    claim_type = str(enriched.get("claim_type") or "")
    if not enriched.get("section_hint"):
        if key.startswith("nutrition.food_suggestion"):
            enriched["section_hint"] = "priority_action"
        elif key.startswith("nutrition."):
            enriched["section_hint"] = "nutrition_note"
        elif key.startswith("training."):
            enriched["section_hint"] = "training_note"
        elif key.startswith("recovery."):
            enriched["section_hint"] = "recovery_note"
        elif key.startswith("limitation.") or claim_type == "limitation":
            enriched["section_hint"] = "summary"
    if not enriched.get("priority"):
        if key in {
            "recovery.readiness_level",
            "recovery.fatigue_risk",
            "training.rir_range",
            "nutrition.protein.status",
        }:
            enriched["priority"] = 1
        elif key.startswith("nutrition.food_suggestion"):
            enriched["priority"] = 2
        else:
            enriched["priority"] = 3
    if not enriched.get("coaching_use"):
        if key.startswith("nutrition.food_suggestion"):
            enriched["coaching_use"] = "prioritize_action"
        elif key.startswith("nutrition."):
            enriched["coaching_use"] = "support_nutrition_action"
        elif key.startswith("training."):
            enriched["coaching_use"] = "support_training_action"
        elif key.startswith("recovery."):
            enriched["coaching_use"] = "support_recovery_action"
        elif key.startswith("limitation."):
            enriched["coaching_use"] = "contextualize_limit"
    return enriched


def _provider_task_context(
    context: dict[str, Any],
    claims: list[dict[str, Any]],
    claim_budgets: dict[str, Any],
) -> dict[str, Any]:
    synthesis = context.get("daily_coach_synthesis") or {}
    return {
        "task": "Write one grounded, scannable Daily Coach card from safe facts and natural context.",
        "tone": "direct practical coach, natural, specific, calm, useful, not a report dump",
        "target_total_claims": (
            f"{claim_budgets['total']['min']}-{claim_budgets['total']['max']}"
        ),
        "adaptive_verbosity_target": "useful_grounded_scannable_coaching",
        "confidence": (
            synthesis.get("confidence") if isinstance(synthesis, dict) else None
        ),
        "claim_count_available": len(claims),
        "highest_priority_claim_count": sum(
            1 for claim in claims if int(claim.get("priority") or 3) == 1
        ),
        "today_story_day_type": (
            (context.get("today_story") or {}).get("day_type")
            if isinstance(context.get("today_story"), dict)
            else None
        ),
    }


def _high_value_claim_keys(
    claims: list[dict[str, Any]], *, max_claims: int
) -> list[str]:
    sorted_claims = sorted(claims, key=_claim_priority_sort_key)
    selected: list[str] = []
    seen_sections: set[str] = set()
    for claim in sorted_claims:
        section = str(claim.get("section_hint") or "")
        if section and section not in seen_sections:
            selected.append(str(claim["key"]))
            seen_sections.add(section)
        if len(selected) >= max_claims:
            return selected
    for claim in sorted_claims:
        key = str(claim["key"])
        if key not in selected:
            selected.append(key)
        if len(selected) >= max_claims:
            break
    return selected


def _preferred_claims_by_field(
    claims: list[dict[str, Any]], claim_budgets: dict[str, Any]
) -> dict[str, list[str]]:
    fields = [
        "summary",
        "nutrition_note",
        "training_note",
        "recovery_note",
        "priority_action",
    ]
    preferred: dict[str, list[str]] = {field: [] for field in fields}
    for claim in sorted(claims, key=_claim_priority_sort_key):
        field = claim.get("section_hint")
        if field not in preferred:
            continue
        field_budget = claim_budgets.get(str(field), {})
        field_max = int(field_budget.get("max", 2))
        if len(preferred[str(field)]) < field_max:
            preferred[str(field)].append(str(claim["key"]))
    return preferred


def _claim_priority_sort_key(claim: dict[str, Any]) -> tuple[int, int, str]:
    priority = int(claim.get("priority") or 3)
    claim_type = str(claim.get("claim_type") or "")
    type_rank = {
        "recovery": 0,
        "training": 1,
        "nutrition_gap": 2,
        "recommendation": 3,
        "nutrition_actual": 4,
        "limitation": 5,
    }.get(claim_type, 9)
    return (priority, type_rank, str(claim.get("key") or ""))


def _claim_usage_rules(claim_budgets: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_total_claims": (
            f"{claim_budgets['total']['min']}-{claim_budgets['total']['max']}"
        ),
        "use_fewer_when": claim_budgets["total"].get("use_fewer_when"),
        "adaptive_verbosity_target": "useful, grounded, scannable coaching",
        "exact_values_require_quoted_values_used": True,
        "do_not_dump_all_claims": True,
        "prefer_status_over_numbers_when_numbers_are_not_needed": True,
        "use_limitations_as_uncertainty_not_user_blame": True,
        "quoted_values_used_must_be_exact_claim_keys": True,
    }


def _field_role_guidance() -> dict[str, str]:
    return {
        "headline": "Short title, not always Daily Coach.",
        "summary": "One sentence saying what matters most today.",
        "nutrition_note": "Concrete nutrition state plus one approved implication.",
        "training_note": "Approved training direction plus effort/execution anchor.",
        "recovery_note": "Recovery signal plus what it means for today's training confidence.",
        "priority_action": "One concrete action the user can do today.",
    }


def _format_value_alias(value: Any, unit: str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        value_text = f"{value:g}"
    else:
        value_text = str(value)
    return f"{value_text}{unit}" if unit else value_text


def _provider_context_summary(value_context: dict[str, Any]) -> dict[str, Any]:
    nutrition = value_context.get("approved_nutrition") or {}
    recovery = value_context.get("approved_recovery") or {}
    suggestions = nutrition.get("approved_food_suggestions") or []
    high_value_claims = value_context.get("high_value_claims") or []
    preferred_claims = value_context.get("preferred_claims_by_field") or {}
    return {
        "has_recovery_values": bool(recovery),
        "nutrition_context_available": bool(nutrition.get("available")),
        "approved_food_suggestion_count": len(suggestions),
        "approved_limitations_count": len(
            value_context.get("approved_limitations") or []
        ),
        "approved_reason_codes_count": len(
            value_context.get("approved_reason_codes") or []
        ),
        "approved_value_claim_count": len(
            value_context.get("approved_value_claims") or []
        ),
        "high_value_claims_available": list(high_value_claims),
        "preferred_claims_by_field": dict(preferred_claims),
        "claim_usage_rules": dict(value_context.get("claim_usage_rules") or {}),
        "today_story": dict(value_context.get("today_story") or {}),
        "claim_budgets": dict(value_context.get("claim_budgets") or {}),
        "adaptive_verbosity_guidance": dict(
            value_context.get("adaptive_verbosity_guidance") or {}
        ),
        "approved_context_brief": dict(
            value_context.get("approved_context_brief") or {}
        ),
        "claim_backing_map": dict(value_context.get("claim_backing_map") or {}),
        "verbosity_budget": dict(value_context.get("verbosity_budget") or {}),
    }


def _compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, str) and value in {"", "Unknown", "unknown"}:
            continue
        if isinstance(value, list | dict) and not value:
            continue
        compact[key] = value
    return compact


def _bounded_list(values: list[str], *, limit: int) -> list[str]:
    deduped = list(dict.fromkeys(value for value in values if value))
    return deduped[:limit]


def _normalize_provider(provider: str | None) -> str:
    if provider is None or not provider.strip():
        return PROVIDER_DETERMINISTIC
    return provider.strip().lower()


def _selected_model(provider: str, configured_model: str | None) -> str:
    if configured_model and configured_model.strip():
        return configured_model.strip()
    if provider == PROVIDER_DIRECT_OLLAMA:
        return DEFAULT_DIRECT_OLLAMA_MODEL
    return DEFAULT_OPENAI_MODEL


def _normalize_ollama_model(model_name: str) -> str:
    return model_name.removeprefix("ollama/")


def _provider_timeout(provider: str, env: Mapping[str, str]) -> float:
    key = (
        DAILY_COACH_VALUE_NARRATIVE_DIRECT_OLLAMA_TIMEOUT_ENV
        if provider == PROVIDER_DIRECT_OLLAMA
        else DAILY_COACH_VALUE_NARRATIVE_OPENAI_TIMEOUT_ENV
    )
    try:
        return max(1.0, float(env.get(key, "60")))
    except ValueError:
        return 60.0


def _markdown_wrapper_detected(raw_output: str) -> bool:
    stripped = raw_output.strip().lower()
    return stripped.startswith("```") or "```json" in stripped


def _provider_exception_reason(provider: str, exc: Exception) -> str:
    text = str(exc).lower()
    if isinstance(exc, TimeoutError) or "timed out" in text or "timeout" in text:
        return f"{provider}_timeout"
    if isinstance(exc, urllib.error.URLError) or "connection" in text:
        return f"{provider}_connection_error"
    if isinstance(exc, DailyCoachValueNarrativeError):
        return str(exc) or f"{provider}_error"
    return f"{provider}_provider_error"
