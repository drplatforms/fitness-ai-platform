# Backend Handoff Current

Milestone: Nutrition Catalog Diagnostic v1

Status: implemented diagnostic / pending final validation and Architecture review.

Source baseline: `main` at `94dc8fd`.

Branch: `feature/nutrition-catalog-diagnostic-v1`.

## Backend implementation summary

Implemented diagnostic/data-audit support for the nutrition catalog foundation.

Expected changed code/test files:

- `services/nutrition_catalog_diagnostic_service.py`
- `tools/nutrition_catalog_diagnostic.py`
- `tests/test_nutrition_catalog_diagnostic_v1.py`

The diagnostic is intentionally read-only. It does not add foods, serving units, migrations, logging behavior, nutrition calculation changes, provider behavior, Streamlit UI changes, workout changes, or recovery changes.

## Diagnostic command

```powershell
python tools/nutrition_catalog_diagnostic.py --output ..\nutrition_catalog_diagnostic_v1.json
```

## Key findings

- Legacy food records: 3,475.
- Canonical food records: 222.
- Active canonical food records: 222.
- Raw/source food records: 0.
- Canonical foods safe for logging/suggestions: 222.
- Alias rows: 555.
- Foods with aliases: 222.
- Complete core macro foods: 222 / 222.
- ServingUnit model/table: not present.
- Household units: not supported.
- Foods with no serving-unit metadata: 222.
- High-value staples present: 43.
- High-value staples missing: 1, mixed nuts.
- Logs are grams-based and linked to food id.
- Logs do not support quantity/unit, servings, meal grouping, or meal type.
- Macros are recalculated from food/nutrient tables.
- Actuals assume grams.
- Confidence is not represented.
- Food suggestion readiness: limited.
- AI/provider grounding readiness: limited until serving units and confidence exist.

## Recommended next backend milestone

Recommended: Nutrition Serving Unit Data Model v1.

Reason: the catalog is more complete than expected, but serving-unit and confidence infrastructure is absent. Serving-based logging and food suggestions should not proceed until backend-owned serving conversions and confidence/range semantics exist.

Architecture may choose Nutrition Canonical Food Model Review v1 first if it wants to settle canonical/legacy write-through and source-confidence semantics before model/schema work.

## Backend non-goals preserved

- No catalog expansion.
- No serving-unit implementation.
- No household conversion.
- No food logging behavior change.
- No macro/target/report calculation change.
- No provider/Ollama/OpenAI change.
- No AI meal/snack generation.
- No Streamlit UI change.
- No workout or recovery change.
- No migration.
- No dependency change.
- No snapshots, qa_artifacts, local runtime artifacts, or patch/apply scripts committed.
- No `git add .`.
