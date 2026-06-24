from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from typing import Any

FITNESS_AI_OLLAMA_KEEP_ALIVE_ENV = "FITNESS_AI_OLLAMA_KEEP_ALIVE"
FITNESS_AI_OLLAMA_UNLOAD_AFTER_REQUEST_ENV = "FITNESS_AI_OLLAMA_UNLOAD_AFTER_REQUEST"
FITNESS_AI_OLLAMA_ALLOW_MANUAL_STOP_ENV = "FITNESS_AI_OLLAMA_ALLOW_MANUAL_STOP"
FITNESS_AI_PROVIDER_LIFECYCLE_LOGGING_ENV = "FITNESS_AI_PROVIDER_LIFECYCLE_LOGGING"
OLLAMA_BASE_URL_ENV = "OLLAMA_BASE_URL"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_KEEP_ALIVE = "0"
DEFAULT_OLLAMA_STATUS_TIMEOUT_SECONDS = 5.0
DEFAULT_OLLAMA_UNLOAD_TIMEOUT_SECONDS = 10.0

KEEP_ALIVE_POLICY_UNLOAD_IMMEDIATELY = "unload_immediately"
KEEP_ALIVE_POLICY_SHORT_KEEPALIVE = "short_keepalive"
KEEP_ALIVE_POLICY_DEFAULT_KEEPALIVE = "default_keepalive"
KEEP_ALIVE_POLICY_PINNED_KEEPALIVE = "pinned_keepalive"
KEEP_ALIVE_POLICY_CUSTOM = "custom"

MODEL_SIZE_SMALL = "small"
MODEL_SIZE_MEDIUM = "medium"
MODEL_SIZE_LARGE = "large"
MODEL_SIZE_VERY_LARGE = "very_large"

RESOURCE_RISK_LOW = "low"
RESOURCE_RISK_MODERATE = "moderate"
RESOURCE_RISK_HIGH = "high"
RESOURCE_RISK_EXTREME = "extreme"

ProviderLifecycleHttpPost = Callable[[str, dict[str, Any], float], dict[str, Any]]
ProviderLifecycleHttpGet = Callable[[str, float], dict[str, Any]]


@dataclass(frozen=True)
class ProviderLifecyclePolicy:
    provider_name: str
    model_name: str
    model_size_class: str
    keep_alive_policy: str
    keep_alive_value: str | int
    unload_after_request: bool
    manual_unload_supported: bool
    max_expected_memory_notes: str
    resource_risk_label: str
    dev_mode_only: bool
    normal_ui_allowed: bool
    automatic_generation_allowed: bool
    fallback_required: bool
    lifecycle_logging_enabled: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderLifecycleActionResult:
    success: bool
    action: str
    provider_name: str
    model_name: str | None
    ollama_base_url: str
    attempted: bool
    safe_message: str
    error_category: str | None = None
    running_models: tuple[str, ...] = ()
    keep_alive_value: str | int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["running_models"] = list(self.running_models)
        return payload


def resolve_provider_lifecycle_policy(
    *,
    provider_name: str = "direct_ollama",
    model_name: str = "qwen2.5:3b",
    environ: Mapping[str, str] | None = None,
) -> ProviderLifecyclePolicy:
    """Resolve safe project provider lifecycle policy.

    The default is intentionally conservative for Dustin's local resource split:
    direct Ollama calls include keep_alive=0 unless explicitly overridden.
    This resolver never requires Ollama to be installed or reachable.
    """

    env = os.environ if environ is None else environ
    normalized_model = normalize_ollama_model_name(model_name)
    keep_alive_value = parse_keep_alive_value(
        env.get(FITNESS_AI_OLLAMA_KEEP_ALIVE_ENV, DEFAULT_OLLAMA_KEEP_ALIVE)
    )
    return ProviderLifecyclePolicy(
        provider_name=provider_name,
        model_name=normalized_model,
        model_size_class=classify_model_size(normalized_model),
        keep_alive_policy=classify_keep_alive_policy(keep_alive_value),
        keep_alive_value=keep_alive_value,
        unload_after_request=_env_bool(
            env.get(FITNESS_AI_OLLAMA_UNLOAD_AFTER_REQUEST_ENV), default=True
        ),
        manual_unload_supported=True,
        max_expected_memory_notes=model_memory_notes(normalized_model),
        resource_risk_label=resource_risk_label(normalized_model),
        dev_mode_only=True,
        normal_ui_allowed=False,
        automatic_generation_allowed=False,
        fallback_required=True,
        lifecycle_logging_enabled=_env_bool(
            env.get(FITNESS_AI_PROVIDER_LIFECYCLE_LOGGING_ENV), default=False
        ),
    )


