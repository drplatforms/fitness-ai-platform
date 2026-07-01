# Recovery Intelligence v2 Service v1

Status: `RECOVERY_INTELLIGENCE_V2_SERVICE_V1_IMPLEMENTATION_CANDIDATE`

Baseline commit:

```text
dd6db0f main_merge-recovery-intelligence-v2-model-contract-v1
```

Baseline snapshot:

```text
fitness_ai_snapshot_2026-06-30_dd6db0f_main_merge-recovery-intelligence-v2-model-contract-v1.zip
```

Source planning:

```text
docs/project_memory/architecture/recovery_intelligence_v2_plan.md
```

## Purpose

Implement the first read-only Recovery Intelligence v2 service layer that populates the accepted v2 model contract from `daily_checkins`.

The service should return `RecoveryIntelligenceV2Summary` without changing Daily Coach behavior, report behavior, provider behavior, Streamlit UI behavior, API behavior, database schema, migrations, recommendation behavior, or persistence behavior.

## Implementation Scope

Expected files:

```text
services/recovery_intelligence_v2_service.py
tests/test_recovery_intelligence_v2_service.py
```

The service should:

- read from `daily_checkins`
- preserve `checkin_date` as the primary date
- use `created_at` / `id` only to choose the latest duplicate same-day check-in
- preserve missing numeric values as `None`
- construct current-day context
- construct a 28-day recovery baseline
- construct recent 7-day vs baseline and recent 7-day vs prior 7-day deltas
- construct data quality, source facts, confidence, reason codes, and limitations
- interpret sleep, energy, soreness, body weight, and check-in consistency as bounded indicators
- avoid medical, diagnostic, sleep-disorder, overtraining, forced-deload, and treatment language

## Non-Goals

This milestone does not authorize:

```text
Daily Coach Snapshot integration
API changes
Streamlit changes
database/schema changes
migrations
provider behavior changes
OpenAI/Ollama/CrewAI changes
recommendation behavior changes
report behavior changes
automatic deload logic
automatic progression logic
RAG/vector/agent work
wearable/HRV integration
medical claims
```

## Validation

Expected validation includes:

```text
python -m pytest tests/test_recovery_intelligence_v2_models.py -q
python -m pytest tests/test_recovery_intelligence_v2_service.py -q
python -m pytest tests/test_recovery_intelligence_service.py -q
python -m pytest tests/test_daily_coach_intelligence_snapshot_service.py -q
python -m pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
scripts/dev_commit_check.ps1 -Mode code
```

## Completion Target

Requested Backend status:

```text
RECOVERY_INTELLIGENCE_V2_SERVICE_V1_IMPLEMENTATION_COMPLETE
```
