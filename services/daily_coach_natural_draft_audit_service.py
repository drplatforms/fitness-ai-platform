from __future__ import annotations

import csv
import json
import os
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from models.daily_coach_natural_draft_audit_models import (
    AddressingPolicy,
    ApprovedCoachBrief,
    ClaimAuditResult,
    NaturalCoachDraft,
    NaturalDraftAuditRunResult,
    ProductVoiceAuditResult,
    RepairAttemptResult,
)
from services.daily_coach_approved_brief_service import build_approved_coach_brief
from services.daily_coach_claim_audit_service import audit_extracted_draft_claims
from services.daily_coach_claim_extraction_service import (
    extract_claims_from_natural_draft,
)
from services.daily_coach_draft_repair_service import repair_natural_coach_draft_once
from services.daily_coach_food_action_language_service import humanize_food_action_text
from services.daily_coach_natural_draft_service import write_natural_coach_draft
from services.daily_coach_product_voice_audit_service import (
    audit_daily_coach_product_voice,
)
from services.daily_coach_prompt_lab_service import (
    list_daily_coach_prompt_lab_scenarios,
)
from services.daily_coach_value_narrative_service import PROVIDER_DETERMINISTIC

DEFAULT_NATURAL_DRAFT_AUDIT_OUTPUT_DIR = (
    "docs/provider_trials/daily_coach_natural_draft_product_voice_audit_v2"
)
SECRET_PATTERNS = ("bearer ", "openai_api_key", "api key", "sk-")
SUPPORTED_NATURAL_DRAFT_PROVIDERS = ("deterministic", "direct_ollama", "openai")


def list_daily_coach_natural_draft_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": scenario.scenario_id,
            "user_id": scenario.user_id,
            "target_date": scenario.target_date,
            "purpose": scenario.purpose,
            "expected_evaluation_focus": list(scenario.expected_evaluation_focus),
        }
        for scenario in list_daily_coach_prompt_lab_scenarios()
        if scenario.scenario_id
        in {
            "rich_nutrition_training_recovery",
            "stable_comparison",
            "training_present_nutrition_missing",
            "nutrition_present_training_missing",
            "data_quality_limited",
            "recovery_limited",
        }
    ]


def get_daily_coach_natural_draft_scenario(scenario_id: str) -> dict[str, Any]:
    for scenario in list_daily_coach_natural_draft_scenarios():
        if scenario["scenario_id"] == scenario_id:
            return scenario
    valid = ", ".join(
        item["scenario_id"] for item in list_daily_coach_natural_draft_scenarios()
    )
    raise ValueError(f"Unknown natural draft scenario: {scenario_id}. Valid: {valid}")


