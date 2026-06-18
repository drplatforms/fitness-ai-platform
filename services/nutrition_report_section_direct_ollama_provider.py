from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from models.nutrition_provider_contract_models import (
    NUTRITION_PROVIDER_FALLBACK_REASON_PARSE_FAILED,
    NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_EXCEPTION,
    NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT,
    NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_TIMEOUT,
    NUTRITION_PROVIDER_FALLBACK_REASON_QA_FORCED_INVALID_PROVIDER_OUTPUT,
    NUTRITION_PROVIDER_FALLBACK_REASON_VALIDATION_FAILED,
    NUTRITION_PROVIDER_FALLBACK_SOURCE,
    NUTRITION_PROVIDER_VALIDATION_STATUS_REJECTED,
)
from models.nutrition_report_section_models import (
    ApprovedNutritionReportSection,
    NutritionReportEvidenceContext,
)
from services import ai_nutrition_explanation_service as explanation_service
from services.nutrition_provider_candidate_parser import (
    parse_candidate_nutrition_report_section,
)
from services.nutrition_provider_validation_service import (
    build_nutrition_provider_safe_context,
    build_nutrition_provider_safe_metadata,
    validate_candidate_nutrition_report_section,
    validation_error_categories_from_errors,
    validation_error_fields_from_errors,
)
from services.nutrition_report_section_service import (
    build_deterministic_nutrition_report_section,
    derive_approved_nutrition_claims,
)

AI_HEALTH_REPORT_NUTRITION_FORCE_INVALID_PROVIDER_OUTPUT_ENV = (
    "AI_HEALTH_REPORT_NUTRITION_FORCE_INVALID_PROVIDER_OUTPUT"
)

DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_PROVIDER_NAME = "direct_ollama"
DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_APPROVED = "direct_ollama_approved"
DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_FALLBACK = (
    "deterministic_nutrition_report_section_fallback"
)
DIRECT_OLLAMA_NUTRITION_DEFAULT_BASE_URL = (
    explanation_service.NUTRITION_EXPLANATION_DEFAULT_BASE_URL
)

DirectOllamaGenerateCallable = explanation_service.DirectOllamaGenerateCallable
normalize_ollama_model_name = explanation_service.normalize_ollama_model_name
call_direct_ollama_generate = explanation_service.call_direct_ollama_generate

CANDIDATE_NUTRITION_REPORT_SECTION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "section_summary",
        "intake_snapshot",
        "target_alignment",
        "logging_quality",
        "practical_food_focus",
        "next_nutrition_action",
        "limitations_context",
        "confidence",
        "reason_codes",
    ],
    "properties": {
        "section_summary": {"type": "string"},
        "intake_snapshot": {"type": "string"},
        "target_alignment": {"type": "string"},
        "logging_quality": {"type": "string"},
        "practical_food_focus": {"type": "string"},
        "next_nutrition_action": {"type": "string"},
        "limitations_context": {"type": "string"},
        "confidence": {
            "type": "string",
            "enum": ["Limited", "Low", "Moderate", "High"],
        },
        "reason_codes": {"type": "array", "items": {"type": "string"}},
    },
}


@dataclass(frozen=True)
class DirectOllamaNutritionReportSectionProviderResult:
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
    parse_status: str | None
    validation_status: str | None
    candidate_valid: bool | None
    fallback_used: bool
    fallback_reason: str | None
    final_section_source: str
    approved_section: ApprovedNutritionReportSection
    safe_metadata: dict[str, Any]
    validation_errors: list[str] = field(default_factory=list)
    validation_error_categories: list[str] = field(default_factory=list)
    validation_error_fields: list[str] = field(default_factory=list)

    @property
    def first_validation_error_category(self) -> str | None:
        return (
            self.validation_error_categories[0]
            if self.validation_error_categories
            else None
        )

    @property
    def first_validation_error_field(self) -> str | None:
        return self.validation_error_fields[0] if self.validation_error_fields else None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approved_section"] = self.approved_section.to_dict()
        payload["safe_metadata"] = dict(self.safe_metadata)
        payload["first_validation_error_category"] = (
            self.first_validation_error_category
        )
        payload["first_validation_error_field"] = self.first_validation_error_field
        return payload


