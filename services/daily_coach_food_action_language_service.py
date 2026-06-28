from __future__ import annotations

import re
from collections.abc import Iterable

from models.daily_coach_natural_draft_audit_models import ApprovedCoachBrief

FOOD_DISPLAY_LANGUAGE_RULES = {
    "oats, dry": {
        "friendly": "oatmeal",
        "bad_actions": ("add dry oats", "use dry oats", "dry oats if calories"),
        "better_actions": ("have oatmeal", "eat oatmeal"),
    },
    "tuna, canned in water": {
        "friendly": "canned tuna",
        "bad_actions": ("add canned tuna", "use canned tuna"),
        "better_actions": ("eat some canned tuna", "canned tuna can help"),
    },
}

MECHANICAL_FOOD_ACTIONS = (
    "add dry oats",
    "use dry oats",
    "dry oats if calories",
    "add canned tuna",
    "use canned tuna",
    "use canned tuna if the protein gap is open",
)

BACKEND_FOOD_PHRASES = (
    "protein gap is open",
    "calories gap is open",
    "suggested because",
    "macro gap addressed",
    "full meal-plan reset",
)


def friendly_food_display_name(canonical_or_friendly: str) -> str:
    normalized = _normalize(canonical_or_friendly)
    if normalized in FOOD_DISPLAY_LANGUAGE_RULES:
        return FOOD_DISPLAY_LANGUAGE_RULES[normalized]["friendly"]
    if normalized == "oats dry":
        return "oatmeal"
    if normalized == "tuna canned in water":
        return "canned tuna"
    text = re.sub(
        r",\s*(cooked|dry|plain|skinless)", "", canonical_or_friendly, flags=re.I
    )
    text = re.sub(r",\s*", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def humanize_food_action_text(text: str, brief: ApprovedCoachBrief) -> str:
    """Convert safe-but-mechanical food action wording into eating language."""

    revised = text
    for action in brief.approved_food_actions:
        friendly = action.friendly_name or (
            friendly_food_display_name(action.canonical_name)
            if action.canonical_name
            else None
        )
        if not friendly:
            continue
        if _normalize(friendly) == "canned tuna":
            revised = re.sub(
                r"\badd canned tuna\b", "eat some canned tuna", revised, flags=re.I
            )
            revised = re.sub(
                r"\buse canned tuna\b", "eat some canned tuna", revised, flags=re.I
            )
            revised = re.sub(
                r"\bif the protein gap is open\b",
                "if protein is still short",
                revised,
                flags=re.I,
            )
        elif _normalize(friendly) == "oatmeal":
            revised = re.sub(r"\badd dry oats\b", "have oatmeal", revised, flags=re.I)
            revised = re.sub(r"\buse dry oats\b", "have oatmeal", revised, flags=re.I)
            revised = re.sub(r"\badd oatmeal\b", "have oatmeal", revised, flags=re.I)
            revised = re.sub(r"\buse oatmeal\b", "have oatmeal", revised, flags=re.I)
            revised = re.sub(
                r"\bif the calories gap is open\b",
                "if calories are still short",
                revised,
                flags=re.I,
            )
        else:
            pattern = rf"\b(add|use)\s+{re.escape(friendly)}\b"
            revised = re.sub(pattern, f"have {friendly}", revised, flags=re.I)
    return re.sub(r"\s+", " ", revised).strip()


def mechanical_food_action_hits(text: str) -> tuple[str, ...]:
    return _phrase_hits(text, MECHANICAL_FOOD_ACTIONS)


def backend_food_phrase_hits(text: str) -> tuple[str, ...]:
    return _phrase_hits(text, BACKEND_FOOD_PHRASES)


def food_action_language_passes(text: str, brief: ApprovedCoachBrief) -> bool:
    if mechanical_food_action_hits(text) or backend_food_phrase_hits(text):
        return False
    lowered = _normalize(text)
    for action in brief.approved_food_actions:
        if action.canonical_name and action.friendly_name:
            canonical = _normalize(action.canonical_name)
            friendly = _normalize(action.friendly_name)
            if canonical in lowered and canonical != friendly:
                return False
    return True


def _phrase_hits(text: str, phrases: Iterable[str]) -> tuple[str, ...]:
    normalized = _normalize(text)
    return tuple(phrase for phrase in phrases if phrase in normalized)


def _normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())
