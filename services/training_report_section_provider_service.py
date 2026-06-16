from __future__ import annotations

import os
from typing import Any

from models.training_report_section_models import (
    ApprovedTrainingReportSection,
    ApprovedTrainingReportSectionResult,
    TrainingReportSectionRuntimeMetadata,
)
from services.training_report_section_direct_ollama_provider import (
    DirectOllamaGenerateCallable,
    build_training_report_section_context,
    call_direct_ollama_generate,
    run_direct_ollama_training_report_section_provider,
)

TRAINING_REPORT_SECTION_PROVIDER_ENV = "TRAINING_REPORT_SECTION_PROVIDER"
TRAINING_REPORT_SECTION_MODEL_ENV = "TRAINING_REPORT_SECTION_MODEL"
TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_ENV = (
    "TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS"
)

TRAINING_REPORT_SECTION_PROVIDER_DETERMINISTIC = "deterministic"
TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA = "direct_ollama"
TRAINING_REPORT_SECTION_DEFAULT_MODEL = "ollama/qwen2.5:3b"
TRAINING_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS = 60.0

FINAL_SECTION_SOURCE_DETERMINISTIC = "deterministic"
FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED = "direct_ollama_approved"
FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"

FALLBACK_REASON_DETERMINISTIC_SELECTED = "deterministic_provider_selected"
FALLBACK_REASON_FULL_REPORT_PROVIDER_DISABLED = (
    "full_report_training_section_provider_disabled"
)
FALLBACK_REASON_INVALID_PROVIDER = "invalid_provider"
FALLBACK_REASON_PROVIDER_EXCEPTION = "provider_exception"
FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE = "candidate_validation_failure"
FALLBACK_REASON_APPROVED_CONTEXT_MISSING_TRAINING_EVIDENCE = (
    "approved_context_missing_training_evidence"
)

TRAINING_SECTION_PARSE_STATUS_NOT_ATTEMPTED = "not_attempted"
TRAINING_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED = "not_attempted"
TRAINING_SECTION_STATUS_NOT_ATTEMPTED = "not_attempted"


def build_configured_training_report_section_with_metadata(
    *,
    user_id: int,
    report_date: str,
    approved_context: dict[str, Any] | None = None,
    direct_ollama_generate: DirectOllamaGenerateCallable | None = None,
) -> ApprovedTrainingReportSectionResult:
    """Build a training report section using configured provider settings.

    Deterministic remains the default. The direct Ollama training section provider is
    opt-in, qwen2.5-first, and bounded by the v4.3 quote-only anchor-first contract,
    strict validation, and deterministic fallback.
    """

    configured_provider = _configured_training_report_section_provider()
    resolved_context = approved_context or build_training_report_section_context(
        user_id=user_id,
        report_date=report_date,
    )

    if configured_provider == TRAINING_REPORT_SECTION_PROVIDER_DETERMINISTIC:
        return build_deterministic_training_report_section_with_metadata(
            user_id=user_id,
            report_date=report_date,
            configured_provider=configured_provider,
            fallback_used=False,
            fallback_reason=FALLBACK_REASON_DETERMINISTIC_SELECTED,
            final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC,
        )

    if configured_provider == TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA:
        return build_direct_ollama_training_report_section_or_fallback(
            user_id=user_id,
            report_date=report_date,
            approved_context=resolved_context,
            generate=direct_ollama_generate or call_direct_ollama_generate,
        )

    metadata = _runtime_metadata(
        user_id=user_id,
        report_date=report_date,
        configured_provider=configured_provider,
        selected_provider=TRAINING_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        configured_model=TRAINING_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        selected_model=TRAINING_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        provider_attempted=False,
        fallback_used=True,
        fallback_reason=FALLBACK_REASON_INVALID_PROVIDER,
        candidate_valid=True,
        validation_errors=[f"Unsupported provider: {configured_provider}"],
        candidate_parse_status=TRAINING_SECTION_PARSE_STATUS_NOT_ATTEMPTED,
        candidate_validation_status=TRAINING_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED,
        validation_status=TRAINING_SECTION_STATUS_NOT_ATTEMPTED,
        final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
    )
    return _result_from_section_payload(
        _deterministic_training_report_section_payload(),
        metadata=metadata,
        source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
    )


def build_deterministic_training_report_section_with_metadata(
    *,
    user_id: int,
    report_date: str,
    configured_provider: str = TRAINING_REPORT_SECTION_PROVIDER_DETERMINISTIC,
    fallback_used: bool = False,
    fallback_reason: str | None = FALLBACK_REASON_DETERMINISTIC_SELECTED,
    final_section_source: str = FINAL_SECTION_SOURCE_DETERMINISTIC,
) -> ApprovedTrainingReportSectionResult:
    """Build the deterministic training section without reading provider config.

    This is used by full-report integration when its higher-level opt-in gate is
    disabled. It prevents a globally configured direct_ollama training provider
    from being attempted inside full report generation unless the full-report gate
    is explicitly enabled.
    """

    metadata = _runtime_metadata(
        user_id=user_id,
        report_date=report_date,
        configured_provider=configured_provider,
        selected_provider=TRAINING_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        configured_model=TRAINING_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        selected_model=TRAINING_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        provider_attempted=False,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        candidate_valid=True,
        validation_errors=[],
        candidate_parse_status=TRAINING_SECTION_PARSE_STATUS_NOT_ATTEMPTED,
        candidate_validation_status=TRAINING_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED,
        validation_status=TRAINING_SECTION_STATUS_NOT_ATTEMPTED,
        final_section_source=final_section_source,
    )
    return _result_from_section_payload(
        _deterministic_training_report_section_payload(),
        metadata=metadata,
        source=final_section_source,
    )


