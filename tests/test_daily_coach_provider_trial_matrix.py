from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from tools.run_daily_coach_provider_trial_matrix import (
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
    parse_model_overrides,
    run_trial_matrix,
)


@dataclass
class FakeNarrative:
    source: str = "deterministic"
    quoted_values_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "headline": "Daily Coach",
            "summary": "Recovery context is available and today supports steady execution.",
            "nutrition_note": "Keep nutrition logging complete enough for useful context.",
            "training_note": "No workout has been started today.",
            "recovery_note": "Recovery readiness is High and fatigue risk is Low.",
            "priority_action": "Use the approved plan and keep logging clean.",
            "confidence": "High",
            "source": self.source,
            "reason_codes": ["unit_test"],
            "limitations": [],
            "quoted_values_used": list(self.quoted_values_used),
        }


@dataclass
class FakeMetadata:
    selected_provider: str = "deterministic"
    selected_model: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
    final_narrative_source: str = "deterministic"
    candidate_parse_status: str = "not_attempted"
    validation_status: str = "not_attempted"
    validation_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "configured_provider": self.selected_provider,
            "selected_provider": self.selected_provider,
            "configured_model": self.selected_model,
            "selected_model": self.selected_model,
            "provider_attempted": self.selected_provider != "deterministic",
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "candidate_parse_status": self.candidate_parse_status,
            "candidate_validation_status": "not_attempted",
            "validation_status": self.validation_status,
            "final_narrative_source": self.final_narrative_source,
            "raw_output_length": None,
            "raw_output_preview_truncated": None,
            "markdown_wrapper_detected": False,
            "validation_errors": list(self.validation_errors),
        }


class FakeResult:
    def __init__(
        self,
        *,
        user_id: int = 102,
        provider: str = "deterministic",
        fallback: bool = False,
        fallback_reason: str | None = None,
        selected_model: str | None = None,
        raw_provider_output: str | None = None,
    ) -> None:
        source = "deterministic_fallback" if fallback else provider
        self.user_id = user_id
        self.narrative = FakeNarrative(
            source=source,
            quoted_values_used=["recovery.readiness_level", "recovery.fatigue_risk"],
        )
        self.raw_provider_output = raw_provider_output
        self.metadata = FakeMetadata(
            selected_provider=provider,
            selected_model=selected_model,
            fallback_used=fallback,
            fallback_reason=fallback_reason,
            final_narrative_source=source,
            candidate_parse_status=(
                "success" if provider != "deterministic" else "not_attempted"
            ),
            validation_status="approved" if not fallback else "rejected",
            validation_errors=["quote validation failed"] if fallback else [],
        )

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "success": True,
            "user_id": self.user_id,
            "narrative_date": "2026-06-27",
            "approved_daily_coach_narrative": self.narrative.to_dict(),
            "rendered_narrative": "## Daily Coach\nRecovery readiness is High.",
        }

    def to_debug_dict(self) -> dict[str, Any]:
        payload = self.to_public_dict()
        payload["runtime_metadata"] = self.metadata.to_dict()
        payload["provider_context_summary"] = {"approved_value_claim_count": 2}
        if self.raw_provider_output is not None:
            payload["raw_provider_output"] = self.raw_provider_output
        return payload


def _fake_builder(user_id: int, target_date: str | None = None) -> FakeResult:
    return FakeResult(user_id=user_id)


def test_trial_matrix_can_run_deterministic_provider_only(tmp_path: Path) -> None:
    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DETERMINISTIC],
        output_dir=tmp_path,
        narrative_builder=_fake_builder,
    )

    assert len(rows) == 1
    row = rows[0]
    assert row.user_id == 102
    assert row.provider == PROVIDER_DETERMINISTIC
    assert row.success is True
    assert row.skipped is False
    assert row.case_label == "aligned_managed_recovery_truth_regression"
    assert row.approved_daily_coach_narrative is not None
    assert row.rendered_narrative is not None
    assert (tmp_path / "trial_matrix.jsonl").exists()
    assert (tmp_path / "trial_matrix_summary.md").exists()
    assert (tmp_path / "selected_outputs.md").exists()


