from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from typing import Any

from models.coach_voice_bakeoff_models import (
    COACH_VOICE_CONTEXT_DAILY_NEXT_ACTION,
    COACH_VOICE_CONTEXT_DATA_QUALITY_LIMITED,
    COACH_VOICE_CONTEXT_NUTRITION_TARGET_VS_ACTUAL,
    COACH_VOICE_CONTEXT_RECOVERY_LIMITED,
    COACH_VOICE_CONTEXT_TYPES,
    COACH_VOICE_CONTEXT_WORKOUT_PREVIEW,
    COACH_VOICE_DECISION_FAIL,
    COACH_VOICE_DECISION_PASS,
    COACH_VOICE_OUTPUT_REQUIRED_FIELDS,
    COACH_VOICE_PARSE_STATUS_FAILED,
    COACH_VOICE_PARSE_STATUS_SUCCESS,
    COACH_VOICE_VALIDATION_STATUS_APPROVED,
    COACH_VOICE_VALIDATION_STATUS_REJECTED,
    CoachVoiceBakeoffResult,
    CoachVoiceCandidateOutput,
    CoachVoiceContext,
    CoachVoiceParseResult,
    CoachVoiceScores,
    CoachVoiceValidationResult,
)

OLLAMA_BASE_URL_ENV = "OLLAMA_BASE_URL"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"

CoachVoiceGenerateCallable = Callable[[str, str, float, str], str]

COACH_VOICE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": sorted(COACH_VOICE_OUTPUT_REQUIRED_FIELDS),
    "properties": {
        "coach_note": {"type": "string"},
        "key_takeaway": {"type": "string"},
        "recommended_focus": {"type": "string"},
        "confidence_language": {"type": "string"},
        "used_approved_facts": {"type": "array", "items": {"type": "string"}},
        "avoided_claims": {"type": "array", "items": {"type": "string"}},
    },
}

_GLOBAL_FORBIDDEN_CLAIM_FRAGMENTS = {
    "meal plan",
    "meal prep plan",
    "serving size",
    "grams of",
    "take protein powder",
    "supplement",
    "diagnose",
    "diagnosis",
    "medical",
    "clinical",
    "injury treatment",
    "guaranteed",
    "as planned",
    "completed as planned",
    "you completed",
    "you progressed",
    "consistent progress",
    "fatigue is high",
    "you are fatigued",
    "new exercise",
    "swap in",
    "substitute",
}

_GENERIC_FILLER_FRAGMENTS = {
    "stay consistent",
    "keep up the good work",
    "trust the process",
    "listen to your body",
}


class CoachVoiceBakeoffError(ValueError):
    """Raised when the offline bakeoff configuration is invalid."""


