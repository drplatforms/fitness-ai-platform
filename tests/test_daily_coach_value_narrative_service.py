from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pytest

from models.daily_coach_synthesis_models import DailyCoachSynthesis
from services.daily_coach_value_narrative_service import (
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
    DailyCoachValueNarrativeError,
    build_daily_coach_value_aware_provider_context,
    build_daily_coach_value_narrative_from_synthesis,
    build_daily_coach_value_narrative_prompt,
    build_minimal_value_context_from_synthesis,
    call_openai_daily_coach_narrative,
)


def _synthesis(*, confidence: str = "High") -> DailyCoachSynthesis:
    return DailyCoachSynthesis(
        user_id=102,
        synthesis_date="2026-06-27",
        scenario="aligned_managed",
        confidence=confidence,
        today_summary="Today supports steady execution with no need to overcorrect.",
        recovery_signal="Recovery readiness is high, with fatigue risk currently low.",
        training_signal="No workout has been started today, so training stays tied to the approved plan context.",
        workout_guidance="Use the approved plan as written and keep RIR 2-3 as the anchor today.",
        execution_context="No workout has been started today.",
        logging_focus="Protein is below target based on logged meals, and food suggestions are available.",
        plan_fit_note="No plan-fit concern is strong enough to change today's approved plan.",
        recommended_focus="Use the approved workout plan and close the approved protein gap if it fits.",
        reason_codes=["unit_test", "protein_below_target_based_on_logs"],
        limitations=[
            "Because logging is incomplete, calorie interpretation should stay cautious."
        ],
    )


def _value_context() -> dict:
    return {
        "approved_recovery": {
            "readiness_level": "High",
            "fatigue_risk": "Low",
            "recovery_signal": "Recovery readiness is high, with fatigue risk currently low.",
        },
        "approved_nutrition": {
            "available": True,
            "macro_status": {
                "protein": {"display_allowed": True, "target_status": "below_target"},
                "calories": {"display_allowed": False},
            },
            "approved_food_suggestions": [
                {
                    "display_name": "Greek Yogurt, Plain",
                    "suggested_grams": 170,
                    "macro_gap_addressed": "protein_g",
                }
            ],
        },
        "approved_training": {
            "training_signal": "No workout has been started today, so training stays tied to the approved plan context."
        },
        "approved_limitations": [
            "Because logging is incomplete, calorie interpretation should stay cautious."
        ],
        "approved_value_claims": [
            {
                "key": "recovery.readiness_level",
                "label": "readiness",
                "value": "High",
                "unit": None,
                "aliases": ["readiness is High", "readiness High"],
                "claim_type": "recovery",
                "display_allowed": True,
                "source": "approved_recovery",
                "confidence": "High",
            },
            {
                "key": "recovery.fatigue_risk",
                "label": "fatigue risk",
                "value": "Low",
                "unit": None,
                "aliases": ["fatigue risk is Low", "fatigue risk Low"],
                "claim_type": "recovery",
                "display_allowed": True,
                "source": "approved_recovery",
                "confidence": "High",
            },
            {
                "key": "recovery.recovery_score",
                "label": "recovery score",
                "value": 90,
                "unit": None,
                "aliases": ["recovery score is 90", "90"],
                "claim_type": "recovery",
                "display_allowed": True,
                "source": "approved_recovery",
                "confidence": "High",
            },
            {
                "key": "nutrition.actuals.logged_protein_g",
                "label": "logged protein",
                "value": 3.7,
                "unit": "g",
                "aliases": ["3.7g", "logged protein 3.7g"],
                "claim_type": "nutrition_actual",
                "display_allowed": True,
                "source": "target_vs_actual_summary",
                "confidence": "Moderate",
            },
            {
                "key": "nutrition.protein.status",
                "label": "protein status",
                "value": "below_target",
                "unit": None,
                "aliases": ["protein is below target", "protein below target"],
                "claim_type": "nutrition_gap",
                "display_allowed": True,
                "source": "target_vs_actual_summary",
                "confidence": "Moderate",
            },
            {
                "key": "nutrition.calories.target_min",
                "label": "calories target_min",
                "value": 2400,
                "unit": "kcal",
                "aliases": ["2400 calories", "2400kcal"],
                "claim_type": "nutrition_target",
                "display_allowed": False,
                "source": "target_vs_actual_summary",
                "confidence": "Limited",
            },
            {
                "key": "training.rir_range",
                "label": "RIR range",
                "value": "2-4",
                "unit": None,
                "aliases": ["RIR 2-4", "RIR 2–4"],
                "claim_type": "training",
                "display_allowed": True,
                "source": "daily_coach_synthesis",
                "confidence": "High",
            },
        ],
    }


