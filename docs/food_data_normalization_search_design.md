# Food Data Normalization/Search Design v1

## Status

Design milestone for Architecture review. No implementation is included in this milestone.

This document defines how the nutrition data layer should preserve raw USDA/source food records while presenting cleaner, app-approved food choices for normal daily logging.

## Purpose

Raw USDA and source food data is valuable, but it is not automatically usable as a daily food picker. Imported source rows can be highly duplicated, overly specific, branded, acquisition-sample oriented, or written in source-database language that is frustrating for normal users.

The goal of this design is to separate source preservation from user-facing food selection:

```text
Raw USDA/source food records
→ normalized source records
→ canonical app foods
→ aliases/search terms
→ user-facing food picker
→ logged food entries
→ verified nutrient actuals
→ Target-vs-Actual
```

The user should normally search and select canonical app foods first, such as:

- Chicken Breast, Cooked, Skinless
- Chicken Breast, Raw, Skinless
- White Rice, Cooked
- Egg, Large
- Ground Beef, 90/10

Raw source records should remain available for provenance, nutrient verification, debugging, and advanced/source-detail views, but should not dominate the default food search experience.

## Core principle

Raw food source data should be preserved.

Normal users should search/select app-approved canonical foods first. Raw source records should remain available only as advanced/developer/source detail when needed.

The system may show:

> Chicken Breast, Cooked, Skinless

It should not force the user to choose from many near-duplicate source rows such as sample/acquisition/sub-sample variants unless they explicitly open source details.

## Current baseline

The current app has a simple food logging structure:

- `foods`
- `nutrients`
- `food_nutrients`
- `food_entries`

The current search path is simple name matching over `foods.name`. This is appropriate for a small hand-curated food list, but it does not scale well when raw USDA/source records are imported directly.

The current imported source files under `data/` contain raw USDA-style source records and nutrient tables. These should be treated as source material, not automatically as app-facing picker rows.

## Design goals

1. Preserve raw USDA/source records and source metadata.
2. Create app-facing canonical foods for daily logging.
3. Search canonical foods first by default.
4. Keep raw/source records available behind advanced/source detail.
5. Group duplicate-looking source rows behind canonical foods.
6. Preserve nutrient provenance for verification and future debugging.
7. Support aliases and common search terms.
8. Prioritize common foods over obscure source rows.
9. Keep grams-first logging stable for v1.
10. Avoid fake serving-size certainty.
11. Avoid barcode scanning, meal planning, and AI food selection in v1.

## Non-goals

This design does not implement:

- new USDA import
- barcode scanning
- Open Food Facts import
- AI food selection
- AI meal planning
- meal template generation
- Streamlit changes
- Target-vs-Actual changes
- DailyCoachSynthesis changes
- report changes
- workout changes
- CrewAI/Ollama paths
- automatic serving-size inference
- branded/package food workflows

## Proposed data model

The preferred long-term design is separate tables for raw source data and app-facing canonical foods.

```text
raw_food_source_records
canonical_foods
canonical_food_aliases
canonical_food_nutrients
food_source_links
```

This keeps source preservation, canonical display, alias/search, nutrient values, and provenance separate.

### `raw_food_source_records`

Stores imported source food rows exactly enough to audit where data came from.

Suggested fields:

- `id`
- `source_name`
- `source_record_id`
- `source_url`
- `license`
- `imported_at`
- `source_data_type`
- `source_category`
- `raw_description`
- `raw_payload_json`
- `normalized_description`
- `canonical_food_id`
- `created_at`
- `updated_at`

Field notes:

- `source_name` might be `USDA FoodData Central`, `manual`, or a future importer.
- `source_record_id` should preserve values such as USDA `fdc_id`.
- `raw_description` should preserve the original source wording.
- `normalized_description` may support matching/grouping but should not overwrite the source description.
- `canonical_food_id` is optional because not every source row needs to be canonicalized immediately.
- `raw_payload_json` is optional but useful when source-specific metadata does not fit the app schema yet.

### `canonical_foods`

Stores user-facing app foods.

Suggested fields:

