from __future__ import annotations

import json
import urllib.error

import pytest

from models.weekly_coach_summary_provider_models import (
    APPROVED_WEEKLY_PROVIDER_MODEL,
    CandidateWeeklyCoachSummaryProviderOutput,
)
from services.provider_lifecycle_service import resolve_provider_lifecycle_policy
from services.weekly_coach_summary_provider_service import (
    WeeklyCoachSummaryProviderServiceError,
    build_weekly_summary_provider_input,
    generate_weekly_summary_provider_preview,
    resolve_weekly_summary_provider_preview_config,
    validate_weekly_summary_provider_candidate,
)
from services.weekly_coach_summary_service import (
    build_weekly_summary_context_from_fixture,
    generate_approved_weekly_summary,
)


def _context_102():
    return build_weekly_summary_context_from_fixture(
        user_id=102,
        week_start="2026-05-31",
        week_end="2026-06-06",
        training_days_logged=5,
        workouts_completed=5,
        planned_workouts=5,
        recovery_notes_available=True,
        nutrition_days_logged=7,
        protein_days_logged=5,
        average_energy=6,
        average_soreness=3,
    )


def _context_105_low_data():
    return build_weekly_summary_context_from_fixture(
        user_id=105,
        week_start="2026-05-31",
        week_end="2026-06-06",
        training_days_logged=1,
        workouts_completed=1,
        planned_workouts=4,
        recovery_notes_available=True,
        nutrition_days_logged=1,
        protein_days_logged=0,
        average_energy=5,
        average_soreness=5,
        limitations=("data_quality_limited scenario requires cautious language",),
    )


def _candidate_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "A steady week with useful signals",
        "summary": "Because meals were logged across the week, the nutrition signal is strong enough to support a bounded weekly read.",
        "recovery_note": "Because recovery notes are present, recovery guidance can stay specific but not aggressive.",
        "nutrition_note": "You logged nutrition across several days, so nutrition is not a blank spot this week.",
        "training_note": "There are workout sessions but no actual set details, so progression comments should stay conservative.",
        "next_action": "Keep the weekly rhythm and log one workout note so next week has more specific training context.",
        "confidence_label": "Moderate",
        "data_limitations": ["Actual set details are not available for this range."],
        "facts_used": [
            "nutrition logged across the selected week",
            "workout sessions are present",
            "zero actual set rows are available",
        ],
        "safety_flags": ["developer_mode_provider_preview_only"],
        "provider_model": APPROVED_WEEKLY_PROVIDER_MODEL,
        "source_context_metadata": {
            "user_id": 102,
            "start_date": "2026-05-31",
            "end_date": "2026-06-06",
            "source": "qa_date_range_debug",
        },
        "generated_at": "2026-06-24T20:00:00+00:00",
    }
    payload.update(overrides)
    return payload


def _enabled_config(**env_overrides: str):
    env = {
        "FITNESS_AI_WEEKLY_SUMMARY_PROVIDER_PREVIEW_ENABLED": "true",
        "FITNESS_AI_OLLAMA_KEEP_ALIVE": "0",
        "FITNESS_AI_OLLAMA_UNLOAD_AFTER_REQUEST": "true",
        **env_overrides,
    }
    return resolve_weekly_summary_provider_preview_config(environ=env)


def test_provider_preview_config_is_disabled_by_default_and_rejects_qwen3() -> None:
    config = resolve_weekly_summary_provider_preview_config(environ={})

    assert config.enabled is False
    assert config.model_name == "qwen2.5:3b"
    assert config.lifecycle_policy.keep_alive_value == 0

    with pytest.raises(WeeklyCoachSummaryProviderServiceError):
        resolve_weekly_summary_provider_preview_config(
            environ={"FITNESS_AI_WEEKLY_SUMMARY_PROVIDER_MODEL": "qwen3:32b"}
        )


def test_provider_input_builder_uses_backend_context_and_excludes_raw_data() -> None:
    context = _context_102()
    deterministic = generate_approved_weekly_summary(context)

    bundle = build_weekly_summary_provider_input(
        context=context,
        deterministic_summary=deterministic,
    )

    assert bundle.payload["user_id"] == 102
    assert bundle.payload["source"] == "qa_date_range_debug"
    rendered = json.dumps(bundle.payload).lower()
    assert "raw_database_rows" not in rendered
    assert "raw_food_logs" not in rendered
    assert "scratchpad" not in rendered
    assert "chain_of_thought" not in rendered
    assert "qwen2.5:3b" in json.dumps(bundle.response_schema)


def test_provider_preview_disabled_returns_deterministic_without_provider_call() -> (
    None
):
    context = _context_102()
    deterministic = generate_approved_weekly_summary(context)
    called = False

    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        nonlocal called
        called = True
        return {}

    result = generate_weekly_summary_provider_preview(
        context=context,
        deterministic_summary=deterministic,
        config=resolve_weekly_summary_provider_preview_config(environ={}),
        http_post=fake_post,
    )

    assert called is False
    assert result.provider_attempted is False
    assert result.fallback_used is True
    assert result.fallback_reason == "provider_preview_disabled"
    assert result.approved_summary.source.value == deterministic.source.value


