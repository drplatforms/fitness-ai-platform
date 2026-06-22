from __future__ import annotations

from pathlib import Path

from tools import project_memory_check
from tools.project_memory_check import (
    REQUIRED_FILES,
    has_failures,
    run_project_memory_check,
    summarize_results,
)


def write_required_project_memory(root: Path) -> None:
    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        text = "placeholder\n"
        if relative_path == "AGENTS.md":
            text = (
                "docs/project_memory\n"
                "Backend owns facts\n"
                "Deterministic fallback remains the default\n"
                "Do not add `CLAUDE.md`\n"
                "Project memory update requirement\n"
                "developer_delivery_workflow_contract.md\n"
                "developer_delivery_workflow_script_safety_addendum_v1.md\n"
            )
        elif relative_path == ".github/copilot-instructions.md":
            text = (
                "Backend owns facts\n"
                "Preserve deterministic fallback behavior\n"
                "Do not add Claude workflow files\n"
                "Project memory update requirement\n"
                "developer_delivery_workflow_contract.md\n"
                "developer_delivery_workflow_script_safety_addendum_v1.md\n"
            )
        elif relative_path == "docs/project_memory/agent_workflow.md":
            text = "ChatGPT\nCodex\nDev Assistant\nClaude\nOut of scope\n"
        elif relative_path == "docs/project_memory/development_workflow.md":
            text = (
                "OLLAMA_BASE_URL\n"
                "Windows owns source-of-truth repo work\n"
                "Linux owns runtime/staging QA\n"
            )
        elif relative_path == "docs/project_memory/future_architecture_ledger.md":
            text = (
                "RAG\nVector\nMoE\nMCP\nfrontend\n"
                "This ledger records direction. It does not authorize implementation.\n"
            )
        elif relative_path == "docs/project_memory/premium_platform_blueprint.md":
            text = (
                "premium\nRAG\nvector\nMoE\nMCP\nqwen3:32b\n"
                "This document is aspirational. It does not authorize implementation of all features.\n"
            )
        elif (
            relative_path
            == "docs/project_memory/developer_delivery_workflow_contract.md"
        ):
            text = (
                "Patch-first delivery is the default\n"
                "Snapshot restore is a fallback, not the normal path\n"
                "When Dustin provides a snapshot filename\n"
                "C:\\projects\\fitness_ai\n"
                "~/projects/fitness-ai-platform\n"
                "OLLAMA_BASE_URL=\n"
                "http://192.168.1.104:11434\n"
            )
        elif (
            relative_path
            == "docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md"
        ):
            text = (
                "git merge-base --is-ancestor <accepted-final-feature-commit> main\n"
                "A clean working tree is not proof that the correct milestone was merged.\n"
                "phase-separated\n"
                "stop before push, snapshot, or Linux pull\n"
            )
        elif (
            relative_path
            == "docs/project_memory/milestones/developer_delivery_workflow_script_safety_addendum_v1.md"
        ):
            text = (
                "Developer Delivery Workflow Script Safety Addendum v1\n"
                "git merge-base --is-ancestor\n"
                "Docs/tooling only\n"
            )
        elif (
            relative_path
            == "docs/project_memory/reviews/developer_delivery_workflow_script_safety_addendum_v1.md"
        ):
            text = (
                "Developer Delivery Workflow Script Safety Addendum v1\n"
                "DEVELOPER_DELIVERY_WORKFLOW_SCRIPT_SAFETY_ADDENDUM_V1_ACCEPTED\n"
                "Docs/tooling only\n"
            )
        elif (
            relative_path
            == "docs/project_memory/milestones/developer_delivery_workflow_contract_v1.md"
        ):
            text = (
                "Developer Delivery Workflow Contract v1\n"
                "patch-first delivery is default\n"
                "Linux pull-after-snapshot is a hard rule\n"
            )
        elif (
            relative_path
            == "docs/project_memory/reviews/developer_delivery_workflow_contract_v1.md"
        ):
            text = (
                "Developer Delivery Workflow Contract v1\n"
                "DEVELOPER_DELIVERY_WORKFLOW_CONTRACT_V1_ACCEPTED\n"
                "docs/tooling only\n"
            )
        elif (
            relative_path
            == "docs/project_memory/milestones/provider_narrative_qa_matrix_v2.md"
        ):
            text = (
                "Provider Narrative QA Matrix v2\n"
                "qwen2.5:3b\n"
                "not a provider promotion milestone\n"
                "no provider output to normal Today UI\n"
            )
        elif (
            relative_path
            == "docs/project_memory/reviews/provider_narrative_qa_matrix_v2.md"
        ):
            text = (
                "Provider Narrative QA Matrix v2\n"
                "AWAITING RUNTIME MATRIX RESULTS\n"
                "Do not accept this milestone until the runtime matrix results are present\n"
                "no model promotion\n"
            )
        elif (
            relative_path
            == "docs/project_memory/runtime_qa/provider_narrative_qa_matrix_v2_results.md"
        ):
            text = (
                "Provider Narrative QA Matrix v2 Results\n"
                "No model is promoted by this report.\n"
                "No same-session approval was added by this matrix.\n"
            )
        elif (
            relative_path
            == "docs/project_memory/milestones/daily_coach_narrative_product_voice_polish_v1.md"
        ):
            text = (
                "Daily Coach Narrative Product Voice Polish v1\n"
                "sound right and be right\n"
                "qwen2.5:3b\n"
                "No provider call occurs on normal Today load\n"
            )
        elif (
            relative_path
            == "docs/project_memory/reviews/daily_coach_narrative_product_voice_polish_v1.md"
        ):
            text = (
                "Daily Coach Narrative Product Voice Polish v1\n"
                "DAILY_COACH_NARRATIVE_PRODUCT_VOICE_POLISH_V1_ACCEPTED\n"
                "No validation loosening\n"
                "Generic/meta copy is blocked or flagged\n"
            )
        elif (
            relative_path
            == "docs/project_memory/runtime_qa/daily_coach_narrative_product_voice_polish_v1_results.md"
        ):
            text = (
                "Daily Coach Narrative Product Voice Polish v1 Runtime QA Results\n"
                "LOCAL MANUAL QA REQUIRED\n"
                "qwen2.5:3b\n"
                "No provider call occurs on normal Today load\n"
            )

        elif relative_path == "docs/project_memory/project_continuity_bootstrap.md":
            text = (
                "Project Continuity Bootstrap\n"
                "Daily Coach Async Service Shell / No Worker v1\n"
                "Current Accepted Milestone Stack\n"
                "Sound right and be right\n"
                "app` command launches Linux runtime\n"
                "qwen3 is not bridge-enabled\n"
                "service shell only\n"
                "no provider runtime yet\n"
                "Daily Coach Async Developer-Only Prototype v1\n"
                "Developer Mode-only manual lifecycle prototype\n"
                "What Future Chats Must Do First\n"
            )

        elif (
            relative_path
            == "docs/project_memory/milestones/daily_coach_async_developer_only_prototype_v1.md"
        ):
            text = (
                "Daily Coach Async Developer-Only Prototype v1\n"
                "Developer Mode\n"
                "manual lifecycle harness\n"
                "no provider execution\n"
                "no DB persistence\n"
                "normal Today behavior remains unchanged\n"
                "DAILY_COACH_ASYNC_DEVELOPER_ONLY_PROTOTYPE_V1_ACCEPTED\n"
            )
        elif (
            relative_path
            == "docs/project_memory/reviews/daily_coach_async_developer_only_prototype_v1.md"
        ):
            text = (
                "Daily Coach Async Developer-Only Prototype v1\n"
                "READY FOR ARCHITECTURE REVIEW\n"
                "DAILY_COACH_ASYNC_DEVELOPER_ONLY_PROTOTYPE_V1_ACCEPTED\n"
                "no provider execution\n"
                "no qwen3 call\n"
                "no normal Today provider call\n"
            )

        elif relative_path == "docs/project_memory/local_developer_command_menu.md":
            text = (
                "scripts/fitness_commands.ps1\n"
                "install_fitness_commands_profile.ps1\n"
                "C:\\projects\\fitness_ai\n"
                "~/projects/fitness-ai-platform\n"
                "http://127.0.0.1:11434\n"
                "http://192.168.1.104:11434\n"
                "fitness\n"
                "app\n"
                "wapp\n"
                "Linux is the canonical\n"
                "Windows-local\n"
                "lstop\n"
                "lrestart\n"
                "lupdate\n"
                "fmerge\n"
                "git merge-base --is-ancestor\n"
            )
        elif (
            relative_path
            == "docs/project_memory/milestones/local_developer_command_menu_v1.md"
        ):
            text = (
                "Local Developer Command Menu Audit + Repo-Owned Commands v1\n"
                "scripts/fitness_commands.ps1\n"
                "docs/tooling/local command changes only\n"
            )
        elif (
            relative_path
            == "docs/project_memory/reviews/local_developer_command_menu_v1.md"
        ):
            text = (
                "Local Developer Command Menu Audit + Repo-Owned Commands v1\n"
                "LOCAL_DEVELOPER_COMMAND_MENU_V1_ACCEPTED\n"
                "PowerShell load smoke\n"
            )

        elif (
            relative_path
            == "docs/project_memory/designs/async_daily_coach_narrative_design_v1.md"
        ):
            text = (
                "Async Daily Coach Narrative Design v1\n"
                "design-only milestone\n"
                "deterministic fallback remains always available\n"
                "qwen2.5:3b\n"
                "qwen3:32b\n"
                "future premium async candidate only\n"
                "not bridge-enabled\n"
                "not promoted\n"
                "not_requested\nqueued\ngenerating\nprovider_succeeded_pending_validation\n"
                "approved\nrejected_validation\nrejected_parse\nprovider_timeout\n"
                "provider_error\nstale\nfallback_available\n"
                "daily_coach_narrative_jobs\n"
                "raw rejected output is not persisted by default\n"
                "No output displays unless all required gates pass.\n"
            )
        elif (
            relative_path
            == "docs/project_memory/milestones/async_daily_coach_narrative_design_v1.md"
        ):
            text = (
                "Async Daily Coach Narrative Design v1\n"
                "IMPLEMENTED / READY FOR ARCHITECTURE REVIEW\n"
                "ASYNC_DAILY_COACH_NARRATIVE_DESIGN_V1_ACCEPTED\n"
                "No provider call occurs on normal Today load.\n"
                "Persistence is proposed only, not implemented.\n"
            )
        elif (
            relative_path
            == "docs/project_memory/reviews/async_daily_coach_narrative_design_v1.md"
        ):
            text = (
                "Async Daily Coach Narrative Design v1 Review\n"
                "READY FOR ARCHITECTURE REVIEW\n"
                "ASYNC_DAILY_COACH_NARRATIVE_DESIGN_V1_ACCEPTED\n"
                "No async runtime implemented.\n"
                "qwen3 remains not bridge-enabled.\n"
                "Workflow contract followed.\n"
            )
        elif (
            relative_path
            == "docs/project_memory/handoffs/architecture_handoff_current.md"
        ):
            text = (
                "Local Command Menu App Runtime Correction v1\n"
                "app` is now the canonical Linux runtime launcher\n"
                "wapp\n"
                "Linux is the canonical FastAPI + Streamlit app runtime\n"
            )
        elif relative_path == "docs/project_memory/handoffs/backend_handoff_current.md":
            text = (
                "Local Command Menu App Runtime Correction v1\n"
                "app` restarts Linux FastAPI + Streamlit through SSH\n"
                "wapp\n"
                "No backend app runtime code changed.\n"
            )
        elif relative_path == "docs/project_memory/handoffs/qa_handoff_current.md":
            text = (
                "Local Command Menu App Runtime Correction v1\n"
                "app` means Linux canonical app runtime\n"
                "wapp\n"
                "fports\n"
            )
        elif (
            relative_path
            == "docs/project_memory/plans/async_daily_coach_narrative_implementation_plan_v1.md"
        ):
            text = (
                "Async Daily Coach Narrative Implementation Plan v1\n"
                "Daily Coach Async Contracts + Data Model v1\n"
                "No provider call occurs during normal Today load.\n"
                "qwen3:32b remains\n"
            )
        elif (
            relative_path
            == "docs/project_memory/milestones/async_daily_coach_narrative_implementation_plan_v1.md"
        ):
            text = (
                "Async Daily Coach Narrative Implementation Plan v1\n"
                "ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1_ACCEPTED\n"
                "No provider call on normal Today load\n"
            )
        elif (
            relative_path
            == "docs/project_memory/reviews/async_daily_coach_narrative_implementation_plan_v1.md"
        ):
            text = (
                "Async Daily Coach Narrative Implementation Plan v1\n"
                "ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1_ACCEPTED\n"
                "No async runtime implemented\n"
            )
        elif (
            relative_path
            == "docs/project_memory/milestones/daily_coach_async_contracts_data_model_v1.md"
        ):
            text = (
                "Daily Coach Async Contracts + Data Model v1\n"
                "contracts/data-model foundation only\n"
                "DailyCoachNarrativeJobStatus\n"
                "DailyCoachNarrativeModelLane\n"
                "DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED\n"
            )
        elif (
            relative_path
            == "docs/project_memory/reviews/daily_coach_async_contracts_data_model_v1.md"
        ):
            text = (
                "Daily Coach Async Contracts + Data Model v1 Review\n"
                "DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED\n"
                "no async runtime implemented\n"
                "no provider execution added\n"
                "no DB schema change\n"
            )
        elif relative_path == "scripts/fitness_commands.ps1":
            text = (
                "function fitness\n"
                "function app\n"
                "function wapp\n"
                "function lstop\n"
                "function lrestart\n"
                "function lupdate\n"
                "function fsnap\n"
                "function fbranch\n"
                "function fmerge\n"
                "git merge-base --is-ancestor\n"
                "C:\\projects\\fitness_ai\n"
                "~/projects/fitness-ai-platform\n"
                "http://127.0.0.1:11434\n"
                "http://192.168.1.104:11434\n"
                "FITNESS_LINUX_STREAMLIT_URL\n"
                "FITNESS_LINUX_STREAMLIT_PORT\n"
                "8501\n"
                "fitness-ui\n"
                "fitness-api\n"
                "Windows-local FastAPI + Streamlit\n"
            )
        elif relative_path == "scripts/install_fitness_commands_profile.ps1":
            text = (
                "AI Health Coach command menu\n"
                "Copy-Item\n"
                "C:\\projects\\fitness_ai\\scripts\\fitness_commands.ps1\n"
                ". `$PROFILE\n"
            )

        elif relative_path == "docs/project_memory/current_state.md":
            text = (
                "Project Memory Alignment + North Star Architecture v1\n"
                "feature/daily-coach-narrative-same-session-approved-preview-bridge-v1\n"
                "reference-only\n"
                "No provider may run on normal Today page load\n"
                "Provider Narrative QA Matrix v2\n"
                "Daily Coach Same-Session Approved Preview Bridge v1 Retry\n"
                "Same-Session Bridge Runtime QA v1\n"
                "Daily Coach Narrative Product Voice Polish v1\n"
                "Daily Coach Narrative Product Voice Runtime QA v1\n"
                "PASS_WITH_NOTE\n"
                "sound right and be right\n"
                "Local Developer Command Menu Audit + Repo-Owned Commands v1\n"
                "scripts/fitness_commands.ps1\n"
                "Local Command Menu App Runtime Correction v1\n"
                "Linux is the canonical\n"
                "wapp\n"
                "Daily Coach Async Service Shell / No Worker v1\n"
                "service shell only\n"
                "no provider execution added\n"
            )
        elif relative_path == "docs/project_memory/ai_boundaries.md":
            text = (
                "Deterministic fallback remains the default\n"
                "Daily Coach Narrative provider lanes are manual/developer-gated preview\n"
                "qwen3:32b remains a future premium coach candidate only\n"
            )
        path.write_text(text, encoding="utf-8")


