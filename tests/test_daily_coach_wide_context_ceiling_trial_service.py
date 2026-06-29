from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from models.daily_coach_natural_draft_audit_models import (
    AddressingPolicy,
    ApprovedCoachBrief,
    ApprovedCoachFact,
    ApprovedFoodAction,
    ApprovedRecoveryInterpretation,
    ApprovedTrainingAction,
    ClaimAuditResult,
    NaturalCoachDraft,
    NaturalDraftAuditRunResult,
    ProductVoiceAuditResult,
    RepairAttemptResult,
)
from models.daily_coach_wide_context_models import (
    DailyCoachWideContextProviderCallResult,
)
from services.daily_coach_wide_context_ceiling_trial_service import (
    BASELINE_DRIFT,
    build_daily_coach_wide_context_packet,
    build_wide_context_writer_prompt,
    list_daily_coach_wide_context_prompt_variants,
    run_daily_coach_wide_context_ceiling_trial_scenario,
    scan_wide_context_product_language,
    write_wide_context_ceiling_trial_artifacts,
)


def _fake_synthesis() -> SimpleNamespace:
    return SimpleNamespace(
        user_id=102,
        synthesis_date="2026-06-27",
        scenario="aligned_managed",
        confidence="Moderate",
        today_summary="Training is appropriate, but nutrition needs a simple check.",
        recovery_signal="Today is a green-light day for training.",
        training_signal="Planned strength work is appropriate today.",
        workout_guidance="Keep most working sets around RIR 2-3.",
        execution_context="Recent training is logged.",
        logging_focus="Protein is the clearest nutrition item to verify.",
        plan_fit_note="The planned session fits the available context.",
        recommended_focus="Train cleanly and verify protein before the day gets away.",
        reason_codes=["aligned_managed", "protein_status_visible"],
        limitations=["Nutrition logging may not capture the whole day."],
    )


def _fake_health_state() -> SimpleNamespace:
    return SimpleNamespace(
        user_id=102,
        primary_goal="strength_and_recomposition",
        age=39,
        height_cm=177.8,
        starting_weight=190.0,
        latest_body_weight=189.5,
        goal_weight=180.0,
        activity_level="moderate",
        recovery_state=SimpleNamespace(
            readiness_level="Supportive",
            fatigue_risk="Low",
            recovery_score=78,
            avg_sleep=7.4,
            avg_energy=8.0,
            avg_soreness=3.0,
            sleep_trend="Stable",
            weight_trend="Stable",
        ),
        training_state=SimpleNamespace(
            workout_summary="Three logged workouts this week.",
            workout_count=3,
            adherence_level="Consistent",
            training_trend="Stable",
            avg_rir=2.4,
            training_load="Moderate",
            recovery_demand="Manageable",
        ),
    )


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
            },
            "macro_status": {
                "protein_g": {
                    "actual": 118,
                    "target_min": 150,
                    "target_status": "Below",
                    "display_allowed": True,
                    "confidence": "Moderate",
                }
            },
            "approved_food_suggestions": [
                {
                    "display_name": "Greek yogurt",
                    "suggested_grams": 200,
                    "estimated_protein_g": 20,
                    "macro_gap_addressed": "protein_g",
                    "confidence": "Moderate",
                    "summary": "A smaller protein option.",
                }
            ],
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
        approved_interpretations=(
            "Recovery is supportive enough for planned training.",
        ),
        approved_food_actions=(
            ApprovedFoodAction(
                food_claim_key="nutrition.food_suggestion.1",
                canonical_name="Greek Yogurt, Plain",
                friendly_name="Greek yogurt",
                macro_reason="protein is still short",
                allowed_conditions=("if protein is still short",),
                serving_display="200g",
                serving_allowed=True,
            ),
        ),
        approved_training_actions=(
            ApprovedTrainingAction(
                claim_keys=("training.rir_range",),
                instruction="Keep most working sets around RIR 2-3.",
            ),
        ),
        approved_recovery_interpretations=(
            ApprovedRecoveryInterpretation(
                claim_keys=("recovery.readiness_level",),
                interpretation="Recovery supports planned training.",
            ),
        ),
    )


