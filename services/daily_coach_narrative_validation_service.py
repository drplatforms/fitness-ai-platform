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
from models.daily_coach_value_narrative_models import (
    DAILY_COACH_VALUE_NARRATIVE_CANDIDATE_KEYS,
    DAILY_COACH_VALUE_NARRATIVE_CONFIDENCE_VALUES,
    CandidateDailyCoachValueNarrative,
)
from models.daily_next_action_models import DAILY_NEXT_ACTION_WORKFLOW_TARGETS
from services.daily_narrative_copy_service import (
    DAILY_NARRATIVE_AWKWARD_COPY_FRAGMENTS,
    DAILY_NARRATIVE_BANNED_COPY_FRAGMENTS,
)

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
    "you got this",
    "crush it",
    "no excuses",
}

_TEMPLATE_COPY_FRAGMENTS = {
    "based on the data provided",
    "based on the information provided",
    "based on your data",
    "data provided",
    "information provided",
    "what matters today:",
    "why it matters:",
    "next step:",
    "avoid overthinking:",
    "as your ai coach",
    "as a coach note",
    "this coach note",
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

_META_PROCESS_LANGUAGE_FRAGMENTS = {
    "approved facts",
    "backend-approved",
    "backend approved",
    "exact approved focus",
    "use the exact",
    "use the approved",
    "approved context",
    "provided context",
    "given context",
    "as instructed",
    "per instruction",
    "according to the instructions",
    "output contract",
    "json",
    "schema",
    "validator",
    "validation",
    "backend facts",
    "model output",
    "provider output",
    "deterministic facts",
    "required focus",
    "required facts",
    "context packet",
    "workflow target",
    "deterministic fallback",
    "backend",
    "provider",
    "exact match",
}

_META_PROCESS_LANGUAGE_ERROR = (
    "Meta/internal process language is not allowed in coach narrative output"
)

_USER_FACING_META_LANGUAGE_FIELDS = (
    "coach_note",
    "key_takeaway",
    "confidence_language",
)


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

    meta_language_found = _meta_process_language_found(candidate)
    if meta_language_found:
        validation_errors.append(
            f"{_META_PROCESS_LANGUAGE_ERROR}: " + "; ".join(meta_language_found)
        )

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

    for fragment in sorted(DAILY_NARRATIVE_BANNED_COPY_FRAGMENTS):
        if fragment in lowercase_public_text:
            validation_errors.append(
                f"Mechanical Daily Narrative phrase found: {fragment}"
            )

    for fragment in sorted(DAILY_NARRATIVE_AWKWARD_COPY_FRAGMENTS):
        if fragment in lowercase_public_text:
            validation_errors.append(
                f"Awkward Daily Narrative phrase found: {fragment}"
            )

    for fragment in sorted(_template_copy_fragments_found(candidate)):
        validation_errors.append(f"Generic/template coach language found: {fragment}")

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
    # Only user-facing narrative fields should be rejected for accidental raw/debug
    # metadata leakage. Contract/debug fields such as used_approved_facts and
    # avoided_claims can contain audit language in offline artifacts and are not
    # rendered as coach copy.
    text = _user_facing_generated_text(candidate).lower()
    return any(fragment in text for fragment in _INTERNAL_METADATA_FRAGMENTS)


def _meta_process_language_found(
    candidate: CandidateDailyCoachNarrative,
) -> list[str]:
    """Return field-specific meta/process language found in user copy.

    The check intentionally ignores canonical field names,
    ``used_approved_facts``, and ``avoided_claims``. Those fields are part of the
    offline audit contract, not coach-facing narrative copy.
    """

    matches: list[str] = []
    for field_name in _USER_FACING_META_LANGUAGE_FIELDS:
        field_text = getattr(candidate, field_name)
        normalized_text = _normalize_for_fragment_matching(field_text)
        field_matches: list[str] = []
        for fragment in sorted(_META_PROCESS_LANGUAGE_FRAGMENTS):
            normalized_fragment = _normalize_for_fragment_matching(fragment)
            if _contains_normalized_fragment(normalized_text, normalized_fragment):
                field_matches.append(fragment)
        if field_matches:
            matches.append(f"{field_name}: " + ", ".join(field_matches))
    return _dedupe_preserve_order(matches)


def _template_copy_fragments_found(
    candidate: CandidateDailyCoachNarrative,
) -> list[str]:
    """Return generic/template fragments from user-facing coach copy only."""

    text = _user_facing_generated_text(candidate).lower()
    return _dedupe_preserve_order(
        [fragment for fragment in sorted(_TEMPLATE_COPY_FRAGMENTS) if fragment in text]
    )


def _user_facing_generated_text(candidate: CandidateDailyCoachNarrative) -> str:
    return " ".join(
        getattr(candidate, field_name)
        for field_name in _USER_FACING_META_LANGUAGE_FIELDS
    )


def _normalize_for_fragment_matching(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def _contains_normalized_fragment(text: str, fragment: str) -> bool:
    if not fragment:
        return False
    return f" {fragment} " in f" {text} "


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


# ---------------------------------------------------------------------------
# Daily Coach Value-Aware Provider Comparison validation
# ---------------------------------------------------------------------------

_VALUE_NARRATIVE_REQUIRED_STRING_FIELDS = [
    "headline",
    "summary",
    "nutrition_note",
    "training_note",
    "recovery_note",
    "priority_action",
]

_VALUE_NARRATIVE_FORBIDDEN_FRAGMENTS = [
    "no recovery notes",
    "no recovery data",
    "no recovery available",
    "recovery is unavailable",
    "without needing to address recovery",
    "without needing to address training or recovery",
    "no need to consider recovery",
    "no need to address recovery",
    "no need to address training",
    "ignore recovery",
    "you are under-eating",
    "you are undereating",
    "you failed",
    "you must",
    "diagnosis",
    "disease",
    "injury has healed",
    "overtraining",
    "stalled fat loss",
    "stalled weight loss",
    "raw sql",
    "traceback",
    "debug payload",
    "provider metadata",
    "internal validator",
]

_VALUE_NARRATIVE_MARKDOWN_FRAGMENTS = ["```", "###", "**", "- headline"]


def parse_daily_coach_value_narrative_candidate(
    raw_output: str,
) -> tuple[CandidateDailyCoachValueNarrative | None, str | None]:
    """Parse exact-schema value-aware Daily Coach narrative provider JSON."""

    if not isinstance(raw_output, str) or not raw_output.strip():
        return None, "empty_provider_output"
    stripped = raw_output.strip()
    if stripped.startswith("```") or stripped.endswith("```"):
        return None, "markdown_wrapped_output"
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None, "malformed_json"
    if not isinstance(parsed, dict):
        return None, "candidate_must_be_object"
    actual_keys = set(parsed)
    if actual_keys != DAILY_COACH_VALUE_NARRATIVE_CANDIDATE_KEYS:
        extra = sorted(actual_keys - DAILY_COACH_VALUE_NARRATIVE_CANDIDATE_KEYS)
        missing = sorted(DAILY_COACH_VALUE_NARRATIVE_CANDIDATE_KEYS - actual_keys)
        if extra:
            return None, f"extra_keys: {', '.join(extra)}"
        return None, f"missing_keys: {', '.join(missing)}"
    for field_name in _VALUE_NARRATIVE_REQUIRED_STRING_FIELDS + ["confidence"]:
        if not isinstance(parsed[field_name], str) or not parsed[field_name].strip():
            return None, f"{field_name}_must_be_non_empty_string"
    reason_codes = parsed["reason_codes"]
    if not isinstance(reason_codes, list) or not all(
        isinstance(item, str) and item.strip() for item in reason_codes
    ):
        return None, "reason_codes_must_be_non_empty_string_array"
    quoted_values_used = parsed["quoted_values_used"]
    if not isinstance(quoted_values_used, list) or not all(
        isinstance(item, str) and item.strip() for item in quoted_values_used
    ):
        return None, "quoted_values_used_must_be_string_array"
    if parsed["confidence"] not in DAILY_COACH_VALUE_NARRATIVE_CONFIDENCE_VALUES:
        return None, "invalid_confidence"
    return (
        CandidateDailyCoachValueNarrative(
            headline=parsed["headline"].strip(),
            summary=parsed["summary"].strip(),
            nutrition_note=parsed["nutrition_note"].strip(),
            training_note=parsed["training_note"].strip(),
            recovery_note=parsed["recovery_note"].strip(),
            priority_action=parsed["priority_action"].strip(),
            confidence=parsed["confidence"].strip(),
            reason_codes=[item.strip() for item in reason_codes],
            quoted_values_used=[item.strip() for item in quoted_values_used],
        ),
        None,
    )


def validate_daily_coach_value_narrative_candidate(
    candidate: CandidateDailyCoachValueNarrative,
    *,
    synthesis,
    value_context: dict,
) -> list[str]:
    """Validate provider candidate against approved DailyCoachSynthesis values."""

    errors: list[str] = []
    public_text = _daily_coach_value_candidate_text(candidate)
    text_lower = public_text.lower()

    for field_name in _VALUE_NARRATIVE_REQUIRED_STRING_FIELDS:
        value = getattr(candidate, field_name)
        if len(value) > 320:
            errors.append(f"{field_name} should stay concise.")

    if candidate.confidence != getattr(synthesis, "confidence", None):
        errors.append("candidate confidence must match DailyCoachSynthesis confidence.")

    for fragment in _VALUE_NARRATIVE_MARKDOWN_FRAGMENTS:
        if fragment in public_text:
            errors.append("candidate must not include markdown or code-fence syntax.")
            break

    for fragment in _VALUE_NARRATIVE_FORBIDDEN_FRAGMENTS:
        if fragment in text_lower:
            errors.append(f"candidate contains forbidden phrase: {fragment}")

    recovery_signal = str(getattr(synthesis, "recovery_signal", "")).strip()
    if recovery_signal and _value_context_has_recovery(value_context):
        for fragment in [
            "no recovery",
            "recovery is unavailable",
            "recovery unavailable",
            "without needing to address recovery",
        ]:
            if fragment in text_lower:
                errors.append(
                    "candidate must not claim recovery is missing when recovery context exists."
                )
                break

    if (
        "no workout has been started today" in text_lower
        and not _training_supports_no_workout_started(synthesis)
    ):
        errors.append(
            "candidate may mention no workout started today only when approved training context supports it."
        )

    if _candidate_has_unapproved_calorie_target_claim(text_lower, value_context):
        errors.append(
            "candidate must not mention calorie targets unless calorie comparison is display-approved."
        )

    if _candidate_has_unapproved_exact_serving_claim(text_lower, value_context):
        errors.append(
            "candidate must not recommend exact food amounts unless approved suggestions include them."
        )

    if _contains_internal_metadata_value_narrative(text_lower):
        errors.append("candidate must not expose raw/debug/provider/internal metadata.")

    errors.extend(_validate_value_quote_claims(candidate, value_context))

    return _dedupe_preserve_order(errors)


def _validate_value_quote_claims(
    candidate: CandidateDailyCoachValueNarrative,
    value_context: dict,
) -> list[str]:
    errors: list[str] = []
    approved_claims = _approved_value_claim_map(value_context)
    declared_keys = list(dict.fromkeys(candidate.quoted_values_used))
    declared_claims: dict[str, dict[str, Any]] = {}

    for key in declared_keys:
        claim = approved_claims.get(key)
        if claim is None:
            errors.append(f"quoted_values_used contains unapproved value: {key}")
            continue
        if not bool(claim.get("display_allowed", True)):
            errors.append(f"quoted value is not display-approved: {key}")
            continue
        declared_claims[key] = claim

    public_text = _daily_coach_value_candidate_text(candidate)
    text_lower = public_text.lower()
    declared_aliases = _declared_value_aliases(declared_claims)

    numeric_claims = _numeric_claim_fragments(public_text)
    for fragment in numeric_claims:
        if not _fragment_is_covered(fragment, declared_aliases):
            errors.append(
                f"narrative contains undeclared numeric value claim: {fragment}"
            )

    for phrase, claim_key in [
        ("readiness is high", "recovery.readiness_level"),
        ("readiness high", "recovery.readiness_level"),
        ("readiness is low", "recovery.readiness_level"),
        ("readiness low", "recovery.readiness_level"),
        ("fatigue risk is low", "recovery.fatigue_risk"),
        ("fatigue risk low", "recovery.fatigue_risk"),
        ("fatigue risk is high", "recovery.fatigue_risk"),
        ("fatigue risk high", "recovery.fatigue_risk"),
        ("protein is below target", "nutrition.protein.status"),
        ("protein below target", "nutrition.protein.status"),
        ("calories below target", "nutrition.calories.status"),
        ("calorie target", "nutrition.calories.target_min"),
    ]:
        if phrase in text_lower and claim_key not in declared_claims:
            errors.append(
                f"narrative contains undeclared approved value claim: {phrase}"
            )

    if re.search(r"\b\d+(?:\.\d+)?\s*(?:oz|ounces)\b", text_lower):
        if not any(
            str(claim.get("claim_type")) == "recommendation"
            and str(claim.get("unit")) in {"g", "gram", "grams"}
            for claim in declared_claims.values()
        ):
            errors.append(
                "serving amount claims require an approved food suggestion claim."
            )

    invented_fragments = [
        "calorie deficit",
        "calorie surplus",
        "500 calorie deficit",
        "900 calories under",
        "overtraining",
        "dropped 15 points",
        "increase weight by 10 pounds",
    ]
    for fragment in invented_fragments:
        if fragment in text_lower and not _fragment_is_covered(
            fragment, declared_aliases
        ):
            errors.append(f"narrative contains invented value claim: {fragment}")
    return errors


def _approved_value_claim_map(value_context: dict) -> dict[str, dict[str, Any]]:
    claims = value_context.get("approved_value_claims") or []
    if not isinstance(claims, list):
        return {}
    mapped: dict[str, dict[str, Any]] = {}
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        key = claim.get("key")
        if isinstance(key, str) and key.strip():
            mapped[key.strip()] = claim
    return mapped


def _declared_value_aliases(claims: dict[str, dict[str, Any]]) -> set[str]:
    aliases: set[str] = set()
    for key, claim in claims.items():
        aliases.add(key.lower())
        value = claim.get("value")
        unit = claim.get("unit")
        if value is not None:
            value_text = _claim_value_text(value)
            aliases.add(value_text.lower())
            if unit:
                aliases.add(f"{value_text}{unit}".lower())
                aliases.add(f"{value_text} {unit}".lower())
            label = claim.get("label")
            if isinstance(label, str) and label:
                aliases.add(f"{label} {value_text}".lower())
                aliases.add(f"{label} is {value_text}".lower())
                if unit:
                    aliases.add(f"{label} {value_text}{unit}".lower())
                    aliases.add(f"{label} {value_text} {unit}".lower())
        for alias in claim.get("aliases") or []:
            if isinstance(alias, str) and alias.strip():
                aliases.add(alias.strip().lower())
    return aliases


def _claim_value_text(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _numeric_claim_fragments(public_text: str) -> list[str]:
    pattern = re.compile(
        r"\b(?:RIR\s*)?\d+(?:\.\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?\s*(?:g|grams?|kcal|calories?|%|percent|score|points?|lb|lbs|pounds?|oz|ounces|minutes?|mins?|hours?|hrs?)?\b",
        re.IGNORECASE,
    )
    fragments: list[str] = []
    for match in pattern.finditer(public_text):
        fragment = re.sub(r"\s+", " ", match.group(0).strip())
        if not fragment:
            continue
        fragments.append(fragment)
    return fragments


def _fragment_is_covered(fragment: str, aliases: set[str]) -> bool:
    normalized = fragment.lower().replace(" ", "")
    for alias in aliases:
        compact_alias = alias.lower().replace(" ", "")
        if (
            normalized == compact_alias
            or normalized in compact_alias
            or compact_alias in normalized
        ):
            return True
    return False


def _daily_coach_value_candidate_text(
    candidate: CandidateDailyCoachValueNarrative,
) -> str:
    return " ".join(
        [
            candidate.headline,
            candidate.summary,
            candidate.nutrition_note,
            candidate.training_note,
            candidate.recovery_note,
            candidate.priority_action,
        ]
    )


def _value_context_has_recovery(value_context: dict) -> bool:
    recovery = value_context.get("approved_recovery")
    if not isinstance(recovery, dict):
        return False
    return any(
        recovery.get(key) not in {None, "", "Unknown", "unknown"}
        for key in [
            "readiness_level",
            "fatigue_risk",
            "recovery_score",
            "recovery_signal",
        ]
    )


def _training_supports_no_workout_started(synthesis) -> bool:
    text = " ".join(
        str(getattr(synthesis, field_name, ""))
        for field_name in ["training_signal", "execution_context", "workout_guidance"]
    ).lower()
    return "no workout has been started today" in text or "no workout started" in text


def _candidate_has_unapproved_calorie_target_claim(
    text_lower: str, value_context: dict
) -> bool:
    calories = (
        value_context.get("approved_nutrition", {})
        .get("macro_status", {})
        .get("calories", {})
    )
    calorie_allowed = bool(calories.get("display_allowed"))
    target_terms = [
        "calorie target",
        "calorie targets",
        "kcal target",
        "you need ",
        "need to eat",
    ]
    return not calorie_allowed and any(term in text_lower for term in target_terms)


def _candidate_has_unapproved_exact_serving_claim(
    text_lower: str, value_context: dict
) -> bool:
    suggestions = value_context.get("approved_food_suggestions")
    has_suggestions = isinstance(suggestions, list) and bool(suggestions)
    exact_amount_terms = ["exact amount", "eat 150g", "eat 200g", "eat this amount"]
    return not has_suggestions and any(
        term in text_lower for term in exact_amount_terms
    )


def _contains_internal_metadata_value_narrative(text_lower: str) -> bool:
    internal_terms = [
        "raw_output",
        "runtime_metadata",
        "provider_attempted",
        "fallback_reason",
        "validation_status",
        "sql",
        "traceback",
        "json schema",
    ]
    return any(term in text_lower for term in internal_terms)
