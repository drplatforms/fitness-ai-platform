from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from models.weekly_coach_summary_models import (
    ApprovedWeeklyCoachSummary,
    WeeklyCoachSummaryConfidence,
    WeeklyCoachSummaryContext,
    WeeklyCoachSummarySource,
)
from models.weekly_coach_summary_provider_models import (
    APPROVED_WEEKLY_PROVIDER_MODEL,
    CandidateWeeklyCoachSummaryProviderOutput,
    ProviderConfidenceLabel,
    WeeklyCoachSummaryProviderModelError,
    assert_provider_input_is_design_safe,
    parse_candidate_weekly_provider_output_json,
    weekly_provider_output_json_schema,
)
from services.provider_lifecycle_service import (
    ProviderLifecycleActionResult,
    ProviderLifecycleHttpPost,
    ProviderLifecyclePolicy,
    build_ollama_generate_payload,
    maybe_unload_model_after_request,
    render_provider_lifecycle_summary,
    resolve_ollama_base_url,
    resolve_provider_lifecycle_policy,
)
from services.weekly_coach_summary_service import (
    approved_weekly_summary_to_public_sections,
)

WEEKLY_SUMMARY_PROVIDER_PREVIEW_ENABLED_ENV = (
    "FITNESS_AI_WEEKLY_SUMMARY_PROVIDER_PREVIEW_ENABLED"
)
WEEKLY_SUMMARY_PROVIDER_MODEL_ENV = "FITNESS_AI_WEEKLY_SUMMARY_PROVIDER_MODEL"
WEEKLY_SUMMARY_PROVIDER_TIMEOUT_SECONDS_ENV = (
    "FITNESS_AI_WEEKLY_SUMMARY_PROVIDER_TIMEOUT_SECONDS"
)
WEEKLY_SUMMARY_PROVIDER_SHOW_RAW_DEBUG_ENV = (
    "FITNESS_AI_WEEKLY_SUMMARY_PROVIDER_SHOW_RAW_DEBUG"
)
DEFAULT_WEEKLY_SUMMARY_PROVIDER_TIMEOUT_SECONDS = 90.0
DEFAULT_WEEKLY_SUMMARY_PROVIDER_TEMPERATURE = 0.2
DEFAULT_WEEKLY_SUMMARY_PROVIDER_NUM_PREDICT = 700
PROVIDER_NAME = "weekly_coach_summary_provider_preview"

WeeklySummaryProviderTransport = Callable[[str, dict[str, Any], float], dict[str, Any]]


class WeeklyCoachSummaryProviderServiceError(ValueError):
    """Raised for safe Weekly Coach Summary provider preview failures."""


@dataclass(frozen=True)
class WeeklySummaryProviderPreviewConfig:
    enabled: bool
    model_name: str
    ollama_base_url: str
    timeout_seconds: float
    show_raw_debug: bool
    lifecycle_policy: ProviderLifecyclePolicy

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "model_name": self.model_name,
            "ollama_base_url": self.ollama_base_url,
            "timeout_seconds": self.timeout_seconds,
            "show_raw_debug": self.show_raw_debug,
            "lifecycle_policy": render_provider_lifecycle_summary(
                self.lifecycle_policy
            ),
            "raw_debug_default": False,
            "normal_ui_allowed": False,
            "manual_action_required": True,
        }


