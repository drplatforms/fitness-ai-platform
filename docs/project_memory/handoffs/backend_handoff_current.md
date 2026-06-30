# Current Backend Handoff — Docs Refresh Development Architecture v1

**Status:** Active backend implementation handoff
**Baseline:** `main @ 23b5378`
**Active branch:** `feature/project-memory-handoff-compression-stale-docs-development-architecture-v1`
**Requested final status:** `PROJECT_MEMORY_HANDOFF_COMPRESSION_STALE_DOCS_DEVELOPMENT_ARCHITECTURE_V1_IMPLEMENTATION_COMPLETE`

## Backend Task

Implement a docs-only repo patch that updates project memory, handoff workflow, stale docs hygiene, team routing, and development architecture.

## Required Scope

Record latest accepted main at `23b5378`, record Fully Free Source-Data Lab v1 as developer-only evidence, record QA/product classification that Fully Free v1 was not meaningfully better than v4, pause provider voice iteration, establish Backend Intelligence Foundation as next center of gravity, add exact seven-team routing, add team quickstarts, add ChatGPT workflow/development architecture, add Prompt Lab lifecycle, add Architecture review checklist, add Research workflow, and update current handoffs.

## Validation

```powershell
git diff --check
python -m pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
scripts/dev_commit_check.ps1 -Mode docs-only
fsweep
```

No broad formatters.

## Non-Goals

No runtime/code behavior, provider, UI, schema, migration, RAG/vector/agent, recovery/workout/trend, food catalog, or custom GPT implementation.
