from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools import dev_daily_coach_human_voice_prompt_preview as tool


@dataclass(frozen=True)
class FakeResult:
    raw_model_output: str = "raw terminal coach output"
    error_type: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict:
        return {
            "result_version": "daily_coach_human_voice_prompt_preview_result_v1",
            "user_id": 102,
            "target_date": "2026-06-14",
            "model_name": "fake-model",
            "prompt_file": "docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md",
            "prompt_sha256": "abc123",
            "generated_at": "2026-07-01T00:00:00+00:00",
            "elapsed_seconds": 0.001,
            "latency_ms": 1,
            "developer_preview_only": True,
            "provider_call_was_opt_in": True,
            "persistence_allowed": False,
            "product_surface_allowed": False,
            "normal_today_surface_allowed": False,
            "payload_version": "daily_coach_provider_preview_raw_data_payload_v1",
            "source_snapshot_version": "daily_coach_intelligence_snapshot_v2",
            "raw_model_output": self.raw_model_output,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


def test_developer_tool_prints_raw_model_output_and_metadata(
    monkeypatch,
    capsys,
) -> None:
    calls = []

    def fake_runner(**kwargs):
        calls.append(kwargs)
        return FakeResult(), "provider input was built"

    monkeypatch.setattr(tool, "run_daily_coach_human_voice_prompt_preview", fake_runner)

    exit_code = tool.main(
        [
            "--user-id",
            "102",
            "--target-date",
            "2026-06-14",
            "--model",
            "fake-model",
            "--prompt-file",
            "docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls[0]["user_id"] == 102
    assert calls[0]["target_date"] == "2026-06-14"
    assert calls[0]["model_name"] == "fake-model"
    assert calls[0]["prompt_file"] == (
        "docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md"
    )
    assert calls[0]["provider_callable"] is None
    assert "=== Daily Coach Human Voice Prompt Preview ===" in captured.out
    assert "user_id: 102" in captured.out
    assert (
        "payload_version: daily_coach_provider_preview_raw_data_payload_v1"
        in captured.out
    )
    assert "developer_preview_only: True" in captured.out
    assert "persistence_allowed: False" in captured.out
    assert "product_surface_allowed: False" in captured.out
    assert "=== Raw Model Output ===" in captured.out
    assert "raw terminal coach output" in captured.out
    assert "=== Provider Input ===" not in captured.out


def test_developer_tool_can_print_provider_input_when_requested(
    monkeypatch,
    capsys,
) -> None:
    def fake_runner(**_kwargs):
        return FakeResult(), "PROMPT\n\n---\n\nRAW_BACKEND_PAYLOAD_JSON:\n{}"

    monkeypatch.setattr(tool, "run_daily_coach_human_voice_prompt_preview", fake_runner)

    exit_code = tool.main(
        [
            "--user-id",
            "102",
            "--target-date",
            "2026-06-14",
            "--model",
            "fake-model",
            "--print-provider-input",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "=== Provider Input ===" in captured.out
    assert "RAW_BACKEND_PAYLOAD_JSON" in captured.out
    assert "=== Raw Model Output ===" in captured.out


def test_developer_tool_mock_output_uses_injected_fake_provider(monkeypatch) -> None:
    calls = []

    def fake_runner(**kwargs):
        calls.append(kwargs)
        raw_output = kwargs["provider_callable"]("provider input")
        return FakeResult(raw_model_output=raw_output), "provider input"

    monkeypatch.setattr(tool, "run_daily_coach_human_voice_prompt_preview", fake_runner)

    exit_code = tool.main(
        [
            "--user-id",
            "102",
            "--target-date",
            "2026-06-14",
            "--model",
            "fake-model",
            "--mock-output",
        ]
    )

    assert exit_code == 0
    assert calls[0]["provider_callable"] is not None


def test_developer_tool_does_not_write_files_by_default(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_runner(**_kwargs):
        return FakeResult(), "provider input"

    monkeypatch.setattr(tool, "run_daily_coach_human_voice_prompt_preview", fake_runner)
    monkeypatch.chdir(tmp_path)
    before = sorted(path.name for path in tmp_path.iterdir())

    exit_code = tool.main(
        [
            "--user-id",
            "102",
            "--target-date",
            "2026-06-14",
            "--model",
            "fake-model",
        ]
    )
    after = sorted(path.name for path in tmp_path.iterdir())

    assert exit_code == 0
    assert after == before


def test_developer_tool_does_not_import_old_provider_runtime_modules() -> None:
    source = Path(tool.__file__).read_text(encoding="utf-8").lower()

    assert "crewai" not in source
    assert "openai" not in source
    assert "provider_service" not in source
    assert "daily_coach_narrative_provider_service" not in source
    assert "daily_coach_narrative_validation_service" not in source
