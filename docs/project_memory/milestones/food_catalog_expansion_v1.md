# Food Catalog Expansion v1

Status: IMPLEMENTED / PENDING ARCHITECTURE + QA REVIEW

Implementation status: `FOOD_CATALOG_EXPANSION_V1_IMPLEMENTED_PENDING_QA`

## Goal

Expand the canonical food catalog in a deterministic, curated, inspectable way so daily food logging becomes more useful after Daily Next Action Panel v1 began routing users toward the food logging workflow.

## Implemented scope

Food Catalog Expansion v1 adds 70 curated canonical foods to the starter seed catalog.

Catalog size changed from:

- 132 starter canonical foods

to:

- 202 starter canonical foods

The expansion covers practical daily logging categories:

- lean proteins and seafood
- eggs and dairy
- grains and starches
- legumes
- fruits
- vegetables
- fats, nuts, and seeds
- simple convenience foods and sauces

## Curation rules preserved

Every added food uses the existing canonical seed structure:

- stable display name
- food type
- useful aliases
- search priority
- calories per 100g
- protein per 100g
- carbohydrate per 100g
- fat per 100g

The seeding path continues to store:

- default unit: grams
- default grams: 100g
- source policy: manually_curated
- confidence: Moderate
- notes: Canonical food for app-facing search

## Tests added or updated

Tests verify:

- starter seed count is at least 200
- seed remains idempotent
- new practical foods are searchable by useful aliases
- new foods include Calories, Protein, Carbohydrate, and Fat
- macro values are non-negative and within sane per-100g ranges
- a newly added canonical food can be logged and reflected in target-vs-actual actuals

## Boundaries preserved

This milestone does not change:

- nutrition target formulas
- provider/report semantics
- Level 5 Training semantics
- Level 5 Nutrition semantics
- Daily Next Action priority order
- Streamlit UI
- workout generation
- deterministic fallback
- provider gates
- validators

No RAG, embeddings, scraping, AI-generated production catalog entries, meal planning, clinical nutrition claims, or exercise catalog changes were added.

## Expected QA result

`FOOD_CATALOG_EXPANSION_V1_ACCEPTED`
