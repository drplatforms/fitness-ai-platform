# Catalog Source Evaluation v1

Status: `CATALOG_SOURCE_EVALUATION_V1_IMPLEMENTED_PENDING_REVIEW`

## Purpose

Evaluate candidate food and exercise data sources before any real catalog import batch.

This milestone is the legal, quality, and technical gate between Catalog Import Pipeline v1 and future production catalog expansion.

## Scope

Allowed:

- research candidate food data sources
- research candidate exercise data sources
- document license, access, attribution, redistribution, and product-use risks
- document field compatibility with Catalog Import Pipeline v1
- recommend the first small food and exercise batch paths
- document rejected or risky sources
- update project memory docs

Not allowed:

- importing rows into canonical food catalog
- importing rows into canonical exercise catalog
- running bulk imports
- committing downloaded datasets
- scraping websites
- adding API clients
- changing app runtime behavior
- changing provider behavior
- changing nutrition calculations
- changing workout generation
- using AI to invent food or exercise facts

## Evaluation criteria

Each candidate source is evaluated on:

- license clarity
- commercial/product-use risk
- attribution requirements
- redistribution risk
- access method
- data format
- per-100g food clarity where applicable
- taxonomy compatibility where applicable
- expected cleanup difficulty
- duplicate risk
- data quality risk
- compatibility with Catalog Import Pipeline v1
- fit for a small first batch

## Final recommendation

Recommended final status:

`CATALOG_SOURCE_EVALUATION_V1_ACCEPTED_WITH_APPROVED_SMALL_BATCH_CANDIDATES`

Recommended first food source path:

- USDA FoodData Central Foundation Foods / SR Legacy, small manually selected generic foods only.

Recommended first exercise source path:

- Manual curation using existing project taxonomy, optionally cross-checking wger/Wikidata for names and taxonomy only.
- Do not copy wger descriptions, images, or any entry with unclear individual license metadata into canonical catalog without a separate review.

## Boundary confirmation

This milestone changes project memory docs only.

No source data is imported. No dataset is committed. No canonical catalog rows are changed. No runtime, provider, validator, persistence, report, nutrition, workout, Streamlit, or FastAPI behavior is changed.
