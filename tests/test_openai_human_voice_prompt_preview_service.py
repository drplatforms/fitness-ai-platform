from __future__ import annotations

import json
import urllib.error
from pathlib import Path

from services import openai_human_voice_prompt_preview_service as openai_service
from services.daily_coach_human_voice_prompt_preview_service import (
    RAW_BACKEND_PAYLOAD_MARKER,
)
from services.openai_human_voice_prompt_preview_service import (
    extract_openai_response_text,
    run_openai_daily_coach_human_voice_prompt_preview,
)

CONTROLLED_PROMPT = "You are a health and fitness professional.\nWrite for the user.\n"
CONTROLLED_PAYLOAD = {
    "payload_version": "daily_coach_provider_preview_raw_data_payload_v1",
    "user_id": 102,
    "target_date": "2026-06-14",
    "source_snapshot_version": "daily_coach_intelligence_snapshot_v2",
    "source_data": {"recovery_intelligence": {"confidence": "Moderate"}},
}

ANTI_CAGE_PHRASES = [
    "GOOD_STYLE_EXAMPLES",
    "BAD_STYLE_EXAMPLES",
    "DAILY_COACH_NARRATIVE_JSON_SCHEMA",
    "Sentence 1:",
    "Sentence 2:",
    "Final sentence:",
    "Return exactly these six keys",
]


def test_openai_provider_request_uses_configured_model_base_url_and_api_key(
    monkeypatch,
) -> None:
    captured = {}
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps({"output_text": "raw openai text"}).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(openai_service.urllib.request, "urlopen", fake_urlopen)

    output = openai_service.call_openai_human_voice_prompt_preview(
        provider_input="human prompt plus raw payload",
        model_name="gpt-5.5",
        timeout_seconds=17,
        openai_base_url="https://openai.test/v1",
    )

    assert output == "raw openai text"
    assert captured["url"] == "https://openai.test/v1/responses"
    assert captured["timeout"] == 17
    assert captured["headers"]["Authorization"] == "Bearer sk-test-secret"
    assert captured["body"] == {
        "model": "gpt-5.5",
        "input": "human prompt plus raw payload",
    }
    assert "text" not in captured["body"]
    assert "format" not in captured["body"]
    assert "tools" not in captured["body"]
    assert "tool_choice" not in captured["body"]
    assert "response_format" not in captured["body"]
    assert "json_schema" not in json.dumps(captured["body"]).lower()


def test_openai_service_sends_human_prompt_and_raw_payload_as_input(
    tmp_path: Path,
) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(CONTROLLED_PROMPT, encoding="utf-8")
    seen_inputs = []

    def fake_provider(provider_input: str) -> str:
        seen_inputs.append(provider_input)
        return "raw gpt family output"

    result, provider_input = run_openai_daily_coach_human_voice_prompt_preview(
        user_id=102,
        target_date="2026-06-14",
        model_name="gpt-5.5",
        prompt_file=prompt_file,
        payload=CONTROLLED_PAYLOAD,
        provider_callable=fake_provider,
    )

    assert result.provider_name == "openai"
    assert result.model_name == "gpt-5.5"
    assert result.raw_model_output == "raw gpt family output"
    assert result.developer_preview_only is True
    assert result.provider_call_was_opt_in is True
    assert result.persistence_allowed is False
    assert result.product_surface_allowed is False
    assert result.normal_today_surface_allowed is False
    assert provider_input == seen_inputs[0]
    assert provider_input.startswith(CONTROLLED_PROMPT)
    assert RAW_BACKEND_PAYLOAD_MARKER in provider_input
    assert (
        '"payload_version": "daily_coach_provider_preview_raw_data_payload_v1"'
        in provider_input
    )


