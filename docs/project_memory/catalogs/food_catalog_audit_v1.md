# Food Catalog Audit v1

Last updated: 2026-06-18

## Status

`FOOD_CATALOG_EXPANSION_V1_IMPLEMENTED_PENDING_QA`

This is a planning audit only. It does not add foods, change nutrition target formulas, change provider behavior, or approve public nutrition claims.

## Current inventory

The app currently has a curated starter canonical food catalog seeded through `services/food_normalization_service.py` and `scripts/seed_canonical_foods.py`.

Current starter count after Food Catalog Expansion v1:

- canonical starter foods: 202
- added in Food Catalog Expansion v1: 70
- food types represented:
  - generic: 88
  - cooked: 57
  - prepared: 41
  - raw: 16

Current canonical food infrastructure includes:

- `canonical_foods`
- `canonical_food_aliases`
- `canonical_food_nutrients`
- `food_source_links`
- `raw_food_source_records`

Current app-facing model fields include:

- `display_name`
- `normalized_name`
- `food_type`
- `default_unit`
- `default_grams`
- `search_priority`
- `active`
- `notes`
- aliases
- nutrients per 100g
- nutrient unit
- source policy
- confidence

## Current strengths

- The catalog is backend-owned and deterministic.
- Canonical food search already exists.
- Aliases reduce logging friction.
- Nutrients are stored per 100g, which supports gram-based logging and target-vs-actual calculations.
- Nutrient confidence/source policy already exists, so uncertain entries can remain bounded.
- The starter catalog already includes many common proteins, dairy items, grains/starches, fruits, vegetables, fats, and prepared/simple items.

## Current gaps

The current catalog is useful for seed flows but should be curated for daily real-world logging.

Likely gaps to review before Food Catalog Expansion v1:

- Not enough explicitly grouped everyday foods by meal/snack context.
- Limited convenience foods that users actually log often.
- Limited common mixed foods where macros are defensible.
- Limited serving defaults for quick logging.
- Limited category taxonomy beyond `food_type`.
- Sodium/fiber fields exist only as optional nutrient names, not a first-class planning commitment.
- No documented duplicate policy for similar cooked/raw/prepared variants.
- No documented rule for when brand-like or prepared foods are allowed.
- No formal curation checklist for source confidence and serving assumptions.

## Proposed target food catalog categories

Food Catalog Expansion v1 should add curated entries in these practical groups:

1. Lean proteins
   - cooked/raw poultry variants where defensible
   - lean beef/pork options
   - fish/seafood
   - canned protein options

2. Eggs and dairy
   - eggs/egg whites
   - Greek yogurt/cottage cheese
   - milk variants
   - common cheeses where useful

3. Grains and starches
   - rice variants
   - potatoes/sweet potatoes
   - oats
   - pasta
   - bread/tortilla options when macros are defensible

4. Fruits
   - bananas
   - apples
   - berries
   - oranges
   - other common quick-log fruits

5. Vegetables
   - leafy greens
   - broccoli/cauliflower
   - carrots
   - peppers/onions
   - mixed vegetables when macros are defensible

6. Fats
   - olive oil
   - avocado
   - peanut butter
   - nuts/seeds in simple forms

7. Snacks and convenience foods
   - simple foods the user is likely to log often
   - only include entries with defensible macro data
   - avoid pretending brand-specific precision when not sourced

8. Common mixed foods, limited
   - only when nutrition values are stable enough
   - must be marked with lower confidence if broad/generic
   - no meal-planning behavior in v1

## Recommended fields for Food Catalog Expansion v1

The current schema is close but the planning target should explicitly track:

- `canonical_food_id`
- `display_name`
- `category`
- `food_type`
- `serving_basis`
- `default_grams`
- `calories_per_100g`
- `protein_per_100g`
- `carbs_per_100g`
- `fat_per_100g`
- `fiber_per_100g` optional
- `sodium_mg_per_100g` optional
- `aliases`
- `source_type`
- `confidence_level`
- `notes`

Implementation can map these to existing canonical food tables first. A schema migration should be deferred unless the implementation review shows the existing tables cannot represent the needed data safely.

## Curation rules

A food qualifies as canonical only when:

- the display name clearly identifies preparation state or food type
- per-100g calories/protein/carbs/fat are defensible
- serving assumptions are explicit
- aliases do not create ambiguous matches with materially different foods
- cooked/raw/prepared variants are separate when nutrition differs materially
- confidence is set honestly
- broad/generic prepared foods are not over-claimed as precise

Duplicates should be avoided by:

- normalized name checks
- explicit cooked/raw/prepared variant naming
- alias review
- search priority review

Uncertain nutrition data should be handled by:

- lower confidence
- notes
- source policy
- excluding the item if it would create false precision

## Non-goals

Do not add:

- unreviewed food dumps
- scraping
- RAG/embeddings
- AI-generated production entries
- meal plans
- clinical nutrition claims
- unverified brand-specific claims
- supplements as recommendations

## Recommended first implementation slice

`Food Catalog Expansion v1`

Reason:
The Daily Next Action Panel often asks the user to log food. Better canonical foods will immediately improve the usefulness of that action.

Expected Food Catalog Expansion v1 should be a curated, reviewed seed expansion with tests around search, aliases, nutrient completeness, and duplicate prevention.


## Food Catalog Expansion v1 implementation summary

Food Catalog Expansion v1 adds 70 curated canonical food entries across practical daily logging categories:

- lean proteins and seafood
- eggs and dairy
- grains and starches
- legumes
- fruits
- vegetables
- fats, nuts, and seeds
- simple convenience foods and sauces

The implementation intentionally keeps the current schema and curation model:

- nutrients are stored per 100g
- required macro nutrients remain Calories, Protein, Carbohydrate, and Fat
- source policy remains `manually_curated` for seeded entries
- confidence remains `Moderate` for seeded entries
- default unit remains grams
- default grams remain 100g
- aliases are explicit and reviewable

The implementation does not add meal planning, brand-heavy foods, scraping, RAG, embeddings, AI-generated production entries, nutrition target formula changes, provider/report behavior changes, or Streamlit UI changes.

## Food Catalog Expansion v1 QA focus

QA should verify:

- starter seed count is 202
- canonical seed remains idempotent
- new foods are searchable by useful aliases
- new foods can be logged by canonical food id
- calories/protein/carbs/fat are present and non-negative
- macro values remain within sane per-100g ranges
- Nutrition Target Display still reflects logged canonical foods
- Daily Next Action Panel remains functional
- provider/report semantics remain unchanged