def build_ollama_generate_payload(
    *,
    model_name: str,
    prompt: str,
    response_schema: dict[str, Any] | None = None,
    stream: bool = False,
    options: Mapping[str, Any] | None = None,
    policy: ProviderLifecyclePolicy | None = None,
) -> dict[str, Any]:
    """Build a direct Ollama /api/generate payload with lifecycle policy.

    This helper centralizes keep_alive so provider call sites do not silently rely
    on Ollama's default model residency behavior.
    """

    resolved_policy = policy or resolve_provider_lifecycle_policy(model_name=model_name)
    payload: dict[str, Any] = {
        "model": normalize_ollama_model_name(model_name),
        "prompt": prompt,
        "stream": stream,
        "keep_alive": resolved_policy.keep_alive_value,
    }
    if response_schema is not None:
        payload["format"] = response_schema
    if options:
        payload["options"] = dict(options)
    return payload


def maybe_unload_model_after_request(
    *,
    model_name: str,
    policy: ProviderLifecyclePolicy,
    base_url: str | None = None,
    timeout_seconds: float = DEFAULT_OLLAMA_UNLOAD_TIMEOUT_SECONDS,
    http_post: ProviderLifecycleHttpPost | None = None,
) -> ProviderLifecycleActionResult:
    """Unload after request when policy requires an explicit follow-up unload.

    keep_alive=0 already tells Ollama to unload after generation, so this helper
    skips the redundant unload call in that case.
    """

    if not policy.unload_after_request:
        return ProviderLifecycleActionResult(
            success=True,
            action="skip_unload_after_request",
            provider_name=policy.provider_name,
            model_name=normalize_ollama_model_name(model_name),
            ollama_base_url=resolve_ollama_base_url(base_url=base_url),
            attempted=False,
            safe_message="Provider lifecycle policy does not require post-request unload.",
            keep_alive_value=policy.keep_alive_value,
        )
    if (
        classify_keep_alive_policy(policy.keep_alive_value)
        == KEEP_ALIVE_POLICY_UNLOAD_IMMEDIATELY
    ):
        return ProviderLifecycleActionResult(
            success=True,
            action="skip_unload_already_requested",
            provider_name=policy.provider_name,
            model_name=normalize_ollama_model_name(model_name),
            ollama_base_url=resolve_ollama_base_url(base_url=base_url),
            attempted=False,
            safe_message="Ollama request already included keep_alive=0.",
            keep_alive_value=policy.keep_alive_value,
        )
    return unload_ollama_model(
        model_name=model_name,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        http_post=http_post,
        provider_name=policy.provider_name,
    )


