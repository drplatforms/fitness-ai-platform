# Nutrition Serving Unit Logging Contract Design v1

Status: proposed contract / docs-only / ready for Architecture review.

Owner: Backend Development / Data Layer.

Milestone type: design / contract / project memory only.

Source baseline: `main` at `9cb1d41`.

Branch: `feature/nutrition-serving-unit-logging-contract-design-v1`.

Commit-check mode: docs-only.

## Purpose

Nutrition Serving Unit Data Model v1 added backend-owned serving-unit metadata for canonical foods. The app can now represent safe, curated units such as `1 large egg`, `1 medium banana`, `1 tablespoon peanut butter`, `1 cup Greek yogurt`, `1/2 cup cooked rice`, and `1 scoop whey protein powder`.

This contract defines how that metadata should enter nutrition logging in a future implementation without changing runtime behavior in this milestone.

The future goal is a safe backend-owned path where a user-facing serving input becomes a grams-based nutrition log entry with preserved provenance:

```text
canonical food + backend-approved serving unit + quantity
-> backend serving-unit lookup
-> backend grams resolution
-> canonical nutrient calculation/write-through
-> food_entries grams bridge
-> serving-unit provenance metadata
-> existing Target-vs-Actual actuals math
```

The current design milestone does not implement this path. It defines the contract Architecture should accept before implementation.

## Current baseline

The accepted serving-unit foundation provides:

- `canonical_food_serving_units` persistence;
- serving units linked to canonical foods;
- deterministic active-unit lookup;
- deterministic serving-to-grams estimation;
- `grams_default`, `grams_min`, `grams_max`, and confidence metadata;
- idempotent starter seed coverage for 18 active serving units across 12 canonical foods;
- no food logging behavior change;
- no Streamlit behavior change;
- no Target-vs-Actual behavior change;
- no provider/Ollama/CrewAI behavior change.

Current nutrition logging surfaces remain grams-based:

- `POST /nutrition/log` accepts legacy `food_id` + `grams`.
- `POST /nutrition/{user_id}/log-canonical` accepts `canonical_food_id` + `grams`.
- `food_entries` remains the grams-based actuals bridge.
- Target-vs-Actual reads logged grams from `food_entries` and computes actuals from nutrient-per-100g rows.

Current canonical food logging already writes through canonical foods into existing legacy-compatible food/nutrient/entry tables. Serving-unit logging should preserve that compatibility in v1.

## Design goals

The future serving-unit logging implementation should:

1. Keep backend ownership of serving-unit conversion.
2. Keep `food_entries` as the grams-based actuals bridge.
3. Persist the resolved grams used at the time of logging.
4. Preserve serving-unit provenance next to the grams-based entry.
5. Preserve enough historical metadata that old logs remain auditable even if serving-unit metadata changes later.
6. Keep Target-vs-Actual grams-based in v1.
7. Keep Streamlit as a renderer/selector of backend-approved fields only.
8. Prevent AI/provider from inventing foods, serving units, grams, macros, targets, or actuals.
9. Treat missing nutrient data as missing/unknown, never zero.
10. Leave room for future actuals-confidence display without forcing that behavior into v1.

## Non-goals

This design milestone does not authorize:

- runtime implementation;
- API endpoint changes;
- schema migration/code changes;
- `/nutrition/log` changes;
- Streamlit changes;
- Target-vs-Actual behavior changes;
- provider/Ollama/CrewAI changes;
- food suggestion changes;
- meal planning;
- workout/recovery/report changes;
- USDA/source imports;
- barcode scanning;
- user-defined serving-unit overrides.

Future implementation milestones must preserve these boundaries unless Architecture explicitly changes scope.

## Persistence options considered

### Option A: Extend `food_entries` directly

This would add serving-unit fields directly to `food_entries`, such as:

- `canonical_food_id`
- `serving_unit_id`
- `serving_quantity`
- `resolved_grams`
- `grams_min`
- `grams_max`
- `confidence`
- `amount_source`
- `original_serving_display`

