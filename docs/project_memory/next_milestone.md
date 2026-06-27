# Next Milestone — Nutrition Actuals Provenance & Confidence Model v1 Review

Current implementation milestone: Nutrition Actuals Provenance & Confidence Model v1.

Owner: Backend Development / Data Layer.

Status: backend implementation complete / ready for Architecture and focused QA review.

Requested final status: `NUTRITION_ACTUALS_PROVENANCE_CONFIDENCE_MODEL_V1_ACCEPTED`.

## Current baseline

Known accepted runtime/product baseline: `0ebb1b4 Nutrition Serving Unit Logging Streamlit UI v1`.

Known project-memory closeout feature commit: `d9a3906 Close Streamlit serving unit UI project memory`.

Canonical accepted product snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

Feature branch: `feature/nutrition-actuals-provenance-confidence-model-v1`.

## Review focus

Architecture should review the new backend-owned actuals interpretation contract:

- source type classification;
- precision classification;
- confidence level classification;
- serving-unit metadata handling;
- grams range width/percent handling;
- nutrient completeness handling;
- public-safe reason codes / limitations / display flags;
- no changes to logging behavior;
- no changes to Target-vs-Actual totals;
- no Streamlit changes;
- no AI/provider changes.

## QA focus

QA class:

CLASS 3 — PERSISTENCE / DATA INTEGRITY / ACTUALS SEMANTICS.

Focused QA should validate:

1. Raw/source grams entry classifies as `raw_grams`.
2. Canonical grams entry classifies as `canonical_grams`.
3. Serving-unit entry with metadata classifies as `canonical_serving_unit`.
4. Serving-unit interpretation exposes resolved grams from persisted backend value.
5. Serving-unit entry with `grams_min` / `grams_max` is marked `ranged`.
6. Wide gram range adds public-safe limitation/reason code.
7. Low serving-unit confidence adds public-safe limitation/reason code.
8. Missing serving-unit metadata does not crash classification.
9. Missing nutrient values are classified as missing/unknown, not zero.
10. Unknown source classifies safely as `unknown`.
11. Public-safe output excludes raw source payloads and SQL/debug internals.
12. Existing serving-unit logging remains stable.
13. Existing canonical grams logging remains stable.
14. Existing raw/source nutrition logging remains stable.
15. Existing Target-vs-Actual totals remain stable.

## Strict non-goals preserved

Do not add in this milestone:

- Streamlit changes;
- Target-vs-Actual UI changes;
- Target-vs-Actual redesign;
- macro target formula changes;
- food suggestion engine;
- meal planning;
- barcode scanning;
- external food database import;
- USDA/Open Food Facts import;
- AI food matching;
- AI serving-size inference;
- nutrition explanation provider changes;
- CrewAI changes;
- direct_ollama changes;
- RAG;
- embeddings;
- PostgreSQL migration;
- custom serving units;
- user-defined serving overrides;
- workout/training/recovery/report changes;
- broad nutrition logging rewrite.

## Potential next milestone after acceptance

After Architecture acceptance and QA pass, a future milestone can decide whether to expose the interpretation in Target-vs-Actual summaries or keep it internal for provider/suggestion readiness.

Do not start that integration until Architecture explicitly authorizes it.

## Historical continuity anchors — reference-only

These phrases are preserved for project-memory continuity checks and are not current implementation scope:

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- feature/daily-coach-async-persistence-contracts-schema-v1
- schema/contracts
- NOT_AUTHORIZED_YET
