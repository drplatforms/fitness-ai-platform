from __future__ import annotations

import json
import os
import re
import time

from models.daily_coach_narrative_models import (
    DAILY_COACH_NARRATIVE_REQUIRED_OUTPUT_KEYS,
    CandidateDailyCoachNarrative,
    DailyCoachNarrativeContext,
    DailyCoachNarrativePreviewResult,
)
from services.daily_coach_narrative_context_service import (
    build_daily_coach_narrative_context,
    build_daily_coach_narrative_qa_preview_context,
)
from services.daily_coach_narrative_provider_service import (
    DEFAULT_OLLAMA_BASE_URL,
    OLLAMA_BASE_URL_ENV,
    DailyCoachNarrativeGenerateCallable,
    build_daily_coach_narrative_prompt,
    call_ollama_generate,
)
from services.daily_coach_narrative_validation_service import (
    parse_daily_coach_narrative_candidate,
    validate_daily_coach_narrative_candidate,
)

DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DETERMINISTIC = "deterministic"
DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA = "direct_ollama"
DAILY_COACH_NARRATIVE_PREVIEW_DEFAULT_MODEL = "qwen3:8b"

PUBLIC_SAFE_FALLBACK_PROVIDER_DISABLED = "provider_disabled"
PUBLIC_SAFE_FALLBACK_PROVIDER_TIMEOUT = "provider_timeout"
PUBLIC_SAFE_FALLBACK_PROVIDER_PARSE_FAILED = "provider_parse_failed"
PUBLIC_SAFE_FALLBACK_PROVIDER_VALIDATION_FAILED = "provider_validation_failed"
PUBLIC_SAFE_FALLBACK_PROVIDER_UNAVAILABLE = "provider_unavailable"

_ALLOWED_PREVIEW_PROVIDERS = {
    DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DETERMINISTIC,
    DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA,
}


class DailyCoachNarrativePreviewError(ValueError):
    """Raised when a Daily Coach Narrative preview request is invalid."""