- `id`
- `display_name`
- `food_family`
- `food_form`
- `preparation_state`
- `brand_type`
- `default_serving_basis`
- `search_priority`
- `is_active`
- `review_status`
- `confidence`
- `reason_codes`
- `limitations`
- `created_at`
- `updated_at`

Suggested values:

`food_form` examples:

- `whole_food`
- `ingredient`
- `prepared_food`
- `branded_food`
- `recipe`

`preparation_state` examples:

- `raw`
- `cooked`
- `roasted`
- `grilled`
- `boiled`
- `dry`
- `prepared`
- `unknown`

`brand_type` examples:

- `generic`
- `branded`
- `restaurant`
- `unknown`

`review_status` examples:

- `approved`
- `needs_review`
- `source_only`
- `deprecated`

`confidence` examples:

- `Limited`
- `Low`
- `Moderate`
- `High`

### `canonical_food_aliases`

Stores searchable aliases and common user terms.

Suggested fields:

- `id`
- `canonical_food_id`
- `alias`
- `normalized_alias`
- `alias_type`
- `search_weight`
- `created_at`
- `updated_at`

Alias examples:

| Canonical food | Example aliases |
| --- | --- |
| Chicken Breast, Cooked, Skinless | chicken breast, boneless chicken, cooked chicken, grilled chicken breast |
| Chicken Breast, Raw, Skinless | raw chicken breast, uncooked chicken breast |
| White Rice, Cooked | white rice, cooked rice, rice |
| Egg, Large | egg, large egg, eggs |
| Ground Beef, 90/10 | ground beef, lean ground beef, 90/10 beef |

`alias_type` examples:

- `common_name`
- `ingredient_name`
- `alternate_spelling`
- `brand_alias`
- `preparation_alias`
- `source_synonym`

### `canonical_food_nutrients`

Stores app-approved nutrient values for canonical foods.

Suggested fields:

- `id`
- `canonical_food_id`
- `nutrient_name`
- `unit`
- `amount_per_100g`
- `data_basis`
- `confidence`
- `source_link_id`
- `created_at`
- `updated_at`

Field notes:

- `amount_per_100g` should remain the v1 normalized nutrient basis.
- `data_basis` can describe how the value was selected, such as `single_source_record`, `averaged_sources`, `manual_review`, or `future_labelling_source`.
- Missing nutrients should remain missing. They should not be coerced to zero.
- Canonical nutrients should be app-approved before they affect Target-vs-Actual actuals.

### `food_source_links`

Links canonical foods to one or more source records used to establish provenance.

Suggested fields:

- `id`
- `canonical_food_id`
- `raw_food_source_record_id`
- `link_type`
- `is_primary_source`
- `source_weight`
- `notes`
- `created_at`
- `updated_at`

`link_type` examples:

- `primary_nutrient_source`
- `supporting_source`
- `duplicate_group_member`
- `excluded_source`
- `needs_review`

This lets the app say: the canonical food is user-facing, but its nutrient facts came from these preserved source records.

## Simpler v1 alternative

If the separate-table design is too much for the next implementation, a simpler v1 can extend the current `foods` table while still preserving the main architectural boundary.

Potential fields on `foods`:

- `source_type`: `raw_usda` | `canonical` | `manual`
- `canonical_food_id`
- `search_priority`
- `display_name`
- `raw_source_name`
- `source_record_id`
- `raw_description`
- `review_status`

This is easier to implement but less clean long term. The separate-table design is preferred because it avoids overloading `foods` with both source and app-facing responsibilities.

## Canonicalization strategy

Canonicalization should transform messy source descriptions into stable app-facing food concepts without deleting the raw data.

### Grouping rules

Duplicate-looking source records may be grouped when they represent the same practical logging choice.

Examples:

- multiple `HUMMUS, SABRA CLASSIC` acquisition/sample rows may group behind a single source-detail cluster, not many default picker rows
- multiple raw chicken breast entries may link to `Chicken Breast, Raw, Skinless`
- multiple cooked chicken breast entries may link to `Chicken Breast, Cooked, Skinless`
- white rice source variants may separate into `White Rice, Cooked` and `White Rice, Dry` if nutrient basis differs materially

Grouping should consider:

- food family
- preparation state
- raw vs cooked state
- fat percentage or lean ratio
- brand/generic distinction
- nutrient profile similarity
- source category
- data type/source quality

### Raw vs cooked vs prepared vs branded

The app should not collapse nutritionally different foods into one canonical row.

Keep separate canonical foods for:

- raw vs cooked meats
- dry vs cooked grains
- lean-ratio differences in ground meat
- plain ingredient vs prepared dish
- generic food vs branded/package food when nutrient values differ materially

Examples:

- `Chicken Breast, Raw, Skinless`
- `Chicken Breast, Cooked, Skinless`
- `White Rice, Dry`
- `White Rice, Cooked`
- `Ground Beef, 90/10`
- `Ground Beef, 80/20`
- `Greek Yogurt, Plain, Nonfat`
- `Greek Yogurt, Plain, 2%`

Branded/package foods should likely be a later lane unless the product specifically needs brand matching. Branded foods can be preserved as raw/source results first and promoted to canonical only after review.

## User-facing display names

Display names should be short, title-cased, and useful for logging.

Recommended pattern:

```text
Food Family, Preparation/State, Key Modifier
```

Examples:

- `Chicken Breast, Cooked, Skinless`
- `Chicken Breast, Raw, Skinless`
- `White Rice, Cooked`
- `Egg, Large`
- `Ground Beef, 90/10`
- `Oats, Dry, Rolled`
- `Greek Yogurt, Plain, Nonfat`
- `Banana, Raw`
- `Potato, Baked`

Avoid raw source formatting such as all-caps names, source acquisition language, unusual punctuation, and overly long descriptions in the default picker.

## Search behavior

Default search should prioritize canonical foods.

Recommended search tiers:

1. exact canonical display-name match
2. exact alias match
3. prefix canonical or alias match
4. token match across canonical display name and aliases
5. higher-priority common foods
6. source-backed canonical foods with higher confidence
7. advanced/source results only when explicitly requested

Default search should not return raw USDA/source rows unless:

- no useful canonical foods match, or
- the user enables `show source results`, or
- the UI is in developer/advanced mode

### Search ranking inputs

Potential ranking features:

- exact match score
- alias match score
- token coverage
- `search_priority`
- `review_status`
- canonical confidence
- source confidence
- common-food boost
- preparation-state match
- brand/generic match
- recent user selection history later
- user favorites later

### Example search expectations

Query: `chicken breast`

Top results should look like:

1. `Chicken Breast, Cooked, Skinless`
2. `Chicken Breast, Raw, Skinless`
3. `Chicken Breast, Cooked, With Skin` if supported
4. source results only behind advanced details

Query: `rice`

Top results should look like:

1. `White Rice, Cooked`
2. `Brown Rice, Cooked`
3. `White Rice, Dry`
4. `Brown Rice, Dry`

Query: `egg`

Top results should look like:

1. `Egg, Large`
2. `Egg Whites`
3. `Egg, Whole, Raw` if needed as a source-backed detail

## Source detail behavior

Canonical food responses may include bounded source-detail metadata for developer or advanced inspection.

User-facing result:

```json
{
  "id": 1,
  "display_name": "Chicken Breast, Cooked, Skinless",
  "serving_basis": "per_100g",
  "confidence": "Moderate"
}
```

Advanced/source detail may include:

```json
{
  "source_name": "USDA FoodData Central",
  "source_record_id": "...",
  "license": "...",
  "imported_at": "...",
  "raw_description": "...",
  "source_link_type": "primary_nutrient_source"
}
```

Public food search should not dump raw rows, raw SQL, full source payloads, or debug metadata by default.

## Nutrient actuals relationship

Canonical foods should feed logged actuals only through app-approved nutrient values.

Suggested future logging flow:

```text
canonical_food_id + grams
→ canonical_food_nutrients amount_per_100g
→ logged actuals
→ NutritionActuals
→ TargetVsActualNutritionSummary
```

Rules:

- actuals come from verified/app-approved nutrient data, not AI estimates
- missing nutrient fields remain missing, not zero
- grams remains the v1 basis
- common serving units can be layered later
- raw source nutrient values should not bypass canonical approval into user-facing actuals

