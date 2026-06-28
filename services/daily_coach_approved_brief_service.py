from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from models.daily_coach_natural_draft_audit_models import (
    AddressingPolicy,
    ApprovedCoachBrief,
    ApprovedCoachFact,
    ApprovedFoodAction,
    ApprovedRecoveryInterpretation,
    ApprovedTrainingAction,
)
from services.daily_coach_food_action_language_service import friendly_food_display_name
from services.daily_coach_synthesis_service import build_daily_coach_synthesis
from services.daily_coach_value_narrative_service import (
    build_daily_coach_value_aware_provider_context,
)
from services.user_state_service import build_user_health_state

_BLOCKED_TOPICS = (
    "medical claims",
    "supplement claims",
    "overtraining claims",
    "fat-loss guarantees",
    "invented targets",
    "invented timing",
    "invented servings",
    "invented food pairings",
)

_BLOCKED_PHRASES = (
    "food move",
    "clean work",
    "make clean reps the win",
    "the win is",
    "useful move",
    "main lever",
    "support the work",
    "support the day",
    "nutrition support",
    "effort anchor",
    "planned effort range",
    "bigger nutrition overhaul",
    "rebuilding the whole plan",
    "if it fits your meals",
    "if it fits your day",
    "protein bump",
    "easy protein bump",
    "fatigue does not require backing off today",
    "Tuna, Canned in Water",
    "add dry oats",
    "use dry oats",
    "add canned tuna",
    "use canned tuna",
)

_FRIENDLY_FOOD_NAMES = {
    "oats, dry": "oatmeal",
    "tuna, canned in water": "canned tuna",
    "white rice, cooked": "rice",
    "chicken breast, cooked, skinless": "chicken breast",
    "greek yogurt, plain": "Greek yogurt",
}


def build_approved_coach_brief(
    *,
    user_id: int,
    target_date: str,
    scenario_id: str,
    synthesis: Any | None = None,
    value_context: Mapping[str, Any] | None = None,
    addressing_policy: AddressingPolicy | None = None,
) -> ApprovedCoachBrief:
    """Build the developer-only ApprovedCoachBrief boundary.

    The brief is deterministic and uses already-approved Daily Coach context. It is
    deliberately friendlier than raw DB context, but it does not approve new facts.
    """

    resolved_synthesis = synthesis or build_daily_coach_synthesis(user_id)
    if value_context is None:
        health_state = build_user_health_state(user_id)
        value_context = build_daily_coach_value_aware_provider_context(
            user_id=user_id,
            narrative_date=target_date,
            synthesis=resolved_synthesis,
            health_state=health_state,
        )
    context = dict(value_context)
    facts = _approved_facts(context)
    claim_registry = {fact.claim_key: fact.to_dict() for fact in facts}
    food_actions = _approved_food_actions(context, claim_registry)
    training_actions = _approved_training_actions(context, claim_registry)
    recovery_actions = _approved_recovery_interpretations(context, claim_registry)
    interpretations = _approved_interpretations(context)
    today_intent = _today_intent(context, resolved_synthesis)
    policy = addressing_policy or AddressingPolicy()

    return ApprovedCoachBrief(
        brief_id=f"daily_coach_natural_draft_claim_audit_v1:{user_id}:{target_date}:{scenario_id}",
        user_id=user_id,
        date=target_date,
        scenario=scenario_id,
        today_intent=today_intent,
        addressing_policy=policy,
        approved_facts=tuple(facts),
        approved_interpretations=tuple(interpretations),
        approved_food_actions=tuple(food_actions),
        approved_training_actions=tuple(training_actions),
        approved_recovery_interpretations=tuple(recovery_actions),
        blocked_topics=_BLOCKED_TOPICS,
        blocked_phrases=_BLOCKED_PHRASES,
        claim_registry=claim_registry,
        display_policy={
            "gate_modes": ["exploration", "audit", "repair", "approval"],
            "first_pass_capture_required": True,
            "raw_db_rows_allowed": False,
            "canonical_food_names_user_facing": "blocked_when_friendly_name_exists",
            "personal_name_usage": policy.visible_name_usage,
            "serving_display": "only_when_explicitly_approved",
            "timing_claims": "only_when_explicitly_approved",
        },
        verbosity_policy={
            "shape": "headline plus natural body",
            "target": "natural coach note, not a field-by-field compliance wrapper",
            "exploration_mode": "allow the writer enough room to show whether the brief supports useful coaching",
            "avoid": "report tone, slogans, and field-by-field compliance voice",
        },
        repair_policy={
            "max_attempts": 1,
            "repairable": [
                "canonical label leakage",
                "hardcoded personal name",
                "unsupported causal phrasing removable without changing facts",
                "unapproved timing phrase removable without changing facts",
            ],
            "non_repairable": [
                "medical claim",
                "invented food",
                "invented serving amount",
                "invented target",
                "invented workout",
            ],
        },
        fallback_policy={
            "after_failed_repair": "humanized_deterministic_fallback",
            "fallback_is_floor_not_goal": True,
            "must_pass_product_voice_audit": True,
            "normal_today_unchanged": True,
        },
    )