def _valid_candidate() -> str:
    return json.dumps(
        {
            "headline": "Daily Coach",
            "summary": "Today is set up for steady execution without forcing a major adjustment.",
            "nutrition_note": "Protein is currently below the approved target based on logged meals.",
            "training_note": "No workout has been started today, so training guidance should stay limited to the approved plan context.",
            "recovery_note": "Recovery looks strong today: readiness is High and fatigue risk is Low.",
            "priority_action": "Use the approved workout plan and close the approved protein gap if it fits.",
            "confidence": "High",
            "reason_codes": ["provider_candidate_value_aware"],
            "quoted_values_used": [
                "recovery.readiness_level",
                "recovery.fatigue_risk",
                "nutrition.protein.status",
            ],
        }
    )


def _install_fake_openai_sdk(
    monkeypatch, *, output_text: str | None = None, exc: Exception | None = None
):
    calls: dict[str, object] = {}

    class FakeResponses:
        def create(self, **kwargs):
            calls["responses_create_kwargs"] = kwargs
            if exc is not None:
                raise exc
            return SimpleNamespace(output_text=output_text)

    class FakeOpenAI:
        def __init__(self, **kwargs):
            calls["client_kwargs"] = kwargs
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    return calls


class _FakeOpenAIStatusError(Exception):
    def __init__(self, message: str, *, status_code: int, body: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body or {}


def test_deterministic_provider_is_default() -> None:
    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={},
    )

    metadata = result.runtime_metadata
    assert metadata.selected_provider == "deterministic"
    assert metadata.provider_attempted is False
    assert metadata.fallback_used is False
    assert result.approved_daily_coach_narrative.source == "deterministic"


def test_direct_ollama_mocked_exact_schema_response_approves() -> None:
    calls = []

    def fake_generate(model: str, prompt: str, timeout: float) -> str:
        calls.append({"model": model, "prompt": prompt, "timeout": timeout})
        return _valid_candidate()

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={
            "DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA,
            "DAILY_COACH_NARRATIVE_MODEL": "ollama/qwen3:8b",
        },
        direct_ollama_generate=fake_generate,
    )

    metadata = result.runtime_metadata
    assert calls
    assert metadata.selected_provider == "direct_ollama"
    assert metadata.selected_model == "ollama/qwen3:8b"
    assert metadata.fallback_used is False
    assert metadata.candidate_parse_status == "success"
    assert metadata.candidate_validation_status == "success"
    assert result.approved_daily_coach_narrative.source == "direct_ollama_approved"


def test_openai_mocked_exact_schema_response_approves() -> None:
    def fake_generate(model: str, prompt: str, timeout: float) -> str:
        assert model == "gpt-test"
        assert "approved_value_context" in prompt
        return _valid_candidate()

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={
            "DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_OPENAI,
            "DAILY_COACH_NARRATIVE_MODEL": "gpt-test",
            "OPENAI_API_KEY": "test-key",
        },
        openai_generate=fake_generate,
    )

    assert result.runtime_metadata.selected_provider == "openai"
    assert result.runtime_metadata.fallback_used is False
    assert result.approved_daily_coach_narrative.source == "openai_approved"


def test_openai_missing_api_key_falls_back_safely() -> None:
    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_OPENAI},
    )

    metadata = result.runtime_metadata
    assert metadata.provider_attempted is True
    assert metadata.fallback_used is True
    assert metadata.fallback_reason == "openai_missing_api_key"
    assert result.approved_daily_coach_narrative.source == "deterministic_fallback"


