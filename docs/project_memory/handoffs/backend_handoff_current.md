# Backend Handoff Current

Milestone: Nutrition Actuals Provenance & Confidence Model v1

Status: recommended next milestone / pending Architecture authorization.

Recommended owner: Backend Development / Data Layer.

Source baseline for future authorization: `main` at `0ebb1b4`.

Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

Do not implement until Architecture issues an explicit implementation handoff.

## Context

Nutrition Serving Unit Logging Streamlit UI v1 is accepted, merged, smoke-tested, and closed.

The serving-unit user flow now works end-to-end:

```text
GET /foods/canonical/search
-> GET /foods/canonical/{canonical_food_id}/serving-units
-> POST /nutrition/{user_id}/log-serving
-> resolved grams through food_entries
-> serving-unit provenance metadata
-> Target-vs-Actual existing actuals flow
```

The next backend problem is not more serving-unit UI. It is actuals semantics:

> What confidence/provenance should the system attach to logged actuals, and how should downstream nutrition logic understand them?

## Expected future backend direction

If Architecture authorizes this milestone, Backend should design and implement a narrow backend-owned interpretation layer for nutrition actuals confidence/provenance.

Candidate classification inputs:

- raw grams user entry;
- canonical grams user entry;
- canonical serving-unit entry;
- serving-unit entry with estimated grams;
- serving-unit entry with ranged grams;
- low-confidence serving estimate;
- missing nutrient values;
- unknown/low-confidence nutrient values;
- source-derived values vs user-entered values.

Expected output:

- narrow service/model contract;
- tests proving actuals confidence classification;
- no UI changes unless only project memory;
- no AI/provider changes;
- no Target-vs-Actual redesign yet.

## Strict non-goals unless explicitly authorized

Do not implement:

- new Streamlit serving-unit UI;
- meal planning;
- barcode scanning;
- USDA/Open Food Facts import;
- AI food matching;
- AI serving-size inference;
- nutrition explanation provider;
- food recommendation engine;
- macro target formula changes;
- Target-vs-Actual redesign;
- DailyCoachSynthesis redesign;
- workout/recovery/report changes;
- custom user serving units;
- broad nutrition logging rewrite.

## Historical continuity anchors

These phrases are reference-only for project-memory continuity:

- Local Command Menu App Runtime Correction v1
- app` restarts Linux FastAPI + Streamlit through SSH
- wapp
- No backend app runtime code changed.
