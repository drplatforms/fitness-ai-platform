from __future__ import annotations

from pathlib import Path

from models.daily_coach_natural_draft_audit_models import NaturalCoachDraft
from services.daily_coach_approved_brief_service import build_approved_coach_brief
from services.daily_coach_natural_draft_audit_service import (
    list_daily_coach_natural_draft_scenarios,
    run_daily_coach_natural_draft_audit_matrix,
    run_daily_coach_natural_draft_audit_scenario,
)
from tests.test_daily_coach_approved_brief_service import FakeSynthesis, _value_context


def _brief():
    return build_approved_coach_brief(
        user_id=102,
        target_date="2026-06-05",
        scenario_id="rich_nutrition_training_recovery",
        synthesis=FakeSynthesis(),
        value_context=_value_context(),
    )


def test_natural_draft_scenario_registry_reuses_required_cases() -> None:
    scenario_ids = {
        scenario["scenario_id"]
        for scenario in list_daily_coach_natural_draft_scenarios()
    }

    assert {
        "rich_nutrition_training_recovery",
        "stable_comparison",
        "training_present_nutrition_missing",
        "nutrition_present_training_missing",
    } <= scenario_ids


def test_natural_draft_audit_approves_valid_deterministic_copy(tmp_path: Path) -> None:
    result = run_daily_coach_natural_draft_audit_scenario(
        scenario_id="rich_nutrition_training_recovery",
        provider="deterministic",
        output_dir=tmp_path,
        brief=_brief(),
        draft=NaturalCoachDraft(
            headline="Train Clean + Handle Protein",
            body=(
                "Recovery looks good enough to train as planned. "
                "Keep a couple reps in reserve. Protein is below target. "
                "Eat some canned tuna if protein is still short."
            ),
        ),
    )

    assert result.audit_result.passed is True
    assert result.repair_result.attempted is False
    assert result.final_source == "draft_approved"
    assert result.product_voice_audit_result is not None
    assert result.product_voice_audit_result.passed is True
    assert (tmp_path / "run_config.json").exists()
    assert (tmp_path / "approved_coach_brief_summary.md").exists()
    assert (tmp_path / "first_pass_model_draft_before_audit.md").exists()
    assert (tmp_path / "natural_draft_output.md").exists()
    assert (tmp_path / "claim_extraction_summary.json").exists()
    assert (tmp_path / "claim_audit_summary.md").exists()
    assert (tmp_path / "product_voice_audit_summary.md").exists()
    assert (tmp_path / "repair_summary.md").exists()
    assert (tmp_path / "repair_delta_summary.md").exists()
    assert (tmp_path / "humanized_fallback_summary.md").exists()
    assert (tmp_path / "side_by_side_output_comparison.md").exists()
    assert (tmp_path / "reviewer_conclusion.md").exists()
    assert (tmp_path / "final_approved_copy.md").exists()
    assert (tmp_path / "comparison_table.csv").exists()
    assert (tmp_path / "comparison_table.md").exists()
    assert (tmp_path / "validation_summary.md").exists()
    assert (tmp_path / "scoring_template.md").exists()
    combined = "\n".join(
        path.read_text() for path in tmp_path.iterdir() if path.is_file()
    )
    assert "raw_provider_output" not in combined
    assert "api_key" not in combined.lower()
    assert "bearer " not in combined.lower()


def test_natural_draft_audit_repairs_once_then_approves(tmp_path: Path) -> None:
    result = run_daily_coach_natural_draft_audit_scenario(
        scenario_id="rich_nutrition_training_recovery",
        provider="deterministic",
        output_dir=tmp_path,
        brief=_brief(),
        draft=NaturalCoachDraft(
            headline="Dustin, Daily Coach",
            body="Add Tuna, Canned in Water if protein is still short.",
        ),
    )

    assert result.audit_result.passed is False
    assert result.repair_result.attempted is True
    assert result.repair_result.passed is True
    assert result.final_source == "repair_approved"
    assert result.final_copy is not None
    assert "Dustin" not in result.final_copy.body
    assert "Tuna, Canned in Water" not in result.final_copy.body
    assert "eat some canned tuna" in result.final_copy.body.lower()
    assert result.repaired_product_voice_audit_result is not None
    assert result.repaired_product_voice_audit_result.passed is True


def test_natural_draft_audit_falls_back_after_nonrepairable_claim() -> None:
    result = run_daily_coach_natural_draft_audit_scenario(
        scenario_id="rich_nutrition_training_recovery",
        provider="deterministic",
        brief=_brief(),
        draft=NaturalCoachDraft(
            headline="Daily Coach",
            body="Add one can of canned tuna to prevent muscle loss.",
        ),
    )

    assert result.audit_result.passed is False
    assert result.audit_result.repairable is False
    assert result.repair_result.attempted is False
    assert result.final_source == "deterministic_fallback"


def test_natural_draft_matrix_writes_artifacts(tmp_path: Path, monkeypatch) -> None:
    import services.daily_coach_natural_draft_audit_service as service

    monkeypatch.setattr(
        service, "build_approved_coach_brief", lambda **kwargs: _brief()
    )

    results = run_daily_coach_natural_draft_audit_matrix(
        scenarios=["rich_nutrition_training_recovery"],
        provider="deterministic",
        output_dir=tmp_path,
    )

    assert len(results) == 1
    assert (tmp_path / "comparison_table.md").exists()


def test_product_bad_but_factually_safe_copy_uses_humanized_fallback() -> None:
    result = run_daily_coach_natural_draft_audit_scenario(
        scenario_id="rich_nutrition_training_recovery",
        provider="deterministic",
        brief=_brief(),
        draft=NaturalCoachDraft(
            headline="Daily Coach",
            body="Protein is below target. Add canned tuna if protein is still short.",
        ),
    )

    assert result.audit_result.passed is True
    assert result.product_voice_audit_result is not None
    assert result.product_voice_audit_result.passed is False
    assert result.final_source == "deterministic_fallback"
    assert result.final_copy is not None
    assert "eat some canned tuna" in result.final_copy.body.lower()
    assert result.reviewer_conclusion == "product_voice_failure"


def test_first_pass_artifact_preserves_draft_before_fallback(tmp_path: Path) -> None:
    result = run_daily_coach_natural_draft_audit_scenario(
        scenario_id="rich_nutrition_training_recovery",
        provider="deterministic",
        output_dir=tmp_path,
        brief=_brief(),
        draft=NaturalCoachDraft(
            headline="First Pass",
            body="Protein is below target. Add canned tuna if protein is still short.",
        ),
    )

    first_pass = (tmp_path / "first_pass_model_draft_before_audit.md").read_text()
    side_by_side = (tmp_path / "side_by_side_output_comparison.md").read_text()
    assert "Add canned tuna" in first_pass
    assert "First Pass" in first_pass
    assert "Deterministic fallback" in side_by_side
    assert "GPT-5.5/provider first-pass natural draft before audit" in side_by_side
    assert result.final_source == "deterministic_fallback"
