"""Developer workflow assistant for AI Health Coach.

This script is intentionally read-only. It summarizes local Git state,
suggests safe next actions, recommends tests, and generates copy/paste
handoff/PR templates without modifying files, committing, or pushing.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_BASE_BRANCHES = [
    "feature/coaching-decision-layer",
    "origin/feature/coaching-decision-layer",
    "main",
    "origin/main",
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


def recommend_next_action(short_status: str, upstream_status: str) -> str:
    if short_status:
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


def main() -> None:
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


if __name__ == "__main__":
    main()
