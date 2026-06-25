from __future__ import annotations

import json
import subprocess
import sys

from models.daily_coach_narrative_models import (
    DAILY_COACH_NARRATIVE_DECISION_FAIL,
    DAILY_COACH_NARRATIVE_DECISION_PASS,
    DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED,
)
from models.daily_next_action_models import DailyNextAction
from services.daily_coach_narrative_context_service import (
    build_daily_coach_narrative_context_from_action,
)
from services.daily_coach_narrative_provider_service import (
    build_daily_coach_narrative_prompt,
    generate_markdown_report,
    run_daily_coach_narrative_candidate,
    run_daily_coach_narrative_offline_qa,
)


def _context(user_id: int = 102):
    action = DailyNextAction(
        action_id="log_food",
        title="Log a meal or snack",
        summary="Add today's food intake so nutrition guidance has enough data.",
        reason="Today's nutrition state is limited until more food data is logged.",
        priority=3,
        workflow_target="nutrition_quick_log",
        severity="info",
        evidence={
            "scenario": "aligned_managed",
            "readiness_level": "High",
            "fatigue_risk": "Low",
            "recovery_checkin_present": True,
            "nutrition_logging_completeness": "likely_incomplete",
            "nutrition_confidence": "Limited",
            "workout_available": True,
            "report_guidance_available": False,
        },
    )
    return build_daily_coach_narrative_context_from_action(
        user_id=user_id,
        action=action,
        context_date="2026-06-19",
    )


def _recovery_context(user_id: int = 101):
    action = DailyNextAction(
        action_id="recovery_training",
        title="Keep training conservative",
        summary="Use lower-risk training while recovery signals are limited.",
        reason="Recovery signals call for a conservative training day.",
        priority=2,
        workflow_target="today_recovery_aware_workout",
        severity="warning",
        evidence={
            "scenario": "recovery_limited",
            "readiness_level": "Low",
            "fatigue_risk": "Elevated",
            "recovery_checkin_present": True,
            "nutrition_logging_completeness": "likely_incomplete",
            "nutrition_confidence": "Limited",
            "workout_available": True,
            "report_guidance_available": False,
        },
    )
    return build_daily_coach_narrative_context_from_action(
        user_id=user_id,
        action=action,
        context_date="2026-06-19",
    )


def _approved_output(context):
    return json.dumps(
        {
            "coach_note": (
                "Log a meal or snack so today's nutrition guidance has enough "
                "information to work from."
            ),
            "key_takeaway": "Today's nutrition state is limited until more food data is logged.",
            "recommended_focus": context.approved_focus,
            "confidence_language": "Keep this limited until more food data is logged.",
            "used_approved_facts": [
                f"Daily next action: {context.next_action_title}",
                f"Daily next action reason: {context.next_action_reason}",
            ],
            "avoided_claims": [
                "No food, exercise, target, recovery, or medical claim was invented."
            ],
        }
    )


def test_prompt_uses_coach_facing_context_without_source_metadata():
    context = _context()

    prompt = build_daily_coach_narrative_prompt(context)

    assert context.next_action_id in prompt
    assert f'FOCUS_TO_COPY_EXACTLY: "{context.approved_focus}"' in prompt
    assert "FACT_STRINGS_FOR_USED_FACTS" in prompt
    assert "copy exactly two strings" in prompt
    assert "Copy them exactly character-for-character" in prompt
    assert "ACTION_FOCUS_HINT" in prompt
    assert "Nutrition confidence: Limited" not in prompt
    assert "source_metadata" not in prompt
    assert "raw_provider" not in prompt
    assert "DailyCoachNarrativeContext" not in prompt
    assert "APPROVED_CONTEXT" not in prompt
    assert "APPROVED_FACTS" not in prompt
    assert "backend" not in prompt.lower()


def test_recovery_prompt_stays_action_focused_and_hides_confidence_fact():
    context = _recovery_context()

    prompt = build_daily_coach_narrative_prompt(context)

    assert 'FOCUS_TO_COPY_EXACTLY: "Keep training conservative"' in prompt
    assert "training/recovery focus" in prompt
    assert "without switching to nutrition logging" in prompt
    assert "Daily next action: Keep training conservative" in prompt
    assert (
        "Daily next action reason: Recovery signals call for a conservative training day."
        in prompt
    )
    assert "Nutrition confidence: Limited" not in prompt


def test_run_candidate_approves_mocked_valid_output():
    context = _context()

    def fake_generate(model_name, prompt, timeout_seconds, ollama_base_url):
        assert model_name == "qwen3:8b"
        assert "SELECTED_ACTION_CONTEXT" in prompt
        assert "FACT_STRINGS_FOR_USED_FACTS" in prompt
        return _approved_output(context)

    result = run_daily_coach_narrative_candidate(
        model_name="qwen3:8b",
        context=context,
        generate=fake_generate,
        timeout_seconds=1.0,
    )

    assert result.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED
    assert result.overall_decision == DAILY_COACH_NARRATIVE_DECISION_PASS
    assert result.representative_safe_excerpt is not None


def test_run_candidate_falls_back_on_malformed_output():
    context = _context()

    def fake_generate(model_name, prompt, timeout_seconds, ollama_base_url):
        return "Here is the JSON: {}"

    result = run_daily_coach_narrative_candidate(
        model_name="qwen2.5:3b",
        context=context,
        generate=fake_generate,
        timeout_seconds=1.0,
    )

    assert result.overall_decision == DAILY_COACH_NARRATIVE_DECISION_FAIL
    assert result.validation_status == "rejected"
    assert result.representative_rejection_reason is not None


def test_run_offline_qa_builds_model_context_matrix_with_fake_provider():
    contexts = [_context(101), _context(102)]

    def fake_generate(model_name, prompt, timeout_seconds, ollama_base_url):
        user_context = contexts[0] if "user_id: 101" in prompt else contexts[1]
        return _approved_output(user_context)

    results = run_daily_coach_narrative_offline_qa(
        model_names=["qwen3:8b", "qwen2.5:3b"],
        contexts=contexts,
        generate=fake_generate,
        timeout_seconds=1.0,
    )

    assert len(results) == 4
    assert all(
        result.overall_decision == DAILY_COACH_NARRATIVE_DECISION_PASS
        for result in results
    )


def test_markdown_report_contains_summary_and_boundary_reminder():
    context = _context()

    def fake_generate(model_name, prompt, timeout_seconds, ollama_base_url):
        return _approved_output(context)

    result = run_daily_coach_narrative_candidate(
        model_name="qwen3:8b",
        context=context,
        generate=fake_generate,
        timeout_seconds=1.0,
    )

    report = generate_markdown_report([result], contexts=[context])

    assert "Daily Coach Narrative Offline Provider QA v1 Results" in report
    assert "Model summary" in report
    assert "Context matrix" in report
    assert "No model is promoted" in report


def test_cli_help_runs_from_repo_root_without_pythonpath():
    completed = subprocess.run(
        [sys.executable, "tools/daily_coach_narrative_offline_qa.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Daily Coach Narrative provider QA" in completed.stdout


def test_provider_prompt_includes_selected_date_reason_codes_for_qa_context():
    from services.daily_coach_narrative_context_service import (
        build_daily_coach_narrative_qa_preview_context,
    )

    context = build_daily_coach_narrative_qa_preview_context(
        102,
        selected_date="2026-06-06",
        lookback_days=1,
    )

    prompt = build_daily_coach_narrative_prompt(context)

    assert "Selected date: 2026-06-06" in prompt
    assert "Daily Narrative reason codes:" in prompt
    assert "Daily next action reason:" in prompt
