# Next Milestone — Nutrition Actuals Provenance & Confidence Model v1

Recommended next milestone: Nutrition Actuals Provenance & Confidence Model v1.

Recommended owner: Backend Development / Data Layer.

CC: Architecture, Streamlit UI, QA / Regression Testing, TPM / Project Control, Project Memory / All Future Agents.

Milestone type: backend/data model + service interpretation.

QA class: CLASS 3 — PERSISTENCE / DATA INTEGRITY / ACTUALS SEMANTICS.

Status: recommended next milestone / pending Architecture authorization.

Do not implement until Architecture issues an explicit implementation handoff.

## Current accepted baseline

Current source of truth: `main` at `0ebb1b4`.

Current canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

Closed milestone: Nutrition Serving Unit Logging Streamlit UI v1.

Final accepted status: `NUTRITION_SERVING_UNIT_LOGGING_STREAMLIT_UI_V1_ACCEPTED_AND_MERGED`.

QA status: PASS via completed manual Streamlit workflow smoke.

The accepted serving-unit chain is now complete:

```text
GET /foods/canonical/search
-> GET /foods/canonical/{canonical_food_id}/serving-units
-> POST /nutrition/{user_id}/log-serving
-> resolved grams through food_entries
-> serving-unit provenance metadata
-> Target-vs-Actual existing actuals flow
```

## Why the next milestone is not more serving-unit UI

The serving-unit user flow now works end-to-end.

The next nutrition problem is no longer:

> Can the user log by serving size?

That is now accepted.

The next problem is:

> What confidence/provenance should the system attach to logged actuals, and how should downstream nutrition logic understand them?

Current state:

- serving-unit logs resolve to grams;
- provenance metadata exists;
- `grams_min` / `grams_max` / `confidence` / `amount_source` may exist;
- Target-vs-Actual reads resolved grams through the existing actuals bridge.

Remaining product gap:

Target-vs-Actual and future food suggestions do not yet meaningfully distinguish:

- exact grams entered by user;
- backend-approved serving estimate;
- ranged serving estimate;
- low-confidence serving estimate;
- missing/unknown nutrient values;
- source-derived values vs user-entered values.

## Expected goal

Define and expose a backend-owned confidence/provenance interpretation for logged nutrition actuals.

The system should be able to distinguish actual entries by source/confidence, for example:

- raw grams user entry;
- canonical grams user entry;
- canonical serving-unit entry;
- serving-unit entry with estimated grams;
- serving-unit entry with ranged grams;
- missing nutrient values;
- unknown/low-confidence nutrient values.

This should prepare the system for better:

- Target-vs-Actual interpretation;
- nutrition actuals transparency;
- future food suggestions;
- future AI nutrition explanations;
- future recommendation quality.

## Suggested implementation shape for Architecture to authorize

Suggested output for the next Backend handoff:

- narrow service/model contract;
- tests proving actuals confidence classification;
- no UI changes unless only project memory;
- no AI/provider changes;
- no Target-vs-Actual redesign yet.

Possible implementation areas to inspect after authorization:

- existing `food_entries` logging path;
- `nutrition_serving_unit_log_metadata` provenance table;
- canonical grams logging behavior;
- raw/source grams logging behavior;
- Target-vs-Actual actuals service read path;
- nutrition service daily actuals assembly.

## Strict non-goals for next milestone

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

This should be a narrow backend-owned actuals/provenance interpretation milestone.

## Historical continuity anchors

The following phrases are preserved for project-memory continuity checks. They are reference-only and are not current Nutrition Actuals Provenance & Confidence Model v1 scope.

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- feature/daily-coach-async-persistence-contracts-schema-v1
- schema/contracts
- NOT_AUTHORIZED_YET