def build_default_coach_voice_contexts() -> dict[str, CoachVoiceContext]:
    """Return fixed backend-approved context packs for offline model comparison.

    These context packs are deliberately static. They do not call provider paths,
    mutate user data, or depend on live report generation. They represent approved
    facts from the product surfaces that future Daily Coach Narrative work may use.
    """

    contexts = [
        CoachVoiceContext(
            context_id="user_101_recovery_limited",
            context_type=COACH_VOICE_CONTEXT_RECOVERY_LIMITED,
            user_id=101,
            title="User 101 recovery-limited conservative training context",
            approved_facts=[
                "Daily next action: Keep training conservative",
                "Recovery stance: conservative training",
                "Allowed constraint: keep intensity controlled today",
                "Workflow target: today_recovery_aware_workout",
            ],
            approved_focus_options=["Keep training conservative"],
            forbidden_claims=[
                "fatigue",
                "injury",
                "diagnosis",
                "overtraining",
                "progress",
                "as planned",
            ],
            workflow_target="today_recovery_aware_workout",
            severity="warning",
            notes="Do not invent fatigue, diagnosis, or trend claims.",
        ),
        CoachVoiceContext(
            context_id="user_102_daily_log_food",
            context_type=COACH_VOICE_CONTEXT_DAILY_NEXT_ACTION,
            user_id=102,
            title="User 102 daily next action context",
            approved_facts=[
                "Daily next action: Log a meal or snack",
                "Reason: Today's nutrition state is limited until more food data is logged",
                "Workflow target: nutrition_quick_log",
                "Priority: nutrition logging incompleteness before workout review",
            ],
            approved_focus_options=["Log a meal or snack"],
            forbidden_claims=[
                "Greek yogurt",
                "chicken breast",
                "protein shake",
                "meal plan",
                "calorie target",
                "macro target",
            ],
            workflow_target="nutrition_quick_log",
            severity="info",
            notes="Do not invent a food, target, or meal plan.",
        ),
        CoachVoiceContext(
            context_id="user_105_data_quality_limited",
            context_type=COACH_VOICE_CONTEXT_DATA_QUALITY_LIMITED,
            user_id=105,
            title="User 105 data-quality-limited context",
            approved_facts=[
                "Daily next action: Log a meal or snack",
                "Evidence quality: limited daily data",
                "Approved limitation: improve logging completeness before stronger guidance",
                "Workflow target: nutrition_quick_log",
            ],
            approved_focus_options=["Log a meal or snack"],
            forbidden_claims=[
                "specific food suggestion",
                "Greek yogurt",
                "chicken breast",
                "serving size",
                "calorie target",
                "macro target",
            ],
            workflow_target="nutrition_quick_log",
            severity="info",
            notes="Be honest about limited evidence.",
        ),
        CoachVoiceContext(
            context_id="user_102_nutrition_target_status",
            context_type=COACH_VOICE_CONTEXT_NUTRITION_TARGET_VS_ACTUAL,
            user_id=102,
            title="User 102 nutrition target-vs-actual context",
            approved_facts=[
                "Nutrition target-vs-actual is available",
                "Logging completeness: likely incomplete",
                "Approved focus: add more food logs before interpreting gaps",
                "Known logged foods only: backend-approved canonical foods",
            ],
            approved_focus_options=["Add more food logs before interpreting gaps"],
            forbidden_claims=[
                "deficit",
                "surplus",
                "calorie target",
                "macro target",
                "grams",
                "meal plan",
                "deficiency",
            ],
            workflow_target="nutrition_target_vs_actual",
            severity="info",
            notes="Explain limited target-vs-actual confidence without inventing numbers.",
        ),
        CoachVoiceContext(
            context_id="user_102_workout_preview",
            context_type=COACH_VOICE_CONTEXT_WORKOUT_PREVIEW,
            user_id=102,
            title="User 102 approved workout preview context",
            approved_facts=[
                "Workout preview is available",
                "Approved workout style: structured strength session",
                "Approved exercise: Goblet Squat",
                "Approved exercise: Dumbbell Bench Press",
                "Approved equipment: dumbbells and bench",
            ],
            approved_focus_options=["Review today's workout"],
            forbidden_claims=[
                "new exercise",
                "barbell back squat",
                "personal record",
                "progression",
                "as planned",
                "completed",
                "fatigue",
            ],
            workflow_target="workout_preview",
            severity="success",
            notes="Use only approved workout preview details.",
        ),
    ]

    return {context.context_id: context for context in contexts}


def starter_context_ids() -> list[str]:
    return [
        "user_101_recovery_limited",
        "user_102_daily_log_food",
        "user_105_data_quality_limited",
    ]


def all_context_ids() -> list[str]:
    """Return every built-in context id in deterministic bakeoff order."""

    return list(build_default_coach_voice_contexts())


