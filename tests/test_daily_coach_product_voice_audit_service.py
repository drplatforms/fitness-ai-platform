from __future__ import annotations

from models.daily_coach_natural_draft_audit_models import NaturalCoachDraft
from services.daily_coach_approved_brief_service import build_approved_coach_brief
from services.daily_coach_product_voice_audit_service import (
    audit_daily_coach_product_voice,
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


def test_product_voice_audit_rejects_mechanical_food_action_in_approval_mode() -> None:
    audit = audit_daily_coach_product_voice(
        NaturalCoachDraft(
            headline="Daily Coach",
            body="Protein is below target. Add canned tuna if protein is still short.",
        ),
        _brief(),
        mode="approval",
    )

    assert audit.passed is False
    assert audit.decision == "repair_required"
    assert audit.mechanical_food_action_count == 1


def test_product_voice_audit_allows_human_food_action() -> None:
    audit = audit_daily_coach_product_voice(
        NaturalCoachDraft(
            headline="Daily Coach",
            body="Protein is below target. Eat some canned tuna if protein is still short.",
        ),
        _brief(),
        mode="approval",
    )

    assert audit.passed is True
    assert audit.product_readiness_score >= 4


def test_product_voice_audit_flags_bad_nutrition_training_causal_logic() -> None:
    audit = audit_daily_coach_product_voice(
        NaturalCoachDraft(
            headline="Daily Coach",
            body="Do not make up for nutrition by pushing harder. Eat some canned tuna if protein is still short.",
        ),
        _brief(),
        mode="approval",
    )

    assert audit.passed is False
    assert any(
        finding.finding_type == "bad_nutrition_training_causal_logic"
        for finding in audit.findings
    )