def test_openai_provider_uses_responses_api_output_text(monkeypatch) -> None:
    calls = _install_fake_openai_sdk(monkeypatch, output_text=_valid_candidate())

    raw = call_openai_daily_coach_narrative(
        "gpt-5.5",
        "Return JSON",
        7.0,
        api_key="test-secret",
        base_url="https://example.test/v1",
    )

    assert json.loads(raw)["headline"] == "Daily Coach"
    assert calls["client_kwargs"] == {
        "api_key": "test-secret",
        "base_url": "https://example.test/v1",
    }
    assert calls["responses_create_kwargs"] == {
        "model": "gpt-5.5",
        "instructions": "Return exact JSON only for the requested schema.",
        "input": "Return JSON",
        "max_output_tokens": 1200,
        "timeout": 7.0,
    }


def test_openai_responses_api_auth_error_is_classified(monkeypatch) -> None:
    _install_fake_openai_sdk(
        monkeypatch,
        exc=_FakeOpenAIStatusError("invalid api key", status_code=401),
    )

    with pytest.raises(DailyCoachValueNarrativeError) as exc_info:
        call_openai_daily_coach_narrative(
            "gpt-5.5", "Return JSON", 7.0, api_key="bad-key"
        )

    assert str(exc_info.value) == "openai_authentication_failed"


def test_openai_responses_api_quota_error_is_classified(monkeypatch) -> None:
    _install_fake_openai_sdk(
        monkeypatch,
        exc=_FakeOpenAIStatusError(
            "insufficient quota",
            status_code=429,
            body={"error": {"code": "insufficient_quota"}},
        ),
    )

    with pytest.raises(DailyCoachValueNarrativeError) as exc_info:
        call_openai_daily_coach_narrative(
            "gpt-5.5", "Return JSON", 7.0, api_key="test-secret"
        )

    assert str(exc_info.value) == "openai_insufficient_quota"


def test_openai_responses_api_model_not_found_is_classified(monkeypatch) -> None:
    _install_fake_openai_sdk(
        monkeypatch,
        exc=_FakeOpenAIStatusError(
            "model not found",
            status_code=404,
            body={"error": {"code": "model_not_found"}},
        ),
    )

    with pytest.raises(DailyCoachValueNarrativeError) as exc_info:
        call_openai_daily_coach_narrative(
            "not-a-model", "Return JSON", 7.0, api_key="test-secret"
        )

    assert str(exc_info.value) == "openai_model_not_found"


def test_openai_responses_api_timeout_is_classified(monkeypatch) -> None:
    timeout_error = type("APITimeoutError", (Exception,), {})("request timed out")
    _install_fake_openai_sdk(monkeypatch, exc=timeout_error)

    with pytest.raises(DailyCoachValueNarrativeError) as exc_info:
        call_openai_daily_coach_narrative(
            "gpt-5.5", "Return JSON", 7.0, api_key="test-secret"
        )

    assert str(exc_info.value) == "openai_timeout"


def test_openai_responses_api_missing_output_text_is_classified(monkeypatch) -> None:
    _install_fake_openai_sdk(monkeypatch, output_text="")

    with pytest.raises(DailyCoachValueNarrativeError) as exc_info:
        call_openai_daily_coach_narrative(
            "gpt-5.5", "Return JSON", 7.0, api_key="test-secret"
        )

    assert str(exc_info.value) == "openai_missing_response"


def test_provider_extra_keys_fall_back() -> None:
    bad = json.loads(_valid_candidate())
    bad["extra"] = "not allowed"

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(bad),
    )

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.candidate_parse_status == "failed"
    assert "extra_keys" in result.runtime_metadata.fallback_reason


def test_provider_markdown_wrapped_output_falls_back() -> None:
    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: (
            f"```json\n{_valid_candidate()}\n```"
        ),
    )

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.markdown_wrapper_detected is True
    assert result.runtime_metadata.candidate_parse_status == "failed"


def test_provider_cannot_claim_no_recovery_when_recovery_signal_exists() -> None:
    bad = json.loads(_valid_candidate())
    bad["recovery_note"] = "There are no recovery notes today."

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(bad),
    )

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.candidate_validation_status == "failed"
    assert any("recovery" in err for err in result.runtime_metadata.validation_errors)


