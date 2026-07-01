# Recovery Intelligence v2 Model Contract v1

**Status:** `RECOVERY_INTELLIGENCE_V2_MODEL_CONTRACT_V1_IMPLEMENTATION_CANDIDATE`
**Owner:** Backend Development / Model Contract Implementation
**Baseline commit:** `871d090 main_merge-recovery-intelligence-v2-architecture-planning-v1`
**Baseline snapshot:** `fitness_ai_snapshot_2026-06-30_871d090_main_merge-recovery-intelligence-v2-architecture-planning-v1.zip`
**Recommended branch:** `feature/recovery-intelligence-v2-model-contract-v1`

## Purpose

Add the Recovery Intelligence v2 model contract before any v2 service, Daily Coach Intelligence Snapshot integration, recommendation behavior, provider behavior, API, UI, schema, or persistence changes are authorized.

This milestone is a Python model-contract slice only. It creates bounded, serializable dataclasses for the future Recovery Intelligence v2 read-only interpretation layer.

## Implemented scope

Expected implementation files:

```text
models/recovery_intelligence_v2_models.py
tests/test_recovery_intelligence_v2_models.py
```

The contract covers:

- current recovery indicator/day context
- recovery baseline summary
- recent-vs-baseline delta
- recent-vs-prior delta
- indicator-level interpretation
- recovery pressure classification
- readiness classification v2
- recovery data quality
- provenance/source-fact references
- confidence, reason codes, limitations, and safe coach-summary guardrails

## Required boundaries

This milestone must not implement:

```text
Recovery Intelligence v2 service
Daily Coach Intelligence Snapshot integration
API changes
Streamlit changes
database/schema/migration changes
provider changes
OpenAI/Ollama/CrewAI changes
recommendation behavior changes
report behavior changes
automatic deload/progression logic
workout plan changes
nutrition target changes
RAG/vector/agent work
wearable/HRV integration
medical claims
```

## Contract rules

Models must preserve:

- bounded enum/value sets
- safe serialization through `to_dict()`
- explicit `None` for missing values instead of coercing unknown values to zero
- confidence gates where Limited/Low confidence requires reason codes or limitations
- no medical, diagnostic, injury, illness, sleep-disorder, overtraining, or forced-deload language in user-facing summary fields
- indicator terminology in new user/product-facing text

## Validation

Recommended validation:

```text
git diff --check
python -m pytest tests/test_recovery_intelligence_v2_models.py -q
python -m pytest tests/test_recovery_intelligence_service.py -q
python -m pytest tests/test_daily_coach_intelligence_snapshot_service.py -q
python -m pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
scripts/dev_commit_check.ps1 -Mode code
```

## Next milestone after acceptance

If this model contract is accepted, the next likely milestone is:

```text
Recovery Intelligence v2 Service v1
```

That later milestone should remain read-only unless Architecture explicitly expands scope.
