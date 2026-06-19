# Catalog Expansion & Curation v1 Planning Review

Status: PLAN_ACCEPTED / FOOD_CATALOG_EXPANSION_V1_IMPLEMENTED_PENDING_QA

Planning status: `CATALOG_EXPANSION_CURATION_V1_PLAN_ACCEPTED`

## Decision request

Review and accept the Catalog Expansion & Curation v1 plan.

## Why this is the correct next product milestone

Daily Next Action Panel v1 completed the first Daily Coaching Product Loop implementation slice. The product can now tell the user the next useful action.

The next premium-product gap is action completion quality:

- Food logging needs enough canonical foods to be practical.
- Workout planning needs enough exercise variety, equipment matching, substitution coverage, and recovery-aware tagging to feel personal and usable.

Catalog work should remain deterministic and curated rather than becoming an AI/RAG feature.

## Review findings

### Food catalog

The current food catalog has a solid deterministic foundation:

- 132 starter canonical foods
- aliases
- per-100g nutrients
- source policy
- confidence
- default grams
- canonical search support

Main planning gaps:

- category taxonomy should be made explicit
- daily logging foods should be expanded deliberately
- mixed/convenience foods need strict confidence rules
- duplicate/cooked/raw/prepared naming rules should be documented
- serving assumptions should be clear and testable

### Exercise catalog

The current exercise catalog is already meaningful:

- 178 curated entries
- strong home-gym equipment coverage
- movement patterns
- primary muscles
- difficulty
- substitution-compatible structure

Main planning gaps:

- mobility/recovery catalog is thin
- recovery suitability is not first-class
- joint stress is not first-class
- substitution groups are inferred rather than explicitly curated
- setup and safety notes are not first-class
- progression type is not first-class

## Recommendation

Accept the planning milestone and proceed first to:

`Food Catalog Expansion v1`

Reason:
The Daily Next Action Panel can route users to food logging now. A better canonical food catalog immediately improves daily usefulness and gives the Nutrition target-vs-actual workflow better inputs.

Then proceed to:

`Exercise Catalog Expansion v1`

Reason:
Workout variety and equipment-aware substitutions will make the training loop feel more premium, but food logging is the more immediate daily action bottleneck.

## Architecture boundaries

This plan preserves:

- deterministic backend ownership
- inspectable catalogs
- testable seed data
- no provider behavior changes
- no Level 5 semantics changes
- no direct_ollama default change
- no qwen3 usage or promotion
- no validator loosening
- no RAG/embeddings/scraping/agent orchestration
- no meal planning
- no unreviewed catalog dumps

## Acceptance criteria for planning

Architecture can accept this plan if it agrees that:

- current catalog inventory has been documented at planning level
- target food and exercise catalog shapes are clear
- required fields/tags are defined
- deterministic curation rules are explicit
- non-goals are preserved
- Food Catalog Expansion v1 is the right first implementation slice

## Expected accepted status

`CATALOG_EXPANSION_CURATION_V1_PLAN_ACCEPTED`


## Food Catalog Expansion v1 implementation note

Architecture accepted this planning milestone and approved Food Catalog Expansion v1 as the first implementation slice. The first slice expands the starter canonical food catalog from 132 to 202 curated entries while preserving deterministic curation, per-100g nutrient storage, manually curated source policy, Moderate confidence, canonical aliases, and existing logging/search behavior.

Implementation status: `FOOD_CATALOG_EXPANSION_V1_IMPLEMENTED_PENDING_QA`.
