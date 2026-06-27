# Current State Update — Nutrition Actuals Provenance Debug / Integration Design v1

Current source of truth: `main`.

Required source main commit: `9b7430c`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_9b7430c_future-feature-technology-inventory-v1.zip`.

Previous accepted technical milestone: Nutrition Actuals Provenance & Confidence Model v1.

Previous technical QA result: `NUTRITION_ACTUALS_PROVENANCE_CONFIDENCE_MODEL_QA_V1_PASS`.

Previous docs milestone: Future Feature & Technology Inventory v1.

Previous docs status: `FUTURE_FEATURE_TECHNOLOGY_INVENTORY_V1_ACCEPTED_AND_MERGED`.

Current backend milestone: Nutrition Actuals Provenance Debug / Integration Design v1.

Branch: `feature/nutrition-actuals-provenance-debug-integration-design-v1`.

Commit-check mode: code.

QA class: CLASS 2 / CLASS 3 HYBRID — backend/API/debug contract over persisted actuals semantics.

Status: backend implementation complete / ready for Architecture review.

Requested final status: `NUTRITION_ACTUALS_PROVENANCE_DEBUG_INTEGRATION_DESIGN_V1_ACCEPTED`.

## Implemented integration path

Added public-safe backend debug/integration endpoint:

`GET /nutrition/{user_id}/actuals-confidence/debug?date=YYYY-MM-DD`

The endpoint returns NutritionActualInterpretation records for a user/date by reusing the accepted actuals provenance/confidence service.

## Response purpose

The debug path answers:

For this user/date, what logged nutrition actuals exist, and how does the backend interpret their provenance/confidence?

It is intended for QA, Architecture, Developer Mode planning, and future UI integration design.

It is not a normal user UI surface yet.

## Public-safe output

The endpoint returns:

- success;
- user_id;
- date;
- actuals list;
- public-safe actual interpretation fields;
- aggregate summary counts.

Each actual may include:

- food_entry_id;
- logged_date;
- source_type;
- precision;
- confidence_level;
- nutrient_completeness;
- has_serving_unit_metadata;
- has_grams_range;
- resolved_grams;
- grams_min / grams_max;
- grams_range_width / grams_range_percent;
- amount_source;
- serving_unit_confidence;
- missing_nutrients;
- limitations;
- reason_codes;
- display_flags.

Forbidden internals remain excluded:

- raw SQL rows;
- raw source payloads;
- raw DB object dumps;
- tracebacks;
- provider/runtime metadata;
- raw AI output;
- private debug internals;
- validator internals;
- hidden source blobs.

## Summary counts

The debug response includes aggregate counts:

- total_entries;
- entries_with_serving_unit_metadata;
- entries_with_grams_range;
- entries_with_low_or_unknown_confidence;
- entries_with_missing_nutrients.

## Boundary confirmation

No Target-vs-Actual totals changed.

No Target-vs-Actual normal response semantics changed.

No macro target formulas changed.

No nutrition logging behavior changed.

No serving-unit logging behavior changed.

No canonical grams logging behavior changed.

No raw/source logging behavior changed.

No Streamlit UI changed.

No AI/provider/CrewAI/direct_ollama behavior changed.

No food suggestions, meal planning, barcode scanning, external food imports, workout, training, recovery, or report behavior changed.

No snapshots committed.

## Files updated

Runtime/API/service/test files:

- `api/routes/nutrition.py`
- `services/nutrition_actuals_confidence_service.py`
- `tests/test_nutrition_actuals_confidence_debug_api.py`

Project-memory files:

- `docs/project_memory/current_state.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/project_continuity_bootstrap.md`
- `docs/project_memory/project_state.json`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`
- `docs/project_memory/milestones/nutrition_actuals_provenance_debug_integration_design_v1.md`

## Architecture review step

Return to Architecture for review and acceptance decision.

Requested final status:

`NUTRITION_ACTUALS_PROVENANCE_DEBUG_INTEGRATION_DESIGN_V1_ACCEPTED`.


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
