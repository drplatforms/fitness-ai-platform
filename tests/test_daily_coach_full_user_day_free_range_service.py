from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from models.daily_coach_full_user_day_models import (
    DailyCoachFullUserDayProviderCallResult,
)
from models.daily_coach_natural_draft_audit_models import (
    AddressingPolicy,
    ApprovedCoachBrief,
    ApprovedCoachFact,
    ApprovedFoodAction,
)
from services.daily_coach_full_user_day_free_range_service import (
    build_daily_coach_full_user_day_packet,
    build_full_user_day_free_range_prompt,
    list_daily_coach_full_user_day_prompt_variants,
    run_daily_coach_full_user_day_free_range_scenario,
    scan_full_user_day_app_copy,
    write_daily_coach_full_user_day_artifacts,
)


def _fake_synthesis() -> SimpleNamespace:
    return SimpleNamespace(
        user_id=102,
        synthesis_date="2026-06-27",
        scenario="aligned_managed",
        confidence="Moderate",
        today_summary="APP PROSE SHOULD NOT BE PASSED",
        recovery_signal="green-light day SHOULD NOT BE PASSED",
        training_signal="planned workout SHOULD NOT BE PASSED",
        workout_guidance="Run the Gradual Progression Strength Session.",
        execution_context="APP EXECUTION PROSE SHOULD NOT BE PASSED",
        logging_focus="APP LOGGING PROSE SHOULD NOT BE PASSED",
        plan_fit_note="APP PLAN PROSE SHOULD NOT BE PASSED",
        recommended_focus="approved protein-focused food options SHOULD NOT BE PASSED",
        reason_codes=["aligned_managed", "protein_status_visible"],
        limitations=["nutrition_logging_may_be_incomplete"],
    )


def _fake_health_state() -> SimpleNamespace:
    return SimpleNamespace(
        user_id=102,
        user_name="Dustin",
        primary_goal="strength_and_recomposition",
        age=39,
        height_cm=177.8,
        starting_weight=190.0,
        latest_body_weight=189.5,
        goal_weight=180.0,
        activity_level="moderate",
        system_stress_level="manageable",
        nutrition_training_alignment="nutrition_supports_training_if_logged",
        coordinator_focus="APP COORDINATOR PROSE SHOULD BE OMITTED",
        recovery_state=SimpleNamespace(
            readiness_level="Supportive",
            fatigue_risk="Low",
            recovery_score=78,
            avg_sleep=7.4,
            avg_energy=8.0,
            avg_soreness=3.0,
            sleep_trend="Stable",
            weight_trend="Stable",
            weight_change=0.2,
        ),
        nutrition_state=SimpleNamespace(
            nutrition_summary="APP NUTRITION PROSE SHOULD BE OMITTED",
            has_nutrition_data=True,
            calories=1750,
            protein_grams=118,
            carbohydrate_grams=190,
            fat_grams=52,
            protein_status="Below",
            calorie_status="Below",
            recovery_nutrition_status="usable",
        ),
        training_state=SimpleNamespace(
            workout_summary="APP WORKOUT PROSE SHOULD BE OMITTED",
            has_workout_data=True,
            workout_count=3,
            adherence_level="Consistent",
            training_trend="Stable",
            total_volume_load=22000,
            avg_rir=2.4,
            training_load="Moderate",
            recovery_demand="Manageable",
        ),
    )


