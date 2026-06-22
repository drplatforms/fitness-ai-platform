from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

from models.async_daily_coach_narrative_models import (
    DAILY_COACH_NARRATIVE_BRIDGE_BASELINE_MODEL,
    DAILY_COACH_NARRATIVE_FORBIDDEN_DIAGNOSTIC_KEYS,
    ApprovedDailyCoachNarrativePayload,
    DailyCoachNarrativeJob,
    DailyCoachNarrativeJobStatus,
    DailyCoachNarrativeModelLane,
    SanitizedDailyCoachNarrativeDiagnostics,
    get_daily_coach_narrative_model_lane,
    is_daily_coach_narrative_bridge_approved_model,
    is_daily_coach_narrative_premium_async_candidate,
)
from services.async_daily_coach_context_identity import (
    DailyCoachNarrativeContextHashError,
    build_daily_coach_narrative_context_hash,
    build_daily_coach_narrative_context_identity,
)

REQUIRED_STATUS_VALUES = {
    "not_requested",
    "queued",
    "generating",
    "provider_succeeded_pending_validation",
    "approved",
    "rejected_validation",
    "rejected_parse",
    "provider_timeout",
    "provider_error",
    "stale",
    "expired",
    "fallback_available",
}


FORBIDDEN_RUNTIME_TOKENS = [
    "ollama",
    "requests.",
    "httpx",
    "subprocess",
    "BackgroundTasks",
    "asyncio.create_task",
    "threading.Thread",
]


def _approved_context() -> dict[str, object]:
    return {
        "daily_next_action": {
            "id": "log_food",
            "title": "Log a meal or snack",
            "workflow_target": "nutrition_quick_log",
        },
        "health_state_summary": {
            "nutrition_confidence": "Limited",
            "recovery_state": "Known",
        },
        "approved_facts": [
            "Daily next action: Log a meal or snack",
            "Workflow target: nutrition_quick_log",
        ],
    }


def test_required_job_statuses_exist() -> None:
    actual = {status.value for status in DailyCoachNarrativeJobStatus}

    assert actual == REQUIRED_STATUS_VALUES


def test_model_lanes_exist() -> None:
    actual = {lane.value for lane in DailyCoachNarrativeModelLane}

    assert actual == {
        "deterministic",
        "fast_manual_bridge",
        "premium_async_candidate",
        "experimental_probe",
    }


def test_context_identity_can_be_created_with_model_lane_metadata() -> None:
    identity = build_daily_coach_narrative_context_identity(
        user_id=102,
        target_date="2026-06-21",
        next_action_id="log_food",
        workflow_target="nutrition_quick_log",
        provider="direct_ollama",
        model="qwen2.5:3b",
        prompt_contract_version="daily_coach_narrative_v1",
        validator_version="daily_coach_narrative_validator_v1",
        approved_context_inputs=_approved_context(),
    )

    assert identity.user_id == 102
    assert identity.context_hash
    assert len(identity.context_hash) == 64
    assert identity.model_lane == DailyCoachNarrativeModelLane.FAST_MANUAL_BRIDGE
    assert identity.bridge_approved is True
    assert identity.to_dict()["model_lane"] == "fast_manual_bridge"


def test_context_hash_is_deterministic_and_key_order_insensitive() -> None:
    context_a = {
        "approved_facts": ["A", "B"],
        "nested": {"second": 2, "first": 1},
        "workflow_target": "nutrition_quick_log",
    }
    context_b = {
        "workflow_target": "nutrition_quick_log",
        "nested": {"first": 1, "second": 2},
        "approved_facts": ["A", "B"],
    }

    assert build_daily_coach_narrative_context_hash(context_a) == (
        build_daily_coach_narrative_context_hash(context_b)
    )


def test_context_hash_changes_when_meaningful_inputs_change() -> None:
    base = _approved_context()
    changed = {
        **base,
        "daily_next_action": {
            "id": "keep_training_conservative",
            "title": "Keep training conservative",
            "workflow_target": "today_recovery_aware_workout",
        },
    }

    assert build_daily_coach_narrative_context_hash(base) != (
        build_daily_coach_narrative_context_hash(changed)
    )


def test_context_hash_rejects_raw_provider_prompt_or_output_fields() -> None:
    with pytest.raises(DailyCoachNarrativeContextHashError):
        build_daily_coach_narrative_context_hash(
            {
                "approved_facts": ["safe fact"],
                "raw_output": "rejected provider text must not be hashed",
            }
        )

    with pytest.raises(DailyCoachNarrativeContextHashError):
        build_daily_coach_narrative_context_hash(
            {
                "approved_context": {
                    "raw_prompt": "prompt internals must not become cache identity"
                }
            }
        )


