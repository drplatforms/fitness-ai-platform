# Backend Handoff Current

Current milestone: Daily Coach Async Provider Runtime Design v1

Status: DESIGN-ONLY / READY FOR ARCHITECTURE REVIEW

Branch: `feature/daily-coach-async-provider-runtime-design-v1`

Baseline accepted before this milestone: Daily Coach Async Developer-Only Prototype v1

## Backend status

No backend runtime behavior was implemented.

This milestone documents the future provider runtime boundary only.

## Design deliverable

- `docs/project_memory/designs/daily_coach_async_provider_runtime_design_v1.md`

## Implementation boundary

Backend must not implement provider execution from this milestone alone.

Future implementation requires a separately authorized milestone.

## Preserved non-goals

- No provider execution.
- No direct_ollama call.
- No CrewAI call.
- No qwen3 call.
- No qwen3:32b call.
- No background worker.
- No queue.
- No scheduler.
- No polling.
- No DB schema or persistence.
- No FastAPI provider execution route.
- No normal Today provider call.
- No public Streamlit async display behavior.
- No model promotion.
- app/wapp Linux runtime split remains intact.

## Backend recommendation from the design

The design recommends Daily Coach Async Persistence Design v1 before product-like provider runtime implementation.

If provider runtime is prototyped first, it should remain Developer Mode-only and should use an isolated runtime boundary rather than same-process hard-timeout provider execution.

## Expected validation

```powershell
git diff --check
pytest tests/test_project_memory_check.py -q
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/project_memory_check.py
. .\scripts\fitness_commands.ps1
fsweep
scripts/dev_commit_check.ps1 -Mode docs-only
```

## Next after Architecture acceptance

Recommended options:

1. Daily Coach Async Persistence Design v1
2. Daily Coach Async Provider Runtime Prototype v1
3. Daily Coach Narrative Premium Voice Research v1
