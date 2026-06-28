from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

from models.daily_coach_natural_draft_audit_models import (
    ApprovedCoachBrief,
    NaturalCoachDraft,
)
from services.daily_coach_food_action_language_service import humanize_food_action_text
from services.daily_coach_value_narrative_service import (
    DAILY_COACH_VALUE_NARRATIVE_PROVIDER_ENV,
    OLLAMA_BASE_URL_ENV,
    OPENAI_API_KEY_ENV,
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
    call_direct_ollama_daily_coach_narrative,
    call_openai_daily_coach_narrative,
)

DEFAULT_NATURAL_DRAFT_PROVIDER_ENV = "DAILY_COACH_NATURAL_DRAFT_PROVIDER"
DEFAULT_NATURAL_DRAFT_MODEL_ENV = "DAILY_COACH_NATURAL_DRAFT_MODEL"
DEFAULT_NATURAL_DRAFT_MODEL = "gpt-5.5"


def build_natural_draft_writer_prompt(brief: ApprovedCoachBrief) -> str:
    """Build the intentionally short writer prompt.

    This prompt is deliberately not the v5 quote/value/schema cage. The audit service
    is responsible for approval after drafting.
    """

    safe_brief = _writer_safe_brief(brief)
    return (
        "You are writing a short Daily Coach note for the user.\n"
        "Use only the approved coach brief below.\n"
        "Write naturally and plainly. Say the useful action, not a slogan.\n"
        "Cover what matters today: whether training is appropriate, how hard to train, "
        "what nutrition gap matters, what food action is available, and what not to overdo.\n"
        "Do not invent facts, foods, servings, timing, targets, causes, medical claims, or user data.\n"
        "Do not mention backend systems, claim keys, validators, JSON, approved context, or internal process.\n"
        "Return one JSON object with exactly these keys: headline, body.\n\n"
        "APPROVED_COACH_BRIEF:\n"
        f"{json.dumps(safe_brief, indent=2, sort_keys=True, default=str)}\n\n"
        "Return the JSON object now."
    )


def write_natural_coach_draft(
    brief: ApprovedCoachBrief,
    *,
    provider: str = PROVIDER_DETERMINISTIC,
    model: str | None = None,
    allow_live_provider: bool = False,
    environ: Mapping[str, str] | None = None,
) -> NaturalCoachDraft:
    env = dict(os.environ if environ is None else environ)
    resolved_provider = _provider_from_env(provider, env)
    resolved_model = (
        model or env.get(DEFAULT_NATURAL_DRAFT_MODEL_ENV) or DEFAULT_NATURAL_DRAFT_MODEL
    )
    if resolved_provider == PROVIDER_DETERMINISTIC:
        return _deterministic_natural_draft(brief)
    if not allow_live_provider:
        raise ValueError("live_provider_not_allowed")
    prompt = build_natural_draft_writer_prompt(brief)
    if resolved_provider == PROVIDER_OPENAI:
        if not env.get(OPENAI_API_KEY_ENV):
            raise ValueError("missing_api_key")
        raw = call_openai_daily_coach_narrative(
            resolved_model,
            prompt,
            30.0,
            api_key=env.get(OPENAI_API_KEY_ENV),
        )
    elif resolved_provider == PROVIDER_DIRECT_OLLAMA:
        if not env.get(OLLAMA_BASE_URL_ENV):
            raise ValueError("missing_OLLAMA_BASE_URL")
        raw = call_direct_ollama_daily_coach_narrative(
            resolved_model,
            prompt,
            30.0,
            ollama_base_url=env.get(OLLAMA_BASE_URL_ENV),
        )
    else:
        raise ValueError(f"unsupported_provider:{resolved_provider}")
    return parse_natural_coach_draft(
        raw, provider=resolved_provider, model=resolved_model
    )


def parse_natural_coach_draft(
    raw_text: str, *, provider: str, model: str | None
) -> NaturalCoachDraft:
    parsed = json.loads(raw_text.strip())
    if not isinstance(parsed, dict):
        raise ValueError("natural_draft_must_be_json_object")
    keys = set(parsed)
    if keys != {"headline", "body"}:
        raise ValueError(f"natural_draft_schema_invalid:{sorted(keys)}")
    headline = str(parsed["headline"]).strip()
    body = str(parsed["body"]).strip()
    if not headline or not body:
        raise ValueError("natural_draft_headline_and_body_required")
    return NaturalCoachDraft(
        headline=headline,
        body=body,
        provider=provider,  # type: ignore[arg-type]
        model=model,
    )


def _deterministic_natural_draft(brief: ApprovedCoachBrief) -> NaturalCoachDraft:
    food = brief.approved_food_actions[0] if brief.approved_food_actions else None
    training = (
        brief.approved_training_actions[0] if brief.approved_training_actions else None
    )
    recovery = (
        brief.approved_recovery_interpretations[0]
        if brief.approved_recovery_interpretations
        else None
    )
    macro_parts = _macro_status_phrases(brief)
    body_parts: list[str] = []
    if recovery:
        body_parts.append("Recovery looks good enough to train as planned.")
    if training:
        body_parts.append(
            "Keep a couple reps in reserve and stop before the set turns into a grind."
        )
    if macro_parts:
        body_parts.append(" and ".join(macro_parts).capitalize() + ".")
    if food and food.friendly_name:
        reason = food.macro_reason or "the gap"
        condition = (
            food.allowed_conditions[0]
            if food.allowed_conditions
            else f"if {reason} is still short"
        )
        if food.friendly_name.lower() == "oatmeal":
            food_sentence = f"Have {food.friendly_name} {condition}."
        elif food.friendly_name.lower() == "canned tuna":
            food_sentence = f"Eat some {food.friendly_name} {condition}."
        else:
            food_sentence = f"Have {food.friendly_name} {condition}."
        body_parts.append(humanize_food_action_text(food_sentence, brief))
    if not body_parts:
        body_parts.append(
            brief.today_intent or "Keep the next action small and easy to verify."
        )
    return NaturalCoachDraft(
        headline=_headline_for_brief(brief),
        body=humanize_food_action_text(" ".join(body_parts), brief),
        provider=PROVIDER_DETERMINISTIC,
        model=None,
    )


def _writer_safe_brief(brief: ApprovedCoachBrief) -> dict[str, Any]:
    payload = brief.to_dict()
    payload.pop("claim_registry", None)
    return payload


def _provider_from_env(provider: str, env: Mapping[str, str]) -> str:
    configured = env.get(DEFAULT_NATURAL_DRAFT_PROVIDER_ENV) or env.get(
        DAILY_COACH_VALUE_NARRATIVE_PROVIDER_ENV
    )
    return (configured or provider).strip().lower()


def _headline_for_brief(brief: ApprovedCoachBrief) -> str:
    if brief.approved_food_actions and brief.approved_training_actions:
        return "Train Clean + Handle Protein"
    if brief.approved_food_actions:
        return "Simple Nutrition Check"
    if brief.approved_training_actions:
        return "Train as Planned"
    return "Daily Coach"


def _macro_status_phrases(brief: ApprovedCoachBrief) -> list[str]:
    phrases: list[str] = []
    for macro in ["calories", "protein", "carbs", "fat"]:
        if any(
            fact.claim_key.startswith(f"nutrition.{macro}.")
            for fact in brief.approved_facts
        ):
            if macro == "calories":
                phrases.append("calories are below target")
            elif macro == "protein":
                phrases.append("protein is below target")
    return phrases[:2]
