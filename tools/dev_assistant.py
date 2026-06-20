"""Developer workflow assistant for AI Health Coach.

This script is intentionally read-only except for explicit local artifact
commands such as session-brief. It summarizes local Git state, suggests
safe next actions, recommends tests, and generates copy/paste handoff/PR
templates without committing, pushing, or changing product/runtime files.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_BASE_BRANCHES = [
    "feature/coaching-decision-layer",
    "origin/feature/coaching-decision-layer",
    "main",
    "origin/main",
]

SOURCE_OF_TRUTH_DOCS = [
    "AGENTS.md",
    "docs/project_memory/current_state.md",
    "docs/project_memory/product_vision.md",
    "docs/project_memory/architecture_principles.md",
    "docs/project_memory/backend_truth_contract.md",
    "docs/project_memory/ai_boundaries.md",
    "docs/project_memory/section_registry_summary.md",
    "docs/project_memory/development_workflow.md",
    "docs/project_memory/agent_workflow.md",
    "docs/project_memory/open_questions.md",
]

FOCUSED_SAFETY_TESTS = [
    "pytest tests/test_project_memory_check.py -q",
    "pytest tests/test_daily_coach_narrative_preview_route.py -q",
    "pytest tests/test_daily_coach_narrative_preview_service.py -q",
    "pytest tests/test_daily_next_action_service.py -q",
    "pytest tests/test_report_persistence_boundary.py -q",
    "pytest tests/test_full_report_section_registry.py -q",
]


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def run_command(command: list[str]) -> CommandResult:
    """Run a command and capture output."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    return CommandResult(
        command=command,
        returncode=result.returncode,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
    )


def get_output(command: list[str], fallback: str = "Unavailable") -> str:
    result = run_command(command)

    if result.returncode != 0:
        return fallback

    return result.stdout or fallback


def print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def split_lines(value: str) -> list[str]:
    if not value:
        return []

    return [line.strip() for line in value.splitlines() if line.strip()]


def unique_sorted(values: list[str]) -> list[str]:
    return sorted(set(values))


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value[:60] or "milestone"


def path_exists(path: str) -> bool:
    return Path(path).exists()


def get_current_branch() -> str:
    return get_output(["git", "branch", "--show-current"])


def get_latest_commit() -> str:
    return get_output(["git", "log", "-1", "--oneline", "--decorate"])


def get_latest_commit_hash() -> str:
    return get_output(["git", "rev-parse", "--short", "HEAD"])


def get_latest_commit_subject() -> str:
    return get_output(["git", "log", "-1", "--pretty=%s"])


def get_recent_commits() -> str:
    return get_output(["git", "log", "--oneline", "--decorate", "-7"])


def get_recent_commits_8() -> str:
    return get_output(["git", "log", "--oneline", "--decorate", "-8"])


def get_short_status() -> str:
    return get_output(["git", "status", "--short"], fallback="")


def get_full_status() -> str:
    return get_output(["git", "status"])


def get_diff_stat() -> str:
    return get_output(["git", "diff", "--stat"], fallback="")


def get_staged_diff_stat() -> str:
    return get_output(["git", "diff", "--cached", "--stat"], fallback="")


def get_upstream_status() -> str:
    return get_output(["git", "status", "-sb"])


def get_changed_files() -> list[str]:
    unstaged = split_lines(get_output(["git", "diff", "--name-only"], fallback=""))
    staged = split_lines(
        get_output(["git", "diff", "--cached", "--name-only"], fallback="")
    )
    untracked = []

    for line in split_lines(get_short_status()):
        if line.startswith("?? "):
            untracked.append(line.replace("?? ", "", 1).strip())

    return unique_sorted(unstaged + staged + untracked)


def branch_exists(branch: str) -> bool:
    result = run_command(["git", "rev-parse", "--verify", branch])
    return result.returncode == 0


def choose_base_branch(current_branch: str) -> str:
    for branch in DEFAULT_BASE_BRANCHES:
        if branch == current_branch:
            continue

        if branch_exists(branch):
            return branch

    return "origin/main"


def get_branch_changed_files(base_branch: str) -> list[str]:
    output = get_output(
        ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
        fallback="",
    )
    return unique_sorted(split_lines(output))


def is_only_qa_artifacts_untracked(short_status: str) -> bool:
    lines = split_lines(short_status)
    if not lines:
        return False

    return all(line.startswith("?? qa_artifacts/") for line in lines)


