# Project Memory

Project memory is the continuity layer for AI Health Coach.

Agents and humans should read these files before changing architecture, provider behavior, persistence, UI behavior, tests, or accepted milestone status.

## Required starting files

1. `current_state.md`
2. `product_vision.md`
3. `architecture_principles.md`
4. `backend_truth_contract.md`
5. `ai_boundaries.md`
6. `section_registry_summary.md`
7. `future_architecture_ledger.md`
8. `premium_platform_blueprint.md`
9. `development_workflow.md`
10. `developer_delivery_workflow_contract.md`
11. `developer_delivery_workflow_script_safety_addendum_v1.md`
12. `agent_workflow.md`
13. `local_developer_command_menu.md`
14. `open_questions.md`

## Project memory update requirement

Every meaningful feature/milestone branch must update project memory before acceptance.

A milestone is not accepted if docs still describe old state, imply unapproved provider behavior, omit reference-only failed branches, or rely on chat memory instead of repo memory.


## Developer delivery workflow contract

Implementation delivery is patch-first by default. Snapshot restore is fallback only.

All future agents should follow `developer_delivery_workflow_contract.md` for branch checks, patch application, validation, explicit staging, snapshot creation, and the hard rule that Linux pull is provided immediately after a snapshot filename.

`developer_delivery_workflow_script_safety_addendum_v1.md` extends the contract with script hard-stop gates, including the mandatory post-merge ancestry check that proves the accepted final feature commit is an ancestor of `main` before push, snapshot, or Linux pull.


## Local developer command menu

Local helper commands are repo-owned in `scripts/fitness_commands.ps1`.

Installation and reload guidance live in `local_developer_command_menu.md`. The PowerShell profile should only dot-source the repo script; project command logic should not live only in a hidden user profile.

The command menu preserves `fitness`, `app`, `lstop`, `lrestart`, and `lupdate`, and adds workflow safety commands including `fsnap`, `fbranch`, `fmerge`, `fsweep`, `fmem`, `fports`, `fkill`, `fdoctor`, `lpull`, `lvalidate`, and `lollama`.

## Active Daily Coach provider docs

Daily Coach narrative product voice polish is tracked in:

- `milestones/daily_coach_narrative_product_voice_polish_v1.md`
- `reviews/daily_coach_narrative_product_voice_polish_v1.md`
- `runtime_qa/daily_coach_narrative_product_voice_polish_v1_results.md`

This milestone improves approved narrative copy inside the accepted manual same-session bridge only. It does not authorize provider default changes, persistence, normal-load AI, qwen3 bridge use, or model promotion.

## Historical docs

Historical milestone, review, runtime QA, and architecture docs are preserved. Do not rewrite history to pretend failed smoke tests did not happen. Classify old branches and decisions instead.