@dataclass(frozen=True)
class WeeklySummaryProviderValidationResult:
    approved: bool
    validation_errors: tuple[str, ...]
    safe_message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WeeklySummaryProviderPreviewResult:
    provider_attempted: bool
    provider_enabled: bool
    provider_model: str
    parse_status: str
    validation_status: str
    fallback_used: bool
    fallback_reason: str | None
    safe_message: str
    approved_summary: ApprovedWeeklyCoachSummary
    deterministic_summary: ApprovedWeeklyCoachSummary
    lifecycle_policy: dict[str, Any]
    unload_result: ProviderLifecycleActionResult | None = None
    validation_errors: tuple[str, ...] = ()
    candidate: CandidateWeeklyCoachSummaryProviderOutput | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_attempted": self.provider_attempted,
            "provider_enabled": self.provider_enabled,
            "provider_model": self.provider_model,
            "parse_status": self.parse_status,
            "validation_status": self.validation_status,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "safe_message": self.safe_message,
            "approved_summary": self.approved_summary.to_dict(),
            "approved_sections": approved_weekly_summary_to_public_sections(
                self.approved_summary
            ),
            "deterministic_summary": self.deterministic_summary.to_dict(),
            "deterministic_sections": approved_weekly_summary_to_public_sections(
                self.deterministic_summary
            ),
            "lifecycle_policy": self.lifecycle_policy,
            "unload_result": (
                self.unload_result.to_dict() if self.unload_result else None
            ),
            "validation_errors": list(self.validation_errors),
            "candidate": self.candidate.to_dict() if self.candidate else None,
        }


@dataclass(frozen=True)
class WeeklySummaryProviderInputBundle:
    payload: dict[str, Any]
    prompt: str
    response_schema: dict[str, Any]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "payload": self.payload,
            "response_schema": self.response_schema,
            "prompt_rendered_for_provider": True,
            "raw_rows_included": False,
            "raw_prompt_display_allowed": False,
        }


def resolve_weekly_summary_provider_preview_config(
    *,
    environ: Mapping[str, str] | None = None,
    model_name: str | None = None,
    base_url: str | None = None,
) -> WeeklySummaryProviderPreviewConfig:
    env = os.environ if environ is None else environ
    resolved_model = (
        model_name
        or env.get(WEEKLY_SUMMARY_PROVIDER_MODEL_ENV)
        or APPROVED_WEEKLY_PROVIDER_MODEL
    ).strip()
    if resolved_model != APPROVED_WEEKLY_PROVIDER_MODEL:
        raise WeeklyCoachSummaryProviderServiceError(
            "Weekly Coach Summary provider prototype only allows qwen2.5:3b."
        )
    timeout = _safe_timeout_seconds(
        env.get(WEEKLY_SUMMARY_PROVIDER_TIMEOUT_SECONDS_ENV),
        DEFAULT_WEEKLY_SUMMARY_PROVIDER_TIMEOUT_SECONDS,
    )
    policy = resolve_provider_lifecycle_policy(
        provider_name=PROVIDER_NAME,
        model_name=resolved_model,
        environ=env,
    )
    return WeeklySummaryProviderPreviewConfig(
        enabled=_env_bool(
            env.get(WEEKLY_SUMMARY_PROVIDER_PREVIEW_ENABLED_ENV), default=False
        ),
        model_name=resolved_model,
        ollama_base_url=resolve_ollama_base_url(base_url=base_url, environ=env),
        timeout_seconds=timeout,
        show_raw_debug=_env_bool(
            env.get(WEEKLY_SUMMARY_PROVIDER_SHOW_RAW_DEBUG_ENV), default=False
        ),
        lifecycle_policy=policy,
    )


def build_weekly_summary_provider_input(
    *,
    context: WeeklyCoachSummaryContext,
    deterministic_summary: ApprovedWeeklyCoachSummary,
) -> WeeklySummaryProviderInputBundle:
    """Build bounded provider input from backend-owned context only."""

    payload: dict[str, Any] = {
        "user_id": context.user_id,
        "scenario": context.scenario,
        "start_date": context.period.week_start.isoformat(),
        "end_date": context.period.week_end.isoformat(),
        "source": "qa_date_range_debug",
        "confidence": context.confidence.value,
        "data_quality_label": _data_quality_label(context),
        "limitations": list(context.limitations),
        "reason_codes": list(context.reason_codes),
        "fact_counts": _safe_fact_availability(context),
        "safe_recovery_summary": context.recovery_summary,
        "safe_nutrition_summary": context.nutrition_summary,
        "safe_training_summary": context.training_summary,
        "deterministic_baseline_summary": _deterministic_summary_text(
            deterministic_summary
        ),
        "voice_contract": (
            "Warm but not cheesy; plainspoken; coach-like but bounded; "
            "specific to the approved facts; use because-grounding; one clear next move; "
            "do not invent facts; confidence must match data quality."
        ),
        "output_schema_name": "CandidateWeeklyCoachSummaryProviderOutput",
    }
    assert_provider_input_is_design_safe(payload)
    schema = weekly_provider_output_json_schema()
    return WeeklySummaryProviderInputBundle(
        payload=payload,
        prompt=_render_provider_prompt(payload, schema),
        response_schema=schema,
    )