def test_wide_context_packet_uses_rich_approved_context_without_raw_fields() -> None:
    packet = build_daily_coach_wide_context_packet(
        user_id=102,
        target_date="2026-06-27",
        scenario_id="aligned_managed",
        brief=_fake_brief(),
        synthesis=_fake_synthesis(),
        health_state=_fake_health_state(),
        value_context=_fake_value_context(),
    )

    payload = packet.to_dict()
    serialized = str(payload).lower()
    assert payload["profile_context"]["latest_body_weight"] == 189.5
    assert (
        payload["nutrition_context"]["macro_status"]["protein_g"]["target_status"]
        == "Below"
    )
    assert payload["food_choices"][0]["friendly_name"] == "Greek yogurt"
    assert "raw_source_payload" not in serialized
    assert "raw_provider_output" not in serialized
    assert "openai_api_key" not in serialized


def test_wide_context_writer_prompt_is_short_uncaged_and_not_narrow_path_cage() -> None:
    packet = build_daily_coach_wide_context_packet(
        user_id=102,
        target_date="2026-06-27",
        scenario_id="aligned_managed",
        brief=_fake_brief(),
        synthesis=_fake_synthesis(),
        health_state=_fake_health_state(),
        value_context=_fake_value_context(),
    )

    prompt = build_wide_context_writer_prompt(packet, "wide_context_practical_coach")

    assert "Write a useful Daily Coach note" in prompt
    assert "Greek yogurt" in prompt
    assert "Return only the coach note" in prompt
    assert "claim_key" not in prompt
    assert "validator" not in prompt.lower()
    assert "APPROVED_CONTEXT" not in prompt
    lowered = prompt.lower()
    assert "approved option" not in lowered
    assert "green-light day" not in lowered
    assert "planned session" not in lowered
    assert "planned workout" not in lowered
    assert "today’s strength work" in lowered
    assert "good day to train" in lowered or "recovery supports today" in lowered
    assert "REQUIRED_JSON_SCHEMA" not in prompt


def test_prompt_variants_include_required_ceiling_trial_variants() -> None:
    variant_ids = {
        variant["variant_id"]
        for variant in list_daily_coach_wide_context_prompt_variants()
    }

    assert "current_narrow_path" in variant_ids
    assert "wide_context_minimal_prompt" in variant_ids
    assert "wide_context_practical_coach" in variant_ids
    assert "wide_context_direct_coach" in variant_ids


def test_openai_live_provider_requires_explicit_allow_live_provider(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.build_daily_coach_wide_context_packet",
        lambda **kwargs: build_daily_coach_wide_context_packet(
            user_id=102,
            target_date="2026-06-27",
            scenario_id="aligned_managed",
            brief=_fake_brief(),
            synthesis=_fake_synthesis(),
            health_state=_fake_health_state(),
            value_context=_fake_value_context(),
        ),
    )

    result = run_daily_coach_wide_context_ceiling_trial_scenario(
        scenario_id="aligned_managed",
        provider="openai",
        model="gpt-5.5",
        variants=["wide_context_minimal_prompt"],
        allow_live_provider=False,
        environ={},
    )

    variant = result.variants[0]
    assert variant.skipped is True
    assert variant.skip_reason == "live_provider_not_allowed"
    assert variant.runtime_metadata["normal_today_unchanged"] is True


def test_mocked_provider_result_records_token_and_cost_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.build_daily_coach_wide_context_packet",
        lambda **kwargs: build_daily_coach_wide_context_packet(
            user_id=102,
            target_date="2026-06-27",
            scenario_id="aligned_managed",
            brief=_fake_brief(),
            synthesis=_fake_synthesis(),
            health_state=_fake_health_state(),
            value_context=_fake_value_context(),
        ),
    )

    def fake_provider(model: str, prompt: str, timeout: float, env: dict):
        assert model == "gpt-5.5"
        assert "Useful coaching context for today" in prompt
        return DailyCoachWideContextProviderCallResult(
            raw_text="Train as planned, keep most sets around RIR 2-3, and use Greek yogurt if protein is still short.",
            input_tokens=1200,
            output_tokens=80,
            total_tokens=1280,
            cached_input_tokens=200,
            estimated_cost_usd=0.01,
            cost_estimate_basis="test",
        )

    result = run_daily_coach_wide_context_ceiling_trial_scenario(
        scenario_id="aligned_managed",
        provider="openai",
        model="gpt-5.5",
        variants=["wide_context_practical_coach"],
        allow_live_provider=True,
        environ={"OPENAI_API_KEY": "test-key"},
        provider_generate=fake_provider,
    )

    variant = result.variants[0]
    assert variant.skipped is False
    assert variant.first_pass_draft.startswith("Train as planned")
    assert variant.runtime_metadata["input_tokens"] == 1200
    assert variant.runtime_metadata["output_tokens"] == 80
    assert variant.runtime_metadata["total_tokens"] == 1280
    assert variant.runtime_metadata["estimated_cost_usd"] == 0.01