def build_direct_ollama_nutrition_report_section_prompt(
    evidence_context: NutritionReportEvidenceContext,
) -> str:
    safe_context = build_nutrition_provider_safe_context(evidence_context)
    return (
        "You are writing one Nutrition Report Section for AI Health Coach.\n"
        "Return JSON only. Do not include markdown, code fences, comments, "
        "or prose outside the JSON object.\n"
        "Use only the approved provider-safe context. Do not invent calories, "
        "protein targets, food suggestions, serving sizes, deficiencies, medical "
        "claims, supplement advice, adherence judgments, or guaranteed outcomes.\n"
        "If evidence is limited, explain the limitation instead of inventing.\n"
        "Use only exact numbers listed in approved_numeric_values. Do not calculate "
        "or infer gaps, deltas, percentages, serving sizes, or targets that are not "
        "explicitly listed there. If a useful number is not listed, describe the "
        "relationship qualitatively without a number.\n"
        "practical_food_focus rules: if approved_practical_food_focus_options "
        "contains items, copy exactly one sentence from that list and do not "
        "paraphrase food names, serving amounts, or gram values. If that list is "
        "empty, copy exactly one sentence from "
        "approved_practical_food_focus_unavailable_options. Do not add other "
        "foods, serving sizes, substitutions, supplements, or meal plans. Do not "
        "write any practical_food_focus sentence that is not supplied by the "
        "backend-approved option lists.\n"
        "Return exactly these keys and no others: section_summary, intake_snapshot, "
        "target_alignment, logging_quality, practical_food_focus, "
        "next_nutrition_action, limitations_context, confidence, reason_codes.\n"
        "Candidate JSON schema:\n"
        f"{json.dumps(CANDIDATE_NUTRITION_REPORT_SECTION_JSON_SCHEMA, sort_keys=True)}\n"
        "Provider-safe nutrition context:\n"
        f"{json.dumps(safe_context.to_dict(), sort_keys=True)}"
    )