def generate_weekly_summary_provider_preview(
    *,
    context: WeeklyCoachSummaryContext,
    deterministic_summary: ApprovedWeeklyCoachSummary,
    config: WeeklySummaryProviderPreviewConfig | None = None,
    http_post: ProviderLifecycleHttpPost | None = None,
    unload_http_post: ProviderLifecycleHttpPost | None = None,
) -> WeeklySummaryProviderPreviewResult:
    """Run a manual Developer Mode-only provider preview with safe fallback.

    Automated tests should pass fake transports. Live Ollama is never required for
    deterministic paths or automated validation.
    """

    resolved_config = config or resolve_weekly_summary_provider_preview_config()
    lifecycle_summary = render_provider_lifecycle_summary(
        resolved_config.lifecycle_policy
    )

    if not resolved_config.enabled:
        return _fallback_result(
            context=context,
            deterministic_summary=deterministic_summary,
            config=resolved_config,
            lifecycle_summary=lifecycle_summary,
            provider_attempted=False,
            parse_status="not_attempted",
            validation_status="not_attempted",
            fallback_reason="provider_preview_disabled",
            safe_message=(
                "Weekly Coach Summary provider preview is disabled by configuration."
            ),
        )

    if _context_too_sparse_for_provider(context):
        return _fallback_result(
            context=context,
            deterministic_summary=deterministic_summary,
            config=resolved_config,
            lifecycle_summary=lifecycle_summary,
            provider_attempted=False,
            parse_status="not_attempted",
            validation_status="not_attempted",
            fallback_reason="context_insufficient_for_provider",
            safe_message=(
                "Selected context is too sparse for provider preview; deterministic fallback remains authoritative."
            ),
        )

    bundle = build_weekly_summary_provider_input(
        context=context,
        deterministic_summary=deterministic_summary,
    )
    endpoint = f"{resolved_config.ollama_base_url.rstrip('/')}/api/generate"
    request_payload = build_ollama_generate_payload(
        model_name=resolved_config.model_name,
        prompt=bundle.prompt,
        response_schema=bundle.response_schema,
        stream=False,
        options={
            "temperature": DEFAULT_WEEKLY_SUMMARY_PROVIDER_TEMPERATURE,
            "num_predict": DEFAULT_WEEKLY_SUMMARY_PROVIDER_NUM_PREDICT,
        },
        policy=resolved_config.lifecycle_policy,
    )
    post = http_post or _http_post_json
    unload_result: ProviderLifecycleActionResult | None = None
    try:
        response_body = post(endpoint, request_payload, resolved_config.timeout_seconds)
        raw_candidate = _extract_ollama_response_text(response_body)
    except urllib.error.URLError as exc:
        return _fallback_result(
            context=context,
            deterministic_summary=deterministic_summary,
            config=resolved_config,
            lifecycle_summary=lifecycle_summary,
            provider_attempted=True,
            parse_status="not_attempted",
            validation_status="not_attempted",
            fallback_reason="provider_unreachable",
            safe_message="Ollama was unreachable; deterministic fallback remains active.",
            validation_errors=(type(exc).__name__,),
        )
    except Exception as exc:  # noqa: BLE001 - sanitized category only
        return _fallback_result(
            context=context,
            deterministic_summary=deterministic_summary,
            config=resolved_config,
            lifecycle_summary=lifecycle_summary,
            provider_attempted=True,
            parse_status="not_attempted",
            validation_status="not_attempted",
            fallback_reason="provider_generation_error",
            safe_message="Provider generation failed safely; deterministic fallback remains active.",
            validation_errors=(type(exc).__name__,),
        )
    finally:
        # keep_alive=0 already requests unload. If a configured policy keeps the
        # model briefly but still requires unload_after_request, this sends a
        # named-model-only unload request. Failures are surfaced below.
        try:
            unload_result = maybe_unload_model_after_request(
                model_name=resolved_config.model_name,
                policy=resolved_config.lifecycle_policy,
                base_url=resolved_config.ollama_base_url,
                http_post=unload_http_post,
            )
        except Exception as exc:  # noqa: BLE001 - sanitized category only
            unload_result = ProviderLifecycleActionResult(
                success=False,
                action="unload_after_request_failure",
                provider_name=PROVIDER_NAME,
                model_name=resolved_config.model_name,
                ollama_base_url=resolved_config.ollama_base_url,
                attempted=True,
                safe_message="Lifecycle unload handling failed safely.",
                error_category=type(exc).__name__,
                keep_alive_value=resolved_config.lifecycle_policy.keep_alive_value,
            )

    try:
        candidate = parse_candidate_weekly_provider_output_json(raw_candidate)
    except WeeklyCoachSummaryProviderModelError as exc:
        return _fallback_result(
            context=context,
            deterministic_summary=deterministic_summary,
            config=resolved_config,
            lifecycle_summary=lifecycle_summary,
            provider_attempted=True,
            parse_status="failed",
            validation_status="not_attempted",
            fallback_reason="provider_parse_failed",
            safe_message="Provider response did not parse as approved JSON; deterministic fallback remains active.",
            validation_errors=(str(exc),),
            unload_result=unload_result,
        )

    # Backend remains the source of truth for provenance. Live small models can
    # omit or slightly misformat source metadata, so canonicalize it from the
    # selected backend context before validation/display instead of trusting
    # model-provided metadata.
    candidate = _candidate_with_authoritative_context_metadata(candidate, context)

    validation = validate_weekly_summary_provider_candidate(
        candidate=candidate,
        context=context,
    )
    if not validation.approved:
        return _fallback_result(
            context=context,
            deterministic_summary=deterministic_summary,
            config=resolved_config,
            lifecycle_summary=lifecycle_summary,
            provider_attempted=True,
            parse_status="parsed",
            validation_status="rejected",
            fallback_reason="provider_validation_rejected",
            safe_message=validation.safe_message,
            validation_errors=validation.validation_errors,
            candidate=None,
            unload_result=unload_result,
        )

    if unload_result is not None and not unload_result.success:
        return _fallback_result(
            context=context,
            deterministic_summary=deterministic_summary,
            config=resolved_config,
            lifecycle_summary=lifecycle_summary,
            provider_attempted=True,
            parse_status="parsed",
            validation_status="rejected",
            fallback_reason="provider_lifecycle_unload_failed",
            safe_message=(
                "Provider candidate parsed, but lifecycle unload did not complete safely; deterministic fallback remains active."
            ),
            validation_errors=(unload_result.safe_message,),
            unload_result=unload_result,
        )

    approved = _candidate_to_approved_summary(candidate, context)
    return WeeklySummaryProviderPreviewResult(
        provider_attempted=True,
        provider_enabled=True,
        provider_model=resolved_config.model_name,
        parse_status="parsed",
        validation_status="approved",
        fallback_used=False,
        fallback_reason=None,
        safe_message="Provider candidate parsed and validated for Developer Mode preview.",
        approved_summary=approved,
        deterministic_summary=deterministic_summary,
        lifecycle_policy=lifecycle_summary,
        unload_result=unload_result,
        validation_errors=(),
        candidate=candidate,
    )