def build_daily_coach_narrative_preview(
    user_id: int,
    *,
    target_date: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    timeout_seconds: float = 300.0,
    generate: DailyCoachNarrativeGenerateCallable | None = None,
    qa_preview: bool = False,
    lookback_days: int = 1,
) -> DailyCoachNarrativePreviewResult:
    """Build a public-safe developer preview of Daily Coach Narrative output.

    The preview is deterministic by default. The provider path is attempted only
    when explicitly requested with provider=direct_ollama. Rejected, unparsable,
    or exception-producing provider output is never returned; the caller receives
    deterministic fallback text plus public-safe status metadata.
    """

    selected_provider = _normalize_provider(provider)
    provider_enabled = (
        selected_provider == DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DIRECT_OLLAMA
    )
    selected_model = _normalize_model_name(model_name) if provider_enabled else None
    if qa_preview:
        context = build_daily_coach_narrative_qa_preview_context(
            user_id,
            selected_date=target_date,
            lookback_days=lookback_days,
        )
    else:
        context = build_daily_coach_narrative_context(
            user_id,
            target_date=target_date,
        )

    if not provider_enabled:
        return _fallback_result(
            context=context,
            provider_enabled=False,
            provider_attempted=False,
            selected_provider=selected_provider,
            selected_model=None,
            fallback_reason=PUBLIC_SAFE_FALLBACK_PROVIDER_DISABLED,
            parse_success=False,
            validation_success=False,
            latency_ms=0,
            developer_diagnostics=_preview_developer_diagnostics(
                provider_enabled=False,
                provider_attempted=False,
                selected_provider=selected_provider,
                selected_model=None,
                parse_success=False,
                validation_success=False,
                fallback_used=True,
                fallback_reason=PUBLIC_SAFE_FALLBACK_PROVIDER_DISABLED,
            ),
        )

    prompt = build_daily_coach_narrative_prompt(context)
    generate_callable = generate or call_ollama_generate
    started = time.perf_counter()
    try:
        raw_output = generate_callable(
            selected_model or DAILY_COACH_NARRATIVE_PREVIEW_DEFAULT_MODEL,
            prompt,
            timeout_seconds,
            _resolved_ollama_base_url(),
        )
    except Exception as exc:
        latency_ms = _elapsed_ms(started)
        return _fallback_result(
            context=context,
            provider_enabled=True,
            provider_attempted=True,
            selected_provider=selected_provider,
            selected_model=selected_model,
            fallback_reason=_public_safe_exception_reason(exc),
            parse_success=False,
            validation_success=False,
            latency_ms=latency_ms,
            developer_diagnostics=_preview_developer_diagnostics(
                provider_enabled=True,
                provider_attempted=True,
                selected_provider=selected_provider,
                selected_model=selected_model,
                parse_success=False,
                validation_success=False,
                fallback_used=True,
                fallback_reason=_public_safe_exception_reason(exc),
            ),
        )

    latency_ms = _elapsed_ms(started)
    normalized_output, parse_extraction_strategy = (
        _normalize_provider_output_for_preview(raw_output)
    )
    parse_result = parse_daily_coach_narrative_candidate(normalized_output)
    if parse_result.candidate is None:
        return _fallback_result(
            context=context,
            provider_enabled=True,
            provider_attempted=True,
            selected_provider=selected_provider,
            selected_model=selected_model,
            fallback_reason=PUBLIC_SAFE_FALLBACK_PROVIDER_PARSE_FAILED,
            parse_success=False,
            validation_success=False,
            latency_ms=latency_ms,
            developer_diagnostics=_preview_developer_diagnostics(
                provider_enabled=True,
                provider_attempted=True,
                selected_provider=selected_provider,
                selected_model=selected_model,
                parse_success=False,
                validation_success=False,
                fallback_used=True,
                fallback_reason=PUBLIC_SAFE_FALLBACK_PROVIDER_PARSE_FAILED,
                parse_error=parse_result.error,
                parse_extraction_strategy=parse_extraction_strategy,
            ),
        )

    validation_result = validate_daily_coach_narrative_candidate(
        parse_result.candidate,
        context=context,
    )
    if not validation_result.approved:
        return _fallback_result(
            context=context,
            provider_enabled=True,
            provider_attempted=True,
            selected_provider=selected_provider,
            selected_model=selected_model,
            fallback_reason=PUBLIC_SAFE_FALLBACK_PROVIDER_VALIDATION_FAILED,
            parse_success=True,
            validation_success=False,
            latency_ms=latency_ms,
            developer_diagnostics=_preview_developer_diagnostics(
                provider_enabled=True,
                provider_attempted=True,
                selected_provider=selected_provider,
                selected_model=selected_model,
                parse_success=True,
                validation_success=False,
                fallback_used=True,
                fallback_reason=PUBLIC_SAFE_FALLBACK_PROVIDER_VALIDATION_FAILED,
                validation_errors=validation_result.validation_errors,
                forbidden_claims_found=validation_result.forbidden_claims_found,
                parse_extraction_strategy=parse_extraction_strategy,
            ),
        )

    return DailyCoachNarrativePreviewResult(
        user_id=context.user_id,
        date=context.date,
        next_action_id=context.next_action_id,
        next_action_title=context.next_action_title,
        workflow_target=context.workflow_target,
        provider_enabled=True,
        provider_attempted=True,
        selected_provider=selected_provider,
        selected_model=selected_model,
        parse_success=True,
        validation_success=True,
        fallback_used=False,
        fallback_reason=None,
        approved_narrative=_approved_narrative_payload(parse_result.candidate),
        deterministic_fallback_note=context.fallback_note,
        approved_focus=context.approved_focus,
        context_summary=_context_summary(context),
        latency_ms=latency_ms,
        developer_diagnostics=_preview_developer_diagnostics(
            provider_enabled=True,
            provider_attempted=True,
            selected_provider=selected_provider,
            selected_model=selected_model,
            parse_success=True,
            validation_success=True,
            fallback_used=False,
            fallback_reason=None,
            approved_narrative_returned=True,
            parse_extraction_strategy=parse_extraction_strategy,
        ),
    )


def _fallback_result(
    *,
    context: DailyCoachNarrativeContext,
    provider_enabled: bool,
    provider_attempted: bool,
    selected_provider: str,
    selected_model: str | None,
    fallback_reason: str,
    parse_success: bool,
    validation_success: bool,
    latency_ms: int,
    developer_diagnostics: dict[str, object] | None = None,
) -> DailyCoachNarrativePreviewResult:
    return DailyCoachNarrativePreviewResult(
        user_id=context.user_id,
        date=context.date,
        next_action_id=context.next_action_id,
        next_action_title=context.next_action_title,
        workflow_target=context.workflow_target,
        provider_enabled=provider_enabled,
        provider_attempted=provider_attempted,
        selected_provider=selected_provider,
        selected_model=selected_model,
        parse_success=parse_success,
        validation_success=validation_success,
        fallback_used=True,
        fallback_reason=fallback_reason,
        approved_narrative=None,
        deterministic_fallback_note=context.fallback_note,
        approved_focus=context.approved_focus,
        context_summary=_context_summary(context),
        latency_ms=latency_ms,
        developer_diagnostics=developer_diagnostics
        or _preview_developer_diagnostics(
            provider_enabled=provider_enabled,
            provider_attempted=provider_attempted,
            selected_provider=selected_provider,
            selected_model=selected_model,
            parse_success=parse_success,
            validation_success=validation_success,
            fallback_used=True,
            fallback_reason=fallback_reason,
        ),
    )


