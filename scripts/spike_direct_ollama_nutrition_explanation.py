from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Some project modules print database diagnostics during import. Keep this CLI
# machine-readable by sending any import-time noise to stderr.
with redirect_stdout(sys.stderr):
    from models.ai_nutrition_explanation_models import NutritionExplanationContext
    from services import ai_nutrition_explanation_service as explanation_service

DIRECT_OLLAMA_PROVIDER_NAME = "direct_ollama_spike"
DIRECT_OLLAMA_DEFAULT_BASE_URL = (
    explanation_service.NUTRITION_EXPLANATION_DEFAULT_BASE_URL
)
DIRECT_OLLAMA_RESPONSE_PREVIEW_LIMIT = 500

CANDIDATE_NUTRITION_EXPLANATION_ALLOWED_KEYS = {
    "explanation_summary",
    "macro_context",
    "food_suggestion_context",
    "trend_context",
    "calibration_context",
    "limitations_context",
    "confidence",
    "reason_codes",
}

CANDIDATE_NUTRITION_EXPLANATION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "explanation_summary",
        "macro_context",
        "food_suggestion_context",
        "trend_context",
        "calibration_context",
        "limitations_context",
        "confidence",
        "reason_codes",
    ],
    "properties": {
        "explanation_summary": {"type": "string"},
        "macro_context": {"type": ["string", "null"]},
        "food_suggestion_context": {"type": ["string", "null"]},
        "trend_context": {"type": ["string", "null"]},
        "calibration_context": {"type": ["string", "null"]},
        "limitations_context": {"type": ["string", "null"]},
        "confidence": {
            "type": "string",
            "enum": ["Limited", "Low", "Moderate", "High"],
        },
        "reason_codes": {"type": "array", "items": {"type": "string"}},
    },
}

DirectOllamaGenerateCallable = Callable[[str, str, str, dict[str, Any], float], str]


@dataclass
class DirectOllamaSpikeResult:
    success: bool
    provider: str
    configured_model: str
    selected_model: str
    user_id: int
    explanation_date: str
    ollama_base_url: str
    elapsed_seconds: float
    provider_attempted: bool
    candidate_parse_status: str
    candidate_validation_status: str
    validation_status: str
    candidate_valid: bool
    fallback_used: bool
    fallback_reason: str | None
    final_explanation_source: str
    validation_errors: list[str] = field(default_factory=list)
    raw_output_length: int | None = None
    raw_output_preview_truncated: str | None = None
    markdown_wrapper_detected: bool = False
    extra_keys_detected: list[str] = field(default_factory=list)
    wrapper_object_detected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_ollama_model_name(model: str) -> str:
    """Normalize a CrewAI-style Ollama model name for direct Ollama REST calls."""

    stripped = model.strip()
    if stripped.startswith("ollama/"):
        return stripped.removeprefix("ollama/")
    return stripped


def build_direct_ollama_nutrition_explanation_prompt(
    context: NutritionExplanationContext,
) -> str:
    """Reuse the approved compressed provider prompt for the direct Ollama spike."""

    return explanation_service.build_crewai_nutrition_explanation_prompt(context)


def call_direct_ollama_generate(
    base_url: str,
    selected_model: str,
    prompt: str,
    response_schema: dict[str, Any],
    timeout_seconds: float,
) -> str:
    """Call Ollama /api/generate with a JSON schema format payload.

    This is spike-only code. The output remains untrusted and must still pass the
    existing strict parser and validator before it can be considered usable.
    """

    endpoint = f"{base_url.rstrip('/')}/api/generate"
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "format": response_schema,
        "stream": False,
        "options": {"temperature": 0},
    }
    response = requests.post(endpoint, json=payload, timeout=timeout_seconds)
    response.raise_for_status()
    body = response.json()
    raw_output = body.get("response")
    if not isinstance(raw_output, str):
        raise ValueError("Ollama response did not include a text response field.")
    return raw_output


