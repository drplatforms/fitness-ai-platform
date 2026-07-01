# Milestone — Daily Coach Note Recovery v2 Integration v1

Status: `APPROVED_FOR_BACKEND_IMPLEMENTATION`

Baseline:

```text
d2e0178 main_merge-recovery-intelligence-v2-qa-seed-matrix-validation-v1
```

Baseline snapshot:

```text
fitness_ai_snapshot_2026-07-01_d2e0178_main_merge-recovery-intelligence-v2-qa-seed-matrix-validation-v1.zip
```

Branch:

```text
feature/daily-coach-note-recovery-v2-integration-v1
```

Requested final status:

```text
DAILY_COACH_NOTE_RECOVERY_V2_INTEGRATION_V1_IMPLEMENTATION_COMPLETE
```

## Purpose

Wire the accepted Recovery Intelligence v2 service into the backend-owned Daily Coach Note context layer as structured source data.

This is an additive backend-context integration only. It does not create final Daily Coach copy or user-facing behavior.

## Implemented Direction

The existing internal context model keeps the compatibility field:

```text
recovery_intelligence
```

and adds the optional v2 field:

```text
recovery_intelligence_v2
```

The existing service keeps the v1 recovery path and additively calls:

```text
build_recovery_intelligence_v2()
```

The v2 service appears in `source_services` only when it succeeds. If v2 is unavailable due to a controlled local data issue, the context still returns successfully with a bounded unavailable status.

## Scope Boundaries

This milestone must not add or change:

```text
Streamlit UI
API routes
provider behavior
OpenAI/Ollama/CrewAI behavior
RAG/vector/agent behavior
database schema
migrations
persistence behavior
report behavior
recommendation behavior
Daily Coach final copy
Today card copy
workout plan behavior
nutrition target behavior
automatic deload logic
automatic progression logic
wearable/HRV integration
medical interpretation
```

## Naming Rule

Use product/roadmap wording:

```text
Daily Coach Note
```

Do not introduce new future-facing product wording that says `Daily Coach Snapshot`. Existing internal identifiers such as `DailyCoachIntelligenceSnapshot`, `daily_coach_intelligence_snapshot_service.py`, and `snapshot_version` are legacy/code identifiers and are not broadly renamed here.

## Backend Chat Rule

Architecture prepares Backend implementation handoffs/tasks. Architecture separately prepares QA testing instructions. Backend implements the Architecture-provided task and reports branch/commit/validation evidence when requested. Backend does not prepare handoff artifacts, QA findings, or QA instructions.

## Evidence Expectations

Focused validation should include:

```text
git diff --check
ruff check models/daily_coach_intelligence_models.py services/daily_coach_intelligence_snapshot_service.py tests/test_daily_coach_intelligence_snapshot_service.py
black --check models/daily_coach_intelligence_models.py services/daily_coach_intelligence_snapshot_service.py tests/test_daily_coach_intelligence_snapshot_service.py
python -m py_compile models/daily_coach_intelligence_models.py services/daily_coach_intelligence_snapshot_service.py
python -m pytest tests/test_daily_coach_intelligence_snapshot_service.py -q
python -m pytest tests/test_recovery_intelligence_v2_seed_matrix.py -q
python -m pytest tests/test_dev_recovery_intelligence_v2_tool.py -q
python -m pytest tests/test_recovery_intelligence_v2_service.py -q
python -m pytest tests/test_recovery_intelligence_v2_models.py -q
python -m pytest tests/test_recovery_intelligence_service.py -q
python -m pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
scripts/dev_commit_check.ps1 -Mode code
```

## End Milestone
