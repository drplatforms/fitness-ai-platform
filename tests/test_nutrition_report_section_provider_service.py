from __future__ import annotations

from models.nutrition_provider_contract_models import (
    NUTRITION_PROVIDER_FALLBACK_REASON_INVALID_PROVIDER,
    NUTRITION_PROVIDER_FALLBACK_REASON_QA_FORCED_INVALID_PROVIDER_OUTPUT,
    NUTRITION_PROVIDER_SAFE_METADATA_ALLOWLIST,
)
from services.full_report_section_registry_service import (
    SECTION_ID_NUTRITION_REPORT,
    get_full_report_section_definition,
    get_provider_integrated_full_report_section_ids,
    get_report_provider_integrated_section_ids,
)
from services.nutrition_report_section_direct_ollama_provider import (
    AI_HEALTH_REPORT_NUTRITION_FORCE_INVALID_PROVIDER_OUTPUT_ENV,
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


def test_nutrition_level_5_promotion_updates_provider_integrated_registry():
    assert get_provider_integrated_full_report_section_ids() == [
        "nutrition_report_section",
        "training",
    ]


def test_nutrition_provider_path_is_level_five_but_report_metadata_is_conditional():
    nutrition = get_full_report_section_definition(SECTION_ID_NUTRITION_REPORT)

    assert nutrition is not None
    assert nutrition.maturity_level == 5
    assert nutrition.provider_status == "opt_in_full_report_integrated"
    assert get_report_provider_integrated_section_ids(
        nutrition_provider_approved=False
    ) == ["training"]
    assert get_report_provider_integrated_section_ids(
        nutrition_provider_approved=True
    ) == ["training", "nutrition_report_section"]


def test_configured_nutrition_provider_preserves_debug_diagnostics_on_rejection(
    monkeypatch,
):
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        NUTRITION_REPORT_SECTION_PROVIDER_ENV,
        NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    evidence = build_complete_nutrition_provider_evidence()

    def fake_generate(*_args):
        return valid_provider_candidate_json(
            target_alignment="Protein appears below the approved target with a 40 g gap."
        )

    result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=evidence,
        direct_ollama_generate=fake_generate,
    )

    assert result.safe_metadata["validation_status"] == "rejected"
    assert result.safe_metadata["validation_errors_count"] > 0
    assert result.validation_error_categories
    assert result.first_validation_error_category is not None
    assert "target_alignment" in result.validation_error_fields
    assert "validation_error_categories" not in result.safe_metadata
    assert "validation_error_fields" not in result.safe_metadata


def test_configured_nutrition_provider_forced_invalid_flag_triggers_fallback(
    monkeypatch,
):
    monkeypatch.setenv(AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED_ENV, "true")
    monkeypatch.setenv(
        NUTRITION_REPORT_SECTION_PROVIDER_ENV,
        NUTRITION_REPORT_SECTION_PROVIDER_DIRECT_OLLAMA,
    )
    monkeypatch.setenv(
        AI_HEALTH_REPORT_NUTRITION_FORCE_INVALID_PROVIDER_OUTPUT_ENV, "true"
    )
    evidence = build_complete_nutrition_provider_evidence()

    def fail_if_called(*_args):
        raise AssertionError("forced-invalid QA mode must not call Ollama")

    result = build_configured_nutrition_report_section_with_metadata(
        user_id=102,
        report_date="2026-06-14",
        evidence_context=evidence,
        direct_ollama_generate=fail_if_called,
    )

    assert result.approved_section.source.endswith("fallback")
    assert result.safe_metadata["provider_attempted"] is True
    assert result.safe_metadata["selected_provider"] == "direct_ollama"
    assert result.safe_metadata["parse_status"] == "success"
    assert result.safe_metadata["candidate_valid"] is False
    assert result.safe_metadata["validation_status"] == "rejected"
    assert result.safe_metadata["fallback_used"] is True
    assert (
        result.safe_metadata["fallback_reason"]
        == NUTRITION_PROVIDER_FALLBACK_REASON_QA_FORCED_INVALID_PROVIDER_OUTPUT
    )
    assert result.validation_error_categories
    assert "practical_food_focus" in result.validation_error_fields
    assert "validation_error_categories" not in result.safe_metadata
    assert "raw_output" not in result.safe_metadata
