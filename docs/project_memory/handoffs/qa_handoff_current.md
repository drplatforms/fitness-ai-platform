# QA Handoff Current

Milestone: Canonical Serving Unit Discovery API v1

QA status: backend implementation validation required after Backend handoff.

Branch: `feature/canonical-serving-unit-discovery-api-v1`.

Source baseline: `main` at `1820fd4`.

Commit-check mode: code.

## QA focus

Validate that active serving units are discoverable through a public-safe backend endpoint before Streamlit serving-unit picker work begins.

Expected endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

## Expected behavior

QA should confirm:

- active canonical food returns active serving units;
- response includes `serving_unit_id`;
- response includes display-safe serving-unit metadata;
- inactive serving units are excluded;
- inactive/missing canonical foods are handled safely;
- canonical food with no active serving units returns a safe empty list;
- ordering is deterministic;
- raw source payloads are not exposed;
- raw SQL/debug fields are not exposed;
- existing `/foods/canonical/search` behavior remains stable;
- existing `POST /nutrition/{user_id}/log-serving` behavior remains stable;
- existing `/nutrition/{user_id}/log-canonical` behavior remains stable;
- existing `/nutrition/log` behavior remains stable;
- Target-vs-Actual remains stable.

## Manual/API smoke

Suggested smoke:

```bash
curl -s "http://127.0.0.1:8000/foods/canonical/search?q=banana" | jq
```

Then use the returned `canonical_food_id`:

```bash
curl -s "http://127.0.0.1:8000/foods/canonical/<canonical_food_id>/serving-units" | jq
```

Expected:

- `success: true`;
- active serving units if seeded;
- `serving_unit_id` visible;
- no raw payload/debug fields.

## Non-goals to verify

No changes should appear in:

- Streamlit UI;
- AI/provider/Ollama/CrewAI paths;
- Target-vs-Actual behavior;
- DailyCoachSynthesis;
- nutrition explanation behavior;
- food suggestions;
- meal planning;
- workout/recovery/report behavior.

## Suggested focused validation

Use targeted checks on touched files only; do not run repo-wide mutating formatter commands.

```powershell
git diff --check

pytest tests/test_canonical_serving_unit_discovery_api.py -q
pytest tests/test_food_canonical_search_api.py -q
pytest tests/test_nutrition_serving_unit_data_model_v1.py -q
pytest tests/test_nutrition_serving_unit_logging_api.py -q
pytest tests/test_nutrition_target_vs_actual_service.py -q
pytest tests/test_api_smoke.py -q
pytest tests/test_project_memory_check.py -q

python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
```

## Next QA routing

If accepted, the next QA lane should validate Streamlit Serving Unit Logging UI v1 using this endpoint as the only source of serving-unit options.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` means Linux canonical app runtime.

`wapp` remains Windows-local only.

`fports` remains available for local port inspection.