## Serving units strategy

V1 should stay grams-first.

This is less convenient than household servings, but safer and clearer while normalization is being designed.

Later serving units may include:

- `large egg`
- `medium banana`
- `cup cooked rice`
- `slice bread`
- `oz cooked meat`

Future serving-unit rules:

- serving units must be source-backed or app-reviewed
- serving conversions should record basis and confidence
- serving-size uncertainty should be displayed as a limitation
- do not invent household serving conversions from AI
- grams should always remain available

## Recommended API direction

This milestone is design-only, but future API shape should separate canonical search from source inspection.

Possible future endpoints:

```text
GET /foods/search?query=chicken&source_mode=canonical
GET /foods/{canonical_food_id}
GET /foods/{canonical_food_id}/source-links
GET /foods/source-records/search?query=chicken
```

Recommended default:

- `source_mode=canonical`
- raw/source results hidden unless explicitly requested

Do not change existing `/foods/search` until the schema/search design is accepted and an implementation milestone is opened.

## Migration strategy

Recommended staged implementation after this design is accepted:

1. Add food normalization schema.
2. Add small canonical-food seed set for common foods.
3. Add alias seed data for common searches.
4. Add canonical food search service.
5. Keep existing food logging working.
6. Add optional mapping from canonical foods to existing `foods` / nutrient values.
7. Add advanced/source detail endpoint only after canonical search is stable.
8. Migrate Streamlit food picker to canonical search.
9. Later, add source-record import/normalization tools.

Do not import more USDA data until the normalization/search strategy is accepted.

## Initial canonical seed recommendation

A small manual seed set is likely more useful than a large raw import.

Suggested initial categories:

- proteins: chicken breast, ground beef, turkey, eggs, Greek yogurt, tuna, salmon
- carbs: white rice, brown rice, oats, potatoes, sweet potatoes, pasta, bread
- fats: olive oil, peanut butter, avocado, butter
- fruits: banana, apple, berries
- vegetables: broccoli, spinach, mixed vegetables, carrots
- staples: milk, cottage cheese, beans

Each canonical food should have:

- clear display name
- aliases
- per-100g macro nutrients at minimum
- source link or manual-review note
- confidence
- limitations when needed

## Validation expectations for future implementation

Future implementation should add tests for:

1. canonical foods search before raw source records
2. aliases resolve common terms such as `chicken breast`, `egg`, and `white rice`
3. duplicate raw source records can link to one canonical food
4. raw descriptions are preserved
5. source metadata is preserved
6. canonical display names are clean and title-cased
7. source records are hidden from default search
8. source records can be returned only through explicit advanced/source query
9. raw vs cooked foods remain separate canonical foods
10. dry vs cooked grains remain separate canonical foods
11. branded/source rows do not dominate generic common food search
12. missing nutrient values remain missing, not zero
13. grams-first logging remains stable
14. existing food logging remains stable until intentionally migrated
15. Target-vs-Actual behavior remains stable
16. DailyCoachSynthesis remains stable
17. no AI/CrewAI/Ollama calls occur in food search tests

## Safety and language rules

Food search and normalization should not produce coaching claims.

Search may say:

> Showing canonical foods first. Source records are available in details.

It should not say:

> This is the best food for fat loss.

Forbidden in food search/normalization:

- medical/disease claims
- supplement assumptions
- shame or moralizing language
- eating-disorder-style restriction language
- AI-generated nutrient values
- unsupported serving-size certainty
- unsupported fat-loss or workout-performance claims

## Architecture decision requested

Architecture should decide whether the next implementation should use:

1. the preferred separate-table design, or
2. the simpler v1 extension to the current `foods` table.

Recommendation: use the separate-table design if the next step is a durable food data layer. Use the simpler `foods` extension only if the goal is a very small interim UX improvement.

## Recommended next milestone if accepted

Food Data Normalization Schema v1.

Suggested scope:

- add raw/canonical food schema
- add canonical aliases schema
- add source-link schema
- seed a small canonical common-food set
- add service-level tests only
- no Streamlit changes yet
- no Target-vs-Actual changes yet
- no new USDA import yet