def recommend_next_action(short_status: str, upstream_status: str) -> str:
    if short_status:
        if is_only_qa_artifacts_untracked(short_status):
            return (
                "Only qa_artifacts appears untracked. Recommended next step:\n"
                "1. Treat qa_artifacts as local handoff output.\n"
                "2. Do not stage or commit qa_artifacts.\n"
                "3. Continue validation, handoff, snapshot, or merge flow as scoped."
            )

        return (
            "Working tree has changes. Recommended next step:\n"
            "1. Review changes with: git status\n"
            "2. Review summary with: git diff --stat\n"
            "3. Run checks before committing: pre-commit run --all-files"
        )

    if "ahead" in upstream_status and "behind" in upstream_status:
        return (
            "Branch is both ahead and behind its upstream. Recommended next step:\n"
            "1. Stop and inspect carefully.\n"
            "2. Run: git status\n"
            "3. Ask for help before pulling, rebasing, or pushing."
        )

    if "ahead" in upstream_status:
        return (
            "Branch has local commits not pushed yet. Recommended next step:\n"
            "1. Push the branch.\n"
            "2. Open or update the pull request."
        )

    if "behind" in upstream_status:
        return (
            "Branch is behind its upstream. Recommended next step:\n"
            "1. Pull latest changes with: git pull\n"
            "2. Re-run tests/checks after pulling."
        )

    return (
        "Working tree is clean. Recommended next step:\n"
        "1. Continue work on this branch, or\n"
        "2. Generate a milestone handoff, or\n"
        "3. Open/update a pull request if the milestone is complete."
    )


def add_if_exists(recommendations: list[str], command: str, path: str) -> None:
    if path_exists(path):
        recommendations.append(command)


def recommend_tests(changed_files: list[str]) -> list[str]:
    recommendations: list[str] = []

    if not changed_files:
        return [
            "pre-commit run --all-files",
            "pytest -q",
        ]

    if any(file.startswith("ui/") for file in changed_files):
        recommendations.append("python -m py_compile ui/streamlit_app.py")

    if any(
        file.startswith("tools/") or file.startswith("docs/project_memory")
        for file in changed_files
    ):
        add_if_exists(
            recommendations,
            "pytest tests/test_project_memory_check.py -q",
            "tests/test_project_memory_check.py",
        )
        if path_exists("tools/dev_assistant.py"):
            recommendations.append("python -m py_compile tools/dev_assistant.py")
        if path_exists("tools/project_memory_check.py"):
            recommendations.append("python -m py_compile tools/project_memory_check.py")

    if any(file.startswith("api/") for file in changed_files):
        add_if_exists(
            recommendations,
            "pytest tests/test_api_smoke.py -q",
            "tests/test_api_smoke.py",
        )

    if any("user_state" in file for file in changed_files):
        add_if_exists(
            recommendations,
            "pytest tests/test_user_state_service.py -q",
            "tests/test_user_state_service.py",
        )

    if any("coaching_decision" in file for file in changed_files):
        add_if_exists(
            recommendations,
            "pytest tests/test_coaching_decision_service.py -q",
            "tests/test_coaching_decision_service.py",
        )

    if any("recommendation" in file for file in changed_files):
        add_if_exists(
            recommendations,
            "pytest tests/test_grounded_recommendation_engine.py -q",
            "tests/test_grounded_recommendation_engine.py",
        )
        add_if_exists(
            recommendations,
            "pytest tests/test_recommendation_candidate_service.py -q",
            "tests/test_recommendation_candidate_service.py",
        )
        add_if_exists(
            recommendations,
            "pytest tests/test_recommendation_runtime.py -q",
            "tests/test_recommendation_runtime.py",
        )

    if any("report" in file or "coordinator" in file for file in changed_files):
        add_if_exists(
            recommendations,
            "pytest tests/test_report_language_validator.py -q",
            "tests/test_report_language_validator.py",
        )
        add_if_exists(
            recommendations,
            "pytest tests/test_report_status.py -q",
            "tests/test_report_status.py",
        )

    if any(file.startswith("scripts/seed_qa_scenarios") for file in changed_files):
        add_if_exists(
            recommendations,
            "pytest tests/test_seed_qa_scenarios.py -q",
            "tests/test_seed_qa_scenarios.py",
        )

    recommendations.extend(
        [
            "pre-commit run --all-files",
            "pytest -q",
        ]
    )

    return unique_sorted(recommendations)


