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
    from services import ai_nutrition_explanation_service as explanation_service
    from services.coaching_decision_service import build_coaching_decision
    from services.user_state_service import build_user_health_state

DIRECT_OLLAMA_HEALTH_REPORT_SECTION_PROVIDER_NAME = "direct_ollama_report_section_spike"
DIRECT_OLLAMA_DEFAULT_BASE_URL = (
    explanation_service.NUTRITION_EXPLANATION_DEFAULT_BASE_URL
)
DIRECT_OLLAMA_RESPONSE_PREVIEW_LIMIT = 500

REPORT_SECTION_PARSE_STATUS_NOT_ATTEMPTED = "not_attempted"
REPORT_SECTION_PARSE_STATUS_SUCCESS = "success"
REPORT_SECTION_PARSE_STATUS_FAILED = "failed"

REPORT_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED = "not_attempted"
REPORT_SECTION_VALIDATION_STATUS_SUCCESS = "success"
REPORT_SECTION_VALIDATION_STATUS_FAILED = "failed"

REPORT_SECTION_STATUS_NOT_ATTEMPTED = "not_attempted"
REPORT_SECTION_STATUS_APPROVED = "approved"
REPORT_SECTION_STATUS_REJECTED = "rejected"

FINAL_SECTION_SOURCE_PROVIDER_APPROVED = "provider_approved"
FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"

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

DirectOllamaGenerateCallable = explanation_service.DirectOllamaGenerateCallable
normalize_ollama_model_name = explanation_service.normalize_ollama_model_name
call_direct_ollama_generate = explanation_service.call_direct_ollama_generate


