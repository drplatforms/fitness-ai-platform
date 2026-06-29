from __future__ import annotations

import json
from pathlib import Path

from models.daily_coach_full_user_day_models import (
    DailyCoachFullUserDayDraftResult,
    DailyCoachFullUserDayPacket,
    DailyCoachFullUserDayTrialRunResult,
)
from tools import dev_daily_coach_full_user_day_free_range_trial as cli


def _fake_packet() -> DailyCoachFullUserDayPacket:
    return DailyCoachFullUserDayPacket(
        packet_version="daily_coach_free_range_voice_precision_payload_enrichment_v2",
        user_id=102,
        date="2026-06-27",
        scenario_id="aligned_managed",
        nutrition={
            "macro_targets_actuals_deltas": {
                "protein_g": {"actual": 118, "target_min": 150, "delta_min": -32}
            }
        },
        food_candidates=(
            {
                "display_name": "canned tuna",
                "plain_name_for_user": "canned tuna",
                "estimated_protein_g": 29,
                "helps_with": "protein",
            },
        ),
        training={"avg_rir": 2.4},
        recovery={"readiness_level": "Supportive"},
        do_not_infer=("Do not invent facts.",),
    )


def _fake_result() -> DailyCoachFullUserDayTrialRunResult:
    packet = _fake_packet()
    variant = DailyCoachFullUserDayDraftResult(
        scenario_id="aligned_managed",
        user_id=102,
        date="2026-06-27",
        provider="deterministic",
        model="gpt-5.5",
        variant_id="free_range_full_user_day_practical_coach",
        repeat_index=1,
        skipped=False,
        skip_reason=None,
        first_pass_draft="Train cleanly and eat canned tuna if protein is still short.",
        provider_input_prompt="Write today’s Daily Coach note.\nDATA_PACKET_JSON:\n{}",
        full_user_day_packet=packet,
        runtime_metadata={
            "prompt_character_count": 56,
            "raw_provider_envelope_persisted": False,
        },
    )
    return DailyCoachFullUserDayTrialRunResult(
        run_id="run-1",
        scenario_id="aligned_managed",
        user_id=102,
        date="2026-06-27",
        provider="deterministic",
        model="gpt-5.5",
        variants=(variant,),
        baseline_drift={"documented": True},
        runtime_metadata={"developer_only": True},
    )


def test_cli_lists_variants(capsys) -> None:
    exit_code = cli.main(["--list-variants"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "free_range_full_user_day_minimal" in captured.out
    assert "free_range_full_user_day_practical_coach" in captured.out
    assert "free_range_full_user_day_direct_coach" in captured.out
    assert "free_range_full_user_day_strict_coach" in captured.out
    assert "free_range_full_user_day_empathetic_coach" in captured.out
    assert "free_range_full_user_day_hypeman_coach" in captured.out


def test_cli_run_scenario_writes_debug_and_pasteback(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    def fake_run(**kwargs):
        assert kwargs["repeat"] == 3
        assert kwargs["write_provider_payload_debug"] is True
        assert kwargs["write_model_input_manifest"] is True
        assert kwargs["write_precision_summary"] is True
        assert kwargs["write_food_candidate_summary"] is True
        assert kwargs["write_completion_diagnostics"] is True
        assert kwargs["write_food_option_card"] is True
        assert kwargs["write_macro_display_card"] is True
        assert kwargs["write_ai_snack_candidates"] is True
        assert kwargs["write_number_formatting_summary"] is True
        assert kwargs["write_voice_style_findings"] is True
        assert kwargs["include_voice_variants"] is True
        output_dir = kwargs["output_dir"]
        result = _fake_result()
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "pasteback_report.md").write_text("pasteback", encoding="utf-8")
        (output_dir / "provider_input_prompt.md").write_text(
            "prompt debug", encoding="utf-8"
        )
        (output_dir / "first_pass_drafts_compact.md").write_text(
            "compact", encoding="utf-8"
        )
        (output_dir / "best_variant_summary.md").write_text("best", encoding="utf-8")
        (output_dir / "model_input_manifest.md").write_text(
            "manifest", encoding="utf-8"
        )
        (output_dir / "precision_usage_summary.md").write_text(
            "precision", encoding="utf-8"
        )
        (output_dir / "food_candidate_summary.md").write_text("food", encoding="utf-8")
        (output_dir / "completion_diagnostics.md").write_text(
            "completion", encoding="utf-8"
        )
        (output_dir / "food_option_card.md").write_text("food card", encoding="utf-8")
        (output_dir / "macro_display_card.md").write_text(
            "macro card", encoding="utf-8"
        )
        (output_dir / "ai_snack_candidates.md").write_text("snacks", encoding="utf-8")
        (output_dir / "number_formatting_summary.md").write_text(
            "numbers", encoding="utf-8"
        )
        (output_dir / "voice_style_findings.md").write_text("voice", encoding="utf-8")
        return result

    monkeypatch.setattr(
        cli, "run_daily_coach_full_user_day_free_range_scenario", fake_run
    )

    exit_code = cli.main(
        [
            "--run-scenario",
            "aligned_managed",
            "--repeat",
            "3",
            "--output-dir",
            str(tmp_path),
            "--write-provider-payload-debug",
            "--write-model-input-manifest",
            "--write-precision-summary",
            "--write-food-candidate-summary",
            "--write-completion-diagnostics",
            "--write-food-option-card",
            "--write-macro-display-card",
            "--write-ai-snack-candidates",
            "--write-number-formatting-summary",
            "--write-voice-style-findings",
            "--include-voice-variants",
            "--write-pasteback-report",
            "--print-first-pass",
            "--print-best-variant",
            "--print-payload-debug",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Full User-Day Free-Range Trial runs: 1" in captured.out
    assert "Provider payload debug requested: True" in captured.out
    assert "Pasteback report:" in captured.out
    assert "compact" in captured.out
    assert "best" in captured.out
    assert "prompt debug" in captured.out
    assert "manifest" in captured.out
    assert "precision" in captured.out
    assert "food" in captured.out
    assert "completion" in captured.out
    assert "food card" in captured.out
    assert "macro card" in captured.out
    assert "snacks" in captured.out
    assert "numbers" in captured.out
    assert "voice" in captured.out


def test_cli_run_matrix_json(monkeypatch, tmp_path: Path, capsys) -> None:
    def fake_matrix(**kwargs):
        assert kwargs["scenarios"] == ["rich_nutrition_training_recovery"]
        assert kwargs["write_provider_payload_debug"] is False
        assert kwargs["write_completion_diagnostics"] is False
        assert kwargs["include_voice_variants"] is False
        return [_fake_result()]

    monkeypatch.setattr(
        cli, "run_daily_coach_full_user_day_free_range_matrix", fake_matrix
    )

    exit_code = cli.main(
        [
            "--run-matrix",
            "--output-dir",
            str(tmp_path),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload[0]["scenario_id"] == "aligned_managed"
    assert payload[0]["variants"][0]["first_pass_draft"].startswith("Train cleanly")