def suggest_recipient_chat(changed_files: list[str]) -> str:
    if not changed_files:
        return "DevOps & Tooling or the active milestone chat"

    if any(
        file.startswith("tools/") or file in {".gitignore", "pyproject.toml"}
        for file in changed_files
    ):
        return "DevOps & Tooling"

    if any(file.startswith("ui/") for file in changed_files):
        return "Streamlit UI"

    if any(file.startswith("tests/") for file in changed_files):
        return "QA & Testing"

    if any(file.startswith("agents/") for file in changed_files):
        return "Agent Engineering"

    if any(
        file.startswith("api/") or file.startswith("services/")
        for file in changed_files
    ):
        return "Backend Development"

    if any(
        file.startswith("docs/") or file.lower().endswith(".md")
        for file in changed_files
    ):
        return "Architecture & System Design or DevOps & Tooling"

    return "DevOps & Tooling or the active milestone chat"


def format_file_list(files: list[str], limit: int = 15) -> str:
    if not files:
        return "- None"

    visible = files[:limit]
    rendered = "\n".join(f"- {file}" for file in visible)

    if len(files) > limit:
        rendered += f"\n- ...and {len(files) - limit} more"

    return rendered


def generate_handoff_template(
    branch: str,
    latest_commit: str,
    changed_files: list[str],
    recipient_chat: str,
) -> str:
    return f"""Project sync — AI Health Coach

Source of truth:
Branch: {branch}
Commit: {latest_commit}

Suggested recipient chat:
{recipient_chat}

Milestone completed:
<fill in milestone name>

What changed:
- <fill in>
- <fill in>
- <fill in>

Validation:
- pre-commit: <pass/fail/not run>
- pytest: <pass/fail/not run>
- manual QA: <pass/fail/not run>

Important files:
{format_file_list(changed_files)}

Current architecture note:
<fill in if architecture changed>

Known limitations:
<fill in or "None known">

Next recommended milestone:
<fill in>
"""


def generate_pr_template(changed_files: list[str], recommended_tests: list[str]) -> str:
    return f"""## Summary

- <fill in main change>
- <fill in supporting change>
- <fill in validation/cleanup change>

## Important files

{format_file_list(changed_files)}

## Validation

{chr(10).join(f"- [ ] `{test}`" for test in recommended_tests)}
"""


