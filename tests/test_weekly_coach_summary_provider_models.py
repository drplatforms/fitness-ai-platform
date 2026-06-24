from __future__ import annotations

import json

import pytest

from models.weekly_coach_summary_provider_models import (
    APPROVED_WEEKLY_PROVIDER_MODEL,
    CandidateWeeklyCoachSummaryProviderOutput,
    ProviderConfidenceLabel,
    WeeklyCoachSummaryProviderModelError,
    WeeklyCoachSummaryProviderRuntimeDesignContract,
    assert_provider_input_is_design_safe,
    parse_candidate_weekly_provider_output_json,
    provider_input_contract_summary,
    weekly_provider_output_json_schema,
)


def _candidate(**overrides: object) -> CandidateWeeklyCoachSummaryProviderOutput:
    payload: dict[str, object] = {
        "title": "A useful week with real signals",
        "summary": "Because nutrition was logged across seven days, the weekly read has enough signal to make a bounded observation.",
        "recovery_note": "Recovery coverage is present, so recovery language can stay specific but cautious.",
        "nutrition_note": "Nutrition logging was consistent enough to support a general pattern.",
        "training_note": "There are workout sessions but no actual set details, so progression claims should stay conservative.",
        "next_action": "Keep logging one workout note and one meal detail so next week has set-level context.",
        "confidence_label": "Moderate",
        "data_limitations": ("Actual set details are not available for this range.",),
        "facts_used": (
            "nutrition logged across seven days",
            "five workout sessions",
            "zero actual set rows",
        ),
        "safety_flags": ("provider_candidate_requires_validation",),
        "provider_model": APPROVED_WEEKLY_PROVIDER_MODEL,
        "source_context_metadata": {
            "user_id": 102,
            "start_date": "2026-05-31",
            "end_date": "2026-06-06",
            "source": "qa_date_range_debug",
        },
        "generated_at": "2026-06-24T12:00:00",
    }
    payload.update(overrides)
    return CandidateWeeklyCoachSummaryProviderOutput(**payload)


def test_provider_output_json_schema_defines_required_json_only_contract() -> None:
    schema = weekly_provider_output_json_schema()

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert "summary" in schema["required"]
    assert "next_action" in schema["required"]
    assert schema["properties"]["provider_model"]["const"] == "qwen2.5:3b"
    assert set(schema["properties"]["confidence_label"]["enum"]) == {
        "Limited",
        "Low",
        "Moderate",
        "High",
    }


def test_provider_input_contract_allows_only_bounded_backend_context_fields() -> None:
    summary = provider_input_contract_summary()

    assert summary["allowed_source"] == "WeeklyCoachSummaryContext"
    assert summary["provider_runtime_execution_authorized"] is False
    assert summary["raw_rows_allowed"] is False
    assert summary["normal_ui_allowed"] is False
    assert "raw_database_rows" in summary["forbidden_fields"]
    assert "scratchpad" in summary["forbidden_fields"]


def test_safe_provider_input_contract_accepts_backend_context_summary() -> None:
    assert_provider_input_is_design_safe(
        {
            "user_id": 102,
            "scenario": "aligned_managed",
            "start_date": "2026-05-31",
            "end_date": "2026-06-06",
            "source": "qa_date_range_debug",
            "confidence": "Moderate",
            "data_quality_label": "usable",
            "limitations": ["Actual set details are not available."],
            "reason_codes": ["selected_range_has_data"],
            "fact_counts": {"nutrition": 21, "workout_sessions": 5},
            "safe_recovery_summary": "Recovery coverage includes 9 check-ins.",
            "safe_nutrition_summary": "Nutrition coverage includes 21 entries across 7 logged days.",
            "safe_training_summary": "Training coverage includes 5 sessions and 0 actual sets.",
            "deterministic_baseline_summary": "Deterministic fallback remains available.",
            "voice_contract": "warm, factual, grounded in because",
            "output_schema_name": "CandidateWeeklyCoachSummaryProviderOutput",
        }
    )


def test_provider_input_contract_rejects_raw_rows_and_unknown_fields() -> None:
    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        assert_provider_input_is_design_safe(
            {
                "user_id": 102,
                "source": "qa_date_range_debug",
                "raw_database_rows": [{"food": "private raw row"}],
            }
        )

    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        assert_provider_input_is_design_safe(
            {"user_id": 102, "source": "streamlit_label", "ui_label": "102 - QA"}
        )


def test_candidate_provider_output_can_be_constructed_but_is_not_approval() -> None:
    candidate = _candidate()

    assert candidate.confidence_label == ProviderConfidenceLabel.MODERATE
    assert candidate.provider_model == "qwen2.5:3b"
    assert candidate.to_dict()["facts_used"] == [
        "nutrition logged across seven days",
        "five workout sessions",
        "zero actual set rows",
    ]
    assert "raw_provider_output" not in candidate.to_dict()


def test_candidate_output_requires_facts_used_for_grounding() -> None:
    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        _candidate(facts_used=())


def test_candidate_output_rejects_non_approved_model() -> None:
    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        _candidate(provider_model="qwen3:32b")


def test_candidate_output_rejects_raw_context_metadata() -> None:
    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        _candidate(
            source_context_metadata={
                "user_id": 102,
                "raw_food_logs": ["private meal description"],
            }
        )


def test_candidate_output_rejects_chain_of_thought_and_guilt_language() -> None:
    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        _candidate(summary="Chain of thought: the user failed their plan.")

    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        _candidate(next_action="You failed, so compensate tomorrow.")


def test_low_data_limitations_cannot_claim_high_confidence() -> None:
    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        _candidate(
            confidence_label="High",
            data_limitations=("Limited workout detail is available.",),
        )


def test_parse_candidate_json_rejects_wrappers_and_accepts_json_object() -> None:
    candidate = _candidate()
    parsed = parse_candidate_weekly_provider_output_json(
        json.dumps(candidate.to_dict())
    )

    assert parsed.title == candidate.title

    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        parse_candidate_weekly_provider_output_json("Here is the JSON: {}")

    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        parse_candidate_weekly_provider_output_json(json.dumps([candidate.to_dict()]))


def test_runtime_design_contract_does_not_authorize_execution_or_public_display() -> (
    None
):
    contract = WeeklyCoachSummaryProviderRuntimeDesignContract()

    assert contract.provider_execution_authorized is False
    assert contract.developer_mode_preview_only is True
    assert contract.public_default_display_authorized is False
    assert contract.crewai_authorized is False
    assert contract.deterministic_fallback_required is True

    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        WeeklyCoachSummaryProviderRuntimeDesignContract(
            provider_execution_authorized=True
        )

    with pytest.raises(WeeklyCoachSummaryProviderModelError):
        WeeklyCoachSummaryProviderRuntimeDesignContract(crewai_authorized=True)
