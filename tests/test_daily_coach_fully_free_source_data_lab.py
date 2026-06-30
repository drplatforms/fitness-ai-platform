from __future__ import annotations

import json

from services.daily_coach_fully_free_source_data_lab_service import (
    BACKEND_PROSE_PATTERNS,
    build_backend_prose_contamination_summary,
    build_fully_free_source_data_packet,
    build_fully_free_source_data_prompt,
    build_model_freedom_summaries,
    run_daily_coach_fully_free_source_data_lab_scenario,
    write_daily_coach_fully_free_source_data_lab_artifacts,
)
from tools.dev_daily_coach_fully_free_source_data_lab import main


class _FakeFullUserDayPacket:
    def to_dict(self):
        return {
            "packet_version": "test-free-range-v4",
            "user_id": 102,
            "date": "2026-06-27",
            "scenario_id": "aligned_managed",
            "user_profile": {
                "user_id": 102,
                "primary_goal": "strength",
                "latest_body_weight_display": "208 lb",
                "internal_workout_model": "debug-only",
            },
            "today_context": {"date": "2026-06-27"},
            "nutrition": {
                "macro_targets_actuals_deltas": {
                    "calories": {
                        "display": "Calories: 1,278 / 2,750–3,000",
                        "macro_gap": "debug-only",
                    },
                    "protein": {"display": "Protein: 101g / 150–200g"},
                },
                "today_food_log_summary": "Food is based on what is logged so far.",
                "confidence": "moderate",
            },
            "food_candidates": (
                {
                    "plain_name_for_user": "cooked chicken breast",
                    "serving_size": "155g",
                    "display_phrase": "Cooked chicken breast — 48g protein, 256 calories",
                    "helps_with": "protein",
                    "why_useful_today": "adds a solid protein serving",
                    "value_precision": "database_calculated",
                    "quote_style": "direct",
                },
            ),
            "ai_snack_candidates": (
                {
                    "snack_name": "Chicken breast + rice",
                    "foods_included": ["cooked chicken breast", "rice"],
                    "serving_notes": "use logged serving sizes",
                    "estimated_calories": 486.0,
                    "estimated_protein_g": 52.0,
                    "estimated_fat_g": 0.0,
                    "display_phrase": "Chicken breast + rice — 52g protein, 486 calories, 0g fat",
                },
            ),
            "macro_display_card": {
                "rows": [
                    "Calories: 1,278 / 2,750–3,000",
                    "Protein: 101g / 150–200g",
                ]
            },
            "food_option_card": {"rows": ["Cooked chicken breast — 48g protein"]},
            "training": {
                "scheduled_session_name": "Upper body strength",
                "session_type": "strength",
                "session_intensity": "moderate",
                "volume_load": 35406.0,
                "training_summary_for_coach": "Recent training workload appears high based on logged work.",
                "set_level_data_available": False,
                "set_level_data_unavailable_reason": "no actual sets logged yet",
            },
            "recovery": {
                "readiness_interpretation": "Recovery looks strong enough for controlled training.",
                "recovery_score_display": "82 / 100",
                "weight_trend_display": "large recent change not surfaced to coach",
            },
            "do_not_infer": ("Do not assume the workout was completed.",),
        }


def _patch_scenario(monkeypatch):
    monkeypatch.setattr(
        "services.daily_coach_fully_free_source_data_lab_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_fully_free_source_data_lab_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: _FakeFullUserDayPacket(),
    )


def test_fully_free_lab_tool_exists_and_lists_variants(capsys):
    assert main(["--list-variants"]) == 0
    captured = capsys.readouterr()
    assert "fully_free_minimal" in captured.out
    assert "fully_free_no_structure" in captured.out


def test_source_data_packet_is_written_without_backend_coach_prose(
    tmp_path, monkeypatch
):
    _patch_scenario(monkeypatch)
    result = run_daily_coach_fully_free_source_data_lab_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["fully_free_minimal"],
        output_dir=tmp_path,
        write_source_data_packet=True,
        write_source_data_completeness_summary=True,
        write_model_freedom_summary=True,
        write_backend_prose_contamination_summary=True,
        write_completion_diagnostics=True,
        write_pasteback_report=True,
    )

    assert result.variants[0].skipped is False
    assert (tmp_path / "fully_free_source_data_packet.json").exists()
    assert (tmp_path / "fully_free_source_data_packet.md").exists()
    assert (tmp_path / "source_data_completeness_summary.json").exists()
    assert (tmp_path / "model_freedom_summary.json").exists()
    assert (tmp_path / "backend_prose_contamination_summary.json").exists()
    assert (tmp_path / "completion_diagnostics.json").exists()
    assert (tmp_path / "pasteback_report.md").exists()

    packet_text = (
        (tmp_path / "fully_free_source_data_packet.md")
        .read_text(encoding="utf-8")
        .lower()
    )
    assert "main lever" not in packet_text
    assert "approved option" not in packet_text
    assert "macro_gap" not in packet_text
    assert "volume_load" not in packet_text
    assert "quote_style" not in packet_text