Advantages:

- simple join path;
- one table contains both actual grams and serving metadata;
- easy to query a single entry.

Disadvantages:

- pollutes the currently stable grams bridge;
- risks broad schema/test/UI churn;
- mixes actuals data with provenance data;
- makes legacy grams-entered entries carry many nullable serving-specific fields;
- makes future canonical logging and legacy logging harder to reason about.

Decision: not preferred for v1.

### Option B: Companion serving-unit provenance table

This keeps `food_entries` as the actuals bridge and adds a future metadata table keyed to `food_entries.id`.

Suggested table name:

- `nutrition_serving_unit_log_metadata`

Alternative acceptable name:

- `food_entry_serving_unit_metadata`

Suggested fields:

- `id`
- `food_entry_id`
- `user_id`
- `canonical_food_id`
- `serving_unit_id`
- `serving_quantity`
- `resolved_grams`
- `grams_min`
- `grams_max`
- `serving_unit_confidence`
- `amount_source`
- `original_serving_display`
- `source`
- `source_note`
- `created_at`
- `updated_at`

Advantages:

- preserves existing `food_entries` behavior;
- preserves current Target-vs-Actual compatibility;
- keeps provenance separate from actuals bridge;
- supports future confidence/quality display;
- supports serving-unit auditability without forcing all entries into a new log model;
- keeps legacy grams-entered rows simple.

Disadvantages:

- requires joins for history/provenance display;
- requires transactional insert of both `food_entries` and metadata;
- requires migration discipline when future canonical logging evolves.

Decision: preferred v1 direction.

### Option C: New canonical nutrition log table

This would create a full canonical-first logging model and eventually reduce reliance on `food_entries`.

Advantages:

- cleaner long-term architecture;
- could make canonical food logging first-class;
- could preserve source/provenance/confidence in one richer table.

Disadvantages:

- too large for v1;
- would require broad Target-vs-Actual changes;
- would require report/daily/Streamlit/history review;
- would risk destabilizing already-working grams-based actuals.

Decision: defer. This may be a future nutrition logging v2 architecture discussion after serving-unit logging and actuals confidence are proven.

## Recommended persistence strategy

Use `food_entries` as the grams-based actuals bridge and add a companion serving-unit provenance table in the future backend implementation.

Future serving-unit logging should:

1. Resolve serving-unit quantity to grams in backend code.
2. Insert a normal `food_entries` row using the resolved grams.
3. Insert a companion provenance row tied to that `food_entries.id`.
4. Return public-safe display/provenance fields to the caller.

This means Target-vs-Actual continues to compute actuals from the same grams path it uses today.

## Resolved grams persistence

Resolved grams must be persisted.

Reason:

- historical actuals should not change if serving-unit metadata changes later;
- logs must remain auditable;
- Target-vs-Actual should compute using the grams that were approved at log time;
- future displays can show both the user-facing serving and the backend-resolved grams.

Persisted resolved grams should be the exact value inserted into `food_entries.grams`.

## Gram range and confidence persistence

The future provenance table should copy the gram range and confidence used at log time:

- `grams_min`
- `grams_max`
- `serving_unit_confidence`

This preserves historical estimate quality even if the canonical serving-unit row is later updated.

If Architecture wants the smallest possible implementation, `resolved_grams` and `serving_unit_confidence` are the minimum acceptable provenance fields, but the recommended v1 stores the full range.

## Canonical food id and legacy food id

Future serving-unit logs should preserve both identities through the two-layer model:

- `food_entries.food_id` remains the legacy/write-through id used by current actuals.
- Companion provenance stores `canonical_food_id`.
- Companion provenance stores `serving_unit_id`.

This avoids forcing Target-vs-Actual to understand canonical/serving-unit internals in v1 while preserving canonical auditability.

## Amount source vocabulary

Future serving-unit logging should use a constrained backend-owned amount source vocabulary.