def test_wide_context_artifacts_are_written_and_sanitized(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.build_daily_coach_wide_context_packet",
        lambda **kwargs: build_daily_coach_wide_context_packet(
            user_id=102,
            target_date="2026-06-27",
            scenario_id="aligned_managed",
            brief=_fake_brief(),
            synthesis=_fake_synthesis(),
            health_state=_fake_health_state(),
            value_context=_fake_value_context(),
        ),
    )

    result = run_daily_coach_wide_context_ceiling_trial_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["current_narrow_path", "wide_context_direct_coach"],
        output_dir=tmp_path,
    )

    write_wide_context_ceiling_trial_artifacts(tmp_path, [result])

    expected_files = {
        "run_config.json",
        "wide_context_packet_summary.json",
        "prompt_variants.md",
        "first_pass_drafts.md",
        "side_by_side_comparison.md",
        "review_summary.md",
        "token_cost_telemetry.md",
        "token_cost_telemetry.csv",
        "scoring_template.md",
        "baseline_drift.md",
        "artifact_safety_summary.md",
        "first_pass_drafts_compact.md",
        "variant_score_summary.md",
        "best_variant_summary.md",
        "product_language_findings.md",
        "pasteback_report.md",
    }
    assert expected_files.issubset({path.name for path in tmp_path.iterdir()})
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in tmp_path.iterdir()
    )
    assert "raw_provider_output" not in combined
    assert "openai_api_key" not in combined.lower()
    assert BASELINE_DRIFT["test_file"] in (tmp_path / "baseline_drift.md").read_text(
        encoding="utf-8"
    )


def test_current_narrow_path_variant_uses_existing_audit_result(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.build_daily_coach_wide_context_packet",
        lambda **kwargs: build_daily_coach_wide_context_packet(
            user_id=102,
            target_date="2026-06-27",
            scenario_id="aligned_managed",
            brief=_fake_brief(),
            synthesis=_fake_synthesis(),
            health_state=_fake_health_state(),
            value_context=_fake_value_context(),
        ),
    )
    narrow_result = NaturalDraftAuditRunResult(
        scenario_id="aligned_managed",
        user_id=102,
        date="2026-06-27",
        provider="deterministic",
        model=None,
        draft=NaturalCoachDraft("Narrow", "Existing narrow-path draft."),
        extracted_claims=(),
        audit_result=ClaimAuditResult(passed=True),
        repair_result=RepairAttemptResult(
            attempted=False, provider="deterministic", model=None
        ),
        final_copy=None,
        final_source="draft_approved",
        product_voice_audit_result=ProductVoiceAuditResult(
            passed=True, mode="approval", decision="approve"
        ),
    )
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.run_daily_coach_natural_draft_audit_scenario",
        lambda **kwargs: narrow_result,
    )

    result = run_daily_coach_wide_context_ceiling_trial_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["current_narrow_path"],
    )

    variant = result.variants[0]
    assert variant.variant_id == "current_narrow_path"
    assert variant.first_pass_draft == "Narrow\n\nExisting narrow-path draft."
    assert variant.runtime_metadata["uses_existing_narrow_path"] is True


