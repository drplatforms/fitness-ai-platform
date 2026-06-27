from __future__ import annotations

import json

from models.daily_coach_synthesis_models import DailyCoachSynthesis
from services.daily_coach_value_narrative_service import (
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
    build_daily_coach_value_aware_provider_context,
    build_daily_coach_value_narrative_from_synthesis,
    build_daily_coach_value_narrative_prompt,
    build_minimal_value_context_from_synthesis,
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