def test_provider_preview_sends_keep_alive_and_accepts_grounded_candidate() -> None:
    context = _context_102()
    deterministic = generate_approved_weekly_summary(context)
    calls: list[tuple[str, dict, float]] = []

    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        calls.append((url, payload, timeout))
        return {"response": json.dumps(_candidate_payload())}

    result = generate_weekly_summary_provider_preview(
        context=context,
        deterministic_summary=deterministic,
        config=_enabled_config(),
        http_post=fake_post,
    )

    assert result.provider_attempted is True
    assert result.parse_status == "parsed"
    assert result.validation_status == "approved"
    assert result.fallback_used is False
    assert result.approved_summary.source.value == "provider_approved"
    assert calls[0][1]["model"] == "qwen2.5:3b"
    assert calls[0][1]["keep_alive"] == 0
    assert calls[0][1]["stream"] is False
    assert result.unload_result is not None
    assert result.unload_result.success is True
    assert result.unload_result.action == "skip_unload_already_requested"


def test_provider_preview_rejects_invalid_json_and_keeps_deterministic_fallback() -> (
    None
):
    context = _context_102()
    deterministic = generate_approved_weekly_summary(context)

    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        return {"response": "not json"}

    result = generate_weekly_summary_provider_preview(
        context=context,
        deterministic_summary=deterministic,
        config=_enabled_config(),
        http_post=fake_post,
    )

    assert result.parse_status == "failed"
    assert result.fallback_used is True
    assert result.fallback_reason == "provider_parse_failed"
    assert result.approved_summary.to_dict() == deterministic.to_dict()


def test_provider_preview_falls_back_when_ollama_unreachable() -> None:
    context = _context_102()
    deterministic = generate_approved_weekly_summary(context)

    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        raise urllib.error.URLError("connection refused")

    result = generate_weekly_summary_provider_preview(
        context=context,
        deterministic_summary=deterministic,
        config=_enabled_config(),
        http_post=fake_post,
    )

    assert result.provider_attempted is True
    assert result.fallback_used is True
    assert result.fallback_reason == "provider_unreachable"
    assert result.approved_summary.to_dict() == deterministic.to_dict()


def test_validator_rejects_unsupported_training_progression_without_actual_sets() -> (
    None
):
    context = _context_102()
    candidate = CandidateWeeklyCoachSummaryProviderOutput(
        **_candidate_payload(
            training_note="Because training intensity improved, you can increase load next week."
        )
    )

    validation = validate_weekly_summary_provider_candidate(
        candidate=candidate,
        context=context,
    )

    assert validation.approved is False
    assert (
        "unsupported_training_progression_without_actual_sets"
        in validation.validation_errors
    )


def test_validator_rejects_overconfident_low_data_user_105_candidate() -> None:
    context = _context_105_low_data()
    candidate = CandidateWeeklyCoachSummaryProviderOutput(
        **_candidate_payload(
            confidence_label="Moderate",
            source_context_metadata={
                "user_id": 105,
                "start_date": "2026-05-31",
                "end_date": "2026-06-06",
                "source": "qa_date_range_debug",
            },
        )
    )

    validation = validate_weekly_summary_provider_candidate(
        candidate=candidate,
        context=context,
    )

    assert validation.approved is False
    assert "overconfident_low_data_candidate" in validation.validation_errors


def test_provider_preview_calls_named_model_unload_when_policy_requires_followup() -> (
    None
):
    context = _context_102()
    deterministic = generate_approved_weekly_summary(context)
    unload_calls: list[dict] = []
    policy = resolve_provider_lifecycle_policy(
        provider_name="weekly_coach_summary_provider_preview",
        model_name="qwen2.5:3b",
        environ={"FITNESS_AI_OLLAMA_KEEP_ALIVE": "30s"},
    )
    config = _enabled_config(FITNESS_AI_OLLAMA_KEEP_ALIVE="30s")
    assert config.lifecycle_policy.keep_alive_value == policy.keep_alive_value

    def fake_generate(url: str, payload: dict, timeout: float) -> dict:
        return {"response": json.dumps(_candidate_payload())}

    def fake_unload(url: str, payload: dict, timeout: float) -> dict:
        unload_calls.append(payload)
        return {"done": True}

    result = generate_weekly_summary_provider_preview(
        context=context,
        deterministic_summary=deterministic,
        config=config,
        http_post=fake_generate,
        unload_http_post=fake_unload,
    )

    assert result.validation_status == "approved"
    assert unload_calls == [
        {"model": "qwen2.5:3b", "prompt": "", "stream": False, "keep_alive": 0}
    ]
    assert result.unload_result is not None
    assert result.unload_result.action == "unload_model"