def _food_suggestions() -> list[dict]:
    return [
        {
            "display_name": "canned tuna",
            "suggested_grams": 120,
            "estimated_calories": 132,
            "estimated_protein_g": 29,
            "estimated_carbohydrate_g": 0,
            "estimated_fat_g": 1,
            "macro_gap_addressed": "protein_g",
            "confidence": "Moderate",
            "summary": "protein_g",
        },
        {
            "display_name": "cooked chicken breast",
            "suggested_grams": 150,
            "estimated_calories": 248,
            "estimated_protein_g": 46,
            "estimated_carbohydrate_g": 0,
            "estimated_fat_g": 5,
            "macro_gap_addressed": "protein_g",
            "confidence": "Moderate",
            "summary": "protein_g",
        },
        {
            "display_name": "turkey breast",
            "suggested_grams": 140,
            "estimated_calories": 189,
            "estimated_protein_g": 41,
            "estimated_carbohydrate_g": 0,
            "estimated_fat_g": 2,
            "macro_gap_addressed": "protein_g",
            "confidence": "Moderate",
            "summary": "protein_g",
        },
        {
            "display_name": "Greek yogurt",
            "suggested_grams": 200,
            "estimated_calories": 118,
            "estimated_protein_g": 20,
            "estimated_carbohydrate_g": 8,
            "estimated_fat_g": 0,
            "macro_gap_addressed": "protein_g",
            "confidence": "Moderate",
            "summary": "protein_g",
        },
        {
            "display_name": "oatmeal",
            "suggested_grams": 80,
            "estimated_calories": 300,
            "estimated_protein_g": 10,
            "estimated_carbohydrate_g": 54,
            "estimated_fat_g": 6,
            "macro_gap_addressed": "calories",
            "confidence": "Moderate",
            "summary": "calories",
        },
        {
            "display_name": "banana",
            "suggested_grams": 120,
            "estimated_calories": 105,
            "estimated_protein_g": 1,
            "estimated_carbohydrate_g": 27,
            "estimated_fat_g": 0,
            "macro_gap_addressed": "carbs_g",
            "confidence": "Moderate",
            "summary": "carbs_g",
        },
        {
            "display_name": "rice",
            "suggested_grams": 180,
            "estimated_calories": 230,
            "estimated_protein_g": 4,
            "estimated_carbohydrate_g": 50,
            "estimated_fat_g": 1,
            "macro_gap_addressed": "carbs_g",
            "confidence": "Moderate",
            "summary": "carbs_g",
        },
        {
            "display_name": "olive oil",
            "suggested_grams": 14,
            "estimated_calories": 119,
            "estimated_protein_g": 0,
            "estimated_carbohydrate_g": 0,
            "estimated_fat_g": 14,
            "macro_gap_addressed": "fat_g",
            "confidence": "Moderate",
            "summary": "fat_g",
        },
        {
            "display_name": "whole milk",
            "suggested_grams": 244,
            "estimated_calories": 149,
            "estimated_protein_g": 8,
            "estimated_carbohydrate_g": 12,
            "estimated_fat_g": 8,
            "macro_gap_addressed": "calories",
            "confidence": "generic",
            "summary": "calories",
        },
    ]


def _fake_value_context() -> dict:
    return {
        "approved_nutrition": {
            "available": True,
            "date": "2026-06-27",
            "logging_completeness": "Partial Day",
            "confidence": "Moderate",
            "actuals": {
                "logged_calories": 1750,
                "logged_protein_g": 118,
                "logged_carbs_g": 190,
                "logged_fat_g": 52,
            },
            "macro_status": {
                "calories": {
                    "actual": 1750,
                    "target_min": 2400,
                    "target_max": 2600,
                    "delta_min": -650,
                    "delta_max": -850,
                    "target_status": "Below",
                    "confidence": "Moderate",
                    "display_allowed": True,
                },
                "protein_g": {
                    "actual": 118,
                    "target_min": 150,
                    "target_max": 180,
                    "delta_min": -32,
                    "delta_max": -62,
                    "target_status": "Below",
                    "confidence": "Moderate",
                    "display_allowed": True,
                },
            },
            "approved_food_suggestions": _food_suggestions(),
        },
        "approved_value_claims": [],
    }


def _fake_brief() -> ApprovedCoachBrief:
    return ApprovedCoachBrief(
        brief_id="test-brief",
        user_id=102,
        date="2026-06-27",
        scenario="aligned_managed",
        today_intent="Train cleanly and verify protein.",
        addressing_policy=AddressingPolicy(),
        approved_facts=(
            ApprovedCoachFact(
                claim_key="nutrition.protein.status",
                claim_type="nutrition_claim",
                value="Below",
                display_value="protein below target",
            ),
        ),
        approved_interpretations=(),
        approved_food_actions=(
            ApprovedFoodAction(
                food_claim_key="nutrition.food_suggestion.1",
                canonical_name="Egg Whites",
                friendly_name="egg whites",
                macro_reason="protein_g",
                allowed_conditions=("if protein is still short",),
                serving_display="150g",
                serving_allowed=True,
            ),
        ),
        approved_training_actions=(),
        approved_recovery_interpretations=(),
    )