def test_provider_cannot_say_without_needing_to_address_training_or_recovery() -> None:
    bad = json.loads(_valid_candidate())
    bad["summary"] = (
        "This can focus on nutrition without needing to address training or recovery."
    )

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(bad),
    )

    assert result.runtime_metadata.fallback_used is True
    assert result.approved_daily_coach_narrative.source == "deterministic_fallback"


def test_provider_cannot_quote_calorie_target_when_not_display_approved() -> None:
    bad = json.loads(_valid_candidate())
    bad["nutrition_note"] = "You need 2400 calories today to stay on target."

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(bad),
    )

    assert result.runtime_metadata.fallback_used is True
    assert any("calorie" in err for err in result.runtime_metadata.validation_errors)


def test_value_aware_prompt_includes_approved_values_and_excludes_raw_metadata() -> (
    None
):
    prompt = build_daily_coach_value_narrative_prompt(
        _synthesis(),
        value_context=_value_context(),
    )

    assert "readiness" in prompt
    assert "High" in prompt
    assert "fatigue risk" in prompt.lower() or "fatigue_risk" in prompt
    assert "approved_value_context" in prompt
    assert "raw_output" not in prompt
    assert "runtime_metadata" not in prompt


def test_build_value_context_includes_recovery_values_from_health_state() -> None:
    class Recovery:
        readiness_level = "High"
        fatigue_risk = "Low"
        recovery_score = 90
        avg_sleep = 7.4
        avg_energy = 6.3
        avg_soreness = 2.6

    class HealthState:
        recovery_state = Recovery()

    context = build_daily_coach_value_aware_provider_context(
        user_id=102,
        narrative_date="2026-06-27",
        synthesis=_synthesis(),
        health_state=HealthState(),
    )

    recovery = context["approved_recovery"]
    assert recovery["readiness_level"] == "High"
    assert recovery["fatigue_risk"] == "Low"
    assert recovery["recovery_score"] == 90


def test_candidate_requires_quoted_values_used() -> None:
    bad = json.loads(_valid_candidate())
    bad.pop("quoted_values_used")

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(bad),
    )

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.candidate_parse_status == "failed"
    assert "missing_keys" in result.runtime_metadata.fallback_reason


def test_provider_can_quote_recovery_score_when_approved() -> None:
    good = json.loads(_valid_candidate())
    good["recovery_note"] = (
        "Recovery score is 90, readiness is High, and fatigue risk is Low."
    )
    good["quoted_values_used"] = [
        "recovery.recovery_score",
        "recovery.readiness_level",
        "recovery.fatigue_risk",
    ]

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(good),
    )

    assert result.runtime_metadata.fallback_used is False
    assert (
        "recovery.recovery_score"
        in result.approved_daily_coach_narrative.quoted_values_used
    )


def test_provider_can_quote_logged_protein_when_approved() -> None:
    good = json.loads(_valid_candidate())
    good["nutrition_note"] = (
        "Logged protein is 3.7g, and protein is below target based on logged meals."
    )
    good["quoted_values_used"] = [
        "recovery.readiness_level",
        "recovery.fatigue_risk",
        "nutrition.actuals.logged_protein_g",
        "nutrition.protein.status",
    ]

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(good),
    )

    assert result.runtime_metadata.fallback_used is False
    assert (
        "nutrition.actuals.logged_protein_g"
        in result.approved_daily_coach_narrative.quoted_values_used
    )


def test_provider_can_quote_rir_range_when_approved() -> None:
    good = json.loads(_valid_candidate())
    good["training_note"] = (
        "Aim for RIR 2-4 today while staying tied to the approved plan context."
    )
    good["quoted_values_used"] = [
        "recovery.readiness_level",
        "recovery.fatigue_risk",
        "training.rir_range",
    ]

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(good),
    )

    assert result.runtime_metadata.fallback_used is False
    assert (
        "training.rir_range" in result.approved_daily_coach_narrative.quoted_values_used
    )