def test_writer_prompt_cleans_backend_shaped_food_language() -> None:
    bad_brief = ApprovedCoachBrief(
        brief_id="test-brief-bad-language",
        user_id=102,
        date="2026-06-27",
        scenario="aligned_managed",
        today_intent="Nutrition is lagging.",
        addressing_policy=AddressingPolicy(),
        approved_facts=(),
        approved_interpretations=(
            "Nutrition is lagging and close any remaining protein gap.",
        ),
        approved_food_actions=(
            ApprovedFoodAction(
                food_claim_key="nutrition.food_suggestion.1",
                canonical_name="Canned Tuna",
                friendly_name="canned tuna",
                macro_reason="remaining protein gap",
                allowed_conditions=("if close any remaining protein gap",),
                serving_display=None,
                serving_allowed=False,
            ),
        ),
    )
    bad_context = _fake_value_context()
    bad_context["approved_nutrition"]["approved_food_suggestions"] = [
        {
            "display_name": "Chicken Breast",
            "macro_gap_addressed": "calorie gap is still open",
            "summary": "Use an approved option like chicken breast to close any remaining protein gap.",
        }
    ]
    packet = build_daily_coach_wide_context_packet(
        user_id=102,
        target_date="2026-06-27",
        scenario_id="aligned_managed",
        brief=bad_brief,
        synthesis=_fake_synthesis(),
        health_state=_fake_health_state(),
        value_context=bad_context,
    )

    prompt = build_wide_context_writer_prompt(packet, "wide_context_practical_coach")
    lowered = prompt.lower()

    assert "approved option" not in lowered
    assert "nutrition is lagging" not in lowered
    assert "protein gap is still open" not in lowered
    assert "remaining protein gap" not in lowered
    assert "close any remaining protein gap" not in lowered
    assert "calorie gap is still open" not in lowered
    assert "protein is still short" in lowered
    assert "calories are still short" in lowered
    assert "canned tuna" in lowered
    assert "chicken breast" in lowered


def test_product_language_scan_flags_required_backend_shaped_phrases() -> None:
    text = " ".join(
        [
            "Nutrition is lagging.",
            "Approved options include tuna.",
            "Use an approved option like chicken.",
            "The protein gap is still open.",
            "Close any remaining protein gap.",
            "The remaining protein gap matters.",
            "The calorie gap is still open.",
            "Today is a green-light day.",
            "Do the planned workout as written.",
            "The planned session and planned workout are ready.",
        ]
    )

    findings = scan_wide_context_product_language(text)
    patterns = {finding["pattern"] for finding in findings}

    assert "Nutrition is lagging" in patterns
    assert "approved options include" in patterns
    assert "approved options" in patterns
    assert "approved option" in patterns
    assert "use an approved option" in patterns
    assert "protein gap is still open" in patterns
    assert "remaining protein gap" in patterns
    assert "close any remaining protein gap" in patterns
    assert "calorie gap is still open" in patterns
    assert "gap is still open" in patterns
    assert "green-light day" in patterns
    assert "do the planned workout as written" in patterns
    assert "planned workout as written" in patterns
    assert "planned session" in patterns
    assert "planned workout" in patterns


def test_product_language_findings_artifact_flags_bad_first_pass_copy(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.build_daily_coach_wide_context_packet",
        lambda **kwargs: build_daily_coach_wide_context_packet(
            user_id=102,
            target_date="2026-06-27",
            scenario_id="aligned_managed",
            brief=_fake_brief(),
            synthesis=_fake_synthesis(),
            health_state=_fake_health_state(),
            value_context=_fake_value_context(),
        ),
    )

    def fake_provider(model: str, prompt: str, timeout: float, env: dict):
        return DailyCoachWideContextProviderCallResult(
            raw_text="Nutrition is lagging. Use an approved option like tuna because the remaining protein gap is open. Today is a green-light day, so do the planned workout as written."
        )

    result = run_daily_coach_wide_context_ceiling_trial_scenario(
        scenario_id="aligned_managed",
        provider="openai",
        model="gpt-5.5",
        variants=["wide_context_practical_coach"],
        allow_live_provider=True,
        environ={"OPENAI_API_KEY": "test-key"},
        provider_generate=fake_provider,
        output_dir=tmp_path,
    )

    write_wide_context_ceiling_trial_artifacts(tmp_path, [result])
    findings = (tmp_path / "product_language_findings.md").read_text(encoding="utf-8")

    assert "Nutrition is lagging" in findings
    assert "approved option" in findings
    assert "remaining protein gap" in findings
    assert "green-light day" in findings
    assert "planned workout as written" in findings
    assert "Total findings:" in findings


