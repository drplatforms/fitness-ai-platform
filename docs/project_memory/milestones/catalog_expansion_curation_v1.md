# Catalog Expansion & Curation v1

Status: PLANNED / PENDING ARCHITECTURE ACCEPTANCE

Planning status: `CATALOG_EXPANSION_CURATION_V1_PLAN_ACCEPTED`

## Goal

Design a structured, deterministic expansion plan for the food and exercise catalogs so AI Health Coach becomes more useful for real daily use.

This is a planning milestone only. It does not implement catalog expansion.

## Product reason

Daily Next Action Panel v1 now tells the user what to do next.

The next product-quality bottleneck is whether the user can easily do it:

- If Today says “Log a meal or snack,” food logging needs enough useful canonical foods.
- If Today says “Review today’s workout,” the exercise catalog needs enough variety, equipment matching, movement patterns, substitutions, and recovery-aware options.

Catalog depth is not side polish. Catalog depth is daily usability.

## Current inventory summary

Food catalog:

- 132 starter canonical foods observed in the code snapshot
- existing canonical food tables support display names, aliases, food types, default grams, nutrients per 100g, source policy, confidence, and notes
- current catalog is deterministic and curated, but needs daily-use category coverage and curation rules

Exercise catalog:

- 178 curated exercise entries observed in the code snapshot
- current coverage includes strength, core, conditioning, and limited mobility
- strong home-gym equipment coverage already exists
- gaps remain around recovery suitability, joint stress, explicit substitution groups, setup/safety notes, and mobility/recovery depth

Detailed audits:

- `docs/project_memory/catalogs/food_catalog_audit_v1.md`
- `docs/project_memory/catalogs/exercise_catalog_audit_v1.md`

## Target food catalog shape

Food Catalog Expansion v1 should focus on practical daily logging across:

- lean proteins
- eggs and dairy
- grains and starches
- fruits
- vegetables
- fats
- snacks and convenience foods
- limited common mixed foods only when macros are defensible

Recommended food fields:

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

## Target exercise catalog shape

Exercise Catalog Expansion v1 should focus on variety, equipment fit, and safer substitutions across:

- dumbbell movements
- barbell/rack/plate movements
- EZ bar movements
- cable system movements
- bodyweight movements
- band movements
- treadmill/bike conditioning
- mobility/recovery movements

Recommended exercise fields:

- `exercise_id`
- `display_name`
- `movement_pattern`
- `primary_muscles`
- `secondary_muscles`
- `equipment_required`
- `difficulty`
- `joint_stress`
- `recovery_suitability`
- `progression_type`
- `substitution_group`
- `setup_notes`
- `safety_notes`

## Curation rules

Catalog entries must remain:

- deterministic
- backend-owned
- inspectable
- testable
- source/confidence-aware
- free of AI-generated production entries
- free of unsupported nutrition or exercise claims

Food curation rules:

- display name must identify preparation state or food type when relevant
- per-100g macro data must be defensible
- serving assumptions must be explicit
- aliases must not hide materially different foods
- cooked/raw/prepared variants must be separate when nutrition differs materially
- confidence and notes must be honest
- broad/generic prepared foods must not be over-claimed as precise

Exercise curation rules:

- display name must be clear and non-duplicative
- movement pattern and required equipment must be accurate
- primary muscles must be conservative
- difficulty must be reasonable
- high joint-stress or advanced options must not be surfaced as default recovery-limited choices
- substitution group should be clear enough for deterministic alternatives
- setup/safety notes should exist where execution risk is non-obvious

## Recommended implementation phases

1. Catalog audit and schema review.
2. Food Catalog Expansion v1.
3. Exercise Catalog Expansion v1.
4. Logging and workout generation integration tests.
5. UX improvements that use expanded catalogs.

## Recommended first implementation slice

`Food Catalog Expansion v1`

Reason:
Daily Next Action Panel v1 often routes users to food logging. Improving the canonical food catalog will make that action immediately more useful.

Food Catalog Expansion v1 should add a curated set of common foods, aliases, per-100g nutrients, default grams where useful, confidence/source policy, and tests for search/logging behavior.

## Recommended second implementation slice

`Exercise Catalog Expansion v1`

Reason:
Workout variety and equipment-aware substitutions are the next daily-use bottleneck after food logging. This should be sequenced after food catalog expansion or planned as a separate implementation lane.

## Strict non-goals

Do not:

- add RAG
- add embeddings
- add scraping
- add agent orchestration
- let AI generate production catalog entries
- add meal planning
- add new provider behavior
- change Level 5 Training semantics
- change Level 5 Nutrition semantics
- make direct_ollama default
- use or promote qwen3
- loosen validators
- remove deterministic fallback
- change nutrition target formulas
- rewrite workout generation
- redesign Streamlit UI
- add a huge unreviewed food dump
- add unverified nutrition claims
- add clinical nutrition claims

## Expected next status

If accepted:

`CATALOG_EXPANSION_CURATION_V1_PLAN_ACCEPTED`

Recommended next milestone:

`Food Catalog Expansion v1`


## Food Catalog Expansion v1 implementation note

Architecture accepted this planning milestone and approved Food Catalog Expansion v1 as the first implementation slice. The first slice expands the starter canonical food catalog from 132 to 202 curated entries while preserving deterministic curation, per-100g nutrient storage, manually curated source policy, Moderate confidence, canonical aliases, and existing logging/search behavior.

Implementation status: `FOOD_CATALOG_EXPANSION_V1_IMPLEMENTED_PENDING_QA`.
