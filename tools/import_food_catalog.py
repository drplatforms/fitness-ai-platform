"""CLI for deterministic staged food catalog imports."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalog_import_common import run_catalog_import_cli


def main() -> int:
    return run_catalog_import_cli(
        "food",
        "Import local food candidate data into staged review artifacts.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