def test_minimal_prompt_allows_model_to_choose_without_renderer(monkeypatch):
    _patch_scenario(monkeypatch)
    source_packet = build_fully_free_source_data_packet(
        user_id=102, target_date="2026-06-27", scenario_id="aligned_managed"
    )
    prompt = build_fully_free_source_data_prompt(source_packet, "fully_free_minimal")

    assert "Choose what matters most" in prompt
    assert "SOURCE_DATA_JSON" in prompt
    assert "approved option" not in prompt
    assert "planned workout as written" not in prompt
    assert "phrase ban" not in prompt.lower()
    assert "###" not in prompt
    assert len(prompt) < 15000


def test_model_freedom_summary_reports_fully_free_expectations(tmp_path, monkeypatch):
    _patch_scenario(monkeypatch)
    result = run_daily_coach_fully_free_source_data_lab_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["fully_free_no_structure"],
        output_dir=tmp_path,
        write_model_freedom_summary=True,
    )
    summary = build_model_freedom_summaries([result])
    record = summary["records"][0]

    assert record["phrase_bans_included"] is False
    assert record["deterministic_coach_prose_included"] is False
    assert record["renderer_structure_included"] is False
    assert record["output_structure_forced"] is False
    assert record["model_can_choose_what_matters"] is True


def test_backend_prose_contamination_audit_does_not_mutate_first_pass(monkeypatch):
    _patch_scenario(monkeypatch)
    result = run_daily_coach_fully_free_source_data_lab_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["fully_free_direct"],
    )
    first_pass_before = result.variants[0].first_pass_draft
    summary = build_backend_prose_contamination_summary([result])

    assert summary["records"][0]["mutated_first_pass"] is False
    assert result.variants[0].first_pass_draft == first_pass_before
    assert set(BACKEND_PROSE_PATTERNS).issuperset(summary["patterns"])


def test_openai_requires_live_provider_permission(monkeypatch):
    _patch_scenario(monkeypatch)
    result = run_daily_coach_fully_free_source_data_lab_scenario(
        scenario_id="aligned_managed",
        provider="openai",
        variants=["fully_free_minimal"],
        allow_live_provider=False,
    )

    assert result.variants[0].skipped is True
    assert result.variants[0].skip_reason == "live_provider_not_allowed"


def test_deterministic_provider_runs_without_live_provider_permission(monkeypatch):
    _patch_scenario(monkeypatch)
    result = run_daily_coach_fully_free_source_data_lab_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["fully_free_minimal"],
        allow_live_provider=False,
        environ={"DAILY_COACH_FULLY_FREE_PROVIDER": "openai"},
    )

    assert result.variants[0].skipped is False
    assert result.variants[0].provider == "deterministic"
    assert "Today" in result.variants[0].first_pass_draft


def test_required_artifacts_and_safety_outputs_are_written(tmp_path, monkeypatch):
    _patch_scenario(monkeypatch)
    result = run_daily_coach_fully_free_source_data_lab_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["fully_free_energy"],
        repeat=2,
    )
    write_daily_coach_fully_free_source_data_lab_artifacts(
        tmp_path,
        [result],
        write_provider_payload_debug=True,
        write_source_data_packet=True,
        write_source_data_completeness_summary=True,
        write_model_freedom_summary=True,
        write_backend_prose_contamination_summary=True,
        write_completion_diagnostics=True,
        write_pasteback_report=True,
    )

    expected = {
        "run_config.json",
        "provider_input_prompt.md",
        "provider_payload_debug.json",
        "fully_free_source_data_packet.json",
        "fully_free_source_data_packet.md",
        "source_data_completeness_summary.md",
        "source_data_completeness_summary.json",
        "model_freedom_summary.md",
        "model_freedom_summary.json",
        "backend_prose_contamination_summary.md",
        "backend_prose_contamination_summary.json",
        "completion_diagnostics.md",
        "completion_diagnostics.json",
        "first_pass_drafts.md",
        "first_pass_drafts_compact.md",
        "side_by_side_comparison.md",
        "best_variant_summary.md",
        "claim_risk_summary.md",
        "consistency_summary.md",
        "token_cost_telemetry.md",
        "token_cost_telemetry.csv",
        "artifact_safety_summary.md",
        "pasteback_report.md",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})
    safety = (tmp_path / "artifact_safety_summary.md").read_text(encoding="utf-8")
    debug = json.loads((tmp_path / "provider_payload_debug.json").read_text())
    completion = json.loads((tmp_path / "completion_diagnostics.json").read_text())

    assert "Raw provider envelopes are not persisted" in safety
    assert debug["records"][0]["raw_provider_envelope_persisted"] is False
    assert debug["records"][0]["secrets_persisted"] is False
    assert completion["summary"]["expected_drafts"] == 2
    assert completion["summary"]["captured_drafts"] == 2
