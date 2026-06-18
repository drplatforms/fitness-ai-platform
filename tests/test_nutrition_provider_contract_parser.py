from __future__ import annotations

import json

from models.nutrition_provider_contract_models import (
    NUTRITION_PROVIDER_PARSE_STATUS_SCHEMA_INVALID,
    NUTRITION_PROVIDER_PARSE_STATUS_SUCCESS,
    NUTRITION_PROVIDER_PARSE_STATUS_WRAPPER_OBJECT,
)
from services.nutrition_provider_candidate_parser import (
    parse_candidate_nutrition_report_section,
)


def _valid_payload() -> dict:
    return {
        "section_summary": "Nutrition logging is incomplete, so conclusions should stay limited.",
        "intake_snapshot": "One nutrition entry is logged for this report date.",
        "target_alignment": "Protein comparison is limited until approved targets and logs are available.",
        "logging_quality": "Logged intake is incomplete, so avoid bigger changes from this day alone.",
        "practical_food_focus": "No approved canonical food suggestion is available from the current evidence.",
        "next_nutrition_action": "Log a complete day before changing nutrition targets.",
        "limitations_context": "This section stays limited because nutrition logging is incomplete.",
        "confidence": "Low",
        "reason_codes": ["provider_contract_parser_test"],
    }


def test_parser_accepts_exact_candidate_schema_from_json_object():
    result = parse_candidate_nutrition_report_section(json.dumps(_valid_payload()))

    assert result.parse_status == NUTRITION_PROVIDER_PARSE_STATUS_SUCCESS
    assert result.valid is True
    assert result.candidate is not None
    assert result.candidate.confidence == "Low"


def test_parser_rejects_missing_extra_and_disallowed_keys():
    payload = _valid_payload()
    del payload["target_alignment"]
    payload["raw_output"] = "debug leak"

    result = parse_candidate_nutrition_report_section(payload)

    assert result.parse_status == NUTRITION_PROVIDER_PARSE_STATUS_SCHEMA_INVALID
    assert result.valid is False
    assert any("missing_keys" in error for error in result.parse_errors)
    assert any("extra_keys_detected" in error for error in result.parse_errors)
    assert any("disallowed_keys_detected" in error for error in result.parse_errors)


def test_parser_rejects_wrapper_objects():
    result = parse_candidate_nutrition_report_section(
        {"nutrition_report_section": _valid_payload()}
    )

    assert result.parse_status == NUTRITION_PROVIDER_PARSE_STATUS_WRAPPER_OBJECT
    assert result.valid is False
    assert any("wrapper_object_detected" in error for error in result.parse_errors)


def test_parser_rejects_placeholder_content_and_invalid_confidence():
    payload = _valid_payload()
    payload["section_summary"] = "TODO"
    payload["confidence"] = "Very High"

    result = parse_candidate_nutrition_report_section(payload)

    assert result.parse_status == NUTRITION_PROVIDER_PARSE_STATUS_SCHEMA_INVALID
    assert result.valid is False
    assert any("placeholder_content" in error for error in result.parse_errors)
    assert any("invalid_enum_value" in error for error in result.parse_errors)