@dataclass(frozen=True)
class CandidateHealthReportSection:
    section_summary: str
    key_observations: list[str]
    coaching_interpretation: str
    suggested_focus: str
    limitations_context: str
    confidence: str
    reason_codes: list[str]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> CandidateHealthReportSection:
        return cls(
            section_summary=payload["section_summary"],
            key_observations=list(payload["key_observations"]),
            coaching_interpretation=payload["coaching_interpretation"],
            suggested_focus=payload["suggested_focus"],
            limitations_context=payload["limitations_context"],
            confidence=payload["confidence"],
            reason_codes=list(payload["reason_codes"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DirectOllamaHealthReportSectionSpikeResult:
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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_nutrition_report_section_context(
    *,
    user_id: int,
    report_date: str,
) -> dict[str, Any]:
    """Build bounded backend-approved context for the nutrition section spike."""

    with redirect_stdout(sys.stderr):
        health_state = build_user_health_state(user_id)
        coaching_decision = build_coaching_decision(health_state)
        nutrition_context = explanation_service.build_nutrition_explanation_context(
            user_id,
            report_date,
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
                        coaching_decision, "nutrition_action", None
                    ),
                    "confidence": getattr(coaching_decision, "confidence", None),
                }
            ),
            "approved_nutrition_context": (
                explanation_service._compressed_provider_context_projection(
                    nutrition_context
                )
            ),
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


def run_direct_ollama_health_report_section_spike(
    *,
    model: str,
    user_id: int,
    report_date: str,
    section: str = "nutrition",
    approved_context: dict[str, Any] | None = None,
    ollama_base_url: str | None = None,
    generate: DirectOllamaGenerateCallable = call_direct_ollama_generate,
    timeout_seconds: float = 600,
) -> DirectOllamaHealthReportSectionSpikeResult:
    """Run one isolated direct Ollama structured-output report section spike."""

    configured_model = model.strip()
    selected_model = normalize_ollama_model_name(configured_model)
    resolved_base_url = (
        ollama_base_url
        or os.getenv(explanation_service.OLLAMA_BASE_URL_ENV)
        or DIRECT_OLLAMA_DEFAULT_BASE_URL
    )
    resolved_context = approved_context or build_nutrition_report_section_context(
        user_id=user_id,
        report_date=report_date,
    )
    prompt = build_direct_ollama_health_report_section_prompt(
        resolved_context,
        section=section,
    )

    start = time.perf_counter()
    raw_output: Any | None = None
    provider_error: str | None = None

    try:
        raw_output = generate(
            resolved_base_url,
            selected_model,
            prompt,
            CANDIDATE_HEALTH_REPORT_SECTION_JSON_SCHEMA,
            timeout_seconds,
        )
    except Exception as exc:
        provider_error = f"{type(exc).__name__}: {exc}"

    elapsed_seconds = round(time.perf_counter() - start, 3)

    if provider_error is not None:
        return _fallback_result(
            section=section,
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            fallback_reason=FALLBACK_REASON_PROVIDER_EXCEPTION,
            validation_errors=[provider_error],
        )

    if not isinstance(raw_output, str):
        return _fallback_result(
            section=section,
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            fallback_reason=FALLBACK_REASON_PROVIDER_NON_STRING_OUTPUT,
            validation_errors=["Provider returned a non-string response."],
        )

    diagnostics = detect_direct_ollama_section_output_diagnostics(raw_output)

    try:
        payload = _parse_candidate_section_payload(raw_output)
    except Exception as exc:
        return _fallback_result(
            section=section,
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            fallback_reason=FALLBACK_REASON_CANDIDATE_PARSE_FAILURE,
            validation_errors=[str(exc)],
            raw_output=raw_output,
            candidate_parse_status=REPORT_SECTION_PARSE_STATUS_FAILED,
            diagnostics=diagnostics,
        )

    candidate = CandidateHealthReportSection.from_payload(payload)
    validation_errors = validate_candidate_health_report_section(
        candidate,
        approved_context=resolved_context,
    )
    if validation_errors:
        return _fallback_result(
            section=section,
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            report_date=report_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            fallback_reason=FALLBACK_REASON_CANDIDATE_VALIDATION_FAILURE,
            validation_errors=validation_errors,
            raw_output=raw_output,
            candidate_parse_status=REPORT_SECTION_PARSE_STATUS_SUCCESS,
            candidate_validation_status=REPORT_SECTION_VALIDATION_STATUS_FAILED,
            validation_status=REPORT_SECTION_STATUS_REJECTED,
            diagnostics=diagnostics,
        )

    return DirectOllamaHealthReportSectionSpikeResult(
        success=True,
        provider=DIRECT_OLLAMA_HEALTH_REPORT_SECTION_PROVIDER_NAME,
        section=section,
        configured_model=configured_model,
        selected_model=selected_model,
        user_id=user_id,
        report_date=report_date,
        ollama_base_url=resolved_base_url,
        elapsed_seconds=elapsed_seconds,
        provider_attempted=True,
        candidate_parse_status=REPORT_SECTION_PARSE_STATUS_SUCCESS,
        candidate_validation_status=REPORT_SECTION_VALIDATION_STATUS_SUCCESS,
        validation_status=REPORT_SECTION_STATUS_APPROVED,
        candidate_valid=True,
        fallback_used=False,
        fallback_reason=None,
        final_section_source=FINAL_SECTION_SOURCE_PROVIDER_APPROVED,
        approved_section=candidate.to_dict(),
        validation_errors=[],
        **diagnostics,
    )


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
            :DIRECT_OLLAMA_RESPONSE_PREVIEW_LIMIT
        ],
        "markdown_wrapper_detected": _detect_markdown_wrapper(stripped),
        "extra_keys_detected": extra_keys,
        "wrapper_object_detected": wrapper_object_detected,
    }


def _parse_candidate_section_payload(raw_output: str) -> dict[str, Any]:
    stripped = raw_output.strip()
    if not stripped:
        raise ValueError("Provider section output was empty.")
    _reject_markdown_or_code_fence(stripped)
    payload = json.loads(stripped)
    if not isinstance(payload, dict):
        raise ValueError("Provider section JSON must be an object.")

    payload_keys = set(payload)
    missing_keys = CANDIDATE_HEALTH_REPORT_SECTION_ALLOWED_KEYS - payload_keys
    if missing_keys:
        raise ValueError(
            "Provider section JSON is missing required keys: "
            + ", ".join(sorted(missing_keys))
        )

    extra_keys = payload_keys - CANDIDATE_HEALTH_REPORT_SECTION_ALLOWED_KEYS
    if extra_keys:
        raise ValueError(
            "Provider section JSON included unsupported keys: "
            + ", ".join(sorted(extra_keys))
        )

    if not isinstance(payload.get("key_observations"), list):
        raise ValueError("key_observations must be an array.")
    if not isinstance(payload.get("reason_codes"), list):
        raise ValueError("reason_codes must be an array.")
    for key in [
        "section_summary",
        "coaching_interpretation",
        "suggested_focus",
        "limitations_context",
        "confidence",
    ]:
        if not isinstance(payload.get(key), str):
            raise ValueError(f"{key} must be a string.")

    return payload