def test_provider_cannot_mention_number_without_declaring_it() -> None:
    bad = json.loads(_valid_candidate())
    bad["recovery_note"] = (
        "Recovery score is 90, readiness is High, and fatigue risk is Low."
    )
    bad["quoted_values_used"] = [
        "recovery.readiness_level",
        "recovery.fatigue_risk",
    ]

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(bad),
    )

    assert result.runtime_metadata.fallback_used is True
    assert any(
        "undeclared numeric" in err for err in result.runtime_metadata.validation_errors
    )


def test_provider_cannot_declare_unknown_quoted_value() -> None:
    bad = json.loads(_valid_candidate())
    bad["quoted_values_used"] = ["nutrition.protein.target_max"]

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(bad),
    )

    assert result.runtime_metadata.fallback_used is True
    assert any(
        "unapproved value" in err for err in result.runtime_metadata.validation_errors
    )


def test_provider_cannot_quote_display_blocked_value() -> None:
    bad = json.loads(_valid_candidate())
    bad["nutrition_note"] = "You need 2400 calories today to stay on target."
    bad["quoted_values_used"] = ["nutrition.calories.target_min"]

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(bad),
    )

    assert result.runtime_metadata.fallback_used is True
    assert any(
        "not display-approved" in err
        for err in result.runtime_metadata.validation_errors
    )


def test_normal_endpoint_approved_narrative_includes_quoted_values_but_hides_metadata() -> (
    None
):
    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={},
    )

    payload = result.to_public_dict()
    assert "quoted_values_used" in payload["approved_daily_coach_narrative"]
    assert "runtime_metadata" not in payload


def test_invalid_provider_config_falls_back_to_deterministic() -> None:
    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=build_minimal_value_context_from_synthesis(_synthesis()),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": "wat"},
    )

    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.fallback_reason == "invalid_provider"
    assert result.approved_daily_coach_narrative.source == "deterministic_fallback"


def test_approved_claim_metadata_is_backward_compatible_and_enriched() -> None:
    context = build_minimal_value_context_from_synthesis(_synthesis())
    claims = {claim["key"]: claim for claim in context["approved_value_claims"]}

    rir_claim = claims["training.rir_range"]
    assert rir_claim["display_allowed"] is True
    assert rir_claim["priority"] == 1
    assert rir_claim["section_hint"] == "training_note"
    assert rir_claim["coaching_use"] == "support_training_action"
    assert rir_claim["value_style"] == "range_allowed"

    limitation_claim = claims["limitation.1"]
    assert limitation_claim["priority"] == 2
    assert limitation_claim["value_style"] == "limitation_only"


def test_provider_context_packaging_adds_high_value_and_preferred_claims() -> None:
    context = build_minimal_value_context_from_synthesis(_synthesis())

    assert context["provider_task_context"]["target_total_claims"] == "1-2"
    assert context["claim_budgets"]["total"]["max"] <= 4
    assert "training.rir_range" in context["high_value_claims"]
    assert "training.rir_range" in context["preferred_claims_by_field"]["training_note"]
    assert context["claim_usage_rules"]["do_not_dump_all_claims"] is True
    assert "priority_action" in context["field_role_guidance"]


def test_prompt_includes_copy_grounding_field_roles_and_claim_rules() -> None:
    prompt = build_daily_coach_value_narrative_prompt(
        _synthesis(),
        value_context=build_minimal_value_context_from_synthesis(_synthesis()),
    )

    assert "Use 3-6 high-value approved claims when context is rich" in prompt
    assert "Target useful, grounded, scannable coaching" in prompt
    assert "Allow more words only when" in prompt
    assert "Do not dump all claims" in prompt
    assert "FIELD_ROLE_GUIDANCE" in prompt
    assert "CLAIM_USAGE_RULES" in prompt
    assert "quoted_values_used may contain only exact keys" in prompt
    assert "Do not mention backend" in prompt
    assert "Return one raw JSON object only" in prompt


