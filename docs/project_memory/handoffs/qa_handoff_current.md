# QA Handoff Current

Milestone: Nutrition Serving Unit Logging Backend v1

QA status: backend implementation validation required.

Branch: `feature/nutrition-serving-unit-logging-backend-v1`.

Source baseline: `main` at `d74ddec`.

Commit-check mode: code.

## QA focus

Validate the new backend serving-unit logging path and confirm no unrelated behavior changed.

Primary route:

- `POST /nutrition/{user_id}/log-serving`

Expected request shape:

```json
{
  "canonical_food_id": 123,
  "serving_unit_id": 456,
  "quantity": 1.5,
  "logged_date": "2026-06-26"
}
```

Expected behavior:

- canonical food must exist and be active;
- serving unit must exist and be active;
- serving unit must belong to the canonical food;
- quantity must be positive;
- backend resolves grams;
- resolved grams are persisted to `food_entries`;
- serving-unit provenance is persisted to `nutrition_serving_unit_log_metadata`;
- Target-vs-Actual sees the logged food through existing grams actuals;
- response is public-safe.

## Regression checks

Confirm these still work:

- existing `/nutrition/log` raw/source grams logging;
- existing `/nutrition/{user_id}/log-canonical` canonical grams logging;
- canonical food search;
- serving-unit seed idempotence;
- canonical food seed idempotence;
- Target-vs-Actual actuals;
- DailyCoachSynthesis/recommendation tests if run in full suite.

## Non-goals to verify

No changes should appear in:

- Streamlit UI;
- AI/provider/Ollama/CrewAI paths;
- nutrition target formula behavior;
- food suggestion behavior;
- meal planning;
- workout/recovery/report behavior.

## Suggested focused validation

```powershell
ruff check . --fix
black .

pytest tests/test_nutrition_serving_unit_data_model_v1.py -q
pytest tests/test_nutrition_serving_unit_logging_service.py -q
pytest tests/test_nutrition_serving_unit_logging_api.py -q
pytest tests/test_canonical_food_logging_api.py -q
pytest tests/test_nutrition_target_vs_actual_service.py -q
pytest tests/test_api_smoke.py -q
pytest

python -m py_compile ui/streamlit_app.py
```

## Manual API smoke idea

After seeding canonical foods and serving units, use a known canonical food/serving unit pair from the test database or local DB, then POST to:

```text
/nutrition/1/log-serving
```

Confirm:

- response includes `resolved_grams`, gram range, confidence, and serving display;
- `/nutrition/1/target-vs-actual?date=<date>` reflects the logged actuals;
- no runtime metadata or raw source payload appears.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` means Linux canonical app runtime.

`wapp` remains Windows-local only.

`fports` remains available for local port inspection.
