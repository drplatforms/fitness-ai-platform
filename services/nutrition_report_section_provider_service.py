from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from models.nutrition_provider_contract_models import (
    NUTRITION_PROVIDER_FALLBACK_REASON_INVALID_PROVIDER,
    NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_DISABLED,
    NUTRITION_PROVIDER_FALLBACK_SOURCE,
)
from models.nutrition_report_section_models import (
    ApprovedNutritionReportSection,
    NutritionReportEvidenceContext,
)
from services.nutrition_provider_validation_service import (
    build_nutrition_provider_safe_context,
    build_nutrition_provider_safe_metadata,
)
from services.nutrition_report_section_direct_ollama_provider import (
    DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_APPROVED,
    DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_FALLBACK,
    DirectOllamaGenerateCallable,
    call_direct_ollama_generate,
    run_direct_ollama_nutrition_report_section_provider,
)
from services.nutrition_report_section_service import (
    build_deterministic_nutrition_report_section,
    build_nutrition_report_evidence_context,
)

AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV = (
    "AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED"
)
NUTRITION_REPORT_SECTION_PROVIDER_ENV = "NUTRITION_REPORT_SECTION_PROVIDER"
NUTRITION_REPORT_SECTION_MODEL_ENV = "NUTRITION_REPORT_SECTION_MODEL"
NUTRITION_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_ENV = (
    "NUTRITION_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS"
)

NUTRITION_REPORT_SECTION_PROVIDER_DETERMINISTIC = "deterministic"
NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA = "direct_ollama"
NUTRITION_REPORT_SECTION_DEFAULT_MODEL = "ollama/qwen2.5:3b"
NUTRITION_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS = 300.0

NUTRITION_SECTION_SOURCE_DETERMINISTIC = "deterministic"
NUTRITION_SECTION_SOURCE_DIRECT_OLLAMA_APPROVED = (
    DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_APPROVED
)
NUTRITION_SECTION_SOURCE_DETERMINISTIC_FALLBACK = (
    DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_FALLBACK
)


@dataclass(frozen=True)
class NutritionReportSectionProviderResult:
    approved_section: ApprovedNutritionReportSection
    safe_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved_section": self.approved_section.to_dict(),
            "safe_metadata": dict(self.safe_metadata),
        }


def build_configured_nutrition_report_section_with_metadata(
    *,
    user_id: int,
    report_date: str,
    evidence_context: NutritionReportEvidenceContext | None = None,
    direct_ollama_generate: DirectOllamaGenerateCallable | None = None,
) -> NutritionReportSectionProviderResult:
    """Build nutrition report section through deterministic or opt-in provider path.

    Deterministic remains the default. The nutrition direct_ollama path is isolated,
    config-gated, fake-generator testable, and does not integrate Nutrition into the
    async full-report provider path or promote Nutrition to Level 5.
    """

    resolved_context = evidence_context or build_nutrition_report_evidence_context(
        user_id=user_id,
        report_date=report_date,
    )
    provider_enabled = _nutrition_provider_enabled()
    configured_provider = _configured_nutrition_report_section_provider()

    if not provider_enabled:
        return build_deterministic_nutrition_report_section_with_metadata(
            evidence_context=resolved_context,
            provider_enabled=False,
            selected_provider=NUTRITION_REPORT_SECTION_PROVIDER_DETERMINISTIC,
            selected_model=NUTRITION_REPORT_SECTION_PROVIDER_DETERMINISTIC,
            fallback_used=False,
            fallback_reason=None,
            nutrition_section_source=NUTRITION_SECTION_SOURCE_DETERMINISTIC,
        )

    if configured_provider == NUTRITION_REPORT_SECTION_PROVIDER_DETERMINISTIC:
        return build_deterministic_nutrition_report_section_with_metadata(
            evidence_context=resolved_context,
            provider_enabled=True,
            selected_provider=NUTRITION_REPORT_SECTION_PROVIDER_DETERMINISTIC,
            selected_model=NUTRITION_REPORT_SECTION_PROVIDER_DETERMINISTIC,
            fallback_used=False,
            fallback_reason=NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_DISABLED,
            nutrition_section_source=NUTRITION_SECTION_SOURCE_DETERMINISTIC,
        )

    if configured_provider == NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA:
        provider_result = run_direct_ollama_nutrition_report_section_provider(
            model=_configured_nutrition_report_section_model(),
            user_id=user_id,
            report_date=report_date,
            evidence_context=resolved_context,
            generate=direct_ollama_generate or call_direct_ollama_generate,
            timeout_seconds=_configured_direct_ollama_timeout_seconds(),
        )
        return NutritionReportSectionProviderResult(
            approved_section=provider_result.approved_section,
            safe_metadata=dict(provider_result.safe_metadata),
        )

    return build_deterministic_nutrition_report_section_with_metadata(
        evidence_context=resolved_context,
        provider_enabled=True,
        selected_provider=NUTRITION_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        selected_model=NUTRITION_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        fallback_used=True,
        fallback_reason=NUTRITION_PROVIDER_FALLBACK_REASON_INVALID_PROVIDER,
        nutrition_section_source=NUTRITION_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
    )


def build_configured_nutrition_report_section(
    *,
    user_id: int,
    report_date: str,
) -> ApprovedNutritionReportSection:
    return build_configured_nutrition_report_section_with_metadata(
        user_id=user_id,
        report_date=report_date,
    ).approved_section


def build_deterministic_nutrition_report_section_with_metadata(
    *,
    evidence_context: NutritionReportEvidenceContext,
    provider_enabled: bool = False,
    selected_provider: str | None = NUTRITION_REPORT_SECTION_PROVIDER_DETERMINISTIC,
    selected_model: str | None = NUTRITION_REPORT_SECTION_PROVIDER_DETERMINISTIC,
    fallback_used: bool = False,
    fallback_reason: str | None = None,
    nutrition_section_source: str = NUTRITION_SECTION_SOURCE_DETERMINISTIC,
) -> NutritionReportSectionProviderResult:
    section = build_deterministic_nutrition_report_section(evidence_context)
    safe_context = build_nutrition_provider_safe_context(evidence_context)
    safe_metadata = build_nutrition_provider_safe_metadata(
        safe_context=safe_context,
        provider_enabled=provider_enabled,
        provider_attempted=False,
        selected_provider=selected_provider,
        selected_model=selected_model,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        fallback_source=NUTRITION_PROVIDER_FALLBACK_SOURCE if fallback_used else None,
        nutrition_section_source=nutrition_section_source,
        provider_latency_ms=None,
    )
    return NutritionReportSectionProviderResult(
        approved_section=section,
        safe_metadata=safe_metadata,
    )


def _nutrition_provider_enabled() -> bool:
    raw = os.getenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _configured_nutrition_report_section_provider() -> str:
    return (
        os.getenv(
            NUTRITION_REPORT_SECTION_PROVIDER_ENV,
            NUTRITION_REPORT_SECTION_PROVIDER_DETERMINISTIC,
        )
        .strip()
        .lower()
    )


def _configured_nutrition_report_section_model() -> str:
    return os.getenv(
        NUTRITION_REPORT_SECTION_MODEL_ENV,
        NUTRITION_REPORT_SECTION_DEFAULT_MODEL,
    ).strip()


def _configured_direct_ollama_timeout_seconds() -> float:
    raw = os.getenv(NUTRITION_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_ENV)
    if not raw:
        return NUTRITION_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        return NUTRITION_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS
    return value if value > 0 else NUTRITION_REPORT_SECTION_DEFAULT_TIMEOUT_SECONDS
