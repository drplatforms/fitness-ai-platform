# Architecture Review Checklist v1

**Status:** Active architecture gate
**Current accepted main:** `23b5378 Merge daily coach fully free source-data lab evidence v1`

Use this checklist before accepting any new milestone.

## Review Gates

1. Scope/product fit: problem, owner, validator, non-goals.
2. Deterministic-first compliance: backend truth, fallback, AI boundary, provider opt-in.
3. Backend truth impact: facts, calculations, state, persistence, recommendations.
4. Provider dependency: model/provider, opt-in, validation/audit, disable path.
5. Persistence/schema/API impact: migration, compatibility, API shape.
6. Recovery intelligence impact: recovery signals, missing data, safe interpretation.
7. Workout intelligence impact: set-level history, progression, fatigue, unsafe advice risk.
8. Nutrition/food knowledge impact: macro targets, logged meals, food claims, food language.
9. Trend engine impact: multi-day/month evidence and gaps.
10. Source-data completeness impact: what the model/user receives and what is missing.
11. UI/renderer/card boundary impact: raw provider output, deterministic cards, copy placement.
12. Testing requirements: unit, integration, docs/project memory, artifact safety, opt-in tests.
13. Runtime/manual QA: commands, artifact directory, optional vs required smoke.
14. Docs/project memory: current_state, project_state, next_milestone, open_questions, milestone doc, handoffs, README/AGENTS.
15. Rollback/disable path.

## Current Strategic Gate

No serious RAG, vector search, embeddings, multi-agent orchestration, LangGraph, CrewAI, LlamaIndex, or production-grade agent architecture until Backend Intelligence Foundation is designed and robust enough to feed those systems.