def validate_weekly_summary_provider_candidate(
    *,
    candidate: CandidateWeeklyCoachSummaryProviderOutput,
    context: WeeklyCoachSummaryContext,
) -> WeeklySummaryProviderValidationResult:
    errors: list[str] = []
    text_values = (
        candidate.title,
        candidate.summary,
        candidate.recovery_note,
        candidate.nutrition_note,
        candidate.training_note,
        candidate.next_action,
        *candidate.facts_used,
        *candidate.data_limitations,
        *candidate.safety_flags,
    )
    rendered = "\n".join(text_values).lower()
    forbidden_phrases = (
        "medical diagnosis",
        "diagnosed",
        "you failed",
        "lack of discipline",
        "burn this off",
        "compensate tomorrow",
        "chain of thought",
        "scratchpad",
        # Do not reject safe statements like "raw rows are excluded" in
        # limitations/safety flags. Actual raw payload leakage is still blocked
        # by the provider input contract, metadata checks, and the more specific
        # forbidden markers below.
        "raw database",
        "raw food",
        "raw check-in",
        "prompt:",
        "optimize your journey",
        "optimized",
        "perfect recovery",
        "excellent recovery",
    )
    for phrase in forbidden_phrases:
        if phrase in rendered:
            errors.append(f"forbidden_phrase:{phrase}")

    if not _has_because_grounding(text_values):
        errors.append("missing_because_grounding")

    if _is_low_data_context(context) and candidate.confidence_label not in {
        ProviderConfidenceLabel.LIMITED,
        ProviderConfidenceLabel.LOW,
    }:
        errors.append("overconfident_low_data_candidate")

    progression_terms = (
        "set progression",
        "progressed your sets",
        "training intensity improved",
        "increased load",
        "lifted heavier",
        "actual set progression",
    )
    if any(term in rendered for term in progression_terms):
        errors.append("unsupported_training_progression_without_actual_sets")

    metadata = candidate.source_context_metadata
    if str(metadata.get("user_id")) != str(context.user_id):
        errors.append("source_context_user_mismatch")
    if metadata.get("start_date") != context.period.week_start.isoformat():
        errors.append("source_context_start_date_mismatch")
    if metadata.get("end_date") != context.period.week_end.isoformat():
        errors.append("source_context_end_date_mismatch")
    if metadata.get("source") != "qa_date_range_debug":
        errors.append("source_context_source_mismatch")

    if len(candidate.next_action.split()) > 60:
        errors.append("next_action_too_long")

    if errors:
        return WeeklySummaryProviderValidationResult(
            approved=False,
            validation_errors=tuple(dict.fromkeys(errors)),
            safe_message="Provider candidate was rejected by grounding/safety validation.",
        )
    return WeeklySummaryProviderValidationResult(
        approved=True,
        validation_errors=(),
        safe_message="Provider candidate is grounded and Developer Mode preview-safe.",
    )