def _normalize_provider(provider: str | None) -> str:
    selected = (
        provider or DAILY_COACH_NARRATIVE_PREVIEW_PROVIDER_DETERMINISTIC
    ).strip()
    if selected not in _ALLOWED_PREVIEW_PROVIDERS:
        raise DailyCoachNarrativePreviewError(
            "Daily Coach Narrative preview provider must be deterministic or direct_ollama."
        )
    return selected


def _normalize_model_name(model_name: str | None) -> str:
    selected = (model_name or DAILY_COACH_NARRATIVE_PREVIEW_DEFAULT_MODEL).strip()
    if not selected:
        return DAILY_COACH_NARRATIVE_PREVIEW_DEFAULT_MODEL
    return selected


def _resolved_ollama_base_url() -> str:
    return os.getenv(OLLAMA_BASE_URL_ENV) or DEFAULT_OLLAMA_BASE_URL


def _public_safe_exception_reason(exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        return PUBLIC_SAFE_FALLBACK_PROVIDER_TIMEOUT
    if "timeout" in type(exc).__name__.lower():
        return PUBLIC_SAFE_FALLBACK_PROVIDER_TIMEOUT
    return PUBLIC_SAFE_FALLBACK_PROVIDER_UNAVAILABLE


def _elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def _approved_narrative_payload(
    candidate: CandidateDailyCoachNarrative,
) -> dict[str, object]:
    return {
        "coach_note": candidate.coach_note,
        "key_takeaway": candidate.key_takeaway,
        "recommended_focus": candidate.recommended_focus,
        "confidence_language": candidate.confidence_language,
        "used_approved_facts": list(candidate.used_approved_facts),
        "avoided_claims": list(candidate.avoided_claims),
    }


def _context_summary(context: DailyCoachNarrativeContext) -> dict[str, object]:
    source_metadata = dict(context.source_metadata or {})
    return {
        "approved_facts_count": len(context.approved_facts),
        "approved_facts_summary": list(context.approved_facts[:6]),
        "approved_limitations_count": len(context.approved_limitations),
        "approved_limitations_summary": list(context.approved_limitations[:6]),
        "forbidden_claim_categories_count": len(context.forbidden_claims),
        "forbidden_claim_categories_summary": list(context.forbidden_claims[:5]),
        "context_source": source_metadata.get("context_source"),
        "selected_date": source_metadata.get("selected_date") or context.date,
        "start_date": source_metadata.get("start_date"),
        "end_date": source_metadata.get("end_date"),
        "lookback_days": source_metadata.get("lookback_days"),
        "data_quality_label": source_metadata.get("data_quality_label"),
        "weekly_inventory_data_quality_label": source_metadata.get(
            "weekly_inventory_data_quality_label"
        ),
        "reason_codes": list(source_metadata.get("reason_codes") or []),
        "recommended_test_label": source_metadata.get("recommended_test_label"),
        "richness_score": source_metadata.get("richness_score"),
        "domains_present_count": source_metadata.get("domains_present_count"),
        "recovery_checkins_count": source_metadata.get("recovery_checkins_count"),
        "nutrition_entries_count": source_metadata.get("nutrition_entries_count"),
        "workout_sessions_count": source_metadata.get("workout_sessions_count"),
        "workout_execution_sessions_count": source_metadata.get(
            "workout_execution_sessions_count"
        ),
        "planned_workouts_count": source_metadata.get("planned_workouts_count"),
        "planned_exercises_count": source_metadata.get("planned_exercises_count"),
        "actual_sets_count": source_metadata.get("actual_sets_count"),
        "next_action_reason": source_metadata.get("next_action_reason"),
    }


def _preview_developer_diagnostics(
    *,
    provider_enabled: bool,
    provider_attempted: bool,
    selected_provider: str,
    selected_model: str | None,
    parse_success: bool,
    validation_success: bool,
    fallback_used: bool,
    fallback_reason: str | None,
    approved_narrative_returned: bool = False,
    parse_error: str | None = None,
    validation_errors: list[str] | None = None,
    forbidden_claims_found: list[str] | None = None,
    parse_extraction_strategy: str | None = None,
    provider_error: str | None = None,
) -> dict[str, object]:
    """Return sanitized diagnostics for Developer Mode preview inspection.

    This intentionally excludes raw provider output, prompts, stack traces, and
    rejected text. The fields are stable enough for QA scripts and Streamlit
    Developer Mode rendering, but they do not change normal Today behavior.
    """

    diagnostics: dict[str, object] = {
        "provider_enabled": provider_enabled,
        "provider_attempted": provider_attempted,
        "selected_provider": selected_provider,
        "selected_model": selected_model,
        "parse_success": parse_success,
        "validation_success": validation_success,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "approved_narrative_returned": approved_narrative_returned,
    }

    if parse_extraction_strategy:
        diagnostics["parse_extraction_strategy"] = _sanitize_diagnostic_text(
            parse_extraction_strategy
        )
    if provider_error:
        diagnostics["provider_error"] = _sanitize_diagnostic_text(provider_error)
    if parse_error:
        diagnostics["parse_error"] = _sanitize_diagnostic_text(parse_error)
    if validation_errors:
        diagnostics["validation_errors"] = [
            _public_safe_validation_error(error) for error in validation_errors
        ]
    if forbidden_claims_found:
        diagnostics["forbidden_claims_found"] = [
            _sanitize_diagnostic_text(error) for error in forbidden_claims_found
        ]

    return diagnostics


_THINK_BLOCK_PATTERN = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)
_MARKDOWN_JSON_FENCE_PATTERN = re.compile(
    r"^```(?:json|JSON)?\s*(?P<body>.*?)\s*```$",
    re.DOTALL,
)


