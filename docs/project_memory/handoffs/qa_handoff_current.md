# QA Handoff Current

Current milestone: Daily Coach Async Provider Runtime Design v1

Status: DESIGN-ONLY / READY FOR QA REVIEW

Branch: `feature/daily-coach-async-provider-runtime-design-v1`

Baseline accepted before this milestone: Daily Coach Async Developer-Only Prototype v1

## QA focus

QA should verify that this branch is docs/design-only and does not change runtime behavior.

## Design deliverable

- `docs/project_memory/designs/daily_coach_async_provider_runtime_design_v1.md`

## Expected behavior

Runtime behavior should remain unchanged from Daily Coach Async Developer-Only Prototype v1.

Normal Today behavior remains unchanged:

- Daily Next Action remains deterministic and primary.
- Normal Today page load does not create an async job.
- Normal Today page load does not call a provider.
- Normal Today does not show async provider narrative.

## Boundary checks

- design only
- no provider execution
- no direct_ollama call
- no CrewAI call
- no qwen3 call
- no qwen3:32b call
- no worker
- no queue
- no scheduler
- no polling
- no DB/schema creation
- no async persistence
- no provider cache
- no normal Today provider call
- no public async narrative display
- no model promotion
- qwen3 remains not bridge-enabled
- app/wapp Linux runtime split remains intact

## Recommended validation

```powershell
git diff --check
pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
. .\scripts\fitness_commands.ps1
fsweep
scripts/dev_commit_check.ps1 -Mode docs-only
```

Manual runtime QA is not required for this docs-only branch unless Architecture requests it.

## Recommended next milestone after acceptance

Architecture recommendation from the design: Daily Coach Async Persistence Design v1 before provider runtime implementation.