def run_direct_ollama_nutrition_report_section_provider(
    *,
    model: str,
    user_id: int,
    report_date: str,
    evidence_context: NutritionReportEvidenceContext,
    ollama_base_url: str | None = None,
    generate: DirectOllamaGenerateCallable = call_direct_ollama_generate,
    timeout_seconds: float = 300,
) -> DirectOllamaNutritionReportSectionProviderResult:
    configured_model = model.strip()
    selected_model = normalize_ollama_model_name(configured_model)
    resolved_base_url = (
        ollama_base_url
        or os.getenv(explanation_service.OLLAMA_BASE_URL_ENV)
        or DIRECT_OLLAMA_NUTRITION_DEFAULT_BASE_URL
    )
    safe_context = build_nutrition_provider_safe_context(evidence_context)

    start = time.perf_counter()
    if _qa_force_invalid_provider_output_enabled():
        raw_output = _forced_invalid_nutrition_provider_candidate_json(safe_context)
        elapsed_seconds = round(time.perf_counter() - start, 3)
        parse_result = parse_candidate_nutrition_report_section(raw_output)
        if parse_result.valid and parse_result.candidate is not None:
            validation_result = validate_candidate_nutrition_report_section(
                parse_result.candidate,
                safe_context=safe_context,
            )
            return _fallback_result(
                configured_model=configured_model,
                selected_model=selected_model,
                user_id=user_id,
                report_date=report_date,
                ollama_base_url=resolved_base_url,
                elapsed_seconds=elapsed_seconds,
                evidence_context=evidence_context,
                fallback_reason=(
                    NUTRITION_PROVIDER_FALLBACK_REASON_QA_FORCED_INVALID_PROVIDER_OUTPUT
                ),
                validation_errors=list(validation_result.validation_errors),
                provider_attempted=True,
                parse_result=parse_result,
                validation_result=validation_result,
            )
        return _fallback_result(
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            evidence_context=evidence_context,
            fallback_reason=NUTRITION_PROVIDER_FALLBACK_REASON_PARSE_FAILED,
            validation_errors=list(parse_result.parse_errors),
            provider_attempted=True,
            parse_result=parse_result,
        )

    prompt = build_direct_ollama_nutrition_report_section_prompt(evidence_context)

    try:
        raw_output = generate(
            resolved_base_url,
            selected_model,
            prompt,
            CANDIDATE_NUTRITION_REPORT_SECTION_JSON_SCHEMA,
            timeout_seconds,
        )
    except TimeoutError as exc:
        elapsed_seconds = round(time.perf_counter() - start, 3)
        return _fallback_result(
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            evidence_context=evidence_context,
            fallback_reason=NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_TIMEOUT,
            validation_errors=[type(exc).__name__],
            provider_attempted=True,
        )
    except Exception as exc:
        elapsed_seconds = round(time.perf_counter() - start, 3)
        return _fallback_result(
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            evidence_context=evidence_context,
            fallback_reason=NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_EXCEPTION,
            validation_errors=[type(exc).__name__],
            provider_attempted=True,
        )

    elapsed_seconds = round(time.perf_counter() - start, 3)
    if not isinstance(raw_output, str):
        return _fallback_result(
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            evidence_context=evidence_context,
            fallback_reason=NUTRITION_PROVIDER_FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT,
            validation_errors=["Provider returned non-string output."],
            provider_attempted=True,
        )

    parse_result = parse_candidate_nutrition_report_section(raw_output)
    if not parse_result.valid or parse_result.candidate is None:
        return _fallback_result(
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            evidence_context=evidence_context,
            fallback_reason=NUTRITION_PROVIDER_FALLBACK_REASON_PARSE_FAILED,
            validation_errors=list(parse_result.parse_errors),
            provider_attempted=True,
            parse_result=parse_result,
        )

    validation_result = validate_candidate_nutrition_report_section(
        parse_result.candidate,
        safe_context=safe_context,
    )
    if not validation_result.valid:
        return _fallback_result(
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            evidence_context=evidence_context,
            fallback_reason=NUTRITION_PROVIDER_FALLBACK_REASON_VALIDATION_FAILED,
            validation_errors=list(validation_result.validation_errors),
            provider_attempted=True,
            parse_result=parse_result,
            validation_result=validation_result,
        )

    approved_section = ApprovedNutritionReportSection.from_candidate(
        parse_result.candidate,
        approved_claims=derive_approved_nutrition_claims(evidence_context),
        source=DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_APPROVED,
    )
    safe_metadata = build_nutrition_provider_safe_metadata(
        safe_context=safe_context,
        parse_result=parse_result,
        validation_result=validation_result,
        provider_enabled=True,
        provider_attempted=True,
        selected_provider=DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_PROVIDER_NAME,
        selected_model=selected_model,
        fallback_used=False,
        fallback_reason=None,
        fallback_source=None,
        nutrition_section_source=DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_APPROVED,
        provider_latency_ms=_latency_ms(elapsed_seconds),
    )
    return DirectOllamaNutritionReportSectionProviderResult(
        success=True,
        provider=DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_PROVIDER_NAME,
        section="nutrition_report_section",
        configured_model=configured_model,
        selected_model=selected_model,
        user_id=user_id,
        report_date=report_date,
        ollama_base_url=resolved_base_url,
        elapsed_seconds=elapsed_seconds,
        provider_attempted=True,
        parse_status=parse_result.parse_status,
        validation_status=validation_result.validation_status,
        candidate_valid=True,
        fallback_used=False,
        fallback_reason=None,
        final_section_source=DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_APPROVED,
        approved_section=approved_section,
        safe_metadata=safe_metadata,
        validation_errors=[],
        validation_error_categories=[],
        validation_error_fields=[],
    )