def run_daily_coach_natural_draft_audit_scenario(
    *,
    scenario_id: str,
    provider: str,
    model: str | None = None,
    allow_live_provider: bool = False,
    output_dir: Path | None = None,
    environ: Mapping[str, str] | None = None,
    brief: ApprovedCoachBrief | None = None,
    draft: NaturalCoachDraft | None = None,
) -> NaturalDraftAuditRunResult:
    scenario = get_daily_coach_natural_draft_scenario(scenario_id)
    env = dict(os.environ if environ is None else environ)
    resolved_provider = _normalize_provider(provider)
    if resolved_provider not in SUPPORTED_NATURAL_DRAFT_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    if resolved_provider != PROVIDER_DETERMINISTIC and not allow_live_provider:
        result = _skipped_result(
            scenario, resolved_provider, model, "live_provider_not_allowed"
        )
        if output_dir:
            write_natural_draft_audit_artifacts(
                output_dir,
                [result],
                config={
                    "scenario_id": scenario_id,
                    "provider": resolved_provider,
                    "model": model,
                    "milestone": "daily_coach_natural_draft_product_voice_audit_v2",
                },
            )
        return result

    try:
        resolved_brief = brief or build_approved_coach_brief(
            user_id=int(scenario["user_id"]),
            target_date=str(scenario["target_date"]),
            scenario_id=scenario_id,
            addressing_policy=AddressingPolicy(),
        )
        deterministic_fallback = _humanized_fallback(resolved_brief)
        fallback_product_audit = audit_daily_coach_product_voice(
            deterministic_fallback, resolved_brief, mode="approval"
        )
    except Exception as exc:  # noqa: BLE001 - dev runner records setup failure safely
        result = _skipped_result(
            scenario, resolved_provider, model, f"brief_build_failed:{_safe_error(exc)}"
        )
        if output_dir:
            write_natural_draft_audit_artifacts(
                output_dir,
                [result],
                config={
                    "scenario_id": scenario_id,
                    "provider": resolved_provider,
                    "model": model,
                    "milestone": "daily_coach_natural_draft_product_voice_audit_v2",
                },
            )
        return result

    try:
        resolved_draft = draft or write_natural_coach_draft(
            resolved_brief,
            provider=resolved_provider,
            model=model,
            allow_live_provider=allow_live_provider,
            environ=env,
        )
    except Exception as exc:  # noqa: BLE001 - dev runner records failure as fallback
        result = _skipped_result(scenario, resolved_provider, model, _safe_error(exc))
        result = _copy_with_fallback(
            result, deterministic_fallback, fallback_product_audit
        )
        if output_dir:
            write_natural_draft_audit_artifacts(
                output_dir,
                [result],
                config={
                    "scenario_id": scenario_id,
                    "provider": resolved_provider,
                    "model": model,
                    "milestone": "daily_coach_natural_draft_product_voice_audit_v2",
                },
            )
        return result

    # First-pass draft is preserved exactly in result.draft before any audit/repair/fallback.
    extracted = tuple(extract_claims_from_natural_draft(resolved_draft, resolved_brief))
    audit = audit_extracted_draft_claims(extracted, resolved_brief)
    product_exploration = audit_daily_coach_product_voice(
        resolved_draft, resolved_brief, mode="exploration"
    )
    product_approval = audit_daily_coach_product_voice(
        resolved_draft, resolved_brief, mode="approval"
    )
    repair_result = RepairAttemptResult(
        attempted=False,
        provider=resolved_provider,  # type: ignore[arg-type]
        model=model,
    )
    repaired_product_audit: ProductVoiceAuditResult | None = None
    final_copy: NaturalCoachDraft | None = None
    final_source = "deterministic_fallback"

    if audit.passed and product_approval.passed:
        final_copy = resolved_draft
        final_source = "draft_approved"
    elif not audit.passed and audit.repairable:
        repair_result = repair_natural_coach_draft_once(
            draft=resolved_draft,
            brief=resolved_brief,
            audit_result=audit,
            provider=resolved_provider,
            model=model,
            allow_live_provider=allow_live_provider,
            environ=env,
        )
        if repair_result.passed and repair_result.final_copy:
            repaired_product_audit = audit_daily_coach_product_voice(
                repair_result.final_copy, resolved_brief, mode="approval"
            )
            if repaired_product_audit.passed:
                final_copy = repair_result.final_copy
                final_source = "repair_approved"

    if final_copy is None:
        final_copy = deterministic_fallback
        final_source = "deterministic_fallback"

    reviewer_conclusion = _reviewer_conclusion(
        audit=audit,
        product_audit=product_approval,
        repair_result=repair_result,
        repaired_product_audit=repaired_product_audit,
        fallback_product_audit=fallback_product_audit,
        final_source=final_source,
    )
    result = NaturalDraftAuditRunResult(
        scenario_id=scenario_id,
        user_id=int(scenario["user_id"]),
        date=str(scenario["target_date"]),
        provider=resolved_provider,  # type: ignore[arg-type]
        model=model,
        draft=resolved_draft,
        extracted_claims=extracted,
        audit_result=audit,
        repair_result=repair_result,
        final_copy=final_copy,
        final_source=final_source,  # type: ignore[arg-type]
        deterministic_fallback=deterministic_fallback,
        product_voice_audit_result=product_approval,
        repaired_product_voice_audit_result=repaired_product_audit,
        fallback_product_voice_audit_result=fallback_product_audit,
        reviewer_conclusion=reviewer_conclusion,  # type: ignore[arg-type]
        runtime_metadata={
            "developer_only": True,
            "normal_today_unchanged": True,
            "allow_live_provider": allow_live_provider,
            "gate_modes": ["exploration", "audit", "repair", "approval"],
            "first_pass_model_draft_captured_before_audit": True,
            "claim_audit_passed_initially": audit.passed,
            "product_voice_audit_passed_initially": product_approval.passed,
            "first_pass_product_voice_exploration": product_exploration.to_dict(),
            "repair_attempted": repair_result.attempted,
            "deterministic_fallback_is_floor_not_goal": True,
        },
    )
    _assert_result_sanitized(result)
    if output_dir:
        write_natural_draft_audit_artifacts(
            output_dir,
            [result],
            config={
                "scenario_id": scenario_id,
                "provider": resolved_provider,
                "model": model,
                "milestone": "daily_coach_natural_draft_product_voice_audit_v2",
            },
        )
    return result


