from __future__ import annotations

from datetime import date as date_cls

from fastapi.testclient import TestClient

import api.routes.ai_nutrition_explanation as explanation_route
from api.main import app
from models.ai_nutrition_explanation_models import (
    ApprovedNutritionExplanation,
    ApprovedNutritionExplanationResult,
    NutritionExplanationRuntimeMetadata,
)


def _approved_explanation(
    *,
    user_id: int = 1,
    explanation_date: str = "2026-06-07",
    confidence: str = "Moderate",
    reason_codes: list[str] | None = None,
    limitations: list[str] | None = None,
) -> ApprovedNutritionExplanation:
    return ApprovedNutritionExplanation(
        user_id=user_id,
        explanation_date=explanation_date,
        explanation_summary=(
            "Based on approved nutrition context, today's logged meals can be "
            "reviewed cautiously against formula-derived targets."
        ),
        macro_context=("Based on today’s logged meals, protein is below target."),
        food_suggestion_context=(
            "The Nutrition tab has approved food suggestions that may help close the gap."
        ),
        trend_context=("Trend context is available for review in the Nutrition tab."),
        calibration_context=(
            "Targets are still formula-derived. Calibration is not ready yet because "
            "more consistent logs or weigh-ins are needed."
        ),
        limitations_context=(
            "Nutrition explanation is limited to approved backend nutrition context."
        ),
        confidence=confidence,
        reason_codes=reason_codes or ["deterministic_nutrition_explanation_service"],
        limitations=limitations
        or ["Nutrition explanation is limited to approved backend nutrition context."],
        source="deterministic_fallback",
    )


def _patch_user_and_service(monkeypatch, approved: ApprovedNutritionExplanation):
    monkeypatch.setattr(
        explanation_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )
    monkeypatch.setattr(
        explanation_route,
        "build_configured_approved_nutrition_explanation",
        lambda user_id, explanation_date: approved,
    )


def _runtime_metadata(
    *,
    configured_provider: str = "deterministic",
    selected_provider: str = "deterministic",
    provider_attempted: bool = False,
    fallback_used: bool = False,
    fallback_reason: str | None = "deterministic_provider_selected",
    candidate_valid: bool = True,
    validation_errors: list[str] | None = None,
    candidate_parse_status: str = "not_attempted",
    validation_status: str = "not_attempted",
    final_explanation_source: str = "deterministic",
    raw_output_length: int | None = None,
    raw_output_preview_truncated: str | None = None,
    configured_model: str | None = "deterministic",
    selected_model: str | None = "deterministic",
    candidate_validation_status: str = "not_attempted",
    markdown_wrapper_detected: bool = False,
) -> NutritionExplanationRuntimeMetadata:
    return NutritionExplanationRuntimeMetadata(
        provider=selected_provider,
        fallback_used=fallback_used,
        validation_status=validation_status,
        validation_errors=validation_errors or [],
        raw_output_preview_truncated=raw_output_preview_truncated,
        raw_output_length=raw_output_length,
        configured_provider=configured_provider,
        selected_provider=selected_provider,
        configured_model=configured_model,
        selected_model=selected_model,
        provider_attempted=provider_attempted,
        fallback_reason=fallback_reason,
        candidate_valid=candidate_valid,
        candidate_parse_status=candidate_parse_status,
        candidate_validation_status=candidate_validation_status,
        final_explanation_source=final_explanation_source,
        markdown_wrapper_detected=markdown_wrapper_detected,
    )


def _approved_result(
    approved: ApprovedNutritionExplanation | None = None,
    metadata: NutritionExplanationRuntimeMetadata | None = None,
) -> ApprovedNutritionExplanationResult:
    return ApprovedNutritionExplanationResult(
        approved_nutrition_explanation=approved or _approved_explanation(),
        runtime_metadata=metadata or _runtime_metadata(),
    )