def build_coach_voice_prompt(context: CoachVoiceContext) -> str:
    """Build the tightened coach voice prompt without exposing raw schema metadata."""

    _validate_context(context)
    approved_focus = context.approved_focus_options[0]
    approved_facts = "\n".join(
        f'{index}. "{fact}"'
        for index, fact in enumerate(context.approved_facts, start=1)
    )
    forbidden_claims = "\n".join(
        f'- "{claim}"' for claim in sorted(set(context.forbidden_claims))
    )
    example_output = {
        "coach_note": "Use the exact approved focus because one approved fact supports it.",
        "key_takeaway": "One exact approved fact copied from the context.",
        "recommended_focus": "Exact approved focus from this context",
        "confidence_language": "This stays limited to the approved facts provided here.",
        "used_approved_facts": ["One exact approved fact copied from the context."],
        "avoided_claims": [
            "No food, exercise, target, recovery, or medical claim was invented."
        ],
    }

    return (
        "You are writing one bounded coach note for AI Health Coach.\n"
        "The backend owns every fact. Your job is language only.\n\n"
        "OUTPUT CONTRACT:\n"
        "- Return one JSON object only. No markdown, prose, code fence, or preface.\n"
        "- Do not return the schema. Do not explain the schema.\n"
        "- Do not return keys like type, properties, required, items, or "
        "additionalProperties.\n"
        "- Return exactly these six keys and no others: coach_note, "
        "key_takeaway, recommended_focus, confidence_language, "
        "used_approved_facts, avoided_claims.\n"
        "- coach_note, key_takeaway, recommended_focus, and "
        "confidence_language must be strings.\n"
        "- used_approved_facts and avoided_claims must be arrays of strings.\n"
        "- recommended_focus must exactly equal the approved focus string below.\n"
        "- used_approved_facts must copy exact strings from APPROVED FACTS only.\n"
        "- avoided_claims should name claims you avoided without adding new facts.\n"
        "- Keep coach_note compact enough for a UI card.\n\n"
        "EXAMPLE ANSWER FORMAT ONLY. Do not copy these placeholder values:\n"
        f"{json.dumps(example_output, indent=2)}\n\n"
        "APPROVED CONTEXT:\n"
        f"- context_id: {context.context_id}\n"
        f"- context_type: {context.context_type}\n"
        f'- approved_focus_exact: "{approved_focus}"\n'
        f"- workflow_target: {context.workflow_target}\n"
        f"- severity: {context.severity}\n"
        f"- context_note: {context.notes}\n\n"
        "APPROVED FACTS. Use only these exact strings when filling "
        "used_approved_facts:\n"
        f"{approved_facts}\n\n"
        "FORBIDDEN CLAIMS. Do not make these claims or close variants:\n"
        f"{forbidden_claims}\n\n"
        "Write the answer now as a single JSON object. "
        f'recommended_focus must be exactly: "{approved_focus}"\n'
    )


def parse_coach_voice_candidate(raw_output: str) -> CoachVoiceParseResult:
    text = raw_output.strip()
    if not text.startswith("{") or not text.endswith("}"):
        return CoachVoiceParseResult(
            parse_status=COACH_VOICE_PARSE_STATUS_FAILED,
            error="Output must be a single JSON object with no markdown or prose.",
        )

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return CoachVoiceParseResult(
            parse_status=COACH_VOICE_PARSE_STATUS_FAILED,
            error=f"Invalid JSON: {exc.msg}",
        )

    if not isinstance(parsed, dict):
        return CoachVoiceParseResult(
            parse_status=COACH_VOICE_PARSE_STATUS_FAILED,
            error="Output must parse to a JSON object.",
        )

    keys = set(parsed)
    missing = sorted(COACH_VOICE_OUTPUT_REQUIRED_FIELDS - keys)
    extra = sorted(keys - COACH_VOICE_OUTPUT_REQUIRED_FIELDS)
    if missing or extra:
        return CoachVoiceParseResult(
            parse_status=COACH_VOICE_PARSE_STATUS_FAILED,
            error=f"Schema keys invalid. missing={missing}; extra={extra}",
        )

    string_fields = [
        "coach_note",
        "key_takeaway",
        "recommended_focus",
        "confidence_language",
    ]
    for field_name in string_fields:
        if not isinstance(parsed[field_name], str):
            return CoachVoiceParseResult(
                parse_status=COACH_VOICE_PARSE_STATUS_FAILED,
                error=f"{field_name} must be a string.",
            )

    for field_name in ["used_approved_facts", "avoided_claims"]:
        value = parsed[field_name]
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            return CoachVoiceParseResult(
                parse_status=COACH_VOICE_PARSE_STATUS_FAILED,
                error=f"{field_name} must be a list of strings.",
            )

    return CoachVoiceParseResult(
        parse_status=COACH_VOICE_PARSE_STATUS_SUCCESS,
        output=CoachVoiceCandidateOutput(
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


def validate_coach_voice_output(
    output: CoachVoiceCandidateOutput,
    *,
    context: CoachVoiceContext,
) -> CoachVoiceValidationResult:
    _validate_context(context)
    validation_errors: list[str] = []
    forbidden_claims_found: list[str] = []

    if output.recommended_focus not in context.approved_focus_options:
        validation_errors.append(
            "recommended_focus must exactly match an approved focus option."
        )

    if not output.used_approved_facts:
        validation_errors.append("used_approved_facts must not be empty.")

    for fact in output.used_approved_facts:
        if fact not in context.approved_facts:
            validation_errors.append(
                f"used_approved_facts contains unapproved fact: {fact}"
            )

    public_text = _candidate_public_text(output)
    lowercase_text = public_text.lower()

    for fragment in sorted(_GLOBAL_FORBIDDEN_CLAIM_FRAGMENTS):
        if fragment in lowercase_text:
            forbidden_claims_found.append(fragment)

    for fragment in sorted(context.forbidden_claims):
        if fragment.lower() in lowercase_text:
            forbidden_claims_found.append(fragment)

    for fragment in sorted(_GENERIC_FILLER_FRAGMENTS):
        if fragment in lowercase_text:
            validation_errors.append(f"Generic filler language found: {fragment}")

    invented_numbers = _invented_numeric_tokens(public_text, context=context)
    if invented_numbers:
        validation_errors.append(
            "Invented numeric tokens found: " + ", ".join(invented_numbers)
        )

    if len(output.coach_note) > 420:
        validation_errors.append("coach_note is too long for a compact UI card.")

    if not _text_mentions_approved_context(public_text, context):
        validation_errors.append(
            "Output does not reference approved context specifically."
        )

    if forbidden_claims_found:
        validation_errors.append(
            "Forbidden claim fragments found: "
            + ", ".join(sorted(set(forbidden_claims_found)))
        )

    unique_errors = _dedupe_preserve_order(validation_errors)
    unique_claims = _dedupe_preserve_order(forbidden_claims_found)
    return CoachVoiceValidationResult(
        validation_status=(
            COACH_VOICE_VALIDATION_STATUS_APPROVED
            if not unique_errors
            else COACH_VOICE_VALIDATION_STATUS_REJECTED
        ),
        validation_errors=unique_errors,
        forbidden_claims_found=unique_claims,
    )


def score_coach_voice_output(
    output: CoachVoiceCandidateOutput | None,
    *,
    context: CoachVoiceContext,
    validation_result: CoachVoiceValidationResult | None = None,
    elapsed_seconds: float = 0.0,
) -> CoachVoiceScores:
    if output is None:
        return CoachVoiceScores(
            grounding=0,
            claim_safety=0,
            coach_voice=0,
            specificity=0,
            brevity=0,
            actionability=0,
            validator_compatibility=0,
            runtime_practicality=_runtime_practicality_score(elapsed_seconds),
        )

    validation_result = validation_result or validate_coach_voice_output(
        output,
        context=context,
    )
    approved = validation_result.approved
    used_fact_count = len(set(output.used_approved_facts))
    text = _candidate_public_text(output)

    return CoachVoiceScores(
        grounding=5 if approved and used_fact_count >= 2 else 3 if approved else 0,
        claim_safety=5 if not validation_result.forbidden_claims_found else 0,
        coach_voice=_coach_voice_score(output),
        specificity=min(
            5, max(1, used_fact_count + _approved_phrase_hits(text, context))
        ),
        brevity=(
            5
            if len(output.coach_note) <= 280
            else 3
            if len(output.coach_note) <= 420
            else 1
        ),
        actionability=(
            5 if output.recommended_focus in context.approved_focus_options else 0
        ),
        validator_compatibility=5 if approved else 0,
        runtime_practicality=_runtime_practicality_score(elapsed_seconds),
    )


def run_coach_voice_candidate(
    *,
    model_name: str,
    context: CoachVoiceContext,
    generate: CoachVoiceGenerateCallable = None,  # type: ignore[assignment]
    timeout_seconds: float = 300.0,
    ollama_base_url: str | None = None,
) -> CoachVoiceBakeoffResult:
    if generate is None:
        generate = call_ollama_generate

    prompt = build_coach_voice_prompt(context)
    start = time.perf_counter()
    try:
        raw_output = generate(
            model_name,
            prompt,
            timeout_seconds,
            ollama_base_url or _resolved_ollama_base_url(),
        )
        elapsed_seconds = round(time.perf_counter() - start, 3)
    except Exception as exc:
        elapsed_seconds = round(time.perf_counter() - start, 3)
        scores = score_coach_voice_output(
            None,
            context=context,
            elapsed_seconds=elapsed_seconds,
        )
        return CoachVoiceBakeoffResult(
            model_name=model_name,
            context_id=context.context_id,
            context_type=context.context_type,
            parse_status=COACH_VOICE_PARSE_STATUS_FAILED,
            validation_status=COACH_VOICE_VALIDATION_STATUS_REJECTED,
            overall_decision=COACH_VOICE_DECISION_FAIL,
            elapsed_seconds=elapsed_seconds,
            latency_ms=round(elapsed_seconds * 1000),
            scores=scores,
            validation_errors=[f"Provider exception: {type(exc).__name__}"],
            forbidden_claims_found=[],
            representative_safe_excerpt=None,
            representative_rejection_reason=f"Provider exception: {type(exc).__name__}",
        )

    parse_result = parse_coach_voice_candidate(raw_output)
    if parse_result.output is None:
        scores = score_coach_voice_output(
            None,
            context=context,
            elapsed_seconds=elapsed_seconds,
        )
        return CoachVoiceBakeoffResult(
            model_name=model_name,
            context_id=context.context_id,
            context_type=context.context_type,
            parse_status=parse_result.parse_status,
            validation_status=COACH_VOICE_VALIDATION_STATUS_REJECTED,
            overall_decision=COACH_VOICE_DECISION_FAIL,
            elapsed_seconds=elapsed_seconds,
            latency_ms=round(elapsed_seconds * 1000),
            scores=scores,
            validation_errors=[parse_result.error or "Parse failed."],
            forbidden_claims_found=[],
            representative_safe_excerpt=None,
            representative_rejection_reason=parse_result.error or "Parse failed.",
        )

    validation_result = validate_coach_voice_output(
        parse_result.output,
        context=context,
    )
    scores = score_coach_voice_output(
        parse_result.output,
        context=context,
        validation_result=validation_result,
        elapsed_seconds=elapsed_seconds,
    )
    overall_decision = (
        COACH_VOICE_DECISION_PASS
        if validation_result.approved and scores.coach_voice >= 3
        else COACH_VOICE_DECISION_FAIL
    )
    errors = list(validation_result.validation_errors)
    if validation_result.approved and scores.coach_voice < 3:
        errors.append("Coach voice score is below acceptance threshold.")

    return CoachVoiceBakeoffResult(
        model_name=model_name,
        context_id=context.context_id,
        context_type=context.context_type,
        parse_status=parse_result.parse_status,
        validation_status=validation_result.validation_status,
        overall_decision=overall_decision,
        elapsed_seconds=elapsed_seconds,
        latency_ms=round(elapsed_seconds * 1000),
        scores=scores,
        validation_errors=errors,
        forbidden_claims_found=validation_result.forbidden_claims_found,
        representative_safe_excerpt=(
            _safe_excerpt(parse_result.output.coach_note)
            if validation_result.approved
            else None
        ),
        representative_rejection_reason=(errors[0] if errors else None),
    )


def run_coach_voice_bakeoff(
    *,
    model_names: Iterable[str],
    contexts: Iterable[CoachVoiceContext],
    generate: CoachVoiceGenerateCallable = None,  # type: ignore[assignment]
    timeout_seconds: float = 300.0,
    ollama_base_url: str | None = None,
) -> list[CoachVoiceBakeoffResult]:
    results: list[CoachVoiceBakeoffResult] = []
    for model_name in model_names:
        for context in contexts:
            results.append(
                run_coach_voice_candidate(
                    model_name=model_name,
                    context=context,
                    generate=generate,
                    timeout_seconds=timeout_seconds,
                    ollama_base_url=ollama_base_url,
                )
            )
    return results


def generate_markdown_report(results: list[CoachVoiceBakeoffResult]) -> str:
    lines = [
        "# Bounded Coach Voice Bakeoff v1 Results",
        "",
        "This report is generated by the offline bakeoff harness. Acceptance of this report does not promote any model to production.",
        "",
        "## Model summary",
        "",
        "| Model | Contexts | Parse pass | Validation pass | Decision pass | Avg grounding | Avg voice | Avg latency ms | Failure categories |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for model_name, model_results in _results_by_model(results).items():
        context_count = len(model_results)
        parse_pass = sum(
            result.parse_status == COACH_VOICE_PARSE_STATUS_SUCCESS
            for result in model_results
        )
        validation_pass = sum(
            result.validation_status == COACH_VOICE_VALIDATION_STATUS_APPROVED
            for result in model_results
        )
        decision_pass = sum(
            result.overall_decision == COACH_VOICE_DECISION_PASS
            for result in model_results
        )
        avg_grounding = _average_score(
            result.scores.grounding for result in model_results
        )
        avg_voice = _average_score(
            result.scores.coach_voice for result in model_results
        )
        avg_latency = round(
            sum(result.latency_ms for result in model_results) / context_count
        )
        failure_categories = ", ".join(_failure_categories(model_results)) or "none"
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(model_name),
                    str(context_count),
                    str(parse_pass),
                    str(validation_pass),
                    str(decision_pass),
                    str(avg_grounding),
                    str(avg_voice),
                    str(avg_latency),
                    _md_cell(failure_categories),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Context matrix",
            "",
            "| Model | Context | Parse | Validation | Decision | Grounding | Voice | Latency ms | Rejection reason |",
            "|---|---|---|---|---|---:|---:|---:|---|",
        ]
    )
    for result in results:
        rejection = result.representative_rejection_reason or ""
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(result.model_name),
                    _md_cell(result.context_id),
                    result.parse_status,
                    result.validation_status,
                    result.overall_decision,
                    str(result.scores.grounding),
                    str(result.scores.coach_voice),
                    str(result.latency_ms),
                    _md_cell(rejection),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Representative safe excerpts",
            "",
        ]
    )
    for result in results:
        if result.representative_safe_excerpt:
            lines.append(
                f"- **{result.model_name} / {result.context_id}:** "
                f"{result.representative_safe_excerpt}"
            )

    lines.extend(
        [
            "",
            "## Boundary reminder",
            "",
            "No model is promoted by this bakeoff. qwen3 remains not approved until a later Architecture decision explicitly promotes it.",
        ]
    )
    return "\n".join(lines) + "\n"


def call_ollama_generate(
    model_name: str,
    prompt: str,
    timeout_seconds: float,
    ollama_base_url: str,
) -> str:
    url = ollama_base_url.rstrip("/") + "/api/generate"
    payload = {
        "model": _normalize_model_name(model_name),
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise CoachVoiceBakeoffError(f"Ollama call failed: {exc}") from exc

    generated = parsed.get("response")
    if not isinstance(generated, str):
        raise CoachVoiceBakeoffError("Ollama response did not include string response.")
    return generated


def _validate_context(context: CoachVoiceContext) -> None:
    if context.context_type not in COACH_VOICE_CONTEXT_TYPES:
        raise CoachVoiceBakeoffError(f"Unknown context_type: {context.context_type}")
    if not context.approved_facts:
        raise CoachVoiceBakeoffError(
            "CoachVoiceContext.approved_facts cannot be empty."
        )
    if not context.approved_focus_options:
        raise CoachVoiceBakeoffError(
            "CoachVoiceContext.approved_focus_options cannot be empty."
        )


def _candidate_public_text(output: CoachVoiceCandidateOutput) -> str:
    return " ".join(
        [
            output.coach_note,
            output.key_takeaway,
            output.recommended_focus,
            output.confidence_language,
        ]
    )


def _invented_numeric_tokens(text: str, *, context: CoachVoiceContext) -> list[str]:
    text_tokens = set(_numeric_tokens(text))
    approved_tokens = set(_numeric_tokens(" ".join(context.approved_facts)))
    approved_tokens.update(_numeric_tokens(" ".join(context.approved_focus_options)))
    return sorted(text_tokens - approved_tokens)


def _numeric_tokens(text: str) -> list[str]:
    return [
        token.lower() for token in re.findall(r"\b\d+(?:\.\d+)?(?:%|g|lb|lbs)?\b", text)
    ]


def _text_mentions_approved_context(text: str, context: CoachVoiceContext) -> bool:
    lowercase_text = text.lower()
    if any(fact.lower() in lowercase_text for fact in context.approved_facts):
        return True
    return any(
        focus.lower() in lowercase_text for focus in context.approved_focus_options
    )


def _approved_phrase_hits(text: str, context: CoachVoiceContext) -> int:
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


def _coach_voice_score(output: CoachVoiceCandidateOutput) -> int:
    text = output.coach_note.strip()
    if len(text) < 40:
        return 2
    if any(fragment in text.lower() for fragment in _GENERIC_FILLER_FRAGMENTS):
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


def _safe_excerpt(text: str, max_chars: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def _normalize_model_name(model_name: str) -> str:
    return model_name.removeprefix("ollama/").strip()


def _resolved_ollama_base_url() -> str:
    return os.getenv(OLLAMA_BASE_URL_ENV) or DEFAULT_OLLAMA_BASE_URL


def _results_by_model(
    results: list[CoachVoiceBakeoffResult],
) -> dict[str, list[CoachVoiceBakeoffResult]]:
    grouped: dict[str, list[CoachVoiceBakeoffResult]] = {}
    for result in results:
        grouped.setdefault(result.model_name, []).append(result)
    return grouped


def _average_score(values: Iterable[int]) -> float:
    values = list(values)
    if not values:
        return 0.0
    return round(sum(values) / len(values), 1)


def _failure_categories(results: list[CoachVoiceBakeoffResult]) -> list[str]:
    categories: list[str] = []
    for result in results:
        error_text = " ".join(result.validation_errors).lower()
        forbidden_text = " ".join(result.forbidden_claims_found).lower()
        combined = f"{error_text} {forbidden_text}"
        if result.parse_status == COACH_VOICE_PARSE_STATUS_FAILED:
            if any(
                fragment in combined
                for fragment in [
                    "additionalproperties",
                    "properties",
                    "required",
                    "schema keys invalid",
                    "type",
                ]
            ):
                categories.append("schema echo")
            else:
                categories.append("parse/json")
        if "forbidden claim" in combined:
            categories.append("forbidden claim")
        if "invented numeric" in combined:
            categories.append("invented number")
        if "generic filler" in combined:
            categories.append("generic filler")
        if "recommended_focus" in combined:
            categories.append("focus mismatch")
        if "used_approved_facts contains unapproved fact" in combined:
            categories.append("unapproved fact")
    return _dedupe_preserve_order(categories)


def _md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
