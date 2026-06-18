from __future__ import annotations

from models.nutrition_provider_contract_models import (
    NUTRITION_PROVIDER_FALLBACK_REASON_INVALID_PROVIDER,
    NUTRITION_PROVIDER_SAFE_METADATA_ALLOWLIST,
)
from services.full_report_section_registry_service import (
    SECTION_ID_NUTRITION_REPORT,
    get_full_report_section_definition,
    get_provider_integrated_full_report_section_ids,
)
from services.nutrition_report_section_provider_service import (
    AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV,
    NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    NUTRITION_REPORT_SECTION_PROVIDER_ENV,
    build_configured_nutrition_report_section_with_metadata,
)
from tests.nutrition_provider_fixtures import (
    build_complete_nutrition_provider_evidence,
    valid_provider_candidate_json,
)


def test_default_nutrition_provider_path_is_deterministic_and_does_not_call_provider(
    monkeypatch,
):
    monkeypatch.delenv(
        AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, raising=False
    )
    monkeypatch.delenv(NUTRITION_REPORT_SECTION_PROVIDER_ENV, raising=False)
    evidence = build_complete_nutrition_provider_evidence()

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("provider should not be called by default")

    result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=evidence,
        direct_ollama_generate=fail_if_called,
    )

    assert result.approved_section.section_id == "nutrition_report_section"
    assert result.safe_metadata["provider_enabled"] is False
    assert result.safe_metadata["provider_attempted"] is False
    assert result.safe_metadata["selected_provider"] == "deterministic"
    assert result.safe_metadata["fallback_used"] is False


def test_opt_in_nutrition_provider_uses_fake_generator_and_approves_candidate(
    monkeypatch,
):
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        NUTRITION_REPORT_SECTION_PROVIDER_ENV,
        NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    evidence = build_complete_nutrition_provider_evidence()
    calls = []

    def fake_generate(*args):
        calls.append(args)
        return valid_provider_candidate_json()

    result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=evidence,
        direct_ollama_generate=fake_generate,
    )

    assert len(calls) == 1
    assert result.approved_section.source == "direct_ollama_approved"
    assert result.safe_metadata["provider_enabled"] is True
    assert result.safe_metadata["provider_attempted"] is True
    assert result.safe_metadata["selected_provider"] == "direct_ollama"
    assert result.safe_metadata["fallback_used"] is False


def test_invalid_provider_falls_back_and_metadata_stays_allowlisted(monkeypatch):
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(NUTRITION_REPORT_SECTION_PROVIDER_ENV, "crewai")
    evidence = build_complete_nutrition_provider_evidence()

    result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=evidence,
    )

    assert result.approved_section.source.endswith("fallback")
    assert result.safe_metadata["provider_attempted"] is False
    assert result.safe_metadata["fallback_used"] is True
    assert (
        result.safe_metadata["fallback_reason"]
        == NUTRITION_PROVIDER_FALLBACK_REASON_INVALID_PROVIDER
    )
    assert set(result.safe_metadata).issubset(
        NUTRITION_PROVIDER_SAFE_METADATA_ALLOWLIST
    )
    assert "raw_output" not in result.safe_metadata
    assert "validation_errors" not in result.safe_metadata


def test_nutrition_opt_in_implementation_does_not_promote_full_report_provider_integration():
    assert get_provider_integrated_full_report_section_ids() == ["training"]


def test_nutrition_provider_opt_in_path_is_level_four_not_level_five():
    nutrition = get_full_report_section_definition(SECTION_ID_NUTRITION_REPORT)

    assert nutrition is not None
    assert nutrition.maturity_level == 4
    assert nutrition.provider_status == "not_full_report_integrated"
    assert get_provider_integrated_full_report_section_ids() == ["training"]