def unload_ollama_model(
    *,
    model_name: str,
    base_url: str | None = None,
    timeout_seconds: float = DEFAULT_OLLAMA_UNLOAD_TIMEOUT_SECONDS,
    http_post: ProviderLifecycleHttpPost | None = None,
    provider_name: str = "manual_dev_tool",
) -> ProviderLifecycleActionResult:
    """Unload only the named model through Ollama's documented API path.

    This helper never kills processes and never stops the Ollama server globally.
    """

    normalized_model = normalize_ollama_model_name(model_name)
    if not normalized_model:
        return ProviderLifecycleActionResult(
            success=False,
            action="unload_model",
            provider_name=provider_name,
            model_name=None,
            ollama_base_url=resolve_ollama_base_url(base_url=base_url),
            attempted=False,
            safe_message="No model name was provided for unload.",
            error_category="missing_model_name",
        )

    resolved_base_url = resolve_ollama_base_url(base_url=base_url)
    endpoint = f"{resolved_base_url.rstrip('/')}/api/generate"
    payload = {
        "model": normalized_model,
        "prompt": "",
        "stream": False,
        "keep_alive": 0,
    }
    post = http_post or _http_post_json
    try:
        post(endpoint, payload, timeout_seconds)
    except urllib.error.URLError as exc:
        return ProviderLifecycleActionResult(
            success=False,
            action="unload_model",
            provider_name=provider_name,
            model_name=normalized_model,
            ollama_base_url=resolved_base_url,
            attempted=True,
            safe_message="Ollama unload request could not reach the API.",
            error_category=type(exc).__name__,
            keep_alive_value=0,
        )
    except Exception as exc:  # noqa: BLE001 - safe diagnostic category only
        return ProviderLifecycleActionResult(
            success=False,
            action="unload_model",
            provider_name=provider_name,
            model_name=normalized_model,
            ollama_base_url=resolved_base_url,
            attempted=True,
            safe_message="Ollama unload request failed safely.",
            error_category=type(exc).__name__,
            keep_alive_value=0,
        )

    return ProviderLifecycleActionResult(
        success=True,
        action="unload_model",
        provider_name=provider_name,
        model_name=normalized_model,
        ollama_base_url=resolved_base_url,
        attempted=True,
        safe_message=f"Unload requested for model {normalized_model}.",
        keep_alive_value=0,
    )


def get_ollama_lifecycle_status(
    *,
    base_url: str | None = None,
    timeout_seconds: float = DEFAULT_OLLAMA_STATUS_TIMEOUT_SECONDS,
    http_get: ProviderLifecycleHttpGet | None = None,
) -> ProviderLifecycleActionResult:
    """Return safe Ollama lifecycle reachability/status metadata.

    The status check reads loaded-model metadata when the Ollama /api/ps endpoint
    is available. It does not generate provider output.
    """

    resolved_base_url = resolve_ollama_base_url(base_url=base_url)
    endpoint = f"{resolved_base_url.rstrip('/')}/api/ps"
    get = http_get or _http_get_json
    try:
        body = get(endpoint, timeout_seconds)
    except urllib.error.URLError as exc:
        return ProviderLifecycleActionResult(
            success=False,
            action="status",
            provider_name="ollama_lifecycle_status",
            model_name=None,
            ollama_base_url=resolved_base_url,
            attempted=True,
            safe_message="Ollama API was not reachable for lifecycle status.",
            error_category=type(exc).__name__,
        )
    except Exception as exc:  # noqa: BLE001 - safe diagnostic category only
        return ProviderLifecycleActionResult(
            success=False,
            action="status",
            provider_name="ollama_lifecycle_status",
            model_name=None,
            ollama_base_url=resolved_base_url,
            attempted=True,
            safe_message="Ollama lifecycle status failed safely.",
            error_category=type(exc).__name__,
        )

    running_models = tuple(
        sorted(
            str(model.get("name") or model.get("model") or "")
            for model in body.get("models", [])
            if isinstance(model, dict) and (model.get("name") or model.get("model"))
        )
    )
    return ProviderLifecycleActionResult(
        success=True,
        action="status",
        provider_name="ollama_lifecycle_status",
        model_name=None,
        ollama_base_url=resolved_base_url,
        attempted=True,
        safe_message="Ollama lifecycle status read completed.",
        running_models=running_models,
    )


def render_provider_lifecycle_summary(
    policy: ProviderLifecyclePolicy,
) -> dict[str, Any]:
    """Render safe developer-facing policy metadata without secrets."""

    return {
        "provider_name": policy.provider_name,
        "model_name": policy.model_name,
        "model_size_class": policy.model_size_class,
        "resource_risk_label": policy.resource_risk_label,
        "keep_alive_policy": policy.keep_alive_policy,
        "keep_alive_value": policy.keep_alive_value,
        "unload_after_request": policy.unload_after_request,
        "manual_unload_supported": policy.manual_unload_supported,
        "dev_mode_only": policy.dev_mode_only,
        "normal_ui_allowed": policy.normal_ui_allowed,
        "automatic_generation_allowed": policy.automatic_generation_allowed,
        "fallback_required": policy.fallback_required,
        "lifecycle_logging_enabled": policy.lifecycle_logging_enabled,
        "max_expected_memory_notes": policy.max_expected_memory_notes,
        "safe_boundary": (
            "Lifecycle diagnostics expose policy and status only; they do not "
            "generate provider output or dump environment values."
        ),
    }