def test_live_provider_skips_without_allow_live_providers(tmp_path: Path) -> None:
    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DETERMINISTIC, PROVIDER_DIRECT_OLLAMA, PROVIDER_OPENAI],
        output_dir=tmp_path,
        narrative_builder=_fake_builder,
        allow_live_providers=False,
    )

    assert [row.provider for row in rows] == [
        PROVIDER_DETERMINISTIC,
        PROVIDER_DIRECT_OLLAMA,
        PROVIDER_OPENAI,
    ]
    assert rows[0].skipped is False
    assert rows[1].skipped is True
    assert rows[1].skip_reason == "live_provider_not_allowed"
    assert rows[2].skipped is True
    assert rows[2].skip_reason == "live_provider_not_allowed"


def test_trial_matrix_records_skipped_provider_cases_cleanly(tmp_path: Path) -> None:
    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_OPENAI],
        output_dir=tmp_path,
        narrative_builder=_fake_builder,
        allow_live_providers=True,
        environ={},
    )

    assert rows[0].skipped is True
    assert rows[0].skip_reason == "missing_api_key"
    assert rows[0].provider_error_type == "missing_api_key"
    assert rows[0].success is False
    assert rows[0].approved_daily_coach_narrative is None


def test_trial_matrix_records_fallback_metadata(tmp_path: Path) -> None:
    def builder(user_id: int, target_date: str | None = None) -> FakeResult:
        return FakeResult(
            user_id=user_id,
            provider="openai",
            fallback=True,
            fallback_reason="candidate_validation_failure",
            selected_model="gpt-test",
        )

    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_OPENAI],
        output_dir=tmp_path,
        narrative_builder=builder,
        allow_live_providers=True,
        environ={"OPENAI_API_KEY": "test-secret"},
        model_overrides={PROVIDER_OPENAI: "gpt-test"},
    )

    assert rows[0].skipped is False
    assert rows[0].runtime_metadata["fallback_used"] is True
    assert rows[0].runtime_metadata["fallback_reason"] == "candidate_validation_failure"
    assert rows[0].runtime_metadata["validation_errors"] == ["quote validation failed"]


def test_trial_matrix_writes_jsonl_output(tmp_path: Path) -> None:
    run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DETERMINISTIC],
        output_dir=tmp_path,
        narrative_builder=_fake_builder,
    )

    lines = (tmp_path / "trial_matrix.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["user_id"] == 102
    assert payload["date"] == "2026-06-27"
    assert payload["provider"] == PROVIDER_DETERMINISTIC
    assert payload["model"] == ""


def test_trial_matrix_writes_markdown_summary(tmp_path: Path) -> None:
    run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DETERMINISTIC],
        output_dir=tmp_path,
        narrative_builder=_fake_builder,
    )

    summary = (tmp_path / "trial_matrix_summary.md").read_text(encoding="utf-8")
    assert "Daily Coach Narrative Provider Trial Matrix v1" in summary
    assert "Schema adherence" in summary
    assert "Should deterministic remain default? Expected answer: yes." in summary


def test_trial_matrix_includes_user_date_provider_model_fields(tmp_path: Path) -> None:
    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_OPENAI],
        output_dir=tmp_path,
        narrative_builder=lambda user_id, target_date=None: FakeResult(
            user_id=user_id,
            provider="openai",
            selected_model="gpt-test",
        ),
        allow_live_providers=True,
        environ={"OPENAI_API_KEY": "test-secret"},
        model_overrides={PROVIDER_OPENAI: "gpt-test"},
    )

    row = rows[0]
    assert row.user_id == 102
    assert row.date == "2026-06-27"
    assert row.provider == PROVIDER_OPENAI
    assert row.model == "gpt-test"


