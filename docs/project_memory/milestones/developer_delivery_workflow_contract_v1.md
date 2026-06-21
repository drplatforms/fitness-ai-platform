# Developer Delivery Workflow Contract v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Date: 2026-06-20

## Goal

Create a repo-level developer delivery workflow contract so future implementation handoffs follow one stable operating model.

## Primary deliverable

- `docs/project_memory/developer_delivery_workflow_contract.md`

## Scope

Docs/tooling only.

## Approved

- create workflow contract doc
- update project-memory cross-links
- update AGENTS.md so future agents follow the contract
- update project-memory checks so the contract exists and contains required rules

## Not approved

- runtime behavior changes
- provider behavior changes
- UI behavior changes
- database/schema/report changes
- same-session approval
- model promotion
- RAG/vector/MoE/MCP implementation
- frontend/deployment changes

## Required workflow rules captured

- patch-first delivery is default
- snapshot fallback is fallback only
- Linux pull-after-snapshot is a hard rule
- Windows source repo is `C:\projects\fitness_ai`
- Linux mirror repo is `~/projects/fitness-ai-platform`
- Ollama runs on Windows by default
- Linux runtime uses `OLLAMA_BASE_URL=http://192.168.1.104:11434` when reaching Windows Ollama
- branch/path verification is required before applying changes
- validation is required before commit
- staging must be explicit
- snapshots, patches, DB files, secrets, and `qa_artifacts` are not committed
- docs/project-memory updates are part of Definition of Done

## Acceptance gate

Do not accept or merge if:

- the workflow remains only in chat memory
- patch-first is not documented as the default
- Linux pull-after-snapshot is not documented as a hard rule
- Ollama location remains ambiguous
- AGENTS.md/future agents are not pointed at the contract
