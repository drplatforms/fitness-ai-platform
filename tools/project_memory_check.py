"""Read-only project-memory consistency checks for AI Health Coach."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MemoryCheckResult:
    status: str
    path: str
    message: str


REQUIRED_FILES = [
    "AGENTS.md",
    ".github/copilot-instructions.md",
    "docs/project_memory/current_state.md",
    "docs/project_memory/product_vision.md",
    "docs/project_memory/architecture_principles.md",
    "docs/project_memory/backend_truth_contract.md",
    "docs/project_memory/ai_boundaries.md",
    "docs/project_memory/section_registry_summary.md",
    "docs/project_memory/future_architecture_ledger.md",
    "docs/project_memory/premium_platform_blueprint.md",
    "docs/project_memory/open_questions.md",
    "docs/project_memory/milestones/provider_narrative_qa_matrix_v2.md",
    "docs/project_memory/reviews/provider_narrative_qa_matrix_v2.md",
    "docs/project_memory/runtime_qa/provider_narrative_qa_matrix_v2_results.md",
    "docs/project_memory/development_workflow.md",
    "docs/project_memory/agent_workflow.md",
]

STALE_MARKERS = {
    "docs/project_memory/current_state.md": [
        "Latest accepted milestone\n\n`Daily Coach Narrative Developer Preview v1`",
        "Current implementation milestone\n\n`Daily Coach Narrative Async Today Preview Design v1`",
        "`Exercise Catalog Import Batch v1` is accepted.\n\nFinal accepted status",
        "feature/daily-coach-narrative-limited-today-ui-readiness-v1",
    ],
}

FORBIDDEN_CURRENT_CLAIMS = {
    "docs/project_memory/current_state.md": [
        "DAILY_COACH_NARRATIVE_SAME_SESSION_APPROVED_PREVIEW_BRIDGE_V1_ACCEPTED",
        "qwen3:32b is promoted",
        "qwen3:32b is production",
        "Daily Coach provider narrative persistence is approved",
    ],
    "docs/project_memory/ai_boundaries.md": [
        "qwen3:32b is promoted",
        "same-session approved display is accepted",
        "Daily Coach provider narrative persistence is approved",
    ],
    "docs/project_memory/premium_platform_blueprint.md": [
        "qwen3:32b is promoted",
        "same-session approved display is accepted",
        "Daily Coach provider narrative persistence is approved",
    ],
}

REQUIRED_PHRASES = {
    "AGENTS.md": [
        "docs/project_memory",
        "Backend owns facts",
        "Deterministic fallback remains the default",
        "Do not add `CLAUDE.md`",
        "Project memory update requirement",
    ],
    ".github/copilot-instructions.md": [
        "Backend owns facts",
        "Preserve deterministic fallback behavior",
        "Do not add Claude workflow files",
        "Project memory update requirement",
    ],
    "docs/project_memory/agent_workflow.md": [
        "ChatGPT",
        "Codex",
        "Dev Assistant",
        "Claude",
        "Out of scope",
    ],
    "docs/project_memory/development_workflow.md": [
        "OLLAMA_BASE_URL",
        "Windows owns source-of-truth repo work",
        "Linux owns runtime/staging QA",
    ],
    "docs/project_memory/future_architecture_ledger.md": [
        "RAG",
        "Vector",
        "MoE",
        "MCP",
        "frontend",
        "This ledger records direction. It does not authorize implementation.",
    ],
    "docs/project_memory/premium_platform_blueprint.md": [
        "premium",
        "RAG",
        "vector",
        "MoE",
        "MCP",
        "qwen3:32b",
        "This document is aspirational. It does not authorize implementation of all features.",
    ],
    "docs/project_memory/milestones/provider_narrative_qa_matrix_v2.md": [
        "Provider Narrative QA Matrix v2",
        "qwen2.5:3b",
        "not a provider promotion milestone",
        "no provider output to normal Today UI",
    ],
    "docs/project_memory/reviews/provider_narrative_qa_matrix_v2.md": [
        "Provider Narrative QA Matrix v2",
        "AWAITING RUNTIME MATRIX RESULTS",
        "Do not accept this milestone until the runtime matrix results are present",
        "no model promotion",
    ],
    "docs/project_memory/runtime_qa/provider_narrative_qa_matrix_v2_results.md": [
        "Provider Narrative QA Matrix v2 Results",
        "does not promote any model",
        "does not approve same-session display",
    ],
    "docs/project_memory/current_state.md": [
        "Project Memory Alignment + North Star Architecture v1",
        "feature/daily-coach-narrative-same-session-approved-preview-bridge-v1",
        "reference-only",
        "No provider may run on normal Today page load",
        "Provider Narrative QA Matrix v2",
    ],
    "docs/project_memory/ai_boundaries.md": [
        "Deterministic fallback remains the default",
        "Daily Coach Narrative provider lanes are manual/developer-gated preview",
        "future premium coach candidate",
    ],
}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def run_project_memory_check(project_root: Path | str = ".") -> list[MemoryCheckResult]:
    """Return PASS/WARN/FAIL project-memory consistency results."""
    root = Path(project_root)
    results: list[MemoryCheckResult] = []

    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        if path.exists():
            results.append(
                MemoryCheckResult("PASS", relative_path, "Required file exists.")
            )
        else:
            results.append(
                MemoryCheckResult("FAIL", relative_path, "Required file is missing.")
            )

    claude_path = root / "CLAUDE.md"
    if claude_path.exists():
        results.append(
            MemoryCheckResult(
                "FAIL",
                "CLAUDE.md",
                "Claude-specific workflow file is out of scope for this project.",
            )
        )
    else:
        results.append(
            MemoryCheckResult("PASS", "CLAUDE.md", "Claude workflow file absent.")
        )

    for relative_path, phrases in REQUIRED_PHRASES.items():
        path = root / relative_path
        if not path.exists():
            continue
        text = _read_text(path)
        for phrase in phrases:
            if phrase in text:
                results.append(
                    MemoryCheckResult(
                        "PASS", relative_path, f"Contains required phrase: {phrase}"
                    )
                )
            else:
                results.append(
                    MemoryCheckResult(
                        "WARN", relative_path, f"Missing expected phrase: {phrase}"
                    )
                )

    for relative_path, markers in STALE_MARKERS.items():
        path = root / relative_path
        if not path.exists():
            continue
        text = _read_text(path)
        for marker in markers:
            if marker in text:
                results.append(
                    MemoryCheckResult(
                        "WARN",
                        relative_path,
                        f"Possible stale milestone wording found: {marker}",
                    )
                )

    for relative_path, forbidden_claims in FORBIDDEN_CURRENT_CLAIMS.items():
        path = root / relative_path
        if not path.exists():
            continue
        text = _read_text(path)
        for claim in forbidden_claims:
            if claim in text:
                results.append(
                    MemoryCheckResult(
                        "FAIL",
                        relative_path,
                        f"Forbidden current-state claim found: {claim}",
                    )
                )

    return results


def format_results(results: list[MemoryCheckResult]) -> str:
    lines = ["Project memory check results:"]
    for result in results:
        lines.append(f"[{result.status}] {result.path} — {result.message}")
    summary = summarize_results(results)
    lines.append("")
    lines.append(
        "Summary: "
        f"PASS={summary['PASS']} WARN={summary['WARN']} FAIL={summary['FAIL']}"
    )
    return "\n".join(lines)


def summarize_results(results: list[MemoryCheckResult]) -> dict[str, int]:
    return {
        "PASS": sum(result.status == "PASS" for result in results),
        "WARN": sum(result.status == "WARN" for result in results),
        "FAIL": sum(result.status == "FAIL" for result in results),
    }


def has_failures(results: list[MemoryCheckResult]) -> bool:
    return any(result.status == "FAIL" for result in results)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run read-only AI Health Coach project-memory checks."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root to inspect. Defaults to current directory.",
    )
    args = parser.parse_args()

    results = run_project_memory_check(args.project_root)
    print(format_results(results))
    return 1 if has_failures(results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
