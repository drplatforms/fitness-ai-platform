# Next Milestone

Current milestone in progress: Nutrition Catalog Diagnostic v1.

Recommended branch: `feature/nutrition-catalog-diagnostic-v1`.

Source branch: `main`.

Required source main commit: `94dc8fd`.

Milestone type: diagnostic / data audit / project memory update.

## Diagnostic objective

Measure and report the current nutrition catalog and food logging foundation before any catalog expansion, serving-unit work, household measure conversion, logging changes, nutrition calculation changes, provider behavior, or UI/runtime changes.

Nutrition Catalog Diagnostic v1 should answer:

- how many canonical and legacy foods exist;
- how many active canonical foods exist;
- nutrient completeness;
- alias/search coverage;
- serving-unit support and gaps;
- duplicate or near-duplicate risks;
- high-value staple coverage;
- current logging assumptions;
- current actuals/targets dependencies;
- deterministic food suggestion readiness;
- AI/provider grounding readiness.

## Diagnostic findings captured

Current diagnostic output found:

- 3,475 total legacy food records.
- 222 total canonical food records.
- 222 active canonical food records.
- 0 inactive canonical food records.
- 0 raw/source food records.
- 222 canonical foods safe for logging and suggestions.
- 555 alias rows.
- 222 foods with aliases and 0 foods without aliases.
- 682 known searchable values.
- 222 / 222 canonical foods with complete core macro data.
- 0 foods missing one or more core macro fields.
- 0 fiber/sugar/sodium optional nutrient coverage in the current diagnostic.
- ServingUnit model/table is not present.
- Household units are not supported.
- 222 foods have gram default units/default grams.
- 222 foods have no serving-unit metadata.
- 43 high-value staple groups are present.
- 1 high-value staple group is missing: mixed nuts.
- Logs are grams-based and linked to food ids.
- Logs do not support quantity/unit, servings, free-text names, meal grouping, or meal type.
- Macros are recalculated from food/nutrient tables rather than persisted directly on logs.
- Actuals assume grams.
- Macro gaps exist.
- Confidence is not represented.
- Deterministic suggestion service exists but readiness is limited.
- Provider grounding is limited until serving units and confidence exist.

## Recommended next milestone after acceptance

Recommended: Nutrition Serving Unit Data Model v1.

Reason:

- The canonical catalog is not empty or broken; it already has 222 active canonical foods, aliases, complete core macros, and broad staple coverage.
- The major blocker is that household serving units, confidence/range metadata, and estimated serving conversions do not exist.
- Food logs currently store grams only and cannot safely represent serving-unit estimates without model/schema work.

Architecture may choose Nutrition Canonical Food Model Review v1 first if it wants a smaller design gate around canonical/legacy write-through, raw/source staging, and source-confidence semantics.

## Strict non-goals for Nutrition Catalog Diagnostic v1

Do not add new foods.

Do not add 150-300 curated foods yet.

Do not add serving units.

Do not add household measure conversion.

Do not add grams_default / grams_min / grams_max schema yet.

Do not modify food logging.

Do not modify macro calculations.

Do not modify nutrition targets.

Do not modify nutrition reports.

Do not modify AI/provider behavior.

Do not add qwen/direct_ollama nutrition generation.

Do not add OpenAI or any high-tier provider.

Do not import USDA/source data.

Do not add raw/staging food rows.

Do not add database migrations unless Architecture explicitly pauses and approves.

Do not touch workout generation.

Do not touch recovery engine.

Do not touch Streamlit UI unless only to avoid import/test failures.

Do not commit snapshots, qa_artifacts, patch/apply scripts, or local runtime artifacts.

Do not use `git add .`.

## Validation for this diagnostic milestone

```powershell
git diff --check
pytest tests/test_nutrition_catalog_diagnostic_v1.py -q
python tools/nutrition_catalog_diagnostic.py --output ..\nutrition_catalog_diagnostic_v1.json
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
pytest tests/test_project_memory_check.py -q
scripts/dev_commit_check.ps1 -Mode code
```

Compile touched Python files:

```powershell
python -m py_compile services/nutrition_catalog_diagnostic_service.py
python -m py_compile tools/nutrition_catalog_diagnostic.py
```

Linux validation is recommended because the diagnostic inspects runtime data paths.

Browser smoke is not required unless runtime/UI behavior changes.

Expected runtime/UI behavior change: none.

## Historical project-memory requirements still present

Some older project-memory tooling still checks for retained phrases related to prior Daily Coach async work:

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- feature/daily-coach-async-persistence-contracts-schema-v1
- schema/contracts
- NOT_AUTHORIZED_YET

These are historical continuity markers only. They do not authorize old async/provider implementation work.
