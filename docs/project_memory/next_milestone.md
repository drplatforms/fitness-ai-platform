# Next Milestone

Current milestone in progress: Test-First Quality Gate Development Plan v1.

Recommended branch: `feature/test-first-quality-gate-development-plan-v1`.

Source branch: `main`.

Required source main commit: `b343a47`.

Milestone type: docs / project memory / process canonization only.

## Acceptance is blocked until

- `current_state.md` records `main` at `b343a47` and the two recent accepted workout milestones.
- `project_continuity_bootstrap.md` documents the Complex Backend Quality Gate.
- Backend, Architecture, and QA role bootstrap docs document their responsibilities in the new process.
- The risk-based process model is documented.
- The bigger milestone / narrow patch doctrine is documented.
- Patch-stacking stop conditions are documented.
- The bug-to-regression-test rule is documented.
- The v1/v2 scope rule is documented.
- Definition of Done for complex milestones is documented.
- Recent accepted commits and snapshots are recorded.
- No app/runtime behavior changed.
- Docs/project-memory validation is green.

## Validation

Docs-only validation:

```powershell
git diff --check
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
scripts/dev_commit_check.ps1 -Mode docs
```

Optional:

```powershell
pytest tests/test_project_memory_check.py -q
```

No browser smoke is required for this docs-only milestone.

No Linux runtime smoke is required unless project policy changes.

## Recommended next milestones after acceptance

- Exercise Eligibility Matrix v1.
- Catalog Reachability Audit v2.
- Workout Preview Rolling Exposure Rotation v2.
- Provider/process planning milestone as needed.
- Nutrition deterministic suggestions / nutrition AI candidate contracts later.

## Deferred / not authorized by this milestone

- workout generation changes
- exercise catalog logic changes
- nutrition logic changes
- provider/Ollama/CrewAI/OpenAI behavior changes
- Streamlit runtime changes
- database changes
- new app features
- catalog-utilization follow-up implementation
- nutrition expansion
- provider strategy implementation

## Historical project-memory requirements still present

Some older project-memory tooling still checks for retained phrases related to prior Daily Coach async work:

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- feature/daily-coach-async-persistence-contracts-schema-v1
- schema/contracts
- NOT_AUTHORIZED_YET

These are historical continuity markers only. They do not authorize old async/provider implementation work.