def _packet():
    return build_daily_coach_full_user_day_packet(
        user_id=102,
        target_date="2026-06-27",
        scenario_id="aligned_managed",
        synthesis=_fake_synthesis(),
        health_state=_fake_health_state(),
        value_context=_fake_value_context(),
        brief=_fake_brief(),
    )


def test_full_user_day_packet_includes_macro_targets_actuals_deltas_and_food_candidates() -> (
    None
):
    packet = _packet()
    payload = packet.to_dict()

    assert payload["nutrition"]["actuals"]["logged_protein_g"] == 118
    assert (
        payload["nutrition"]["macro_targets_actuals_deltas"]["protein_g"]["target_min"]
        == 150
    )
    assert (
        payload["nutrition"]["macro_targets_actuals_deltas"]["protein_g"]["delta_min"]
        == -32
    )
    assert len(payload["food_candidates"]) > 3
    assert payload["food_candidates"][0]["estimated_protein_g"] == 29
    assert payload["food_candidates"][0]["plain_name_for_user"] == "canned tuna"
    assert "approved option" not in json.dumps(payload).lower()


def test_user_health_state_projection_records_included_and_omitted_fields() -> None:
    packet = _packet()
    coverage = packet.user_health_state_field_coverage

    assert "primary_goal" in coverage["included_fields"]
    assert "training_state.avg_rir" in coverage["included_fields"]
    assert "user_name" in coverage["omitted_fields"]
    assert "nutrition_state.nutrition_summary" in coverage["omitted_fields"]
    assert "training_state.workout_summary" in coverage["omitted_fields"]


def test_free_range_prompt_uses_structured_packet_without_phrase_bans_or_app_copy() -> (
    None
):
    prompt = build_full_user_day_free_range_prompt(
        _packet(), "free_range_full_user_day_practical_coach"
    )
    lowered = prompt.lower()

    assert "DATA_PACKET_JSON" in prompt
    assert "calories" in prompt
    assert "canned tuna" in prompt
    assert "approved option" not in lowered
    assert "approved food option" not in lowered
    assert "approved protein-focused" not in lowered
    assert "green-light day" not in lowered
    assert "planned workout" not in lowered
    assert "current_narrow_path" not in lowered
    assert "fallback" not in lowered
    assert "do not use the phrase" not in lowered
    assert "old daily coach copy" not in lowered


def test_product_language_scan_flags_forensic_leaks() -> None:
    text = "use an approved option for the remaining protein gap on this green-light day after the planned workout"
    findings = scan_full_user_day_app_copy(text)
    patterns = {finding["pattern"] for finding in findings}

    assert "approved option" in patterns
    assert "remaining protein gap" in patterns
    assert "green-light day" in patterns
    assert "planned workout" in patterns


def test_run_supports_repeat_and_captures_first_pass_before_audit(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: _packet(),
    )

    def fake_provider(model: str, prompt: str, timeout: float, env: dict):
        assert model == "gpt-5.5"
        assert "DATA_PACKET_JSON" in prompt
        return DailyCoachFullUserDayProviderCallResult(
            raw_text="Run today’s strength work, keep RIR 2-4, and eat canned tuna if protein is still short.",
            input_tokens=1000,
            output_tokens=80,
            total_tokens=1080,
            estimated_cost_usd=0.01,
            cost_estimate_basis="test",
        )

    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="openai",
        model="gpt-5.5",
        variants=["free_range_full_user_day_practical_coach"],
        repeat=3,
        allow_live_provider=True,
        environ={},
        provider_generate=fake_provider,
    )

    assert len(result.variants) == 3
    assert {variant.repeat_index for variant in result.variants} == {1, 2, 3}
    assert all("canned tuna" in variant.first_pass_draft for variant in result.variants)
    assert all(
        variant.runtime_metadata["repair_or_fallback_before_first_pass"] is False
        for variant in result.variants
    )
    assert result.variants[0].runtime_metadata["total_tokens"] == 1080