def test_pasteback_report_is_terminal_friendly(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.build_daily_coach_wide_context_packet",
        lambda **kwargs: build_daily_coach_wide_context_packet(
            user_id=102,
            target_date="2026-06-27",
            scenario_id="aligned_managed",
            brief=_fake_brief(),
            synthesis=_fake_synthesis(),
            health_state=_fake_health_state(),
            value_context=_fake_value_context(),
        ),
    )

    run_daily_coach_wide_context_ceiling_trial_scenario(
        scenario_id="aligned_managed",
        provider="deterministic",
        variants=["wide_context_practical_coach"],
        output_dir=tmp_path,
    )

    report = (tmp_path / "pasteback_report.md").read_text(encoding="utf-8")

    assert "Run id" in report
    assert "Best variant" in report
    assert "Compact First-Pass Drafts" in report
    assert "Product Language Findings" in report
    assert "Token / Cost Summary" in report
    assert "Known Baseline Drift" in report
    assert BASELINE_DRIFT["test_file"] in report


def test_writer_prompt_presents_foods_as_user_facing_choices() -> None:
    packet = build_daily_coach_wide_context_packet(
        user_id=102,
        target_date="2026-06-27",
        scenario_id="aligned_managed",
        brief=_fake_brief(),
        synthesis=_fake_synthesis(),
        health_state=_fake_health_state(),
        value_context=_fake_value_context(),
    )

    prompt = build_wide_context_writer_prompt(packet, "wide_context_practical_coach")
    lowered = prompt.lower()

    assert "food ideas that may be mentioned if relevant" in lowered
    assert "greek yogurt" in lowered
    assert "approved option" not in lowered
    assert "approved options" not in lowered
    assert "approved options include" not in lowered
    assert "protein is still short" in lowered


def test_pasteback_report_includes_full_exact_key_outputs(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.get_daily_coach_natural_draft_scenario",
        lambda scenario_id: {
            "scenario_id": scenario_id,
            "user_id": 102,
            "target_date": "2026-06-27",
        },
    )
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service.build_daily_coach_wide_context_packet",
        lambda **kwargs: build_daily_coach_wide_context_packet(
            user_id=102,
            target_date="2026-06-27",
            scenario_id="aligned_managed",
            brief=_fake_brief(),
            synthesis=_fake_synthesis(),
            health_state=_fake_health_state(),
            value_context=_fake_value_context(),
        ),
    )

    long_best = "BEST_VARIANT_FULL_TEXT " + "keep every word " * 90
    long_narrow = "CURRENT_NARROW_FULL_TEXT " + "narrow words " * 80
    long_baseline = "DETERMINISTIC_BASELINE_FULL_TEXT " + "baseline words " * 80

    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service._deterministic_baseline_note",
        lambda packet: long_baseline,
    )
    monkeypatch.setattr(
        "services.daily_coach_wide_context_ceiling_trial_service._current_narrow_path_output",
        lambda **kwargs: long_narrow,
    )

    def fake_provider(model: str, prompt: str, timeout: float, env: dict):
        return DailyCoachWideContextProviderCallResult(raw_text=long_best)

    result = run_daily_coach_wide_context_ceiling_trial_scenario(
        scenario_id="aligned_managed",
        provider="openai",
        model="gpt-5.5",
        variants=["current_narrow_path", "wide_context_practical_coach"],
        allow_live_provider=True,
        environ={"OPENAI_API_KEY": "test-key"},
        provider_generate=fake_provider,
        output_dir=tmp_path,
    )

    write_wide_context_ceiling_trial_artifacts(tmp_path, [result])
    report = (tmp_path / "pasteback_report.md").read_text(encoding="utf-8")
    first_pass = (tmp_path / "first_pass_drafts.md").read_text(encoding="utf-8")

    assert "Full Exact Key Outputs" in report
    assert long_baseline in report
    assert long_narrow in report
    assert long_best.strip() in report
    assert long_best.strip() in first_pass
    assert "BEST_VARIANT_FULL_TEXT" in (
        tmp_path / "first_pass_drafts_compact.md"
    ).read_text(encoding="utf-8")
