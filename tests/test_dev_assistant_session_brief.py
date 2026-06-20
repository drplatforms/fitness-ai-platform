from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def load_dev_assistant():
    module_path = Path("tools/dev_assistant.py")
    spec = importlib.util.spec_from_file_location("dev_assistant", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["dev_assistant"] = module
    spec.loader.exec_module(module)
    return module


def run_dev_assistant(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/dev_assistant.py", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_session_brief_command_is_discoverable() -> None:
    result = run_dev_assistant("--help")

    assert result.returncode == 0
    assert "session-brief" in result.stdout

    result = run_dev_assistant("session-brief", "--help")

    assert result.returncode == 0
    assert "--out" in result.stdout


def test_session_brief_writes_utf8_output(tmp_path: Path) -> None:
    dev_assistant = load_dev_assistant()
    output_path = tmp_path / "session_brief.txt"

    dev_assistant.write_session_brief(
        str(output_path),
        milestone="Supercharger v1.1 - Session Brief Command",
    )

    assert output_path.exists()

    output = output_path.read_text(encoding="utf-8")

    required_sections = [
        "AI Health Coach",
        "Git Status",
        "Recent Commits",
        "Dev Assistant Status",
        "Memory Check",
        "Stale Doc Check",
        "Suggested Next Action",
        "Snapshot Command",
        "Linux Sync Reminder",
    ]

    for section in required_sections:
        assert section in output

    assert "Supercharger v1.1 - Session Brief Command" in output


def test_session_brief_avoids_known_bad_characters(tmp_path: Path) -> None:
    dev_assistant = load_dev_assistant()
    output_path = tmp_path / "session_brief.txt"

    dev_assistant.write_session_brief(str(output_path))

    output = output_path.read_text(encoding="utf-8")

    assert "ù" not in output
    assert "\f" not in output


def test_session_brief_does_not_mutate_source_files(tmp_path: Path) -> None:
    dev_assistant = load_dev_assistant()
    source_files = [
        Path("tools/dev_assistant.py"),
        Path("docs/project_memory/development_workflow.md"),
    ]
    before = {path: path.read_bytes() for path in source_files}

    output_path = tmp_path / "session_brief.txt"
    dev_assistant.write_session_brief(str(output_path))

    assert output_path.exists()

    after = {path: path.read_bytes() for path in source_files}
    assert after == before
