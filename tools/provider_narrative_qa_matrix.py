"""Developer-only Daily Coach provider narrative QA matrix runner.

This script probes the existing Daily Coach narrative preview debug route and
writes a sanitized model behavior matrix. It is intentionally outside the product
runtime path: it does not call providers directly, does not persist model output,
and does not alter Today UI behavior.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_USER_ID = 102
DEFAULT_MODELS = [
    "qwen2.5:3b",
    "qwen2.5:7b",
    "qwen3:8b",
    "qwen3:14b",
    "qwen3:32b",
    "qwen3:30b-a3b",
]

FORBIDDEN_DEBUG_TOKENS = [
    "raw_output",
    "raw provider",
    "raw rejected",
    "prompt",
    "traceback",
    "stack trace",
    "backend-approved facts",
    "full model context",
]

CLASSIFICATION_APPROVED_BASELINE = "APPROVED_BASELINE"
CLASSIFICATION_APPROVED_PROBE = "APPROVED_PROBE"
CLASSIFICATION_SAFE_REJECTED_PARSE = "SAFE_REJECTED_PARSE"
CLASSIFICATION_SAFE_REJECTED_VALIDATION = "SAFE_REJECTED_VALIDATION"
CLASSIFICATION_PROVIDER_ERROR = "PROVIDER_ERROR"
CLASSIFICATION_TIMEOUT = "TIMEOUT"
CLASSIFICATION_NOT_RUN = "NOT_RUN"
CLASSIFICATION_DO_NOT_USE_FOR_BRIDGE = "DO_NOT_USE_FOR_BRIDGE"


@dataclass(frozen=True)
class ProviderNarrativeMatrixRow:
    provider: str
    model: str
    user_id: int | None
    date: str | None
    next_action_id: str | None
    next_action_title: str | None
    workflow_target: str | None
    provider_enabled: bool | None
    provider_attempted: bool | None
    parse_success: bool | None
    validation_success: bool | None
    approved_narrative_returned: bool | None
    fallback_used: bool | None
    fallback_reason: str | None
    parse_extraction_strategy: str | None
    forbidden_debug_leaks: list[str] = field(default_factory=list)
    runtime_seconds: float | None = None
    classification: str = CLASSIFICATION_NOT_RUN
    qualitative_voice_note: str = ""
    over_inference_risk: str = ""
    display_readiness_recommendation: str = ""
    sanitized_parse_error: Any = None
    sanitized_validation_errors: Any = None
    sanitized_provider_error: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def collect_forbidden_debug_leaks(payload: Any) -> list[str]:
    """Return forbidden diagnostic tokens found in a sanitized response payload."""

    text = json.dumps(payload, sort_keys=True, default=str).lower()
    return [token for token in FORBIDDEN_DEBUG_TOKENS if token.lower() in text]


def classify_preview(
    model: str, preview: dict[str, Any], *, request_failed: bool = False
) -> str:
    """Classify one sanitized preview response for QA matrix reporting."""

    if request_failed:
        provider_error = str(preview.get("provider_error") or "").lower()
        if "timed out" in provider_error or "timeout" in provider_error:
            return CLASSIFICATION_TIMEOUT
        return CLASSIFICATION_PROVIDER_ERROR

    leaks = collect_forbidden_debug_leaks(preview)
    if leaks:
        return CLASSIFICATION_DO_NOT_USE_FOR_BRIDGE

    if preview.get("provider_error"):
        return CLASSIFICATION_PROVIDER_ERROR

    parse_success = preview.get("parse_success")
    validation_success = preview.get("validation_success")
    approved = preview.get("approved_narrative_returned")

    if parse_success is True and validation_success is True and approved is True:
        if model == "qwen2.5:3b":
            return CLASSIFICATION_APPROVED_BASELINE
        return CLASSIFICATION_APPROVED_PROBE

    if parse_success is False:
        return CLASSIFICATION_SAFE_REJECTED_PARSE

    if parse_success is True and validation_success is False:
        return CLASSIFICATION_SAFE_REJECTED_VALIDATION

    return CLASSIFICATION_DO_NOT_USE_FOR_BRIDGE


def default_quality_notes(classification: str, model: str) -> tuple[str, str, str]:
    """Return conservative default notes for a matrix row.

    These notes are intentionally non-promotional. Runtime/manual reviewers may
    edit the generated markdown with richer voice observations before acceptance.
    """

    if classification == CLASSIFICATION_APPROVED_BASELINE:
        return (
            "Contract-approved baseline. Manual voice review should confirm whether the copy is useful enough for bridge retry.",
            "Low if diagnostics show no validation warnings and no forbidden leaks.",
            "Bridge baseline candidate only; not a product default or model promotion.",
        )
    if classification == CLASSIFICATION_APPROVED_PROBE:
        return (
            "Contract-approved probe. Manual voice review required before any future use beyond Developer Mode.",
            "Unknown until manually reviewed for over-inference and unsupported certainty.",
            "Probe only; do not use for bridge unless Architecture accepts additional evidence.",
        )
    if classification == CLASSIFICATION_SAFE_REJECTED_PARSE:
        return (
            "Did not produce safely extractable contract JSON.",
            "Contained output that the parser could not safely accept.",
            "Do not use for bridge; safe rejection is acceptable characterization.",
        )
    if classification == CLASSIFICATION_SAFE_REJECTED_VALIDATION:
        return (
            "Parsed but failed backend validation.",
            "Validation failure suggests unsupported wording or contract mismatch.",
            "Do not use for bridge without a narrow Architecture-approved follow-up.",
        )
    if classification == CLASSIFICATION_TIMEOUT:
        return (
            "Request timed out during manual preview.",
            "Latency makes this unsuitable for interactive preview as tested.",
            "Do not use for bridge; consider async-only future evaluation.",
        )
    if classification == CLASSIFICATION_PROVIDER_ERROR:
        return (
            "Provider request failed or returned a provider-level error.",
            "No language quality conclusion from this run.",
            "Do not use for bridge until connectivity/model availability is confirmed.",
        )
    return (
        f"{model} was not display-ready in this run.",
        "Unknown or unsafe.",
        "Do not use for bridge.",
    )


def row_from_payload(
    *,
    model: str,
    provider: str,
    payload: dict[str, Any],
    runtime_seconds: float,
) -> ProviderNarrativeMatrixRow:
    preview = payload.get("daily_coach_narrative_preview", payload)
    leaks = collect_forbidden_debug_leaks(payload)
    classification = classify_preview(model, preview)
    voice_note, risk, recommendation = default_quality_notes(classification, model)

    return ProviderNarrativeMatrixRow(
        provider=provider,
        model=model,
        user_id=preview.get("user_id"),
        date=preview.get("date"),
        next_action_id=preview.get("next_action_id"),
        next_action_title=preview.get("next_action_title"),
        workflow_target=preview.get("workflow_target"),
        provider_enabled=preview.get("provider_enabled"),
        provider_attempted=preview.get("provider_attempted"),
        parse_success=preview.get("parse_success"),
        validation_success=preview.get("validation_success"),
        approved_narrative_returned=preview.get("approved_narrative_returned"),
        fallback_used=preview.get("fallback_used"),
        fallback_reason=preview.get("fallback_reason"),
        parse_extraction_strategy=preview.get("parse_extraction_strategy"),
        forbidden_debug_leaks=leaks,
        runtime_seconds=round(runtime_seconds, 2),
        classification=classification,
        qualitative_voice_note=voice_note,
        over_inference_risk=risk,
        display_readiness_recommendation=recommendation,
        sanitized_parse_error=preview.get("parse_error"),
        sanitized_validation_errors=preview.get("validation_errors"),
        sanitized_provider_error=preview.get("provider_error"),
    )


def row_from_exception(
    *,
    model: str,
    provider: str,
    user_id: int,
    exc: Exception,
    runtime_seconds: float,
) -> ProviderNarrativeMatrixRow:
    message = _public_safe_exception_message(exc)
    preview = {"provider_error": message}
    classification = classify_preview(model, preview, request_failed=True)
    voice_note, risk, recommendation = default_quality_notes(classification, model)
    return ProviderNarrativeMatrixRow(
        provider=provider,
        model=model,
        user_id=user_id,
        date=None,
        next_action_id=None,
        next_action_title=None,
        workflow_target=None,
        provider_enabled=None,
        provider_attempted=None,
        parse_success=None,
        validation_success=None,
        approved_narrative_returned=None,
        fallback_used=None,
        fallback_reason=None,
        parse_extraction_strategy=None,
        forbidden_debug_leaks=[],
        runtime_seconds=round(runtime_seconds, 2),
        classification=classification,
        qualitative_voice_note=voice_note,
        over_inference_risk=risk,
        display_readiness_recommendation=recommendation,
        sanitized_provider_error=message,
    )


def fetch_preview(
    *,
    base_url: str,
    user_id: int,
    provider: str,
    model: str,
    timeout_seconds: int,
) -> tuple[dict[str, Any], float]:
    params = urllib.parse.urlencode(
        {
            "provider": provider,
            "model": model,
            "timeout_seconds": str(timeout_seconds),
        }
    )
    url = (
        f"{base_url.rstrip('/')}/daily-coach/{user_id}/narrative-preview/debug?{params}"
    )
    started = time.time()
    with urllib.request.urlopen(url, timeout=timeout_seconds + 20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload, time.time() - started


def run_matrix(
    *,
    base_url: str,
    user_id: int,
    models: list[str],
    provider: str,
    timeout_seconds: int,
) -> list[ProviderNarrativeMatrixRow]:
    rows: list[ProviderNarrativeMatrixRow] = []
    for model in models:
        try:
            payload, runtime_seconds = fetch_preview(
                base_url=base_url,
                user_id=user_id,
                provider=provider,
                model=model,
                timeout_seconds=timeout_seconds,
            )
            rows.append(
                row_from_payload(
                    model=model,
                    provider=provider,
                    payload=payload,
                    runtime_seconds=runtime_seconds,
                )
            )
        except Exception as exc:  # pragma: no cover - exercised in manual runtime
            rows.append(
                row_from_exception(
                    model=model,
                    provider=provider,
                    user_id=user_id,
                    exc=exc,
                    runtime_seconds=timeout_seconds,
                )
            )
    return rows


def render_markdown_report(rows: list[ProviderNarrativeMatrixRow]) -> str:
    lines = [
        "# Provider Narrative QA Matrix v2 Results",
        "",
        "Generated from sanitized Daily Coach narrative preview diagnostics.",
        "",
        "This report characterizes model behavior only. It does not promote any model, enable same-session approval, add provider persistence, or change normal Today behavior.",
        "",
        "## Summary table",
        "",
        "| Model | Classification | Parse | Validation | Approved narrative | Fallback | Strategy | Runtime seconds | Forbidden leaks |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]

    for row in rows:
        lines.append(
            "| {model} | {classification} | {parse} | {validation} | {approved} | {fallback} | {strategy} | {runtime} | {leaks} |".format(
                model=_md(row.model),
                classification=_md(row.classification),
                parse=_md(row.parse_success),
                validation=_md(row.validation_success),
                approved=_md(row.approved_narrative_returned),
                fallback=_md(row.fallback_used),
                strategy=_md(row.parse_extraction_strategy),
                runtime=_md(row.runtime_seconds),
                leaks=_md(
                    ", ".join(row.forbidden_debug_leaks)
                    if row.forbidden_debug_leaks
                    else "none"
                ),
            )
        )

    lines.extend(
        [
            "",
            "## Per-model notes",
            "",
        ]
    )

    for row in rows:
        lines.extend(
            [
                f"### {row.model}",
                "",
                f"- Provider: `{row.provider}`",
                f"- User/date: `{row.user_id}` / `{row.date or 'n/a'}`",
                f"- Next action: `{row.next_action_id or 'n/a'}` / `{row.next_action_title or 'n/a'}`",
                f"- Workflow target: `{row.workflow_target or 'n/a'}`",
                f"- Classification: `{row.classification}`",
                f"- Runtime seconds: `{row.runtime_seconds}`",
                f"- Parse success: `{row.parse_success}`",
                f"- Validation success: `{row.validation_success}`",
                f"- Approved narrative returned: `{row.approved_narrative_returned}`",
                f"- Fallback used: `{row.fallback_used}`",
                f"- Fallback reason: `{row.fallback_reason}`",
                f"- Parse extraction strategy: `{row.parse_extraction_strategy}`",
                f"- Forbidden/debug leaks: `{', '.join(row.forbidden_debug_leaks) if row.forbidden_debug_leaks else 'none'}`",
                f"- Qualitative voice note: {row.qualitative_voice_note}",
                f"- Over-inference risk: {row.over_inference_risk}",
                f"- Display-readiness recommendation: {row.display_readiness_recommendation}",
            ]
        )
        if row.sanitized_parse_error:
            lines.append(f"- Sanitized parse error: `{_md(row.sanitized_parse_error)}`")
        if row.sanitized_validation_errors:
            lines.append(
                f"- Sanitized validation errors: `{_md(row.sanitized_validation_errors)}`"
            )
        if row.sanitized_provider_error:
            lines.append(
                f"- Sanitized provider error: `{_md(row.sanitized_provider_error)}`"
            )
        lines.append("")

    lines.extend(
        [
            "## Boundary confirmation",
            "",
            "- Provider preview remains manual/developer-gated.",
            "- Normal Today UI must not call the provider.",
            "- No same-session approval is added by this matrix.",
            "- No provider narrative is displayed in normal Today UI.",
            "- No model is promoted by this report.",
            "- Raw/rejected provider output is not included in this report.",
            "",
        ]
    )
    return "\n".join(lines)


def _md(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _public_safe_exception_message(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_error_{exc.code}"
    if isinstance(exc, TimeoutError):
        return "timeout"
    message = str(exc).lower()
    if "timed out" in message:
        return "timeout"
    if "connection refused" in message:
        return "provider_or_api_connection_refused"
    if "name or service not known" in message:
        return "provider_or_api_unreachable"
    return "provider_or_api_request_failed"


def _parse_models(raw_models: list[str] | None) -> list[str]:
    if not raw_models:
        return list(DEFAULT_MODELS)
    models: list[str] = []
    for raw in raw_models:
        models.extend(part.strip() for part in raw.split(",") if part.strip())
    return models


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a sanitized Daily Coach provider narrative QA matrix."
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--user-id", type=int, default=DEFAULT_USER_ID)
    parser.add_argument("--provider", default="direct_ollama")
    parser.add_argument("--model", action="append", dest="models")
    parser.add_argument("--timeout-seconds", type=int, default=240)
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    args = parser.parse_args()

    rows = run_matrix(
        base_url=args.base_url,
        user_id=args.user_id,
        models=_parse_models(args.models),
        provider=args.provider,
        timeout_seconds=args.timeout_seconds,
    )

    json_payload = [row.to_dict() for row in rows]
    print(json.dumps(json_payload, indent=2))

    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(json_payload, indent=2) + "\n", encoding="utf-8"
        )

    if args.markdown_out:
        markdown_path = Path(args.markdown_out)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_markdown_report(rows), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