def weekly_provider_preview_result_to_display_rows(
    result: WeeklySummaryProviderPreviewResult | dict[str, Any],
) -> list[dict[str, str]]:
    payload = result.to_dict() if hasattr(result, "to_dict") else dict(result)
    unload = payload.get("unload_result") or {}
    return [
        {
            "Field": "Provider Enabled",
            "Value": str(payload.get("provider_enabled")).lower(),
        },
        {
            "Field": "Provider Attempted",
            "Value": str(payload.get("provider_attempted")).lower(),
        },
        {"Field": "Provider Model", "Value": str(payload.get("provider_model"))},
        {"Field": "Parse Status", "Value": str(payload.get("parse_status"))},
        {"Field": "Validation Status", "Value": str(payload.get("validation_status"))},
        {"Field": "Fallback Used", "Value": str(payload.get("fallback_used")).lower()},
        {
            "Field": "Fallback Reason",
            "Value": str(payload.get("fallback_reason") or ""),
        },
        {"Field": "Unload Action", "Value": str(unload.get("action", ""))},
        {"Field": "Unload Success", "Value": str(unload.get("success", "")).lower()},
        {"Field": "Unload Message", "Value": str(unload.get("safe_message", ""))},
    ]


def _fallback_result(
    *,
    context: WeeklyCoachSummaryContext,
    deterministic_summary: ApprovedWeeklyCoachSummary,
    config: WeeklySummaryProviderPreviewConfig,
    lifecycle_summary: dict[str, Any],
    provider_attempted: bool,
    parse_status: str,
    validation_status: str,
    fallback_reason: str,
    safe_message: str,
    validation_errors: tuple[str, ...] = (),
    candidate: CandidateWeeklyCoachSummaryProviderOutput | None = None,
    unload_result: ProviderLifecycleActionResult | None = None,
) -> WeeklySummaryProviderPreviewResult:
    return WeeklySummaryProviderPreviewResult(
        provider_attempted=provider_attempted,
        provider_enabled=config.enabled,
        provider_model=config.model_name,
        parse_status=parse_status,
        validation_status=validation_status,
        fallback_used=True,
        fallback_reason=fallback_reason,
        safe_message=safe_message,
        approved_summary=deterministic_summary,
        deterministic_summary=deterministic_summary,
        lifecycle_policy=lifecycle_summary,
        unload_result=unload_result,
        validation_errors=tuple(dict.fromkeys(validation_errors)),
        candidate=candidate,
    )