def test_provider_payload_debug_artifacts_are_opt_in_and_safe(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: _packet(),
    )

    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["free_range_full_user_day_minimal"],
        output_dir=None,
    )
    write_daily_coach_full_user_day_artifacts(
        tmp_path,
        [result],
        write_provider_payload_debug=True,
    )

    expected = {
        "provider_input_prompt.md",
        "provider_payload_debug.json",
        "full_user_day_packet.json",
        "full_user_day_packet_summary.md",
        "first_pass_drafts.md",
        "first_pass_drafts_compact.md",
        "side_by_side_comparison.md",
        "best_variant_summary.md",
        "product_language_findings.md",
        "claim_risk_summary.md",
        "consistency_summary.md",
        "token_cost_telemetry.md",
        "token_cost_telemetry.csv",
        "artifact_safety_summary.md",
        "pasteback_report.md",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})
    prompt_debug = (tmp_path / "provider_input_prompt.md").read_text(encoding="utf-8")
    payload_debug = json.loads(
        (tmp_path / "provider_payload_debug.json").read_text(encoding="utf-8")
    )
    first_pass = (tmp_path / "first_pass_drafts.md").read_text(encoding="utf-8")
    serialized = "\n".join(
        path.read_text(encoding="utf-8")
        for path in tmp_path.iterdir()
        if path.is_file()
    ).lower()

    assert "DATA_PACKET_JSON" in prompt_debug
    assert payload_debug["records"][0]["prompt_character_count"] > 100
    assert (
        payload_debug["records"][0]["redaction_safety_summary"][
            "raw_provider_envelope_persisted"
        ]
        is False
    )
    assert "Run today" in first_pass or "Today" in first_pass
    assert "sk-" not in serialized
    assert "openai_api_key" not in serialized
    assert "raw provider envelope" in serialized


def test_payload_debug_artifacts_are_not_written_without_explicit_flag(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: _packet(),
    )

    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["free_range_full_user_day_minimal"],
        output_dir=None,
    )
    write_daily_coach_full_user_day_artifacts(
        tmp_path,
        [result],
        write_provider_payload_debug=False,
    )

    assert not (tmp_path / "provider_input_prompt.md").exists()
    assert not (tmp_path / "provider_payload_debug.json").exists()
    assert (tmp_path / "pasteback_report.md").exists()


def test_voice_variants_exist_without_phrase_bans_or_old_app_examples() -> None:
    variants = {
        row["variant_id"]: row
        for row in list_daily_coach_full_user_day_prompt_variants()
    }

    for variant_id in (
        "free_range_full_user_day_strict_coach",
        "free_range_full_user_day_empathetic_coach",
        "free_range_full_user_day_hypeman_coach",
    ):
        assert variant_id in variants
        text = json.dumps(variants[variant_id]).lower()
        assert "do not use the phrase" not in text
        assert "old daily coach copy" not in text
        assert "fallback" not in text


def test_food_candidates_include_precision_quote_style_and_display_phrase() -> None:
    packet = _packet()
    foods = packet.to_dict()["food_candidates"]

    assert len(foods) >= 8
    first = foods[0]
    assert first["value_precision"] == "database_calculated"
    assert first["quote_style"] == "direct"
    assert "29g protein" in first["display_phrase"]
    assert "approved" not in json.dumps(foods).lower()
    assert any(food["quote_style"] == "hedged" for food in foods)


def test_macro_precision_is_represented_without_global_about_ban() -> None:
    packet = _packet()
    prompt = build_full_user_day_free_range_prompt(
        packet, "free_range_full_user_day_practical_coach"
    )
    protein = packet.nutrition["macro_targets_actuals_deltas"]["protein_g"]

    assert protein["value_precision"] == "exact_app_calculated"
    assert protein["quote_style"] == "direct"
    assert "when quote_style is direct" in prompt
    assert "about/roughly only" in prompt
    assert "do not use about" not in prompt.lower()
    assert "never say about" not in prompt.lower()


