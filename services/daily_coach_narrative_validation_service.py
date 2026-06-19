from __future__ import annotations

import json
import re
from typing import Any

from models.daily_coach_narrative_models import (
    DAILY_COACH_NARRATIVE_DECISION_FAIL,
    DAILY_COACH_NARRATIVE_DECISION_PASS,
    DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
    DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS,
    DAILY_COACH_NARRATIVE_REQUIRED_OUTPUT_KEYS,
    DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED,
    DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED,
    CandidateDailyCoachNarrative,
    DailyCoachNarrativeContext,
    DailyCoachNarrativeParseResult,
    DailyCoachNarrativeScores,
    DailyCoachNarrativeValidationResult,
)
from models.daily_next_action_models import DAILY_NEXT_ACTION_WORKFLOW_TARGETS

_MAX_COACH_NOTE_CHARS = 420

_KNOWN_DAILY_ACTION_TITLES = {
    "Complete recovery check-in",
    "Keep training conservative",
    "Log a meal or snack",
    "Review today's workout",
    "Review today's report guidance",
    "Review nutrition target progress",
}

_GLOBAL_FORBIDDEN_PUBLIC_FRAGMENTS = {
    "meal plan",
    "meal prep",
    "serving size",
    "grams of",
    "calorie target",
    "protein target",
    "macro target",
    "calorie range",
    "macro range",
    "eat chicken",
    "eat rice",
    "eat yogurt",
    "take protein powder",
    "supplement",
    "medical",
    "clinical",
    "diagnose",
    "diagnosis",
    "injury treatment",
    "overtraining",
    "fatigue is high",
    "you are fatigued",
    "you progressed",
    "consistent progress",
    "progression is working",
    "as planned",
    "completed as planned",
    "exercise substitution",
    "swap in",
    "substitute",
}

_GENERIC_FILLER_FRAGMENTS = {
    "stay consistent",
    "keep up the good work",
    "trust the process",
    "listen to your body",
}

_INTERNAL_METADATA_FRAGMENTS = {
    "raw",
    "debug",
    "provider",
    "prompt",
    "schema",
    "validation_error",
    "validation errors",
    "traceback",
    "payload",
    "model",
    "ollama",
    "qwen",
    "crewai",
    "parser",
}


class DailyCoachNarrativeProviderValidationError(ValueError):
    """Raised when the offline provider validation configuration is invalid."""


def parse_daily_coach_narrative_candidate(
    raw_output: str,
) -> DailyCoachNarrativeParseResult:
    """Parse strict Daily Coach Narrative provider output.

    The parser intentionally does not extract JSON from markdown, wrappers, or
    surrounding prose. Offline QA should measure provider contract compliance, not
    paper over malformed provider behavior.
    """

    text = raw_output.strip()
    if not text.startswith("{") or not text.endswith("}"):
        return DailyCoachNarrativeParseResult(
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
            error="Output must be a single JSON object with no markdown or prose.",
        )

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return DailyCoachNarrativeParseResult(
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
            error=f"Invalid JSON: {exc.msg}",
        )

    if not isinstance(parsed, dict):
        return DailyCoachNarrativeParseResult(
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
            error="Output must parse to a JSON object.",
        )

    keys = set(parsed)
    missing = sorted(DAILY_COACH_NARRATIVE_REQUIRED_OUTPUT_KEYS - keys)
    extra = sorted(keys - DAILY_COACH_NARRATIVE_REQUIRED_OUTPUT_KEYS)
    if missing or extra:
        return DailyCoachNarrativeParseResult(
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
            error=f"Schema keys invalid. missing={missing}; extra={extra}",
        )

    for field_name in [
        "coach_note",
        "key_takeaway",
        "recommended_focus",
        "confidence_language",
    ]:
        if not isinstance(parsed[field_name], str):
            return DailyCoachNarrativeParseResult(
                parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
                error=f"{field_name} must be a string.",
            )

    for field_name in ["used_approved_facts", "avoided_claims"]:
        value = parsed[field_name]
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            return DailyCoachNarrativeParseResult(
                parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
                error=f"{field_name} must be a list of strings.",
            )

    return DailyCoachNarrativeParseResult(
        parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS,
        candidate=CandidateDailyCoachNarrative(
            coach_note=parsed["coach_note"].strip(),
            key_takeaway=parsed["key_takeaway"].strip(),
            recommended_focus=parsed["recommended_focus"].strip(),
            confidence_language=parsed["confidence_language"].strip(),
            used_approved_facts=[
                item.strip() for item in parsed["used_approved_facts"]
            ],
            avoided_claims=[item.strip() for item in parsed["avoided_claims"]],
        ),
    )