def _candidate_with_authoritative_context_metadata(
    candidate: CandidateWeeklyCoachSummaryProviderOutput,
    context: WeeklyCoachSummaryContext,
) -> CandidateWeeklyCoachSummaryProviderOutput:
    """Return candidate with backend-owned selected-range provenance.

    The provider is allowed to improve wording, not to define truth/provenance.
    This keeps validation stable while ensuring any displayed candidate carries
    the selected user/date/source from the backend context.
    """

    return CandidateWeeklyCoachSummaryProviderOutput(
        title=candidate.title,
        summary=candidate.summary,
        recovery_note=candidate.recovery_note,
        nutrition_note=candidate.nutrition_note,
        training_note=candidate.training_note,
        next_action=candidate.next_action,
        confidence_label=candidate.confidence_label,
        data_limitations=candidate.data_limitations,
        facts_used=candidate.facts_used,
        safety_flags=candidate.safety_flags,
        provider_model=candidate.provider_model,
        source_context_metadata={
            "user_id": context.user_id,
            "start_date": context.period.week_start.isoformat(),
            "end_date": context.period.week_end.isoformat(),
            "source": "qa_date_range_debug",
        },
        generated_at=candidate.generated_at,
    )


def _candidate_to_approved_summary(
    candidate: CandidateWeeklyCoachSummaryProviderOutput,
    context: WeeklyCoachSummaryContext,
) -> ApprovedWeeklyCoachSummary:
    return ApprovedWeeklyCoachSummary(
        headline=candidate.title,
        weekly_overview=candidate.summary,
        recovery_observation=candidate.recovery_note,
        nutrition_observation=candidate.nutrition_note,
        training_observation=candidate.training_note,
        primary_pattern=(
            "Provider wording stayed grounded in the selected QA date-range context."
        ),
        recommended_focus=candidate.next_action,
        next_week_guidance=candidate.next_action,
        confidence=WeeklyCoachSummaryConfidence(candidate.confidence_label.value),
        source=WeeklyCoachSummarySource.PROVIDER_APPROVED,
        public_safe=True,
        displayable=True,
        reason_codes=tuple(
            dict.fromkeys(
                (
                    *context.reason_codes,
                    "provider_candidate_parsed",
                    "provider_candidate_validated",
                    "developer_mode_provider_preview_only",
                )
            )
        ),
        limitations=tuple(
            dict.fromkeys(
                (
                    *context.limitations,
                    *candidate.data_limitations,
                    "Provider candidate is Developer Mode preview output only.",
                )
            )
        ),
    )


