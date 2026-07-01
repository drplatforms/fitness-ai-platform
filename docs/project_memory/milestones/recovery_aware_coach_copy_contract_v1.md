# Milestone — Recovery-Aware Coach Copy Contract v1

Status: `APPROVED_FOR_BACKEND_IMPLEMENTATION`

Baseline:

```text
66a70d3 Merge daily coach note recovery v2 integration v1
```

Baseline snapshot:

```text
fitness_ai_snapshot_2026-07-01_66a70d3_main_merge-daily-coach-note-recovery-v2-integration-v1.zip
```

Branch:

```text
feature/recovery-aware-coach-copy-contract-v1
```

Requested final status:

```text
RECOVERY_AWARE_COACH_COPY_CONTRACT_V1_IMPLEMENTATION_COMPLETE
```

## Purpose

Create a deterministic, backend-owned copy contract that translates Recovery Intelligence v2 facts into bounded Daily Coach Note copy inputs for future use.

This milestone does not expose new user-facing copy.

This milestone does not change Today behavior.

This milestone does not change UI/API/provider/schema/persistence/recommendation/report behavior.

This milestone creates a deterministic copy contract for future use.

## Implemented Direction

The contract layer reads the existing backend Daily Coach Note context through `DailyCoachIntelligenceSnapshot` or its serialized dictionary form.

It consumes only the existing structured field:

```text
recovery_intelligence_v2
```

and produces:

```text
RecoveryAwareCoachCopyContract
```

The contract preserves:

- Recovery v2 availability
- readiness classification
- recovery pressure
- confidence
- data-quality status
- allowed recovery-aware claim guidance
- required caveats
- forbidden claim categories
- copy tone guidance
- reason codes
- limitations
- source services

The output is structured guidance only. It is not final Daily Coach Note copy and is not rendered by Today, Streamlit, API routes, reports, recommendations, providers, or persistence.

## Safety Rules

Allowed guidance uses bounded wording such as:

```text
appears
suggests
based on recent check-ins
available check-in data
recovery pressure
readiness context
limited confidence
```

Allowed claim categories include:

- sleep appears lower, higher, mixed, or near baseline when supported
- energy appears lower, higher, mixed, or near baseline when supported
- soreness appears elevated, somewhat elevated, mixed, or near baseline when supported
- recent recovery pressure appears low, moderate, or high when supported
- check-in data is limited or incomplete when applicable
- Recovery v2 confidence is preserved
- body weight is context only and not causal evidence

Forbidden claim categories are represented without authorizing forbidden wording:

- medical or diagnostic claims
- clinical advice or risk-certainty claims
- forced training-load changes
- automatic training-progression changes
- causal body-weight, fat-change, or nutrition-blame claims
- unsafe-to-train claims

The contract does not authorize medical interpretation, diagnosis, automatic deload logic, automatic progression logic, body-weight causality, nutrition blame, or unsafe-to-train claims.

## Scope Boundaries

This milestone must not add or change:

```text
Daily Coach final copy
Today card copy
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
workout plan behavior
nutrition target behavior
automatic deload logic
automatic progression logic
wearable/HRV integration
medical interpretation
```

## Implementation Files

```text
models/daily_coach_recovery_copy_models.py
services/daily_coach_recovery_copy_contract_service.py
tests/test_daily_coach_recovery_copy_contract_service.py
docs/project_memory/current_state.md
docs/project_memory/next_milestone.md
docs/project_memory/project_state.json
docs/project_memory/milestones/recovery_aware_coach_copy_contract_v1.md
```

## Evidence Expectations

Focused validation should include:

```text
git diff --check
ruff check models/daily_coach_recovery_copy_models.py services/daily_coach_recovery_copy_contract_service.py tests/test_daily_coach_recovery_copy_contract_service.py
black --check models/daily_coach_recovery_copy_models.py services/daily_coach_recovery_copy_contract_service.py tests/test_daily_coach_recovery_copy_contract_service.py
python -m py_compile models/daily_coach_recovery_copy_models.py services/daily_coach_recovery_copy_contract_service.py tests/test_daily_coach_recovery_copy_contract_service.py
python -m py_compile models/daily_coach_intelligence_models.py services/daily_coach_intelligence_snapshot_service.py ui/streamlit_app.py
python -m pytest tests/test_daily_coach_recovery_copy_contract_service.py -q
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