def _reject_markdown_or_code_fence(text: str) -> None:
    if re.fullmatch(r"```(?:json)?\s*.*?\s*```", text, flags=re.DOTALL):
        raise ValueError(
            "Provider section output must be raw JSON without markdown or code fences."
        )
    if text.startswith("```") or text.endswith("```"):
        raise ValueError(
            "Provider section output must not include markdown code fences."
        )


def _detect_markdown_wrapper(text: str) -> bool:
    return bool(
        re.fullmatch(r"```(?:json)?\s*.*?\s*```", text, flags=re.DOTALL)
        or text.startswith("```")
        or text.endswith("```")
    )


def _fallback_result(
    *,
    section: str,
    configured_model: str,
    selected_model: str,
    user_id: int,
    report_date: str,
    ollama_base_url: str,
    elapsed_seconds: float,
    fallback_reason: str,
    validation_errors: list[str],
    raw_output: str | None = None,
    candidate_parse_status: str = REPORT_SECTION_PARSE_STATUS_NOT_ATTEMPTED,
    candidate_validation_status: str = REPORT_SECTION_VALIDATION_STATUS_NOT_ATTEMPTED,
    validation_status: str = REPORT_SECTION_STATUS_NOT_ATTEMPTED,
    diagnostics: dict[str, Any] | None = None,
) -> DirectOllamaHealthReportSectionSpikeResult:
    if diagnostics is None:
        diagnostics = (
            detect_direct_ollama_section_output_diagnostics(raw_output)
            if isinstance(raw_output, str)
            else {
                "raw_output_length": None,
                "raw_output_preview_truncated": None,
                "markdown_wrapper_detected": False,
                "extra_keys_detected": [],
                "wrapper_object_detected": False,
            }
        )

    return DirectOllamaHealthReportSectionSpikeResult(
        success=False,
        provider=DIRECT_OLLAMA_HEALTH_REPORT_SECTION_PROVIDER_NAME,
        section=section,
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
        **diagnostics,
    )


def _deterministic_fallback_section() -> CandidateHealthReportSection:
    return CandidateHealthReportSection(
        section_summary="Nutrition context is available from backend-approved data.",
        key_observations=[
            "Nutrition targets, logged intake, gaps, and food suggestions remain backend-owned."
        ],
        coaching_interpretation=(
            "Use the approved nutrition dashboard and food suggestions for the safest current guidance."
        ),
        suggested_focus="Keep logging consistent and review approved nutrition gaps before changing intake.",
        limitations_context=(
            "This deterministic fallback does not add AI-generated nutrition claims."
        ),
        confidence="Limited",
        reason_codes=["deterministic_health_report_section_fallback"],
    )


def _candidate_health_report_section_example() -> dict[str, Any]:
    return {
        "section_summary": "Nutrition support is mostly on track within the approved context.",
        "key_observations": [
            "Logged meals provide enough context for cautious coaching.",
            "Macro gaps should be interpreted using backend-approved targets and actuals.",
        ],
        "coaching_interpretation": (
            "The main nutrition focus is consistency rather than a dramatic change."
        ),
        "suggested_focus": "Review the Nutrition tab for approved target and food suggestion details.",
        "limitations_context": "This section only uses approved backend nutrition context.",
        "confidence": "Moderate",
        "reason_codes": ["direct_ollama_report_section_candidate"],
    }


def _candidate_text_fields(candidate: CandidateHealthReportSection) -> list[str]:
    return [
        candidate.section_summary,
        *candidate.key_observations,
        candidate.coaching_interpretation,
        candidate.suggested_focus,
        candidate.limitations_context,
    ]


def _unapproved_numbers_in_candidate(
    candidate_payload: dict[str, Any],
    *,
    approved_context: dict[str, Any],
) -> set[str]:
    allowed_numbers = _number_tokens_from_object(approved_context)
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
        description="Direct Ollama structured-output health report section spike."
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--date", required=True, dest="report_date")
    parser.add_argument("--section", default="nutrition", choices=["nutrition"])
    parser.add_argument("--ollama-base-url", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=600)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = run_direct_ollama_health_report_section_spike(
        model=args.model,
        user_id=args.user_id,
        report_date=args.report_date,
        section=args.section,
        ollama_base_url=args.ollama_base_url,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
