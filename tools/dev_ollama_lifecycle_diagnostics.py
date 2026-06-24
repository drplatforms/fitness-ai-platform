from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.provider_lifecycle_service import (  # noqa: E402
    get_ollama_lifecycle_status,
    render_provider_lifecycle_summary,
    resolve_ollama_base_url,
    resolve_provider_lifecycle_policy,
    unload_ollama_model,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Developer-only Ollama lifecycle diagnostics for AI Health Coach."
    )
    parser.add_argument("--policy", action="store_true", help="Print lifecycle policy.")
    parser.add_argument(
        "--status", action="store_true", help="Read safe Ollama status."
    )
    parser.add_argument(
        "--unload",
        metavar="MODEL",
        help="Explicitly request unload for one named Ollama model.",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5:3b",
        help="Model name used when rendering policy. Defaults to qwen2.5:3b.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Optional Ollama base URL. Defaults to OLLAMA_BASE_URL or localhost.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=5.0,
        help="HTTP timeout for status/unload calls.",
    )
    args = parser.parse_args()

    if not args.policy and not args.status and not args.unload:
        args.policy = True

    output: dict[str, object] = {
        "developer_tool": "dev_ollama_lifecycle_diagnostics",
        "normal_ui_changed": False,
        "provider_generation_attempted": False,
        "ollama_base_url": resolve_ollama_base_url(base_url=args.base_url),
    }

    if args.policy:
        policy = resolve_provider_lifecycle_policy(model_name=args.model)
        output["policy"] = render_provider_lifecycle_summary(policy)

    if args.status:
        output["status"] = get_ollama_lifecycle_status(
            base_url=args.base_url,
            timeout_seconds=args.timeout_seconds,
        ).to_dict()

    if args.unload:
        output["unload"] = unload_ollama_model(
            model_name=args.unload,
            base_url=args.base_url,
            timeout_seconds=args.timeout_seconds,
        ).to_dict()

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
