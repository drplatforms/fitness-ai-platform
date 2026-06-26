# Current State

Latest accepted milestone: Nutrition Catalog Diagnostic v1.

Latest accepted feature commit: `9f1285f`.

Latest main merge commit: `8b2c4c3`.

Latest accepted snapshot: `fitness_ai_snapshot_2026-06-26_8b2c4c3_merge-nutrition-catalog-diagnostic-code-closeout.zip`.

Current implementation milestone: Nutrition Serving Unit Data Model v1.

Current branch: `feature/nutrition-serving-unit-data-model-v1`.

Source baseline: `main` at `8b2c4c3`.

Milestone type: backend data model / service / tests / project memory update.

## Current process doctrine

The current operating doctrine is:

> Bite by bite, just bigger bites.

Meaning:

- Larger objectives are allowed.
- Single patches stay narrow.
- Complexity determines process weight.
- Complex backend behavior requires diagnostic-first and test-first gates where practical.
- Real smoke failures become automated regression tests, diagnostic/coverage tests, documented limitations, or backlog items.
- Architecture defines v1/v2 scope before branches spiral.
- Backend must not blindly stack patches after repeated failures.
- QA validates the real user path, not only generic test-green status.

## Recent accepted milestones

### Workout Preview Full-Slot Rotation v1

Accepted and merged.

- Feature commit: `3b32f97`
- Main merge commit: `f39b403`
- Snapshot: `fitness_ai_snapshot_2026-06-25_3b32f97_fix-first-refresh-workout-slot-rotation.zip`
- Accepted scope: immediate previous-preview anti-repeat.
- Deferred v2 scope: rolling multi-refresh novelty.

This milestone proved that generic tests were not enough. The real path was `variation 0 -> variation 1`, where refreshed previews repeated exercises despite valid alternatives. A focused quality gate reproduced the behavior before the narrow fix landed.

### Exercise Catalog Utilization / Specialized Movement Coverage v1

Accepted and merged.

- Feature commit: `1d44b3d`
- Main merge commit: `b343a47`
- Snapshot: `fitness_ai_snapshot_2026-06-26_1d44b3d_preserve-primary-workout-rotation-after-catalog-expansion.zip`
- Accepted scope: improved deterministic catalog breadth and specialized movement reachability past quality gates.
- Preserved: Quick / Standard / Full sizing, immediate preview refresh anti-repeat, selected workout persistence, Active Workout persistence, Today workout de-dup, and no provider/AI workout generation path.
- Deferred future scope: Exercise Eligibility Matrix v1, Catalog Reachability Audit v2, rolling exposure tracking, deeper movement-family de-duplication, and complete catalog reachability.

This milestone proved the value of stop conditions. The first breadth implementation improved utilization but regressed preview rotation. Linux smoke later caught a home-gym hinge/vertical_pull regression. Patch drift also occurred. The final accepted branch succeeded only after each failure was treated as a diagnostic signal instead of continuing blind patch stacking.

### Test-First Quality Gate Development Plan v1

Accepted and merged.

- Feature commit: `227990e`
- Main merge commit: `37d210f`
- Snapshot: `fitness_ai_snapshot_2026-06-26_227990e_clarify-continuity-brief-metadata.zip`
- Accepted scope: canonized diagnostic-first / test-first quality gate process.
- Preserved: no app/runtime behavior changes, no service changes, no provider changes, no workout/nutrition/catalog behavior changes.

This milestone made the current quality doctrine repo-discoverable instead of chat-only.

### Exercise Eligibility Matrix v1

Accepted and merged.

- Feature commit: `851a7ca`
- Primary code checkpoint commit: `05d319e`
- Main merge commit: `f469c89`
- Snapshot: `fitness_ai_snapshot_2026-06-26_851a7ca_update-exercise-eligibility-matrix-project-memory.zip`
- Accepted scope: explicit generator-facing exercise eligibility matrix, diagnostic tool, quality-gate tests, reachability/exclusion visibility, and preserved workout behavior.
- Preserved: Quick / Standard / Full sizing, immediate preview refresh anti-repeat, selected workout persistence, Active Workout persistence, Today workout de-dup, no provider/AI workout generation path.
- Deferred future scope: complete catalog reachability, rolling multi-refresh novelty, persistent exercise exposure tracking, arms/mobility slot expansion, deeper movement-family de-duplication, and optional diagnostic/service deduplication cleanup.