def test_trial_matrix_does_not_write_raw_provider_output_or_api_keys(
    tmp_path: Path,
) -> None:
    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_OPENAI],
        output_dir=tmp_path,
        narrative_builder=lambda user_id, target_date=None: FakeResult(
            user_id=user_id,
            provider="openai",
            selected_model="gpt-test",
        ),
        allow_live_providers=True,
        environ={"OPENAI_API_KEY": "test-secret"},
        model_overrides={PROVIDER_OPENAI: "gpt-test"},
    )

    combined = json.dumps([row.to_dict() for row in rows]).lower()
    combined += (tmp_path / "trial_matrix.jsonl").read_text(encoding="utf-8").lower()
    combined += (
        (tmp_path / "trial_matrix_summary.md").read_text(encoding="utf-8").lower()
    )
    combined += (tmp_path / "selected_outputs.md").read_text(encoding="utf-8").lower()
    assert "raw_provider_output" not in combined
    assert "test-secret" not in combined


def test_trial_matrix_handles_unavailable_user_date_without_crashing(
    tmp_path: Path,
) -> None:
    def builder(user_id: int, target_date: str | None = None) -> FakeResult:
        raise RuntimeError("no data for requested user/date")

    rows = run_trial_matrix(
        users=[999],
        trial_date="2026-06-27",
        providers=[PROVIDER_DETERMINISTIC],
        output_dir=tmp_path,
        narrative_builder=builder,
    )

    assert rows[0].skipped is True
    assert rows[0].skip_reason is not None
    assert "case_unavailable_or_builder_error" in rows[0].skip_reason


def test_trial_matrix_includes_required_user_102_regression_case_when_requested(
    tmp_path: Path,
) -> None:
    rows = run_trial_matrix(
        users=[101, 102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DETERMINISTIC],
        output_dir=tmp_path,
        narrative_builder=_fake_builder,
    )

    assert any(
        row.user_id == 102
        and row.date == "2026-06-27"
        and row.case_label == "aligned_managed_recovery_truth_regression"
        for row in rows
    )


def test_trial_matrix_preserves_deterministic_default(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("DAILY_COACH_NARRATIVE_PROVIDER", raising=False)
    run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DETERMINISTIC],
        output_dir=tmp_path,
        narrative_builder=_fake_builder,
    )

    assert "DAILY_COACH_NARRATIVE_PROVIDER" not in __import__("os").environ


def test_model_overrides_require_provider_model_shape() -> None:
    assert parse_model_overrides(["openai=gpt-test"]) == {"openai": "gpt-test"}
    with pytest.raises(ValueError):
        parse_model_overrides(["gpt-test"])


def test_raw_provider_output_diagnostic_mode_is_off_by_default(tmp_path: Path) -> None:
    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DETERMINISTIC],
        output_dir=tmp_path,
        narrative_builder=lambda user_id, target_date=None: FakeResult(
            user_id=user_id,
            raw_provider_output="SECRET RAW MODEL TEXT",
        ),
    )

    assert rows[0].diagnostic_mode_enabled is False
    assert rows[0].raw_output_saved_local_path is None
    assert not list(tmp_path.glob("*raw_provider_output*"))


def test_raw_provider_output_written_only_when_explicitly_enabled(
    tmp_path: Path,
) -> None:
    raw_dir = tmp_path / "raw"
    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DETERMINISTIC],
        output_dir=tmp_path / "artifacts",
        narrative_builder=lambda user_id, target_date=None: FakeResult(
            user_id=user_id,
            raw_provider_output="SECRET RAW MODEL TEXT",
        ),
        diagnostic_raw_output=True,
        raw_output_dir=raw_dir,
    )

    raw_path = rows[0].raw_output_saved_local_path
    assert raw_path is not None
    raw_text = Path(raw_path).read_text(encoding="utf-8")
    assert "QA RAW PROVIDER OUTPUT / DO NOT COMMIT" in raw_text
    assert "SECRET RAW MODEL TEXT" in raw_text

    normal_artifacts = "\n".join(
        [
            (tmp_path / "artifacts" / "trial_matrix.jsonl").read_text(encoding="utf-8"),
            (tmp_path / "artifacts" / "trial_matrix_summary.md").read_text(
                encoding="utf-8"
            ),
            (tmp_path / "artifacts" / "selected_outputs.md").read_text(
                encoding="utf-8"
            ),
        ]
    )
    assert "SECRET RAW MODEL TEXT" not in normal_artifacts
    assert rows[0].diagnostic_mode_enabled is True


