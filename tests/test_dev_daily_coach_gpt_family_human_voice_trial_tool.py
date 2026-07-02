from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools import dev_daily_coach_gpt_family_human_voice_trial as tool


@dataclass(frozen=True)
class FakeResult:
    model_name: str
    raw_model_output: str
    error_type: str | None = None
    error_message: str | None = None
    provider_name: str = "openai"
    elapsed_seconds: float = 0.123
    latency_ms: int = 123
    prompt_sha256: str = "abc123"
    payload_version: str = "daily_coach_provider_preview_raw_data_payload_v1"
    source_snapshot_version: str = "daily_coach_intelligence_snapshot_v2"

    def to_dict(self) -> dict:
        return {
            "result_version": "daily_coach_human_voice_prompt_preview_result_v1",
            "user_id": 102,
            "target_date": "2026-06-14",
            "model_name": self.model_name,
            "provider_name": self.provider_name,
            "prompt_file": "docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md",
            "prompt_sha256": self.prompt_sha256,
            "generated_at": "2026-07-01T00:00:00+00:00",
            "elapsed_seconds": self.elapsed_seconds,
            "latency_ms": self.latency_ms,
            "developer_preview_only": True,
            "provider_call_was_opt_in": True,
            "persistence_allowed": False,
            "product_surface_allowed": False,
            "normal_today_surface_allowed": False,
            "payload_version": self.payload_version,
            "source_snapshot_version": self.source_snapshot_version,
            "raw_model_output": self.raw_model_output,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


def test_parse_model_ids_supports_comma_separated_models() -> None:
    assert tool.parse_model_ids("gpt-5.4-mini, gpt-5.4,gpt-5.5") == [
        "gpt-5.4-mini",
        "gpt-5.4",
        "gpt-5.5",
    ]


def test_trial_tool_continues_after_one_model_fails(monkeypatch, capsys) -> None:
    calls = []

    def fake_runner(**kwargs):
        calls.append(kwargs)
        model_name = kwargs["model_name"]
        if model_name == "bad-model":
            return (
                FakeResult(
                    model_name=model_name,
                    raw_model_output="",
                    error_type="RuntimeError",
                    error_message="model unavailable",
                ),
                "provider input",
            )
        return (
            FakeResult(
                model_name=model_name,
                raw_model_output=f"raw output from {model_name}",
            ),
            "provider input",
        )

    monkeypatch.setattr(
        tool,
        "run_openai_daily_coach_human_voice_prompt_preview",
        fake_runner,
    )

    exit_code = tool.main(
        [
            "--user-id",
            "102",
            "--target-date",
            "2026-06-14",
            "--models",
            "good-model,bad-model,second-good-model",
            "--prompt-file",
            "docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert [call["model_name"] for call in calls] == [
        "good-model",
        "bad-model",
        "second-good-model",
    ]
    assert "=== Model: good-model ===" in captured.out
    assert "raw output from good-model" in captured.out
    assert "=== Model: bad-model ===" in captured.out
    assert "status: failed" in captured.out
    assert "model unavailable" in captured.out
    assert "=== Model: second-good-model ===" in captured.out
    assert "=== Trial Summary ===" in captured.out


def test_trial_tool_prints_raw_model_output_by_model(monkeypatch, capsys) -> None:
    def fake_runner(**kwargs):
        model_name = kwargs["model_name"]
        return (
            FakeResult(model_name=model_name, raw_model_output=f"RAW {model_name}"),
            "input",
        )

    monkeypatch.setattr(
        tool,
        "run_openai_daily_coach_human_voice_prompt_preview",
        fake_runner,
    )

    tool.main(
        [
            "--user-id",
            "102",
            "--target-date",
            "2026-06-14",
            "--models",
            "gpt-a,gpt-b",
        ]
    )
    captured = capsys.readouterr()

    assert "=== Model: gpt-a ===" in captured.out
    assert "RAW gpt-a" in captured.out
    assert "=== Model: gpt-b ===" in captured.out
    assert "RAW gpt-b" in captured.out


def test_trial_tool_does_not_write_files_by_default(
    monkeypatch, tmp_path: Path
) -> None:
    def fake_runner(**kwargs):
        return (
            FakeResult(model_name=kwargs["model_name"], raw_model_output="raw"),
            "input",
        )

    monkeypatch.setattr(
        tool,
        "run_openai_daily_coach_human_voice_prompt_preview",
        fake_runner,
    )
    monkeypatch.chdir(tmp_path)
    before = sorted(path.name for path in tmp_path.iterdir())

    exit_code = tool.main(
        [
            "--user-id",
            "102",
            "--target-date",
            "2026-06-14",
            "--models",
            "gpt-a,gpt-b",
        ]
    )

    assert exit_code == 0
    assert sorted(path.name for path in tmp_path.iterdir()) == before


def test_trial_tool_writes_artifacts_only_when_output_dir_is_passed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_runner(**kwargs):
        return (
            FakeResult(
                model_name=kwargs["model_name"],
                raw_model_output=f"raw {kwargs['model_name']}",
            ),
            "provider input without secret",
        )

    monkeypatch.setattr(
        tool,
        "run_openai_daily_coach_human_voice_prompt_preview",
        fake_runner,
    )
    output_dir = tmp_path / "qa-runs" / "trial"

    exit_code = tool.main(
        [
            "--user-id",
            "102",
            "--target-date",
            "2026-06-14",
            "--models",
            "gpt-a,gpt-b",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert (output_dir / "run_config.json").exists()
    assert (output_dir / "provider_input_102_2026-06-14.txt").exists()
    assert (output_dir / "raw_output_gpt-a.txt").exists()
    assert (output_dir / "raw_output_gpt-b.txt").exists()
    assert (output_dir / "trial_summary.json").exists()
    assert (output_dir / "trial_summary.md").exists()


def test_trial_artifacts_do_not_include_api_key(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")

    def fake_runner(**kwargs):
        return (
            FakeResult(model_name=kwargs["model_name"], raw_model_output="raw"),
            "input",
        )

    monkeypatch.setattr(
        tool,
        "run_openai_daily_coach_human_voice_prompt_preview",
        fake_runner,
    )
    output_dir = tmp_path / "artifacts"

    tool.main(
        [
            "--user-id",
            "102",
            "--target-date",
            "2026-06-14",
            "--models",
            "gpt-a",
            "--output-dir",
            str(output_dir),
        ]
    )

    artifact_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in output_dir.iterdir()
        if path.is_file()
    )
    assert "sk-test-secret" not in artifact_text


def test_trial_tool_mock_output_uses_injected_fake_provider(
    monkeypatch,
    capsys,
) -> None:
    calls = []

    def fake_runner(**kwargs):
        calls.append(kwargs)
        raw_output = kwargs["provider_callable"]("provider input")
        return (
            FakeResult(model_name=kwargs["model_name"], raw_model_output=raw_output),
            "input",
        )

    monkeypatch.setattr(
        tool,
        "run_openai_daily_coach_human_voice_prompt_preview",
        fake_runner,
    )

    exit_code = tool.main(
        [
            "--user-id",
            "102",
            "--target-date",
            "2026-06-14",
            "--models",
            "fake-gpt-a,fake-gpt-b",
            "--prompt-file",
            "docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md",
            "--mock-output",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert all(call["provider_callable"] is not None for call in calls)
    assert "fake-gpt-a" in captured.out
    assert "fake-gpt-b" in captured.out
    assert "MOCK RAW MODEL OUTPUT" in captured.out
