# Current Project Memory Status — 187e433

Latest accepted main evidence: `Platform North Star + Future Stack Canonicalization v1 @ 187e433`.

Latest accepted snapshot:

```text
fitness_ai_snapshot_2026-06-30_187e433_main_merge-platform-north-star-future-stack-canonicalization-v1.zip
```

Canonical long-term platform vision and future technology stack:

```text
docs/project_memory/architecture/platform_north_star_and_future_stack.md
```

Read the north-star file before making future-stack, SaaS, RAG, vector, agent, model-routing, or product-platform decisions.

Provider voice iteration is paused. Backend Intelligence Foundation remains the product-brain center of gravity.

Current next architecture planning target: `Recovery Intelligence v2 Architecture Planning v1`, unless Architecture explicitly changes course.

Canonical seven visible team lanes are recorded in `team_routing_contract.md`.

---

# Project Memory

Project memory is the continuity layer for AI Health Coach.

Agents and humans should read these files before changing architecture, provider behavior, persistence, UI behavior, tests, or accepted milestone status.


## Workflow command memory

The phase-separated Backend patch workflow and Architecture acceptance/merge/snapshot workflow are preserved in:

```text
docs/project_memory/architecture_backend_command_workflow_v1.md
```

Architecture may handle docs-only project-memory patches when no runtime/code files are touched. Backend Development remains the owner for implementation patches.

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
11. `architecture_backend_command_workflow_v1.md`
12. `developer_delivery_workflow_script_safety_addendum_v1.md`
13. `agent_workflow.md`
14. `local_developer_command_menu.md`
15. `open_questions.md`

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

## Active strategic architecture docs

The current canonical long-term platform vision and future technology stack is:

- `docs/project_memory/architecture/platform_north_star_and_future_stack.md`

This file is a strategic compass. It does not authorize immediate implementation of RAG, vector databases, agents, provider promotion, SaaS infrastructure, UI rewrites, or runtime behavior changes.

## Historical docs

Historical milestone, review, runtime QA, and architecture docs are preserved. Do not rewrite history to pretend failed smoke tests did not happen. Classify old branches and decisions instead.

## Test-first quality gate doctrine

The current process doctrine is recorded in `milestones/test_first_quality_gate_development_plan_v1.md`.

Future agents must follow the Complex Backend Quality Gate for complex state, scoring, selection, persistence, provider, nutrition, workout, recommendation, or user-visible workflow behavior.

The short version:

```text
diagnostic
→ failing/coverage test
→ narrow implementation
→ targeted validation
→ original smoke reproduction
→ project memory update
→ Architecture acceptance
```

Bigger milestone is okay. Bigger single patch is not okay.
