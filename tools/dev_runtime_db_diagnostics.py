from __future__ import annotations

import dataclasses
import importlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _to_jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return _to_jsonable(dataclasses.asdict(value))

    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}

    if isinstance(value, list | tuple):
        return [_to_jsonable(item) for item in value]

    if isinstance(value, Path):
        return str(value)

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except TypeError:
            return str(value)

    if hasattr(value, "__dict__"):
        return _to_jsonable(vars(value))

    return value


def main() -> int:
    diagnostics_module = importlib.import_module("services.runtime_diagnostics_service")
    diagnostics = diagnostics_module.build_runtime_db_diagnostics()

    print(json.dumps(_to_jsonable(diagnostics), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