def test_training_set_level_availability_is_honest_when_absent() -> None:
    packet = _packet()

    assert packet.training["set_level_data_available"] is False
    assert (
        "no structured set-level data"
        in packet.training["set_level_data_unavailable_reason"]
    )


def test_training_set_level_data_is_projected_when_available() -> None:
    health = _fake_health_state()
    health.training_state.set_level_data = [
        {
            "exercise_name": "bench press",
            "target_sets": 3,
            "target_reps": 8,
            "actual_sets": 3,
            "actual_reps": 8,
            "actual_rir": 2,
            "progression_signal": "in_range",
        }
    ]
    packet = build_daily_coach_full_user_day_packet(
        user_id=102,
        target_date="2026-06-27",
        scenario_id="aligned_managed",
        synthesis=_fake_synthesis(),
        health_state=health,
        value_context=_fake_value_context(),
        brief=_fake_brief(),
    )

    assert packet.training["set_level_data_available"] is True
    assert packet.training["set_level_data"][0]["exercise_name"] == "bench press"


def test_voice_variants_run_when_requested(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: _packet(),
    )

    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        include_voice_variants=True,
    )
    variant_ids = {variant.variant_id for variant in result.variants}

    assert "free_range_full_user_day_strict_coach" in variant_ids
    assert "free_range_full_user_day_empathetic_coach" in variant_ids
    assert "free_range_full_user_day_hypeman_coach" in variant_ids


def test_v2_artifacts_include_manifest_precision_food_and_voice_summaries(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: _packet(),
    )

    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["free_range_full_user_day_strict_coach"],
        output_dir=None,
    )
    write_daily_coach_full_user_day_artifacts(
        tmp_path,
        [result],
        write_provider_payload_debug=True,
        write_model_input_manifest=True,
        write_precision_summary=True,
        write_food_candidate_summary=True,
    )

    for filename in (
        "model_input_manifest.md",
        "voice_variant_summary.md",
        "precision_usage_summary.md",
        "food_candidate_summary.md",
    ):
        assert (tmp_path / filename).exists()
    manifest = (tmp_path / "model_input_manifest.md").read_text(encoding="utf-8")
    pasteback = (tmp_path / "pasteback_report.md").read_text(encoding="utf-8")
    assert "Food candidates seen:" in manifest
    assert "Set-level data available:" in manifest
    assert "strict_coach" in (tmp_path / "voice_variant_summary.md").read_text(
        encoding="utf-8"
    )
    assert "Food candidate summary:" in pasteback
    assert "Set-level data available:" in pasteback


def test_payload_debug_records_precision_and_field_manifest_data(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: _packet(),
    )

    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["free_range_full_user_day_minimal"],
        output_dir=None,
    )
    write_daily_coach_full_user_day_artifacts(
        tmp_path,
        [result],
        write_provider_payload_debug=True,
    )
    payload = json.loads(
        (tmp_path / "provider_payload_debug.json").read_text(encoding="utf-8")
    )
    record = payload["records"][0]

    assert record["food_candidate_count"] >= 8
    assert record["precision_summary"]["food_quote_styles"]["direct"] >= 1
    assert record["user_health_state_included_fields"]
    assert record["set_level_data_available"] is False


def test_deterministic_provider_runs_without_live_provider_permission(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: _packet(),
    )

    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["free_range_full_user_day_minimal"],
        allow_live_provider=False,
    )

    assert result.variants[0].skipped is False
    assert result.variants[0].skip_reason is None


def test_live_provider_still_requires_explicit_opt_in(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: _packet(),
    )

    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="openai",
        variants=["free_range_full_user_day_minimal"],
        allow_live_provider=False,
    )

    assert result.variants[0].skipped is True
    assert result.variants[0].skip_reason == "live_provider_not_allowed"