def test_project_memory_check_passes_when_required_docs_exist(tmp_path: Path) -> None:
    write_required_project_memory(tmp_path)

    results = run_project_memory_check(tmp_path)
    summary = summarize_results(results)

    assert not has_failures(results)
    assert summary["FAIL"] == 0
    assert any(result.path == "AGENTS.md" for result in results)


def test_project_memory_check_fails_when_required_doc_is_missing(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (tmp_path / "docs/project_memory/current_state.md").unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path == "docs/project_memory/current_state.md"
        for result in results
    )


def test_project_memory_check_fails_if_claude_file_exists(tmp_path: Path) -> None:
    write_required_project_memory(tmp_path)
    (tmp_path / "CLAUDE.md").write_text("not allowed\n", encoding="utf-8")

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL" and result.path == "CLAUDE.md" for result in results
    )


def test_project_memory_check_warns_on_stale_current_state_marker(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (tmp_path / "docs/project_memory/current_state.md").write_text(
        "Latest accepted milestone\n\n"
        "`Daily Coach Narrative Developer Preview v1`\n",
        encoding="utf-8",
    )

    results = run_project_memory_check(tmp_path)

    assert any(
        result.status == "WARN"
        and result.path == "docs/project_memory/current_state.md"
        and "Possible stale milestone wording" in result.message
        for result in results
    )


def test_project_memory_check_requires_future_architecture_ledger(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (tmp_path / "docs/project_memory/future_architecture_ledger.md").unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path == "docs/project_memory/future_architecture_ledger.md"
        for result in results
    )


def test_project_memory_check_fails_on_forbidden_provider_claim(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (tmp_path / "docs/project_memory/current_state.md").write_text(
        "Project Memory Alignment + North Star Architecture v1\n"
        "feature/daily-coach-narrative-same-session-approved-preview-bridge-v1\n"
        "reference-only\n"
        "No provider may run on normal Today page load\n"
        "qwen3:32b is promoted\n",
        encoding="utf-8",
    )

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path == "docs/project_memory/current_state.md"
        and "Forbidden current-state claim" in result.message
        for result in results
    )


def test_project_memory_check_requires_developer_delivery_workflow_contract(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (tmp_path / "docs/project_memory/developer_delivery_workflow_contract.md").unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path == "docs/project_memory/developer_delivery_workflow_contract.md"
        for result in results
    )


def test_project_memory_check_requires_script_safety_addendum(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (
        tmp_path
        / "docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md"
    ).unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path
        == "docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md"
        for result in results
    )


def test_project_memory_check_requires_same_session_bridge_runtime_qa_results(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (
        tmp_path
        / "docs/project_memory/runtime_qa/same_session_bridge_runtime_qa_v1_results.md"
    ).unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path
        == "docs/project_memory/runtime_qa/same_session_bridge_runtime_qa_v1_results.md"
        for result in results
    )


def test_project_memory_check_requires_product_voice_polish_docs(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (
        tmp_path
        / "docs/project_memory/milestones/daily_coach_narrative_product_voice_polish_v1.md"
    ).unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path
        == "docs/project_memory/milestones/daily_coach_narrative_product_voice_polish_v1.md"
        for result in results
    )


def test_project_memory_check_requires_product_voice_runtime_qa_docs(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (
        tmp_path
        / "docs/project_memory/runtime_qa/daily_coach_narrative_product_voice_runtime_qa_v1_results.md"
    ).unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path
        == "docs/project_memory/runtime_qa/daily_coach_narrative_product_voice_runtime_qa_v1_results.md"
        for result in results
    )


def test_project_memory_check_requires_local_developer_command_menu_docs(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (tmp_path / "docs/project_memory/local_developer_command_menu.md").unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path == "docs/project_memory/local_developer_command_menu.md"
        for result in results
    )


def test_project_memory_check_requires_async_daily_coach_design_docs(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (
        tmp_path
        / "docs/project_memory/designs/async_daily_coach_narrative_design_v1.md"
    ).unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path
        == "docs/project_memory/designs/async_daily_coach_narrative_design_v1.md"
        for result in results
    )


def test_project_memory_check_requires_daily_coach_async_contract_docs(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (
        tmp_path
        / "docs/project_memory/milestones/daily_coach_async_contracts_data_model_v1.md"
    ).unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path
        == "docs/project_memory/milestones/daily_coach_async_contracts_data_model_v1.md"
        for result in results
    )


def test_project_memory_check_requires_daily_coach_async_service_shell_docs(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (
        tmp_path
        / "docs/project_memory/milestones/daily_coach_async_service_shell_no_worker_v1.md"
    ).unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path
        == "docs/project_memory/milestones/daily_coach_async_service_shell_no_worker_v1.md"
        for result in results
    )


def test_daily_coach_async_developer_only_prototype_memory_is_required() -> None:
    assert (
        "docs/project_memory/milestones/daily_coach_async_developer_only_prototype_v1.md"
        in project_memory_check.REQUIRED_FILES
    )
    assert (
        "docs/project_memory/reviews/daily_coach_async_developer_only_prototype_v1.md"
        in project_memory_check.REQUIRED_FILES
    )
    assert (
        "Daily Coach Async Developer-Only Prototype v1"
        in project_memory_check.REQUIRED_PHRASES[
            "docs/project_memory/project_continuity_bootstrap.md"
        ]
    )