def blocked_natural_draft_phrases() -> tuple[str, ...]:
    return _BLOCKED_PHRASES


def friendly_food_name(canonical_name: str) -> str:
    normalized = _normalize_text(canonical_name)
    return _FRIENDLY_FOOD_NAMES.get(
        normalized, friendly_food_display_name(canonical_name)
    )


def _approved_facts(context: Mapping[str, Any]) -> list[ApprovedCoachFact]:
    facts: list[ApprovedCoachFact] = []
    raw_claims = context.get("approved_value_claims") or []
    if isinstance(raw_claims, Sequence) and not isinstance(raw_claims, str):
        for claim in raw_claims:
            item = _claim_to_fact(claim)
            if item is not None:
                facts.append(item)
    return facts


def _claim_to_fact(claim: Any) -> ApprovedCoachFact | None:
    if not isinstance(claim, Mapping):
        return None
    key = str(claim.get("key") or "").strip()
    if not key or claim.get("display_allowed") is False:
        return None
    value = claim.get("value")
    display_value = _display_value_for_claim(claim)
    friendly_display = None
    if key.endswith(".friendly_name"):
        friendly_display = display_value
    elif key.endswith(".display_name"):
        friendly_display = friendly_food_name(display_value)
    return ApprovedCoachFact(
        claim_key=key,
        claim_type=_claim_type_for_key(key),
        value=value,
        display_value=display_value,
        friendly_display_value=friendly_display,
        user_facing_allowed=True,
        source=str(claim.get("source") or "backend"),
        confidence=(
            claim.get("confidence")
            if isinstance(claim.get("confidence"), str)
            else None
        ),
    )


def _display_value_for_claim(claim: Mapping[str, Any]) -> str:
    value = claim.get("value")
    label = str(claim.get("label") or "").strip()
    unit = str(claim.get("unit") or "").strip()
    if value is None:
        return label
    text = str(value)
    if unit:
        text = f"{text}{unit}" if unit == "%" else f"{text} {unit}"
    if label and label.lower() not in text.lower():
        return text
    return text


def _claim_type_for_key(key: str) -> str:
    if key.startswith("nutrition.food_suggestion") and key.endswith("friendly_name"):
        return "food_identity_claim"
    if key.startswith("nutrition.food_suggestion") and key.endswith("display_name"):
        return "food_identity_claim"
    if key.startswith("nutrition.") and key.endswith(".status"):
        return "macro_status_claim"
    if key.startswith("nutrition."):
        return "nutrition_claim"
    if key.startswith("training.") and "rir" in key:
        return "training_intensity_claim"
    if key.startswith("training."):
        return "training_plan_claim"
    if key.startswith("recovery."):
        return "recovery_status_claim"
    if key.startswith("limitation."):
        return "limitation_claim"
    return "context_claim"


def _approved_food_actions(
    context: Mapping[str, Any], claim_registry: Mapping[str, Any]
) -> list[ApprovedFoodAction]:
    actions: list[ApprovedFoodAction] = []
    copy_context = context.get("food_action_context") or context.get(
        "food_suggestion_copy_context"
    )
    suggestions = []
    if isinstance(copy_context, Mapping):
        suggestions = (
            copy_context.get("friendly_food_options")
            or copy_context.get("suggestions")
            or []
        )
    if isinstance(suggestions, Sequence) and not isinstance(suggestions, str):
        for index, suggestion in enumerate(suggestions, start=1):
            if not isinstance(suggestion, Mapping):
                continue
            canonical = _optional_str(
                suggestion.get("canonical_name") or suggestion.get("display_name")
            )
            friendly = _optional_str(
                suggestion.get("friendly_name")
                or suggestion.get("friendly_display_name")
            )
            if not friendly and canonical:
                friendly = friendly_food_name(canonical)
            macro_reason = _optional_str(suggestion.get("macro_reason"))
            claim_keys = suggestion.get("claim_keys") or {}
            food_key = ""
            if isinstance(claim_keys, Mapping):
                food_key = str(
                    claim_keys.get("friendly_name")
                    or claim_keys.get("canonical_name")
                    or claim_keys.get("display_name")
                    or ""
                )
            if not food_key:
                food_key = f"nutrition.food_suggestion.{index}.friendly_name"
            serving_display = _optional_str(suggestion.get("serving_display"))
            actions.append(
                ApprovedFoodAction(
                    food_claim_key=food_key,
                    canonical_name=canonical,
                    friendly_name=friendly,
                    macro_reason=macro_reason,
                    allowed_conditions=_food_allowed_conditions(macro_reason),
                    serving_display=serving_display,
                    serving_allowed=bool(serving_display),
                    blocked_user_facing_names=tuple(
                        item
                        for item in [canonical]
                        if item
                        and friendly
                        and _normalize_text(item) != _normalize_text(friendly)
                    ),
                )
            )
    if actions:
        return actions[:2]

    for key, fact in claim_registry.items():
        if key.startswith("nutrition.food_suggestion") and key.endswith(
            ".friendly_name"
        ):
            friendly = str(fact.get("display_value") or fact.get("value") or "")
            actions.append(
                ApprovedFoodAction(
                    food_claim_key=key,
                    canonical_name=None,
                    friendly_name=friendly,
                    macro_reason="protein" if "tuna" in friendly.lower() else None,
                    allowed_conditions=_food_allowed_conditions("protein"),
                )
            )
    return actions[:2]


