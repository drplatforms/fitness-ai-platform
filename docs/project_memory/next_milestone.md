# Next Milestone — Recovery Intelligence v2 Model Contract v1

Baseline:

```text
main after Recovery Intelligence v2 Architecture Planning v1 is merged and snapshotted
```

Planning source:

```text
docs/project_memory/architecture/recovery_intelligence_v2_plan.md
```

Owner:

```text
Backend Development
```

Purpose:

```text
Add the Recovery Intelligence v2 model contract before any v2 service, snapshot integration, recommendation behavior, provider, API, UI, or persistence changes are authorized.
```

Primary deliverables:

```text
models/recovery_intelligence_v2_models.py
tests/test_recovery_intelligence_v2_models.py
```

Expected model concepts:

- RecoveryIntelligenceV2Summary
- RecoveryBaseline
- RecoverySignalInterpretation
- RecoveryDataQuality
- bounded readiness classification
- bounded recovery pressure
- bounded trend direction
- confidence
- reason_codes
- limitations
- source_facts / coach-safe summary guardrails if present

Required behavior:

- model construction validates enum values
- Limited/Low confidence outputs require reason_codes or limitations
- missing data remains explicit, not coerced to zero
- serialization remains public-safe and bounded
- forbidden medical/diagnostic/overtraining language is rejected where model fields own user-facing summaries

Non-goals for this implementation slice:

```text
service implementation
Daily Coach Snapshot integration
API changes
Streamlit changes
database/schema changes
provider behavior changes
OpenAI/Ollama/CrewAI changes
recommendation behavior changes
report behavior changes
automatic deloads
workout plan changes
nutrition target changes
RAG
embeddings
vector DB setup
agents/orchestration
wearable/HRV integration
medical claims
```

Recommended validation:

```text
git diff --check
ruff check . --fix
black .
pytest tests/test_recovery_intelligence_v2_models.py -q
pytest tests/test_recovery_intelligence_service.py -q
pytest tests/test_daily_coach_intelligence_snapshot_service.py -q
pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
pytest
python -m py_compile ui/streamlit_app.py
```

Completion criteria:

- Recovery Intelligence v2 model contract is specific and validated.
- No runtime behavior changes occur.
- Recovery v1 behavior remains stable.
- Daily Coach Intelligence Snapshot behavior remains stable.
- Backend-owned truth, confidence, provenance, limitations, and deterministic fallback remain explicit.
- AI/provider output remains out of scope.
- Project memory points to the accepted Recovery Intelligence v2 plan.

---

# Previous Milestone — Recovery Intelligence v2 Architecture Planning v1

Baseline:

```text
main @ fc7ed70
fitness_ai_snapshot_2026-06-30_fc7ed70_main_merge-post-north-star-state-reconciliation-v1.zip
```

Owner:

```text
Architecture
```

Primary deliverable:

```text
docs/project_memory/architecture/recovery_intelligence_v2_plan.md
```

Status:

```text
DOCS_ONLY_ARCHITECTURE_PLAN_READY_FOR_ACCEPTANCE
```

---

# Next Milestone — Daily Coach Workout Set Intelligence v1 + Intelligence Snapshot v2

Baseline:

```text
main @ 43927d4
fitness_ai_snapshot_2026-06-30_43927d4_main_merge-daily-coach-intelligence-snapshot-recovery-v1.zip
```

Active milestone:

```text
Daily Coach Workout Set Intelligence v1 + Intelligence Snapshot v2
```

Owner:

```text
Backend Development
```

Purpose:

```text
Build the second read-only Backend Intelligence Foundation slice: Workout Set Intelligence v1 plus Daily Coach Intelligence Snapshot v2.
```

This milestone does not build the full foundation. It deepens the training source-data layer while preserving Recovery Intelligence v1 and existing read-only nutrition/training summaries.

Required implementation:

- `models/workout_set_intelligence_models.py`
- `services/workout_set_intelligence_service.py`
- `models/daily_coach_intelligence_models.py` update
- `services/daily_coach_intelligence_snapshot_service.py` update
- `tools/dev_daily_coach_intelligence_snapshot.py` update
- targeted tests
- project-memory updates

After this milestone, Architecture should review whether Workout Set Intelligence v1 and Daily Coach Intelligence Snapshot v2 are acceptable.

Future next architecture target after acceptance:

```text
Recovery Intelligence v2
```

Remaining Backend Intelligence Foundation slices:

- Recovery Intelligence v2
- Cross-Domain Trend Engine
- Food Knowledge Expansion
- Six-Month Seed Data refinement