def resolve_ollama_base_url(
    *, base_url: str | None = None, environ: Mapping[str, str] | None = None
) -> str:
    env = os.environ if environ is None else environ
    return (base_url or env.get(OLLAMA_BASE_URL_ENV) or DEFAULT_OLLAMA_BASE_URL).strip()


def normalize_ollama_model_name(model_name: str) -> str:
    return model_name.strip().removeprefix("ollama/").strip()


def parse_keep_alive_value(value: str | int | float | None) -> str | int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else str(value)
    stripped = str(value).strip()
    if stripped in {"", "none", "None"}:
        return 0
    try:
        return int(stripped)
    except ValueError:
        return stripped


def classify_keep_alive_policy(value: str | int) -> str:
    if isinstance(value, int):
        if value == 0:
            return KEEP_ALIVE_POLICY_UNLOAD_IMMEDIATELY
        if value < 0:
            return KEEP_ALIVE_POLICY_PINNED_KEEPALIVE
        if value <= 60:
            return KEEP_ALIVE_POLICY_SHORT_KEEPALIVE
        return KEEP_ALIVE_POLICY_DEFAULT_KEEPALIVE

    stripped = value.strip().lower()
    if stripped == "0":
        return KEEP_ALIVE_POLICY_UNLOAD_IMMEDIATELY
    if stripped.startswith("-"):
        return KEEP_ALIVE_POLICY_PINNED_KEEPALIVE
    if stripped.endswith("s"):
        try:
            seconds = int(stripped[:-1])
        except ValueError:
            return KEEP_ALIVE_POLICY_CUSTOM
        return (
            KEEP_ALIVE_POLICY_SHORT_KEEPALIVE
            if seconds <= 60
            else KEEP_ALIVE_POLICY_DEFAULT_KEEPALIVE
        )
    if stripped in {"1m", "30s", "60s"}:
        return KEEP_ALIVE_POLICY_SHORT_KEEPALIVE
    if stripped in {"5m", "10m", "15m"}:
        return KEEP_ALIVE_POLICY_DEFAULT_KEEPALIVE
    return KEEP_ALIVE_POLICY_CUSTOM


def classify_model_size(model_name: str) -> str:
    lowered = normalize_ollama_model_name(model_name).lower()
    if "32b" in lowered or "70b" in lowered:
        return MODEL_SIZE_VERY_LARGE
    if "14b" in lowered or "8b" in lowered or "7b" in lowered:
        return MODEL_SIZE_LARGE
    if "3b" in lowered or "4b" in lowered:
        return MODEL_SIZE_MEDIUM
    return MODEL_SIZE_SMALL


def resource_risk_label(model_name: str) -> str:
    size = classify_model_size(model_name)
    if size == MODEL_SIZE_VERY_LARGE:
        return RESOURCE_RISK_EXTREME
    if size == MODEL_SIZE_LARGE:
        return RESOURCE_RISK_HIGH
    if size == MODEL_SIZE_MEDIUM:
        return RESOURCE_RISK_MODERATE
    return RESOURCE_RISK_LOW


def model_memory_notes(model_name: str) -> str:
    size = classify_model_size(model_name)
    if size == MODEL_SIZE_VERY_LARGE:
        return "32B-class local models can push the Windows host to its limits."
    if size == MODEL_SIZE_LARGE:
        return "7B/8B-class local models can consume several GB of memory."
    if size == MODEL_SIZE_MEDIUM:
        return "3B/4B-class local models are still significant on the dev host."
    return "Small/unknown local model; keep lifecycle conservative by default."


def _env_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _http_post_json(
    url: str, payload: dict[str, Any], timeout_seconds: float
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def _http_get_json(url: str, timeout_seconds: float) -> dict[str, Any]:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}