def _normalize_provider_output_for_preview(raw_output: str) -> tuple[str, str]:
    """Return a deterministic JSON candidate string and extraction strategy.

    The preview lane is allowed to normalize common local-model wrappers before
    passing text to the existing strict parser. It never exposes raw provider
    output, and it refuses ambiguous multi-object output unless exactly one JSON
    object satisfies the Daily Coach Narrative contract key set.
    """

    text = raw_output.strip()
    strategy_steps: list[str] = []

    without_thinking = _THINK_BLOCK_PATTERN.sub("", text).strip()
    if without_thinking != text:
        text = without_thinking
        strategy_steps.append("qwen_think_stripped")

    fence_match = _MARKDOWN_JSON_FENCE_PATTERN.match(text)
    if fence_match:
        text = fence_match.group("body").strip()
        strategy_steps.append("markdown_json_fence_stripped")

    if text.startswith("{") and text.endswith("}"):
        try:
            json.loads(text)
        except json.JSONDecodeError:
            pass
        else:
            strategy_steps.append("raw_json_object")
            return text, "+".join(strategy_steps)

    json_objects = _extract_balanced_json_objects(text)
    if len(json_objects) == 1:
        strategy_steps.append("single_embedded_json_object")
        return json_objects[0], "+".join(strategy_steps)

    contract_objects = [
        candidate for candidate in json_objects if _looks_like_contract_json(candidate)
    ]
    if len(contract_objects) == 1:
        strategy_steps.append("single_contract_json_object")
        return contract_objects[0], "+".join(strategy_steps)

    if len(json_objects) > 1:
        strategy_steps.append("ambiguous_multiple_json_objects")
    else:
        strategy_steps.append("no_json_object_found")
    return text, "+".join(strategy_steps)


def _extract_balanced_json_objects(text: str) -> list[str]:
    objects: list[str] = []
    depth = 0
    start: int | None = None
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
            continue
        if char == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start : index + 1].strip())
                start = None

    return objects


def _looks_like_contract_json(candidate: str) -> bool:
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return False
    if not isinstance(parsed, dict):
        return False
    return set(parsed) == DAILY_COACH_NARRATIVE_REQUIRED_OUTPUT_KEYS


def _public_safe_validation_error(value: object) -> str:
    text = _sanitize_diagnostic_text(value)
    lowered = text.lower()
    if "meta/internal process language" in lowered:
        return (
            "Meta/internal process language is not allowed in coach narrative output."
        )
    if "unapproved fact" in lowered:
        return "Provider output used a fact that was not approved for this preview context."
    if "forbidden claim" in lowered:
        return "Provider output included a claim category that is not approved for this preview context."
    if "invented numeric" in lowered:
        return "Provider output included numeric detail that is not approved for this preview context."
    return text


def _sanitize_diagnostic_text(value: object) -> str:
    text = str(value).strip()
    if not text:
        return ""
    return text.replace("\n", " ").replace("\r", " ")[:500]