def generate_snapshot_name(commit_hash: str, commit_subject: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(commit_subject)
    return f"fitness_ai_snapshot_{today}_{commit_hash}_{slug}.zip"


def generate_snapshot_command() -> str:
    return r"""$commit = git rev-parse --short HEAD
$date = Get-Date -Format "yyyy-MM-dd"
$commitMessage = git log -1 --pretty=%s

$safeMessage = $commitMessage -replace '[^a-zA-Z0-9]+', '-'
$safeMessage = $safeMessage.ToLower().Trim('-')

$zipName = "..\fitness_ai_snapshot_${date}_${commit}_${safeMessage}.zip"

git archive --format=zip --output=$zipName HEAD

Write-Host "Created snapshot:"
Write-Host $zipName

Get-Item $zipName"""


def generate_linux_sync_command(branch: str | None = None) -> str:
    selected_branch = branch or get_current_branch() or "main"
    return f"""cd ~/projects/fitness-ai-platform

git fetch origin
git switch {selected_branch} || git switch --track origin/{selected_branch}
git pull --ff-only origin {selected_branch}

git status -sb
git log --oneline -5"""


def generate_windows_push_command(branch: str | None = None) -> str:
    selected_branch = branch or get_current_branch() or "<branch-name>"
    return f"""cd C:\\projects\\fitness_ai

git status --short
git log --oneline -5
git push -u origin {selected_branch}"""


def generate_runtime_restart_commands(ollama_base_url: str) -> str:
    return f"""# Linux deterministic-safe FastAPI restart.
# OLLAMA_BASE_URL only tells FastAPI where Windows Ollama lives.
# It does not make provider output the default.

cd ~/projects/fitness-ai-platform

unset RECOMMENDATION_CANDIDATE_PROVIDER
unset NUTRITION_EXPLANATION_PROVIDER
export OLLAMA_BASE_URL={ollama_base_url}

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Connectivity check from Linux to Windows Ollama:
curl -s {ollama_base_url}/api/tags | head

# Daily Coach Narrative direct_ollama lane smoke test:
curl -s "http://127.0.0.1:8000/daily-coach/102/narrative-preview/debug?provider=direct_ollama&model=qwen3:8b&date=2026-06-19&timeout_seconds=180" | python -m json.tool

# Streamlit alternate-port restart when 8501 is occupied:
streamlit run ui/streamlit_app.py --server.address 0.0.0.0 --server.port 8502"""


def generate_validation_block() -> str:
    checks = [
        "git diff --check",
        "powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code",
        ".\\.venv\\Scripts\\python.exe -m py_compile tools\\dev_assistant.py",
        ".\\.venv\\Scripts\\python.exe -m py_compile tools\\project_memory_check.py",
        ".\\.venv\\Scripts\\python.exe -m pytest tests\\test_project_memory_check.py -q",
    ]
    return "\n".join(checks)


def generate_agent_prompt(target: str, milestone: str) -> str:
    branch = get_current_branch()
    commit = get_latest_commit()
    source_docs = "\n".join(f"- {doc}" for doc in SOURCE_OF_TRUTH_DOCS)
    focused_tests = "\n".join(f"- {test}" for test in FOCUSED_SAFETY_TESTS)
    return f"""Recipient:
{target}

Project:
AI Health Coach / fitness-ai

Branch:
{branch}

Latest commit:
{commit}

Milestone:
{milestone}

Role:
You are a scoped implementation worker. You are not the Architecture owner, milestone owner, or final approver.

Source-of-truth docs to read first:
{source_docs}

Core doctrine:
- Backend owns truth.
- AI explains backend-approved truth only.
- Validators enforce reality.
- Deterministic fallback remains default.
- Provider defaults must not change.
- qwen3 is not production-approved.
- Do not loosen validators.
- Do not add Claude workflow files or commands.

Scope:
<fill in exact approved scope>

Strict non-goals:
- no product/runtime behavior changes unless explicitly scoped
- no provider behavior changes unless explicitly scoped
- no validator loosening
- no deterministic fallback weakening
- no broad rewrites
- no staged artifacts or snapshots

Expected files:
<fill in expected files>

Validation commands:
{focused_tests}

Acceptance criteria:
<fill in pass criteria>

Artifact rules:
- Do not stage *.zip or *.patch files.
- Do not stage artifacts/, qa_artifacts/, runtime output, or local DB copies.
- User owns final commit, push, merge, and snapshot.
"""


def generate_context_pack(target: str, milestone: str) -> str:
    branch = get_current_branch()
    commit = get_latest_commit()
    recent = get_recent_commits()
    docs = "\n".join(f"- {doc}" for doc in SOURCE_OF_TRUTH_DOCS)
    return f"""AI Health Coach context pack

Target: {target}
Milestone: {milestone}
Branch: {branch}
Latest commit: {commit}

Read order:
{docs}

Recent commits:
{recent}

Non-negotiable boundaries:
- backend owns facts/calculations/validation/persistence/fallback
- AI/provider output is never source of truth
- deterministic fallback remains default
- provider lanes remain opt-in/manual/debug unless explicitly promoted
- raw provider output/prompts/payloads/validation internals stay out of normal UI/API
- do not add CLAUDE.md or Claude-specific commands
- do not stage patch/snapshot/runtime artifacts

Windows path:
C:\\projects\\fitness_ai

Linux path:
~/projects/fitness-ai-platform

Linux provider-lane note:
FastAPI may set OLLAMA_BASE_URL to reach Windows Ollama without changing provider defaults.
"""


def generate_qa_plan(milestone: str) -> str:
    focused_tests = "\n".join(f"- {test}" for test in FOCUSED_SAFETY_TESTS)
    return f"""QA plan — {milestone}

Static checks:
- git diff --check
- scripts/dev_commit_check.ps1 -Mode code

Focused tests:
{focused_tests}

Manual checks:
- Confirm expected surfaces exist only where scoped.
- Confirm normal product UI is unchanged unless explicitly scoped.
- Confirm no raw provider output, prompts, payloads, validation internals, stack traces, or rejected text leak.
- Confirm deterministic fallback remains available.
- Confirm provider defaults did not change.

Artifact checks:
- git status --short
- git diff --cached --name-only
- no *.zip snapshots staged
- no *.patch files staged
- no artifacts/ or qa_artifacts/ staged

Result format:
PASS / PARTIAL PASS / FAIL

Notes:
- <fill in>
"""


def get_project_memory_check_text() -> str:
    try:
        from project_memory_check import format_results, run_project_memory_check
    except Exception as exc:  # pragma: no cover - defensive CLI fallback
        return f"Project memory check unavailable: {exc}"

    results = run_project_memory_check(".")
    return format_results(results)


def build_session_brief(milestone: str | None = None) -> str:
    branch = get_current_branch()
    latest_commit = get_latest_commit()
    latest_commit_hash = get_latest_commit_hash()
    latest_commit_subject = get_latest_commit_subject()
    short_status = get_short_status()
    upstream_status = get_upstream_status()
    recent_commits = get_recent_commits_8()
    snapshot_name = generate_snapshot_name(latest_commit_hash, latest_commit_subject)
    next_action = recommend_next_action(short_status, upstream_status)

    memory_check = get_project_memory_check_text()
    stale_doc_check = get_project_memory_check_text()

    lines = [
        "AI Health Coach - Developer Workflow Assistant",
        "=" * 72,
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "Project: AI Health Coach / fitness-ai",
    ]

    if milestone:
        lines.append(f"Milestone: {milestone}")

    lines.extend(
        [
            f"Current branch: {branch}",
            f"Latest commit: {latest_commit}",
            "",
            "Git Status",
            "-" * 72,
            upstream_status,
            "",
            "git status --short:",
            short_status or "Clean - no uncommitted changes.",
            "",
            "Recent Commits",
            "-" * 72,
            recent_commits,
            "",
            "Dev Assistant Status",
            "-" * 72,
            f"Branch: {branch}",
            f"Latest commit: {latest_commit}",
            f"Suggested snapshot filename: {snapshot_name}",
            "",
            "Memory Check",
            "-" * 72,
            memory_check,
            "",
            "Stale Doc Check",
            "-" * 72,
            stale_doc_check,
            "",
            "Suggested Next Action",
            "-" * 72,
            next_action,
            "",
            "Snapshot Command",
            "-" * 72,
            generate_snapshot_command(),
            "",
            "Linux Sync Reminder",
            "-" * 72,
            generate_linux_sync_command(branch),
            "",
            "Artifact Rules",
            "-" * 72,
            "- qa_artifacts is local handoff output and should not be committed.",
            "- Do not stage snapshots, patches, local DB files, logs, raw provider output, or Headroom artifacts.",
            "- Do not include secrets, provider payloads, or local database contents in handoff briefs.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def write_session_brief(output_path: str, milestone: str | None = None) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_session_brief(milestone), encoding="utf-8")
    return path


def print_status_report() -> None:
    branch = get_current_branch()
    latest_commit = get_latest_commit()
    latest_commit_hash = get_latest_commit_hash()
    latest_commit_subject = get_latest_commit_subject()
    recent_commits = get_recent_commits()
    short_status = get_short_status()
    full_status = get_full_status()
    diff_stat = get_diff_stat()
    staged_diff_stat = get_staged_diff_stat()
    upstream_status = get_upstream_status()

    base_branch = choose_base_branch(branch)
    working_tree_files = get_changed_files()
    branch_files = get_branch_changed_files(base_branch)
    analysis_files = working_tree_files or branch_files

    recommended_tests = recommend_tests(analysis_files)
    recipient_chat = suggest_recipient_chat(analysis_files)
    next_action = recommend_next_action(short_status, upstream_status)
    handoff_template = generate_handoff_template(
        branch=branch,
        latest_commit=latest_commit,
        changed_files=analysis_files,
        recipient_chat=recipient_chat,
    )
    pr_template = generate_pr_template(
        changed_files=analysis_files,
        recommended_tests=recommended_tests,
    )
    snapshot_name = generate_snapshot_name(latest_commit_hash, latest_commit_subject)

    print_section("AI Health Coach — Developer Workflow Assistant")

    print(f"Branch:\n{branch}")
    print()
    print(f"Latest commit:\n{latest_commit}")
    print()
    print(f"Base branch used for branch diff:\n{base_branch}")

    print_section("Git upstream/status summary")
    print(upstream_status)

    print_section("Working tree")
    if short_status:
        print(short_status)
    else:
        print("Clean — no uncommitted changes.")

    print_section("Unstaged diff summary")
    if diff_stat:
        print(diff_stat)
    else:
        print("No unstaged diff.")

    print_section("Staged diff summary")
    if staged_diff_stat:
        print(staged_diff_stat)
    else:
        print("No staged diff.")

    print_section("Files changed in working tree")
    print(format_file_list(working_tree_files))

    print_section(f"Files changed on branch vs {base_branch}")
    print(format_file_list(branch_files))

    print_section("Recommended tests/checks")
    for command in recommended_tests:
        print(f"- {command}")

    print_section("Suggested recipient chat")
    print(recipient_chat)

    print_section("Suggested snapshot filename")
    print(snapshot_name)

    print_section("Snapshot command")
    print(generate_snapshot_command())

    print_section("Linux sync after snapshot")
    print(generate_linux_sync_command(branch))

    print_section("Runtime restart / provider-lane commands")
    print(generate_runtime_restart_commands("http://192.168.1.104:11434"))

    print_section("PR description template")
    print(pr_template)

    print_section("Chat handoff template")
    print(handoff_template)

    print_section("Recent commits")
    print(recent_commits)

    print_section("Suggested next action")
    print(next_action)

    print_section("Full git status")
    print(full_status)


def run_memory_check() -> int:
    from project_memory_check import (
        format_results,
        has_failures,
        run_project_memory_check,
    )

    results = run_project_memory_check(".")
    print(format_results(results))
    return 1 if has_failures(results) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only developer workflow assistant for AI Health Coach."
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Print repo state and workflow guidance.")
    subparsers.add_parser("memory-check", help="Run project-memory existence checks.")
    subparsers.add_parser(
        "stale-doc-check", help="Run project-memory stale-doc checks."
    )

    agent_prompt = subparsers.add_parser(
        "agent-prompt", help="Generate a scoped coding-agent prompt."
    )
    agent_prompt.add_argument("target", choices=["codex", "aider", "copilot"])
    agent_prompt.add_argument("--milestone", required=True)

    context_pack = subparsers.add_parser(
        "context-pack", help="Generate a compact context pack for a coding helper."
    )
    context_pack.add_argument(
        "--target", choices=["codex", "aider", "copilot"], required=True
    )
    context_pack.add_argument("--milestone", required=True)

    qa_plan = subparsers.add_parser("qa-plan", help="Generate a milestone QA plan.")
    qa_plan.add_argument("--milestone", required=True)

    session_brief = subparsers.add_parser(
        "session-brief",
        help="Write a clean UTF-8 uploadable session brief to a local artifact file.",
    )
    session_brief.add_argument(
        "--out", required=True, help="Output path for the brief."
    )
    session_brief.add_argument("--milestone", default=None)

    snapshot_command = subparsers.add_parser(
        "snapshot-command", help="Print snapshot and Linux sync commands."
    )
    snapshot_command.add_argument("--branch", default=None)

    runtime_restart = subparsers.add_parser(
        "runtime-restart",
        help="Print deterministic-safe restart/provider-lane commands.",
    )
    runtime_restart.add_argument(
        "--ollama-base-url",
        default="http://192.168.1.104:11434",
        help="Windows-hosted Ollama base URL reachable from Linux FastAPI.",
    )

    sync = subparsers.add_parser(
        "sync-commands", help="Print Windows push and Linux pull blocks."
    )
    sync.add_argument("--branch", default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in {None, "status"}:
        print_status_report()
        return 0

    if args.command in {"memory-check", "stale-doc-check"}:
        return run_memory_check()

    if args.command == "agent-prompt":
        print(generate_agent_prompt(args.target, args.milestone))
        return 0

    if args.command == "context-pack":
        print(generate_context_pack(args.target, args.milestone))
        return 0

    if args.command == "qa-plan":
        print(generate_qa_plan(args.milestone))
        return 0

    if args.command == "session-brief":
        output_path = write_session_brief(args.out, args.milestone)
        print(f"Session brief written to: {output_path}")
        return 0

    if args.command == "snapshot-command":
        print_section("Windows snapshot command")
        print(generate_snapshot_command())
        print_section("Linux sync after snapshot")
        print(generate_linux_sync_command(args.branch))
        return 0

    if args.command == "runtime-restart":
        print(generate_runtime_restart_commands(args.ollama_base_url))
        return 0

    if args.command == "sync-commands":
        print_section("Windows push command")
        print(generate_windows_push_command(args.branch))
        print_section("Linux pull/sync command")
        print(generate_linux_sync_command(args.branch))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