def test_missing_openai_key_is_classified_as_missing_api_key(tmp_path: Path) -> None:
    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_OPENAI],
        output_dir=tmp_path,
        narrative_builder=_fake_builder,
        allow_live_providers=True,
        environ={},
    )

    assert rows[0].skipped is True
    assert rows[0].skip_reason == "missing_api_key"
    assert rows[0].provider_error_type == "missing_api_key"
    assert rows[0].api_key_present is False


def test_openai_auth_error_is_classified_distinctly(tmp_path: Path) -> None:
    def builder(user_id: int, target_date: str | None = None) -> FakeResult:
        return FakeResult(
            user_id=user_id,
            provider="openai",
            fallback=True,
            fallback_reason="openai_auth_error",
            selected_model="gpt-test",
        )

    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_OPENAI],
        output_dir=tmp_path,
        narrative_builder=builder,
        allow_live_providers=True,
        environ={"OPENAI_API_KEY": "test-secret"},
        model_overrides={PROVIDER_OPENAI: "gpt-test"},
    )

    assert rows[0].provider_error_type == "invalid_api_key_or_auth_failed"


def test_openai_timeout_is_classified_distinctly(tmp_path: Path) -> None:
    def builder(user_id: int, target_date: str | None = None) -> FakeResult:
        return FakeResult(
            user_id=user_id,
            provider="openai",
            fallback=True,
            fallback_reason="openai_timeout",
            selected_model="gpt-test",
        )

    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_OPENAI],
        output_dir=tmp_path,
        narrative_builder=builder,
        allow_live_providers=True,
        environ={"OPENAI_API_KEY": "test-secret"},
        model_overrides={PROVIDER_OPENAI: "gpt-test"},
    )

    assert rows[0].provider_error_type == "timeout"


def test_openai_model_not_found_is_classified_distinctly(tmp_path: Path) -> None:
    def builder(user_id: int, target_date: str | None = None) -> FakeResult:
        return FakeResult(
            user_id=user_id,
            provider="openai",
            fallback=True,
            fallback_reason="openai_model_not_found",
            selected_model="gpt-test",
        )

    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_OPENAI],
        output_dir=tmp_path,
        narrative_builder=builder,
        allow_live_providers=True,
        environ={"OPENAI_API_KEY": "test-secret"},
        model_overrides={PROVIDER_OPENAI: "gpt-test"},
    )

    assert rows[0].provider_error_type == "model_not_found"


def test_malformed_response_is_classified_distinctly(tmp_path: Path) -> None:
    def builder(user_id: int, target_date: str | None = None) -> FakeResult:
        return FakeResult(
            user_id=user_id,
            provider="openai",
            fallback=True,
            fallback_reason="openai_malformed_response",
            selected_model="gpt-test",
        )

    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_OPENAI],
        output_dir=tmp_path,
        narrative_builder=builder,
        allow_live_providers=True,
        environ={"OPENAI_API_KEY": "test-secret"},
        model_overrides={PROVIDER_OPENAI: "gpt-test"},
    )

    assert rows[0].provider_error_type == "malformed_response"


def test_quote_validation_failure_remains_classified(tmp_path: Path) -> None:
    def builder(user_id: int, target_date: str | None = None) -> FakeResult:
        return FakeResult(
            user_id=user_id,
            provider="direct_ollama",
            fallback=True,
            fallback_reason="candidate_validation_failure",
            selected_model="ollama/qwen2.5:3b",
        )

    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DIRECT_OLLAMA],
        output_dir=tmp_path,
        narrative_builder=builder,
        allow_live_providers=True,
        environ={"OLLAMA_BASE_URL": "http://localhost:11434"},
        model_overrides={PROVIDER_DIRECT_OLLAMA: "ollama/qwen2.5:3b"},
    )

    assert rows[0].provider_error_type == "quote_validation_failed"


