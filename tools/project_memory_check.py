"""Read-only project-memory consistency checks for AI Health Coach."""

from __future__ import annotations

import argparse
import json
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
    "docs/project_memory/project_continuity_bootstrap.md",
    "docs/project_memory/project_state.json",
    "docs/project_memory/role_bootstrap_architecture.md",
    "docs/project_memory/role_bootstrap_backend.md",
    "docs/project_memory/role_bootstrap_qa.md",
    "docs/project_memory/role_bootstrap_devops_tooling.md",
    "docs/project_memory/current_workflow_contract.md",
    "docs/project_memory/next_milestone.md",
    "docs/project_memory/chat_onboarding_test.md",
    "docs/project_memory/milestones/project_continuity_system_v2.md",
    "docs/project_memory/reviews/project_continuity_system_v2.md",
    "docs/project_memory/product_vision.md",
    "docs/project_memory/architecture_principles.md",
    "docs/project_memory/backend_truth_contract.md",
    "docs/project_memory/ai_boundaries.md",
    "docs/project_memory/section_registry_summary.md",
    "docs/project_memory/future_architecture_ledger.md",
    "docs/project_memory/premium_platform_blueprint.md",
    "docs/project_memory/developer_delivery_workflow_contract.md",
    "docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md",
    "scripts/install_fitness_commands_profile.ps1",
    "scripts/fitness_commands.ps1",
    "docs/project_memory/reviews/local_developer_command_menu_v1.md",
    "docs/project_memory/milestones/local_developer_command_menu_v1.md",
    "docs/project_memory/local_developer_command_menu.md",
    "docs/project_memory/designs/async_daily_coach_narrative_design_v1.md",
    "docs/project_memory/milestones/async_daily_coach_narrative_design_v1.md",
    "docs/project_memory/reviews/async_daily_coach_narrative_design_v1.md",
    "docs/project_memory/plans/async_daily_coach_narrative_implementation_plan_v1.md",
    "docs/project_memory/milestones/async_daily_coach_narrative_implementation_plan_v1.md",
    "docs/project_memory/reviews/async_daily_coach_narrative_implementation_plan_v1.md",
    "docs/project_memory/milestones/daily_coach_async_contracts_data_model_v1.md",
    "docs/project_memory/reviews/daily_coach_async_contracts_data_model_v1.md",
    "docs/project_memory/milestones/daily_coach_async_service_shell_no_worker_v1.md",
    "docs/project_memory/reviews/daily_coach_async_service_shell_no_worker_v1.md",
    "docs/project_memory/milestones/daily_coach_async_developer_only_prototype_v1.md",
    "docs/project_memory/reviews/daily_coach_async_developer_only_prototype_v1.md",
    "docs/project_memory/designs/daily_coach_async_provider_runtime_design_v1.md",
    "docs/project_memory/designs/daily_coach_async_persistence_design_v1.md",
    "docs/project_memory/milestones/daily_coach_async_persistence_contracts_schema_v1.md",
    "docs/project_memory/reviews/daily_coach_async_persistence_contracts_schema_v1.md",
    "docs/project_memory/milestones/daily_coach_async_persistence_service_shell_v1.md",
    "docs/project_memory/reviews/daily_coach_async_persistence_service_shell_v1.md",
    "docs/project_memory/reviews/developer_mode_persistence_inspection_v1.md",
    "docs/project_memory/milestones/developer_mode_persistence_inspection_v1.md",
    "docs/project_memory/milestones/daily_coach_async_provider_runtime_prototype_v1.md",
    "docs/project_memory/reviews/daily_coach_async_provider_runtime_prototype_v1.md",
    "docs/project_memory/milestones/daily_coach_async_provider_runtime_qa_hardening_v1.md",
    "docs/project_memory/reviews/daily_coach_async_provider_runtime_qa_hardening_v1.md",
    "docs/project_memory/designs/daily_coach_async_approved_preview_bridge_design_v1.md",
    "docs/project_memory/milestones/daily_coach_async_approved_preview_bridge_design_v1.md",
    "docs/project_memory/reviews/daily_coach_async_approved_preview_bridge_design_v1.md",
    "docs/project_memory/milestones/daily_coach_async_approved_preview_bridge_implementation_v1.md",
    "docs/project_memory/reviews/daily_coach_async_approved_preview_bridge_implementation_v1.md",
    "docs/project_memory/milestones/daily_coach_async_approved_preview_bridge_qa_v1.md",
    "docs/project_memory/reviews/daily_coach_async_approved_preview_bridge_qa_v1.md",
    "docs/project_memory/patterns/async_job_delivery_pattern_v1.md",
    "docs/project_memory/milestones/async_job_delivery_pattern_playbook_v1.md",
    "docs/project_memory/reviews/async_job_delivery_pattern_playbook_v1.md",
    "docs/project_memory/milestones/next_async_job_candidate_selection_v1.md",
    "docs/project_memory/reviews/next_async_job_candidate_selection_v1.md",
    "docs/project_memory/milestones/weekly_coach_summary_async_contracts_data_model_v1.md",
    "docs/project_memory/reviews/weekly_coach_summary_async_contracts_data_model_v1.md",
    "services/weekly_coach_summary_service.py",
    "tests/test_weekly_coach_summary_service.py",
    "tools/dev_weekly_coach_summary_preview.py",
    "docs/project_memory/milestones/weekly_coach_summary_async_service_shell_no_worker_v1.md",
    "docs/project_memory/reviews/weekly_coach_summary_async_service_shell_no_worker_v1.md",
    "tests/test_streamlit_weekly_coach_summary_developer_mode.py",
    "docs/project_memory/milestones/weekly_coach_summary_developer_mode_inspection_v1.md",
    "docs/project_memory/reviews/weekly_coach_summary_developer_mode_inspection_v1.md",
    "services/weekly_coach_summary_persistence_service.py",
    "tests/test_weekly_coach_summary_persistence_service.py",
    "docs/project_memory/milestones/weekly_coach_summary_async_persistence_v1.md",
    "docs/project_memory/reviews/weekly_coach_summary_async_persistence_v1.md",
    "tools/dev_weekly_coach_summary_latency_probe.py",
    "docs/project_memory/milestones/weekly_coach_summary_persistence_latency_investigation_v1.md",
    "docs/project_memory/reviews/weekly_coach_summary_persistence_latency_investigation_v1.md",
    "services/weekly_coach_summary_qa_data_service.py",
    "tests/test_weekly_coach_summary_qa_data_service.py",
    "docs/project_memory/milestones/weekly_coach_summary_date_range_qa_data_debug_v1.md",
    "docs/project_memory/reviews/weekly_coach_summary_date_range_qa_data_debug_v1.md",
    "docs/project_memory/handoffs/architecture_handoff_current.md",
    "docs/project_memory/handoffs/backend_handoff_current.md",
    "docs/project_memory/handoffs/qa_handoff_current.md",
    "docs/project_memory/open_questions.md",
    "docs/project_memory/milestones/provider_narrative_qa_matrix_v2.md",
    "docs/project_memory/reviews/provider_narrative_qa_matrix_v2.md",
    "docs/project_memory/runtime_qa/provider_narrative_qa_matrix_v2_results.md",
    "docs/project_memory/milestones/developer_delivery_workflow_contract_v1.md",
    "docs/project_memory/reviews/developer_delivery_workflow_contract_v1.md",
    "docs/project_memory/milestones/developer_delivery_workflow_script_safety_addendum_v1.md",
    "docs/project_memory/reviews/developer_delivery_workflow_script_safety_addendum_v1.md",
    "docs/project_memory/milestones/daily_coach_same_session_approved_preview_bridge_v1_retry.md",
    "docs/project_memory/reviews/daily_coach_same_session_approved_preview_bridge_v1_retry.md",
    "docs/project_memory/milestones/same_session_bridge_runtime_qa_v1.md",
    "docs/project_memory/reviews/same_session_bridge_runtime_qa_v1.md",
    "docs/project_memory/runtime_qa/same_session_bridge_runtime_qa_v1_results.md",
    "docs/project_memory/milestones/daily_coach_narrative_product_voice_polish_v1.md",
    "docs/project_memory/reviews/daily_coach_narrative_product_voice_polish_v1.md",
    "docs/project_memory/runtime_qa/daily_coach_narrative_product_voice_polish_v1_results.md",
    "docs/project_memory/milestones/daily_coach_narrative_product_voice_runtime_qa_v1.md",
    "docs/project_memory/reviews/daily_coach_narrative_product_voice_runtime_qa_v1.md",
    "docs/project_memory/runtime_qa/daily_coach_narrative_product_voice_runtime_qa_v1_results.md",
    "docs/project_memory/development_workflow.md",
    "docs/project_memory/agent_workflow.md",
]

