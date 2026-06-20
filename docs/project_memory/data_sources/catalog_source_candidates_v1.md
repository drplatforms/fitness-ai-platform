# Catalog Source Candidates v1

Checked date: 2026-06-20

This file records candidate source data evaluations for future food and exercise catalog expansion.

This is not an import approval. No source rows are production-approved here.

## Decision key

- `approve_for_small_manual_batch`: suitable for a tiny reviewed import batch after Architecture approves the batch plan.
- `approve_for_future_eval`: promising but needs another focused review before import.
- `manual_curation_only`: may inform manually written rows, but do not copy/import directly.
- `reject_for_now`: not suitable for current import work.

## Food source candidates

| Source | Owner / publisher | Access | License / terms summary | Product-use risk | Format | Compatibility | Recommendation | Notes |
|---|---|---|---|---|---|---|---|---|
| USDA FoodData Central - Foundation Foods / SR Legacy | USDA Agricultural Research Service | Downloadable CSV/JSON and API docs | FDC states its data is public domain, not copyrighted, and published under CC0 1.0; citation requested | Low | CSV/JSON | High after nutrient-field mapping | approve_for_small_manual_batch | Best first food source. Use tiny generic-food batch only. Prefer Foundation/SR Legacy generic foods over branded products. |
| USDA FoodData Central - FNDDS | USDA Agricultural Research Service | Downloadable CSV/JSON | Same FDC public-domain/CC0 source umbrella | Medium | CSV/JSON | Medium | approve_for_future_eval | Useful later, but survey/mixed-food concepts need careful manual selection and per-100g clarity checks. |
| USDA FoodData Central - Branded Foods | USDA / public-private branded food data | Downloadable CSV/JSON | Same FDC public-domain/CC0 source umbrella, but branded source provenance and product churn increase review burden | Medium to high | CSV/JSON | Medium | reject_for_now | Too large and brand-heavy for first batch. Defer until generic-food pipeline is proven. |
| Open Food Facts | Open Food Facts Association / contributors | Public database/download/API | Database is ODbL; content/images may have separate licenses such as CC BY-SA; attribution/share-alike obligations matter | Medium to high | CSV/JSON exports/API | Medium | approve_for_future_eval | Good future branded-food candidate, not first batch. Requires attribution/share-alike policy and no copied images/prose. |
| Commercial food APIs such as Nutritionix, Edamam, FatSecret | Private API providers | API | Terms/API contracts vary; app integration and paid/API dependency are out of scope | High | API JSON | Low for this milestone | reject_for_now | Defer unless Product/Architecture explicitly approve API integration and terms review. |
| Random Kaggle / mirrored nutrition datasets | Mixed third-party uploaders | Download | License and provenance often unclear or mirror-dependent | High | CSV/JSON | Unknown | reject_for_now | Do not use without source-of-origin license traceability. |

## Exercise source candidates

| Source | Owner / publisher | Access | License / terms summary | Product-use risk | Format | Compatibility | Recommendation | Notes |
|---|---|---|---|---|---|---|---|---|
| wger exercise data | wger project / contributors | Repository and API | App code is AGPL; initial exercise/ingredient data is CC-BY-SA 3.0; README says exercise/ingredient data is Creative Commons with individual entries | Medium | API/repository data | Medium | manual_curation_only | Promising source for exercise names/taxonomy checks, but first batch should not copy descriptions/images. Per-entry license/attribution needs review. |
| Wikidata exercise concepts | Wikidata / contributors | Dumps, API, query service | Structured data is CC0; attribution requested but not required | Low to medium | RDF/JSON/API/dumps | Low to medium | approve_for_future_eval | Useful for exercise-name/taxonomy cross-checks, not enough for direct import without manual mapping. No app API integration in this milestone. |
| ExRx exercise pages | ExRx.net | Web pages | Official reuse/license clarity was not established in this evaluation; site access/scraping is not approved | High | HTML | Low | reject_for_now | Do not scrape or copy prose/images. Can be used by a human as general inspiration only if no content is copied. |
| ACE Fitness exercise library | American Council on Exercise | Web pages | Official reusable dataset/license was not established in this evaluation | High | HTML | Low | reject_for_now | Do not scrape or copy exercise descriptions/media. |
| MuscleWiki / commercial exercise libraries | Private publishers | Web/API/app pages | Reuse and redistribution rights unclear without specific written terms | High | HTML/API | Low | reject_for_now | Not suitable for deterministic import. |
| AI-generated exercise metadata | Any provider/model | Generated text | Not source data; provenance impossible to verify | High | Text | Not compatible | reject_for_now | Do not use AI to invent production exercise truth. |

## Source pages reviewed

FoodData Central:

- https://fdc.nal.usda.gov/
- https://fdc.nal.usda.gov/download-datasets/
- https://fdc.nal.usda.gov/api-guide/

Open Food Facts / ODbL:

- https://world.openfoodfacts.org/data
- https://world.openfoodfacts.org/terms-of-use
- https://opendatacommons.org/licenses/odbl/1-0/

wger:

- https://github.com/wger-project/wger
- https://wger.readthedocs.io/en/latest/
- https://raw.githubusercontent.com/wger-project/wger/master/README.md

Wikidata:

- https://www.wikidata.org/wiki/Wikidata:Licensing
- https://www.wikidata.org/wiki/Wikidata:Data_access

## Recommended first small food batch

Use USDA FoodData Central Foundation Foods / SR Legacy only.

Recommended batch shape:

- 20 generic foods
- no branded products
- no restaurant foods
- no complex recipes
- per-100g nutrient values only
- calories, protein, carbs, fat required
- source_name set to USDA FoodData Central
- source_policy set to public domain / CC0 with citation requested
- confidence set to high or moderate based on row clarity
- all rows staged first through Catalog Import Pipeline v1
- human review before canonical merge

Suggested categories:

- lean proteins
- eggs/dairy
- staple grains/starches
- legumes
- common fruits
- common vegetables
- simple fats/seeds

## Recommended first small exercise batch

Use manual curation against the existing project taxonomy.

Recommended batch shape:

- 20 equipment-matched exercises
- no copied descriptions
- no copied images
- no medical/rehab claims
- no programming claims
- names, equipment, movement_pattern, primary_muscle_group, aliases only where clear
- source_name should describe manual curation and any cross-check source used
- source_policy should document whether source is project-authored or source-assisted
- all rows staged first through Catalog Import Pipeline v1
- human review before canonical merge

Possible cross-check sources:

- wger for exercise-name/taxonomy inspiration only, with attribution/license review before any copied data
- Wikidata for concept/name cross-checking only

## Rejected source patterns

Reject for now:

- scraped websites
- unclear dataset mirrors
- paid/commercial APIs
- user-uploaded datasets without source provenance
- copyrighted exercise prose/images
- AI-generated nutrition facts
- AI-generated exercise metadata
- large branded food dumps as the first batch

## Legal note

This is an engineering/product risk review, not legal advice. Architecture should require a narrower source-specific review before committing any third-party dataset or publishing a catalog that includes non-USDA third-party source rows.