def build_configured_training_report_section(
    *,
    user_id: int,
    report_date: str,
) -> ApprovedTrainingReportSection:
    """Return only the public approved training report section."""

    return build_configured_training_report_section_with_metadata(
        user_id=user_id,
        report_date=report_date,
    ).approved_section


def build_direct_ollama_training_report_section_or_fallback(
    *,
    user_id: int,
    report_date: str,
    approved_context: dict[str, Any],
    generate: DirectOllamaGenerateCallable = call_direct_ollama_generate,
) -> ApprovedTrainingReportSectionResult:
    """Run the opt-in direct Ollama training provider and convert to service result."""

    provider_result = run_direct_ollama_training_report_section_provider(
        model=_configured_training_report_section_model(),
        user_id=user_id,
        report_date=report_date,
        approved_context=approved_context,
        generate=generate,
        timeout_seconds=_configured_direct_ollama_timeout_seconds(),
    )
    source = (
        FINAL_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED
        if provider_result.success
        else FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK
    )
    metadata = _metadata_from_provider_result(
        provider_result,
        configured_provider=TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
        selected_provider=TRAINING_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
        final_section_source=source,
    )
    return _result_from_section_payload(
        provider_result.approved_section,
        metadata=metadata,
        source=source,
    )


def _configured_training_report_section_provider() -> str:
    return (
        os.getenv(
            TRAINING_REPORT_SECTION_PROVIDER_ENV,
            TRAINING_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        )
        .strip()
        .lower()
    )


def _configured_training_report_section_model() -> str:
    return os.getenv(
        TRAINING_REPORT_SECTION_MODEL_ENV,
        TRAINING_REPORT_SECTION_DEFAULT_MODEL,
    ).strip()


def _configured_direct_ollama_timeout_seconds() -> float:
    raw = os.getenv(TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_ENV)
    if not raw:
        return TRAINING_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        return TRAINING_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS
    return value if value > 0 else TRAINING_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS


def _metadata_from_provider_result(
    provider_result: Any,
    *,
    configured_provider: str,
    selected_provider: str,
    final_section_source: str,
) -> TrainingReportSectionRuntimeMetadata:
    return _runtime_metadata(
        user_id=provider_result.user_id,
        report_date=provider_result.report_date,
        configured_provider=configured_provider,
        selected_provider=selected_provider,
        configured_model=provider_result.configured_model,
        selected_model=provider_result.selected_model,
        provider_attempted=provider_result.provider_attempted,
        fallback_used=provider_result.fallback_used,
        fallback_reason=provider_result.fallback_reason,
        candidate_valid=provider_result.candidate_valid,
        validation_errors=list(provider_result.validation_errors),
        candidate_parse_status=provider_result.candidate_parse_status,
        candidate_validation_status=provider_result.candidate_validation_status,
        validation_status=provider_result.validation_status,
        final_section_source=final_section_source,
        raw_output_length=provider_result.raw_output_length,
        raw_output_preview_truncated=provider_result.raw_output_preview_truncated,
        markdown_wrapper_detected=provider_result.markdown_wrapper_detected,
        extra_keys_detected=list(provider_result.extra_keys_detected),
        wrapper_object_detected=provider_result.wrapper_object_detected,
        elapsed_seconds=provider_result.elapsed_seconds,
        provider_latency_ms=_provider_latency_ms(provider_result.elapsed_seconds),
        required_anchor_count=provider_result.required_anchor_count,
        matched_required_fact_anchors=list(
            provider_result.matched_required_fact_anchors
        ),
        missing_required_anchor_count=provider_result.missing_required_anchor_count,
        matched_approved_interpretation_claims=list(
            provider_result.matched_approved_interpretation_claims
        ),
        model_facing_quote_context=dict(provider_result.model_facing_quote_context),
        approved_training_quote_context=dict(
            provider_result.approved_training_quote_context
        ),
    )


def _provider_latency_ms(elapsed_seconds: float | None) -> int | None:
    if elapsed_seconds is None:
        return None
    return int(round(elapsed_seconds * 1000))


def _runtime_metadata(**kwargs: Any) -> TrainingReportSectionRuntimeMetadata:
    return TrainingReportSectionRuntimeMetadata(**kwargs)


def _result_from_section_payload(
    payload: dict[str, Any],
    *,
    metadata: TrainingReportSectionRuntimeMetadata,
    source: str,
) -> ApprovedTrainingReportSectionResult:
    return ApprovedTrainingReportSectionResult(
        approved_section=ApprovedTrainingReportSection.from_payload(
            payload,
            source=source,
        ),
        runtime_metadata=metadata,
    )


def _deterministic_training_report_section_payload() -> dict[str, Any]:
    return {
        "section_summary": "Training context is available from backend-approved workout execution data.",
        "key_observations": [
            "Workout execution summaries remain backend-owned and should be interpreted conservatively."
        ],
        "performance_interpretation": (
            "Use the approved training summary to review completion, effort, and logging quality."
        ),
        "fatigue_recovery_interpretation": (
            "Recovery and fatigue context should stay bounded by logged readiness and execution data."
        ),
        "suggested_focus": "Keep workout logging consistent before changing training direction.",
        "limitations_context": (
            "This deterministic fallback does not add AI-generated training claims."
        ),
        "confidence": "Limited",
        "reason_codes": ["deterministic_training_report_section_fallback"],
    }
