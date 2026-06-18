from __future__ import annotations

import json
from typing import Any

from models.nutrition_provider_contract_models import (
    NUTRITION_PROVIDER_CANDIDATE_DISALLOWED_KEYS,
    NUTRITION_PROVIDER_CANDIDATE_REQUIRED_KEYS,
    NUTRITION_PROVIDER_CANDIDATE_TEXT_FIELDS,
    NUTRITION_PROVIDER_CONFIDENCE_ORDER,
    NUTRITION_PROVIDER_PARSE_STATUS_EMPTY,
    NUTRITION_PROVIDER_PARSE_STATUS_INVALID_JSON,
    NUTRITION_PROVIDER_PARSE_STATUS_NOT_OBJECT,
    NUTRITION_PROVIDER_PARSE_STATUS_SCHEMA_INVALID,
    NUTRITION_PROVIDER_PARSE_STATUS_SUCCESS,
    NUTRITION_PROVIDER_PARSE_STATUS_WRAPPER_OBJECT,
    NUTRITION_PROVIDER_PLACEHOLDER_LANGUAGE,
    NUTRITION_PROVIDER_WRAPPER_KEYS,
    NutritionProviderCandidateParseResult,
)
from models.nutrition_report_section_models import CandidateNutritionReportSection


def parse_candidate_nutrition_report_section(
    raw_candidate: str | dict[str, Any],
) -> NutritionProviderCandidateParseResult:
    """Parse a future nutrition provider candidate without executing a provider.

    This parser accepts either a raw JSON string or an already-loaded dictionary
    for tests/scaffolding. It enforces an exact object contract and rejects
    wrappers, missing keys, extra keys, type mismatches, invalid confidence,
    placeholder content, and unsafe text rejected by the section model.
    """

    payload_result = _load_payload(raw_candidate)
    if isinstance(payload_result, NutritionProviderCandidateParseResult):
        return payload_result
    payload = payload_result

    wrapper_error = _wrapper_object_error(payload)
    if wrapper_error:
        return NutritionProviderCandidateParseResult(
            parse_status=NUTRITION_PROVIDER_PARSE_STATUS_WRAPPER_OBJECT,
            parse_errors=[wrapper_error],
        )

    schema_errors = _schema_errors(payload)
    if schema_errors:
        return NutritionProviderCandidateParseResult(
            parse_status=NUTRITION_PROVIDER_PARSE_STATUS_SCHEMA_INVALID,
            parse_errors=schema_errors,
        )

    try:
        candidate = CandidateNutritionReportSection.from_payload(payload)
    except (KeyError, TypeError, ValueError) as exc:
        return NutritionProviderCandidateParseResult(
            parse_status=NUTRITION_PROVIDER_PARSE_STATUS_SCHEMA_INVALID,
            parse_errors=[f"candidate_model_rejected: {exc}"],
        )

    return NutritionProviderCandidateParseResult(
        parse_status=NUTRITION_PROVIDER_PARSE_STATUS_SUCCESS,
        candidate=candidate,
        parse_errors=[],
    )


def _load_payload(
    raw_candidate: str | dict[str, Any],
) -> dict[str, Any] | NutritionProviderCandidateParseResult:
    if isinstance(raw_candidate, dict):
        return dict(raw_candidate)

    if not isinstance(raw_candidate, str):
        return NutritionProviderCandidateParseResult(
            parse_status=NUTRITION_PROVIDER_PARSE_STATUS_NOT_OBJECT,
            parse_errors=["candidate output must be a JSON string or dictionary"],
        )

    stripped = raw_candidate.strip()
    if not stripped:
        return NutritionProviderCandidateParseResult(
            parse_status=NUTRITION_PROVIDER_PARSE_STATUS_EMPTY,
            parse_errors=["candidate output is empty"],
        )

    if stripped.startswith("```") or not (
        stripped.startswith("{") and stripped.endswith("}")
    ):
        return NutritionProviderCandidateParseResult(
            parse_status=NUTRITION_PROVIDER_PARSE_STATUS_INVALID_JSON,
            parse_errors=["candidate output must be exactly one JSON object"],
        )

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as exc:
        return NutritionProviderCandidateParseResult(
            parse_status=NUTRITION_PROVIDER_PARSE_STATUS_INVALID_JSON,
            parse_errors=[f"invalid_json: {exc.msg}"],
        )

    if not isinstance(parsed, dict):
        return NutritionProviderCandidateParseResult(
            parse_status=NUTRITION_PROVIDER_PARSE_STATUS_NOT_OBJECT,
            parse_errors=["candidate output must be a JSON object"],
        )

    return parsed


def _wrapper_object_error(payload: dict[str, Any]) -> str | None:
    if len(payload) == 1:
        only_key = next(iter(payload))
        if only_key in NUTRITION_PROVIDER_WRAPPER_KEYS:
            return f"wrapper_object_detected: {only_key}"
    return None


def _schema_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    keys = set(payload)
    missing_keys = sorted(NUTRITION_PROVIDER_CANDIDATE_REQUIRED_KEYS - keys)
    extra_keys = sorted(keys - NUTRITION_PROVIDER_CANDIDATE_REQUIRED_KEYS)
    disallowed_keys = sorted(keys & NUTRITION_PROVIDER_CANDIDATE_DISALLOWED_KEYS)

    if missing_keys:
        errors.append("missing_keys: " + ", ".join(missing_keys))
    if extra_keys:
        errors.append("extra_keys_detected: " + ", ".join(extra_keys))
    if disallowed_keys:
        errors.append("disallowed_keys_detected: " + ", ".join(disallowed_keys))

    for field_name in sorted(NUTRITION_PROVIDER_CANDIDATE_TEXT_FIELDS):
        value = payload.get(field_name)
        if not isinstance(value, str):
            errors.append(f"type_mismatch: {field_name} must be a string")
            continue
        stripped = value.strip()
        if not stripped:
            errors.append(f"empty_content: {field_name}")
        if stripped.lower() in NUTRITION_PROVIDER_PLACEHOLDER_LANGUAGE:
            errors.append(f"placeholder_content: {field_name}")

    confidence = payload.get("confidence")
    if confidence not in NUTRITION_PROVIDER_CONFIDENCE_ORDER:
        errors.append("invalid_enum_value: confidence")

    reason_codes = payload.get("reason_codes")
    if not isinstance(reason_codes, list) or not all(
        isinstance(value, str) and value.strip() for value in reason_codes
    ):
        errors.append("type_mismatch: reason_codes must be a list of strings")

    return errors