def test_openai_provider_input_does_not_inject_old_caged_prompt_scaffolding(
    tmp_path: Path,
) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(CONTROLLED_PROMPT, encoding="utf-8")

    _result, provider_input = run_openai_daily_coach_human_voice_prompt_preview(
        user_id=102,
        target_date="2026-06-14",
        model_name="gpt-5.5",
        prompt_file=prompt_file,
        payload=CONTROLLED_PAYLOAD,
        provider_callable=lambda _: "raw output",
    )

    for phrase in ANTI_CAGE_PHRASES:
        assert phrase not in provider_input


def test_openai_provider_does_not_expose_api_key_on_http_failure(
    monkeypatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-very-secret")

    def fake_urlopen(_request, timeout):
        raise urllib.error.HTTPError(
            url="https://openai.test/v1/responses",
            code=401,
            msg="Unauthorized sk-very-secret",
            hdrs=None,
            fp=_FakeErrorBody("bad key sk-very-secret"),
        )

    monkeypatch.setattr(openai_service.urllib.request, "urlopen", fake_urlopen)

    try:
        openai_service.call_openai_human_voice_prompt_preview(
            provider_input="input",
            model_name="gpt-5.5",
            openai_base_url="https://openai.test/v1",
        )
    except RuntimeError as exc:
        message = str(exc)
    else:  # pragma: no cover - explicit failure path
        raise AssertionError("HTTP failure should raise")

    assert "sk-very-secret" not in message
    assert "[redacted]" in message


def test_openai_service_returns_clear_error_metadata_on_http_failure(
    tmp_path: Path,
) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(CONTROLLED_PROMPT, encoding="utf-8")

    def failing_provider(_: str) -> str:
        raise RuntimeError("OpenAI Responses API request failed with HTTP 404")

    result, _provider_input = run_openai_daily_coach_human_voice_prompt_preview(
        user_id=102,
        target_date="2026-06-14",
        model_name="unavailable-model",
        prompt_file=prompt_file,
        payload=CONTROLLED_PAYLOAD,
        provider_callable=failing_provider,
    )

    assert result.raw_model_output == ""
    assert result.error_type == "RuntimeError"
    assert "HTTP 404" in (result.error_message or "")
    assert result.persistence_allowed is False


def test_openai_service_returns_error_metadata_on_missing_api_key(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(CONTROLLED_PROMPT, encoding="utf-8")

    result, _provider_input = run_openai_daily_coach_human_voice_prompt_preview(
        user_id=102,
        target_date="2026-06-14",
        model_name="gpt-5.5",
        prompt_file=prompt_file,
        payload=CONTROLLED_PAYLOAD,
    )

    assert result.raw_model_output == ""
    assert result.error_type == "MissingOpenAIAPIKeyError"
    assert "OPENAI_API_KEY" in (result.error_message or "")


def test_openai_service_returns_error_metadata_on_malformed_response(
    tmp_path: Path,
) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(CONTROLLED_PROMPT, encoding="utf-8")

    def malformed_provider(_: str) -> str:
        raise RuntimeError("OpenAI response did not include extractable text output")

    result, _provider_input = run_openai_daily_coach_human_voice_prompt_preview(
        user_id=102,
        target_date="2026-06-14",
        model_name="gpt-5.5",
        prompt_file=prompt_file,
        payload=CONTROLLED_PAYLOAD,
        provider_callable=malformed_provider,
    )

    assert result.raw_model_output == ""
    assert result.error_type == "RuntimeError"
    assert "extractable text" in (result.error_message or "")


def test_extracts_output_text_when_present() -> None:
    assert (
        extract_openai_response_text({"output_text": "preferred text"})
        == "preferred text"
    )


def test_extracts_output_content_text_when_output_text_absent() -> None:
    payload = {
        "output": [
            {
                "content": [
                    {"type": "output_text", "text": "hello "},
                    {"type": "output_text", "text": "coach"},
                ]
            }
        ]
    }

    assert extract_openai_response_text(payload) == "hello coach"


class _FakeErrorBody:
    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> bytes:
        return self._text.encode("utf-8")

    def close(self) -> None:
        return None