Diagnostic baseline from the accepted branch:

- total active catalog exercises: 240
- equipment-compatible exercises: 237
- generator-eligible exercises classified by matrix/diagnostic: 232
- exercises selected in 10-variation deterministic sweep: 54
- largest exclusion reason: `not_supported_by_current_generator_candidate_pools` (170)
- weak movement families called out by diagnostic: arms_biceps, arms_triceps, mobility

### Nutrition Catalog + Serving Foundation Planning v1

Accepted and merged.

- Feature commit: `8c72f23`
- Main merge commit: `94dc8fd`
- Snapshot: `fitness_ai_snapshot_2026-06-26_8c72f23_plan-nutrition-catalog-and-serving-foundation.zip`
- Accepted scope: planning/project-memory only nutrition foundation roadmap, two-layer food catalog doctrine, serving-unit confidence/range strategy, nutrition actuals confidence direction, deterministic suggestions before AI meal/snack generation, and provider boundary.
- Preserved: no app/runtime behavior changes, no food catalog expansion, no serving-unit implementation, no food logging changes, no nutrition calculation changes, no provider/Ollama behavior changes, no Streamlit changes, no workout changes, no recovery changes, no migrations, no dependencies.

This milestone pivoted the project from the workout foundation pass to the nutrition foundation phase.

### Nutrition Catalog Diagnostic v1

Accepted and merged through diagnostic project-memory/code closeout.

- Feature implementation commit: `6765abb`
- Diagnostic code closeout commit: `9f1285f`
- Main merge commit: `8b2c4c3`
- Source snapshot for the current branch: `fitness_ai_snapshot_2026-06-26_8b2c4c3_merge-nutrition-catalog-diagnostic-code-closeout.zip`
- Accepted scope: diagnostic service, diagnostic CLI, focused tests, project-memory closeout, and no app/runtime behavior change.
- Preserved: no catalog expansion, no serving units, no food logging behavior changes, no nutrition calculation changes, no provider/Ollama behavior changes, no Streamlit changes, no workout changes, no recovery changes.

This milestone established that the canonical food catalog is stronger than expected and that serving-unit/confidence infrastructure is the immediate blocker before practical household-measure logging or food suggestions.

## Current implementation milestone

Nutrition Serving Unit Data Model v1 is the active implementation milestone.

The milestone adds backend-owned serving-unit metadata for canonical foods without changing normal nutrition logging behavior, Streamlit behavior, target-vs-actual behavior, provider behavior, workout behavior, or recovery behavior.

Implemented surfaces:

- serving-unit model/dataclass contracts
- serving-unit persistence/schema initialization
- deterministic serving-unit lookup and conversion helpers
- starter serving-unit seed script
- idempotent seed behavior
- focused model/service/seed tests
- project-memory closeout

## Nutrition Catalog Diagnostic v1 findings

Current diagnostic summary:

- total legacy food records: 3,475
- total canonical food records: 222
- active canonical food records: 222
- inactive canonical food records: 0
- raw source food records: 0
- canonical foods safe for logging: 222
- canonical foods safe for suggestions: 222
- legacy/user-created-or-legacy food records: 3,467
- canonical alias rows: 555
- foods with aliases: 222
- foods without aliases: 0
- searchable values: 682

Schema state:

- legacy food, nutrient, and food entry tables are present.
- canonical food, canonical alias, canonical nutrient, raw source record, and food source link tables are present.
- two-layer table structure exists, but raw/source staging is currently empty.
- serving-unit tables are not present.

Nutrient completeness:

- core macros tracked: calories, protein, carbohydrates, fat.
- complete core macro canonical foods: 222 / 222 (100%).
- foods missing one or more core macro fields: 0.
- optional nutrient coverage for fiber, sugar, and sodium is currently 0.
- macro-derived calorie warnings exist for some low-calorie vegetables such as Asparagus, Mushrooms, and Spinach; these are diagnostic warnings, not blocking errors.

Serving-unit readiness:

- grams-based logging is supported.
- canonical default unit/default grams are present for all 222 canonical foods.
- household units are not supported.
- serving-unit model/table is not present.
- foods with no serving-unit metadata: 222.
- serving units are not representable safely without schema/model work.

Alias/search readiness:

- aliases are supported.
- canonical display names and normalized names are supported.
- all 222 canonical foods have aliases.
- no canonical foods are currently missing aliases.

High-value staple coverage:

- required staple groups present: 43.
- missing staple groups: 1.
- present but incomplete staple groups: 0.
- only missing high-value staple called out by the diagnostic: mixed nuts.
- duplicate/near-duplicate risks exist around broad search terms such as chicken breast, greek yogurt, potato, egg, bread, and tortilla.

Logging assumptions:

- logs use `food_id` linkage.
- logs use grams.
- logs do not use quantity/unit, servings, free-text food names, meal grouping, or meal type.
- logs use entry date and user id.
- macros are not persisted directly on logs.
- macros are recalculated from food/nutrient tables.
- current summary: food logs are grams-based and linked to legacy foods; canonical logging writes through into legacy food/nutrient tables.
- serving units are not representable without schema/model changes.

Actuals/targets dependencies:

- daily actuals service: `services.nutrition_service.get_daily_nutrition`.
- target-vs-actual service: `services.nutrition_target_vs_actual_service.build_target_vs_actual_nutrition_summary`.
- dependent tables: `food_entries`, `food_nutrients`, `nutrients`.
- actuals assume grams.
- macro gaps exist.
- confidence is not represented.
- missing logs aggregate to an empty actuals result; downstream target-vs-actual behavior controls unavailable/zero display semantics.

Food suggestion readiness:

- deterministic suggestion service is present.
- complete macro canonical foods available: 222.
- active canonical foods available: 222.
- protein/carb/fat groups are backend-derived.
- common snack/meal coverage is mostly present: 43 present, 1 missing.
- serving amounts are not ready.
- confidence/source is not present at the catalog/actuals level.
- readiness: limited.
- blockers: serving unit model missing, actuals confidence missing, source confidence not catalog-level, high-value staple gaps exist.

AI/provider grounding readiness:

- provider can quote approved actuals, targets, gaps, and canonical food names.
- provider cannot safely use serving units yet.
- risk of invented foods/macros remains medium until serving and catalog contracts are hardened.
- validation boundary is present.
- readiness: limited until serving units and confidence exist.

## Recommended next nutrition milestone

Recommended next milestone after Nutrition Serving Unit Data Model v1 acceptance: Nutrition Serving Unit Logging Contract Design v1.

Reason:

- the canonical catalog is already strong enough for a diagnostic baseline: 222 active canonical foods, 100% core macro completeness, alias/search support, and broad high-value staple coverage.
- the biggest blocker is not raw catalog size; it is serving-unit and confidence infrastructure.
- grams-only logs and legacy write-through cannot represent household measures, confidence, or estimated serving conversions safely yet.

Architecture may still choose a short Nutrition Canonical Food Model Review v1 first if it wants to settle canonical/legacy write-through and source-confidence semantics before schema work.

## Nutrition Serving Unit Data Model v1 implementation checkpoint

Current serving-unit implementation adds trusted backend metadata only. It does not expose serving-based logging yet.

Implemented files:

- `models/nutrition_serving_unit_models.py`
- `services/nutrition_serving_unit_service.py`
- `scripts/seed_canonical_food_serving_units.py`
- `tests/test_nutrition_serving_unit_data_model_v1.py`

Current seed smoke result on Windows:

- first seed run inserted serving units: 18
- second seed run inserted serving units: 0
- second seed run updated serving units: 18
- active serving-unit count: 18
- foods with active serving units: 12
- missing canonical foods: none
- confidence vocabulary used: High / Moderate

Seeded examples include cooked white rice, cooked brown rice, large egg, banana, peanut butter, Greek yogurt, dry oats, cooked chicken breast, olive oil, baked potato, apple, and whey protein powder.

Known validation note:

- Full pytest on source main `8b2c4c3` already has 7 unrelated Daily Coach / Daily Narrative baseline failures.
- Those failures reproduced on the source baseline and are not caused by Nutrition Serving Unit Data Model v1.
- Serving-unit focused validation, related nutrition/canonical validation, seed smoke, idempotency smoke, and full suite excluding the known baseline Daily Coach / Daily Narrative failures were green before project-memory closeout.

## Nutrition foundation direction

Nutrition should become a grounded coaching engine, not only a calorie/macro logger.

Backend owns:

- food truth
- canonical foods
- nutrient data
- serving unit conversions
- grams
- confidence
- logged actuals
- targets
- gaps
- validation
- fallback

Provider/AI may eventually help explain or assemble approved facts, but must not invent foods, macros, serving sizes, gram conversions, targets, missing intake, or health claims.

