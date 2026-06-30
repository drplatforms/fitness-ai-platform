# Next Milestone — Recovery Intelligence v2 Architecture Planning v1

Baseline:

```text
main @ 187e433
fitness_ai_snapshot_2026-06-30_187e433_main_merge-platform-north-star-future-stack-canonicalization-v1.zip
```

Owner:

```text
Architecture
```

Purpose:

```text
Design the next Recovery Intelligence layer before Backend implementation. The goal is to make recovery signals more useful to Daily Coach intelligence without changing runtime behavior prematurely.
```

Primary deliverable:

```text
docs/project_memory/architecture/recovery_intelligence_v2_plan.md
```

Expected design topics:

- What Recovery Intelligence v1 already provides.
- Which v2 signals are allowed: sleep consistency, energy trend, soreness trend, body-weight trend, check-in completeness, rolling readiness, fatigue-risk support, and recovery-data confidence.
- How Recovery Intelligence v2 should interact with Workout Set Intelligence v1 and the Daily Coach Intelligence Snapshot.
- How confidence/provenance/limitations should be represented.
- How to avoid medical, diagnostic, injury, illness, sleep-disorder, or overtraining claims.
- Which behavior changes are explicitly not authorized until after design acceptance.

Non-goals for planning:

```text
runtime behavior changes
provider behavior changes
OpenAI/Ollama defaults
Today provider display
Streamlit UI changes
API changes
schema changes
migration changes
RAG
embeddings
pgvector
Qdrant
vector DB setup
LangGraph
CrewAI
LlamaIndex
multi-agent runtime
custom GPT build
food catalog expansion
USDA import
wearable integration
auth/billing/SaaS infrastructure
observability stack setup
cloud deployment
```

Recommended validation for design-only work:

```text
git diff --check
python -m pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
scripts/dev_commit_check.ps1 -Mode docs-only
```

Completion criteria:

- Recovery Intelligence v2 scope is specific enough for Backend to implement later.
- Backend-owned truth, confidence, provenance, limitations, and deterministic fallback remain explicit.
- AI/provider output remains out of scope.
- No user-facing behavior is changed.
- Project memory points to the accepted `187e433` baseline.

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