def _render_provider_prompt(payload: dict[str, Any], schema: dict[str, Any]) -> str:
    return (
        "You are improving the wording of a Weekly Coach Summary. "
        "Use only the approved backend facts in the JSON payload. "
        "Return JSON only. Do not include markdown, prose wrappers, chain-of-thought, raw rows, prompts, or unsupported claims. "
        "Use warm, plainspoken coach language grounded in because-statements. "
        "Respect data quality and limitations. If actual sets are zero, do not claim set-level progression.\n\n"
        "APPROVED_PROVIDER_INPUT_JSON:\n"
        f"{json.dumps(payload, sort_keys=True)}\n\n"
        "REQUIRED_OUTPUT_JSON_SCHEMA:\n"
        f"{json.dumps(schema, sort_keys=True)}"
    )


def _extract_ollama_response_text(response_body: dict[str, Any]) -> str:
    if not isinstance(response_body, dict):
        raise WeeklyCoachSummaryProviderServiceError(
            "Ollama response was not a JSON object."
        )
    response = response_body.get("response")
    if not isinstance(response, str) or not response.strip():
        raise WeeklyCoachSummaryProviderServiceError(
            "Ollama response did not contain text in the response field."
        )
    return response.strip()


def _data_quality_label(context: WeeklyCoachSummaryContext) -> str:
    if _is_low_data_context(context):
        return "limited"
    if context.confidence == WeeklyCoachSummaryConfidence.HIGH:
        return "strong"
    if context.confidence == WeeklyCoachSummaryConfidence.MODERATE:
        return "usable"
    return "limited"


def _safe_fact_availability(context: WeeklyCoachSummaryContext) -> dict[str, Any]:
    return {
        "recovery_facts_available": context.fact_boundary.recovery_facts_available,
        "nutrition_facts_available": context.fact_boundary.nutrition_facts_available,
        "training_facts_available": context.fact_boundary.training_facts_available,
        "workout_execution_facts_available": context.fact_boundary.workout_execution_facts_available,
        "data_quality_limited": context.fact_boundary.data_quality_limited,
    }


def _deterministic_summary_text(summary: ApprovedWeeklyCoachSummary) -> str:
    return " ".join(
        (
            summary.headline,
            summary.weekly_overview,
            summary.recovery_observation,
            summary.nutrition_observation,
            summary.training_observation,
            summary.recommended_focus,
            summary.next_week_guidance,
        )
    )


def _context_too_sparse_for_provider(context: WeeklyCoachSummaryContext) -> bool:
    return (
        not context.fact_boundary.recovery_facts_available
        and not context.fact_boundary.nutrition_facts_available
        and not context.fact_boundary.training_facts_available
    )


def _is_low_data_context(context: WeeklyCoachSummaryContext) -> bool:
    return (
        context.fact_boundary.data_quality_limited
        or context.confidence
        in {WeeklyCoachSummaryConfidence.LIMITED, WeeklyCoachSummaryConfidence.LOW}
        or (context.scenario or "").lower() == "data_quality_limited"
    )


def _has_because_grounding(values: tuple[str, ...] | list[str]) -> bool:
    rendered = " ".join(str(value).lower() for value in values)
    return any(marker in rendered for marker in ("because", " so ", " since "))


def _safe_timeout_seconds(value: str | None, default: float) -> float:
    if value is None or not str(value).strip():
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise WeeklyCoachSummaryProviderServiceError(
            "Provider timeout must be numeric seconds."
        ) from exc
    return max(5.0, min(parsed, 180.0))


def _env_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _http_post_json(
    url: str, payload: dict[str, Any], timeout_seconds: float
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