Recommended canonical values:

- `weighed_grams`
- `grams_entered`
- `serving_unit_estimate`
- `package_label`
- `user_saved_serving`
- `copied_previous_entry`
- `unknown`

For the first serving-unit logging backend milestone, all entries created through the serving-unit endpoint should use:

- `serving_unit_estimate`

The client should not be allowed to submit arbitrary `amount_source` values in v1. Backend should derive this from the logging path.

## Confidence vocabulary

Serving-unit row confidence should remain:

- `Low`
- `Moderate`
- `High`

`Medium` should continue to normalize to `Moderate` as already established in the serving-unit service.

The broader project confidence vocabulary remains:

- `Limited`
- `Low`
- `Moderate`
- `High`

Recommended distinction:

- serving-unit metadata confidence uses `Low` / `Moderate` / `High`;
- actuals/logging confidence may later use `Limited` / `Low` / `Moderate` / `High`;
- missing/incomplete data should become `Limited` at the actuals-confidence layer, not a valid serving-unit row confidence.

## Endpoint options considered

### Option A: Extend `POST /nutrition/log`

This would let `/nutrition/log` accept either `food_id + grams` or `canonical_food_id + serving_unit_id + quantity`.

Advantages:

- fewer endpoints;
- single nutrition logging route.

Disadvantages:

- ambiguous request semantics;
- increases risk of breaking legacy grams logging;
- requires request branching in an already simple route;
- makes Streamlit integration easier to get wrong;
- blurs legacy, canonical grams, and serving-unit estimate behavior.

Decision: not preferred for v1.

### Option B: Extend `POST /nutrition/{user_id}/log-canonical`

This would add optional `serving_unit_id` and `quantity` fields to canonical grams logging.

Advantages:

- canonical path already exists;
- less legacy route disruption.

Disadvantages:

- mixes canonical grams-entered behavior with serving-unit-estimate behavior;
- creates confusion around `grams` versus serving quantity;
- may tempt UI to send both grams and serving-unit fields.

Decision: acceptable only if Architecture rejects a new endpoint, but not preferred.

### Option C: Add dedicated `POST /nutrition/{user_id}/log-serving`

This route would accept only canonical food + backend-approved serving unit + serving quantity.

Advantages:

- clear route semantics;
- isolated validation;
- lower risk to existing grams logging;
- clear amount-source derivation;
- easier tests;
- safer Streamlit contract.

Disadvantages:

- one more route to maintain;
- history display must reconcile multiple logging paths.

Decision: preferred v1 direction.

## Recommended future endpoint contract

Recommended endpoint:

```text
POST /nutrition/{user_id}/log-serving
```

Recommended request body:

```json
{
  "canonical_food_id": 1,
  "serving_unit_id": 10,
  "serving_quantity": 1.0,
  "entry_date": "2026-06-26"
}
```

Fields:

- `canonical_food_id`: required; must reference an active canonical food.
- `serving_unit_id`: required; must reference an active serving unit for that canonical food.
- `serving_quantity`: required; positive number.
- `entry_date`: optional; valid `YYYY-MM-DD`; defaults to current local app date if omitted, consistent with existing logging conventions.

Do not allow `grams` override in v1.

Do not allow caller-supplied `amount_source` in v1.

Do not allow caller-supplied confidence in v1.

Do not allow free-text serving-unit name matching in v1.

## Recommended future response contract

Recommended public-safe response:

```json
{
  "success": true,
  "user_id": 1,
  "logged_food_entry_id": 123,
  "canonical_food_id": 45,
  "serving_unit_id": 67,
  "display_name": "Egg, Large",
  "serving_display": "1 large egg",
  "serving_quantity": 1.0,
  "resolved_grams": 50.0,
  "grams_min": 45.0,
  "grams_max": 55.0,
  "confidence": "High",
  "amount_source": "serving_unit_estimate",
  "logged_date": "2026-06-26",
  "nutrient_summary": {
    "calories": 143.0,
    "protein_g": 12.6,
    "carbohydrates_g": 0.7,
    "fat_g": 9.5
  }
}
```