def _patch_user_and_result(
    monkeypatch,
    result: ApprovedNutritionExplanationResult,
    candidates: list[dict[str, object]] | None = None,
):
    monkeypatch.setattr(
        explanation_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )
    monkeypatch.setattr(
        explanation_route,
        "build_nutrition_explanation_context",
        lambda user_id, explanation_date: {
            "user_id": user_id,
            "date": explanation_date,
        },
    )
    monkeypatch.setattr(
        explanation_route,
        "build_debug_approved_food_suggestion_candidates",
        lambda _context: candidates or [],
    )
    monkeypatch.setattr(
        explanation_route,
        "build_configured_approved_nutrition_explanation_with_metadata",
        lambda user_id, explanation_date, **_kwargs: result,
    )


def test_preview_endpoint_returns_approved_deterministic_explanation(monkeypatch):
    approved = _approved_explanation()
    _patch_user_and_service(monkeypatch, approved)

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["explanation_date"] == "2026-06-07"
    assert payload["confidence"] == "Moderate"
    explanation = payload["approved_nutrition_explanation"]
    assert explanation["explanation_summary"]
    assert "formula-derived" in explanation["calibration_context"]
    assert explanation["source"] if "source" in explanation else True


def test_preview_endpoint_defaults_date_to_today(monkeypatch):
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        explanation_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(user_id: int, explanation_date: str) -> ApprovedNutritionExplanation:
        captured["date"] = explanation_date
        return _approved_explanation(explanation_date=explanation_date)

    monkeypatch.setattr(
        explanation_route,
        "build_configured_approved_nutrition_explanation",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview")

    assert response.status_code == 200
    assert captured["date"] == date_cls.today().isoformat()
    assert response.json()["explanation_date"] == date_cls.today().isoformat()


def test_preview_endpoint_supports_explicit_date(monkeypatch):
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        explanation_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(user_id: int, explanation_date: str) -> ApprovedNutritionExplanation:
        captured["date"] = explanation_date
        return _approved_explanation(explanation_date=explanation_date)

    monkeypatch.setattr(
        explanation_route,
        "build_configured_approved_nutrition_explanation",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-01")

    assert response.status_code == 200
    assert captured["date"] == "2026-06-01"
    assert response.json()["explanation_date"] == "2026-06-01"


def test_preview_endpoint_invalid_date_returns_safe_400(monkeypatch):
    _patch_user_and_service(monkeypatch, _approved_explanation())

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=06-07-2026")

    assert response.status_code == 400
    assert response.json()["detail"] == "date must use YYYY-MM-DD format."


def test_preview_endpoint_nonexistent_user_returns_safe_404(monkeypatch):
    monkeypatch.setattr(explanation_route, "get_user_profile", lambda user_id: None)

    client = TestClient(app)
    response = client.get("/nutrition/999/explanation/preview?date=2026-06-07")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_preview_endpoint_incomplete_context_returns_safe_limited_explanation(
    monkeypatch,
):
    approved = _approved_explanation(
        confidence="Limited",
        reason_codes=["deterministic_nutrition_explanation_fallback"],
        limitations=["Nutrition explanation is limited because context is incomplete."],
    )
    _patch_user_and_service(monkeypatch, approved)

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    payload = response.json()
    assert payload["confidence"] == "Limited"
    assert payload["limitations"]
    assert payload["approved_nutrition_explanation"]["limitations"]


def test_preview_endpoint_returns_safe_400_for_validation_failure(monkeypatch):
    monkeypatch.setattr(
        explanation_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(user_id: int, explanation_date: str) -> ApprovedNutritionExplanation:
        raise ValueError("candidate validation failed")

    monkeypatch.setattr(
        explanation_route,
        "build_configured_approved_nutrition_explanation",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 400
    assert response.json()["detail"] == "AI nutrition explanation validation failed."


def test_preview_response_does_not_expose_raw_internal_or_provider_fields(monkeypatch):
    _patch_user_and_service(monkeypatch, _approved_explanation())

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    payload_text = str(response.json()).lower()
    forbidden_public_terms = [
        "raw_food_entries",
        "raw_daily_checkins",
        "raw_sql",
        "debug_payload",
        "provider_metadata",
        "crewai",
        "ollama",
        "raw_output",
        "validation_errors",
        "raw_output_preview_truncated",
    ]
    assert not any(term in payload_text for term in forbidden_public_terms)


def test_preview_endpoint_does_not_expose_provider_metadata_in_normal_response(
    monkeypatch,
):
    _patch_user_and_service(monkeypatch, _approved_explanation())

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    explanation = response.json()["approved_nutrition_explanation"]
    assert "source" not in explanation
    assert "provider" not in explanation
    assert "fallback_used" not in explanation


def test_preview_endpoint_forbidden_language_does_not_appear(monkeypatch):
    _patch_user_and_service(monkeypatch, _approved_explanation())

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    payload_text = str(response.json()).lower()
    forbidden_terms = [
        "your true maintenance is exactly",
        "your targets have been changed",
        "calibration has been applied",
        "calibrated targets are active",
        "you failed",
        "you must cut calories",
        "burn this off",
        "compensate tomorrow",
        "skip meals",
        "meal plan",
    ]
    assert not any(term in payload_text for term in forbidden_terms)


def test_preview_endpoint_does_not_call_ai_provider(monkeypatch):
    called = {"service": False}

    monkeypatch.setattr(
        explanation_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(user_id: int, explanation_date: str) -> ApprovedNutritionExplanation:
        called["service"] = True
        return _approved_explanation(explanation_date=explanation_date)

    monkeypatch.setattr(
        explanation_route,
        "build_configured_approved_nutrition_explanation",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    assert called["service"] is True
    assert "provider" not in str(response.json()).lower()


def test_debug_endpoint_returns_deterministic_runtime_metadata(monkeypatch):
    metadata = _runtime_metadata(final_explanation_source="deterministic")
    _patch_user_and_result(monkeypatch, _approved_result(metadata=metadata))

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/debug?date=2026-06-07")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["explanation_date"] == "2026-06-07"
    assert payload["approved_nutrition_explanation"]["explanation_summary"]
    runtime = payload["runtime_metadata"]
    assert runtime["configured_provider"] == "deterministic"
    assert runtime["selected_provider"] == "deterministic"
    assert runtime["configured_model"] == "deterministic"
    assert runtime["selected_model"] == "deterministic"
    assert runtime["provider_attempted"] is False
    assert runtime["fallback_used"] is False
    assert runtime["candidate_validation_status"] == "not_attempted"
    assert runtime["markdown_wrapper_detected"] is False
    assert runtime["final_explanation_source"] == "deterministic"


def test_debug_endpoint_returns_invalid_provider_fallback_metadata(monkeypatch):
    metadata = _runtime_metadata(
        configured_provider="not-real",
        selected_provider="deterministic",
        fallback_used=True,
        fallback_reason="invalid_provider_config",
        final_explanation_source="deterministic_fallback",
        validation_errors=["Unsupported provider: not-real"],
    )
    _patch_user_and_result(monkeypatch, _approved_result(metadata=metadata))

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/debug?date=2026-06-07")

    assert response.status_code == 200
    runtime = response.json()["runtime_metadata"]
    assert runtime["configured_provider"] == "not-real"
    assert runtime["selected_provider"] == "deterministic"
    assert runtime["fallback_used"] is True
    assert runtime["fallback_reason"] == "invalid_provider_config"


def test_debug_endpoint_returns_provider_error_fallback_metadata(monkeypatch):
    metadata = _runtime_metadata(
        configured_provider="crewai",
        selected_provider="crewai",
        configured_model="ollama/test-model:3b",
        selected_model="ollama/test-model:3b",
        provider_attempted=True,
        fallback_used=True,
        fallback_reason="provider_exception",
        candidate_valid=False,
        validation_errors=["RuntimeError"],
        final_explanation_source="deterministic_fallback",
    )
    _patch_user_and_result(monkeypatch, _approved_result(metadata=metadata))

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/debug?date=2026-06-07")

    assert response.status_code == 200
    runtime = response.json()["runtime_metadata"]
    assert runtime["configured_model"] == "ollama/test-model:3b"
    assert runtime["selected_model"] == "ollama/test-model:3b"
    assert runtime["provider_attempted"] is True
    assert runtime["fallback_used"] is True
    assert runtime["fallback_reason"] == "provider_exception"
    assert runtime["validation_errors"] == ["RuntimeError"]


def test_debug_endpoint_returns_parse_failure_metadata(monkeypatch):
    metadata = _runtime_metadata(
        configured_provider="crewai",
        selected_provider="crewai",
        provider_attempted=True,
        fallback_used=True,
        fallback_reason="candidate_parse_failure",
        candidate_valid=False,
        validation_errors=["Provider candidate could not be parsed."],
        candidate_parse_status="failed",
        validation_status="not_attempted",
        final_explanation_source="deterministic_fallback",
        raw_output_length=19,
        raw_output_preview_truncated="not valid json output",
        configured_model="ollama/parse-test:4b",
        selected_model="ollama/parse-test:4b",
    )
    _patch_user_and_result(monkeypatch, _approved_result(metadata=metadata))

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/debug?date=2026-06-07")

    assert response.status_code == 200
    runtime = response.json()["runtime_metadata"]
    assert runtime["configured_model"] == "ollama/parse-test:4b"
    assert runtime["selected_model"] == "ollama/parse-test:4b"
    assert runtime["candidate_parse_status"] == "failed"
    assert runtime["candidate_validation_status"] == "not_attempted"
    assert runtime["fallback_reason"] == "candidate_parse_failure"
    assert runtime["raw_output_preview_truncated"] == "not valid json output"


def test_debug_endpoint_returns_validation_failure_metadata(monkeypatch):
    metadata = _runtime_metadata(
        configured_provider="crewai",
        selected_provider="crewai",
        provider_attempted=True,
        fallback_used=True,
        fallback_reason="candidate_validation_failure",
        candidate_valid=False,
        validation_errors=["Forbidden nutrition explanation language detected."],
        candidate_parse_status="success",
        candidate_validation_status="failed",
        validation_status="rejected",
        final_explanation_source="deterministic_fallback",
    )
    _patch_user_and_result(monkeypatch, _approved_result(metadata=metadata))

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/debug?date=2026-06-07")

    assert response.status_code == 200
    runtime = response.json()["runtime_metadata"]
    assert runtime["candidate_valid"] is False
    assert runtime["candidate_validation_status"] == "failed"
    assert runtime["validation_status"] == "rejected"
    assert runtime["validation_errors"]


def test_debug_endpoint_returns_provider_approved_metadata(monkeypatch):
    approved = _approved_explanation(
        reason_codes=["provider_candidate_safe"],
        limitations=[],
    )
    metadata = _runtime_metadata(
        configured_provider="crewai",
        selected_provider="crewai",
        provider_attempted=True,
        fallback_used=False,
        fallback_reason=None,
        candidate_valid=True,
        validation_errors=[],
        candidate_parse_status="success",
        candidate_validation_status="success",
        validation_status="approved",
        final_explanation_source="provider_approved",
        raw_output_length=250,
        raw_output_preview_truncated='{"explanation_summary": "safe"}',
    )
    _patch_user_and_result(monkeypatch, _approved_result(approved, metadata))

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/debug?date=2026-06-07")

    assert response.status_code == 200
    runtime = response.json()["runtime_metadata"]
    assert runtime["fallback_used"] is False
    assert runtime["candidate_valid"] is True
    assert runtime["candidate_validation_status"] == "success"
    assert runtime["validation_status"] == "approved"
    assert runtime["final_explanation_source"] == "provider_approved"


def test_debug_endpoint_returns_direct_ollama_provider_metadata(monkeypatch):
    approved = _approved_explanation(
        reason_codes=["provider_candidate_safe"],
        limitations=[],
    )
    metadata = _runtime_metadata(
        configured_provider="direct_ollama",
        selected_provider="direct_ollama",
        configured_model="ollama/qwen2.5:3b",
        selected_model="qwen2.5:3b",
        provider_attempted=True,
        fallback_used=False,
        fallback_reason=None,
        candidate_valid=True,
        validation_errors=[],
        candidate_parse_status="success",
        candidate_validation_status="success",
        validation_status="approved",
        final_explanation_source="provider_approved",
        raw_output_length=250,
        raw_output_preview_truncated='{"explanation_summary": "safe"}',
    )
    _patch_user_and_result(monkeypatch, _approved_result(approved, metadata))

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/debug?date=2026-06-07")

    assert response.status_code == 200
    runtime = response.json()["runtime_metadata"]
    assert runtime["configured_provider"] == "direct_ollama"
    assert runtime["selected_provider"] == "direct_ollama"
    assert runtime["configured_model"] == "ollama/qwen2.5:3b"
    assert runtime["selected_model"] == "qwen2.5:3b"
    assert runtime["provider_attempted"] is True
    assert runtime["fallback_used"] is False
    assert runtime["candidate_parse_status"] == "success"
    assert runtime["candidate_validation_status"] == "success"
    assert runtime["validation_status"] == "approved"
    assert runtime["final_explanation_source"] == "provider_approved"


def test_preview_endpoint_remains_without_runtime_metadata(monkeypatch):
    _patch_user_and_service(monkeypatch, _approved_explanation())

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    payload = response.json()
    payload_text = str(payload).lower()
    assert "runtime_metadata" not in payload
    assert "configured_provider" not in payload_text
    assert "selected_provider" not in payload_text
    assert "configured_model" not in payload_text
    assert "selected_model" not in payload_text
    assert "validation_errors" not in payload_text


def test_preview_endpoint_does_not_expose_debug_food_candidates(monkeypatch):
    _patch_user_and_service(monkeypatch, _approved_explanation())

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    payload_text = str(response.json()).lower()
    assert "approved_food_suggestion_candidates" not in payload_text
    assert "suggested_grams" not in payload_text


def test_debug_endpoint_exposes_sanitized_approved_food_candidates(monkeypatch):
    candidates = [
        {
            "display_name": "Chicken Breast, Cooked, Skinless",
            "suggested_grams": 150,
            "macro_gap_addressed": "protein_g",
            "suggestion_summary": "150 g chicken breast can support the protein gap.",
        }
    ]
    _patch_user_and_result(
        monkeypatch,
        _approved_result(),
        candidates=candidates,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/debug?date=2026-06-07")

    assert response.status_code == 200
    payload = response.json()
    assert payload["approved_food_suggestion_candidates"] == candidates
    payload_text = str(payload).lower()
    assert "raw_source_payload" not in payload_text
    assert "canonical_food_id" not in payload_text


def test_debug_endpoint_raw_output_preview_is_bounded(monkeypatch):
    metadata = _runtime_metadata(
        configured_provider="crewai",
        selected_provider="crewai",
        provider_attempted=True,
        fallback_used=True,
        fallback_reason="candidate_validation_failure",
        candidate_valid=False,
        validation_errors=["candidate rejected"],
        candidate_parse_status="success",
        validation_status="rejected",
        final_explanation_source="deterministic_fallback",
        raw_output_length=900,
        raw_output_preview_truncated="x" * 500,
        markdown_wrapper_detected=True,
    )
    _patch_user_and_result(monkeypatch, _approved_result(metadata=metadata))

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/debug?date=2026-06-07")

    assert response.status_code == 200
    runtime = response.json()["runtime_metadata"]
    assert runtime["raw_output_length"] == 900
    assert len(runtime["raw_output_preview_truncated"]) <= 500
    assert runtime["markdown_wrapper_detected"] is True


def test_debug_endpoint_does_not_expose_stack_traces_or_raw_internal_context(
    monkeypatch,
):
    metadata = _runtime_metadata(
        configured_provider="crewai",
        selected_provider="crewai",
        provider_attempted=True,
        fallback_used=True,
        fallback_reason="candidate_validation_failure",
        candidate_valid=False,
        validation_errors=["candidate rejected"],
        candidate_parse_status="success",
        validation_status="rejected",
        final_explanation_source="deterministic_fallback",
        raw_output_length=28,
        raw_output_preview_truncated="safe bounded provider preview",
    )
    _patch_user_and_result(monkeypatch, _approved_result(metadata=metadata))

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/debug?date=2026-06-07")

    assert response.status_code == 200
    payload_text = str(response.json()).lower()
    forbidden_terms = [
        "traceback",
        "stack trace",
        "raw_food_entries",
        "raw_daily_checkins",
        "raw_sql",
        "debug_payload",
        "raw_provider_output",
        "context_built",
    ]
    assert not any(term in payload_text for term in forbidden_terms)