def test_approved_narrative_payload_has_no_raw_output_contract_fields() -> None:
    payload = ApprovedDailyCoachNarrativePayload(
        narrative="Log a meal or snack so today's nutrition guidance has enough data.",
        key_takeaway="Nutrition confidence is limited until food is logged.",
        recommended_focus="Log a meal or snack",
        source="validated_async_candidate",
        provider="direct_ollama",
        model="qwen2.5:3b",
        validation_summary={"claim_safety": "approved"},
    )

    field_names = {field.name for field in fields(ApprovedDailyCoachNarrativePayload)}
    assert field_names.isdisjoint(DAILY_COACH_NARRATIVE_FORBIDDEN_DIAGNOSTIC_KEYS)
    assert "raw" not in str(payload.to_dict()).lower()


def test_sanitized_diagnostics_has_no_raw_prompt_or_output_fields() -> None:
    diagnostics = SanitizedDailyCoachNarrativeDiagnostics(
        provider_attempted=True,
        selected_provider="direct_ollama",
        selected_model="qwen3:32b",
        parse_success=False,
        validation_success=False,
        fallback_used=True,
        fallback_reason="provider_parse_failed",
        failure_classification="rejected_parse",
        latency_ms=336000,
        model_lane=DailyCoachNarrativeModelLane.PREMIUM_ASYNC_CANDIDATE,
        approval_eligible=False,
    )

    field_names = {
        field.name for field in fields(SanitizedDailyCoachNarrativeDiagnostics)
    }
    assert field_names.isdisjoint(DAILY_COACH_NARRATIVE_FORBIDDEN_DIAGNOSTIC_KEYS)
    assert diagnostics.to_dict()["model_lane"] == "premium_async_candidate"
    assert "raw_output" not in diagnostics.to_dict()
    assert "raw_prompt" not in diagnostics.to_dict()
    assert "traceback" not in diagnostics.to_dict()


def test_qwen_model_policy_boundaries_are_encoded_without_promotion() -> None:
    assert DAILY_COACH_NARRATIVE_BRIDGE_BASELINE_MODEL == "qwen2.5:3b"
    assert is_daily_coach_narrative_bridge_approved_model("qwen2.5:3b") is True
    assert get_daily_coach_narrative_model_lane("qwen2.5:3b") == (
        DailyCoachNarrativeModelLane.FAST_MANUAL_BRIDGE
    )

    assert is_daily_coach_narrative_bridge_approved_model("qwen3:32b") is False
    assert is_daily_coach_narrative_premium_async_candidate("qwen3:32b") is True
    assert get_daily_coach_narrative_model_lane("qwen3:32b") == (
        DailyCoachNarrativeModelLane.PREMIUM_ASYNC_CANDIDATE
    )

    for model in ["qwen2.5:7b", "qwen3:8b", "qwen3:14b", "qwen3:30b-a3b"]:
        assert is_daily_coach_narrative_bridge_approved_model(model) is False
        assert get_daily_coach_narrative_model_lane(model) == (
            DailyCoachNarrativeModelLane.EXPERIMENTAL_PROBE
        )


def test_job_contract_is_in_memory_and_exposes_context_identity() -> None:
    job = DailyCoachNarrativeJob(
        id="job-1",
        user_id=102,
        target_date="2026-06-21",
        next_action_id="log_food",
        workflow_target="nutrition_quick_log",
        provider="direct_ollama",
        model="qwen3:32b",
        context_hash="abc123",
        prompt_contract_version="daily_coach_narrative_v1",
        validator_version="daily_coach_narrative_validator_v1",
        status=DailyCoachNarrativeJobStatus.QUEUED,
    )

    assert job.to_dict()["status"] == "queued"
    assert job.to_dict()["model_lane"] == "premium_async_candidate"
    assert job.approval_eligible is False
    assert job.context_identity().context_hash == "abc123"


def test_contract_files_do_not_introduce_provider_execution_or_db_schema() -> None:
    contract_sources = [
        Path("models/async_daily_coach_narrative_models.py").read_text(
            encoding="utf-8"
        ),
        Path("services/async_daily_coach_context_identity.py").read_text(
            encoding="utf-8"
        ),
    ]
    combined = "\n".join(contract_sources)

    for forbidden in FORBIDDEN_RUNTIME_TOKENS:
        assert forbidden not in combined

    assert "CREATE TABLE daily_coach_narrative_jobs" not in combined
    assert "sqlite" not in combined.lower()
