# Current State Update — Nutrition Serving Unit Logging Streamlit UI v1 Accepted

Current source of truth: `main` at `0ebb1b4`.

Current canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

Closed milestone: Nutrition Serving Unit Logging Streamlit UI v1.

Final accepted status: `NUTRITION_SERVING_UNIT_LOGGING_STREAMLIT_UI_V1_ACCEPTED_AND_MERGED`.

QA status: PASS via completed manual Streamlit workflow smoke.

Separate QA handoff: not required unless Architecture explicitly requests independent QA review.

Previous accepted baseline: Canonical Serving Unit Discovery API v1 at `fd87538`.

Feature commit: `15aa150 Add Streamlit serving unit nutrition logging`.

Canonical main merge commit: `0ebb1b4`.

## Accepted end-to-end serving-unit chain

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

## Accepted UI behavior

Streamlit now supports:

- canonical food search;
- canonical food selection;
- backend serving-unit discovery;
- backend-approved serving-unit selection;
- positive quantity entry;
- serving-unit log submission;
- backend-returned resolved grams display;
- existing grams logging path preservation;
- existing raw/source fallback preservation;
- existing Nutrition page behavior preservation;
- existing Target-vs-Actual / Nutrition Today Summary behavior preservation.

Confirmed boundaries:

- UI does not infer `serving_unit_id`.
- UI does not calculate grams.
- UI does not submit grams overrides.
- UI does not calculate nutrient values.
- UI does not query raw database tables.
- UI does not inspect `canonical_food_serving_units` directly.
- UI does not involve AI/provider logic.
- No backend behavior changed in the Streamlit UI milestone.
- No API shape changed in the Streamlit UI milestone.
- No persistence/schema changed in the Streamlit UI milestone.
- No Target-vs-Actual redesign was introduced.
- No nutrition target formula changed.
- No workout/training behavior changed.
- No AI/provider/CrewAI/direct_ollama behavior changed.
- No snapshots were committed.

## QA / validation closeout

Manual Streamlit smoke: PASS.

Manual smoke confirmed:

- Streamlit starts;
- Nutrition page loads;
- existing nutrition UI still appears;
- serving-unit logging section appears;
- user can search canonical foods;
- user can select canonical food;
- serving units load from backend;
- serving-unit selector shows backend-approved options;
- `serving_unit_id` is not manually typed by user;
- quantity accepts valid positive values;
- submit logs serving successfully;
- success message displays backend-returned resolved grams;
- no UI-side grams conversion is performed;
- existing grams logging path still works;
- existing raw/source fallback remains available;
- Target-vs-Actual / Nutrition Today Summary updates according to existing UI behavior;
- no traceback appears;
- no AI/provider path is involved;
- no raw DB/source/debug internals appear in normal UI;
- changing selected canonical food does not submit stale `serving_unit_id`.

QA classification: CLASS 4 — STREAMLIT / USER-FACING WORKFLOW.

Final QA interpretation: PASS.

## Current accepted nutrition foundation

Nutrition Serving Unit Data Model v1 is accepted and merged.

Nutrition Serving Unit Logging Backend v1 is accepted and merged.

Canonical Serving Unit Discovery API v1 is accepted and merged.

Nutrition Serving Unit Logging Streamlit UI v1 is accepted and merged.

The serving-unit user flow now works end-to-end.

## Snapshot Ownership / Main Acceptance Artifact Policy v1

Canonical accepted snapshots should be created from accepted `main` commits after Architecture acceptance / merge.

Feature snapshots may still exist as implementation artifacts, but they are not final accepted continuity snapshots unless explicitly designated.

Future handoffs must distinguish:

- feature commit;
- main merge commit;
- feature snapshot, if any;
- canonical accepted snapshot.

Current canonical accepted snapshot:

`fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`

## Recommended next implementation milestone

Recommended next milestone: Nutrition Actuals Provenance & Confidence Model v1.

Recommended owner: Backend Development / Data Layer.

Milestone type: backend/data model + service interpretation.

QA class: CLASS 3 — PERSISTENCE / DATA INTEGRITY / ACTUALS SEMANTICS.

Status: recommended next milestone / pending Architecture authorization.

Primary question:

How should the backend represent and expose confidence/provenance for nutrition actuals now that serving-unit logging is user-facing?

Purpose:

Create a backend-owned interpretation layer for nutrition actuals confidence and provenance so downstream nutrition features understand not just what grams were logged, but how reliable the logged actual is.

The system should be able to distinguish actual entries by source/confidence, for example:

- raw grams user entry;
- canonical grams user entry;
- canonical serving-unit entry;
- serving-unit entry with estimated grams;
- serving-unit entry with ranged grams;
- low-confidence serving estimate;
- missing nutrient values;
- unknown/low-confidence nutrient values;
- source-derived values vs user-entered values.

This should prepare the system for better:

- Target-vs-Actual interpretation;
- nutrition actuals transparency;
- future food suggestions;
- future AI nutrition explanations;
- future recommendation quality.

## Strict non-goals for the recommended next milestone

Do not implement without separate Architecture authorization:

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
