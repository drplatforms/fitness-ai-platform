# Current Handoff: QA

Project: AI Health Coach / fitness-ai

## Current active milestone

`Async Daily Coach Narrative Design v1`

Status: `IMPLEMENTED / READY FOR ARCHITECTURE REVIEW`

Primary design doc:

`docs/project_memory/designs/async_daily_coach_narrative_design_v1.md`

## QA scope

This is a docs/design milestone. QA should confirm documentation and boundary preservation, not async runtime behavior.

QA should verify:

- design doc exists
- milestone doc exists
- review doc exists
- handoffs were updated
- current state mentions Async Daily Coach Narrative Design v1
- project memory checks pass
- artifact sweep is clean
- no runtime/provider/UI/database behavior changed
- no qa_artifacts or snapshots are committed

## Runtime boundaries to protect

- No provider call on normal Today load.
- Deterministic Today Coach Note remains always available.
- Developer Mode provider preview remains manual.
- Same-session approval remains explicit and session-only.
- `qwen2.5:3b` remains bridge baseline only.
- qwen3 remains not bridge-enabled.
- `qwen3:32b` remains future premium async candidate only.
- Raw/rejected output is not approved for normal UI.
- Persistence is proposed only, not implemented.

## Suggested validation

```powershell
cd C:\projects\fitness_ai

git diff --check
scripts/dev_commit_check.ps1 -Mode code
pytest tests/test_project_memory_check.py -q
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
fsweep
```

Expected artifact sweep: no output.