def validate_daily_coach_narrative_candidate(
    candidate: CandidateDailyCoachNarrative,
    *,
    context: DailyCoachNarrativeContext,
) -> DailyCoachNarrativeValidationResult:
    """Validate a provider candidate against DailyCoachNarrativeContext."""

    _validate_context_for_provider(context)
    validation_errors: list[str] = []
    forbidden_claims_found: list[str] = []

    if candidate.recommended_focus != context.approved_focus:
        validation_errors.append("recommended_focus must exactly match approved_focus.")

    if not candidate.used_approved_facts:
        validation_errors.append("used_approved_facts must not be empty.")

    for fact in candidate.used_approved_facts:
        if fact not in context.approved_facts:
            validation_errors.append(
                f"used_approved_facts contains unapproved fact: {fact}"
            )

    public_text = _candidate_public_text(candidate)
    lowercase_public_text = public_text.lower()

    for action_title in sorted(_KNOWN_DAILY_ACTION_TITLES - {context.approved_focus}):
        if action_title.lower() in lowercase_public_text:
            validation_errors.append(
                f"Output mentions a different Daily Next Action: {action_title}"
            )

    for workflow_target in DAILY_NEXT_ACTION_WORKFLOW_TARGETS:
        if (
            workflow_target != context.workflow_target
            and workflow_target.lower() in lowercase_public_text
        ):
            validation_errors.append(
                f"Output mentions a different workflow target: {workflow_target}"
            )

    context_forbidden_fragments = _forbidden_fragments_for_context(context)
    for fragment in sorted(_GLOBAL_FORBIDDEN_PUBLIC_FRAGMENTS):
        if fragment in lowercase_public_text:
            forbidden_claims_found.append(fragment)

    for fragment in sorted(context_forbidden_fragments):
        if fragment.lower() in lowercase_public_text:
            forbidden_claims_found.append(fragment)

    for fragment in sorted(_GENERIC_FILLER_FRAGMENTS):
        if fragment in lowercase_public_text:
            validation_errors.append(f"Generic filler language found: {fragment}")

    invented_numbers = _invented_numeric_tokens(public_text, context=context)
    if invented_numbers:
        validation_errors.append(
            "Invented numeric tokens found: " + ", ".join(invented_numbers)
        )

    if len(candidate.coach_note) > _MAX_COACH_NOTE_CHARS:
        validation_errors.append("coach_note is too long for a compact UI card.")

    if not _text_mentions_approved_context(public_text, context):
        validation_errors.append(
            "Output does not reference approved context specifically."
        )

    if _contains_internal_metadata(candidate):
        validation_errors.append("Output exposes raw/debug/provider/model metadata.")

    if forbidden_claims_found:
        validation_errors.append(
            "Forbidden claim fragments found: "
            + ", ".join(sorted(set(forbidden_claims_found)))
        )

    unique_errors = _dedupe_preserve_order(validation_errors)
    unique_claims = _dedupe_preserve_order(forbidden_claims_found)
    return DailyCoachNarrativeValidationResult(
        validation_status=(
            DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED
            if not unique_errors
            else DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
        ),
        validation_errors=unique_errors,
        forbidden_claims_found=unique_claims,
    )


def score_daily_coach_narrative_candidate(
    candidate: CandidateDailyCoachNarrative | None,
    *,
    context: DailyCoachNarrativeContext,
    validation_result: DailyCoachNarrativeValidationResult | None = None,
    elapsed_seconds: float = 0.0,
) -> DailyCoachNarrativeScores:
    if candidate is None:
        return DailyCoachNarrativeScores(
            grounding=0,
            claim_safety=0,
            coach_voice=0,
            specificity=0,
            brevity=0,
            actionability=0,
            validator_compatibility=0,
            runtime_practicality=_runtime_practicality_score(elapsed_seconds),
        )

    validation_result = validation_result or validate_daily_coach_narrative_candidate(
        candidate,
        context=context,
    )
    approved = validation_result.approved
    used_fact_count = len(set(candidate.used_approved_facts))
    text = _candidate_public_text(candidate)

    return DailyCoachNarrativeScores(
        grounding=5 if approved and used_fact_count >= 2 else 3 if approved else 0,
        claim_safety=5 if not validation_result.forbidden_claims_found else 0,
        coach_voice=_coach_voice_score(candidate),
        specificity=min(
            5, max(1, used_fact_count + _approved_phrase_hits(text, context))
        ),
        brevity=(
            5
            if len(candidate.coach_note) <= 280
            else 3
            if len(candidate.coach_note) <= _MAX_COACH_NOTE_CHARS
            else 1
        ),
        actionability=5 if candidate.recommended_focus == context.approved_focus else 0,
        validator_compatibility=5 if approved else 0,
        runtime_practicality=_runtime_practicality_score(elapsed_seconds),
    )


def overall_decision_for_candidate(
    *,
    validation_result: DailyCoachNarrativeValidationResult,
    scores: DailyCoachNarrativeScores,
) -> str:
    if validation_result.approved and scores.coach_voice >= 3:
        return DAILY_COACH_NARRATIVE_DECISION_PASS
    return DAILY_COACH_NARRATIVE_DECISION_FAIL