def test_completion_diagnostics_artifact_detects_truncated_draft(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: _packet(),
    )

    def fake_provider(model: str, prompt: str, timeout: float, env: dict):
        return DailyCoachFullUserDayProviderCallResult(
            raw_text="Train clean, eat well, and",
            output_tokens=1330,
            max_output_tokens=1400,
            finish_reason="length",
            completion_status="incomplete",
        )

    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="openai",
        variants=["free_range_full_user_day_practical_coach"],
        allow_live_provider=True,
        provider_generate=fake_provider,
        environ={},
    )
    write_daily_coach_full_user_day_artifacts(
        tmp_path,
        [result],
        write_completion_diagnostics=True,
    )

    diagnostics = json.loads(
        (tmp_path / "completion_diagnostics.json").read_text(encoding="utf-8")
    )
    record = diagnostics["records"][0]
    assert record["truncated"] is True
    assert "finish_reason:length" in record["truncation_heuristics"]
    assert (tmp_path / "completion_diagnostics.md").exists()


def test_number_formatting_and_macro_display_cards_are_display_ready(
    tmp_path: Path, monkeypatch
) -> None:
    health = _fake_health_state()
    health.training_state.total_volume_load = 35406.0
    health.recovery_state.weight_change = 22.0
    packet = build_daily_coach_full_user_day_packet(
        user_id=102,
        target_date="2026-06-27",
        scenario_id="aligned_managed",
        synthesis=_fake_synthesis(),
        health_state=health,
        value_context=_fake_value_context(),
        brief=_fake_brief(),
    )
    assert packet.training["total_volume_load_display"] == "35,406 total volume load"
    assert packet.recovery["weight_change_display"] == "22 lb"
    assert packet.recovery["weight_trend_surface_to_coach"] is False

    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: packet,
    )
    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["free_range_full_user_day_minimal"],
    )
    write_daily_coach_full_user_day_artifacts(
        tmp_path,
        [result],
        write_macro_display_card=True,
        write_number_formatting_summary=True,
    )
    macro_card = (tmp_path / "macro_display_card.md").read_text(encoding="utf-8")
    formatting = (tmp_path / "number_formatting_summary.md").read_text(encoding="utf-8")

    assert "1,750 calories / 2,400 calories–2,600 calories" in macro_card
    assert "35,406 total volume load" in formatting
    assert "22.0" not in formatting


def test_food_option_card_and_snack_candidates_use_known_food_pool(
    tmp_path: Path, monkeypatch
) -> None:
    packet = _packet()
    food_names = {food["plain_name_for_user"] for food in packet.food_candidates}
    snacks = packet.to_dict()["ai_snack_candidates"]

    assert len(packet.food_candidates) >= 20
    assert any(
        food["category"] == "carb_foods_that_may_help"
        for food in packet.food_candidates
    )
    assert snacks
    for snack in snacks:
        assert set(snack["foods_included"]).issubset(food_names)

    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: packet,
    )
    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["free_range_full_user_day_minimal"],
    )
    write_daily_coach_full_user_day_artifacts(
        tmp_path,
        [result],
        write_food_option_card=True,
        write_ai_snack_candidates=True,
    )

    assert "| Option | Serving | Protein | Calories |" in (
        tmp_path / "food_option_card.md"
    ).read_text(encoding="utf-8")
    assert "Greek yogurt + banana" in (tmp_path / "ai_snack_candidates.md").read_text(
        encoding="utf-8"
    )


def test_model_input_manifest_reports_v3_visibility(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_full_user_day_free_range_service.build_daily_coach_full_user_day_packet",
        lambda **kwargs: _packet(),
    )
    result = run_daily_coach_full_user_day_free_range_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["free_range_full_user_day_hypeman_coach"],
    )
    write_daily_coach_full_user_day_artifacts(
        tmp_path,
        [result],
        write_model_input_manifest=True,
        write_voice_style_findings=True,
    )
    manifest = (tmp_path / "model_input_manifest.md").read_text(encoding="utf-8")
    voice = (tmp_path / "voice_style_findings.md").read_text(encoding="utf-8")

    assert "Food candidates seen:" in manifest
    assert "Set-level data available:" in manifest
    assert "Prompt contains phrase bans: False" in manifest
    assert "free_range_full_user_day_hypeman_coach" in voice
