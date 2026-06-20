# Headroom Developer Workflow Spike v1

Status: `HEADROOM_DEVELOPER_WORKFLOW_SPIKE_V1_REJECTED_FOR_NOW`

## Purpose

Evaluate Headroom as a developer-workflow-only compression tool for AI Health Coach handoffs, context packs, QA logs, diffs, pytest output, helper prompts, and milestone summaries.

## Final decision

Headroom is rejected for now.

Final status:

`HEADROOM_DEVELOPER_WORKFLOW_SPIKE_V1_REJECTED_FOR_NOW`

Reason:

- The spike shape was safe.
- Local artifact handling was safe.
- The deterministic baseline was useful as a control.
- The real Headroom comparison did not produce adoption-ready evidence meeting the required Safety >= 4 and Accuracy >= 4 threshold.
- Architecture does not approve Headroom as a default workflow helper.

## Boundary

This spike was developer workflow only.

No changes were made to:

- FastAPI runtime
- Streamlit runtime
- provider runtime
- provider prompts
- model-facing health context
- validation schemas
- nutrition/training/report contracts
- persistence
- database behavior
- user-facing UI
- app dependencies required for pytest
- deterministic fallback behavior
- Claude workflow

Compressed output is convenience context only. It is not source of truth.

## What was tested

The spike generated local-only source artifacts under:

```text
qa_artifacts/headroom_spike_v1/original/
```

It generated local-only deterministic baseline/control artifacts under:

```text
qa_artifacts/headroom_spike_v1/compressed/
```

It also generated or attempted local real Headroom artifacts under:

```text
qa_artifacts/headroom_spike_v1/real_headroom/
```

These local artifacts are intentionally not committed.

## Inputs used

- Dev Assistant status output
- Codex context pack
- Aider context pack
- Copilot context pack
- QA plan
- Git diff stat
- Git diff name-only
- Focused pytest output
- Supercharger session brief
- Long Architecture/Backend handoff
- QA / pytest-style report

## Deterministic baseline/control comparison

The deterministic baseline was not Headroom. It was used only as a control to prove that local workflow artifacts could be generated safely and kept out of git.

| Case | Original chars | Compressed chars | Reduction | Compression | Safety | Usefulness | Accuracy | Result |
|---|---:|---:|---:|---|---:|---:|---:|---|
| context_pack_aider | 2275 | 947 | 58.4% | Baseline only | 5 | 3 | 4 | Control only |
| context_pack_codex | 2275 | 961 | 57.8% | Baseline only | 5 | 3 | 4 | Control only |
| context_pack_copilot | 2277 | 947 | 58.4% | Baseline only | 5 | 3 | 4 | Control only |
| dev_assistant_status | 10120 | 3148 | 68.9% | Baseline only | 5 | 3 | 4 | Control only |
| git_diff_name_only | 0 | 1 | 0% | Baseline only | 5 | 3 | 4 | Control only |
| git_diff_stat | 0 | 1 | 0% | Baseline only | 5 | 3 | 4 | Control only |
| pytest_project_memory_check | 100 | 18 | 82% | Baseline only | 5 | 3 | 4 | Control only |
| qa_plan | 1081 | 799 | 26.1% | Baseline only | 5 | 3 | 4 | Control only |

## Real Headroom Comparison Addendum

### Real Headroom run summary

A real Headroom comparison pass was attempted as a developer-workflow-only evaluation.

The local real Headroom artifacts were generated under:

```text
qa_artifacts/headroom_spike_v1/real_headroom/
```

Those artifacts are intentionally not committed.

The command/tool block is not adoption evidence. The captured command/output record was not complete enough to support adopting Headroom as a default workflow helper.

### Real Headroom scoring conclusion

The real Headroom comparison did not produce adoption-ready evidence that met the required project threshold.

Required threshold:

- Safety >= 4
- Accuracy >= 4

Result:

- The automated review did not meet the minimum safety/accuracy threshold.
- The comparison evidence was not strong enough to approve Headroom as a default workflow helper.
- Architecture therefore rejects Headroom adoption for now.

The previous empty comparison table is not adoption evidence. It means the real Headroom output was not usable enough, or not sufficiently captured, to support a scored project-memory comparison table.

### Final status

`HEADROOM_DEVELOPER_WORKFLOW_SPIKE_V1_REJECTED_FOR_NOW`

## Findings

### What was preserved

- Headroom remained developer-workflow only.
- Compressed output remained convenience context, not source of truth.
- No FastAPI runtime integration was added.
- No Streamlit runtime integration was added.
- No provider prompt compression was added.
- No model-facing health context compression was added.
- No validator, fallback, persistence, report, nutrition, training, food catalog, or exercise catalog behavior changed.
- No Claude workflow was added.
- Codex remains optional/scoped only.

### What was lost or weakened

The real Headroom evidence was not strong enough to prove safe adoption.

The rejected-for-now decision is based on insufficient adoption-ready safety/accuracy evidence, not on a product/runtime defect.

### Invention / hallucination findings

The real Headroom evidence was not complete enough to prove semantic accuracy for this project.

Because source-of-truth preservation is non-negotiable, Architecture rejects Headroom adoption for now rather than relying on incomplete evidence.

## Current project position

Headroom may be revisited later as a developer-workflow-only experiment, but it is not approved for default daily use.

Current forbidden position:

- not adopted by default
- not runtime
- not provider prompt compression
- not model-facing context compression
- not source of truth
- not required for tests
- not required for development
- not added as an app dependency
- not used in FastAPI
- not used in Streamlit
- not used in validation, persistence, reports, nutrition, training, food catalog, or exercise catalog behavior
- not connected to Claude workflow

## Recommended allowed future position

Allowed later only if Architecture explicitly reopens the experiment:

- developer-workflow-only compression experiment
- local-only handoff summarization test
- local-only QA artifact compression test
- local-only context-pack comparison test

Any future attempt must preserve the rule that compressed output is convenience context only and never source of truth.

## Recommended forbidden uses

Forbidden:

- FastAPI runtime
- Streamlit runtime
- provider runtime
- provider prompts
- model-facing health context
- validation schemas
- nutrition/training/report contracts
- food/exercise catalog truth
- user health facts
- persisted source-of-truth docs
- tests requiring Headroom
- app dependencies required for pytest
- replacing backend truth with compressed text
- replacing project memory with compressed text
- Claude workflow

## Validation

Validation expected for the doc-only cleanup:

```powershell
git diff --check
scripts/dev_commit_check.ps1 -Mode code
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
pytest tests/test_project_memory_check.py -q
pytest tests/test_daily_coach_narrative_preview_route.py -q
pytest tests/test_daily_coach_narrative_preview_service.py -q
pytest tests/test_daily_next_action_service.py -q
pytest tests/test_report_persistence_boundary.py -q
pytest tests/test_full_report_section_registry.py -q
```

## Recommended next milestone

`Supercharger v1.1 - session-brief command`

Reason:

The Headroom spike exposed a real workflow pain: manual PowerShell logging and copy/paste capture are clunky and encoding-prone.

Desired future command:

```powershell
python tools/dev_assistant.py session-brief --out qa_artifacts/session_brief.txt
```