def run_daily_coach_natural_draft_audit_matrix(
    *,
    scenarios: Sequence[str],
    provider: str,
    output_dir: Path,
    model: str | None = None,
    allow_live_provider: bool = False,
    environ: Mapping[str, str] | None = None,
) -> list[NaturalDraftAuditRunResult]:
    selected = list(scenarios) or ["rich_nutrition_training_recovery"]
    results = [
        run_daily_coach_natural_draft_audit_scenario(
            scenario_id=scenario_id,
            provider=provider,
            model=model,
            allow_live_provider=allow_live_provider,
            environ=environ,
        )
        for scenario_id in selected
    ]
    write_natural_draft_audit_artifacts(
        output_dir,
        results,
        config={
            "run_id": _build_run_id(provider),
            "scenarios": selected,
            "provider": provider,
            "model": model,
            "allow_live_provider": allow_live_provider,
            "milestone": "daily_coach_natural_draft_product_voice_audit_v2",
        },
    )
    return results


def write_natural_draft_audit_artifacts(
    output_dir: Path,
    results: Sequence[NaturalDraftAuditRunResult],
    *,
    config: Mapping[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run_config.json").write_text(
        json.dumps(dict(config), indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    (output_dir / "approved_coach_brief_summary.md").write_text(
        _render_brief_summary(results), encoding="utf-8"
    )
    (output_dir / "first_pass_model_draft_before_audit.md").write_text(
        _render_first_pass_drafts(results), encoding="utf-8"
    )
    (output_dir / "natural_draft_output.md").write_text(
        _render_drafts(results), encoding="utf-8"
    )
    (output_dir / "claim_extraction_summary.json").write_text(
        json.dumps(
            [
                {
                    "scenario_id": result.scenario_id,
                    "claims": [claim.to_dict() for claim in result.extracted_claims],
                }
                for result in results
            ],
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (output_dir / "claim_audit_summary.md").write_text(
        _render_audit_summary(results), encoding="utf-8"
    )
    (output_dir / "product_voice_audit_summary.md").write_text(
        _render_product_voice_audit_summary(results), encoding="utf-8"
    )
    (output_dir / "repair_summary.md").write_text(
        _render_repair_summary(results), encoding="utf-8"
    )
    (output_dir / "repair_delta_summary.md").write_text(
        _render_repair_delta_summary(results), encoding="utf-8"
    )
    (output_dir / "humanized_fallback_summary.md").write_text(
        _render_humanized_fallback_summary(results), encoding="utf-8"
    )
    (output_dir / "side_by_side_output_comparison.md").write_text(
        _render_side_by_side_comparison(results), encoding="utf-8"
    )
    (output_dir / "reviewer_conclusion.md").write_text(
        _render_reviewer_conclusion(results), encoding="utf-8"
    )
    (output_dir / "final_approved_copy.md").write_text(
        _render_final_copy(results), encoding="utf-8"
    )
    _write_comparison_csv(output_dir / "comparison_table.csv", results)
    (output_dir / "comparison_table.md").write_text(
        _render_comparison_table(results), encoding="utf-8"
    )
    (output_dir / "validation_summary.md").write_text(
        _render_validation_summary(results), encoding="utf-8"
    )
    (output_dir / "scoring_template.md").write_text(
        _render_scoring_template(results), encoding="utf-8"
    )
    serialized = "\n".join(
        path.read_text(encoding="utf-8")
        for path in output_dir.iterdir()
        if path.is_file()
    )
    if _contains_secretish_text(serialized):
        raise ValueError("Natural Draft Audit artifacts contain secret-like text.")
    if "raw_provider_output" in serialized:
        raise ValueError(
            "Natural Draft Audit default artifacts contain raw provider output."
        )


def _skipped_result(
    scenario: Mapping[str, Any], provider: str, model: str | None, reason: str
) -> NaturalDraftAuditRunResult:
    audit = ClaimAuditResult(
        passed=False,
        repairable=False,
        final_decision="fallback_required",
    )
    repair = RepairAttemptResult(
        attempted=False,
        provider=provider,  # type: ignore[arg-type]
        model=model,
        fallback_reason=reason,
    )
    return NaturalDraftAuditRunResult(
        scenario_id=str(scenario["scenario_id"]),
        user_id=int(scenario["user_id"]),
        date=str(scenario["target_date"]),
        provider=provider,  # type: ignore[arg-type]
        model=model,
        draft=None,
        extracted_claims=(),
        audit_result=audit,
        repair_result=repair,
        final_copy=None,
        final_source="skipped",
        reviewer_conclusion="model_failure",
        runtime_metadata={"skipped": True, "skip_reason": reason},
    )


def _copy_with_fallback(
    result: NaturalDraftAuditRunResult,
    fallback: NaturalCoachDraft,
    fallback_audit: ProductVoiceAuditResult,
) -> NaturalDraftAuditRunResult:
    return NaturalDraftAuditRunResult(
        scenario_id=result.scenario_id,
        user_id=result.user_id,
        date=result.date,
        provider=result.provider,
        model=result.model,
        draft=result.draft,
        extracted_claims=result.extracted_claims,
        audit_result=result.audit_result,
        repair_result=result.repair_result,
        final_copy=fallback,
        final_source="deterministic_fallback",
        deterministic_fallback=fallback,
        fallback_product_voice_audit_result=fallback_audit,
        reviewer_conclusion="model_failure",
        runtime_metadata=result.runtime_metadata,
    )


def _humanized_fallback(brief: ApprovedCoachBrief) -> NaturalCoachDraft:
    fallback = write_natural_coach_draft(brief, provider=PROVIDER_DETERMINISTIC)
    return NaturalCoachDraft(
        headline=fallback.headline,
        body=humanize_food_action_text(fallback.body, brief),
        provider=PROVIDER_DETERMINISTIC,
        model=None,
    )


def _render_brief_summary(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = [
        "# Approved Coach Brief Summary",
        "",
        "This artifact summarizes scenario/date/provider only. It does not include raw DB rows.",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"## {result.scenario_id}",
                f"User: {result.user_id}",
                f"Date: {result.date}",
                f"Provider: {result.provider}",
                f"Final source: {result.final_source}",
                f"Reviewer conclusion: {result.reviewer_conclusion}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_first_pass_drafts(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = [
        "# First-Pass Model Draft Before Audit",
        "",
        "This preserves the returned headline/body before claim audit, product voice audit, repair, fallback, or cleanup.",
        "Raw provider envelopes are not included.",
        "",
    ]
    for result in results:
        lines.append(f"## {result.scenario_id}")
        if result.draft:
            lines.extend([f"### {result.draft.headline}", "", result.draft.body])
        else:
            lines.append("(draft skipped or unavailable)")
        lines.append("")
    return "\n".join(lines)


def _render_drafts(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = [
        "# Natural Draft Output",
        "",
        "Raw provider output is not included in this default artifact.",
        "",
    ]
    for result in results:
        lines.extend(
            [f"## {result.scenario_id}", f"Final source: {result.final_source}"]
        )
        if result.draft:
            lines.extend(
                [f"Draft headline: {result.draft.headline}", "", result.draft.body]
            )
        else:
            lines.append("(draft skipped or unavailable)")
        lines.append("")
    return "\n".join(lines)


def _render_audit_summary(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = ["# Claim Audit Summary", ""]
    for result in results:
        lines.extend(
            [
                f"## {result.scenario_id}",
                f"Passed: {result.audit_result.passed}",
                f"Decision: {result.audit_result.final_decision}",
                f"Findings: {len(result.audit_result.findings)}",
            ]
        )
        for finding in result.audit_result.findings:
            lines.append(
                f"- {finding.finding_type}: {finding.reason} Repairable={finding.repairable}"
            )
        lines.append("")
    return "\n".join(lines)


def _render_product_voice_audit_summary(
    results: Sequence[NaturalDraftAuditRunResult],
) -> str:
    lines = ["# Product Voice Audit Summary", ""]
    for result in results:
        audit = result.product_voice_audit_result
        lines.append(f"## {result.scenario_id}")
        if not audit:
            lines.extend(["Product voice audit: unavailable", ""])
            continue
        lines.extend(
            [
                f"Mode: {audit.mode}",
                f"Passed: {audit.passed}",
                f"Decision: {audit.decision}",
                f"Product readiness: {audit.product_readiness_score}",
                "",
                "### Scores",
            ]
        )
        for score in audit.scores:
            lines.append(f"- {score.dimension}: {score.score} — {score.reason}")
        lines.append("")
        lines.append("### Findings")
        if audit.findings:
            for finding in audit.findings:
                lines.append(
                    f"- {finding.finding_type} ({finding.severity}): {finding.text_span} — {finding.reason}"
                )
        else:
            lines.append("- none")
        lines.append("")
    return "\n".join(lines)


def _render_repair_summary(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = ["# Repair Summary", ""]
    for result in results:
        repair = result.repair_result
        lines.extend(
            [
                f"## {result.scenario_id}",
                f"Attempted: {repair.attempted}",
                f"Passed claim audit after repair: {repair.passed}",
                f"Passed product voice after repair: {_bool_or_na(result.repaired_product_voice_audit_result.passed if result.repaired_product_voice_audit_result else None)}",
                f"Fallback reason: {repair.fallback_reason or 'none'}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_repair_delta_summary(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = ["# Repair Delta Summary", ""]
    for result in results:
        lines.append(f"## {result.scenario_id}")
        if not result.repair_result.attempted:
            lines.extend(["Repair attempted: False", ""])
            continue
        before = _draft_text(result.draft)
        after = _draft_text(result.repair_result.final_copy)
        lines.extend(
            [
                "Repair attempted: True",
                f"Changed: {before != after}",
                "Reason: repair only listed claim-audit findings; product voice is audited separately.",
                f"Product voice after repair passed: {_bool_or_na(result.repaired_product_voice_audit_result.passed if result.repaired_product_voice_audit_result else None)}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_humanized_fallback_summary(
    results: Sequence[NaturalDraftAuditRunResult],
) -> str:
    lines = ["# Humanized Fallback Summary", ""]
    for result in results:
        lines.append(f"## {result.scenario_id}")
        fallback = result.deterministic_fallback
        fallback_audit = result.fallback_product_voice_audit_result
        lines.extend(
            [
                f"Fallback used: {result.final_source == 'deterministic_fallback'}",
                f"Why fallback was used: {_fallback_reason(result)}",
                f"Fallback passed Product Voice Audit: {_bool_or_na(fallback_audit.passed if fallback_audit else None)}",
            ]
        )
        if fallback:
            lines.extend([f"### {fallback.headline}", "", fallback.body])
        lines.append("")
    return "\n".join(lines)


def _render_side_by_side_comparison(
    results: Sequence[NaturalDraftAuditRunResult],
) -> str:
    lines = ["# Side-by-Side Output Comparison", ""]
    for result in results:
        lines.append(f"## {result.scenario_id}")
        lines.extend(
            [
                "### Deterministic fallback",
                _draft_text(result.deterministic_fallback),
                "",
                "### GPT-5.5/provider first-pass natural draft before audit",
                _draft_text(result.draft),
                "",
                "### Audited/repaired draft",
                _draft_text(result.repair_result.final_copy),
                "",
                "### Final approved copy",
                _draft_text(result.final_copy),
                "",
                f"Final source: {result.final_source}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_reviewer_conclusion(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = ["# Reviewer Conclusion", ""]
    for result in results:
        first_score = (
            result.product_voice_audit_result.product_readiness_score
            if result.product_voice_audit_result
            else "n/a"
        )
        fallback_score = (
            result.fallback_product_voice_audit_result.product_readiness_score
            if result.fallback_product_voice_audit_result
            else "n/a"
        )
        lines.extend(
            [
                f"## {result.scenario_id}",
                f"Conclusion: {result.reviewer_conclusion}",
                f"First-pass product readiness: {first_score}",
                f"Fallback product readiness: {fallback_score}",
                f"Initial claim audit passed: {result.audit_result.passed}",
                f"Initial product voice audit passed: {_bool_or_na(result.product_voice_audit_result.passed if result.product_voice_audit_result else None)}",
                f"Repair attempted: {result.repair_result.attempted}",
                f"Final source: {result.final_source}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_final_copy(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = ["# Final Approved Copy", ""]
    for result in results:
        lines.extend([f"## {result.scenario_id}", f"Source: {result.final_source}"])
        if result.final_copy:
            lines.extend(
                [f"### {result.final_copy.headline}", "", result.final_copy.body]
            )
        else:
            lines.append("(no final copy)")
        lines.append("")
    return "\n".join(lines)


def _write_comparison_csv(
    path: Path, results: Sequence[NaturalDraftAuditRunResult]
) -> None:
    rows = [_comparison_row(result) for result in results]
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _render_comparison_table(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = [
        "# Natural Draft Product Voice Audit Comparison Table",
        "",
        "| Scenario | Provider | Final source | Claim audit | Product voice | Fallback voice | Repair attempted | Reviewer conclusion |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| {result.scenario_id} | {result.provider} | {result.final_source} | {result.audit_result.passed} | {_bool_or_na(result.product_voice_audit_result.passed if result.product_voice_audit_result else None)} | {_bool_or_na(result.fallback_product_voice_audit_result.passed if result.fallback_product_voice_audit_result else None)} | {result.repair_result.attempted} | {result.reviewer_conclusion} |"
        )
    return "\n".join(lines) + "\n"


def _render_validation_summary(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = ["# Natural Draft Product Voice Audit Validation Summary", ""]
    for result in results:
        voice = result.product_voice_audit_result
        lines.extend(
            [
                f"## {result.scenario_id}",
                f"Developer only: {result.runtime_metadata.get('developer_only', False)}",
                f"Normal Today unchanged: {result.runtime_metadata.get('normal_today_unchanged', True)}",
                f"First pass captured before audit: {result.runtime_metadata.get('first_pass_model_draft_captured_before_audit', False)}",
                f"Gate modes: {', '.join(result.runtime_metadata.get('gate_modes', []))}",
                f"Unsupported claims: {result.audit_result.unsupported_claim_count}",
                f"Food claims: {result.audit_result.food_claim_count}",
                f"Causal claims: {result.audit_result.causal_claim_count}",
                f"Addressing violations: {result.audit_result.addressing_violation_count}",
                f"Product voice findings: {len(voice.findings) if voice else 0}",
                f"Reviewer conclusion: {result.reviewer_conclusion}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_scoring_template(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = [
        "# Natural Draft + Product Voice Audit Scoring Template",
        "",
        "Score product voice after technical validation. Grounding must remain 5.",
        "",
        "| Scenario | Provider | First-pass better than fallback? | Plainspoken voice | Scenario specificity | Action clarity | Food naturalness | Training clarity | Recovery clarity | Logic coherence | Grounding | Product readiness | Notes |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| {result.scenario_id} | {result.provider} |  |  |  |  |  |  |  |  |  |  |  |"
        )
    return "\n".join(lines) + "\n"


def _comparison_row(result: NaturalDraftAuditRunResult) -> dict[str, Any]:
    voice = result.product_voice_audit_result
    fallback_voice = result.fallback_product_voice_audit_result
    return {
        "scenario_id": result.scenario_id,
        "user_id": result.user_id,
        "date": result.date,
        "provider": result.provider,
        "model": result.model or "",
        "final_source": result.final_source,
        "initial_claim_audit_passed": result.audit_result.passed,
        "initial_product_voice_passed": voice.passed if voice else "",
        "initial_product_readiness_score": voice.product_readiness_score
        if voice
        else "",
        "fallback_product_voice_passed": fallback_voice.passed
        if fallback_voice
        else "",
        "fallback_product_readiness_score": fallback_voice.product_readiness_score
        if fallback_voice
        else "",
        "repair_attempted": result.repair_result.attempted,
        "repair_passed": result.repair_result.passed,
        "finding_count": len(result.audit_result.findings),
        "product_voice_finding_count": len(voice.findings) if voice else 0,
        "unsupported_claim_count": result.audit_result.unsupported_claim_count,
        "causal_claim_count": result.audit_result.causal_claim_count,
        "addressing_violation_count": result.audit_result.addressing_violation_count,
        "reviewer_conclusion": result.reviewer_conclusion,
    }


def _normalize_provider(provider: str) -> str:
    return provider.strip().lower()


def _build_run_id(provider: str) -> str:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    return f"daily_coach_natural_draft_product_voice_audit_v2_{provider}_{timestamp.replace(':', '').replace('+', 'z')}"


def _contains_secretish_text(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in SECRET_PATTERNS)


def _assert_result_sanitized(result: NaturalDraftAuditRunResult) -> None:
    serialized = json.dumps(result.to_dict(), default=str).lower()
    if "raw_provider_output" in serialized:
        raise ValueError("Natural Draft Audit result contains raw provider output.")
    if _contains_secretish_text(serialized):
        raise ValueError("Natural Draft Audit result contains secret-like text.")


def _safe_error(exc: Exception) -> str:
    return re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", str(exc).replace("\n", " ")[:180])


def _draft_text(draft: NaturalCoachDraft | None) -> str:
    if not draft:
        return "(unavailable)"
    return f"### {draft.headline}\n\n{draft.body}"


def _bool_or_na(value: bool | None) -> str:
    if value is None:
        return "n/a"
    return "True" if value else "False"


def _fallback_reason(result: NaturalDraftAuditRunResult) -> str:
    if result.final_source != "deterministic_fallback":
        return "not used"
    if not result.audit_result.passed:
        return "claim audit failed or repair failed"
    if (
        result.product_voice_audit_result
        and not result.product_voice_audit_result.passed
    ):
        return "product voice audit failed"
    return "fallback selected by final approval"


def _reviewer_conclusion(
    *,
    audit: ClaimAuditResult,
    product_audit: ProductVoiceAuditResult,
    repair_result: RepairAttemptResult,
    repaired_product_audit: ProductVoiceAuditResult | None,
    fallback_product_audit: ProductVoiceAuditResult,
    final_source: str,
) -> str:
    if final_source != "deterministic_fallback":
        return "success"
    if not fallback_product_audit.passed:
        return "fallback_failure"
    if not audit.passed and not audit.repairable:
        return "audit_failure"
    if repair_result.attempted and not repair_result.passed:
        return "repair_failure"
    if repaired_product_audit is not None and not repaired_product_audit.passed:
        return "repair_failure"
    if not product_audit.passed:
        return "product_voice_failure"
    return "fallback_failure"
