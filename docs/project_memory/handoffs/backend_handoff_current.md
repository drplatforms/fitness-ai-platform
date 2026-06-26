# Backend Handoff Current

Milestone: Nutrition Serving Unit Data Model v1

Status: implemented / scoped validation green / pending Architecture review and final snapshot.

Source baseline: `main` at `8b2c4c3`.

Branch: `feature/nutrition-serving-unit-data-model-v1`.

## Backend implementation summary

Implemented backend-owned serving-unit metadata for canonical foods.

Changed files:

- `models/nutrition_serving_unit_models.py`
- `services/nutrition_serving_unit_service.py`
- `scripts/seed_canonical_food_serving_units.py`
- `tests/test_nutrition_serving_unit_data_model_v1.py`

Project-memory files were updated for milestone closeout.

## Service behavior

The serving-unit service supports:

- schema initialization for `canonical_food_serving_units`;
- idempotent starter seed upsert;
- active serving-unit lookup by canonical food id;
- individual serving-unit lookup;
- grams estimation from serving-unit quantity;
- nutrient estimation using canonical food nutrient data.

## Seed behavior

Seed script:

```powershell
python scripts/seed_canonical_food_serving_units.py --output ..\nutrition_serving_unit_seed_v1_first.json
python scripts/seed_canonical_food_serving_units.py --output ..\nutrition_serving_unit_seed_v1_second.json
```

Observed seed smoke:

- first run inserted: 18
- second run inserted: 0
- second run updated: 18
- skipped: 0
- active serving-unit count: 18
- foods with active serving units: 12
- missing canonical foods: none

## Starter serving units

Seeded examples include:

- 1/2 cup cooked white rice, about 90g, range 80g..100g, Moderate confidence
- 1 cup cooked white rice, about 180g, range 160g..200g, Moderate confidence
- 1 large egg, about 50g, range 45g..55g, High confidence
- 1 medium banana, about 118g, range 100g..136g, Moderate confidence
- 1 tablespoon peanut butter, about 16g, range 14g..18g, High confidence
- 1 cup Greek yogurt, plain, about 245g, range 225g..265g, Moderate confidence
- 1/2 cup dry oats, about 40g, range 35g..45g, High confidence
- 4 oz cooked chicken breast, about 113g, range 110g..116g, High confidence
- 1 tablespoon olive oil, about 14g, range 13g..15g, High confidence
- 1 medium baked potato, about 173g, range 150g..200g, Moderate confidence
- 1 medium apple, about 182g, range 160g..205g, Moderate confidence
- 1 scoop whey protein powder, about 30g, range 25g..35g, Moderate confidence

## Backend non-goals preserved

- No `/nutrition/log` behavior change.
- No serving-unit logging endpoint.
- No Streamlit nutrition logging change.
- No Target-vs-Actual behavior change.
- No nutrition target formula change.
- No Daily Coach synthesis change.
- No provider/Ollama/CrewAI change.
- No AI serving-size inference.
- No broad food catalog expansion.
- No USDA/source import.
- No workout or recovery change.

## Validation note

Scoped validation passed. Full pytest has a documented baseline exception: 7 Daily Coach / Daily Narrative tests fail on source main `8b2c4c3`, so they are not treated as serving-unit regressions.

## Next backend recommendation

Nutrition Serving Unit Logging Contract Design v1.

Do not implement serving-unit logging until Architecture decides how logs should preserve original quantity/unit, resolved grams, grams ranges, and confidence.
