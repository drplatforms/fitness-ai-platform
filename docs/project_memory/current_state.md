# Current State Update — Nutrition Actuals Provenance & Confidence Model v1 Implemented

Current source baseline for this feature branch: `main` after Streamlit UI project-memory closeout.

Known accepted runtime/product baseline: `0ebb1b4 Nutrition Serving Unit Logging Streamlit UI v1`.

Known project-memory closeout feature commit: `d9a3906 Close Streamlit serving unit UI project memory`.

Canonical accepted product snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

Implementation branch: `feature/nutrition-actuals-provenance-confidence-model-v1`.

Milestone: Nutrition Actuals Provenance & Confidence Model v1.

Status: backend implementation complete / ready for Architecture and focused QA review.

Requested final status: `NUTRITION_ACTUALS_PROVENANCE_CONFIDENCE_MODEL_V1_ACCEPTED`.

## Why this milestone exists

The serving-unit logging chain is accepted end-to-end:

```text
GET /foods/canonical/search
-> user selects canonical food
-> GET /foods/canonical/{canonical_food_id}/serving-units
-> user selects backend-approved serving unit
-> user enters quantity
-> POST /nutrition/{user_id}/log-serving
-> backend validates food/unit/ownership
-> backend resolves grams
-> backend writes food_entries
-> backend writes serving-unit provenance metadata
-> existing Target-vs-Actual reads resolved grams
```

The current backend can log actual intake by grams, canonical grams, and canonical serving unit. This milestone adds a deterministic interpretation layer so downstream services can understand how reliable a logged actual is without changing logging totals or UI behavior.

## Implemented backend contract

Added a public-safe model/service pair:

- `models/nutrition_actuals_confidence_models.py`
- `services/nutrition_actuals_confidence_service.py`

Primary service functions:

- `build_nutrition_actual_interpretation(food_entry_id)`
- `build_nutrition_actual_interpretations_for_date(user_id, target_date)`
- `build_public_nutrition_actual_interpretation(food_entry_id)`

The service classifies logged nutrition actuals by:

- source type;
- precision;
- confidence level;
- serving-unit metadata presence;
- gram range presence/width/percent;
- nutrient completeness;
- public-safe reason codes;
- public-safe limitations;
- public-safe display flags.

## Source types implemented

The model distinguishes:

- `raw_grams`
- `canonical_grams`
- `canonical_serving_unit`
- `unknown`

## Precision values implemented

The model distinguishes:

- `exact`
- `estimated`
- `ranged`
- `low_confidence`
- `unknown`

## Confidence values implemented

The model exposes normalized public-safe confidence values:

- `high`
- `moderate`
- `low`
- `unknown`

Serving-unit confidence is derived from persisted `nutrition_serving_unit_log_metadata.serving_unit_confidence` when available.

Raw grams and canonical grams are treated as user-entered exact gram amounts with moderate confidence unless a future milestone adds stronger source metadata.

## Nutrient completeness implemented

The service classifies core nutrient coverage for logged actuals:

- `complete`
- `partial`
- `missing_nutrients`
- `unknown`

Missing nutrient values remain missing/unknown. They are not coerced to zero.

## Serving-unit provenance interpretation

Serving-unit entries are recognized by companion metadata in `nutrition_serving_unit_log_metadata`.

The service exposes public-safe values such as:

- resolved grams;
- grams min/max when present;
- grams range width;
- grams range percent;
- amount source;
- serving-unit confidence;
- reason codes and limitations.

Wide gram ranges add a limitation and reason code.

Low-confidence serving units add a limitation and reason code.

## Boundaries preserved

No Streamlit behavior changed.

No logging endpoint behavior changed.

No Target-vs-Actual totals changed.

No macro target formula behavior changed.

No AI/provider/CrewAI/direct_ollama behavior changed.

No food suggestion or meal planning behavior changed.

No schema migration was added.

No snapshots were committed.

## Tests added

Added focused tests in:

- `tests/test_nutrition_actuals_confidence_service.py`

Coverage includes:

- raw grams classification;
- canonical grams classification;
- canonical serving-unit classification;
- resolved grams from persisted backend value;
- ranged serving-unit interpretation;
- wide range limitation;
- low-confidence serving-unit limitation;
- missing serving-unit metadata safety;
- missing nutrient values as missing, not zero;
- unknown source safety;
- public-safe output exclusion of raw/source/SQL/debug fields;
- deterministic per-date ordering;
- Target-vs-Actual totals unchanged after interpretation.

## Validation status

Focused sandbox validation:

- `pytest tests/test_nutrition_actuals_confidence_service.py -q`: 11 passed
- adjacent focused nutrition/API/project-memory tests: 117 passed
- `python -m py_compile` for new model/service/test: PASS

Sandbox note: Ruff/Black executables were not available in the sandbox. Local and Linux validation should run targeted Ruff/Black on the touched Python files only.

## Next review step

Return to Architecture for acceptance review and focused QA routing.

Recommended QA class remains:

CLASS 3 — PERSISTENCE / DATA INTEGRITY / ACTUALS SEMANTICS.

## Historical continuity anchors — reference-only

These phrases are preserved for project-memory continuity checks and are reference-only, not current scope:

- Project Memory Alignment + North Star Architecture v1
- feature/daily-coach-narrative-same-session-approved-preview-bridge-v1
- reference-only
- No provider may run on normal Today page load
- Provider Narrative QA Matrix v2
- Daily Coach Same-Session Approved Preview Bridge v1 Retry
- Same-Session Bridge Runtime QA v1
- Daily Coach Narrative Product Voice Polish v1
- Daily Coach Narrative Product Voice Runtime QA v1
- PASS_WITH_NOTE
- sound right and be right
- Local Developer Command Menu Audit + Repo-Owned Commands v1
- scripts/fitness_commands.ps1
- Local Command Menu App Runtime Correction v1
- Linux is the canonical
- wapp
- Daily Coach Async Service Shell / No Worker v1
- service shell only
- no provider execution added
