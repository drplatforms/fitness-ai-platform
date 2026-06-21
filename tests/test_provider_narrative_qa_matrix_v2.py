from __future__ import annotations

from tools.provider_narrative_qa_matrix import (
    CLASSIFICATION_APPROVED_BASELINE,
    CLASSIFICATION_APPROVED_PROBE,
    CLASSIFICATION_PROVIDER_ERROR,
    CLASSIFICATION_SAFE_REJECTED_PARSE,
    CLASSIFICATION_SAFE_REJECTED_VALIDATION,
    collect_forbidden_debug_leaks,
    render_markdown_report,
    row_from_exception,
    row_from_payload,
)


def _payload(**overrides):
    preview = {
        "user_id": 102,
        "date": "2026-06-20",
        "next_action_id": "log_food",
        "next_action_title": "Log a meal or snack",
        "workflow_target": "nutrition_quick_log",
        "provider_enabled": True,
        "provider_attempted": True,
        "selected_provider": "direct_ollama",
        "selected_model": "qwen2.5:3b",
        "parse_success": True,
        "validation_success": True,
        "approved_narrative_returned": True,
        "fallback_used": False,
        "fallback_reason": None,
        "parse_extraction_strategy": "raw_json_object",
        "approved_narrative": {
            "coach_note": "Log a meal or snack so today's nutrition state has enough information to work from.",
            "recommended_focus": "Log a meal or snack",
        },
    }
    preview.update(overrides)
    return {"success": True, "daily_coach_narrative_preview": preview}


def test_qwen25_3b_success_is_classified_as_approved_baseline() -> None:
    row = row_from_payload(
        model="qwen2.5:3b",
        provider="direct_ollama",
        payload=_payload(),
        runtime_seconds=12.345,
    )

    assert row.classification == CLASSIFICATION_APPROVED_BASELINE
    assert row.parse_success is True
    assert row.validation_success is True
    assert row.approved_narrative_returned is True
    assert row.runtime_seconds == 12.35
    assert row.forbidden_debug_leaks == []
    assert "not a product default" in row.display_readiness_recommendation


def test_qwen3_success_is_classified_as_approved_probe_not_promotion() -> None:
    row = row_from_payload(
        model="qwen3:8b",
        provider="direct_ollama",
        payload=_payload(selected_model="qwen3:8b"),
        runtime_seconds=20,
    )

    assert row.classification == CLASSIFICATION_APPROVED_PROBE
    assert "Probe only" in row.display_readiness_recommendation


def test_parse_failure_is_safe_rejected_parse() -> None:
    row = row_from_payload(
        model="qwen3:32b",
        provider="direct_ollama",
        payload=_payload(
            selected_model="qwen3:32b",
            parse_success=False,
            validation_success=False,
            approved_narrative_returned=False,
            fallback_used=True,
            fallback_reason="provider_parse_failed",
            parse_error="Unable to extract one safe JSON object.",
            approved_narrative=None,
        ),
        runtime_seconds=90,
    )

    assert row.classification == CLASSIFICATION_SAFE_REJECTED_PARSE
    assert row.fallback_used is True
    assert row.sanitized_parse_error == "Unable to extract one safe JSON object."
    assert "Do not use for bridge" in row.display_readiness_recommendation


def test_validation_failure_is_safe_rejected_validation() -> None:
    row = row_from_payload(
        model="qwen3:14b",
        provider="direct_ollama",
        payload=_payload(
            selected_model="qwen3:14b",
            parse_success=True,
            validation_success=False,
            approved_narrative_returned=False,
            fallback_used=True,
            fallback_reason="provider_validation_failed",
            validation_errors=["Provider output included unsupported certainty."],
            approved_narrative=None,
        ),
        runtime_seconds=30,
    )

    assert row.classification == CLASSIFICATION_SAFE_REJECTED_VALIDATION
    assert row.sanitized_validation_errors == [
        "Provider output included unsupported certainty."
    ]


def test_provider_error_row_is_public_safe() -> None:
    row = row_from_exception(
        model="qwen3:30b-a3b",
        provider="direct_ollama",
        user_id=102,
        exc=ConnectionRefusedError("connection refused"),
        runtime_seconds=1.2,
    )

    assert row.classification == CLASSIFICATION_PROVIDER_ERROR
    assert row.sanitized_provider_error == "provider_or_api_connection_refused"
    assert row.parse_success is None
    assert row.approved_narrative_returned is None


def test_forbidden_debug_leak_detection_marks_unsafe_payload() -> None:
    payload = _payload(prompt="hidden prompt should not be exposed")

    leaks = collect_forbidden_debug_leaks(payload)

    assert "prompt" in leaks


def test_markdown_report_is_sanitized_and_boundary_explicit() -> None:
    rows = [
        row_from_payload(
            model="qwen2.5:3b",
            provider="direct_ollama",
            payload=_payload(),
            runtime_seconds=10,
        )
    ]

    report = render_markdown_report(rows)

    assert "# Provider Narrative QA Matrix v2 Results" in report
    assert "APPROVED_BASELINE" in report
    assert "No model is promoted by this report." in report
    assert "Provider preview remains manual/developer-gated." in report
    assert "raw_output" not in report