def test_rich_context_uses_v2_today_story_claim_budgets_and_adaptive_verbosity() -> (
    None
):
    context = _value_context()
    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=context,
        environ={},
    )

    summary = result.provider_context_summary
    today_story = summary["today_story"]
    assert today_story["day_type"] in {
        "nutrition_support",
        "nutrition_supported_strength_day",
        "training_execution_focus",
        "controlled_progress",
    }
    assert "nutrition.protein.status" in today_story["primary_claim_keys"]
    assert summary["claim_budgets"]["total"]["min"] == 3
    assert summary["claim_budgets"]["total"]["max"] == 6
    assert len(summary["high_value_claims_available"]) >= 3
    assert summary["adaptive_verbosity_guidance"]["target"] == (
        "useful, grounded, scannable coaching"
    )
    assert "maximum brevity" in summary["adaptive_verbosity_guidance"]["not_the_target"]


def test_prompt_includes_today_story_budgets_and_adaptive_verbosity_guidance() -> None:
    context = _value_context()
    prompt = build_daily_coach_value_narrative_prompt(
        _synthesis(), value_context=context
    )

    assert "TODAY_STORY_AND_CLAIM_BUDGETS" in prompt
    assert "claim_budgets" in prompt
    assert "adaptive_verbosity_guidance" in prompt
    assert "What kind of day" not in prompt
    assert "useful, grounded, scannable coaching" in prompt
    assert "model repeats metrics" in prompt


def test_v3_context_includes_context_brief_backing_map_and_verbosity_budget() -> None:
    context = _value_context()
    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=context,
        environ={},
    )

    summary = result.provider_context_summary
    brief = summary["approved_context_brief"]
    assert brief["sentences"]
    assert all(sentence["claim_keys"] for sentence in brief["sentences"])
    brief_text = " ".join(sentence["text"] for sentence in brief["sentences"])
    for banned in ["main lever", "effort anchor", "planned effort range"]:
        assert banned not in brief_text.lower()

    backing_map = summary["claim_backing_map"]
    assert backing_map
    assert any(
        item["claim_key"] == "training.rir_range" for item in backing_map.values()
    )
    assert summary["verbosity_budget"]["mode"] in {"normal", "rich"}
    assert summary["verbosity_budget"]["target_words_min"] > 0


def test_v3_prompt_includes_natural_voice_examples_and_context_brief() -> None:
    context = _value_context()
    prompt = build_daily_coach_value_narrative_prompt(
        _synthesis(), value_context=context
    )

    assert "APPROVED_CONTEXT_BRIEF" in prompt
    assert "CLAIM_BACKING_MAP" in prompt
    assert "VOICE_EXAMPLES" in prompt
    assert "VERBOSITY_BUDGET" in prompt
    assert "real practical coach" in prompt
    assert "Keep a couple reps in reserve" in prompt
    assert "main lever" in prompt


def test_v3_framework_phrase_candidate_falls_back() -> None:
    def fake_generate(model: str, prompt: str, timeout: float) -> str:
        payload = json.loads(_valid_candidate())
        payload["summary"] = "Make nutrition support the main lever today."
        payload["training_note"] = "Use RIR 2-4 as your effort anchor."
        payload["quoted_values_used"] = [
            "nutrition.protein.status",
            "training.rir_range",
        ]
        return json.dumps(payload)

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={
            "DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA,
            "DAILY_COACH_NARRATIVE_MODEL": "ollama/test",
        },
        direct_ollama_generate=fake_generate,
    )

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "candidate_validation_failure"
    assert any(
        "main lever" in error for error in result.runtime_metadata.validation_errors
    )


def test_v3_raw_claim_key_candidate_falls_back() -> None:
    def fake_generate(model: str, prompt: str, timeout: float) -> str:
        payload = json.loads(_valid_candidate())
        payload["priority_action"] = "Use nutrition.protein.status to guide the day."
        return json.dumps(payload)

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_value_context(),
        environ={
            "DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA,
            "DAILY_COACH_NARRATIVE_MODEL": "ollama/test",
        },
        direct_ollama_generate=fake_generate,
    )

    assert result.runtime_metadata.fallback_used is True
    assert any(
        "raw claim keys" in error for error in result.runtime_metadata.validation_errors
    )


def _tuna_value_context() -> dict:
    context = _value_context()
    context["approved_nutrition"] = {
        **context["approved_nutrition"],
        "macro_status": {
            "protein": {"display_allowed": True, "target_status": "below_target"},
            "calories": {"display_allowed": True, "target_status": "below_target"},
        },
        "approved_food_suggestions": [
            {
                "display_name": "Tuna, Canned in Water",
                "suggested_grams": 100,
                "macro_gap_addressed": "protein_g",
                "confidence": "Moderate",
            }
        ],
    }
    context.pop("approved_value_claims", None)
    return context