def _approved_training_actions(
    context: Mapping[str, Any], claim_registry: Mapping[str, Any]
) -> list[ApprovedTrainingAction]:
    training_keys = tuple(key for key in claim_registry if key.startswith("training."))
    if not training_keys:
        story = context.get("today_story") or {}
        if isinstance(story, Mapping) and story.get("training_implication"):
            training_keys = tuple(story.get("primary_claim_keys") or ())
    if not training_keys:
        return []
    return [
        ApprovedTrainingAction(
            claim_keys=training_keys,
            instruction="Train as planned, keep a couple reps in reserve, and stop before the set turns into a grind.",
            allowed_phrasings=(
                "train as planned",
                "keep a couple reps in reserve",
                "stop before the set turns into a grind",
                "do not turn it into a max-effort test",
            ),
            blocked_phrasings=("effort anchor", "planned effort range", "clean work"),
        )
    ]


def _approved_recovery_interpretations(
    context: Mapping[str, Any], claim_registry: Mapping[str, Any]
) -> list[ApprovedRecoveryInterpretation]:
    recovery_keys = tuple(key for key in claim_registry if key.startswith("recovery."))
    if not recovery_keys:
        return []
    story = context.get("today_story") or {}
    interpretation = "Recovery looks good enough to train as planned, but not to turn the session into a max-effort test."
    if isinstance(story, Mapping):
        interpretation = str(
            story.get("recovery_implication")
            or story.get("recovery_angle")
            or interpretation
        )
    return [
        ApprovedRecoveryInterpretation(
            claim_keys=recovery_keys,
            interpretation=interpretation,
            allowed_phrasings=(
                "recovery looks good enough to train",
                "you do not need to back off today",
                "train normally, not recklessly",
            ),
            blocked_phrasings=(
                "fully recovered",
                "fatigue is not a concern",
                "recovery guarantees performance",
            ),
        )
    ]


def _approved_interpretations(context: Mapping[str, Any]) -> list[str]:
    items: list[str] = []
    brief = context.get("approved_context_brief") or {}
    sentences = brief.get("sentences") if isinstance(brief, Mapping) else None
    if isinstance(sentences, Sequence) and not isinstance(sentences, str):
        for sentence in sentences:
            if isinstance(sentence, Mapping):
                text = str(
                    sentence.get("user_safe_context")
                    or sentence.get("text")
                    or sentence.get("meaning")
                    or ""
                ).strip()
                if text:
                    items.append(text)
    story = context.get("today_story") or {}
    if isinstance(story, Mapping):
        for key in [
            "main_tension",
            "training_implication",
            "nutrition_implication",
            "recovery_implication",
            "desired_coaching_move",
        ]:
            text = str(story.get(key) or "").strip()
            if text:
                items.append(text)
    return _dedupe(items)[:8]


def _today_intent(context: Mapping[str, Any], synthesis: Any) -> str:
    story = context.get("today_story") or {}
    if isinstance(story, Mapping):
        for key in ["desired_coaching_move", "priority_angle", "main_tension", "why"]:
            if story.get(key):
                return str(story[key])
    return str(
        getattr(synthesis, "recommended_focus", "") or "Give one useful next action."
    )


def _food_allowed_conditions(macro_reason: str | None) -> tuple[str, ...]:
    if not macro_reason:
        return ("if the gap is still open",)
    macro = macro_reason.strip().lower()
    if macro == "protein":
        return ("if protein is still short", "if you still need more protein")
    if macro == "calories":
        return ("if calories are still short", "if you still need more calories")
    return (f"if {macro} is still short",)


def _fallback_friendly_name(name: str) -> str:
    text = re.sub(r",\s*(cooked|dry|plain|skinless)", "", name, flags=re.I)
    text = re.sub(r",\s*", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _dedupe(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        key = _normalize_text(item)
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())
