from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping

from models.daily_coach_natural_draft_audit_models import (
    ApprovedCoachBrief,
    ClaimAuditResult,
    NaturalCoachDraft,
    RepairAttemptResult,
)
from services.daily_coach_claim_audit_service import audit_extracted_draft_claims
from services.daily_coach_claim_extraction_service import (
    extract_claims_from_natural_draft,
)
from services.daily_coach_food_action_language_service import humanize_food_action_text
from services.daily_coach_natural_draft_service import parse_natural_coach_draft
from services.daily_coach_value_narrative_service import (
    OLLAMA_BASE_URL_ENV,
    OPENAI_API_KEY_ENV,
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
    call_direct_ollama_daily_coach_narrative,
    call_openai_daily_coach_narrative,
)

DAILY_COACH_REPAIR_PROVIDER_ENV = "DAILY_COACH_REPAIR_PROVIDER"
DAILY_COACH_REPAIR_MODEL_ENV = "DAILY_COACH_REPAIR_MODEL"


def repair_natural_coach_draft_once(
    *,
    draft: NaturalCoachDraft,
    brief: ApprovedCoachBrief,
    audit_result: ClaimAuditResult,
    provider: str,
    model: str | None = None,
    allow_live_provider: bool = False,
    environ: Mapping[str, str] | None = None,
) -> RepairAttemptResult:
    if not audit_result.repairable:
        return RepairAttemptResult(
            attempted=False,
            provider=provider,  # type: ignore[arg-type]
            model=model,
            fallback_reason="audit_not_repairable",
        )
    env = dict(os.environ if environ is None else environ)
    repair_provider = (
        (env.get(DAILY_COACH_REPAIR_PROVIDER_ENV) or provider).strip().lower()
    )
    repair_model = env.get(DAILY_COACH_REPAIR_MODEL_ENV) or model
    try:
        repaired = (
            _deterministic_repair(draft, brief, audit_result)
            if repair_provider == PROVIDER_DETERMINISTIC
            else _provider_repair(
                draft,
                brief,
                audit_result,
                provider=repair_provider,
                model=repair_model,
                allow_live_provider=allow_live_provider,
                env=env,
            )
        )
    except Exception as exc:  # noqa: BLE001 - repair failure should fall back safely
        return RepairAttemptResult(
            attempted=True,
            provider=repair_provider,  # type: ignore[arg-type]
            model=repair_model,
            passed=False,
            fallback_reason=f"repair_failed:{_safe_error(exc)}",
        )
    claims = extract_claims_from_natural_draft(repaired, brief)
    post_audit = audit_extracted_draft_claims(claims, brief)
    return RepairAttemptResult(
        attempted=True,
        provider=repair_provider,  # type: ignore[arg-type]
        model=repair_model,
        passed=post_audit.passed,
        findings_after_repair=post_audit.findings,
        final_copy=repaired if post_audit.passed else None,
        fallback_reason=None if post_audit.passed else "repair_audit_failed",
    )


def build_draft_repair_prompt(
    *,
    draft: NaturalCoachDraft,
    brief: ApprovedCoachBrief,
    audit_result: ClaimAuditResult,
) -> str:
    findings = [finding.to_dict() for finding in audit_result.findings]
    safe_brief = brief.to_dict()
    safe_brief.pop("claim_registry", None)
    return (
        "Rewrite only to fix the audit findings. Do not add new facts.\n"
        "Do not add foods, serving sizes, timing, causality, medical claims, or new user data.\n"
        "Keep the same useful coaching intent. Return one JSON object with exactly headline and body.\n\n"
        f"DRAFT:\n{json.dumps(draft.to_dict(), indent=2, sort_keys=True)}\n\n"
        f"AUDIT_FINDINGS:\n{json.dumps(findings, indent=2, sort_keys=True)}\n\n"
        f"APPROVED_COACH_BRIEF:\n{json.dumps(safe_brief, indent=2, sort_keys=True, default=str)}"
    )


def _deterministic_repair(
    draft: NaturalCoachDraft, brief: ApprovedCoachBrief, audit_result: ClaimAuditResult
) -> NaturalCoachDraft:
    headline = draft.headline
    body = draft.body
    for finding in audit_result.findings:
        if finding.finding_type == "addressing_policy_violation":
            headline = re.sub(r"\bDustin\b,?\s*", "", headline, flags=re.I).strip()
            body = re.sub(r"\bDustin\b,?\s*", "", body, flags=re.I).strip()
        elif finding.finding_type == "canonical_food_label_visible":
            for action in brief.approved_food_actions:
                if action.canonical_name and action.friendly_name:
                    headline = headline.replace(
                        action.canonical_name, action.friendly_name
                    )
                    body = body.replace(action.canonical_name, action.friendly_name)
        elif finding.finding_type in {
            "unsupported_causal_claim",
            "invented_timing_claim",
            "unsupported_macro_status_claim",
            "unsupported_training_claim",
            "unsupported_recovery_claim",
            "unsupported_recovery_overclaim",
        }:
            body = _remove_sentence_containing(body, finding.text_span)
        elif finding.finding_type == "unsupported_judgment_claim":
            body = _remove_sentence_containing(body, finding.text_span)
    if not headline:
        headline = "Daily Coach"
    if not body:
        body = brief.today_intent or "Keep the next action small and easy to verify."
    body = humanize_food_action_text(body, brief)
    return NaturalCoachDraft(
        headline=headline,
        body=body,
        provider=PROVIDER_DETERMINISTIC,
        model=None,
    )


def _provider_repair(
    draft: NaturalCoachDraft,
    brief: ApprovedCoachBrief,
    audit_result: ClaimAuditResult,
    *,
    provider: str,
    model: str | None,
    allow_live_provider: bool,
    env: Mapping[str, str],
) -> NaturalCoachDraft:
    if not allow_live_provider:
        raise ValueError("live_provider_not_allowed")
    selected_model = model or "gpt-5.5"
    prompt = build_draft_repair_prompt(
        draft=draft, brief=brief, audit_result=audit_result
    )
    if provider == PROVIDER_OPENAI:
        if not env.get(OPENAI_API_KEY_ENV):
            raise ValueError("missing_api_key")
        raw = call_openai_daily_coach_narrative(
            selected_model,
            prompt,
            30.0,
            api_key=env.get(OPENAI_API_KEY_ENV),
        )
    elif provider == PROVIDER_DIRECT_OLLAMA:
        if not env.get(OLLAMA_BASE_URL_ENV):
            raise ValueError("missing_OLLAMA_BASE_URL")
        raw = call_direct_ollama_daily_coach_narrative(
            selected_model,
            prompt,
            30.0,
            ollama_base_url=env.get(OLLAMA_BASE_URL_ENV),
        )
    else:
        raise ValueError(f"unsupported_provider:{provider}")
    return parse_natural_coach_draft(raw, provider=provider, model=selected_model)


def _remove_sentence_containing(text: str, span: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    normalized_span = span.lower()
    kept = [
        sentence for sentence in sentences if normalized_span not in sentence.lower()
    ]
    return " ".join(sentence.strip() for sentence in kept if sentence.strip())


def _safe_error(exc: Exception) -> str:
    return re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", str(exc).replace("\n", " ")[:180])