Response rules:

- expose only public-safe fields;
- do not expose raw source payloads;
- do not expose provider/debug metadata;
- return nutrient summary only from canonical/backend-owned nutrient data;
- do not invent missing nutrient values;
- do not convert missing nutrients to zero.

## Backend resolution flow

Future serving-unit logging service should follow this order:

1. Validate request path/user context.
2. Validate `canonical_food_id` exists and is active.
3. Validate `serving_unit_id` exists and is active.
4. Validate the serving unit belongs to the canonical food.
5. Validate `serving_quantity` is positive.
6. Resolve grams using serving-unit metadata:
   - `resolved_grams = serving_quantity * grams_default / unit_quantity`
   - `grams_min = serving_quantity * grams_min / unit_quantity` when present
   - `grams_max = serving_quantity * grams_max / unit_quantity` when present
7. Validate resolved grams and ranges are positive and internally consistent.
8. Verify canonical nutrient data is usable.
9. Create or use the canonical write-through legacy food/nutrient row as current canonical logging does.
10. Insert `food_entries` with resolved grams.
11. Insert serving-unit provenance metadata in the companion table.
12. Return public-safe response.

Implementation should be transactional where possible so the `food_entries` row and companion metadata row cannot drift apart.

## Validation requirements

Future backend implementation must reject or safely fail when:

- canonical food does not exist;
- canonical food is inactive;
- serving unit does not exist;
- serving unit is inactive;
- serving unit belongs to a different canonical food;
- serving quantity is missing, zero, negative, non-numeric, or not finite;
- resolved grams is zero/negative/not finite;
- gram range is internally inconsistent;
- entry date is invalid;
- canonical nutrient data is unavailable or insufficient for safe actuals;
- caller tries to supply grams override;
- caller tries to supply confidence or amount source;
- caller tries to log by free-text serving unit name.

Errors should be public-safe and should not expose raw database internals.

## Missing nutrients behavior

Missing nutrient values must remain missing/unknown.

They must not become zero.

Recommended v1 behavior:

- reject serving-unit logging if canonical food has no usable canonical nutrient rows;
- allow partial optional nutrients to remain missing when core macro data is sufficient;
- preserve existing Target-vs-Actual missing-nutrient behavior;
- do not produce confident macro claims from incomplete data.

If a future milestone allows logging entries with limited nutrients, it must explicitly define how those entries affect nutrition actuals confidence.

## Target-vs-Actual behavior

Target-vs-Actual should not change immediately.

Future serving-unit logs should enter Target-vs-Actual as grams-based entries because the backend resolves the serving quantity before writing the log.

Target-vs-Actual should continue to calculate actuals from:

- `food_entries.grams`
- nutrient-per-100g rows

Serving-unit provenance should be available for history/debug/future confidence display, but Target-vs-Actual math does not need to consume the provenance table in v1.

## Actuals confidence follow-up

Serving-unit logging should eventually affect actuals confidence, but not inside the first serving-unit logging implementation unless separately authorized.

Recommended later milestone:

Nutrition Actuals Confidence Model v1

That milestone should define:

- how weighed grams differ from serving-unit estimates;
- how gram ranges affect displayed confidence;
- how mixed exact/estimated entries affect daily confidence;
- how history displays estimated entries;
- how Daily Coach, reports, and provider contexts may summarize confidence.

## User overrides

User-defined serving overrides are not recommended for v1.

Reasons:

- overrides require user-specific persistence;
- overrides require validation and edit/delete flows;
- overrides create trust/source questions;
- overrides complicate actuals confidence and historical reproducibility.

The future table can leave room for `user_saved_serving` amount source later, but v1 should only log backend-approved serving units.

## History and display behavior

Future history display should show both the original serving intent and backend-resolved grams.

Example display:

```text
Egg, Large — 1 large egg (~50g, High confidence)
```

