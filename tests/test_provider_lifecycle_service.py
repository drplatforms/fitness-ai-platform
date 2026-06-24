from __future__ import annotations

import urllib.error

from services.provider_lifecycle_service import (
    KEEP_ALIVE_POLICY_PINNED_KEEPALIVE,
    KEEP_ALIVE_POLICY_SHORT_KEEPALIVE,
    KEEP_ALIVE_POLICY_UNLOAD_IMMEDIATELY,
    build_ollama_generate_payload,
    classify_keep_alive_policy,
    get_ollama_lifecycle_status,
    maybe_unload_model_after_request,
    render_provider_lifecycle_summary,
    resolve_provider_lifecycle_policy,
    unload_ollama_model,
)


def test_lifecycle_policy_defaults_are_conservative() -> None:
    policy = resolve_provider_lifecycle_policy(
        provider_name="daily_coach_async_provider",
        model_name="qwen2.5:3b",
        environ={},
    )

    assert policy.keep_alive_policy == KEEP_ALIVE_POLICY_UNLOAD_IMMEDIATELY
    assert policy.keep_alive_value == 0
    assert policy.unload_after_request is True
    assert policy.dev_mode_only is True
    assert policy.normal_ui_allowed is False
    assert policy.automatic_generation_allowed is False
    assert policy.fallback_required is True


def test_large_local_model_policy_defaults_to_unload_immediately() -> None:
    policy = resolve_provider_lifecycle_policy(
        provider_name="weekly_future_provider",
        model_name="qwen3:32b",
        environ={},
    )

    assert policy.model_size_class == "very_large"
    assert policy.resource_risk_label == "extreme"
    assert policy.keep_alive_policy == KEEP_ALIVE_POLICY_UNLOAD_IMMEDIATELY
    assert "32B-class" in policy.max_expected_memory_notes


def test_keep_alive_env_can_request_short_keepalive() -> None:
    policy = resolve_provider_lifecycle_policy(
        model_name="qwen2.5:3b",
        environ={"FITNESS_AI_OLLAMA_KEEP_ALIVE": "30s"},
    )

    assert policy.keep_alive_policy == KEEP_ALIVE_POLICY_SHORT_KEEPALIVE
    assert policy.keep_alive_value == "30s"


def test_pinned_keepalive_is_explicitly_classified_not_default() -> None:
    assert classify_keep_alive_policy("-1") == KEEP_ALIVE_POLICY_PINNED_KEEPALIVE


def test_generate_payload_includes_keep_alive_from_policy() -> None:
    policy = resolve_provider_lifecycle_policy(
        model_name="ollama/qwen2.5:3b", environ={}
    )

    payload = build_ollama_generate_payload(
        model_name="ollama/qwen2.5:3b",
        prompt="approved facts only",
        response_schema={"type": "object"},
        options={"temperature": 0},
        policy=policy,
    )

    assert payload["model"] == "qwen2.5:3b"
    assert payload["prompt"] == "approved facts only"
    assert payload["keep_alive"] == 0
    assert payload["stream"] is False
    assert payload["format"] == {"type": "object"}
    assert payload["options"] == {"temperature": 0}


def test_unload_helper_targets_only_named_model() -> None:
    calls: list[tuple[str, dict, float]] = []

    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        calls.append((url, payload, timeout))
        return {"done": True, "done_reason": "unload"}

    result = unload_ollama_model(
        model_name="ollama/qwen2.5:3b",
        base_url="http://example.test:11434",
        timeout_seconds=2.0,
        http_post=fake_post,
    )

    assert result.success is True
    assert result.model_name == "qwen2.5:3b"
    assert result.attempted is True
    assert calls == [
        (
            "http://example.test:11434/api/generate",
            {
                "model": "qwen2.5:3b",
                "prompt": "",
                "stream": False,
                "keep_alive": 0,
            },
            2.0,
        )
    ]


def test_unload_helper_handles_unreachable_ollama_safely() -> None:
    def failing_post(url: str, payload: dict, timeout: float) -> dict:
        raise urllib.error.URLError("connection refused")

    result = unload_ollama_model(
        model_name="qwen2.5:3b",
        base_url="http://example.test:11434",
        http_post=failing_post,
    )

    assert result.success is False
    assert result.error_category == "URLError"
    assert "could not reach" in result.safe_message


def test_maybe_unload_skips_when_keep_alive_already_zero() -> None:
    policy = resolve_provider_lifecycle_policy(model_name="qwen2.5:3b", environ={})
    result = maybe_unload_model_after_request(
        model_name="qwen2.5:3b",
        policy=policy,
        base_url="http://example.test:11434",
    )

    assert result.success is True
    assert result.attempted is False
    assert result.action == "skip_unload_already_requested"


def test_status_helper_handles_unreachable_ollama_safely() -> None:
    def failing_get(url: str, timeout: float) -> dict:
        raise urllib.error.URLError("connection refused")

    result = get_ollama_lifecycle_status(
        base_url="http://example.test:11434",
        http_get=failing_get,
    )

    assert result.success is False
    assert result.error_category == "URLError"
    assert result.running_models == ()


def test_status_helper_reports_running_models_without_generation() -> None:
    def fake_get(url: str, timeout: float) -> dict:
        return {"models": [{"name": "qwen2.5:3b"}, {"model": "llama3.2"}]}

    result = get_ollama_lifecycle_status(
        base_url="http://example.test:11434",
        http_get=fake_get,
    )

    assert result.success is True
    assert result.running_models == ("llama3.2", "qwen2.5:3b")


def test_render_summary_does_not_expose_secrets_or_env_dump() -> None:
    policy = resolve_provider_lifecycle_policy(
        model_name="qwen2.5:3b",
        environ={"SECRET_TOKEN": "do-not-show"},
    )

    summary = render_provider_lifecycle_summary(policy)
    rendered = str(summary)

    assert "do-not-show" not in rendered
    assert "SECRET_TOKEN" not in rendered
    assert summary["normal_ui_allowed"] is False
    assert summary["automatic_generation_allowed"] is False