def test_ollama_cleanup_can_be_requested_without_crashing(tmp_path: Path) -> None:
    cleanup_calls: list[tuple[str, str | None]] = []

    def cleanup(
        model: str, env: dict[str, str], keep_alive: str | None
    ) -> dict[str, Any]:
        cleanup_calls.append((model, keep_alive))
        return {
            "ollama_cleanup_attempted": True,
            "ollama_cleanup_success": True,
            "ollama_cleanup_error": None,
        }

    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DIRECT_OLLAMA],
        output_dir=tmp_path,
        narrative_builder=lambda user_id, target_date=None: FakeResult(
            user_id=user_id,
            provider="direct_ollama",
            selected_model="ollama/qwen2.5:3b",
        ),
        allow_live_providers=True,
        environ={"OLLAMA_BASE_URL": "http://localhost:11434"},
        model_overrides={PROVIDER_DIRECT_OLLAMA: "ollama/qwen2.5:3b"},
        ollama_unload_after_run=True,
        ollama_keep_alive="0",
        ollama_cleanup=cleanup,
    )

    assert cleanup_calls == [("ollama/qwen2.5:3b", "0")]
    assert rows[0].ollama_cleanup_status["ollama_cleanup_success"] is True


def test_ollama_cleanup_failure_records_safe_metadata(tmp_path: Path) -> None:
    def cleanup(
        model: str, env: dict[str, str], keep_alive: str | None
    ) -> dict[str, Any]:
        return {
            "ollama_cleanup_attempted": True,
            "ollama_cleanup_success": False,
            "ollama_cleanup_error": "connection_error",
        }

    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DIRECT_OLLAMA],
        output_dir=tmp_path,
        narrative_builder=lambda user_id, target_date=None: FakeResult(
            user_id=user_id,
            provider="direct_ollama",
            selected_model="ollama/qwen2.5:3b",
        ),
        allow_live_providers=True,
        environ={"OLLAMA_BASE_URL": "http://localhost:11434"},
        model_overrides={PROVIDER_DIRECT_OLLAMA: "ollama/qwen2.5:3b"},
        ollama_unload_after_run=True,
        ollama_cleanup=cleanup,
    )

    assert rows[0].success is True
    assert rows[0].ollama_cleanup_status["ollama_cleanup_success"] is False
    assert rows[0].ollama_cleanup_status["ollama_cleanup_error"] == "connection_error"


class FakeEnrichedResult(FakeResult):
    def to_debug_dict(self) -> dict[str, Any]:
        payload = super().to_debug_dict()
        payload["provider_context_summary"] = {
            "approved_value_claim_count": 4,
            "high_value_claims_available": [
                "recovery.readiness_level",
                "recovery.fatigue_risk",
                "training.rir_range",
            ],
            "preferred_claims_by_field": {
                "recovery_note": [
                    "recovery.readiness_level",
                    "recovery.fatigue_risk",
                ],
                "training_note": ["training.rir_range"],
            },
        }
        return payload


def test_trial_matrix_includes_copy_grounding_review_fields(tmp_path: Path) -> None:
    rows = run_trial_matrix(
        users=[102],
        trial_date="2026-06-27",
        providers=[PROVIDER_DETERMINISTIC],
        output_dir=tmp_path,
        narrative_builder=lambda user_id, target_date=None: FakeEnrichedResult(
            user_id=user_id
        ),
    )

    row = rows[0]
    assert row.high_value_claims_available == [
        "recovery.readiness_level",
        "recovery.fatigue_risk",
        "training.rir_range",
    ]
    assert row.high_value_claims_used == [
        "recovery.readiness_level",
        "recovery.fatigue_risk",
    ]
    assert row.preferred_claims_by_field_used == {
        "recovery_note": [
            "recovery.readiness_level",
            "recovery.fatigue_risk",
        ]
    }
    assert row.declared_claim_count == 2
    payload = json.loads((tmp_path / "trial_matrix.jsonl").read_text().splitlines()[0])
    assert payload["declared_claim_count"] == 2
    summary = (tmp_path / "trial_matrix_summary.md").read_text(encoding="utf-8")
    assert "high_value_claims_used" in summary
    assert "specificity_score" in summary
