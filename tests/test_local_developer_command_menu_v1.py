from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMAND_SCRIPT = ROOT / "scripts" / "fitness_commands.ps1"
INSTALLER_SCRIPT = ROOT / "scripts" / "install_fitness_commands_profile.ps1"
COMMAND_DOC = ROOT / "docs" / "project_memory" / "local_developer_command_menu.md"


REQUIRED_COMMANDS = [
    "fitness",
    "cdf",
    "gsync",
    "gstate",
    "gcheck",
    "gacp",
    "app",
    "wapp",
    "lupdate",
    "lstatus",
    "lsetup",
    "lrestart",
    "lstop",
    "lsh",
    "fsnap",
    "fpull",
    "fbranch",
    "fmerge",
    "fsweep",
    "fmem",
    "fports",
    "fkill",
    "fdoctor",
    "lpull",
    "lvalidate",
    "lollama",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_function(text: str, name: str) -> str:
    start = text.index(f"function {name}")
    next_function = text.find("\nfunction ", start + 1)
    if next_function == -1:
        return text[start:]
    return text[start:next_function]


def test_repo_owned_command_script_exists() -> None:
    assert COMMAND_SCRIPT.exists()
    assert INSTALLER_SCRIPT.exists()
    assert COMMAND_DOC.exists()


def test_command_script_defines_required_commands() -> None:
    text = read(COMMAND_SCRIPT)
    for command in REQUIRED_COMMANDS:
        assert f"function {command}" in text


def test_command_menu_lists_current_and_new_commands() -> None:
    text = read(COMMAND_SCRIPT)
    for command in [
        "app",
        "wapp",
        "lstop",
        "lrestart",
        "lupdate",
        "fsnap",
        "fbranch",
        "fmerge",
        "lollama",
    ]:
        assert command in text


def test_command_script_encodes_project_runtime_truths() -> None:
    text = read(COMMAND_SCRIPT)
    assert "C:\\projects\\fitness_ai" in text
    assert "~/projects/fitness-ai-platform" in text
    assert "dusty@itsAlwaysDNS" in text
    assert "http://127.0.0.1:11434" in text
    assert "http://192.168.1.104:11434" in text
    assert "8510" in text
    assert "FITNESS_WINDOWS_REPO" in text
    assert "FITNESS_LINUX_REPO" in text
    assert "FITNESS_LINUX_SSH" in text
    assert "FITNESS_WINDOWS_OLLAMA_URL" in text
    assert "FITNESS_LINUX_OLLAMA_URL" in text
    assert "FITNESS_LINUX_STREAMLIT_URL" in text


def test_command_script_preserves_workflow_safety_rules() -> None:
    text = read(COMMAND_SCRIPT)
    assert "git merge-base --is-ancestor" in text
    assert "Stage explicit expected files" in text
    assert "No staged files" in text
    assert "Refusing to commit on main" in text
    assert "STOP: working tree is dirty" in text
    assert "git archive --format=zip" in text
    assert "qa_artifacts" not in text


def test_profile_installer_is_guarded_and_non_destructive() -> None:
    text = read(INSTALLER_SCRIPT)
    assert "Copy-Item" in text
    assert "AI Health Coach command menu" in text
    assert "fitness_commands.ps1" in text
    assert "Add-Content" in text
    assert "Remove-Item $PROFILE" not in text
    assert "Set-Content $PROFILE" not in text


def test_command_docs_reference_install_and_runtime_assumptions() -> None:
    text = read(COMMAND_DOC)
    assert (
        "scripts/fitness_commands.ps1" in text
        or "scripts\\fitness_commands.ps1" in text
    )
    assert "install_fitness_commands_profile.ps1" in text
    assert "C:\\projects\\fitness_ai" in text
    assert "~/projects/fitness-ai-platform" in text
    assert "http://127.0.0.1:11434" in text
    assert "http://192.168.1.104:11434" in text
    assert "git merge-base --is-ancestor" in text
    assert "wapp" in text
    assert "Linux is the canonical" in text or "Canonical app runtime" in text


def test_command_artifacts_do_not_include_citations_or_obvious_secrets() -> None:
    combined = "\n".join(
        read(path) for path in [COMMAND_SCRIPT, INSTALLER_SCRIPT, COMMAND_DOC]
    )
    forbidden = [
        "content" + "Reference",
        "oai" + "cite",
        "file" + "cite",
        "utm_source=" + "chatgpt",
        "chatgpt" + ".com",
        "BEGIN OPENSSH PRIVATE KEY",
        "api_key=",
        "password=",
    ]
    for marker in forbidden:
        assert marker not in combined


def test_linux_status_and_pull_commands_use_safe_bash_payloads() -> None:
    text = read(COMMAND_SCRIPT)
    assert "git log -5 --oneline --decorate" in text
    assert "git log --oneline -5" not in text
    assert "find . -maxdepth 3 -type f \\(" not in text
    assert "find . -maxdepth 3 -type f \\\\(" not in text
    assert "DB files:" in text
    assert "printf '%s\\n' 'DB files:'" in text


def test_app_is_linux_canonical_and_wapp_is_windows_local() -> None:
    text = read(COMMAND_SCRIPT)
    app_block = extract_function(text, "app")
    wapp_block = extract_function(text, "wapp")

    assert "lrestart" in app_block
    assert "FitnessLinuxStreamlitUrl" in app_block
    assert "Start-Process powershell" not in app_block
    assert "uvicorn api.main:app" not in app_block
    assert "streamlit run ui/streamlit_app.py" not in app_block

    assert "Windows-local FastAPI + Streamlit" in wapp_block
    assert "Start-Process powershell" in wapp_block
    assert "uvicorn api.main:app" in wapp_block
    assert "streamlit run ui/streamlit_app.py" in wapp_block
    assert "FitnessWindowsOllamaUrl" in wapp_block


def test_command_menu_labels_linux_app_and_windows_local_escape_hatch() -> None:
    text = read(COMMAND_SCRIPT)
    assert "app       Start Linux FastAPI + Streamlit and open app" in text
    assert "wapp      Start Windows-local FastAPI + Streamlit" in text
    assert "fports    Show Windows-side app/Ollama ports only" in text
    assert "Windows-side ports only" in extract_function(text, "fports")


def test_linux_runtime_uses_tmux_sessions_and_8501() -> None:
    text = read(COMMAND_SCRIPT)
    lrestart_block = extract_function(text, "lrestart")
    lstop_block = extract_function(text, "lstop")

    assert "tmux new -d -s fitness-api" in lrestart_block
    assert "tmux new -d -s fitness-ui" in lrestart_block
    assert "tmux kill-session -t fitness-api" in lrestart_block
    assert "tmux kill-session -t fitness-ui" in lrestart_block
    assert "nohup" not in lrestart_block
    assert "FitnessLinuxStreamlitPort" in lrestart_block
    assert "--server.port $script:FitnessLinuxStreamlitPort" in lrestart_block
    assert "export OLLAMA_BASE_URL=$script:FitnessLinuxOllamaUrl" in lrestart_block

    assert "tmux kill-session -t fitness-api" in lstop_block
    assert "tmux kill-session -t fitness-ui" in lstop_block


def test_linux_streamlit_port_is_separate_from_windows_local_port() -> None:
    text = read(COMMAND_SCRIPT)
    assert "$script:FitnessStreamlitPort" in text
    assert "$script:FitnessLinuxStreamlitPort" in text
    assert "else { 8510 }" in text
    assert "else { 8501 }" in text
    assert "http://${linuxHost}:$script:FitnessLinuxStreamlitPort" in text


def test_lrestart_keeps_linux_runtime_using_windows_ollama() -> None:
    text = read(COMMAND_SCRIPT)
    lrestart_block = extract_function(text, "lrestart")
    assert "export OLLAMA_BASE_URL=$script:FitnessLinuxOllamaUrl" in lrestart_block
    assert "python -m uvicorn api.main:app --host 0.0.0.0" in lrestart_block
    assert "python -m streamlit run ui/streamlit_app.py" in lrestart_block
    assert "tmux new -d -s fitness-ui" in lrestart_block
    assert "nohup" not in lrestart_block


def test_lollama_uses_printf_without_literal_newline_suffix() -> None:
    text = read(COMMAND_SCRIPT)
    lollama_block = text[text.index("function lollama") :]
    assert "Checking Windows Ollama from Linux" in lollama_block
    assert "printf '%s\\n'" in lollama_block
    assert "api/tags\\\\n" not in lollama_block
    assert "echo 'Windows Ollama reachable from Linux.'" not in lollama_block