def test_v4_context_adds_friendly_food_label_and_action_context() -> None:
    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_tuna_value_context(),
        environ={},
    )

    summary = result.provider_context_summary
    food_copy = summary["food_suggestion_copy_context"]
    suggestion = food_copy["suggestions"][0]
    assert suggestion["canonical_name"] == "Tuna, Canned in Water"
    assert suggestion["friendly_name"] == "canned tuna"
    assert suggestion["claim_keys"]["friendly_name"] == (
        "nutrition.food_suggestion.1.friendly_name"
    )
    nutrition_action = summary["nutrition_action_context"]
    assert nutrition_action["primary_gap"] == "protein"
    assert nutrition_action["action_type"] == "simple_add_on"
    assert nutrition_action["approved_food_option_count"] == 1


def test_v4_prompt_includes_food_copy_context_and_bans_rejected_phrases() -> None:
    prompt = build_daily_coach_value_narrative_prompt(
        _synthesis(),
        value_context=_tuna_value_context(),
    )

    assert "FOOD_SUGGESTION_COPY_CONTEXT" in prompt
    assert "NUTRITION_ACTION_CONTEXT" in prompt
    assert "canned tuna" in prompt
    assert "Make nutrition support the work" in prompt
    assert "Fuel the session instead" in prompt
    assert "fatigue does not require backing off" in prompt


def test_v4_friendly_food_label_passes_when_quote_backed() -> None:
    good = json.loads(_valid_candidate())
    good["nutrition_note"] = "Protein is below target; an easy option is canned tuna."
    good["priority_action"] = "Add 100g canned tuna and keep the workout clean."
    good["quoted_values_used"] = [
        "recovery.readiness_level",
        "recovery.fatigue_risk",
        "nutrition.protein.status",
        "nutrition.food_suggestion.1.friendly_name",
        "nutrition.food_suggestion.1.suggested_grams",
    ]

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_tuna_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(good),
    )

    assert result.runtime_metadata.fallback_used is False
    assert "nutrition.food_suggestion.1.friendly_name" in (
        result.approved_daily_coach_narrative.quoted_values_used
    )


def test_v4_canonical_food_label_falls_back_when_friendly_label_exists() -> None:
    bad = json.loads(_valid_candidate())
    bad["nutrition_note"] = "Protein is below target; use Tuna, Canned in Water."
    bad["quoted_values_used"] = [
        "nutrition.protein.status",
        "nutrition.food_suggestion.1.display_name",
    ]

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_tuna_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(bad),
    )

    assert result.runtime_metadata.fallback_used is True
    assert any(
        "friendly food label" in error
        for error in result.runtime_metadata.validation_errors
    )


def test_v4_rejected_phrase_candidate_falls_back() -> None:
    bad = json.loads(_valid_candidate())
    bad["priority_action"] = (
        "The useful move is simple: make nutrition support the work."
    )

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_tuna_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(bad),
    )

    assert result.runtime_metadata.fallback_used is True
    assert any(
        "forbidden phrase" in error
        for error in result.runtime_metadata.validation_errors
    )


def test_v4_unapproved_serving_display_falls_back() -> None:
    bad = json.loads(_valid_candidate())
    bad["nutrition_note"] = "Protein is below target; add one can of canned tuna."
    bad["quoted_values_used"] = [
        "nutrition.protein.status",
        "nutrition.food_suggestion.1.friendly_name",
    ]

    result = build_daily_coach_value_narrative_from_synthesis(
        _synthesis(),
        value_context=_tuna_value_context(),
        environ={"DAILY_COACH_NARRATIVE_PROVIDER": PROVIDER_DIRECT_OLLAMA},
        direct_ollama_generate=lambda model, prompt, timeout: json.dumps(bad),
    )

    assert result.runtime_metadata.fallback_used is True
    assert any(
        "serving display" in error
        for error in result.runtime_metadata.validation_errors
    )
