# Backend Intelligence Foundation v1

**Status:** Next product architecture center after docs/process cleanup
**Current accepted main:** `187e433 main_merge-platform-north-star-future-stack-canonicalization-v1`

Backend Intelligence Foundation is the product-brain prerequisite for advanced provider, RAG, vector, and agent architecture.

## Why This Exists

The v1-v4 provider experiments and Fully Free Source-Data Lab v1 showed that GPT-5.5 can write competent notes from richer source data, but provider voice iteration alone is not enough. Fully Free Lab v1 did not meaningfully beat v4. The bottleneck is backend intelligence and source-data depth.

## Foundation Layers

### Recovery Intelligence

Richer deterministic recovery interpretation from recovery, sleep, soreness, workload, and readiness signals.

### Workout Set Intelligence

Set-level and exercise-history understanding: recent sets/reps/load, progression, fatigue risk, repeated movement exposure, intensity context, and safe substitutions when authorized.

### Trend Engine

Stable trend summaries across days/weeks/months for adherence, training consistency, nutrition patterns, recovery patterns, weight/body metrics, and repeated blockers.

### Six-Month Seed Data

Realistic multi-month data for trend testing, coach memory testing, and fair provider evaluation.

### Food Knowledge Expansion

Curated, coach-usable food knowledge toward the long-term target of 450–500 practical foods.

## Sequencing Rule

Build the product brain first. Then build the fancy nervous system.

No serious RAG, vector search, embeddings, multi-agent orchestration, LangGraph, CrewAI, LlamaIndex, or production-grade agent architecture until these backend intelligence layers are designed and robust enough to feed them.

## Future Sequence

```text
Backend Intelligence Foundation
→ Unified Health State Snapshot / source-data contracts
→ Prompt Lab / reviewer / renderer evaluation
→ Advanced retrieval / orchestration candidates
```

Provider voice work pauses until richer source data and UI/renderer boundaries exist.

## Implementation Slice — Daily Coach Intelligence Snapshot + Recovery Intelligence v1

Baseline: `main @ 271ac7e`.

This is the first concrete implementation slice after the docs/process/development architecture refresh.

Scope:

- Recovery Intelligence v1 is implemented as a read-only deterministic layer over `daily_checkins`.
- Daily Coach Intelligence Snapshot v1 is implemented as a read-only source-data contract.
- Training Execution Summary is included read-only as existing evidence.
- Nutrition Trend Window is included read-only when available, otherwise recorded as a controlled limitation.
- Foundation layer status remains honest: Workout Set Intelligence, full Trend Engine, Six-Month Seed Data refinement, and Food Knowledge Expansion are not complete in this slice.

Provider voice iteration remains paused. This slice improves source-data truth, not prompt style.

## Implementation Slice — Daily Coach Workout Set Intelligence v1 + Intelligence Snapshot v2

Baseline: `main @ 43927d4`.

This is the second concrete implementation slice after Recovery Intelligence v1.

Scope:

- Workout Set Intelligence v1 is implemented as a read-only deterministic layer over completed planned workout executions.
- Daily Coach Intelligence Snapshot v2 includes `workout_set_intelligence` as the richer set/exercise training layer.
- Existing Training Execution Summary remains in the snapshot for compatibility.
- Recovery Intelligence v1 remains present.
- Nutrition Trend Window remains read-only when available, otherwise recorded as a controlled limitation.
- Foundation layer status is honest: Trend Engine, Six-Month Seed Data refinement, and Food Knowledge Expansion are not complete in this slice.

Provider voice iteration remains paused. This slice improves source-data truth, not prompt style.

Workout Set Intelligence v1 is accepted as of `123d115`. Platform North Star + Future Stack Canonicalization v1 is accepted as of `187e433`. Current next architecture planning target: `Recovery Intelligence v2 Architecture Planning v1`.


## Platform North Star Reference

The canonical long-term platform vision and future technology stack lives in:

```text
docs/project_memory/architecture/platform_north_star_and_future_stack.md
```

Backend Intelligence Foundation remains the product-brain prerequisite described by the north-star file. Future RAG, vector search, model routing, multi-agent orchestration, and SaaS-grade platform architecture stay parked until Architecture scopes them after the backend source-data contracts are mature enough.
