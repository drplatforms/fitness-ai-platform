from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from models.daily_coach_human_voice_prompt_preview_models import (
    DAILY_COACH_HUMAN_VOICE_PROMPT_PREVIEW_RESULT_VERSION,
    DailyCoachHumanVoicePromptPreviewResult,
)
from services.daily_coach_provider_preview_payload_service import (
    build_daily_coach_provider_preview_raw_data_payload_for_user,
)

ProviderCallable = Callable[[str], str]

RAW_BACKEND_PAYLOAD_MARKER = "RAW_BACKEND_PAYLOAD_JSON:"


def load_human_voice_prompt_file(prompt_file: str | Path) -> str:
    prompt_path = Path(prompt_file)
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Daily Coach human voice prompt file not found: {prompt_path}"
        )
    if not prompt_path.is_file():
        raise ValueError(
            f"Daily Coach human voice prompt path is not a file: {prompt_path}"
        )
    return prompt_path.read_text(encoding="utf-8")


def build_daily_coach_human_voice_provider_input(
    prompt_text: str,
    payload: Mapping[str, Any] | Any,
) -> str:
    payload_dict = _payload_to_dict(payload)
    pretty_payload_json = json.dumps(payload_dict, indent=2, sort_keys=True)
    return (
        f"{prompt_text}\n\n---\n\n{RAW_BACKEND_PAYLOAD_MARKER}\n{pretty_payload_json}"
    )


def run_daily_coach_human_voice_prompt_preview(
    *,
    user_id: int,
    target_date: str,
    model_name: str,
    prompt_file: str | Path,
    payload: Mapping[str, Any] | Any | None = None,
    provider_callable: ProviderCallable | None = None,
    timeout_seconds: float = 300,
    ollama_base_url: str = "http://localhost:11434",
    temperature: float = 0.9,
) -> tuple[DailyCoachHumanVoicePromptPreviewResult, str]:
    """Run an explicit developer-only raw-output preview.

    This function returns raw provider output and terminal-preview metadata only. It
    does not parse, validate, score, approve, persist, or product-surface the
    provider output.
    """

    prompt_text = load_human_voice_prompt_file(prompt_file)
    payload_object = payload
    if payload_object is None:
        payload_object = build_daily_coach_provider_preview_raw_data_payload_for_user(
            user_id=user_id,
            target_date=target_date,
        )
    payload_dict = _payload_to_dict(payload_object)
    provider_input = build_daily_coach_human_voice_provider_input(
        prompt_text,
        payload_dict,
    )

    started_at = time.perf_counter()
    error_type: str | None = None
    error_message: str | None = None
    raw_model_output = ""

    try:
        if provider_callable is not None:
            raw_model_output = provider_callable(provider_input)
        else:
            raw_model_output = call_ollama_human_voice_prompt_preview(
                provider_input=provider_input,
                model_name=model_name,
                timeout_seconds=timeout_seconds,
                ollama_base_url=ollama_base_url,
                temperature=temperature,
            )
        if not isinstance(raw_model_output, str):
            raise TypeError("provider callable must return raw output as a string")
    except Exception as exc:  # noqa: BLE001 - developer preview must report failures safely
        error_type = exc.__class__.__name__
        error_message = str(exc)
        raw_model_output = ""

    elapsed_seconds = time.perf_counter() - started_at
    result = DailyCoachHumanVoicePromptPreviewResult(
        result_version=DAILY_COACH_HUMAN_VOICE_PROMPT_PREVIEW_RESULT_VERSION,
        user_id=user_id,
        target_date=target_date,
        model_name=model_name,
        prompt_file=str(prompt_file),
        prompt_sha256=hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
        generated_at=datetime.now(UTC).isoformat(),
        elapsed_seconds=round(elapsed_seconds, 3),
        latency_ms=round(elapsed_seconds * 1000),
        developer_preview_only=True,
        provider_call_was_opt_in=True,
        persistence_allowed=False,
        product_surface_allowed=False,
        normal_today_surface_allowed=False,
        payload_version=str(payload_dict.get("payload_version", "unknown")),
        source_snapshot_version=str(
            payload_dict.get("source_snapshot_version", "unknown")
        ),
        raw_model_output=raw_model_output,
        error_type=error_type,
        error_message=error_message,
    )
    return result, provider_input


def call_ollama_human_voice_prompt_preview(
    *,
    provider_input: str,
    model_name: str,
    timeout_seconds: float = 300,
    ollama_base_url: str = "http://localhost:11434",
    temperature: float = 0.9,
) -> str:
    url = ollama_base_url.rstrip("/") + "/api/generate"
    request_payload = {
        "model": model_name,
        "prompt": provider_input,
        "stream": False,
        "options": {"temperature": temperature},
    }
    request_body = json.dumps(request_payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Ollama request failed with HTTP {exc.code}: {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama request failed: {exc.reason}") from exc

    try:
        response_payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Ollama response was not valid JSON") from exc

    raw_output = response_payload.get("response")
    if not isinstance(raw_output, str):
        raise RuntimeError("Ollama response did not include raw response text")
    return raw_output


def _payload_to_dict(payload: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(payload, Mapping):
        return dict(payload)
    if hasattr(payload, "to_dict"):
        return payload.to_dict()
    return asdict(payload)
