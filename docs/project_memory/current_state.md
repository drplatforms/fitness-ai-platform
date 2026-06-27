# Current State Update — Future Feature & Technology Inventory v1

Current source of truth: `main`.

Current accepted main commit: `9d66514`.

Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_9d66514_nutrition-actuals-provenance-confidence-model-v1.zip`.

Previous accepted milestone: Nutrition Actuals Provenance & Confidence Model v1.

Previous QA result: `NUTRITION_ACTUALS_PROVENANCE_CONFIDENCE_MODEL_QA_V1_PASS`.

Current project-memory milestone: Future Feature & Technology Inventory v1.

Milestone type: CLASS 0 — DOCS / PROJECT MEMORY ONLY.

Branch: `feature/future-feature-technology-inventory-v1`.

Status: docs/project-memory update complete / ready for Architecture review.

Requested final status: `FUTURE_FEATURE_TECHNOLOGY_INVENTORY_V1_ACCEPTED`.

## Current accepted nutrition capability

The accepted nutrition chain is now:

```text
canonical food search
-> backend-approved serving-unit discovery
-> Streamlit serving-unit selection
-> quantity entry
-> backend log-serving
-> resolved grams
-> food_entries actuals bridge
-> serving-unit provenance metadata
-> actuals provenance/confidence interpretation
-> Target-vs-Actual compatibility
```

Recently closed chain:

1. Nutrition Serving Unit Logging Backend v1
2. Canonical Serving Unit Discovery API v1
3. Nutrition Serving Unit Logging Streamlit UI v1
4. Nutrition Actuals Provenance & Confidence Model v1

## Why this milestone exists

The project is now moving fast enough that high-value product, technology, AI, workflow, UX, learning, and architecture ideas can get lost in development-controlled chaos.

Future Feature & Technology Inventory v1 creates a durable project-memory inventory so future Architecture, Backend, Streamlit, QA, TPM, and AI-provider work has a shared north star.

This milestone does not authorize implementation.

## North star recorded

Fitness AI Platform is a personal AI health operating system.

It is not just a workout tracker, macro tracker, chatbot, meal generator, or report generator.

The platform is intended to become a private, data-grounded coaching platform that understands training, nutrition, recovery, readiness, equipment, preferences, schedule constraints, adherence, friction, history, goals, uncertainty, provenance, and confidence.

## Doctrine recorded

Backend owns facts.

Backend owns validation.

Backend owns persistence.

Backend owns provenance/confidence.

Backend owns safety boundaries.

Streamlit renders approved fields and collects user input.

AI may explain, summarize, propose, or generate candidates only inside strict backend-approved contracts.

AI must not become the source of truth.

## Inventory document

Primary new inventory doc:

- `docs/project_memory/future_feature_technology_inventory_v1.md`

Milestone record:

- `docs/project_memory/milestones/future_feature_technology_inventory_v1.md`

## Ideas preserved

The inventory records future ideas including:

- AI meal generation;
- meal planning / meal prep;
- AI workout explanations / interpretations;
- nutrition label scanning;
- barcode scanning;
- photo-assisted food logging;
- restaurant/menu parsing;
- grocery list generation;
- receipt/grocery import eventually;
- What-If simulator;
- weekly/monthly coach review;
- RAG-powered education layer;
- coach memory / personalization;
- wearable integrations;
- mobile-first / PWA future;
- premium Daily Command Center.

## Boundary

This docs patch records ideas only.

It does not authorize implementation.

Every future idea still requires scoped milestone authorization, tests, validation, project-memory update, QA classification, Architecture acceptance, and canonical main snapshot after merge.

## Scope confirmation

No runtime code changed.

No API code changed.

No schema changed.

No Streamlit changed.

No provider/Ollama/CrewAI changed.

No nutrition behavior changed.

No training/workout behavior changed.

No snapshots committed.

## Next review step

Return to Architecture for docs/project-memory acceptance review.

Requested final status:

`FUTURE_FEATURE_TECHNOLOGY_INVENTORY_V1_ACCEPTED`.

## Historical continuity anchors — reference-only

These phrases are preserved for project-memory continuity checks and are reference-only, not current scope:

- Project Memory Alignment + North Star Architecture v1
- feature/daily-coach-narrative-same-session-approved-preview-bridge-v1
- reference-only
- No provider may run on normal Today page load
- Provider Narrative QA Matrix v2
- Daily Coach Same-Session Approved Preview Bridge v1 Retry
- Same-Session Bridge Runtime QA v1
- Daily Coach Narrative Product Voice Polish v1
- Daily Coach Narrative Product Voice Runtime QA v1
- PASS_WITH_NOTE
- sound right and be right
- Local Developer Command Menu Audit + Repo-Owned Commands v1
- scripts/fitness_commands.ps1
- Local Command Menu App Runtime Correction v1
- Linux is the canonical
- wapp
- Daily Coach Async Service Shell / No Worker v1
- service shell only
- no provider execution added