def _candidate_public_text(candidate: CandidateDailyCoachNarrative) -> str:
    return " ".join(
        [
            candidate.coach_note,
            candidate.key_takeaway,
            candidate.recommended_focus,
            candidate.confidence_language,
        ]
    )


def _validate_context_for_provider(context: DailyCoachNarrativeContext) -> None:
    if (
        not context.approved_focus
        or context.approved_focus != context.next_action_title
    ):
        raise DailyCoachNarrativeProviderValidationError(
            "DailyCoachNarrativeContext approved_focus must equal next_action_title."
        )
    if not context.approved_facts:
        raise DailyCoachNarrativeProviderValidationError(
            "DailyCoachNarrativeContext approved_facts cannot be empty."
        )
    if not context.workflow_target:
        raise DailyCoachNarrativeProviderValidationError(
            "DailyCoachNarrativeContext workflow_target is required."
        )


def _forbidden_fragments_for_context(context: DailyCoachNarrativeContext) -> set[str]:
    fragments: set[str] = set()
    for claim in context.forbidden_claims:
        claim_lower = claim.lower()
        if "food" in claim_lower:
            fragments.update({"chicken breast", "greek yogurt", "rice", "egg"})
        if "exercise" in claim_lower:
            fragments.update({"barbell squat", "dumbbell press", "new exercise"})
        if "calorie" in claim_lower:
            fragments.update({"calorie target", "calorie range", "calorie deficit"})
        if "macro" in claim_lower:
            fragments.update(
                {"macro target", "protein target", "carb target", "fat target"}
            )
        if "serving" in claim_lower:
            fragments.update({"serving size", "grams of"})
        if "meal plan" in claim_lower:
            fragments.add("meal plan")
        if "medical" in claim_lower or "clinical" in claim_lower:
            fragments.update({"medical", "clinical", "diagnosis", "diagnose"})
        if "fatigue" in claim_lower:
            fragments.update({"you are fatigued", "fatigue is high", "high fatigue"})
        if "progression" in claim_lower:
            fragments.update({"progression", "progressed", "increase load"})
        if "consistency" in claim_lower:
            fragments.update({"consistent over time", "consistency trend"})
    return fragments


def _invented_numeric_tokens(
    text: str,
    *,
    context: DailyCoachNarrativeContext,
) -> list[str]:
    text_tokens = set(_numeric_tokens(text))
    approved_tokens = set(_numeric_tokens(" ".join(context.approved_facts)))
    approved_tokens.update(_numeric_tokens(context.approved_focus))
    approved_tokens.update(_numeric_tokens(context.next_action_reason))
    approved_tokens.update(_numeric_tokens(context.confidence_language))
    return sorted(text_tokens - approved_tokens)


def _numeric_tokens(text: str) -> list[str]:
    return [
        token.lower() for token in re.findall(r"\b\d+(?:\.\d+)?(?:%|g|lb|lbs)?\b", text)
    ]


def _text_mentions_approved_context(
    text: str,
    context: DailyCoachNarrativeContext,
) -> bool:
    lowercase_text = text.lower()
    if context.approved_focus.lower() in lowercase_text:
        return True
    if any(fact.lower() in lowercase_text for fact in context.approved_facts):
        return True
    return any(
        _important_tail(fact) in lowercase_text for fact in context.approved_facts
    )


def _approved_phrase_hits(text: str, context: DailyCoachNarrativeContext) -> int:
    lowercase_text = text.lower()
    return sum(
        1
        for fact in context.approved_facts
        if fact.lower() in lowercase_text or _important_tail(fact) in lowercase_text
    )


def _important_tail(fact: str) -> str:
    if ":" in fact:
        return fact.split(":", 1)[1].strip().lower()
    return fact.lower()


def _coach_voice_score(candidate: CandidateDailyCoachNarrative) -> int:
    text = candidate.coach_note.strip()
    lowered = text.lower()
    if len(text) < 40:
        return 2
    if any(fragment in lowered for fragment in _GENERIC_FILLER_FRAGMENTS):
        return 2
    if text.endswith(".") and 40 <= len(text) <= 280:
        return 4
    return 3


def _runtime_practicality_score(elapsed_seconds: float) -> int:
    if elapsed_seconds <= 5:
        return 5
    if elapsed_seconds <= 20:
        return 4
    if elapsed_seconds <= 60:
        return 3
    if elapsed_seconds <= 180:
        return 2
    return 1


def _contains_internal_metadata(candidate: CandidateDailyCoachNarrative) -> bool:
    payload: dict[str, Any] = candidate.to_dict()
    text = json.dumps(payload, sort_keys=True).lower()
    return any(fragment in text for fragment in _INTERNAL_METADATA_FRAGMENTS)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped
