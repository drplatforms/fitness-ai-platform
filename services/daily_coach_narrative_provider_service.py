from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from typing import Any

from models.daily_coach_narrative_models import (
    DAILY_COACH_NARRATIVE_DECISION_FAIL,
    DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
    DAILY_COACH_NARRATIVE_REQUIRED_OUTPUT_KEYS,
    DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED,
    DailyCoachNarrativeContext,
    DailyCoachNarrativeOfflineQAResult,
)
from services.daily_coach_narrative_context_service import (
    build_daily_coach_narrative_context,
)
from services.daily_coach_narrative_validation_service import (
    overall_decision_for_candidate,
    parse_daily_coach_narrative_candidate,
    score_daily_coach_narrative_candidate,
    validate_daily_coach_narrative_candidate,
)

OLLAMA_BASE_URL_ENV = "OLLAMA_BASE_URL"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"

DailyCoachNarrativeGenerateCallable = Callable[[str, str, float, str], str]

DAILY_COACH_NARRATIVE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": sorted(DAILY_COACH_NARRATIVE_REQUIRED_OUTPUT_KEYS),
    "properties": {
        "coach_note": {"type": "string"},
        "key_takeaway": {"type": "string"},
        "recommended_focus": {"type": "string"},
        "confidence_language": {"type": "string"},
        "used_approved_facts": {"type": "array", "items": {"type": "string"}},
        "avoided_claims": {"type": "array", "items": {"type": "string"}},
    },
}


class DailyCoachNarrativeProviderError(ValueError):
    """Raised when an offline narrative provider call cannot complete."""


def build_daily_coach_narrative_prompt(context: DailyCoachNarrativeContext) -> str:
    """Build a compact prompt from approved DailyCoachNarrativeContext fields only."""

    fact_strings_json = json.dumps(_provider_fact_strings(context), indent=2)
    limitations = "\n".join(
        f'- "{limitation}"' for limitation in context.approved_limitations
    )
    forbidden_claims = "\n".join(
        f'- "{claim}"' for claim in sorted(set(context.forbidden_claims))
    )
    example_output = {
        "coach_note": "Log a meal or snack to improve today's nutrition picture.",
        "key_takeaway": "More food logging gives today's guidance a clearer base.",
        "recommended_focus": "Log a meal or snack",
        "confidence_language": "Keep this limited until more food data is logged.",
        "used_approved_facts": [
            "Daily next action: Log a meal or snack",
            (
                "Daily next action reason: Today's nutrition state is limited until "
                "more food data is logged."
            ),
        ],
        "avoided_claims": [
            "No food, exercise, target, recovery, or medical claim was invented."
        ],
    }

    return (
        "Write one short Daily Coach Narrative for AI Health Coach.\n"
        "Today's action is already selected. Explain why it matters without "
        "changing the action or adding a second action.\n"
        "Use only the listed fact strings and plain coach language.\n\n"
        "OUTPUT FORMAT:\n"
        "- Return a single raw object only. No markdown, code fence, preface, or "
        "follow-up explanation.\n"
        "- Return exactly these six keys and no others: coach_note, "
        "key_takeaway, recommended_focus, confidence_language, "
        "used_approved_facts, avoided_claims.\n"
        "- coach_note, key_takeaway, recommended_focus, and confidence_language "
        "must be strings.\n"
        "- used_approved_facts and avoided_claims must be arrays of strings.\n"
        "- recommended_focus must exactly copy FOCUS_TO_COPY_EXACTLY.\n"
        "- For used_approved_facts, copy exactly two strings from "
        "FACT_STRINGS_FOR_USED_FACTS. The safest choice is the first two "
        "strings.\n"
        "- Do not paraphrase, edit, re-spell, punctuate, or summarize "
        "used_approved_facts. Copy them exactly character-for-character.\n"
        "- Do not place CONFIDENCE_TONE, WORDING_LIMITS, or your own summary "
        "inside used_approved_facts.\n"
        "- Keep coach_note compact enough for a small Today card.\n"
        "- In coach_note, key_takeaway, and confidence_language, do not mention "
        "prompts, objects, validators, services, data packets, routes, internal "
        "instructions, or whether facts were approved.\n\n"
        "EXAMPLE SHAPE ONLY. Do not copy these placeholder values:\n"
        f"{json.dumps(example_output, indent=2)}\n\n"
        "SELECTED_ACTION_CONTEXT:\n"
        f"- user_id: {context.user_id}\n"
        f"- date: {context.date}\n"
        f"- action_id: {context.next_action_id}\n"
        f'- action_title: "{context.next_action_title}"\n'
        f'- action_reason: "{context.next_action_reason}"\n'
        f"- priority: {context.priority}\n"
        f"- severity: {context.severity}\n"
        f'- FOCUS_TO_COPY_EXACTLY: "{context.approved_focus}"\n'
        f'- ACTION_FOCUS_HINT: "{_action_focus_hint(context)}"\n'
        f'- CONFIDENCE_TONE: "{context.confidence_language}"\n\n'
        "FACT_STRINGS_FOR_USED_FACTS:\n"
        f"{fact_strings_json}\n\n"
        "WORDING_LIMITS:\n"
        f"{limitations}\n\n"
        "CLAIMS_TO_AVOID:\n"
        f"{forbidden_claims}\n\n"
        "Write the answer now as the single raw object. "
        f'recommended_focus must be exactly: "{context.approved_focus}"\n'
    )


def _provider_fact_strings(context: DailyCoachNarrativeContext) -> list[str]:
    """Return fact strings useful for provider grounding without route internals.

    The offline provider only needs stable, user-facing grounding facts. Keeping
    confidence and route internals out of the list reduces the chance that a
    model cites a paraphrased confidence label as a used fact.
    """

    excluded_prefixes = (
        "Workflow target:",
        "Nutrition confidence:",
    )
    return [
        fact
        for fact in context.approved_facts
        if not any(fact.startswith(prefix) for prefix in excluded_prefixes)
    ]


def _action_focus_hint(context: DailyCoachNarrativeContext) -> str:
    title = context.next_action_title.lower()
    reason = context.next_action_reason.lower()
    if "training" in title or "workout" in title or "rir" in reason:
        return (
            "Explain today's training/recovery focus without switching to "
            "nutrition logging."
        )
    if "meal" in title or "nutrition" in title or "food" in title:
        return "Explain today's nutrition logging focus without adding workout advice."
    if "recovery" in title or "sleep" in reason or "soreness" in reason:
        return "Explain today's recovery focus without adding food or workout changes."
    return "Explain only the selected action for today."


def build_daily_coach_narrative_contexts_for_users(
    user_ids: Iterable[int],
    *,
    target_date: str | None = None,
) -> list[DailyCoachNarrativeContext]:
    return [
        build_daily_coach_narrative_context(user_id, target_date=target_date)
        for user_id in user_ids
    ]


def run_daily_coach_narrative_candidate(
    *,
    model_name: str,
    context: DailyCoachNarrativeContext,
    generate: DailyCoachNarrativeGenerateCallable = None,  # type: ignore[assignment]
    timeout_seconds: float = 300.0,
    ollama_base_url: str | None = None,
) -> DailyCoachNarrativeOfflineQAResult:
    if generate is None:
        generate = call_ollama_generate

    prompt = build_daily_coach_narrative_prompt(context)
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
        scores = score_daily_coach_narrative_candidate(
            None,
            context=context,
            elapsed_seconds=elapsed_seconds,
        )
        return DailyCoachNarrativeOfflineQAResult(
            model_name=model_name,
            user_id=context.user_id,
            date=context.date,
            next_action_id=context.next_action_id,
            next_action_title=context.next_action_title,
            workflow_target=context.workflow_target,
            parse_status=DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
            validation_status=DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED,
            overall_decision=DAILY_COACH_NARRATIVE_DECISION_FAIL,
            elapsed_seconds=elapsed_seconds,
            latency_ms=round(elapsed_seconds * 1000),
            scores=scores,
            validation_errors=[f"Provider exception: {type(exc).__name__}"],
            forbidden_claims_found=[],
            representative_safe_excerpt=None,
            representative_rejection_reason=f"Provider exception: {type(exc).__name__}",
        )

    parse_result = parse_daily_coach_narrative_candidate(raw_output)
    if parse_result.candidate is None:
        scores = score_daily_coach_narrative_candidate(
            None,
            context=context,
            elapsed_seconds=elapsed_seconds,
        )
        return DailyCoachNarrativeOfflineQAResult(
            model_name=model_name,
            user_id=context.user_id,
            date=context.date,
            next_action_id=context.next_action_id,
            next_action_title=context.next_action_title,
            workflow_target=context.workflow_target,
            parse_status=parse_result.parse_status,
            validation_status=DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED,
            overall_decision=DAILY_COACH_NARRATIVE_DECISION_FAIL,
            elapsed_seconds=elapsed_seconds,
            latency_ms=round(elapsed_seconds * 1000),
            scores=scores,
            validation_errors=[parse_result.error or "Parse failed."],
            forbidden_claims_found=[],
            representative_safe_excerpt=None,
            representative_rejection_reason=parse_result.error or "Parse failed.",
        )

    validation_result = validate_daily_coach_narrative_candidate(
        parse_result.candidate,
        context=context,
    )
    scores = score_daily_coach_narrative_candidate(
        parse_result.candidate,
        context=context,
        validation_result=validation_result,
        elapsed_seconds=elapsed_seconds,
    )
    overall_decision = overall_decision_for_candidate(
        validation_result=validation_result,
        scores=scores,
    )
    errors = list(validation_result.validation_errors)
    if overall_decision == DAILY_COACH_NARRATIVE_DECISION_FAIL and not errors:
        errors.append("Coach voice score is below acceptance threshold.")

    return DailyCoachNarrativeOfflineQAResult(
        model_name=model_name,
        user_id=context.user_id,
        date=context.date,
        next_action_id=context.next_action_id,
        next_action_title=context.next_action_title,
        workflow_target=context.workflow_target,
        parse_status=parse_result.parse_status,
        validation_status=validation_result.validation_status,
        overall_decision=overall_decision,
        elapsed_seconds=elapsed_seconds,
        latency_ms=round(elapsed_seconds * 1000),
        scores=scores,
        validation_errors=errors,
        forbidden_claims_found=validation_result.forbidden_claims_found,
        representative_safe_excerpt=(
            _safe_excerpt(parse_result.candidate.coach_note)
            if validation_result.approved
            else None
        ),
        representative_rejection_reason=(errors[0] if errors else None),
    )


def run_daily_coach_narrative_offline_qa(
    *,
    model_names: Iterable[str],
    contexts: Iterable[DailyCoachNarrativeContext],
    generate: DailyCoachNarrativeGenerateCallable = None,  # type: ignore[assignment]
    timeout_seconds: float = 300.0,
    ollama_base_url: str | None = None,
) -> list[DailyCoachNarrativeOfflineQAResult]:
    results: list[DailyCoachNarrativeOfflineQAResult] = []
    for model_name in model_names:
        for context in contexts:
            results.append(
                run_daily_coach_narrative_candidate(
                    model_name=model_name,
                    context=context,
                    generate=generate,
                    timeout_seconds=timeout_seconds,
                    ollama_base_url=ollama_base_url,
                )
            )
    return results


def generate_markdown_report(
    results: list[DailyCoachNarrativeOfflineQAResult],
    *,
    contexts: Iterable[DailyCoachNarrativeContext] | None = None,
) -> str:
    lines = [
        "# Daily Coach Narrative Offline Provider QA v1 Results",
        "",
        "This report is generated by the offline/debug-only QA harness. "
        "Acceptance of this report does not promote any model or integrate "
        "narrative output into Today.",
        "",
        "## Model summary",
        "",
        "| Model | Contexts | Parse pass | Validation pass | Decision pass | "
        "Avg grounding | Avg voice | Avg latency ms | Failure categories |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for model_name, model_results in _results_by_model(results).items():
        context_count = len(model_results)
        parse_pass = sum(result.parse_status == "success" for result in model_results)
        validation_pass = sum(
            result.validation_status == "approved" for result in model_results
        )
        decision_pass = sum(
            result.overall_decision == "pass" for result in model_results
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

    context_list = list(contexts or [])
    if context_list:
        lines.extend(["", "## DailyCoachNarrativeContext summary", ""])
        lines.extend(
            [
                "| User | Next Action | Workflow Target | Approved Facts | Limitations |",
                "|---:|---|---|---:|---:|",
            ]
        )
        for context in context_list:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(context.user_id),
                        _md_cell(context.next_action_title),
                        _md_cell(context.workflow_target),
                        str(len(context.approved_facts)),
                        str(len(context.approved_limitations)),
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Context matrix",
            "",
            "| Model | User | Next Action | Workflow Target | Parse | Validation | "
            "Decision | Grounding | Voice | Latency ms | Rejection reason |",
            "|---|---:|---|---|---|---|---|---:|---:|---:|---|",
        ]
    )
    for result in results:
        rejection = result.representative_rejection_reason or ""
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(result.model_name),
                    str(result.user_id),
                    _md_cell(result.next_action_title),
                    _md_cell(result.workflow_target),
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

    lines.extend(["", "## Representative safe excerpts", ""])
    for result in results:
        if result.representative_safe_excerpt:
            lines.append(
                f"- **{result.model_name} / user {result.user_id}:** "
                f"{result.representative_safe_excerpt}"
            )

    lines.extend(
        [
            "",
            "## Boundary reminder",
            "",
            "No model is promoted by this offline QA run. qwen3 remains not "
            "approved. direct_ollama remains opt-in only. Narrative output is not "
            "integrated into normal Today, Streamlit, reports, or persistence surfaces.",
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
        "format": DAILY_COACH_NARRATIVE_JSON_SCHEMA,
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
        raise DailyCoachNarrativeProviderError(f"Ollama call failed: {exc}") from exc

    generated = parsed.get("response")
    if not isinstance(generated, str):
        raise DailyCoachNarrativeProviderError(
            "Ollama response did not include string response."
        )
    return generated


def _resolved_ollama_base_url() -> str:
    return os.getenv(OLLAMA_BASE_URL_ENV) or DEFAULT_OLLAMA_BASE_URL


def _normalize_model_name(model_name: str) -> str:
    return model_name.removeprefix("ollama/").strip()


def _safe_excerpt(text: str, max_chars: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def _results_by_model(
    results: list[DailyCoachNarrativeOfflineQAResult],
) -> dict[str, list[DailyCoachNarrativeOfflineQAResult]]:
    grouped: dict[str, list[DailyCoachNarrativeOfflineQAResult]] = {}
    for result in results:
        grouped.setdefault(result.model_name, []).append(result)
    return grouped


def _average_score(values: Iterable[int]) -> float:
    values = list(values)
    if not values:
        return 0.0
    return round(sum(values) / len(values), 1)


def _failure_categories(results: list[DailyCoachNarrativeOfflineQAResult]) -> list[str]:
    categories: list[str] = []
    for result in results:
        error_text = " ".join(result.validation_errors).lower()
        forbidden_text = " ".join(result.forbidden_claims_found).lower()
        combined = f"{error_text} {forbidden_text}"
        if result.parse_status == "failed":
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
        if "unapproved fact" in combined:
            categories.append("unapproved fact")
        if "different daily next action" in combined:
            categories.append("changed action")
        if "different workflow target" in combined:
            categories.append("changed workflow")
    return _dedupe_preserve_order(categories)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def _md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