def run_direct_ollama_nutrition_explanation_spike(
    *,
    model: str,
    user_id: int,
    explanation_date: str,
    ollama_base_url: str | None = None,
    context: NutritionExplanationContext | None = None,
    generate: DirectOllamaGenerateCallable = call_direct_ollama_generate,
    timeout_seconds: float = 600,
) -> DirectOllamaSpikeResult:
    """Run one direct Ollama structured-output nutrition explanation spike.

    This function intentionally does not change production provider behavior. It
    builds approved backend context, calls the supplied direct Ollama generator,
    and evaluates the raw response through the existing parser/validator/fallback
    boundary used by the nutrition explanation service.
    """

    configured_model = model.strip()
    selected_model = normalize_ollama_model_name(configured_model)
    resolved_base_url = (
        ollama_base_url
        or os.getenv(explanation_service.OLLAMA_BASE_URL_ENV)
        or DIRECT_OLLAMA_DEFAULT_BASE_URL
    )
    resolved_context = (
        context
        or explanation_service.build_nutrition_explanation_context(
            user_id,
            explanation_date,
        )
    )
    prompt = build_direct_ollama_nutrition_explanation_prompt(resolved_context)

    start = time.perf_counter()
    raw_output: Any | None = None
    provider_attempted = True
    provider_error: str | None = None

    try:
        raw_output = generate(
            resolved_base_url,
            selected_model,
            prompt,
            CANDIDATE_NUTRITION_EXPLANATION_JSON_SCHEMA,
            timeout_seconds,
        )
    except Exception as exc:
        provider_error = f"{type(exc).__name__}: {exc}"

    elapsed_seconds = round(time.perf_counter() - start, 3)

    if provider_error is not None:
        return DirectOllamaSpikeResult(
            success=False,
            provider=DIRECT_OLLAMA_PROVIDER_NAME,
            configured_model=configured_model,
            selected_model=selected_model,
            user_id=user_id,
            explanation_date=explanation_date,
            ollama_base_url=resolved_base_url,
            elapsed_seconds=elapsed_seconds,
            provider_attempted=provider_attempted,
            candidate_parse_status=explanation_service.CANDIDATE_PARSE_STATUS_NOT_ATTEMPTED,
            candidate_validation_status=explanation_service.CANDIDATE_VALIDATION_STATUS_NOT_ATTEMPTED,
            validation_status=explanation_service.VALIDATION_STATUS_NOT_ATTEMPTED,
            candidate_valid=False,
            fallback_used=True,
            fallback_reason=explanation_service.FALLBACK_REASON_PROVIDER_EXCEPTION,
            final_explanation_source=explanation_service.FINAL_EXPLANATION_SOURCE_DETERMINISTIC_FALLBACK,
            validation_errors=[provider_error],
        )

    approved_result = (
        explanation_service.approve_candidate_output_or_fallback_with_metadata(
            raw_output,
            resolved_context,
            configured_provider=DIRECT_OLLAMA_PROVIDER_NAME,
            selected_provider=DIRECT_OLLAMA_PROVIDER_NAME,
            configured_model=configured_model,
            selected_model=selected_model,
            provider_attempted=provider_attempted,
        )
    )
    metadata = approved_result.runtime_metadata
    diagnostics = detect_direct_ollama_output_diagnostics(raw_output)

    return DirectOllamaSpikeResult(
        success=not metadata.fallback_used,
        provider=DIRECT_OLLAMA_PROVIDER_NAME,
        configured_model=configured_model,
        selected_model=selected_model,
        user_id=user_id,
        explanation_date=explanation_date,
        ollama_base_url=resolved_base_url,
        elapsed_seconds=elapsed_seconds,
        provider_attempted=metadata.provider_attempted,
        candidate_parse_status=metadata.candidate_parse_status,
        candidate_validation_status=metadata.candidate_validation_status,
        validation_status=metadata.validation_status,
        candidate_valid=metadata.candidate_valid,
        fallback_used=metadata.fallback_used,
        fallback_reason=metadata.fallback_reason,
        final_explanation_source=metadata.final_explanation_source,
        validation_errors=list(metadata.validation_errors),
        raw_output_length=metadata.raw_output_length,
        raw_output_preview_truncated=metadata.raw_output_preview_truncated,
        markdown_wrapper_detected=metadata.markdown_wrapper_detected,
        extra_keys_detected=diagnostics["extra_keys_detected"],
        wrapper_object_detected=diagnostics["wrapper_object_detected"],
    )


def detect_direct_ollama_output_diagnostics(raw_output: Any) -> dict[str, Any]:
    """Return lightweight diagnostics without relaxing parser acceptance rules."""

    extra_keys: list[str] = []
    wrapper_detected = False

    if isinstance(raw_output, str):
        stripped = raw_output.strip()
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
    elif isinstance(raw_output, dict):
        payload = raw_output
    else:
        payload = None

    if isinstance(payload, dict):
        extra_keys = sorted(
            str(key)
            for key in payload.keys()
            if str(key) not in CANDIDATE_NUTRITION_EXPLANATION_ALLOWED_KEYS
        )
        wrapper_detected = any(
            isinstance(payload.get(key), dict)
            for key in ("candidate", "explanation", "output", "response", "result")
        )

    return {
        "extra_keys_detected": extra_keys,
        "wrapper_object_detected": wrapper_detected,
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Spike direct Ollama structured output for nutrition explanations."
    )
    parser.add_argument(
        "--model", required=True, help="Model name, e.g. ollama/qwen2.5:3b"
    )
    parser.add_argument("--user-id", required=True, type=int)
    parser.add_argument("--date", required=True, dest="explanation_date")
    parser.add_argument(
        "--ollama-base-url",
        default=os.getenv(
            explanation_service.OLLAMA_BASE_URL_ENV, DIRECT_OLLAMA_DEFAULT_BASE_URL
        ),
    )
    parser.add_argument("--timeout-seconds", type=float, default=600)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    # Keep stdout reserved for the final spike JSON so the CLI can be piped to jq.
    # Any database/service diagnostics emitted while building context go to stderr.
    with redirect_stdout(sys.stderr):
        result = run_direct_ollama_nutrition_explanation_spike(
            model=args.model,
            user_id=args.user_id,
            explanation_date=args.explanation_date,
            ollama_base_url=args.ollama_base_url,
            timeout_seconds=args.timeout_seconds,
        )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
