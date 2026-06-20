# Catalog Source Evaluation v1 Review

Status: `CATALOG_SOURCE_EVALUATION_V1_IMPLEMENTED_PENDING_REVIEW`

Proposed final status:

`CATALOG_SOURCE_EVALUATION_V1_ACCEPTED_WITH_APPROVED_SMALL_BATCH_CANDIDATES`

## Summary

Catalog Source Evaluation v1 evaluated candidate food and exercise data sources before any real import batch.

The evaluation recommends:

- Food: approve USDA FoodData Central Foundation Foods / SR Legacy for a tiny reviewed generic-food batch.
- Exercise: use manual curation for the first batch, with wger and Wikidata only as optional cross-check sources until per-entry license and attribution handling is reviewed.
- Reject scraping, commercial APIs, unclear mirrored datasets, copied exercise prose/images, AI-generated food facts, and AI-generated exercise metadata.

No data was imported. No dataset was committed. No canonical catalog rows were changed.

## Scope and non-goals

This milestone is docs/research/evaluation only.

In scope:

- food source evaluation
- exercise source evaluation
- license/access review
- data quality review
- import-pipeline compatibility review
- first-batch recommendation
- rejected-source documentation

Out of scope:

- canonical food import
- canonical exercise import
- bulk imports
- committed downloaded datasets
- scraping
- app API integration
- runtime dependencies
- AI-generated catalog truth
- provider calls
- product UI changes
- nutrition/workout behavior changes

## Evaluation criteria

Sources were reviewed for:

- license clarity
- attribution requirements
- redistribution risk
- product/commercial-use risk
- access method
- structured data availability
- Catalog Import Pipeline v1 compatibility
- per-100g nutrition clarity for foods
- taxonomy consistency for exercises
- duplicate risk
- quality risk
- cleanup difficulty
- first-batch suitability

## Food source candidates

### USDA FoodData Central - Foundation Foods / SR Legacy

Recommendation: `approve_for_small_manual_batch`

Reason:

- Official USDA source.
- FoodData Central states its data is public domain, not copyrighted, and published under CC0 1.0.
- Download files are available as CSV and JSON.
- Foundation/SR Legacy are better first-batch sources than branded foods because they are more generic and less product-churn-heavy.
- Compatible with Catalog Import Pipeline v1 after a small manual mapping step for calories, protein, carbs, and fat.

Risk:

- Nutrient field mapping must be reviewed carefully.
- Per-100g basis must be verified per staged row.
- Do not import thousands of rows in the first batch.

Decision:

Approve as the first food batch source, limited to a tiny reviewed generic-food batch.

### USDA FNDDS

Recommendation: `approve_for_future_eval`

Reason:

- Official USDA source and available through FoodData Central downloads.
- Useful for foods as consumed in dietary survey context.

Risk:

- Mixed foods and survey-food concepts may introduce serving/recipe ambiguity.
- Needs a separate mapping review before import.

Decision:

Defer until after a generic Foundation/SR Legacy batch succeeds.

### USDA Branded Foods

Recommendation: `reject_for_now`

Reason:

- Official FDC data type, but large, brand-heavy, and product-churn-heavy.
- First batch should not start with branded products.

Risk:

- Duplicate risk is high.
- Product labels and serving data can be noisy.
- Dataset size is too large for first controlled batch.

Decision:

Reject for now. Revisit after generic food import workflow is proven.

### Open Food Facts

Recommendation: `approve_for_future_eval`

Reason:

- Large open food/product database.
- Potentially useful for branded foods later.

Risk:

- ODbL attribution/share-alike obligations need a project policy before use.
- Product data is crowdsourced and brand-heavy.
- Images and some content can have separate licenses.
- Not a good first batch source.

Decision:

Future evaluation only. Do not use for first production import batch.

### Commercial food APIs and random mirrored datasets

Recommendation: `reject_for_now`

Reason:

- API integration, paid tools, and unclear dataset provenance are out of scope.
- Mirrors often obscure original license and source quality.

Decision:

Reject for now.

## Exercise source candidates

### wger exercise data

Recommendation: `manual_curation_only`

Reason:

- wger is a free/open-source fitness project with exercise wiki/API concepts.
- Project documentation says initial exercise/ingredient data is CC-BY-SA 3.0.
- README says exercise/ingredient data is Creative Commons with individual entries.

Risk:

- Individual entry license and attribution handling must be reviewed before copying data.
- Exercise descriptions/images should not be copied into this project in the first batch.
- API integration is not approved in this milestone.

Decision:

Use only as a manual cross-check/inspiration source for names/taxonomy. Do not copy descriptions/images. Do not run an API import.

### Wikidata exercise concepts

Recommendation: `approve_for_future_eval`

Reason:

- Wikidata structured data is CC0.
- It can help cross-check names and high-level taxonomy.

Risk:

- It is broad and not fitness-programming-specific.
- It does not directly map to this project's equipment and movement-pattern taxonomy without manual curation.
- API/query integration is not approved in this milestone.

Decision:

Useful future cross-check source. Not a first direct import source.

### ExRx, ACE Fitness, MuscleWiki, and similar exercise libraries

