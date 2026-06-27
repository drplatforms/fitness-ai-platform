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
    DailyCoachValueNarrativeResult,
    DailyCoachValueNarrativeRuntimeMetadata,
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

    env = environ or os.environ
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
    env = environ or os.environ
    configured_provider = _normalize_provider(
        env.get(DAILY_COACH_VALUE_NARRATIVE_PROVIDER_ENV)
    )
    configured_model = env.get(DAILY_COACH_VALUE_NARRATIVE_MODEL_ENV)
    value_context = value_context or build_minimal_value_context_from_synthesis(
        synthesis
    )

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
    return context


def build_daily_coach_value_narrative_prompt(
    synthesis: DailyCoachSynthesis,
    *,
    value_context: dict[str, Any],
) -> str:
    example = {
        "headline": "Daily Coach",
        "summary": "Recovery looks strong today, so the goal is steady execution rather than overcorrecting.",
        "nutrition_note": "Protein is below the approved target based on logged meals, so use the approved Nutrition options if they fit.",
        "training_note": "No workout has been started today, so training guidance should stay tied to the approved plan context.",
        "recovery_note": "Recovery readiness is High and fatigue risk is Low.",
        "priority_action": "Keep today's plan controlled and well logged.",
        "confidence": synthesis.confidence,
        "reason_codes": ["provider_candidate_value_aware"],
        "quoted_values_used": [
            "recovery.readiness_level",
            "recovery.fatigue_risk",
            "nutrition.protein.status",
            "training.rir_range",
        ],
    }
    return (
        "Write a concise Daily Coach narrative for AI Health Coach.\n"
        "Use only approved backend context. You may quote values only when they appear in approved_value_claims.\n"
        "Return one raw JSON object only. No markdown, no code fences, no prose wrapper, no extra keys.\n"
        "Do not calculate targets, gaps, readiness, fatigue, servings, or nutrition values.\n"
        "Do not say recovery is missing when recovery_signal or approved recovery values exist.\n"
        "Do not say 'without needing to address training or recovery'.\n"
        "Do not say the user is under-eating unless that exact claim is approved.\n"
        "Do not say the user needs calories unless calorie targets are display-approved.\n"
        "Do not prescribe exact food amounts unless approved food suggestions include those amounts.\n\n"
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
    resolved_base_url = (
        base_url or os.getenv(OPENAI_BASE_URL_ENV) or DEFAULT_OPENAI_BASE_URL
    ).rstrip("/")
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": "Return exact JSON only for the requested schema.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "daily_coach_value_narrative",
                "schema": _CANDIDATE_SCHEMA,
                "strict": True,
            },
        },
    }
    request = urllib.request.Request(
        f"{resolved_base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resolved_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        response_payload = json.loads(response.read().decode("utf-8"))
    try:
        raw_text = response_payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise DailyCoachValueNarrativeError("openai_malformed_response") from exc
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise DailyCoachValueNarrativeError("openai_missing_response")
    return raw_text


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
            return call_openai_daily_coach_narrative(
                model,
                prompt,
                timeout,
                api_key=env.get(OPENAI_API_KEY_ENV),
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
            confidence=context.get("daily_coach_synthesis", {}).get("confidence"),
        )
        _add_claim(
            claims,
            key="recovery.fatigue_risk",
            label="fatigue risk",
            value=recovery.get("fatigue_risk"),
            claim_type="recovery",
            aliases=[f"fatigue risk is {recovery.get('fatigue_risk')}"],
            source="approved_recovery",
            confidence=context.get("daily_coach_synthesis", {}).get("confidence"),
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
            confidence=context.get("daily_coach_synthesis", {}).get("confidence"),
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
                confidence=context.get("daily_coach_synthesis", {}).get("confidence"),
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
                )
        macro_status = nutrition.get("macro_status") or {}
        if isinstance(macro_status, dict):
            for macro_name, macro in macro_status.items():
                if not isinstance(macro, dict):
                    continue
                display_allowed = bool(macro.get("display_allowed"))
                target_status = macro.get("target_status")
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
                )

    training = context.get("approved_training") or {}
    if isinstance(training, dict):
        training_text = " ".join(str(value) for value in training.values() if value)
        rir_match = re.search(
            r"RIR\s*(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)",
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
                confidence=context.get("daily_coach_synthesis", {}).get("confidence"),
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
            confidence=context.get("daily_coach_synthesis", {}).get("confidence"),
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
        )
    )


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