## Two-layer food catalog strategy

Future nutrition work should strongly prefer a two-layer model.

Layer 1: raw / source food data.

- large imported food datasets
- USDA or source records
- not directly user-facing
- useful for search, enrichment, mapping, future expansion

Layer 2: canonical app food catalog.

- curated food names
- aliases
- nutrients per 100g
- approved serving units
- confidence/source metadata
- safe for logging
- safe for deterministic suggestions
- safe for AI/provider contracts

Doctrine: do not expose a huge raw import directly to food logging, suggestions, or provider contracts. Raw/staging imports can be large, but only approved canonical foods should power normal user-facing flows.

## Complex Backend Quality Gate

For any complex feature involving state, scoring, selection, persistence, provider output, routing, nutrition targets, workout generation, recommendation logic, or user-visible workflow behavior:

1. Diagnose current behavior before patching.
2. Identify the exact failing, missing, or underperforming user path.
3. Add a failing regression test, diagnostic test, or coverage test that captures the real path where practical.
4. Confirm the test fails or exposes the gap before implementation.
5. Apply the smallest safe implementation change.
6. Prove the new test passes.
7. Re-run prior milestone regression tests.
8. Re-run the original manual/browser smoke path.
9. Update project memory.
10. Only then request Architecture acceptance.

Do not treat generic green tests as sufficient if the product-critical path is not covered.

## Current boundaries

- Deterministic backend owns truth.
- Provider may propose only inside approved contracts.
- Backend validates and approves.
- User sees only approved output.
- Deterministic fallback remains mandatory.
- No provider may run on normal Today page load unless Architecture explicitly promotes it.
- No provider/AI workout generation is accepted.
- No provider may invent foods, serving units, grams, macros, targets, or gaps.
- No raw/staging food import should directly power user-facing logging, suggestions, or provider contracts.
- No catalog expansion was implemented in Nutrition Catalog Diagnostic v1.
- No serving units were implemented in Nutrition Catalog Diagnostic v1.
- No food logging behavior changed in Nutrition Catalog Diagnostic v1.
- No nutrition calculation behavior changed in Nutrition Catalog Diagnostic v1.
- No provider/Ollama behavior changed in Nutrition Catalog Diagnostic v1.
- No Streamlit UI behavior changed in Nutrition Catalog Diagnostic v1.
- No workout or recovery behavior changed in Nutrition Catalog Diagnostic v1.
- No CrewAI/Ollama/OpenAI/PydanticAI/LangGraph workout generation is accepted.
- No worker/queue/scheduler/polling is accepted unless explicitly scoped.
- No broad rewrite is authorized by process docs.
- Codex is not used by default.

## Current next-roadmap candidates

After Nutrition Serving Unit Data Model v1 is accepted, likely roadmap candidates are:

- Nutrition Serving Unit Logging Contract Design v1.
- Nutrition Actuals Confidence Model v1 if Architecture wants confidence semantics before serving-based logging.
- Nutrition Logging Backend Contract v1 after serving-unit logging direction is accepted.
- Curated Food Catalog Expansion v1 after serving-unit/confidence model decisions.
- Nutrition Actuals Confidence v1.
- Nutrition Deterministic Food Suggestions v1.
- Nutrition AI Meal/Snack Candidate Contract v1.
- Recovery engine improvements later.
- Workout rolling exposure / catalog reachability work later.

## Historical continuity reminders

Historical project-memory entries remain valid context and should not be erased just because the current active milestone changed:

- Project Memory Alignment + North Star Architecture v1.
- `feature/daily-coach-narrative-same-session-approved-preview-bridge-v1` is reference-only, not accepted.
- Provider Narrative QA Matrix v2.
- Daily Coach Same-Session Approved Preview Bridge v1 Retry.
- Same-Session Bridge Runtime QA v1.
- Daily Coach Narrative Product Voice Polish v1.
- Daily Coach Narrative Product Voice Runtime QA v1.
- PASS_WITH_NOTE product-voice outcomes remain context for future voice work.
- The product goal remains to sound right and be right.
- Local Developer Command Menu Audit + Repo-Owned Commands v1.
- `scripts/fitness_commands.ps1` remains the repo-owned command source.
- Local Command Menu App Runtime Correction v1 clarified that Linux is the canonical app runtime and `wapp` is Windows-local only.
- Daily Coach Async Service Shell / No Worker v1 remains service shell only; no provider execution added.
