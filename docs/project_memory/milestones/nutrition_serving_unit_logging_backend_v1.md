# Nutrition Serving Unit Logging Backend v1

Status: backend implementation drafted / pending validation and Architecture review.

Branch: `feature/nutrition-serving-unit-logging-backend-v1`.

Source baseline: `main` at `d74ddec`.

Milestone type: backend implementation / service / endpoint / tests / project memory.

Commit-check mode: code.

## Goal

Implement backend-owned serving-unit logging for canonical foods.

The backend accepts:

```text
canonical_food_id + serving_unit_id + quantity
```

Then it validates ownership/active state, resolves quantity to grams, writes resolved grams through the existing `food_entries` actuals bridge, and preserves serving-unit provenance in a companion table.

## Implemented scope

- Added backend serving-unit logging service.
- Added companion metadata table: `nutrition_serving_unit_log_metadata`.
- Added endpoint: `POST /nutrition/{user_id}/log-serving`.
- Added public-safe response fields.
- Added service tests.
- Added API tests.
- Preserved existing canonical grams logging behavior.
- Preserved existing raw/source grams logging behavior.
- Preserved Target-vs-Actual behavior by writing resolved grams to `food_entries`.

## Contract preserved

Accepted path:

```text
serving-unit log
-> backend grams resolution
-> food_entries row with resolved grams
-> nutrition_serving_unit_log_metadata row with provenance
-> existing Target-vs-Actual actuals calculation
```

## Public-safe response fields

Expected response includes:

- `success`
- `user_id`
- `food_entry_id`
- `logged_food_entry_id`
- `canonical_food_id`
- `serving_unit_id`
- `display_name`
- `serving_quantity`
- `serving_display`
- `resolved_grams`
- `grams_min`
- `grams_max`
- `confidence`
- `amount_source`
- `logged_date`
- `metadata_id`
- `nutrient_summary` when available

The response does not expose raw source payloads, provider metadata, raw model output, or debug internals.

## Validation expectations

Focused tests cover:

- serving-unit quantity resolves to grams;
- serving-unit quantity resolves to gram ranges;
- decimal quantities are allowed;
- zero/negative quantities are rejected;
- missing serving unit is rejected;
- inactive serving unit is rejected;
- wrong-food serving unit is rejected;
- resolved grams are persisted to `food_entries`;
- serving-unit metadata is persisted;
- missing optional gram range values remain missing, not zero;
- missing optional nutrients remain missing, not zero;
- existing canonical grams logging remains stable;
- existing raw/source grams logging remains stable;
- Target-vs-Actual sees serving-unit logged foods.

## Strict non-goals preserved

This milestone does not add:

- Streamlit serving-unit UI;
- food picker changes;
- AI/provider serving-unit behavior;
- CrewAI/Ollama changes;
- Target-vs-Actual redesign;
- nutrition target formula changes;
- serving-aware food suggestions;
- meal planning;
- barcode scanning;
- USDA/Open Food Facts import;
- workout/recovery/report changes.

## Recommended next milestone after acceptance

Nutrition Actuals Confidence Model v1.

Purpose:

- model confidence/provenance for weighed grams vs entered grams vs serving-unit estimates;
- prepare Target-vs-Actual confidence display;
- unblock safe Streamlit Serving Unit Logging UI v1 later.