For ranged estimates:

```text
Banana — 1 medium banana (~118g, range 100g-136g, Moderate confidence)
```

History should not imply exact certainty for estimates.

History should not imply user failure or poor adherence when an entry is estimated.

## Streamlit contract

Future Streamlit UI should:

- search/select canonical foods through backend-approved canonical search;
- fetch active serving units from backend for the selected canonical food;
- show only backend-provided serving labels, gram estimates, ranges, and confidence;
- submit `canonical_food_id`, `serving_unit_id`, and `serving_quantity`;
- render the backend response;
- avoid deriving grams client-side;
- avoid mapping canonical foods to legacy foods client-side;
- avoid free-text serving unit matching in v1;
- avoid grams override for serving-unit logging in v1.

Streamlit must not invent serving mappings.

## AI/provider boundary

Serving-unit internals should not enter AI/provider context immediately.

Provider may eventually see only approved summaries after logging and actuals confidence are stable.

Allowed future provider summary examples:

- `Logged serving estimate: 1 large egg, about 50g, High confidence.`
- `Daily nutrition actuals include some estimated serving-unit entries.`
- `Actuals confidence is Moderate because some entries were household-measure estimates.`

Provider must not:

- invent serving units;
- infer grams from free text;
- convert units to grams;
- invent macros;
- invent targets;
- treat missing logs as zero intake;
- treat estimate ranges as exact physiological certainty;
- bypass backend validation;
- render raw provenance/debug internals.

## Future implementation sequence

Recommended sequence after Architecture accepts this contract:

1. Nutrition Serving Unit Logging Backend v1
   - add endpoint/service;
   - resolve serving units to grams;
   - persist companion provenance;
   - preserve Target-vs-Actual behavior;
   - no Streamlit change yet.

2. Nutrition Actuals Confidence Model v1
   - classify weighed/grams-entered/serving-estimated entries;
   - summarize confidence safely;
   - define allowed display language.

3. Streamlit Serving Unit Logging UI v1
   - user selects backend-approved serving units;
   - backend resolves/logs;
   - UI renders response only.

4. Target-vs-Actual Confidence Display v1
   - show estimated vs weighed entries safely;
   - avoid false precision.

5. Nutrition Food Suggestions Serving-Aware v1
   - use serving units only after logging and confidence are stable.

## Future backend acceptance criteria

A future Nutrition Serving Unit Logging Backend v1 should prove:

- canonical food serving-unit entries can be logged;
- inactive canonical foods cannot be logged;
- inactive serving units cannot be logged;
- serving unit must belong to canonical food;
- serving quantity must be positive;
- resolved grams are persisted in `food_entries`;
- provenance metadata is persisted and tied to the entry;
- gram range and confidence are copied at log time;
- existing raw/legacy grams logging remains stable;
- existing canonical grams logging remains stable;
- Target-vs-Actual reflects serving-unit logs through resolved grams;
- missing nutrients remain missing/unknown;
- no raw source payloads are exposed;
- normal public responses remain safe;
- no provider/Ollama/CrewAI path is involved;
- tests do not call live providers;
- full scoped pytest passes.

## Open Architecture questions

1. Should the companion table be named `nutrition_serving_unit_log_metadata` or `food_entry_serving_unit_metadata`?
2. Should future backend implementation reject all canonical foods without complete core macros, or allow partial optional nutrient gaps?
3. Should `entry_date` default behavior exactly mirror current canonical logging behavior?
4. Should meal type/grouping be deferred until after serving-unit logging, or included in a broader nutrition logging v2?
5. Should serving-unit history display be added with the Streamlit UI milestone or with the backend logging milestone through API response only?
6. Should Nutrition Actuals Confidence Model v1 happen immediately after backend logging, before UI?

## Final design status

Recommended final status after Architecture review:

`NUTRITION_SERVING_UNIT_LOGGING_CONTRACT_DESIGN_V1_ACCEPTED`
