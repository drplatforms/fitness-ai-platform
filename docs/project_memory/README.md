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
11. `agent_workflow.md`
12. `open_questions.md`

## Project memory update requirement

Every meaningful feature/milestone branch must update project memory before acceptance.

A milestone is not accepted if docs still describe old state, imply unapproved provider behavior, omit reference-only failed branches, or rely on chat memory instead of repo memory.


## Developer delivery workflow contract

Implementation delivery is patch-first by default. Snapshot restore is fallback only.

All future agents should follow `developer_delivery_workflow_contract.md` for branch checks, patch application, validation, explicit staging, snapshot creation, and the hard rule that Linux pull is provided immediately after a snapshot filename.

## Historical docs

Historical milestone, review, runtime QA, and architecture docs are preserved. Do not rewrite history to pretend failed smoke tests did not happen. Classify old branches and decisions instead.