Recommendation: `reject_for_now`

Reason:

- No source-specific reusable dataset/license was approved in this evaluation.
- These sources contain copyrighted prose, media, and site-specific presentation.
- Scraping is not approved.

Decision:

Do not scrape or copy. Human readers may learn general exercise concepts, but canonical catalog rows must be independently written and reviewed.

### AI-generated exercise metadata

Recommendation: `reject_for_now`

Reason:

- AI-generated metadata has no source provenance.
- It can invent unsafe or unsupported claims.
- It violates the project rule that backend owns truth and AI may not create production catalog facts.

Decision:

Reject.

## Rejected sources

Rejected for now:

- scraped websites
- unclear dataset mirrors
- paid/commercial APIs
- user-uploaded datasets without source provenance
- copied exercise prose/images
- AI-generated food facts
- AI-generated exercise metadata
- large branded food dumps as the first batch

## Legal/licensing risk summary

Lowest risk:

- USDA FoodData Central Foundation/SR Legacy for a tiny generic-food batch.

Medium risk:

- Open Food Facts because ODbL and content-license obligations require attribution/share-alike policy.
- wger because exercise/ingredient data license depends on Creative Commons and individual entries.
- Wikidata because data is CC0, but taxonomy mapping and source quality require manual review.

Highest risk:

- commercial APIs, scraped exercise libraries, mirrored datasets, copied copyrighted descriptions/images, and AI-generated catalog truth.

## Data quality risk summary

Food risks:

- branded-product churn
- serving-size ambiguity
- per-serving values mistaken for per-100g values
- duplicate names/aliases
- source/confidence gaps
- mixed foods or recipes with unclear composition

Exercise risks:

- inconsistent equipment names
- inconsistent movement-pattern labels
- unsafe/medical/rehab claims
- copied descriptions
- duplicate aliases
- taxonomy mismatch with workout generation

## Import pipeline compatibility summary

High compatibility:

- USDA Foundation/SR Legacy after manual nutrient mapping into the importer's food fields.

Medium compatibility:

- USDA FNDDS after a separate mapping review.
- Open Food Facts after attribution/share-alike and branded-data policy are approved.
- wger as manual curation/cross-check only.
- Wikidata as taxonomy/name cross-check only.

Low compatibility:

- commercial APIs, HTML-only exercise sites, mirrored datasets, and sources requiring scraping.

## Recommended first small food batch

Recommended next milestone:

`Food Catalog Import Batch v1`

Source:

USDA FoodData Central Foundation Foods / SR Legacy.

Batch shape:

- 20 generic foods
- no branded foods
- no restaurant foods
- no complex recipes
- per-100g values only
- calories, protein, carbs, fat required
- source_name: USDA FoodData Central
- source_policy: public domain / CC0 with citation requested
- confidence: high or moderate based on row clarity
- staged through Catalog Import Pipeline v1
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

Recommended next milestone after food batch or as a separate track:

`Exercise Catalog Import Batch v1`

Source path:

Manual curation against existing project taxonomy, optionally cross-checking wger/Wikidata for exercise names and taxonomy only.

Batch shape:

- 20 equipment-matched exercises
- no copied descriptions
- no copied images
- no medical/rehab claims
- no programming claims
- names/equipment/movement_pattern/primary_muscle_group/aliases only where clear
- source_name documents manual curation and cross-check source if used
- source_policy documents project-authored or source-assisted status
- staged through Catalog Import Pipeline v1
- human review before canonical merge

## Open questions

- Should USDA source rows be mapped from Foundation Foods first or SR Legacy first?
- Should the first food import batch be 10 rows or 20 rows?
- What exact human-review checklist should be required before staged rows enter canonical catalogs?
- Should Open Food Facts be deferred until a formal ODbL attribution/share-alike policy exists?
- Should wger per-entry license metadata be reviewed before any copied exercise data is considered?
- Should Wikidata be used only for cross-checking names, or should a tiny CC0 taxonomy sample be evaluated later?

## Final recommendation

`CATALOG_SOURCE_EVALUATION_V1_ACCEPTED_WITH_APPROVED_SMALL_BATCH_CANDIDATES`

Recommended next milestone:

`Food Catalog Import Batch v1`

Reason:

USDA FoodData Central Foundation/SR Legacy is the lowest-risk, official, structured source path for a tiny reviewed generic-food import batch.

Recommended follow-up milestone:

`Exercise Catalog Import Batch v1`

Reason:

Exercise source data is legally and qualitatively riskier. The safest first exercise batch should be manually curated and source-assisted only, not copied from an exercise website or bulk API.

## Boundary confirmation

- no canonical food rows changed
- no canonical exercise rows changed
- no datasets committed
- no scraping added
- no API integration added
- no runtime behavior changed
- no provider behavior changed
- no validator/fallback behavior changed
- no persistence behavior changed
- no report behavior changed
- no nutrition calculations changed
- no workout generation changed
- no AI calls added
- no paid tools required
- no Aider required
- no Codex required
- no Headroom reintroduced
- no Claude workflow
- qa_artifacts not committed