def _fallback_result(
    *,
    configured_model: str,
    selected_model: str,
    user_id: int,
    report_date: str,
    ollama_base_url: str,
    elapsed_seconds: float,
    evidence_context: NutritionReportEvidenceContext,
    fallback_reason: str,
    validation_errors: list[str],
    provider_attempted: bool,
    parse_result: Any | None = None,
    validation_result: Any | None = None,
) -> DirectOllamaNutritionReportSectionProviderResult:
    safe_context = build_nutrition_provider_safe_context(evidence_context)
    section = build_deterministic_nutrition_report_section(evidence_context)
    safe_metadata = build_nutrition_provider_safe_metadata(
        safe_context=safe_context,
        parse_result=parse_result,
        validation_result=validation_result,
        provider_enabled=True,
        provider_attempted=provider_attempted,
        selected_provider=DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_PROVIDER_NAME,
        selected_model=selected_model,
        fallback_used=True,
        fallback_reason=fallback_reason,
        fallback_source=NUTRITION_PROVIDER_FALLBACK_SOURCE,
        nutrition_section_source=DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_FALLBACK,
        provider_latency_ms=_latency_ms(elapsed_seconds),
    )
    return DirectOllamaNutritionReportSectionProviderResult(
        success=False,
        provider=DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_PROVIDER_NAME,
        section="nutrition_report_section",
        configured_model=configured_model,
        selected_model=selected_model,
        user_id=user_id,
        report_date=report_date,
        ollama_base_url=ollama_base_url,
        elapsed_seconds=elapsed_seconds,
        provider_attempted=provider_attempted,
        parse_status=parse_result.parse_status if parse_result else None,
        validation_status=(
            validation_result.validation_status
            if validation_result
            else NUTRITION_PROVIDER_VALIDATION_STATUS_REJECTED
        ),
        candidate_valid=False,
        fallback_used=True,
        fallback_reason=fallback_reason,
        final_section_source=DIRECT_OLLAMA_NUTRITION_REPORT_SECTION_SOURCE_FALLBACK,
        approved_section=section,
        safe_metadata=safe_metadata,
        validation_errors=list(validation_errors),
        validation_error_categories=_fallback_validation_error_categories(
            validation_errors,
            validation_result=validation_result,
        ),
        validation_error_fields=_fallback_validation_error_fields(
            validation_errors,
            parse_result=parse_result,
            validation_result=validation_result,
        ),
    )


def _fallback_validation_error_categories(
    validation_errors: list[str],
    *,
    validation_result: Any | None,
) -> list[str]:
    if validation_result is not None and getattr(
        validation_result, "validation_error_categories", None
    ):
        return list(validation_result.validation_error_categories)
    return validation_error_categories_from_errors(validation_errors)


def _fallback_validation_error_fields(
    validation_errors: list[str],
    *,
    parse_result: Any | None,
    validation_result: Any | None,
) -> list[str]:
    if validation_result is not None and getattr(
        validation_result, "validation_error_fields", None
    ):
        return list(validation_result.validation_error_fields)
    candidate = getattr(parse_result, "candidate", None)
    return validation_error_fields_from_errors(validation_errors, candidate=candidate)


def _latency_ms(elapsed_seconds: float) -> int:
    return max(0, int(round(elapsed_seconds * 1000)))


def _qa_force_invalid_provider_output_enabled() -> bool:
    raw = os.getenv(AI_HEALTH_REPORT_NUTRITION_FORCE_INVALID_PROVIDER_OUTPUT_ENV, "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _forced_invalid_nutrition_provider_candidate_json(safe_context: Any) -> str:
    """Return a parseable but invalid QA-only candidate without calling a model."""

    confidence = getattr(safe_context, "confidence_ceiling", "Limited")
    return json.dumps(
        {
            "section_summary": (
                "Nutrition evidence is present, but this QA candidate is "
                "intentionally invalid."
            ),
            "intake_snapshot": (
                "Logged intake should remain interpreted only through approved "
                "backend evidence."
            ),
            "target_alignment": (
                "Nutrition target alignment must fall back when provider validation "
                "rejects the candidate."
            ),
            "logging_quality": (
                "Logging quality should remain bounded to approved backend context."
            ),
            "practical_food_focus": (
                "Try 999 g of unapproved salmon to close the protein gap."
            ),
            "next_nutrition_action": (
                "Add 999 g of unapproved salmon before changing targets."
            ),
            "limitations_context": (
                "This candidate is intentionally invalid for QA fallback testing."
            ),
            "confidence": confidence,
            "reason_codes": ["qa_forced_invalid_provider_output"],
        },
        sort_keys=True,
    )
