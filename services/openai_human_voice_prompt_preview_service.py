from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from models.daily_coach_human_voice_prompt_preview_models import (
    DAILY_COACH_HUMAN_VOICE_PROMPT_PREVIEW_RESULT_VERSION,
    DailyCoachHumanVoicePromptPreviewResult,
)
from services.daily_coach_human_voice_prompt_preview_service import (
    build_daily_coach_human_voice_provider_input,
    load_human_voice_prompt_file,
)
from services.daily_coach_provider_preview_payload_service import (
    build_daily_coach_provider_preview_raw_data_payload_for_user,
)

OpenAIProviderCallable = Callable[[str], str]

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_PROVIDER_NAME = "openai"


class MissingOpenAIAPIKeyError(RuntimeError):
    """Raised when the explicit developer OpenAI preview path lacks a key."""


def run_openai_daily_coach_human_voice_prompt_preview(
    *,
    user_id: int,
    target_date: str,
    model_name: str,
    prompt_file: str | Path,
    payload: Mapping[str, Any] | Any | None = None,
    provider_callable: OpenAIProviderCallable | None = None,
    timeout_seconds: float = 300,
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL,
) -> tuple[DailyCoachHumanVoicePromptPreviewResult, str]:
    """Run an explicit developer-only OpenAI raw-output preview.

    This preserves raw model output as terminal trial evidence only. It does not
    parse, validate, score, approve, persist, or product-surface the provider
    output.
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
            raw_model_output = call_openai_human_voice_prompt_preview(
                provider_input=provider_input,
                model_name=model_name,
                timeout_seconds=timeout_seconds,
                openai_base_url=openai_base_url,
            )
        if not isinstance(raw_model_output, str):
            raise TypeError("provider callable must return raw output as a string")
    except Exception as exc:  # noqa: BLE001 - developer preview reports failures safely
        error_type = exc.__class__.__name__
        error_message = _sanitize_error_message(str(exc))
        raw_model_output = ""

    elapsed_seconds = time.perf_counter() - started_at
    result = DailyCoachHumanVoicePromptPreviewResult(
        result_version=DAILY_COACH_HUMAN_VOICE_PROMPT_PREVIEW_RESULT_VERSION,
        user_id=user_id,
        target_date=target_date,
        model_name=model_name,
        provider_name=OPENAI_PROVIDER_NAME,
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


def call_openai_human_voice_prompt_preview(
    *,
    provider_input: str,
    model_name: str,
    timeout_seconds: float = 300,
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL,
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise MissingOpenAIAPIKeyError(
            "OPENAI_API_KEY is required for --provider openai"
        )

    url = openai_base_url.rstrip("/") + "/responses"
    request_payload = {
        "model": model_name,
        "input": provider_input,
    }
    request_body = json.dumps(request_payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=request_body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"OpenAI Responses API request failed with HTTP {exc.code}: "
            f"{_sanitize_error_message(detail)}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"OpenAI Responses API request failed: "
            f"{_sanitize_error_message(str(exc.reason))}"
        ) from exc

    try:
        response_payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI response was not valid JSON") from exc

    return extract_openai_response_text(response_payload)


def extract_openai_response_text(response_payload: Mapping[str, Any]) -> str:
    output_text = response_payload.get("output_text")
    if isinstance(output_text, str):
        return output_text

    output = response_payload.get("output")
    if isinstance(output, list):
        text_parts: list[str] = []
        for output_item in output:
            if not isinstance(output_item, Mapping):
                continue
            content = output_item.get("content")
            if isinstance(content, list):
                text_parts.extend(_extract_text_parts_from_content(content))
        joined = "".join(text_parts)
        if joined:
            return joined

    raise RuntimeError("OpenAI response did not include extractable text output")


def _extract_text_parts_from_content(content: list[Any]) -> list[str]:
    text_parts: list[str] = []
    for content_item in content:
        if not isinstance(content_item, Mapping):
            continue
        text = content_item.get("text")
        if isinstance(text, str):
            text_parts.append(text)
            continue
        output_text = content_item.get("output_text")
        if isinstance(output_text, str):
            text_parts.append(output_text)
    return text_parts


def _payload_to_dict(payload: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(payload, Mapping):
        return dict(payload)
    if hasattr(payload, "to_dict"):
        return payload.to_dict()
    from dataclasses import asdict

    return asdict(payload)


def _sanitize_error_message(message: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    sanitized = message
    if api_key:
        sanitized = sanitized.replace(api_key, "[redacted]")
    return sanitized
