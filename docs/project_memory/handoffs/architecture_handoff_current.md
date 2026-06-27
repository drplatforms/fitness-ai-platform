# Architecture Handoff Current

Milestone closing: Nutrition Serving Unit Logging Streamlit UI v1

Final status: `NUTRITION_SERVING_UNIT_LOGGING_STREAMLIT_UI_V1_ACCEPTED_AND_MERGED`.

Current source of truth: `main` at `0ebb1b4`.

Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

QA status: PASS via completed manual Streamlit workflow smoke.

Separate QA handoff: not required unless Architecture explicitly wants independent QA review.

## Closeout summary

Nutrition Serving Unit Logging Streamlit UI v1 is accepted, merged, smoke-tested, and closed.

The accepted nutrition serving-unit chain is now:

```text
GET /foods/canonical/search
-> user selects canonical food
-> GET /foods/canonical/{canonical_food_id}/serving-units
-> user selects backend-approved serving unit
-> user enters quantity
-> POST /nutrition/{user_id}/log-serving
-> backend validates food/unit/ownership
-> backend resolves grams
-> backend writes food_entries
-> backend writes serving-unit provenance metadata
-> existing Target-vs-Actual reads resolved grams
```

## Accepted snapshot / commit state

Previous accepted baseline: `fd87538 Canonical Serving Unit Discovery API v1`.

Feature commit: `15aa150 Add Streamlit serving unit nutrition logging`.

Canonical main merge commit: `0ebb1b4`.

Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

## Accepted UI behavior

Streamlit now supports canonical food search, backend serving-unit discovery, backend-approved serving-unit selection, positive quantity entry, serving-unit log submission, backend-returned resolved grams display, existing grams logging path preservation, existing raw/source fallback preservation, and existing Target-vs-Actual / Nutrition Today Summary behavior preservation.

Confirmed boundaries:

- UI does not infer `serving_unit_id`.
- UI does not calculate grams.
- UI does not submit grams override.
- UI does not calculate nutrient values.
- UI does not query raw database tables.
- UI does not involve AI/provider logic.
- No backend behavior changed.
- No API shape changed.
- No persistence/schema changed.
- No Target-vs-Actual redesign.
- No nutrition target formula changed.
- No workout/training changed.
- No AI/provider/CrewAI/direct_ollama changed.
- No snapshots committed.

## Recommended next Architecture decision

Authorize or refine the next recommended milestone:

Nutrition Actuals Provenance & Confidence Model v1.

Recommended owner: Backend Development / Data Layer.

Primary question:

How should the backend represent and expose confidence/provenance for nutrition actuals now that serving-unit logging is user-facing?

Recommended first milestone shape:

- narrow backend service/model contract;
- tests proving actuals confidence classification;
- no UI changes unless only project memory;
- no AI/provider changes;
- no Target-vs-Actual redesign yet.

## Historical continuity anchors

These phrases are reference-only for project-memory continuity:

- Local Command Menu App Runtime Correction v1
- app` is now the canonical Linux runtime launcher
- wapp
- Linux is the canonical FastAPI + Streamlit app runtime