STALE_MARKERS = {
    "docs/project_memory/current_state.md": [
        "Latest accepted milestone\n\n`Daily Coach Narrative Developer Preview v1`",
        "Current implementation milestone\n\n`Daily Coach Narrative Async Today Preview Design v1`",
        "`Exercise Catalog Import Batch v1` is accepted.\n\nFinal accepted status",
        "feature/daily-coach-narrative-limited-today-ui-readiness-v1",
        "Daily Coach Async Persistence Service Shell v1",
        "DAILY_COACH_ASYNC_PERSISTENCE_SERVICE_SHELL_V1_ACCEPTED",
        "Developer Mode Persistence Inspection v1",
        "feature/developer-mode-persistence-inspection-v1",
        "Developer Mode-only read-only inspection",
        "raw provider output display",
        "rejected provider output display",
        "full prompt/raw context/scratchpad display",
    ],
}

FORBIDDEN_CURRENT_CLAIMS = {
    "docs/project_memory/current_state.md": [
        "DAILY_COACH_NARRATIVE_SAME_SESSION_APPROVED_PREVIEW_BRIDGE_V1_ACCEPTED",
        "qwen3:32b is promoted",
        "qwen3:32b is production",
        "Daily Coach provider narrative persistence is approved",
        "Daily Coach async persistence implementation is approved",
        "raw provider output persistence is approved",
        "rejected provider output persistence is approved",
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
    "docs/project_memory/project_state.json": [
        "Daily Coach Async Provider Runtime Design v1",
        "DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED",
        "Project Continuity System v2",
        "feature/project-continuity-system-v2",
        "Daily Coach Async Persistence Design v1",
        "DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED",
        "Daily Coach Async Persistence Contracts + Schema v1",
        "feature/daily-coach-async-persistence-contracts-schema-v1",
        "provider runtime implementation",
        "raw provider output persistence",
        "rejected provider output persistence",
        "C:\\projects",
        "Daily Coach Async Persistence Service Shell v1",
        "feature/daily-coach-async-persistence-service-shell-v1",
        "service/repository shell only",
        "python ..\\<script>.py",
        "git apply --check ..\\<patch>.patch",
        "qwen3",
        "not bridge-enabled",
        "qwen3:32b",
        "research / future premium async candidate only",
        "Deterministic fallback remains mandatory.",
        "normal Today provider call",
        "public async narrative display",
        "Daily Coach Async Provider Runtime Prototype v1",
        "feature/daily-coach-async-provider-runtime-prototype-v1",
        "Developer Mode-only manual provider runtime prototype",
        "provider disabled by default",
        "manual trigger only",
    ],
    "docs/project_memory/role_bootstrap_architecture.md": [
        "Architecture owns",
        "Architecture does not implement",
        "Architecture acceptance can be ACCEPTED",
        "merge commands only when merge is actually the next action",
        "Long milestone handoffs must be in one copy/paste-ready code block",
        "qwen3 is not bridge-enabled",
        "normal Today provider call",
    ],
    "docs/project_memory/role_bootstrap_backend.md": [
        "Do not infer project rules from memory alone",
        "phase-separated delivery",
        "Every phase has one purpose",
        "Never stage with `git add .`",
        "C:\\projects",
        "python ..\\<script>.py",
        "git apply --check ..\\<patch>.patch",
        "Snapshot only after commit",
        "Linux pull immediately after snapshot",
        "Do not run broad formatters for docs-only work",
    ],
    "docs/project_memory/role_bootstrap_qa.md": [
        "QA validates behavior and boundary preservation",
        "PASS WITH NOTES",
        "normal UI does not leak provider/debug/runtime internals",
        "snapshots are not committed",
        "qa_artifacts are not committed",
    ],
    "docs/project_memory/role_bootstrap_devops_tooling.md": [
        "Windows is the source-of-truth development/control machine",
        "Linux is the canonical FastAPI + Streamlit runtime",
        "`app` launches/manages Linux FastAPI + Streamlit runtime",
        "`wapp` is Windows-local only",
        "Do not confuse `app` and `wapp`",
        "Do not reset/stash/clean on Linux unless diagnosing a dirty tree",
    ],
    "docs/project_memory/current_workflow_contract.md": [
        "phase-separated delivery",
        "Never use `git add .`",
        "temporary apply scripts and patch files live outside the repo",
        "C:\\projects",
        "python ..\\<script>.py",
        "git apply --check ..\\<patch>.patch",
        "Do not run broad formatters for docs-only work",
        "Linux pull happens immediately after snapshot",
        "Long handoffs must be in one copy/paste-ready code block",
        "Deterministic fallback remains mandatory",
        "qwen3 is not bridge-enabled",
        "qwen3:32b is research / future premium async candidate only",
        "normal Today provider call",
        "public async narrative display",
    ],
    "docs/project_memory/next_milestone.md": [
        "Daily Coach Async Provider Runtime Design v1",
        "DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED",
        "Project Continuity System v2",
        "Daily Coach Async Persistence Design v1",
        "DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED",
        "Daily Coach Async Persistence Contracts + Schema v1",
        "feature/daily-coach-async-persistence-contracts-schema-v1",
        "schema/contracts",
        "NOT_AUTHORIZED_YET",
    ],
    "docs/project_memory/milestones/daily_coach_async_persistence_service_shell_v1.md": [
        "Daily Coach Async Persistence Service Shell v1",
        "daily_coach_async_jobs",
        "daily_coach_approved_narratives",
        "service/repository shell only",
        "raw provider output persistence",
        "rejected provider output persistence",
        "no provider runtime",
        "Codex do not use by default",
    ],
    "docs/project_memory/reviews/daily_coach_async_persistence_service_shell_v1.md": [
        "Daily Coach Async Persistence Service Shell v1",
        "DAILY_COACH_ASYNC_PERSISTENCE_SERVICE_SHELL_V1_ACCEPTED",
        "daily_coach_async_jobs",
        "daily_coach_approved_narratives",
        "no provider runtime",
        "no raw provider output persistence",
        "no rejected provider output persistence",
        "no Codex used by default",
    ],
    "docs/project_memory/chat_onboarding_test.md": [
        "What is the latest accepted milestone?",
        "Where should temporary apply scripts and patches live?",
        "Should docs-only work run `black .` or `ruff check . --fix`?",
        "Long handoffs must be in one copy/paste-ready code block",
        "C:\\projects",
        "qwen3 is not bridge-enabled",
    ],
    "docs/project_memory/milestones/project_continuity_system_v2.md": [
        "Project Continuity System v2",
        "AUTHORIZED FOR BACKEND / DEVOPS TOOLING IMPLEMENTATION",
        "docs + tooling",
        "no Daily Coach provider runtime",
    ],
    "docs/project_memory/reviews/project_continuity_system_v2.md": [
        "Project Continuity System v2 Review",
        "PROJECT_CONTINUITY_SYSTEM_V2_ACCEPTED",
        "docs + tooling only",
        "no provider runtime",
    ],
    "docs/project_memory/project_continuity_bootstrap.md": [
        "Project Continuity Bootstrap",
        "Daily Coach Async Service Shell / No Worker v1",
        "Current Accepted Milestone Stack",
        "Sound right and be right",
        "app` command launches Linux runtime",
        "qwen3 is not bridge-enabled",
        "service shell only",
        "no provider runtime yet",
        "Daily Coach Async Developer-Only Prototype v1",
        "Developer Mode-only manual lifecycle prototype",
        "What Future Chats Must Do First",
    ],
    "docs/project_memory/designs/daily_coach_async_provider_runtime_design_v1.md": [
        "Daily Coach Async Provider Runtime Design v1",
        "design-only milestone",
        "Provider output must never be rendered directly.",
        "strict parser",
        "schema validation",
        "claim validation",
        "deterministic fallback remains mandatory",
        "qwen3 is not bridge-enabled",
        "qwen3:32b is research / future premium async candidate only",
        "same-process hard-timeout provider execution is treated as risky",
        "Daily Coach Async Persistence Design v1",
        "no provider execution implemented",
        "no normal Today provider call added",
        "no public async narrative display added",
    ],
    "docs/project_memory/milestones/daily_coach_async_persistence_contracts_schema_v1.md": [
        "Daily Coach Async Persistence Contracts + Schema v1",
        "daily_coach_async_jobs",
        "daily_coach_approved_narratives",
        "daily_coach_job_events deferred",
        "raw provider output must not be persisted",
        "rejected provider output must not be persisted",
        "no provider runtime",
    ],
    "docs/project_memory/reviews/daily_coach_async_persistence_contracts_schema_v1.md": [
        "Daily Coach Async Persistence Contracts + Schema v1",
        "DAILY_COACH_ASYNC_PERSISTENCE_CONTRACTS_SCHEMA_V1_ACCEPTED",
        "daily_coach_async_jobs",
        "daily_coach_approved_narratives",
        "no provider runtime",
        "no raw provider output persistence",
        "no rejected provider output persistence",
    ],
    "docs/project_memory/milestones/daily_coach_async_provider_runtime_prototype_v1.md": [
        "Daily Coach Async Provider Runtime Prototype v1",
        "Developer Mode",
        "manual provider trigger",
        "provider disabled by default",
        "strict JSON parser",
        "approved public-safe narrative persistence",
        "sanitized failure/fallback metadata only",
        "no normal Today provider call",
        "no public async narrative display",
        "no qwen3 bridge",
        "qwen3:32b promotion",
    ],
    "docs/project_memory/reviews/daily_coach_async_provider_runtime_prototype_v1.md": [
        "Daily Coach Async Provider Runtime Prototype v1",
        "DAILY_COACH_ASYNC_PROVIDER_RUNTIME_PROTOTYPE_V1_ACCEPTED",
        "Developer Mode-only provider runtime prototype",
        "manual trigger only",
        "provider disabled by default",
        "raw provider output not persisted",
        "rejected provider output not persisted",
        "full prompt/raw context/scratchpad not persisted",
        "no qwen3 call",
        "no public async narrative display",
    ],
    "docs/project_memory/milestones/daily_coach_async_developer_only_prototype_v1.md": [
        "Daily Coach Async Developer-Only Prototype v1",
        "Developer Mode",
        "manual lifecycle harness",
        "no provider execution",
        "no DB persistence",
        "normal Today behavior remains unchanged",
        "DAILY_COACH_ASYNC_DEVELOPER_ONLY_PROTOTYPE_V1_ACCEPTED",
    ],
    "docs/project_memory/reviews/daily_coach_async_developer_only_prototype_v1.md": [
        "Daily Coach Async Developer-Only Prototype v1",
        "READY FOR ARCHITECTURE REVIEW",
        "DAILY_COACH_ASYNC_DEVELOPER_ONLY_PROTOTYPE_V1_ACCEPTED",
        "no provider execution",
        "no qwen3 call",
        "no normal Today provider call",
    ],
    "AGENTS.md": [
        "docs/project_memory",
        "Backend owns facts",
        "Deterministic fallback remains the default",
        "Do not add `CLAUDE.md`",
        "Project memory update requirement",
        "developer_delivery_workflow_contract.md",
        "developer_delivery_workflow_script_safety_addendum_v1.md",
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
    "docs/project_memory/developer_delivery_workflow_contract.md": [
        "Patch-first delivery is the default",
        "Snapshot restore is a fallback, not the normal path",
        "When Dustin provides a snapshot filename",
        "C:\\projects\\fitness_ai",
        "~/projects/fitness-ai-platform",
        "OLLAMA_BASE_URL=",
        "http://192.168.1.104:11434",
    ],
    "docs/project_memory/milestones/developer_delivery_workflow_contract_v1.md": [
        "Developer Delivery Workflow Contract v1",
        "patch-first delivery is default",
        "Linux pull-after-snapshot is a hard rule",
    ],
    "docs/project_memory/reviews/developer_delivery_workflow_contract_v1.md": [
        "Developer Delivery Workflow Contract v1",
        "DEVELOPER_DELIVERY_WORKFLOW_CONTRACT_V1_ACCEPTED",
        "docs/tooling only",
    ],
    "docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md": [
        "git merge-base --is-ancestor <accepted-final-feature-commit> main",
        "A clean working tree is not proof that the correct milestone was merged.",
        "phase-separated",
        "stop before push, snapshot, or Linux pull",
    ],
    "docs/project_memory/milestones/developer_delivery_workflow_script_safety_addendum_v1.md": [
        "Developer Delivery Workflow Script Safety Addendum v1",
        "git merge-base --is-ancestor",
        "Docs/tooling only",
    ],
    "docs/project_memory/reviews/developer_delivery_workflow_script_safety_addendum_v1.md": [
        "Developer Delivery Workflow Script Safety Addendum v1",
        "DEVELOPER_DELIVERY_WORKFLOW_SCRIPT_SAFETY_ADDENDUM_V1_ACCEPTED",
        "Docs/tooling only",
    ],
    "docs/project_memory/milestones/daily_coach_same_session_approved_preview_bridge_v1_retry.md": [
        "Daily Coach Same-Session Approved Preview Bridge v1 Retry",
        "qwen2.5:3b",
        "session-state",
        "nothing is persisted",
    ],
    "docs/project_memory/reviews/daily_coach_same_session_approved_preview_bridge_v1_retry.md": [
        "Daily Coach Same-Session Approved Preview Bridge v1 Retry",
        "DAILY_COACH_SAME_SESSION_APPROVED_PREVIEW_BRIDGE_V1_RETRY_ACCEPTED",
        "session-only",
        "no provider call occurs on normal Today load",
    ],
    "docs/project_memory/milestones/same_session_bridge_runtime_qa_v1.md": [
        "Same-Session Bridge Runtime QA v1",
        "RUNTIME QA PASS",
        "qwen2.5:3b",
        "No provider call occurred on normal Today load",
    ],
    "docs/project_memory/reviews/same_session_bridge_runtime_qa_v1.md": [
        "Same-Session Bridge Runtime QA v1",
        "SAME_SESSION_BRIDGE_RUNTIME_QA_V1_ACCEPTED",
        "session-only",
        "no persistence",
    ],
    "docs/project_memory/runtime_qa/same_session_bridge_runtime_qa_v1_results.md": [
        "Same-Session Bridge Runtime QA v1 Results",
        "Status: PASS",
        "RUNTIME_APPROVED_SESSION_DISPLAY",
        "No provider call occurred on normal Today load",
        "No DB/report/file persistence was observed",
    ],
    "docs/project_memory/milestones/daily_coach_narrative_product_voice_polish_v1.md": [
        "Daily Coach Narrative Product Voice Polish v1",
        "sound right and be right",
        "qwen2.5:3b",
        "No provider call occurs on normal Today load",
    ],
    "docs/project_memory/reviews/daily_coach_narrative_product_voice_polish_v1.md": [
        "Daily Coach Narrative Product Voice Polish v1",
        "DAILY_COACH_NARRATIVE_PRODUCT_VOICE_POLISH_V1_ACCEPTED",
        "No validation loosening",
        "Generic/meta copy is blocked or flagged",
    ],
    "docs/project_memory/runtime_qa/daily_coach_narrative_product_voice_polish_v1_results.md": [
        "Daily Coach Narrative Product Voice Polish v1 Runtime QA Results",
        "LOCAL MANUAL QA REQUIRED",
        "qwen2.5:3b",
        "No provider call occurs on normal Today load",
    ],
    "docs/project_memory/milestones/daily_coach_narrative_product_voice_runtime_qa_v1.md": [
        "Daily Coach Narrative Product Voice Runtime QA v1",
        "DAILY_COACH_NARRATIVE_PRODUCT_VOICE_RUNTIME_QA_V1_ACCEPTED",
        "qwen2.5:3b",
        "PASS_WITH_NOTE",
    ],
    "docs/project_memory/reviews/daily_coach_narrative_product_voice_runtime_qa_v1.md": [
        "Daily Coach Narrative Product Voice Runtime QA v1",
        "DAILY_COACH_NARRATIVE_PRODUCT_VOICE_RUNTIME_QA_V1_ACCEPTED",
        "No provider call occurs on normal Today load",
        "No persistence",
    ],
    "docs/project_memory/runtime_qa/daily_coach_narrative_product_voice_runtime_qa_v1_results.md": [
        "Daily Coach Narrative Product Voice Runtime QA v1 Results",
        "Status: PASS",
        "PASS_WITH_NOTE",
        "approximately `22.5 seconds`",
        "No DB/report/file persistence",
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
        "No model is promoted by this report.",
        "No same-session approval was added by this matrix.",
    ],
    "docs/project_memory/local_developer_command_menu.md": [
        "scripts/fitness_commands.ps1",
        "install_fitness_commands_profile.ps1",
        "C:\\projects\\fitness_ai",
        "~/projects/fitness-ai-platform",
        "http://127.0.0.1:11434",
        "http://192.168.1.104:11434",
        "fitness",
        "app",
        "wapp",
        "Linux is the canonical",
        "Windows-local",
        "lstop",
        "lrestart",
        "lupdate",
        "fmerge",
        "git merge-base --is-ancestor",
    ],
    "docs/project_memory/milestones/local_developer_command_menu_v1.md": [
        "Local Developer Command Menu Audit + Repo-Owned Commands v1",
        "scripts/fitness_commands.ps1",
        "docs/tooling/local command changes only",
    ],
    "docs/project_memory/reviews/local_developer_command_menu_v1.md": [
        "Local Developer Command Menu Audit + Repo-Owned Commands v1",
        "LOCAL_DEVELOPER_COMMAND_MENU_V1_ACCEPTED",
        "PowerShell load smoke",
    ],
    "docs/project_memory/designs/async_daily_coach_narrative_design_v1.md": [
        "Async Daily Coach Narrative Design v1",
        "design-only milestone",
        "deterministic fallback remains always available",
        "qwen2.5:3b",
        "qwen3:32b",
        "future premium async candidate only",
        "not bridge-enabled",
        "not promoted",
        "not_requested",
        "queued",
        "generating",
        "provider_succeeded_pending_validation",
        "approved",
        "rejected_validation",
        "rejected_parse",
        "provider_timeout",
        "provider_error",
        "stale",
        "fallback_available",
        "daily_coach_narrative_jobs",
        "raw rejected output is not persisted by default",
        "No output displays unless all required gates pass.",
    ],
    "docs/project_memory/milestones/async_daily_coach_narrative_design_v1.md": [
        "Async Daily Coach Narrative Design v1",
        "IMPLEMENTED / READY FOR ARCHITECTURE REVIEW",
        "ASYNC_DAILY_COACH_NARRATIVE_DESIGN_V1_ACCEPTED",
        "No provider call occurs on normal Today load.",
        "Persistence is proposed only, not implemented.",
    ],
    "docs/project_memory/reviews/async_daily_coach_narrative_design_v1.md": [
        "Async Daily Coach Narrative Design v1 Review",
        "READY FOR ARCHITECTURE REVIEW",
        "ASYNC_DAILY_COACH_NARRATIVE_DESIGN_V1_ACCEPTED",
        "No async runtime implemented.",
        "qwen3 remains not bridge-enabled.",
        "Workflow contract followed.",
    ],
    "docs/project_memory/plans/async_daily_coach_narrative_implementation_plan_v1.md": [
        "Async Daily Coach Narrative Implementation Plan v1",
        "Daily Coach Async Contracts + Data Model v1",
        "No provider call occurs during normal Today load.",
        "qwen3:32b remains",
    ],
    "docs/project_memory/milestones/async_daily_coach_narrative_implementation_plan_v1.md": [
        "Async Daily Coach Narrative Implementation Plan v1",
        "ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1_ACCEPTED",
        "provider call on normal Today load",
    ],
    "docs/project_memory/reviews/async_daily_coach_narrative_implementation_plan_v1.md": [
        "Async Daily Coach Narrative Implementation Plan v1",
        "ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1_ACCEPTED",
        "async runtime",
    ],
    "docs/project_memory/milestones/daily_coach_async_contracts_data_model_v1.md": [
        "Daily Coach Async Contracts + Data Model v1",
        "contracts/data-model foundation only",
        "DailyCoachNarrativeJobStatus",
        "DailyCoachNarrativeModelLane",
        "DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED",
    ],
    "docs/project_memory/reviews/daily_coach_async_contracts_data_model_v1.md": [
        "Daily Coach Async Contracts + Data Model v1 Review",
        "DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED",
        "no async runtime implemented",
        "no provider execution added",
        "no DB schema change",
    ],
    "docs/project_memory/designs/daily_coach_async_approved_preview_bridge_design_v1.md": [
        "Daily Coach Async Approved Preview Bridge Design v1",
        "DESIGNED / READY FOR ARCHITECTURE REVIEW",
        "DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_DESIGN_V1_ACCEPTED",
        "Today preview must not run provider execution",
        "DAILY_COACH_ASYNC_APPROVED_PREVIEW_ENABLED=false",
        "deterministic Daily Next Action remains primary",
        "no provider call on Today render",
        "no provider call on page load",
        "qwen3 remains not bridge-enabled",
        "qwen3:32b remains not promoted",
    ],
    "docs/project_memory/milestones/daily_coach_async_approved_preview_bridge_design_v1.md": [
        "Daily Coach Async Approved Preview Bridge Design v1",
        "DESIGNED / READY FOR ARCHITECTURE REVIEW",
        "design-only milestone",
        "no Today preview bridge implemented",
        "no normal Today provider call",
    ],
    "docs/project_memory/reviews/daily_coach_async_approved_preview_bridge_design_v1.md": [
        "Daily Coach Async Approved Preview Bridge Design v1",
        "DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_DESIGN_V1_ACCEPTED",
        "design only",
        "no Today preview bridge implemented",
        "no provider call on Today render authorized",
    ],
    "docs/project_memory/milestones/daily_coach_async_approved_preview_bridge_implementation_v1.md": [
        "Daily Coach Async Approved Preview Bridge Implementation v1",
        "DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_IMPLEMENTATION_V1_ACCEPTED",
        "DAILY_COACH_ASYNC_APPROVED_PREVIEW_ENABLED=false",
        "no provider call on Today render",
        "deterministic Daily Next Action remains primary",
    ],
    "docs/project_memory/reviews/daily_coach_async_approved_preview_bridge_implementation_v1.md": [
        "Daily Coach Async Approved Preview Bridge Implementation v1",
        "DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_IMPLEMENTATION_V1_ACCEPTED",
        "feature flag disabled by default",
        "normal Today unchanged when disabled",
        "qwen3 remains not bridge-enabled",
    ],
    "docs/project_memory/milestones/daily_coach_async_approved_preview_bridge_qa_v1.md": [
        "Daily Coach Async Approved Preview Bridge QA v1",
        "DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_QA_V1_ACCEPTED",
        "no provider call",
        "no async job creation",
        "deterministic Daily Next Action remains primary",
    ],
    "docs/project_memory/reviews/daily_coach_async_approved_preview_bridge_qa_v1.md": [
        "Daily Coach Async Approved Preview Bridge QA v1",
        "DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_QA_V1_ACCEPTED",
        "no provider call",
        "no async job creation",
        "qwen3",
    ],
    "docs/project_memory/patterns/async_job_delivery_pattern_v1.md": [
        "Async Job Delivery Pattern / Playbook v1",
        "Canonical Async Job Lifecycle",
        "Minimum Data Model / Persistence Concepts",
        "Developer Mode Inspection Requirement",
        "Provider Runtime Pattern",
        "Preview Bridge Pattern",
        "Feature Flag Strategy",
        "QA Milestone Pattern",
        "Standard Milestone Templates",
        "Daily Coach Async Case Study",
        "lstop/lrestart/app are Windows PowerShell helper commands that SSH into Linux",
        "Fix lstop/lrestart/app SSH command CRLF handling",
    ],
    "docs/project_memory/milestones/async_job_delivery_pattern_playbook_v1.md": [
        "Async Job Delivery Pattern / Playbook v1",
        "IMPLEMENTED / READY FOR ARCHITECTURE REVIEW",
        "ASYNC_JOB_DELIVERY_PATTERN_PLAYBOOK_V1_ACCEPTED",
        "docs/pattern only",
        "no runtime behavior changed",
    ],
    "docs/project_memory/reviews/async_job_delivery_pattern_playbook_v1.md": [
        "Async Job Delivery Pattern / Playbook v1",
        "ASYNC_JOB_DELIVERY_PATTERN_PLAYBOOK_V1_ACCEPTED",
        "no runtime behavior changed",
        "lstop/lrestart/app CRLF issue recorded as backlog only",
    ],
    "docs/project_memory/milestones/weekly_coach_summary_async_contracts_data_model_v1.md": [
        "Weekly Coach Summary Async Contracts + Data Model v1",
        "WEEKLY_COACH_SUMMARY_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED",
        "contracts/data model only",
        "deterministic-first",
        "no provider runtime",
        "no persistence schema",
    ],
    "docs/project_memory/reviews/weekly_coach_summary_async_contracts_data_model_v1.md": [
        "Weekly Coach Summary Async Contracts + Data Model v1",
        "WEEKLY_COACH_SUMMARY_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED",
        "no weekly summary generation implemented",
        "no provider runtime added",
        "no raw provider output approval/display field",
    ],
    "docs/project_memory/milestones/weekly_coach_summary_async_service_shell_no_worker_v1.md": [
        "Weekly Coach Summary Async Service Shell / No Worker v1",
        "WEEKLY_COACH_SUMMARY_ASYNC_SERVICE_SHELL_NO_WORKER_V1_ACCEPTED",
        "deterministic",
        "developer-only preview",
        "No persistence schema",
        "No provider runtime",
    ],
    "docs/project_memory/reviews/weekly_coach_summary_async_service_shell_no_worker_v1.md": [
        "Weekly Coach Summary Async Service Shell / No Worker v1",
        "WEEKLY_COACH_SUMMARY_ASYNC_SERVICE_SHELL_NO_WORKER_V1_ACCEPTED",
        "ApprovedWeeklyCoachSummary",
        "deterministic fallback",
        "no provider runtime added",
    ],
    "docs/project_memory/milestones/weekly_coach_summary_developer_mode_inspection_v1.md": [
        "Weekly Coach Summary Developer Mode Inspection v1",
        "WEEKLY_COACH_SUMMARY_DEVELOPER_MODE_INSPECTION_V1_ACCEPTED",
        "Developer Mode-only",
        "no provider runtime",
        "no public/default display",
    ],
    "docs/project_memory/reviews/weekly_coach_summary_developer_mode_inspection_v1.md": [
        "Weekly Coach Summary Developer Mode Inspection v1",
        "WEEKLY_COACH_SUMMARY_DEVELOPER_MODE_INSPECTION_V1_ACCEPTED",
        "Developer Mode-only",
        "normal/default UI unchanged",
        "no provider runtime added",
    ],
    "docs/project_memory/milestones/weekly_coach_summary_async_persistence_v1.md": [
        "Weekly Coach Summary Async Persistence v1",
        "WEEKLY_COACH_SUMMARY_ASYNC_PERSISTENCE_V1_ACCEPTED",
        "approved/public-safe",
        "sanitized metadata",
        "no provider runtime",
    ],
    "docs/project_memory/reviews/weekly_coach_summary_async_persistence_v1.md": [
        "Weekly Coach Summary Async Persistence v1",
        "WEEKLY_COACH_SUMMARY_ASYNC_PERSISTENCE_V1_ACCEPTED",
        "no raw provider output persisted",
        "Duplicate Policy",
        "Developer Mode-only",
    ],
    "docs/project_memory/milestones/weekly_coach_summary_persistence_latency_investigation_v1.md": [
        "Weekly Coach Summary Persistence Latency Investigation v1",
        "WEEKLY_COACH_SUMMARY_PERSISTENCE_LATENCY_INVESTIGATION_V1_ACCEPTED",
        "Streamlit fragment reruns",
        "Developer Mode-only timing diagnostics",
        "no provider runtime",
    ],
    "docs/project_memory/reviews/weekly_coach_summary_persistence_latency_investigation_v1.md": [
        "Weekly Coach Summary Persistence Latency Investigation v1",
        "WEEKLY_COACH_SUMMARY_PERSISTENCE_LATENCY_INVESTIGATION_V1_ACCEPTED",
        "root cause",
        "before/after timing",
        "no provider runtime added",
    ],
    "docs/project_memory/milestones/weekly_coach_summary_date_range_qa_data_debug_v1.md": [
        "Weekly Coach Summary Date-Range QA Data Debug v1",
        "WEEKLY_COACH_SUMMARY_DATE_RANGE_QA_DATA_DEBUG_V1_ACCEPTED",
        "Developer Mode-only",
        "QA user/date-range",
        "live DB fact counts",
        "no provider runtime",
    ],
    "docs/project_memory/reviews/weekly_coach_summary_date_range_qa_data_debug_v1.md": [
        "Weekly Coach Summary Date-Range QA Data Debug v1",
        "WEEKLY_COACH_SUMMARY_DATE_RANGE_QA_DATA_DEBUG_V1_ACCEPTED",
        "selected user/date range honored",
        "raw rows not exposed",
        "no provider runtime added",
    ],
    "docs/project_memory/handoffs/architecture_handoff_current.md": [
        "Local Command Menu App Runtime Correction v1",
        "app` is now the canonical Linux runtime launcher",
        "wapp",
        "Linux is the canonical FastAPI + Streamlit app runtime",
    ],
    "docs/project_memory/handoffs/backend_handoff_current.md": [
        "Local Command Menu App Runtime Correction v1",
        "app` restarts Linux FastAPI + Streamlit through SSH",
        "wapp",
        "No backend app runtime code changed.",
    ],
    "docs/project_memory/handoffs/qa_handoff_current.md": [
        "Local Command Menu App Runtime Correction v1",
        "app` means Linux canonical app runtime",
        "wapp",
        "fports",
    ],
    "scripts/fitness_commands.ps1": [
        "function fitness",
        "function app",
        "function wapp",
        "function lstop",
        "function lrestart",
        "function lupdate",
        "function fsnap",
        "function fbranch",
        "function fmerge",
        "git merge-base --is-ancestor",
        "C:\\projects\\fitness_ai",
        "~/projects/fitness-ai-platform",
        "http://127.0.0.1:11434",
        "http://192.168.1.104:11434",
        "FITNESS_LINUX_STREAMLIT_URL",
        "FITNESS_LINUX_STREAMLIT_PORT",
        "8501",
        "fitness-ui",
        "fitness-api",
        "Windows-local FastAPI + Streamlit",
    ],
    "scripts/install_fitness_commands_profile.ps1": [
        "AI Health Coach command menu",
        "Copy-Item",
        "C:\\projects\\fitness_ai\\scripts\\fitness_commands.ps1",
        ". `$PROFILE",
    ],
    "docs/project_memory/current_state.md": [
        "Project Memory Alignment + North Star Architecture v1",
        "feature/daily-coach-narrative-same-session-approved-preview-bridge-v1",
        "reference-only",
        "No provider may run on normal Today page load",
        "Provider Narrative QA Matrix v2",
        "Daily Coach Same-Session Approved Preview Bridge v1 Retry",
        "Same-Session Bridge Runtime QA v1",
        "Daily Coach Narrative Product Voice Polish v1",
        "Daily Coach Narrative Product Voice Runtime QA v1",
        "PASS_WITH_NOTE",
        "sound right and be right",
        "Local Developer Command Menu Audit + Repo-Owned Commands v1",
        "scripts/fitness_commands.ps1",
        "Local Command Menu App Runtime Correction v1",
        "Linux is the canonical",
        "wapp",
        "Daily Coach Async Service Shell / No Worker v1",
        "service shell only",
        "no provider execution added",
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

    project_state_path = root / "docs/project_memory/project_state.json"
    if project_state_path.exists():
        try:
            state = json.loads(_read_text(project_state_path))
            if isinstance(state, dict) and state.get("project"):
                results.append(
                    MemoryCheckResult(
                        "PASS",
                        "docs/project_memory/project_state.json",
                        "Machine-readable project state JSON is valid.",
                    )
                )
            else:
                results.append(
                    MemoryCheckResult(
                        "FAIL",
                        "docs/project_memory/project_state.json",
                        "Project state JSON must be an object with a project section.",
                    )
                )
        except json.JSONDecodeError as exc:
            results.append(
                MemoryCheckResult(
                    "FAIL",
                    "docs/project_memory/project_state.json",
                    f"Project state JSON is invalid: {exc}",
                )
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
