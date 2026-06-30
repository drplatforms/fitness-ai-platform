# Milestone — Daily Coach Workout Set Intelligence v1 + Intelligence Snapshot v2

**Status:** `IMPLEMENTATION_CANDIDATE`

**Baseline accepted main:**

```text
43927d4 main_merge-daily-coach-intelligence-snapshot-recovery-v1
```

**Accepted snapshot:**

```text
fitness_ai_snapshot_2026-06-30_43927d4_main_merge-daily-coach-intelligence-snapshot-recovery-v1.zip
```

**Feature branch:**

```text
feature/daily-coach-workout-set-intelligence-v1
```

**Requested final status:**

```text
DAILY_COACH_WORKOUT_SET_INTELLIGENCE_V1_IMPLEMENTATION_COMPLETE
```

## Purpose

Implement the second Backend Intelligence Foundation slice:

```text
Daily Coach Workout Set Intelligence v1
+
Daily Coach Intelligence Snapshot v2
```

The layer is read-only, deterministic, set-aware, exercise-aware, confidence-gated, source-data oriented, and developer-inspectable.

## Implemented Scope

- Add `models/workout_set_intelligence_models.py`.
- Add `services/workout_set_intelligence_service.py`.
- Update Daily Coach Intelligence Snapshot to v2.
- Add `workout_set_intelligence` to the snapshot.
- Update the developer snapshot tool to include workout set indicators in JSON, Markdown, pasteback, and `workout_set_intelligence_summary.md`.
- Add targeted tests for workout set intelligence and snapshot v2.

## Boundaries

No user-facing Today behavior changed.

No provider call was added.

No OpenAI/Ollama/CrewAI default changed.

No Streamlit UI, API route, schema migration, snapshot persistence, workout generation change, nutrition target change, RAG, vector database, embeddings, multi-agent runtime, reviewer, or renderer was added.

## Terminology

New product/artifact/doc language uses `indicator` terminology:

```text
completion_indicator
effort_indicator
rep_range_indicator
load_indicator
training_indicator
```

Do not reintroduce the older wording the user flagged in new user-facing copy or artifact text.

## Future Next Architecture Target

After acceptance, Architecture should return to:

```text
Recovery Intelligence v2
```

## Known Baseline Drift

Known unrelated baseline drift remains intentionally unpatched:

```text
tests/test_daily_narrative_rich_day_service.py
```

Known mismatch:

```text
expected:
Read the day before adding more

actual:
Consider the full day
```
